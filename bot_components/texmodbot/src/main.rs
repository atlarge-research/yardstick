use clap::Parser;
use enumset::{EnumSet, EnumSetType};
use futures_util::future::OptionFuture;
use mt_auth::Auth;
use mt_net::{CltSender, ReceiverExt, SenderExt, ToCltPkt, ToSrvPkt};
use std::collections::HashSet;
use std::pin::Pin;
use std::time::Duration;
use tokio::time::{sleep, Sleep};

#[derive(Parser, Debug)]
#[clap(version, about, long_about = None)]
struct Args {
    /// Server address. Format: address:port
    #[clap(value_parser)]
    address: String,

    /// Quit after QUIT_AFTER seconds
    #[clap(short, long, value_parser)]
    quit_after_seconds: Option<f32>,

    /// Quit after having received item and node definitions
    #[clap(short = 'Q', long, value_parser, default_value_t = false)]
    quit_after_defs: bool,

    /// Player name
    #[clap(short, long, value_parser, default_value = "texmodbot")]
    username: String,

    /// Password
    #[clap(short, long, value_parser, default_value = "owo")]
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
}

#[derive(EnumSetType)]
enum DefType {
    NodeDef,
    ItemDef,
}

struct Bot {
    conn: CltSender,
    quit_after_defs: bool,
    auth: Auth,
    pending: EnumSet<DefType>,
    has: HashSet<String>,
    auto_register: bool,
    tried_register: bool,
    username: String, 
    password: String,
}

impl Bot {
    fn got_def(&mut self, def: DefType) {
        self.pending.remove(def);
        if self.quit_after_defs && self.pending.is_empty() {
            self.conn.close()
        }
    }
    
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

    async fn handle_pkt(&mut self, pkt: ToCltPkt) {
        use ToCltPkt::*;

        self.auth.handle_pkt(&pkt).await;

        let mut print_texture = |tex: &String| {
            if !tex.is_empty() && self.has.insert(tex.clone()) {
                println!("{tex}");
            }
        };

        fn print_texmod(tex: &String, print_texture: &mut impl FnMut(&String)) {
            if !tex.is_empty() {
                print_texture(&format!("blank.png{tex}"));
            }
        }

        let print_obj_msg = |msg: &mt_net::ObjMsg| {
            use mt_net::ObjMsg::*;
            match msg {
                TextureMod { texture_mod } => print_texmod(texture_mod, &mut print_texture),
                Props(props) => {
                    props.textures.iter().for_each(&mut print_texture);
                    print_texmod(&props.dmg_texture_mod, &mut print_texture);
                }
                _ => {}
            }
        };

        match pkt {
            NodeDefs(defs) => {
                defs.0
                    .values()
                    .flat_map(|def| {
                        std::iter::empty()
                            .chain(&def.tiles)
                            .chain(&def.special_tiles)
                            .chain(&def.overlay_tiles)
                    })
                    .map(|tile| &tile.texture.name)
                    .for_each(print_texture);

                self.got_def(DefType::NodeDef);
            }
            ItemDefs { defs, .. } => {
                defs.iter()
                    .flat_map(|def| {
                        [
                            &def.inventory_image,
                            &def.wield_image,
                            &def.inventory_overlay,
                            &def.wield_overlay,
                        ]
                    })
                    .for_each(print_texture);

                self.got_def(DefType::ItemDef);
            }
            ObjMsgs { msgs } => {
                msgs.iter().map(|x| &x.msg).for_each(print_obj_msg);
            }
            ObjRemoveAdd { add, .. } => {
                add.iter()
                    .flat_map(|x| x.init_data.msgs.iter())
                    .map(|x| &x.0)
                    .for_each(print_obj_msg);
            }
            Kick(reason) => {
                eprintln!("kicked: {reason}");
                
                // If we get kicked with "wrong password" and auto_register is true,
                // we should try to register instead
                if format!("{reason}").contains("wrong password") && 
                   self.auto_register && 
                   !self.tried_register {
                    eprintln!("Auto-register: Login failed with wrong password. Trying to register a new account...");
                    self.tried_register = true;
                    self.try_register().await;
                }
            }
            _ => {}
        }
    }
}

#[tokio::main]
async fn main() {
    let Args {
        address,
        quit_after_seconds,
        quit_after_defs,
        username,
        password,
        force_lowercase,
        register,
        auto_register,
    } = Args::parse();

    // Use lowercase username if force_lowercase is true
    let username = if force_lowercase {
        username.to_lowercase()
    } else {
        username
    };
    
    eprintln!("Connecting to {} as user '{}' (register: {}, auto_register: {})", 
              &address, &username, register, auto_register);
    
    let (tx, mut rx, worker) = mt_net::connect(&address).await.unwrap();

    let mut bot = Bot {
        auth: Auth::new(tx.clone(), username.clone(), password.clone(), "en_US", register),
        conn: tx,
        quit_after_defs,
        pending: EnumSet::all(),
        has: HashSet::new(),
        auto_register,
        tried_register: false,
        username,
        password,
    };

    let worker = tokio::spawn(worker.run());

    let mut quit_sleep: Option<Pin<Box<Sleep>>> = quit_after_seconds.and_then(|x| {
        if x >= 0.0 {
            Some(Box::pin(sleep(Duration::from_secs_f32(x))))
        } else {
            None
        }
    });

    loop {
        tokio::select! {
            pkt = rx.recv() => match pkt {
                None => break,
                Some(Err(e)) => eprintln!("{e}"),
                Some(Ok(pkt)) => bot.handle_pkt(pkt).await,
            },
            _ = bot.auth.poll() => {
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
            }
            Some(_) = OptionFuture::from(quit_sleep.as_mut()) => {
                bot.conn.close();
            }
            _ = tokio::signal::ctrl_c() => {
                bot.conn.close();
            }
        }
    }

    worker.await.unwrap();
}
