use super::*;

#[mt_derive(to = "clt", repr = "u8", tag = "reason")]
pub enum KickReason {
    WrongPasswd,
    UnexpectedData,
    SrvIsSingleplayer,
    UnsupportedVersion,
    BadNameChars,
    BadName,
    TooManyClts,
    EmptyPasswd,
    AlreadyConnected,
    SrvErr,
    Custom { custom: String },
    Shutdown { custom: String, reconnect: bool },
    Crash { custom: String, reconnect: bool },
}

impl KickReason {
    pub fn reconnect(&self) -> bool {
        use KickReason::*;

        match self {
            Shutdown { reconnect, .. } | Crash { reconnect, .. } => *reconnect,
            _ => false,
        }
    }
}

impl fmt::Display for KickReason {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        use KickReason::*;

        match self {
            WrongPasswd => write!(f, "wrong password"),
            UnexpectedData => write!(f, "unexpected data"),
            SrvIsSingleplayer => write!(f, "server is singleplayer"),
            UnsupportedVersion => write!(f, "unsupported client version"),
            BadNameChars => write!(f, "disallowed character(s) in player name"),
            BadName => write!(f, "disallowed player name"),
            TooManyClts => write!(f, "too many clients"),
            EmptyPasswd => write!(f, "empty password"),
            AlreadyConnected => write!(f, "another client is already connected with the same name"),
            SrvErr => write!(f, "unsupported client version"),
            Custom { custom } => write!(f, "{custom}"),
            Shutdown { custom, .. } => {
                if custom.is_empty() {
                    write!(f, "server shutdown")
                } else {
                    write!(f, "server shutdown: {custom}")
                }
            }
            Crash { custom, .. } => {
                if custom.is_empty() {
                    write!(f, "server crash")
                } else {
                    write!(f, "server crash: {custom}")
                }
            }
        }
    }
}
