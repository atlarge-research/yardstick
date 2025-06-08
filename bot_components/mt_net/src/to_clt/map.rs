use super::*;

#[mt_derive(to = "clt", repr = "u8", enumset)]
pub enum MapBlockFlag {
    IsUnderground = 0,
    DayNightDiff,
    LightExpired,
    NotGenerated,
}

pub const ALWAYS_LIT_FROM: u16 = 0xf000;

pub const CONTENT_UNKNOWN: u16 = 125;
pub const CONTENT_AIR: u16 = 126;
pub const CONTENT_IGNORE: u16 = 127;

#[mt_derive(to = "clt")]
pub struct NodeMetaField {
    #[mt(len = "u32")]
    value: String,
    private: bool,
}

#[mt_derive(to = "clt")]
pub struct NodeMeta {
    #[mt(len = "u32")]
    fields: HashMap<String, NodeMetaField>,
    inv: Inventory,
}

#[derive(Debug)]
pub struct NodeMetasLen;

#[cfg(any(feature = "client", feature = "server"))]
impl MtCfg for NodeMetasLen {
    type Len = <DefCfg as MtCfg>::Len;
    type Inner = <DefCfg as MtCfg>::Inner;

    fn write_len(
        len: usize,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        if len == 0 {
            0u8.mt_serialize::<DefCfg>(writer)
        } else {
            2u8.mt_serialize::<DefCfg>(writer)?;
            DefCfg::write_len(len, writer)
        }
    }

    fn read_len(reader: &mut impl std::io::Read) -> Result<Self::Len, mt_ser::DeserializeError> {
        match u8::mt_deserialize::<DefCfg>(reader)? {
            0 => Ok(0),
            2 => DefCfg::read_len(reader),
            x => Err(mt_ser::DeserializeError::InvalidEnum(
                "NodeMetasLen",
                Box::new(x),
            )),
        }
    }
}

#[mt_derive(to = "clt")]
pub struct MapBlock {
    pub flags: EnumSet<MapBlockFlag>,
    pub lit_from: u16,
    #[mt(const_before = "2u8")] // param0 size
    #[mt(const_before = "2u8")] // param1 size + param2 size
    #[serde(with = "serde_arrays")]
    pub param_0: [u16; 4096],
    #[serde(with = "serde_arrays")]
    pub param_1: [u8; 4096],
    #[serde(with = "serde_arrays")]
    pub param_2: [u8; 4096],
    #[mt(len = "NodeMetasLen")]
    pub metas: HashMap<u16, NodeMeta>,
}
