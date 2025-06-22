use clap::Parser;
use futures_util::future::OptionFuture;
use mt_auth::Auth;
use mt_net::{self, CltSender, Key, PlayerPos, ReceiverExt, SenderExt, ToCltPkt, ToSrvPkt};
use mt_net::{Interaction, PointedThing};
// Import enumset through mt_net to avoid version conflicts
use mt_net::enumset::{EnumSet};
// Import Deg and Rad from mt_net
use mt_net::{Deg, Rad};
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};
use tokio::time::{sleep, Sleep};
use rand::prelude::*;

#[derive(Parser, Debug)]
#[clap(version, about = "A block-placing bot for Luanti/Minetest", long_about = None)]
struct Args {
    /// Server address. Format: address:port
    #[clap(value_parser)]
    address: String,

    /// Quit after QUIT_AFTER seconds
    #[clap(short, long, value_parser)]
    quit_after_seconds: Option<f32>,

    /// Player name
    #[clap(short, long, value_parser, default_value = "blockbot")]
    username: String,

    /// Password
    #[clap(short, long, value_parser, default_value = "blockbot123")]
    password: String,
    
    /// Force using lowercase username for authentication
    #[clap(long, value_parser, default_value_t = false)]
    force_lowercase: bool,
    
    /// Register a new account (if false, tries to log in to existing account)
    #[clap(long, value_parser, default_value_t = false)]
    register: bool,
    
    /// Auto register: if login fails, try registration
    #[clap(long, value_parser, default_value_t = true)]
    auto_register: bool,

    /// Building pattern: tower, wall, platform, random, spiral, house
    #[clap(short, long, value_parser, default_value = "tower")]
    pattern: String,

    /// Block placement speed in seconds between placements
    #[clap(short, long, value_parser, default_value_t = 1.0)]
    speed: f32,
    
    /// Maximum blocks to place before stopping (-1 for unlimited)
    #[clap(long, value_parser, default_value_t = 100)]
    max_blocks: i32,
    
    /// Starting X coordinate for building
    #[clap(long, value_parser, default_value_t = 0.0)]
    start_x: f32,
    
    /// Starting Y coordinate for building  
    #[clap(long, value_parser, default_value_t = 8.0)]
    start_y: f32,
    
    /// Starting Z coordinate for building
    #[clap(long, value_parser, default_value_t = 0.0)]
    start_z: f32,
    
    /// Block type to place (item slot number, 0-based)
    #[clap(long, value_parser, default_value_t = 0)]
    block_slot: u16,
    
    /// Also dig/remove blocks (destructive mode)
    #[clap(long, value_parser, default_value_t = false)]
    destructive: bool,
}

#[derive(Debug, Clone)]
pub enum BuildingPattern {
    Tower,      // Build straight up
    Wall,       // Build horizontally in a line
    Platform,   // Build a flat platform
    Random,     // Place blocks randomly nearby
    Spiral,     // Build in a spiral pattern upward
    House,      // Build a simple house structure
}

pub struct BotState {
    pub connected: bool,
    pub authenticated: bool,
    pub ready: bool,
}

pub struct BlockBot {
    pub conn: CltSender,
    pub auth: Auth,
    pub state: BotState,
    pub auto_register: bool,
    pub tried_register: bool,
    pub username: String, 
    pub password: String,
    pub position: Option<PlayerPos>,
    pub building_pattern: BuildingPattern,
    pub placement_interval: Duration,
    pub last_placement: Option<Instant>,
    pub running: Arc<AtomicBool>,
    
    // Block placement state
    pub blocks_placed: u32,
    pub max_blocks: i32,
    pub current_build_pos: [f32; 3],  // Current building position
    pub build_direction: i32,          // Direction counter for patterns
    pub block_slot: u16,               // Which inventory slot to use
    pub destructive_mode: bool,        // Whether to also dig blocks
    
    // Pattern-specific state
    pub spiral_radius: f32,
    pub spiral_angle: f32,
    pub house_progress: u32,  // Which part of house we're building
}

impl BlockBot {
    async fn try_register(&mut self) {
        // Create a new Auth instance in registration mode
        self.auth = Auth::new(
            self.conn.clone(), 
            self.username.clone(), 
            self.password.clone(), 
            "en_US", 
            true // Register mode
        );
        
        // Start the auth process again
        tokio::spawn(async move {
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
            eprintln!("Reconnecting with registration mode...");
        });
    }

