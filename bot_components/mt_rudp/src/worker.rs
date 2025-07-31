use super::*;
use async_recursion::async_recursion;
use byteorder::{BigEndian, ReadBytesExt, WriteBytesExt};
use std::{
    borrow::Cow,
    collections::HashMap,
    io,
    pin::Pin,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::{
    sync::{mpsc, watch},
    time::{interval, sleep, Interval, Sleep},
};

fn to_seqnum(seqnum: u16) -> usize {
    (seqnum as usize) & (REL_BUFFER - 1)
}

type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
struct Split {
    timestamp: Option<Instant>,
    chunks: Vec<Option<Vec<u8>>>,
    got: usize,
}

#[derive(Debug)]
struct RecvChan {
    packets: Vec<Option<Vec<u8>>>, // char ** 😛
    splits: HashMap<u16, Split>,
    seqnum: u16,
}

#[derive(Debug)]
pub struct Worker<S: UdpSender, R: UdpReceiver> {
    sender: Arc<Sender<S>>,
    chans: [RecvChan; NUM_CHANS],
    input: R,
    close: watch::Receiver<bool>,
    resend: Interval,
    ping: Interval,
    cleanup: Interval,
    timeout: Pin<Box<Sleep>>,
    output: mpsc::UnboundedSender<Result<Pkt<'static>>>,
    closed: bool,
}

impl<S: UdpSender, R: UdpReceiver> Worker<S, R> {
    pub(crate) fn new(
        input: R,
        close: watch::Receiver<bool>,
        sender: Arc<Sender<S>>,
        output: mpsc::UnboundedSender<Result<Pkt<'static>>>,
    ) -> Self {
        Self {
            input,
            sender,
            close,
            output,
            resend: interval(Duration::from_millis(500)),
            ping: interval(Duration::from_secs(PING_TIMEOUT)),
            cleanup: interval(Duration::from_secs(TIMEOUT)),
            timeout: Box::pin(sleep(Duration::from_secs(TIMEOUT))),
            closed: false,
            chans: std::array::from_fn(|_| RecvChan {
                packets: (0..REL_BUFFER).map(|_| None).collect(),
                seqnum: INIT_SEQNUM,
                splits: HashMap::new(),
            }),
        }
    }

    pub async fn run(mut self) {
        use Error::*;

        while !self.closed {
            tokio::select! {
                _ = self.close.changed() => {
                    self.sender
                        .send_rudp_type(
                            PktType::Ctl,
                            None,
                            Pkt {
                                unrel: true,
                                chan: 0,
                                data: Cow::Borrowed(&[CtlType::Disco as u8]),
                            },
                        )
                        .await
                        .ok();

                    self.output.send(Err(LocalDisco)).ok();
                    break;
                },
                _ = &mut self.timeout => {
                    self.output.send(Err(RemoteDisco(true))).ok();
                    break;
                },
                _ = self.cleanup.tick() => {
                    let timeout = Duration::from_secs(TIMEOUT);

                    for chan in self.chans.iter_mut() {
                        chan.splits.retain(|_, v| !matches!(v.timestamp, Some(t) if t.elapsed() < timeout));
                    }
                },
                _ = self.resend.tick() => {
                    for chan in self.sender.chans.iter() {
                        for (_, ack) in chan.lock().await.acks.iter() {
                            self.sender.send_udp(&ack.data).await.ok();
                        }
                    }
                },
                _ = self.ping.tick() => {
                    self.sender
                        .send_rudp_type(
                            PktType::Ctl,
                            None,
                            Pkt {
                                chan: 0,
                                unrel: false,
                                data: Cow::Borrowed(&[CtlType::Ping as u8]),
                            },
                        )
                        .await
                        .ok();
                }
                pkt = self.input.recv() => {
                    if let Err(e) = self.handle_pkt(pkt).await {
                        self.output.send(Err(e)).ok();
                    }
                }
            }
        }
    }

    async fn handle_pkt(&mut self, pkt: io::Result<Vec<u8>>) -> Result<()> {
        use Error::*;

        let mut cursor = io::Cursor::new(pkt?);

        self.timeout
            .as_mut()
            .reset(tokio::time::Instant::now() + Duration::from_secs(TIMEOUT));

        let proto_id = cursor.read_u32::<BigEndian>()?;
        if proto_id != PROTO_ID {
            return Err(InvalidProtoId(proto_id));
        }

        let _peer_id = cursor.read_u16::<BigEndian>()?;

        let chan = cursor.read_u8()?;
        if chan >= NUM_CHANS as u8 {
            return Err(InvalidChannel(chan));
        }

        self.process_pkt(cursor, true, chan).await
    }

    #[async_recursion]
    async fn process_pkt(
        &mut self,
        mut cursor: io::Cursor<Vec<u8>>,
        unrel: bool,
        chan: u8,
    ) -> Result<()> {
        use Error::*;

        let ch = chan as usize;
        match cursor.read_u8()?.try_into()? {
            PktType::Ctl => match cursor.read_u8()?.try_into()? {
                CtlType::Ack => {
                    let seqnum = cursor.read_u16::<BigEndian>()?;
                    if let Some(ack) = self.sender.chans[ch].lock().await.acks.remove(&seqnum) {
                        ack.tx.send(true).ok();
                    }
                }
                CtlType::SetPeerID => {
                    let mut id = self.sender.remote_id.write().await;

                    if *id != PeerID::Nil as u16 {
                        return Err(PeerIDAlreadySet);
                    }

                    *id = cursor.read_u16::<BigEndian>()?;
                }
                CtlType::Ping => {}
                CtlType::Disco => {
                    self.closed = true;
                    return Err(RemoteDisco(false));
                }
            },
            PktType::Orig => {
                self.output
                    .send(Ok(Pkt {
                        chan,
                        unrel,
                        data: Cow::Owned({
    let pos = cursor.position() as usize;
    let buffer = cursor.get_ref();
    &buffer[pos..]
}.into()),
                    }))
                    .ok();
            }
            PktType::Split => {
                let seqnum = cursor.read_u16::<BigEndian>()?;
                let chunk_count = cursor.read_u16::<BigEndian>()? as usize;
                let chunk_index = cursor.read_u16::<BigEndian>()? as usize;

                let mut split = self.chans[ch]
                    .splits
                    .entry(seqnum)
                    .or_insert_with(|| Split {
                        got: 0,
                        chunks: (0..chunk_count).map(|_| None).collect(),
                        timestamp: None,
                    });

                if split.chunks.len() != chunk_count {
                    return Err(InvalidChunkCount(split.chunks.len(), chunk_count));
                }

                if split
                    .chunks
                    .get_mut(chunk_index)
                    .ok_or(InvalidChunkIndex(chunk_index, chunk_count))?
                    .replace({
    let pos = cursor.position() as usize;
    let buffer = cursor.get_ref();
    &buffer[pos..]
}.into())
                    .is_none()
                {
                    split.got += 1;
                }

                split.timestamp = if unrel { Some(Instant::now()) } else { None };

                if split.got == chunk_count {
                    let split = self.chans[ch].splits.remove(&seqnum).unwrap();

                    self.output
                        .send(Ok(Pkt {
                            chan,
                            unrel,
                            data: split
                                .chunks
                                .into_iter()
                                .map(|x| x.unwrap())
                                .reduce(|mut a, mut b| {
                                    a.append(&mut b);
                                    a
                                })
                                .unwrap_or_default()
                                .into(),
                        }))
                        .ok();
                }
            }
            PktType::Rel => {
                let seqnum = cursor.read_u16::<BigEndian>()?;
                self.chans[ch].packets[to_seqnum(seqnum)].replace({
    let pos = cursor.position() as usize;
    let buffer = cursor.get_ref();
    &buffer[pos..]
}.into());

                let mut ack_data = Vec::with_capacity(3);
                ack_data.write_u8(CtlType::Ack as u8)?;
                ack_data.write_u16::<BigEndian>(seqnum)?;

                self.sender
                    .send_rudp_type(
                        PktType::Ctl,
                        None,
                        Pkt {
                            chan,
                            unrel: true,
                            data: ack_data.into(),
                        },
                    )
                    .await?;

                let next_pkt = |chan: &mut RecvChan| chan.packets[to_seqnum(chan.seqnum)].take();
                while let Some(pkt) = next_pkt(&mut self.chans[ch]) {
                    if let Err(e) = self.process_pkt(io::Cursor::new(pkt), false, chan).await {
                        self.output.send(Err(e)).ok();
                    }

                    self.chans[ch].seqnum = self.chans[ch].seqnum.overflowing_add(1).0;
                }
            }
        }

        Ok(())
    }
}
