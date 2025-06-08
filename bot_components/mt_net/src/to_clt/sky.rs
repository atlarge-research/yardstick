use super::*;

#[mt_derive(to = "clt", tag = "type", content = "data", custom)]
pub enum Sky {
    Regular {
        day_sky: Color,
        day_horizon: Color,
        dawn_sky: Color,
        dawn_horizon: Color,
        night_sky: Color,
        night_horizon: Color,
        indoor: Color,
    },
    Skybox {
        textures: Vec<String>,
    },
    Plain,
}

#[mt_derive(to = "clt", tag = "type", custom)]
pub enum FogTint {
    Default,
    Custom { sun: Color, moon: Color },
}

#[mt_derive(to = "clt", custom)]
pub struct SkyParams {
    pub bg_color: Color,
    pub clouds: bool,
    pub fog_tint: FogTint,
    pub sky: Sky,
}

#[cfg(feature = "server")]
impl MtSerialize for SkyParams {
    fn mt_serialize<C: MtCfg>(
        &self,
        writer: &mut impl std::io::Write,
    ) -> Result<(), mt_ser::SerializeError> {
        self.bg_color.mt_serialize::<DefCfg>(writer)?;

        match &self.sky {
            Sky::Regular { .. } => "regular",
            Sky::Skybox { .. } => "skybox",
            Sky::Plain => "plain",
        }
        .mt_serialize::<DefCfg>(writer)?;

        self.clouds.mt_serialize::<DefCfg>(writer)?;

        match &self.fog_tint {
            FogTint::Default => {
                let unused_color = Color {
                    a: 0,
                    r: 0,
                    g: 0,
                    b: 0,
                };

                unused_color.mt_serialize::<DefCfg>(writer)?;
                unused_color.mt_serialize::<DefCfg>(writer)?;
                "default".mt_serialize::<DefCfg>(writer)?;
            }
            FogTint::Custom { sun, moon } => {
                sun.mt_serialize::<DefCfg>(writer)?;
                moon.mt_serialize::<DefCfg>(writer)?;
                "custom".mt_serialize::<DefCfg>(writer)?;
            }
        }

        match &self.sky {
            Sky::Regular {
                day_sky,
                day_horizon,
                dawn_sky,
                dawn_horizon,
                night_sky,
                night_horizon,
                indoor,
            } => {
                day_sky.mt_serialize::<DefCfg>(writer)?;
                day_horizon.mt_serialize::<DefCfg>(writer)?;
                dawn_sky.mt_serialize::<DefCfg>(writer)?;
                dawn_horizon.mt_serialize::<DefCfg>(writer)?;
                night_sky.mt_serialize::<DefCfg>(writer)?;
                night_horizon.mt_serialize::<DefCfg>(writer)?;
                indoor.mt_serialize::<DefCfg>(writer)?;
            }
            Sky::Skybox { textures } => {
                textures.mt_serialize::<DefCfg>(writer)?;
            }
            Sky::Plain => {}
        }

        Ok(())
    }
}

#[cfg(feature = "client")]
impl MtDeserialize for SkyParams {
    fn mt_deserialize<C: MtCfg>(
        reader: &mut impl std::io::Read,
    ) -> Result<Self, mt_ser::DeserializeError> {
        use mt_ser::DeserializeError::InvalidEnum;

        let bg_color = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
        let sky_type = String::mt_deserialize::<DefCfg>(reader)?;
        let clouds = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;

        let sun = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
        let moon = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;

        let fog_tint_type = String::mt_deserialize::<DefCfg>(reader)?;
        let fog_tint = match fog_tint_type.as_str() {
            "default" => FogTint::Default,
            "custom" => FogTint::Custom { sun, moon },
            _ => return Err(InvalidEnum("FogTint", Box::new(fog_tint_type))),
        };

        let sky = match sky_type.as_str() {
            "regular" => {
                let day_sky = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let day_horizon = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let dawn_sky = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let dawn_horizon = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let night_sky = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let night_horizon = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;
                let indoor = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;

                Sky::Regular {
                    day_sky,
                    day_horizon,
                    dawn_sky,
                    dawn_horizon,
                    night_sky,
                    night_horizon,
                    indoor,
                }
            }
            "skybox" => {
                let textures = MtDeserialize::mt_deserialize::<DefCfg>(reader)?;

                Sky::Skybox { textures }
            }
            "plain" => Sky::Plain,
            _ => return Err(InvalidEnum("Sky", Box::new(sky_type))),
        };

        Ok(Self {
            bg_color,
            clouds,
            fog_tint,
            sky,
        })
    }
}

#[mt_derive(to = "clt")]
pub struct SunParams {
    pub visible: bool,
    pub texture: String,
    pub tone_map: String,
    pub rise: String,
    pub rising: bool,
    pub size: f32,
}

#[mt_derive(to = "clt")]
pub struct MoonParams {
    pub visible: bool,
    pub texture: String,
    pub tone_map: String,
    pub size: f32,
}

#[mt_derive(to = "clt")]
pub struct StarParams {
    pub visible: bool,
    pub count: u32,
    pub color: Color,
    pub size: f32,
}

#[mt_derive(to = "clt")]
pub struct CloudParams {
    pub density: f32,
    pub diffuse_color: Color,
    pub ambient_color: Color,
    pub height: f32,
    pub thickness: f32,
    pub speed: Vector2<f32>,
}
