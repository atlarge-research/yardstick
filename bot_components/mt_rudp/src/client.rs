use super::*;
use async_trait::async_trait;
use std::{io, sync::Arc};
use tokio::{
    net,
    sync::{mpsc, watch},
};

#[derive(Debug)]
pub struct UdpCltSender(Arc<net::UdpSocket>);

#[derive(Debug)]
pub struct UdpCltReceiver(Arc<net::UdpSocket>);

#[async_trait]
impl UdpSender for UdpCltSender {
    async fn send(&self, data: &[u8]) -> io::Result<()> {
        self.0.send(data).await?;
        Ok(())
    }
}

#[async_trait]
impl UdpReceiver for UdpCltReceiver {
    async fn recv(&mut self) -> io::Result<Vec<u8>> {
        let mut buffer = Vec::new();
        buffer.resize(UDP_PKT_SIZE, 0);

        let len = self.0.recv(&mut buffer).await?;
        buffer.truncate(len);

        Ok(buffer)
    }
}

#[derive(Debug)]
pub struct CltReceiver(mpsc::UnboundedReceiver<Result<Pkt<'static>, Error>>);

impl CltReceiver {
    pub async fn recv_rudp(&mut self) -> Option<Result<Pkt<'static>, Error>> {
        self.0.recv().await
    }
}

pub type CltSender = Arc<Sender<UdpCltSender>>;
pub type CltWorker = Worker<UdpCltSender, UdpCltReceiver>;

pub async fn connect(addr: &str) -> io::Result<(CltSender, CltReceiver, CltWorker)> {
    let sock = Arc::new(net::UdpSocket::bind("0.0.0.0:0").await?);
    sock.connect(addr).await?;

    let (close_tx, close_rx) = watch::channel(false);
    let (pkt_tx, pkt_rx) = mpsc::unbounded_channel();

    let sender = Sender::new(
        UdpCltSender(Arc::clone(&sock)),
        close_tx,
        PeerID::Srv as u16,
        PeerID::Nil as u16,
    );

    Ok((
        Arc::clone(&sender),
        CltReceiver(pkt_rx),
        Worker::new(UdpCltReceiver(sock), close_rx, sender, pkt_tx),
    ))
}
