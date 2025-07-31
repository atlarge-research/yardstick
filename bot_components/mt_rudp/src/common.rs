use async_trait::async_trait;
use num_enum::TryFromPrimitive;
use std::{borrow::Cow, fmt::Debug, io};

pub const PROTO_ID: u32 = 0x4f457403;
pub const UDP_PKT_SIZE: usize = 512;
pub const NUM_CHANS: usize = 3;
pub const REL_BUFFER: usize = 0x8000;
pub const INIT_SEQNUM: u16 = 65500;
pub const TIMEOUT: u64 = 30;
pub const PING_TIMEOUT: u64 = 5;

#[async_trait]
pub trait UdpSender: Send + Sync {
    async fn send(&self, data: &[u8]) -> io::Result<()>;
}

#[async_trait]
pub trait UdpReceiver: Send {
    async fn recv(&mut self) -> io::Result<Vec<u8>>;
}

#[derive(Debug, Copy, Clone, PartialEq)]
#[repr(u16)]
pub enum PeerID {
    Nil = 0,
    Srv,
    CltMin,
}

#[derive(Debug, Copy, Clone, PartialEq, TryFromPrimitive)]
#[repr(u8)]
pub enum PktType {
    Ctl = 0,
    Orig,
    Split,
    Rel,
}

#[derive(Debug, Copy, Clone, PartialEq, TryFromPrimitive)]
#[repr(u8)]
pub enum CtlType {
    Ack = 0,
    SetPeerID,
    Ping,
    Disco,
}

#[derive(Debug)]
pub struct Pkt<'a> {
    pub unrel: bool,
    pub chan: u8,
    pub data: Cow<'a, [u8]>,
}

impl<'a> Pkt<'a> {
    pub fn size(&self) -> usize {
        self.header_size() + self.body_size()
    }

    pub fn body_size(&self) -> usize {
        self.data.len()
    }

    pub fn header_size(&self) -> usize {
        4 + 2 + 1 + if self.unrel { 0 } else { 1 + 2 } + 1
    }
}
