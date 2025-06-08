use super::*;

#[mt_derive(to = "clt", custom)]
pub struct Inventory; // TODO

#[cfg(feature = "server")]
impl MtSerialize for Inventory {
    fn mt_serialize<C: MtCfg>(
        &self,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        "EndInventory\n".mt_serialize::<()>(writer)
    }
}

#[cfg(feature = "client")]
fn read_line(reader: &mut impl std::io::Read) -> Result<String, mt_ser::DeserializeError> {
    let utf8 = mt_ser::mt_deserialize_seq::<(), u8>(reader)?
        .map_while(|x| match x {
            Ok(0x0A) => None,
            x => Some(x),
        })
        .try_collect::<Vec<_>>()?;

    String::from_utf8(utf8)
        .map_err(|e| mt_ser::DeserializeError::Other(format!("Invalid UTF-8: {e}")))
}

#[cfg(feature = "client")]
impl MtDeserialize for Inventory {
    fn mt_deserialize<C: MtCfg>(
        reader: &mut impl std::io::Read,
    ) -> Result<Self, mt_ser::DeserializeError> {
        loop {
            match read_line(reader)?.as_str() {
                "EndInventory" => return Ok(Self),
                _ => {}
            }
        }
    }
}
