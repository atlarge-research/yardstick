use clap::Parser;
use futures_util::future::OptionFuture;
use mt_auth::Auth;
use mt_net::{self, CltSender, Key, PlayerPos, ReceiverExt, SenderExt, ToCltPkt, ToSrvPkt};
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
#[clap(version, about = "A simple walking bot for Minetest", long_about = None)]
struct Args {
    /// Server address. Format: address:port
    #[clap(value_parser)]
    address: String,

    /// Quit after QUIT_AFTER seconds
    #[clap(short, long, value_parser)]
    quit_after_seconds: Option<f32>,

    /// Player name
    #[clap(short, long, value_parser, default_value = "walkbot")]
    username: String,

    /// Password
    #[clap(short, long, value_parser, default_value = "walkbot123")]
    password: String,
    
    /// Force using lowercase username for authentication
    #[clap(long, value_parser, default_value_t = false)]
    force_lowercase: bool,
    
    /// Register a new account (if false, tries to log in to existing account)
    #[clap(long, value_parser, default_value_t = false)]
    register: bool,
    
    /// Auto register: if login fails, try registration (--auto-register implies --register=false initially)
    #[clap(long, value_parser, default_value_t = true)]
    auto_register: bool,

    /// Movement mode: random (default), circular, static, or follow
    #[clap(short, long, value_parser, default_value = "random")]
    mode: String,

    /// Movement speed in seconds between direction changes
    #[clap(short, long, value_parser, default_value_t = 2.0)]
    speed: f32,
    
    /// Target X coordinate for "follow" mode
    #[clap(long, value_parser)]
    target_x: Option<f32>,
    
    /// Target Y coordinate for "follow" mode
    #[clap(long, value_parser)]
    target_y: Option<f32>,
    
    /// Target Z coordinate for "follow" mode
    #[clap(long, value_parser)]
    target_z: Option<f32>,
}

// Instead of using EnumSet for the bot state, use simple boolean flags
pub struct BotState {
    pub connected: bool,
    pub authenticated: bool,
    pub ready: bool,
}

pub enum MovementMode {
    Random,
    Circular,
    Static,
    Follow {
        target_x: f32,
        target_y: f32,
        target_z: f32,
    },
}

pub struct WalkBot {
    pub conn: CltSender,
    pub auth: Auth,
    pub state: BotState,
    pub auto_register: bool,
    pub tried_register: bool,
    pub username: String, 
    pub password: String,
    pub position: Option<PlayerPos>,
    pub movement_mode: MovementMode,
    pub change_interval: Duration,
    pub yaw: f32,
    pub last_movement: Option<Instant>,
    pub running: Arc<AtomicBool>,
}

// Helper function for atan2 that returns the correct angle for our coordinate system
fn atan2f32(y: f32, x: f32) -> f32 {
    if x == 0.0 {
        if y > 0.0 {
            return std::f32::consts::FRAC_PI_2;
        } else if y < 0.0 {
            return -std::f32::consts::FRAC_PI_2;
        } else {
            return 0.0; // undefined, but return 0
        }
    }
    
    let mut angle = y.atan2(x);
    if angle < 0.0 {
        angle += 2.0 * std::f32::consts::PI;
    }
    angle
}

impl WalkBot {
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
                    // Initialize the position with the server's position but fix Y to 8.5
                    // to ensure the bot doesn't spawn in the air
                    let mut fixed_pos = *pos;
                    fixed_pos[1] = 8.5; // Set Y coordinate to 8.5
                    