    pub async fn handle_pkt(&mut self, pkt: ToCltPkt) {
        use ToCltPkt::*;

        match &pkt {
            Kick(reason) => {
                eprintln!("Kicked: {reason}");
                
                // If we get kicked with "wrong password" and auto_register is true,
                // we should try to register instead
                if format!("{reason}").contains("wrong password") && 
                   self.auto_register && 
                   !self.tried_register {
                    eprintln!("Auto-register: Login failed with wrong password. Trying to register a new account...");
                    self.tried_register = true;
                    self.try_register().await;
                }
            },
            MovePlayer { pos, .. } => {
                if self.position.is_none() {
                    // Initialize the position with the server's position
                    let mut fixed_pos = *pos;
                    fixed_pos[1] = self.current_build_pos[1]; // Use our intended Y position
                    
                    self.position = Some(PlayerPos {
                        pos: fixed_pos,
                        vel: [0.0, 0.0, 0.0].into(),
                        pitch: Deg(-45.0), // Look down slightly to see blocks better
                        yaw: Deg(0.0),
                        keys: EnumSet::new(),
                        fov: Rad(1.0),
                        wanted_range: 10,
                    });
                    self.last_placement = Some(Instant::now());
                    eprintln!("[{}] Initial position set: ({:.2}, {:.2}, {:.2}) - Ready to build!", 
                              self.username, fixed_pos[0], fixed_pos[1], fixed_pos[2]);
                }
            },
            // Listen for inventory updates to track our blocks
            Inv { inv } => {
                // Could parse inventory to see what blocks we have
                eprintln!("[{}] Inventory update received (length: {})", self.username, inv.len());
            },
            // Listen for node addition confirmations
            AddNode { pos, param0, .. } => {
                eprintln!("[{}] Block placed confirmed at ({}, {}, {}), type: {}", 
                          self.username, pos.x, pos.y, pos.z, param0);
            },
            RemoveNode { pos } => {
                eprintln!("[{}] Block removed at ({}, {}, {})", 
                          self.username, pos[0], pos[1], pos[2]);
            },
            _ => {}
        }

        // Pass the packet to the auth handler
        self.auth.handle_pkt(&pkt).await;
    }

    pub async fn update_building(&mut self) {
        // Check if we're ready to build
        if self.position.is_none() || !self.state.ready {
            return;
        }
        
        // Check placement timing
        let now = Instant::now();
        if let Some(last) = self.last_placement {
            if now.duration_since(last) < self.placement_interval {
                return;
            }
        }
        
        // Check if we've reached our block limit
        if self.max_blocks > 0 && self.blocks_placed >= self.max_blocks as u32 {
            eprintln!("[{}] Reached block limit ({}), stopping building", self.username, self.max_blocks);
            return;
        }
        
        // Calculate next block position based on pattern
        let next_pos = self.calculate_next_block_position();
        
        // Move towards the building area if needed
        self.move_to_building_position(next_pos).await;
        
        // Place or dig a block
        if self.destructive_mode && self.blocks_placed % 3 == 0 {
            // Every 3rd action, dig instead of place
            self.dig_block(next_pos).await;
        } else {
            self.place_block(next_pos).await;
        }
        
        // Update placement timing
        self.last_placement = Some(now);
        self.blocks_placed += 1;
        
        // Progress the building pattern
        self.advance_building_pattern();
        
        // Status update every 10 blocks
        if self.blocks_placed % 10 == 0 {
            eprintln!("[{}] Building progress: {} blocks placed (pattern: {:?})", 
                      self.username, self.blocks_placed, self.building_pattern);
        }
    }
    
