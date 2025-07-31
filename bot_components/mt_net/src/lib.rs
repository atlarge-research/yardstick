#![feature(iterator_try_collect)]

pub use enumset;
pub use mt_ser;

#[cfg(feature = "random")]
pub use generate_random;

#[cfg(feature = "random")]
pub use rand;

#[cfg(feature = "serde")]
pub use serde;

use enumset::{EnumSet, EnumSetType};
use mt_ser::mt_derive;
use std::{
    collections::{HashMap, HashSet},
    fmt,
    ops::RangeInclusive,
};

#[cfg(any(feature = "client", feature = "server"))]
use mt_ser::{DefCfg, MtCfg, MtDeserialize, MtSerialize, Utf16};

#[cfg(feature = "random")]
use generate_random::GenerateRandom;

#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};

#[cfg(feature = "conn")]
mod conn;

#[cfg(feature = "conn")]
pub use conn::*;

pub use cgmath::{Deg, Euler, Point2, Point3, Rad, Vector2, Vector3};
pub use collision::{Aabb2, Aabb3};

pub const BS: f32 = 10.0;

mod to_clt;
mod to_srv;

pub use to_clt::*;
pub use to_srv::*;

pub trait PktInfo {
    fn pkt_info(&self) -> (u8, bool);
}
