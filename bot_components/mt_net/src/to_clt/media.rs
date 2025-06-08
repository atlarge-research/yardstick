use super::*;

#[mt_derive(to = "clt", repr = "u8")]
pub enum Param1Type {
    None = 0,
    Light,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum Param2Type {
    Nibble = 0,
    Byte,
    Flowing,
    FaceDir,
    Mounted,
    Leveled,
    Rotation,
    Mesh,
    Color,
    ColorFaceDir,
    ColorMounted,
    GrassLikeLevel,
    ColorRotation,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum DrawType {
    Cube = 0,
    None,
    Liquid,
    Flowing,
    GlassLike,
    AllFaces,
    AllFacesOpt,
    Torch,
    Sign,
    Plant,
    Fence,
    Rail,
    NodeBox,
    GlassFrame,
    Fire,
    GlassFrameOpt,
    Mesh,
    RootedPlant,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum Waving {
    None = 0,
    Plant,
    Leaf,
    Liquid,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum Liquid {
    None = 0,
    Flowing,
    Source,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum Alpha {
    Blend = 0,
    Mask, // either fully opaque or transparent
    Opaque,
    Legacy,
}

#[mt_derive(to = "clt", repr = "u8", tag = "type")]
pub enum TileAnim {
    None = 0,
    VerticalFrame {
        n_frames: Vector2<u16>,
        duration: f32,
    },
    SpriteSheet {
        aspect_ratio: Vector2<u8>,
        duration: f32,
    },
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum TileAlign {
    None = 0,
    World,
    User,
}

#[mt_derive(to = "clt", enumset, custom)]
pub enum TileFlag {
    BackfaceCull,
    TileHorizontal,
    TileVertical,
}

#[mt_derive(to = "clt", repr = "u16", enumset)]
enum TileFlagInternal {
    BackfaceCull,
    TileHorizontal,
    TileVertical,
    Color,
    Scale,
    Align,
}

#[mt_derive(to = "clt")]
pub struct Texture {
    pub name: String,
    /// set to zero. use this field however you like
    #[mt(map_ser = "|_| Ok(())", map_des = "|_: ()| Ok(0)")]
    pub custom: usize,
}

#[mt_derive(to = "clt", custom)]
pub struct TileDef {
    // #[mt(const_before = "6u8")]
    pub texture: Texture,
    pub animation: TileAnim,
    pub flags: EnumSet<TileFlag>,
    pub color: Option<[u8; 3]>,
    pub scale: Option<u8>,
    pub align: Option<TileAlign>,
}

#[cfg(feature = "server")]
impl MtSerialize for TileDef {
    fn mt_serialize<C: MtCfg>(
        &self,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        6u8.mt_serialize::<DefCfg>(writer)?;
        self.texture.mt_serialize::<DefCfg>(writer)?;
        self.animation.mt_serialize::<DefCfg>(writer)?;

        let mut flags: EnumSet<TileFlagInternal> = self
            .flags
            .iter()
            .map(|f| match f {
                TileFlag::BackfaceCull => TileFlagInternal::BackfaceCull,
                TileFlag::TileHorizontal => TileFlagInternal::TileHorizontal,
                TileFlag::TileVertical => TileFlagInternal::TileVertical,
            })
            .collect();

        if self.color.is_some() {
            flags.insert(TileFlagInternal::Color);
        }

        if self.scale.is_some() {
            flags.insert(TileFlagInternal::Scale);
        }

        if self.align.is_some() {
            flags.insert(TileFlagInternal::Align);
        }

        flags.mt_serialize::<DefCfg>(writer)?;
        self.color.mt_serialize::<DefCfg>(writer)?;
        self.scale.mt_serialize::<DefCfg>(writer)?;
        self.align.mt_serialize::<DefCfg>(writer)?;

        Ok(())
    }
}

#[cfg(feature = "client")]
impl MtDeserialize for TileDef {
    fn mt_deserialize<C: MtCfg>(
        reader: &mut impl std::io::Read,
    ) -> Result<Self, mt_ser::DeserializeError> {
        let const6u8 = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
        if 6u8 != const6u8 {
            return Err(mt_ser::DeserializeError::InvalidConst(
                Box::new(const6u8),
                Box::new(6u8),
            ));
        }

        let texture = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
        let animation = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;

        let flags_internal = EnumSet::<TileFlagInternal>::mt_deserialize::<DefCfg>(reader)?;

        let color = if flags_internal.contains(TileFlagInternal::Color) {
            Some(MtDeserialize::mt_deserialize::<DefCfg>(reader)?)
        } else {
            None
        };

        let scale = if flags_internal.contains(TileFlagInternal::Scale) {
            Some(MtDeserialize::mt_deserialize::<DefCfg>(reader)?)
        } else {
            None
        };

        let align = if flags_internal.contains(TileFlagInternal::Align) {
            Some(MtDeserialize::mt_deserialize::<DefCfg>(reader)?)
        } else {
            None
        };

        let flags = flags_internal
            .iter()
            .flat_map(|f| match f {
                TileFlagInternal::BackfaceCull => Some(TileFlag::BackfaceCull),
                TileFlagInternal::TileHorizontal => Some(TileFlag::TileHorizontal),
                TileFlagInternal::TileVertical => Some(TileFlag::TileVertical),
                _ => None,
            })
            .collect();

        Ok(Self {
            texture,
            animation,
            flags,
            color,
            scale,
            align,
        })
    }
}

trait BsAabb: Sized {
    fn ser(&self) -> Self;
    fn des(&self) -> Self;
}

impl BsAabb for Aabb3<f32> {
    fn ser(&self) -> Self {
        collision::Aabb::mul_s(self, BS)
    }

    fn des(&self) -> Self {
        collision::Aabb::mul_s(self, BS)
    }
}

impl<T: BsAabb> BsAabb for Vec<T> {
    fn ser(&self) -> Self {
        self.iter().map(BsAabb::ser).collect()
    }

    fn des(&self) -> Self {
        self.iter().map(BsAabb::des).collect()
    }
}

impl<T: BsAabb, const N: usize> BsAabb for [T; N] {
    fn ser(&self) -> Self {
        std::array::from_fn(|i| self[i].ser())
    }

    fn des(&self) -> Self {
        std::array::from_fn(|i| self[i].des())
    }
}

#[cfg(feature = "server")]
fn ser_bs_aabb<T: BsAabb>(aabb: &T) -> Result<T, mt_ser::SerializeError> {
    Ok(aabb.ser())
}

#[cfg(feature = "client")]
fn des_bs_aabb<T: BsAabb>(aabb: T) -> Result<T, mt_ser::DeserializeError> {
    Ok(aabb.des())
}

#[mt_derive(to = "clt")]
pub struct MountedNodeBox {
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    wall_top: Aabb3<f32>,
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    wall_bottom: Aabb3<f32>,
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    wall_sides: Aabb3<f32>,
}

#[mt_derive(to = "clt")]
pub struct ConnectedNodeBox {
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    fixed: Vec<Aabb3<f32>>,
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    connect_dirs: [Vec<Aabb3<f32>>; 6],
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    disconnect_dirs: [Vec<Aabb3<f32>>; 6],
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    disconnect_all: Vec<Aabb3<f32>>,
    #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
    disconnect_sides: Vec<Aabb3<f32>>,
}

#[mt_derive(to = "clt", repr = "u8", tag = "type")]
#[mt(const_before = "6u8")]
pub enum NodeBox {
    Cube = 0,
    Fixed {
        #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
        fixed: Vec<Aabb3<f32>>,
    },
    Mounted(Box<MountedNodeBox>),
    Leveled {
        #[mt(map_ser = "ser_bs_aabb", map_des = "des_bs_aabb")]
        fixed: Vec<Aabb3<f32>>,
    },
    Connected(Box<ConnectedNodeBox>),
}

#[mt_derive(to = "clt")]
#[mt(size = "u16")]
pub struct NodeDef {
    // TODO: impl Default
    #[mt(const_before = "13u8")]
    pub name: String,
    pub groups: HashMap<String, u16>,
    pub param1_type: Param1Type,
    pub param2_type: Param2Type,
    pub draw_type: DrawType,
    pub mesh: String,
    pub scale: f32,
    #[mt(const_before = "6u8")]
    pub tiles: [TileDef; 6],
    pub overlay_tiles: [TileDef; 6],
    #[mt(const_before = "6u8")]
    pub special_tiles: [TileDef; 6],
    pub color: Color,
    pub palette: String,
    pub waving: Waving,
    pub connect_sides: u8,
    pub connect_to: Vec<u16>,
    pub inside_tint: Color,
    pub level: u8,         // FIXME: must be below 128
    pub translucent: bool, // sunlight scattering
    pub transparent: bool,
    pub light_source: u8, // FIXME: max: 14 (?)
    pub ground_content: bool,
    pub collision: bool,
    pub pointable: bool,
    pub diggable: bool,
    pub climbable: bool,
    pub replaceable: bool,
    pub has_on_right_click: bool,
    pub damage_per_second: i32,
    pub liquid: Liquid,
    pub flowing_alt: String,
    pub source_alt: String,
    pub viscosity: u8, // FIXME: 0-7
    pub liquid_renewable: bool,
    pub flow_range: u8,
    pub drown_damage: u8,
    pub floodable: bool,
    pub draw_box: NodeBox,
    pub collision_box: NodeBox,
    pub selection_box: NodeBox,
    pub footstep_sound: SoundDef,
    pub digging_sound: SoundDef,
    pub dug_sound: SoundDef,
    pub legacy_face_dir: bool,
    pub legacy_mounted: bool,
    pub dig_predict: String,
    pub max_level: u8,
    pub alpha: Alpha,
    pub move_resistance: u8,
    pub liquid_move_physics: bool,
}

#[mt_derive(to = "clt", custom)]
pub struct NodeDefs(pub HashMap<u16, NodeDef>);

// stupid bullshit ahead

#[cfg(feature = "server")]
impl MtSerialize for NodeDefs {
    fn mt_serialize<C: MtCfg>(
        &self,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        DefCfg::write_len(self.0.len(), writer)?;

        let mut buf = Vec::new();
        self.0.mt_serialize::<()>(&mut buf)?;
        buf.mt_serialize::<u32>(writer)?;

        Ok(())
    }
}

#[cfg(feature = "client")]
impl MtDeserialize for NodeDefs {
    fn mt_deserialize<C: MtCfg>(
        reader: &mut impl std::io::Read,
    ) -> Result<Self, mt_ser::DeserializeError> {
        use mt_ser::MtLen;

        let len = DefCfg::read_len(reader)?;
        let mut reader = u32::read_len(reader)?.take(mt_ser::WrapRead(reader));
        let inner =
            mt_ser::mt_deserialize_sized_seq::<DefCfg, _>(&len, &mut reader)?.try_collect()?;

        Ok(Self(inner))
    }
}

/* TODO: Rustify this

func BuiltinNodeDefs(n int) map[Content]NodeDef {
    defs := make(map[Content]NodeDef, 3+n)
    defs[Unknown] = NodeDef{
        Name: "unknown",
    }
    defs[Air] = NodeDef{
        Name:        "air",
        DrawType:    DrawNothing,
        P1Type:      P1Light,
        Translucent: true,
        Transparent: true,
        Replaceable: true,
        Floodable:   true,
        GndContent:  true,
    }
    defs[Ignore] = NodeDef{
        Name:        "ignore",
        DrawType:    DrawNothing,
        Replaceable: true,
        GndContent:  true,
    }
    return defs
}
*/

#[mt_derive(to = "clt")]
pub struct ToolGroupCap {
    pub uses: i16, // 32to16
    pub max_level: i16,
    #[mt(len = "u32")]
    pub times: HashMap<i16, f32>,
}

#[mt_derive(to = "clt")]
pub struct ToolCaps {
    #[mt(const_before = "5u8")]
    pub attack_cooldown: f32,
    pub max_drop_level: i16,
    #[mt(len = "u32")]
    pub group_caps: HashMap<String, ToolGroupCap>,
    #[mt(len = "u32")]
    pub dmg_groups: HashMap<String, u16>,
    pub punch_uses: u16, // 32tou16
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum ItemType {
    None = 0,
    Node,
    Craft,
    Tool,
}

#[mt_derive(to = "clt", repr = "u8")]
pub enum SoundSource {
    Nowhere = 0,
    Pos,
    Obj,
}

#[mt_derive(to = "clt")]
pub struct SoundDef {
    pub name: String,
    pub gain: f32,
    pub pitch: f32,
    pub fade: f32,
}

#[mt_derive(to = "clt")]
#[mt(size = "u16")]
pub struct ItemDef {
    #[mt(const_before = "6u8")]
    #[serde(rename = "type")]
    pub item_type: ItemType,
    pub name: String,
    pub description: String,
    pub inventory_image: String,
    pub wield_image: String,
    pub wield_scale: Vector3<f32>,
    pub stack_max: u16,
    pub usable: bool,
    pub can_point_liquids: bool,
    #[mt(size = "u16")]
    pub tool_caps: Option<ToolCaps>,
    pub groups: HashMap<String, u16>,
    pub place_predict: String,
    pub place_sound: SoundDef,
    pub place_fail_sound: SoundDef,
    pub point_range: f32,
    pub palette: String,
    pub color: Color,
    pub inventory_overlay: String,
    pub wield_overlay: String,
    pub short_description: String,
    pub place_param2: u8,
}