    fn calculate_next_block_position(&self) -> [i16; 3] {
        let base = [
            self.current_build_pos[0] as i16,
            self.current_build_pos[1] as i16,
            self.current_build_pos[2] as i16,
        ];
        
        match self.building_pattern {
            BuildingPattern::Tower => {
                // Build straight up
                [base[0], base[1] + self.build_direction as i16, base[2]]
            },
            BuildingPattern::Wall => {
                // Build horizontally in X direction
                [base[0] + self.build_direction as i16, base[1], base[2]]
            },
            BuildingPattern::Platform => {
                // Build a platform (5x5)
                let row = self.build_direction / 5;
                let col = self.build_direction % 5;
                [base[0] + col as i16 - 2, base[1], base[2] + row as i16 - 2]
            },
            BuildingPattern::Random => {
                // Random position within 10 blocks
                let mut rng = thread_rng();
                [
                    base[0] + rng.gen_range(-10..=10),
                    base[1] + rng.gen_range(-5..=5),
                    base[2] + rng.gen_range(-10..=10),
                ]
            },
            BuildingPattern::Spiral => {
                // Spiral upward
                let x = base[0] + (self.spiral_radius * self.spiral_angle.cos()) as i16;
                let z = base[2] + (self.spiral_radius * self.spiral_angle.sin()) as i16;
                let y = base[1] + (self.spiral_angle / (2.0 * std::f32::consts::PI)) as i16;
                [x, y, z]
            },
            BuildingPattern::House => {
                // Simple house: foundation, walls, roof
                self.calculate_house_position(base)
            },
        }
    }
    
    fn calculate_house_position(&self, base: [i16; 3]) -> [i16; 3] {
        let progress = self.house_progress;
        
        // House is 5x5x4 (width x depth x height)
        match progress {
            // Foundation (0-24): 5x5 floor
            0..=24 => {
                let row = (progress / 5) as i16;
                let col = (progress % 5) as i16;
                [base[0] + col - 2, base[1], base[2] + row - 2]
            },
            // Walls (25-84): 4 walls, 3 blocks high, with door opening
            25..=84 => {
                let wall_progress = progress - 25;
                let level = (wall_progress / 20) as i16; // 20 blocks per level
                let wall_block = wall_progress % 20;
                
                match wall_block {
                    // North wall (5 blocks)
                    0..=4 => [base[0] + wall_block as i16 - 2, base[1] + level + 1, base[2] - 2],
                    // East wall (3 blocks, skip corners)
                    5..=7 => [base[0] + 2, base[1] + level + 1, base[2] + (wall_block - 4) as i16 - 2],
                    // South wall (5 blocks, skip middle for door on ground level)
                    8..=12 => {
                        let pos = wall_block - 8;
                        if level == 0 && pos == 2 {
                            // Skip door position on ground level
                            [base[0] + pos as i16 - 2, base[1] + level + 1, base[2] + 2]
                        } else {
                            [base[0] + pos as i16 - 2, base[1] + level + 1, base[2] + 2]
                        }
                    },
                    // West wall (3 blocks, skip corners) 
                    _ => [base[0] - 2, base[1] + level + 1, base[2] + (wall_block - 12) as i16 - 2],
                }
            },
            // Roof (85+): simple flat roof
            _ => {
                let roof_progress = progress - 85;
                let row = (roof_progress / 5) as i16;
                let col = (roof_progress % 5) as i16;
                [base[0] + col - 2, base[1] + 4, base[2] + row - 2]
            },
        }
    }
    
    fn advance_building_pattern(&mut self) {
        match self.building_pattern {
            BuildingPattern::Tower => {
                self.build_direction += 1;
                // Reset after 20 blocks to build multiple towers
                if self.build_direction >= 20 {
                    self.build_direction = 0;
                    self.current_build_pos[0] += 3.0; // Move to next tower position
                }
            },
            BuildingPattern::Wall => {
                self.build_direction += 1;
                // Build a 20-block wall, then start a new row
                if self.build_direction >= 20 {
                    self.build_direction = 0;
                    self.current_build_pos[2] += 1.0; // Next row
                }
            },
            BuildingPattern::Platform => {
                self.build_direction += 1;
                // 5x5 = 25 blocks per platform
                if self.build_direction >= 25 {
                    self.build_direction = 0;
                    self.current_build_pos[1] += 1.0; // Next level
                }
            },
            BuildingPattern::Random => {
                // Nothing to advance for random
            },
            BuildingPattern::Spiral => {
                self.spiral_angle += 0.5; // Adjust for tighter/looser spiral
                self.spiral_radius += 0.1; // Expand spiral slowly
                if self.spiral_radius > 10.0 {
                    self.spiral_radius = 2.0; // Reset radius
                    self.current_build_pos[1] += 10.0; // Start new spiral higher up
                }
            },
            BuildingPattern::House => {
                self.house_progress += 1;
                // After finishing one house, move to next location
                if self.house_progress >= 110 { // Foundation + walls + roof
                    self.house_progress = 0;
                    self.current_build_pos[0] += 10.0; // Next house location
                }
            },
        }
    }
    
