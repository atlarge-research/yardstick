use super::*;

#[mt_derive(to = "clt", repr = "u32", enumset)]
pub enum HudStyleFlag {
    Bold,
    Italic,
    Mono,
}

#[mt_derive(to = "clt", repr = "u8", tag = "attribute", content = "value")]
pub enum HudChange {
    Pos(Point2<f32>) = 0,
    Name(String),
    Scale(Vector2<f32>),
    Text(String),
    Number(u32),
    Item(u32),
    Dir(u32),
    Align(Vector2<f32>),
    Offset(Vector2<f32>),
    WorldPos(Point3<f32>),
    Size(Vector2<i32>),
    ZIndex(i32), // this is i16 in HudAdd, minetest is weird
    Text2(String),
    Style(EnumSet<HudStyleFlag>),
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum HudType {
    Image = 0,
    Text,
    Statbar,
    Inv,
    Waypoint,
    ImageWaypoint,
    Polygone = 7,
    Item = 8,
    // Add additional types as needed for future compatibility
}

#[mt_derive(to = "clt")]
pub struct HudElement {
    pub hud_type: HudType,
    pub pos: Point2<f32>,
    pub name: String,
    pub scale: Vector2<f32>,
    pub text: String,
    pub number: u32,
    pub item: u32,
    pub dir: u32,
    pub align: Vector2<f32>,
    pub offset: Vector2<f32>,
    pub world_pos: Point3<f32>,
    pub size: Vector2<i32>,
    pub z_index: i16,
    pub text_2: String,
    pub style: EnumSet<HudStyleFlag>,
}

impl HudElement {
    pub fn apply_change(&mut self, change: HudChange) {
        use HudChange::*;

        match change {
            Pos(v) => self.pos = v,
            Name(v) => self.name = v,
            Scale(v) => self.scale = v,
            Text(v) => self.text = v,
            Number(v) => self.number = v,
            Item(v) => self.item = v,
            Dir(v) => self.dir = v,
            Align(v) => self.align = v,
            Offset(v) => self.offset = v,
            WorldPos(v) => self.world_pos = v,
            Size(v) => self.size = v,
            ZIndex(v) => self.z_index = v.try_into().unwrap_or(0),
            Text2(v) => self.text_2 = v,
            Style(v) => self.style = v,
        }
    }
}

#[mt_derive(to = "clt", repr = "u32", enumset)]
pub enum HudFlag {
    Hotbar,
    HealthBar,
    Crosshair,
    WieldedItem,
    BreathBar,
    Minimap,
    RadarMinimap,
}

#[mt_derive(to = "clt", repr = "u16", tag = "attribute", content = "value")]
pub enum HotbarParam {
    Size(#[mt(const_before = "4u16")] u32) = 1,
    Image(String),
    SelectionImage(String),
}

#[mt_derive(to = "clt", repr = "u16")]
pub enum MinimapType {
    None = 0,
    Surface,
    Radar,
    Texture,
}

#[mt_derive(to = "clt")]
pub struct MinimapMode {
    pub minimap_type: MinimapType,
    pub label: String,
    pub size: u16,
    pub texture: String,
    pub scale: u16,
}

#[mt_derive(to = "clt", custom)]
pub struct MinimapModesPkt {
    current: u16,
    modes: Vec<MinimapMode>,
}

#[cfg(feature = "server")]
impl MtSerialize for MinimapModesPkt {
    fn mt_serialize<C: MtCfg>(
        &self,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        DefCfg::write_len(self.modes.len(), writer)?;
        self.current.mt_serialize::<DefCfg>(writer)?;
        self.modes.mt_serialize::<()>(writer)?;

        Ok(())
    }
}

#[cfg(feature = "client")]
impl MtDeserialize for MinimapModesPkt {
    fn mt_deserialize<C: MtCfg>(
        reader: &mut impl std::io::Read,
    ) -> Result<Self, mt_ser::DeserializeError> {
        let len = DefCfg::read_len(reader)?;
        let current = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
        let modes = mt_ser::mt_deserialize_sized_seq::<DefCfg, _>(&len, reader)?.try_collect()?;

        Ok(Self { current, modes })
    }
}

/*
TODO: rustify this

var DefaultMinimap = []MinimapMode{
    {Type: NoMinimap},
    {Type: SurfaceMinimap, Size: 256},
    {Type: SurfaceMinimap, Size: 128},
    {Type: SurfaceMinimap, Size: 64},
    {Type: RadarMinimap, Size: 512},
    {Type: RadarMinimap, Size: 256},
    {Type: RadarMinimap, Size: 128},
}
*/