                    self.position = Some(PlayerPos {
                        pos: fixed_pos,
                        vel: [0.0, 0.0, 0.0].into(),
                        pitch: Deg(0.0),
                        yaw: Deg(0.0),
                        keys: EnumSet::new(),
                        fov: Rad(1.0),
                        wanted_range: 10,
                    });
                    self.last_movement = Some(Instant::now());
                    eprintln!("Initial position set: ({}, {}, {}) (Y fixed to 8.5)", 
                              fixed_pos[0], fixed_pos[1], fixed_pos[2]);
                }
            },
            _ => {}
        }

        // Pass the packet to the auth handler
        self.auth.handle_pkt(&pkt).await;
    }
    async fn send_position_update(&mut self) {
        if let Some(ref pos) = self.position {
            // Send current position to server
            let _ = self.conn.send(&ToSrvPkt::PlayerPos(pos.clone())).await;
        }
    }
    pub async fn update_movement(&mut self) {
        // if self.position.is_none() || !self.state.ready {
        //     return;
        // }
        
        let now = Instant::now();
        // if self.last_movement.is_some() && now.duration_since(self.last_movement.unwrap()) < self.change_interval {
        //     return;
        // }
        
        let mut keys = EnumSet::new();
        // let mut rng = thread_rng(); // Moved into MovementMode::Random
        
        match self.movement_mode {
            MovementMode::Random => {
                let mut rng = thread_rng(); // Initialize rng only when needed
                // Randomly decide movement direction
                if rng.gen_bool(0.7) {
                    keys.insert(Key::Forward);
                } else if rng.gen_bool(0.3) {
                    keys.insert(Key::Backward);
                }
                
                if rng.gen_bool(0.4) {
                    keys.insert(Key::Left);
                } else if rng.gen_bool(0.4) {
                    keys.insert(Key::Right);
                }
                
                if rng.gen_bool(0.2) {
                    keys.insert(Key::Jump);
                }
                
                // Random rotation
                self.yaw = (self.yaw + rng.gen_range(-0.5..0.5)) % 360.0;
                if self.yaw < 0.0 {
                    self.yaw += 360.0;
                }
            },
            MovementMode::Circular => {
                // Walk in a circle
                keys.insert(Key::Forward);
                // Add a slight sideways motion to make the circle smoother
                if (self.yaw % 90.0) < 45.0 {
                    keys.insert(Key::Left);
                } else {
                    keys.insert(Key::Right);
                }
                self.yaw = (self.yaw + 3.0) % 360.0; // Slower rotation for a wider circle
            },
            MovementMode::Static => {
                // Stand in place, just look around
                self.yaw = (self.yaw + 10.0) % 360.0;
            },
            MovementMode::Follow { target_x, target_y, target_z } => {
                // Calculate direction to target
                if let Some(pos) = &self.position {
                    let dx = target_x - pos.pos[0];
                    let dy = target_y - pos.pos[1];
                    let dz = target_z - pos.pos[2];

                    // Calculate the standard mathematical angle with atan2
                    // In standard atan2: 0° is east (+X), 90° is north (+Z)
                    let math_angle = f32::atan2(dz, dx).to_degrees();
                    
                    // Calculate angle to target in radians for horizontal movement
                    // In Minetest: 0° is north (+Z), 90° is east (+X), 180° is south (-Z), 270° is west (-X)
                    // Use atan2 to find the angle, but we need to adjust for Minetest's coordinate system
                    // atan2 takes (y, x) but we need to reverse the coordinates since Minetest's Z is like
                    // the mathematical Y axis (north/south) and X is like mathematical X (east/west)
                    let target_angle = (90.0 - math_angle) % 360.0;

                    let target_angle = if target_angle < 0.0 { 
                        target_angle + 360.0 
                    } else { 
                        target_angle 
                    };
        
                    // Calculate angle difference
                    let mut angle_diff = target_angle - self.yaw;
                    if angle_diff > 180.0 {
                        angle_diff -= 360.0;
                    } else if angle_diff < -180.0 {
                        angle_diff += 360.0;
                    }
                    
                    // Adjust yaw to face target
                    let rotation_speed = 20.0; // Increased from 5.0 to 20.0 for faster rotation
                    if angle_diff.abs() > rotation_speed {
                        if angle_diff > 0.0 {
                            self.yaw = (self.yaw + rotation_speed) % 360.0;
                        } else {
                            self.yaw = (self.yaw - rotation_speed + 360.0) % 360.0;
                        }
                    } else {
                        self.yaw = target_angle;
                    }
                    let _distance = (dx.powi(2) + dy.powi(2) + dz.powi(2)).sqrt();
        
                    // Debug the direction calculation
                    eprintln!("Target: ({:.1}, {:.1}, {:.1}), Current: ({:.1}, {:.1}, {:.1})", 
                            target_x, target_y, target_z, pos.pos[0], pos.pos[1], pos.pos[2]);
                    eprintln!("Direction vector: dx={:.1}, dz={:.1}, Target angle: {:.1}°, Current yaw: {:.1}°", 
                            dx, dz, target_angle, self.yaw);


                    // Calculate if we need to jump or sneak based on Y difference
                    let y_diff = target_y - pos.pos[1];
                    if y_diff > 1.0 && angle_diff.abs() < 45.0 {
                        // Target is significantly higher, try jumping
                        keys.insert(Key::Jump);
                    } else if y_diff < -1.0 && angle_diff.abs() < 45.0 {
                        // Target is significantly lower
                        keys.insert(Key::Sneak);
                    }
                    
                    // Almost always move forward regardless of facing direction
                    // Only avoid moving if we're completely backwards (angle diff > 120 degrees)
                    if angle_diff.abs() < 120.0 {  // Increased from 90.0 to 120.0 for even more aggressive movement
                        keys.insert(Key::Forward);
                         // Add steering assistance
                        if angle_diff > 15.0 {
                            keys.insert(Key::Right);
                        } else if angle_diff < -15.0 {
                            keys.insert(Key::Left);
                        }
                        // Add debug info about movement direction
                        eprintln!("Moving toward target: ({:.1}, {:.1}, {:.1}), current: ({:.1}, {:.1}, {:.1}), yaw: {:.1}°, distance: (dx={:.1}, dy={:.1}, dz={:.1})", 
                                   target_x, target_y, target_z, pos.pos[0], pos.pos[1], pos.pos[2], self.yaw, dx, dy, dz);
                        
                    } else {
                        eprintln!("Rotating to face target: current yaw: {:.1}°, target angle: {:.1}°, diff: {:.1}°", 
                                   self.yaw, target_angle, angle_diff);
                    }
                    
                    // Calculate distance to target (3D distance including Y)
                    let _distance = (dx.powi(2) + dy.powi(2) + dz.powi(2)).sqrt();

                    if _distance < 1.0 {
                        // Near the target, slow down
                        eprintln!("Near target position ({:.1}, {:.1}, {:.1}), distance: {:.2}", 
                                  target_x, target_y, target_z, _distance);
                    }
                }
            }
        }
        // let move_speed = 300; // Increased movement speed per update

//         let move_speed = match &self.movement_mode {
//     MovementMode::Follow { target_x, target_y, target_z } => {
//         if let Some(pos) = &self.position {
//             let dx = target_x - pos.pos[0];
//             let dz = target_z - pos.pos[2];
//             let distance_squared = dx.powi(2) + dz.powi(2);
            
//             if distance_squared < 9.0 { // Within 3 units of target
//                 0.3 // Slower but still quick when close
//             } else {
//                 1.0 // Fast movement when far away
//             }
//         } else {
//             0.5 // Default if position is unknown
//         }
//     },
//     _ => 0.5 // Standard speed for other movement modes
// };

        
        // Apply movement to current position
        if let Some(ref mut pos) = self.position {
            // Check if we're in Follow mode with a specific target_y
            let default_height = match &self.movement_mode {
                MovementMode::Follow { target_x: _, target_y, target_z: _ } => *target_y,
                _ => 8.5 // Default Y position for other modes
            };
            
            // Ensure the bot stays at the right height unless we're actively trying to reach a different Y
            if (pos.pos[1] - default_height).abs() > 0.5 {
                pos.pos[1] = default_height;
                eprintln!("Setting Y position to {:.1}", default_height);
            }
            
            // Update position based on movement keys and direction
            let move_speed = 0.1; // Increased movement speed per update
            let yaw_rad = self.yaw * std::f32::consts::PI / 180.0; // Convert yaw to radians
            
            // Calculate movement vector based on keys
            let mut dx = 0.0;
            let mut dy = 0.0;
            let mut dz = 0.0;
            
            // In Minetest, 0° yaw is north (+Z), 90° is east (+X), 180° is south (-Z), 270° is west (-X)
            // We need to convert the yaw angle to the appropriate movement vector
            
            if keys.contains(Key::Forward) {
                // Forward is in the direction of yaw
                // In Minetest: 0° is north (+Z), 90° is east (+X), 180° is south (-Z), 270° is west (-X)
                dx += move_speed * yaw_rad.sin(); // East/West movement
                dz += move_speed * yaw_rad.cos(); // North/South movement
            }
            if keys.contains(Key::Backward) {
                // Backward is opposite of forward
                dx -= move_speed * yaw_rad.sin();
                dz -= move_speed * yaw_rad.cos();
            }
            if keys.contains(Key::Left) {
                // Left is 90° counter-clockwise from forward
                dx -= move_speed * yaw_rad.cos() * 0.6;
                dz -= move_speed * yaw_rad.sin() * 0.6;
            }
            if keys.contains(Key::Right) {
                // Right is 90° clockwise from forward
                dx += move_speed * yaw_rad.cos() * 0.6;
                dz += move_speed * yaw_rad.sin() * 0.6;
            }
            
            // Handle jump and sneak for Y-axis movement
            if keys.contains(Key::Jump) {
                dy += move_speed * 0.5; // Move up more slowly than horizontal movement
            }
            if keys.contains(Key::Sneak) {
                dy -= move_speed * 0.5; // Move down more slowly
            }
            
            // Apply movement to position
            pos.pos[0] += dx;
            pos.pos[1] += dy; // Apply Y-axis movement
            pos.pos[2] += dz;
            
            // Set movement keys and yaw
            pos.keys = keys;
            pos.yaw = Deg(self.yaw);
            
            // Send position update to server
            self.conn.send(&ToSrvPkt::PlayerPos(pos.clone())).await.unwrap();
            
            // Debug output to show movement with direction indicators
            eprintln!("Position updated: ({:.2}, {:.2}, {:.2}), Yaw: {:.1}°, Movement: dx={:.3}, dz={:.3}", 
                pos.pos[0], pos.pos[1], pos.pos[2], self.yaw, dx, dz);
        }
        
        self.last_movement = Some(now);
    }

    // No longer need this method as we're running movement updates in the main loop
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
        mode,
        speed,
        target_x,
        target_y,
        target_z,
    } = Args::parse();

    // Use lowercase username if force_lowercase is true
    let username = if force_lowercase {
        username.to_lowercase()
    } else {
        username
    };
    
    // Parse movement mode
    let movement_mode = match mode.to_lowercase().as_str() {
        "random" => MovementMode::Random,
        "circular" => MovementMode::Circular,
        "static" => MovementMode::Static,
        "follow" => {
            // Need target coordinates for follow mode
            let target_x = target_x.unwrap_or_else(|| {
                eprintln!("Missing --target-x for follow mode, using default 0.0");
                0.0
            });
            let target_y = target_y.unwrap_or_else(|| {
                eprintln!("Missing --target-y for follow mode, using default 8.5");
                8.5
            });
            let target_z = target_z.unwrap_or_else(|| {
                eprintln!("Missing --target-z for follow mode, using default 0.0");
                0.0
            });
            eprintln!("Follow mode: moving to target coordinates ({}, {}, {})", target_x, target_y, target_z);
            MovementMode::Follow { target_x, target_y, target_z }
        },
        _ => {
            eprintln!("Unknown movement mode: {}, using random", mode);
            MovementMode::Random
        }
    };
    
    eprintln!("Connecting to {} as user '{}' (register: {}, auto_register: {})", 
              &address, &username, register, auto_register);
    eprintln!("Movement mode: {}, change interval: {} seconds", mode, speed);
    
    let (tx, mut rx, worker) = mt_net::connect(&address).await.unwrap();

    // Create shared running state
    let running = Arc::new(AtomicBool::new(true));
    let running_clone = running.clone();

    let mut bot = WalkBot {
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
        movement_mode,
        change_interval: Duration::from_secs_f32(speed),
        yaw: 0.0,
        last_movement: None,
        running,
    };

    let worker = tokio::spawn(worker.run());
    
    // Instead of using a mutex to share the bot instance, we'll run the movement loop
    // directly in the main loop to avoid borrowing issues

    let mut quit_sleep: Option<Pin<Box<Sleep>>> = quit_after_seconds.and_then(|x| {
        if x >= 0.0 {
            Some(Box::pin(sleep(Duration::from_secs_f32(x))))
        } else {
            None
        }
    });

    // Create a ticker for the movement updates
    let mut movement_interval = tokio::time::interval(Duration::from_micros(30000));

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
                        version: "https://github.com/LizzyFleckenstein03/texmodbot".into(),
                        formspec: 4,
                    })
                    .await
                    .unwrap();
                
                // Now we're ready to start sending movement updates
                bot.state.ready = true;
                eprintln!("Bot is ready and authenticated!");
            },
            _ = movement_interval.tick() => {
                // Update movement directly in the main loop
                bot.update_movement().await;
                // bot.send_position_update().await;
            },
            Some(_) = OptionFuture::from(quit_sleep.as_mut()) => {
                eprintln!("Quitting after time limit...");
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            },
            _ = tokio::signal::ctrl_c() => {
                eprintln!("Received Ctrl+C, shutting down...");
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            }
        }
    }

    worker.await.unwrap();
}
