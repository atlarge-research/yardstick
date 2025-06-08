mod walkbot;
use std::pin::Pin;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use tokio::time::{sleep, Sleep};
use futures_util::future::OptionFuture;
use walkbot::{WalkBot, BotState, MovementMode};
use mt_auth::Auth;
use mt_net::{self, ToSrvPkt};
use mt_net::ReceiverExt;
use mt_net::SenderExt;

/// Simple config for each bot instance
struct BotConfig {
    address: String,
    username: String,
    password: String,
    movement_mode: MovementMode,
    speed: f32,
    register: bool,
    auto_register: bool,
    quit_after_seconds: Option<f32>,
}

#[tokio::main]
async fn main() {
    // Example: spawn 3 bots with different usernames and random movement
    let bot_configs = vec![
        BotConfig {
            address: "127.0.0.1:30000".to_string(),
            username: "walkbot1".to_string(),
            password: "walkbot123".to_string(),
            movement_mode: MovementMode::Random,
            speed: 2.0,
            register: false,
            auto_register: true,
            quit_after_seconds: Some(60.0),
        },
        BotConfig {
            address: "127.0.0.1:30000".to_string(),
            username: "walkbot2".to_string(),
            password: "walkbot123".to_string(),
            movement_mode: MovementMode::Circular,
            speed: 2.0,
            register: false,
            auto_register: true,
            quit_after_seconds: Some(60.0),
        },
        BotConfig {
            address: "127.0.0.1:30000".to_string(),
            username: "walkbot3".to_string(),
            password: "walkbot123".to_string(),
            movement_mode: MovementMode::Static,
            speed: 2.0,
            register: false,
            auto_register: true,
            quit_after_seconds: Some(60.0),
        },
    ];

    let mut handles = Vec::new();
    for config in bot_configs {
        let handle = tokio::spawn(run_bot(config));
        handles.push(handle);
    }

    // Wait for all bots to finish
    for handle in handles {
        let _ = handle.await;
    }
}

async fn run_bot(config: BotConfig) {
    let (tx, mut rx, worker) = match mt_net::connect(&config.address).await {
        Ok(res) => res,
        Err(e) => {
            eprintln!("[{}] Failed to connect: {}", config.username, e);
            return;
        }
    };

    let running = Arc::new(AtomicBool::new(true));
    let running_clone = running.clone();

    let mut bot = WalkBot {
        auth: Auth::new(tx.clone(), config.username.clone(), config.password.clone(), "en_US", config.register),
        conn: tx,
        state: BotState {
            connected: false,
            authenticated: false,
            ready: false,
        },
        auto_register: config.auto_register,
        tried_register: false,
        username: config.username.clone(),
        password: config.password.clone(),
        position: None,
        movement_mode: config.movement_mode,
        change_interval: Duration::from_secs_f32(config.speed),
        yaw: 0.0,
        last_movement: None,
        running: running.clone(),
    };

    let worker = tokio::spawn(worker.run());

    let mut quit_sleep: Option<Pin<Box<Sleep>>> = config.quit_after_seconds.and_then(|x| {
        if x >= 0.0 {
            Some(Box::pin(sleep(Duration::from_secs_f32(x))))
        } else {
            None
        }
    });

    let mut movement_interval = tokio::time::interval(Duration::from_micros(30000));

    loop {
        tokio::select! {
            pkt = rx.recv() => match pkt {
                None => break,
                Some(Err(e)) => eprintln!("[{}] {}", config.username, e),
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
                bot.state.ready = true;
                eprintln!("[{}] Bot is ready and authenticated!", config.username);
            },
            _ = movement_interval.tick() => {
                bot.update_movement().await;
            },
            Some(_) = OptionFuture::from(quit_sleep.as_mut()) => {
                eprintln!("[{}] Quitting after time limit...", config.username);
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            },
            _ = tokio::signal::ctrl_c() => {
                eprintln!("[{}] Received Ctrl+C, shutting down...", config.username);
                running_clone.store(false, Ordering::Relaxed);
                bot.conn.close();
                break;
            }
        }
    }
    let _ = worker.await;
}
