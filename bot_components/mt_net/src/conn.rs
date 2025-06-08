use super::PktInfo;
use async_trait::async_trait;
use mt_rudp::Pkt;
pub use mt_rudp::{Ack, Error as RudpError};
use mt_ser::{DefCfg, MtDeserialize, MtSerialize};
use std::{borrow::Cow, io};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RecvError {
    #[error("connection error: {0}")]
    ConnError(#[from] RudpError),
    #[error("deserialize error: {0}")]
    DeserializeError(#[from] mt_ser::DeserializeError),
}

#[derive(Error, Debug)]
pub enum SendError {
    #[error("connection error: {0}")]
    ConnError(#[from] io::Error),
    #[error("serialize error: {0}")]
    SerializeError(#[from] mt_ser::SerializeError),
}

#[async_trait]
pub trait SenderExt {
    type Pkt: MtSerialize + PktInfo + Send + Sync;

    async fn send_raw(&self, pkt: Pkt<'_>) -> io::Result<Ack>;
    async fn send(&self, pkt: &Self::Pkt) -> Result<Ack, SendError> {
        let mut writer = Vec::new();
        pkt.mt_serialize::<DefCfg>(&mut writer)?;

        let (chan, unrel) = pkt.pkt_info();
        Ok(self
            .send_raw(Pkt {
                chan,
                unrel,
                data: Cow::Borrowed(&writer),
            })
            .await?)
    }
}

#[async_trait]
pub trait ReceiverExt {
    type Pkt: MtDeserialize;

    async fn recv_raw(&mut self) -> Option<Result<Pkt<'static>, RudpError>>;
    async fn recv(&mut self) -> Option<Result<Self::Pkt, RecvError>> {
        self.recv_raw().await.map(|res| {
            res.map_err(RecvError::from).and_then(|pkt| {
                // TODO: warn on trailing data
                Self::Pkt::mt_deserialize::<DefCfg>(&mut io::Cursor::new(pkt.data))
                    .map_err(RecvError::from)
            })
        })
    }
}

#[cfg(feature = "client")]
pub use mt_rudp::{connect, CltReceiver, CltSender, CltWorker};

#[cfg(feature = "client")]
#[async_trait]
impl ReceiverExt for CltReceiver {
    type Pkt = crate::ToCltPkt;

    async fn recv_raw(&mut self) -> Option<Result<Pkt<'static>, RudpError>> {
        self.recv_rudp().await
    }
}

#[cfg(feature = "client")]
#[async_trait]
impl SenderExt for CltSender {
    type Pkt = crate::ToSrvPkt;

    async fn send_raw(&self, pkt: Pkt<'_>) -> io::Result<Ack> {
        self.send_rudp(pkt).await
    }
}
