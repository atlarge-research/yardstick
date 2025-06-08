use super::*;
use num_enum::TryFromPrimitiveError;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum Error {
    #[error("io error: {0}")]
    IoError(#[from] std::io::Error),
    #[error("invalid protocol ID: {0}")]
    InvalidProtoId(u32),
    #[error("invalid channel: {0}")]
    InvalidChannel(u8),
    #[error("invalid type: {0}")]
    InvalidType(u8),
    #[error("invalid control type: {0}")]
    InvalidCtlType(u8),
    #[error("peer ID already set")]
    PeerIDAlreadySet,
    #[error("chunk index {0} bigger than chunk count {1}")]
    InvalidChunkIndex(usize, usize),
    #[error("chunk count changed from {0} to {1}")]
    InvalidChunkCount(usize, usize),
    #[error("remote disconnected (timeout = {0})")]
    RemoteDisco(bool),
    #[error("local disconnected")]
    LocalDisco,
}

impl From<TryFromPrimitiveError<PktType>> for Error {
    fn from(err: TryFromPrimitiveError<PktType>) -> Self {
        Self::InvalidType(err.number)
    }
}

impl From<TryFromPrimitiveError<CtlType>> for Error {
    fn from(err: TryFromPrimitiveError<CtlType>) -> Self {
        Self::InvalidCtlType(err.number)
    }
}