    async fn move_to_building_position(&mut self, target_pos: [i16; 3]) {
        if let Some(ref mut pos) = self.position {
            // Calculate where the player should be to place the block
            let player_target = [
                target_pos[0] as f32,
                target_pos[1] as f32,
                target_pos[2] as f32 - 2.0, // Stand 2 blocks away from target
            ];
            
            // Simple movement towards target position
            let dx = player_target[0] - pos.pos[0];
            let dz = player_target[2] - pos.pos[2];
            let distance = (dx * dx + dz * dz).sqrt();
            
            // Only move if we're far from the target
            if distance > 1.5 {
                let move_speed = 0.2;
                pos.pos[0] += dx.signum() * move_speed;
                pos.pos[2] += dz.signum() * move_speed;
                
                // Look towards the building area
                let yaw = f32::atan2(dx, dz).to_degrees();
                pos.yaw = Deg(yaw);
                
                // Send position update
                if let Err(e) = self.conn.send(&ToSrvPkt::PlayerPos(pos.clone())).await {
                    eprintln!("[{}] Failed to send position update: {}", self.username, e);
                }
            }
        }
    }
    
    async fn place_block(&mut self, target_pos: [i16; 3]) {
        if let Some(ref pos) = self.position {
            // Create the interaction packet to place a block
            let pointed_thing = PointedThing::Node {
                under: [target_pos[0], target_pos[1] - 1, target_pos[2]].into(), // Block we're placing on
                above: target_pos.into(), // Position where we want to place the block
            };
            
            let interact_packet = ToSrvPkt::Interact {
                action: Interaction::Place,
                item_slot: self.block_slot,
                pointed: pointed_thing,
                pos: pos.clone(),
            };
            
            match self.conn.send(&interact_packet).await {
                Ok(_) => {
                    eprintln!("[{}] Placed block at ({}, {}, {}) [slot {}]", 
                              self.username, target_pos[0], target_pos[1], target_pos[2], self.block_slot);
                },
                Err(e) => {
                    eprintln!("[{}] Failed to place block: {}", self.username, e);
                }
            }
        }
    }
    
    async fn dig_block(&mut self, target_pos: [i16; 3]) {
        if let Some(ref pos) = self.position {
            // Create the interaction packet to dig a block
            let pointed_thing = PointedThing::Node {
                under: target_pos.into(),
                above: [target_pos[0], target_pos[1] + 1, target_pos[2]].into(),
            };
            
            // Start digging
            let dig_start_packet = ToSrvPkt::Interact {
                action: Interaction::Dig,
                item_slot: self.block_slot,
                pointed: pointed_thing.clone(),
                pos: pos.clone(),
            };
            
            // Finish digging (simulate instant digging)
            let dig_complete_packet = ToSrvPkt::Interact {
                action: Interaction::Dug,
                item_slot: self.block_slot,
                pointed: pointed_thing,
                pos: pos.clone(),
            };
            
            match self.conn.send(&dig_start_packet).await {
                Ok(_) => {
                    // Wait a tiny bit then send completion
                    tokio::time::sleep(Duration::from_millis(50)).await;
                    if let Err(e) = self.conn.send(&dig_complete_packet).await {
                        eprintln!("[{}] Failed to complete digging: {}", self.username, e);
                    } else {
                        eprintln!("[{}] Dug block at ({}, {}, {})", 
                                  self.username, target_pos[0], target_pos[1], target_pos[2]);
                    }
                },
                Err(e) => {
                    eprintln!("[{}] Failed to start digging: {}", self.username, e);
                }
            }
        }
    }
    
    async fn give_blocks(&mut self) {
        // Try to give ourselves blocks using chat commands (if we have privileges)
        let give_command = format!("/give {} default:cobble 999", self.username);
        
        let chat_packet = ToSrvPkt::ChatMsg {
            msg: give_command,
        };
        
        if let Err(e) = self.conn.send(&chat_packet).await {
            eprintln!("[{}] Failed to send give command: {}", self.username, e);
        } else {
            eprintln!("[{}] Requested blocks via /give command", self.username);
        }
    }
}

