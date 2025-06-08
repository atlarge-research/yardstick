use super::*;

#[mt_derive(to = "srv", repr = "u32", enumset)]
pub enum Key {
    Forward,
    Backward,
    Left,
    Right,
    Jump,
    Special,
    Sneak,
    Dig,
    Place,
    Zoom,
}

#[cfg(feature = "client")]
fn ser_cast_err() -> mt_ser::SerializeError {
    mt_ser::SerializeError::Other("cast failed".into())
}

#[cfg(feature = "server")]
fn des_cast_err() -> mt_ser::DeserializeError {
    mt_ser::DeserializeError::Other("cast failed".into())
}

#[mt_derive(to = "srv")]
pub struct PlayerPos {
    #[mt(multiplier = "100.0 * BS")]
    #[mt(map_ser = "|x| x.cast::<i32>().ok_or_else(ser_cast_err)")]
    #[mt(map_des = "|x: Point3<i32>| x.cast::<f32>().ok_or_else(des_cast_err)")]
    pub pos: Point3<f32>,
    #[mt(multiplier = "100.0 * BS")]
    #[mt(map_ser = "|x| x.cast::<i32>().ok_or_else(ser_cast_err)")]
    #[mt(map_des = "|x: Vector3<i32>| x.cast::<f32>().ok_or_else(des_cast_err)")]
    pub vel: Vector3<f32>,
    #[mt(multiplier = "100.0")]
    #[mt(map_ser = "|x| Ok(x.0 as i32)", map_des = "|x: i32| Ok(Deg(x as f32))")]
    pub pitch: Deg<f32>,
    #[mt(multiplier = "100.0")]
    #[mt(map_ser = "|x| Ok(x.0 as i32)", map_des = "|x: i32| Ok(Deg(x as f32))")]
    pub yaw: Deg<f32>,
    pub keys: EnumSet<Key>,
    #[mt(multiplier = "80.0")]
    #[mt(map_ser = "|x| Ok(x.0 as u8)", map_des = "|x: u8| Ok(Rad(x as f32))")]
    pub fov: Rad<f32>,
    pub wanted_range: u8,
}

#[mt_derive(to = "srv", repr = "u8")]
pub enum Interaction {
    Dig = 0,
    StopDigging,
    Dug,
    Place,
    Use,
    Activate,
}

#[mt_derive(to = "srv", repr = "u8", tag = "type")]
#[mt(const_before = "0u8")] // version
pub enum PointedThing {
    None = 0,
    Node {
        under: Point3<i16>,
        above: Point3<i16>,
    },
    Obj {
        obj: u16,
    },
}

#[mt_derive(to = "srv", repr = "u16", tag = "type", content = "data")]
pub enum ToSrvPkt {
    Nil = 0,
    Init {
        serialize_version: u8,
        #[mt(const_before = "1u16")] // supported compression
        proto_version: RangeInclusive<u16>,
        player_name: String,
        #[mt(default)]
        send_full_item_meta: bool,
    } = 2,
    Init2 {
        lang: String,
    } = 17,
    JoinModChan {
        channel: String,
    } = 23,
    LeaveModChan {
        channel: String,
    } = 24,
    MsgModChan {
        channel: String,
        msg: String,
    } = 25,
    PlayerPos(PlayerPos) = 35,
    GotBlocks {
        #[mt(len = "u8")]
        blocks: Vec<Point3<i16>>,
    } = 36,
    DeletedBlocks {
        #[mt(len = "u8")]
        blocks: Vec<[i16; 3]>,
    } = 37,
    HaveMedia {
        #[mt(len = "u8")]
        tokens: Vec<u32>,
    } = 41,
    InvAction {
        #[mt(len = "()")]
        action: String,
    } = 49,
    ChatMsg {
        #[mt(len = "Utf16")]
        msg: String,
    } = 50,
    FallDmg {
        amount: u16,
    } = 53,
    SelectItem {
        select_item: u16,
    } = 55,
    Respawn = 56,
    Interact {
        action: Interaction,
        item_slot: u16,
        #[mt(size = "u32")]
        pointed: PointedThing,
        pos: PlayerPos,
    } = 57,
    RemovedSounds {
        ids: Vec<i32>,
    } = 58,
    NodeMetaFields {
        pos: [i16; 3],
        formname: String,
        #[mt(len = "(DefCfg, (DefCfg, u32))")]
        fields: HashMap<String, String>,
    } = 59,
    InvFields {
        formname: String,
        #[mt(len = "(DefCfg, (DefCfg, u32))")]
        fields: HashMap<String, String>,
    } = 60,
    RequestMedia {
        filenames: Vec<String>,
    } = 64,
    CltReady {
        major: u8,
        minor: u8,
        patch: u8,
        reserved: u8,
        version: String,
        formspec: u16,
    } = 67,
    FirstSrp {
        salt: Vec<u8>,
        verifier: Vec<u8>,
        empty_passwd: bool,
    } = 80,
    SrpBytesA {
        a: Vec<u8>,
        no_sha1: bool,
    } = 81,
    SrpBytesM {
        m: Vec<u8>,
    } = 82,
    Disco = 0xffff,
}

impl PktInfo for ToSrvPkt {
    fn pkt_info(&self) -> (u8, bool) {
        use ToSrvPkt::*;

        match self {
            Init { .. } => (1, false),
            Init2 { .. }
            | RequestMedia { .. }
            | CltReady { .. }
            | FirstSrp { .. }
            | SrpBytesA { .. }
            | SrpBytesM { .. } => (1, true),
            PlayerPos { .. } => (0, false),
            GotBlocks { .. } | HaveMedia { .. } | DeletedBlocks { .. } | RemovedSounds { .. } => {
                (2, true)
            }
            _ => (0, true),
        }
    }
}
