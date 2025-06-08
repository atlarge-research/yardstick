use super::*;

#[mt_derive(to = "clt", repr = "str")]
pub enum ObjVisual {
    Cube,
    Sprite,
    UprightSprite,
    Mesh,
    Wielditem,
    Item,
}

#[mt_derive(to = "clt")]
pub struct ObjProps {
    #[mt(const_before = "4u8")] // version
    pub max_hp: u16, // player only
    pub collide_with_nodes: bool,
    pub weight: f32, // deprecated
    pub collision_box: Aabb3<f32>,
    pub selection_box: Aabb3<f32>,
    pub pointable: bool,
    pub visual: ObjVisual,
    pub visual_size: Vector3<f32>,
    pub textures: Vec<String>,
    pub sprite_sheet_size: Vector2<i16>, // in sprites
    pub sprite_pos: Point2<i16>,         // in sprite sheet
    pub visible: bool,
    pub make_footstep_sounds: bool,
    pub rotate_speed: Rad<f32>, // per second
    pub mesh: String,
    pub colors: Vec<Color>,
    pub collide_with_objs: bool,
    pub step_height: f32,
    pub face_rotate_dir: bool,
    pub face_rotate_dir_off: Deg<f32>,
    pub backface_cull: bool,
    pub nametag: String,
    pub nametag_color: Color,
    pub face_rotate_speed: Deg<f32>, // per second
    pub infotext: String,
    pub itemstring: String,
    pub glow: i8,
    pub max_breath: u16,    // player only
    pub eye_height: f32,    // player only
    pub zoom_fov: Deg<f32>, // player only
    pub use_texture_alpha: bool,
    pub dmg_texture_mod: String, // suffix
    pub shaded: bool,
    pub show_on_minimap: bool,
    pub nametag_bg: Color,
}

#[mt_derive(to = "clt")]
pub struct ObjPos {
    #[mt(multiplier = "BS")]
    pub pos: Point3<f32>,
    #[mt(multiplier = "BS")]
    pub vel: Vector3<f32>,
    #[mt(multiplier = "BS")]
    pub acc: Vector3<f32>,
    pub rot: Euler<Deg<f32>>,
    pub interpolate: bool,
    pub end: bool,
    pub update_interval: f32,
}

#[mt_derive(to = "clt")]
pub struct ObjSprite {
    pub frame_0: Point2<i16>,
    pub frames: u16,
    pub frame_duration: f32,
    pub view_angle_frames: bool,
}

#[mt_derive(to = "clt")]
pub struct ObjAnim {
    pub frames: Vector2<i32>,
    pub speed: f32,
    pub blend: f32,
    pub no_loop: bool,
}

#[mt_derive(to = "clt")]
pub struct ObjBonePos {
    pub pos: Point3<f32>,
    pub rot: Euler<Deg<f32>>,
}

#[mt_derive(to = "clt")]
pub struct ObjAttach {
    pub parent_id: u16,
    pub bone: String,
    pub pos: Point3<f32>,
    pub rot: Euler<Deg<f32>>,
    pub force_visible: bool,
}

#[mt_derive(to = "clt")]
pub struct ObjPhysicsOverride {
    pub walk: f32,
    pub jump: f32,
    pub gravity: f32,
    // the following are player only
    pub no_sneak: bool,
    pub no_sneak_glitch: bool,
    pub old_sneak: bool,
}

pub const GENERIC_CAO: u8 = 101;

#[mt_derive(to = "clt", repr = "u8", tag = "type", content = "data")]
pub enum ObjMsg {
    Props(Box<ObjProps>) = 0,
    Pos(ObjPos),
    TextureMod {
        #[serde(rename = "mod")]
        texture_mod: String,
    },
    Sprite(ObjSprite),
    Hp {
        hp: u16,
    },
    ArmorGroups {
        armor: HashMap<String, u16>,
    },
    Anim(ObjAnim),
    BonePos {
        bone: String,
        pos: ObjBonePos,
    },
    Attach(ObjAttach),
    PhysicsOverride(ObjPhysicsOverride),
    SpawnInfant {
        #[mt(const_after = "GENERIC_CAO")]
        id: u16,
    } = 11,
    AnimSpeed {
        speed: f32,
    },
}

#[mt_derive(to = "clt")]
pub struct ObjIdMsg {
    pub id: u16,
    #[mt(size = "u16")]
    pub msg: ObjMsg,
}

#[mt_derive(to = "clt")]
pub struct ObjInitMsg(#[mt(size = "u32")] pub ObjMsg);

#[mt_derive(to = "clt")]
pub struct ObjInitData {
    #[mt(const_before = "1u8")] // version
    pub name: String,
    pub is_player: bool,
    pub id: u16,
    #[mt(multiplier = "BS")]
    pub pos: Point3<f32>,
    pub rot: Euler<Deg<f32>>,
    pub hp: u16,
    #[mt(len = "u8")]
    pub msgs: Vec<ObjInitMsg>,
}

#[mt_derive(to = "clt")]
pub struct ObjAdd {
    pub id: u16,
    #[mt(const_before = "GENERIC_CAO")]
    #[mt(size = "u32")]
    pub init_data: ObjInitData,
}