#[tokio::main]
async fn main() {
    let Args {
        address,
        quit_after_seconds,
        username,
        password,
        force_lowercase,
        register,
        auto_register,
        pattern,
        speed,
        max_blocks,
        start_x,
        start_y,
        start_z,
        block_slot,
        destructive,
    } = Args::parse();

    // Use lowercase username if force_lowercase is true
    let username = if force_lowercase {
        username.to_lowercase()
    } else {
        username
    };
    
    // Parse building pattern
    let building_pattern = match pattern.to_lowercase().as_str() {
        "tower" => BuildingPattern::Tower,
        "wall" => BuildingPattern::Wall,
        "platform" => BuildingPattern::Platform,
        "random" => BuildingPattern::Random,
        "spiral" => BuildingPattern::Spiral,
        "house" => BuildingPattern::House,
        _ => {
            eprintln!("Unknown building pattern: {}, using tower", pattern);
            BuildingPattern::Tower
        }
    };
    
    eprintln!("BlockBot connecting to {} as user '{}'", &address, &username);
    eprintln!("Building pattern: {:?}, speed: {}s, max blocks: {}", building_pattern, speed, max_blocks);
    eprintln!("Starting position: ({}, {}, {}), block slot: {}", start_x, start_y, start_z, block_slot);
    if destructive {
        eprintln!("Destructive mode enabled - will also dig blocks");
    }
    
    let (tx, mut rx, worker) = mt_net::connect(&address).await.unwrap();

    // Create shared running state
    let running = Arc::new(AtomicBool::new(true));
    let running_clone = running.clone();

    let mut bot = BlockBot {
        auth: Auth::new(tx.clone(), username.clone(), password.clone(), "en_US", register),
        conn: tx,
        state: BotState {
            connected: false,
            authenticated: false,
            ready: false,
        },
        auto_register,
        tried_register: false,
        username,
        password,
        position: None,
        building_pattern,
        placement_interval: Duration::from_secs_f32(speed),
        last_placement: None,
        running,
        
        blocks_placed: 0,
        max_blocks,
        current_build_pos: [start_x, start_y, start_z],
        build_direction: 0,
        block_slot,
        destructive_mode: destructive,
        
        spiral_radius: 2.0,
        spiral_angle: 0.0,
        house_progress: 0,
    };

    let worker = tokio::spawn(worker.run());

    let mut quit_sleep: Option<Pin<Box<Sleep>>> = quit_after_seconds.and_then(|x| {
        if x >= 0.0 {
            Some(Box::pin(sleep(Duration::from_secs_f32(x))))
        } else {
            None
        }
    });

    // Create a ticker for building updates
    let mut building_interval = tokio::time::interval(Duration::from_millis(100));

    // Request blocks after authentication
    let mut requested_blocks = false;

    loop {
        tokio::select! {
            pkt = rx.recv() => match pkt {
                None => break,
                Some(Err(e)) => eprintln!("{e}"),
                Some(Ok(pkt)) => {
                    bot.handle_pkt(pkt).await;
                }
            },
            _ = bot.auth.poll() => {
                bot.state.authenticated = true;
                bot.conn
                    .send(&ToSrvPkt::CltReady {
                        major: 0,
                        minor: 0,
                        patch: 0,
                        reserved: 0,
                        version: "https://github.com/LizzyFleckenstein03/blockbot".into(),
                        formspec: 4,
                    })
                    .await
                    .unwrap();
                
                bot.state.ready = true;
                eprintln!("[{}] BlockBot is ready and authenticated! Starting to build...", bot.username);
            },
            _ = building_interval.tick() => {
                // Update building logic
                bot.update_building().await;
                
                // Try to get blocks if we haven't yet and we're ready
                if bot.state.ready && !requested_blocks {
                    bot.give_blocks().await;
                    requested_blocks = true;
                }
            },
            Some(_) = OptionFuture::from(quit_sleep.as_mut()) => {
                eprintln!("[{}] Quitting after time limit... (placed {} blocks)", 
                          bot.username, bot.blocks_placed);
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            },
            _ = tokio::signal::ctrl_c() => {
                eprintln!("[{}] Received Ctrl+C, shutting down... (placed {} blocks)", 
                          bot.username, bot.blocks_placed);
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            }
        }
    }

    worker.await.unwrap();
}