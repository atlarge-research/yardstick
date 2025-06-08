use super::*;
use byteorder::{BigEndian, WriteBytesExt};
use std::{
    borrow::Cow,
    collections::HashMap,
    io::{self, Write},
    sync::Arc,
};
use tokio::sync::{watch, Mutex, RwLock};

pub type Ack = Option<watch::Receiver<bool>>;

#[derive(Debug)]
pub(crate) struct AckWait {
    pub(crate) tx: watch::Sender<bool>,
    pub(crate) rx: watch::Receiver<bool>,
    pub(crate) data: Vec<u8>,
}

#[derive(Debug)]
pub(crate) struct Chan {
    pub(crate) acks: HashMap<u16, AckWait>,
    pub(crate) seqnum: u16,
    pub(crate) splits_seqnum: u16,
}

#[derive(Debug)]
pub struct Sender<S: UdpSender> {
    pub(crate) id: u16,
    pub(crate) remote_id: RwLock<u16>,
    pub(crate) chans: [Mutex<Chan>; NUM_CHANS],
    udp: S,
    close: watch::Sender<bool>,
}

impl<S: UdpSender> Sender<S> {
    pub fn new(udp: S, close: watch::Sender<bool>, id: u16, remote_id: u16) -> Arc<Self> {
        Arc::new(Self {
            id,
            remote_id: RwLock::new(remote_id),
            udp,
            close,
            chans: std::array::from_fn(|_| {
                Mutex::new(Chan {
                    acks: HashMap::new(),
                    seqnum: INIT_SEQNUM,
                    splits_seqnum: INIT_SEQNUM,
                })
            }),
        })
    }

    pub async fn send_rudp(&self, pkt: Pkt<'_>) -> io::Result<Ack> {
        if pkt.size() > UDP_PKT_SIZE {
            let chunks = pkt
                .data
                .chunks(UDP_PKT_SIZE - (pkt.header_size() + 1 + 2 + 2 + 2));
            let num_chunks: u16 = chunks
                .len()
                .try_into()
                .map_err(|_| io::Error::new(io::ErrorKind::Other, "too many chunks"))?;

            let seqnum = {
                let mut chan = self.chans[pkt.chan as usize].lock().await;
                let sn = chan.splits_seqnum;
                chan.splits_seqnum = chan.splits_seqnum.overflowing_add(1).0;

                sn
            };

            for (i, ch) in chunks.enumerate() {
                self.send_rudp_type(
                    PktType::Orig,
                    Some((seqnum, num_chunks, i as u16)),
                    Pkt {
                        unrel: pkt.unrel,
                        chan: pkt.chan,
                        data: Cow::Borrowed(ch),
                    },
                )
                .await?;
            }

            Ok(None) // TODO: ack
        } else {
            self.send_rudp_type(PktType::Orig, None, pkt).await
        }
    }

    pub async fn send_rudp_type(
        &self,
        tp: PktType,
        chunk: Option<(u16, u16, u16)>,
        pkt: Pkt<'_>,
    ) -> io::Result<Ack> {
        let mut buf =
            Vec::with_capacity(pkt.size() + if chunk.is_some() { 1 + 2 + 2 + 2 } else { 0 });

        buf.write_u32::<BigEndian>(PROTO_ID)?;
        buf.write_u16::<BigEndian>(*self.remote_id.read().await)?;
        buf.write_u8(pkt.chan)?;

        let mut chan = self.chans[pkt.chan as usize].lock().await;
        let seqnum = chan.seqnum;

        if !pkt.unrel {
            buf.write_u8(PktType::Rel as u8)?;
            buf.write_u16::<BigEndian>(seqnum)?;
        }

        if let Some((seqnum, count, index)) = chunk {
            buf.write_u8(PktType::Split as u8)?;
            buf.write_u16::<BigEndian>(seqnum)?;
            buf.write_u16::<BigEndian>(count)?;
            buf.write_u16::<BigEndian>(index)?;
        } else {
            buf.write_u8(tp as u8)?;
        }

        buf.write_all(pkt.data.as_ref())?;

        self.send_udp(&buf).await?;

        if pkt.unrel {
            Ok(None)
        } else {
            // TODO: reliable window
            let (tx, rx) = watch::channel(false);
            chan.acks.insert(
                seqnum,
                AckWait {
                    tx,
                    rx: rx.clone(),
                    data: buf,
                },
            );
            chan.seqnum = chan.seqnum.overflowing_add(1).0;

            Ok(Some(rx))
        }
    }

    pub async fn send_udp(&self, data: &[u8]) -> io::Result<()> {
        if data.len() > UDP_PKT_SIZE {
            panic!(
                "attempted to send a packet with len {} > {UDP_PKT_SIZE}",
                data.len()
            );
        }

        self.udp.send(data).await
    }

    pub async fn peer_id(&self) -> u16 {
        self.id
    }

    pub async fn is_server(&self) -> bool {
        self.id == PeerID::Srv as u16
    }

    pub fn close(&self) {
        self.close.send(true).ok();
    }
}
