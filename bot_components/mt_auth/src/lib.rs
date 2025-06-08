use mt_net::{CltSender, SenderExt, ToCltPkt, ToSrvPkt};
use rand::RngCore;
use sha2::Sha256;
use srp::{client::SrpClient, groups::G_2048};
use std::time::Duration;
use tokio::time::{interval, Interval};

enum AuthState {
    Init(ToSrvPkt, Interval),
    Verify(Vec<u8>, SrpClient<'static, Sha256>),
    Done(bool),
}

pub struct Auth {
    tx: CltSender,
    state: AuthState,
    username: String,
    password: String,
    lang: String,
    register: bool,
}

impl Auth {
    pub fn new(
        tx: CltSender,
        username: impl Into<String>,
        password: impl Into<String>,
        lang: impl Into<String>,
        register: bool,
    ) -> Self {
        // Convert username to String and keep both original and lowercase versions
        let username_original = username.into();
        let username_lowercase = username_original.to_lowercase();
        
        Self {
            tx,
            state: AuthState::Init(
                ToSrvPkt::Init {
                    serialize_version: 29,
                    proto_version: 40..=40,
                    player_name: username_lowercase.clone(),
                    send_full_item_meta: false,
                },
                interval(Duration::from_millis(100)),
            ),
            username: username_lowercase,
            password: password.into(),
            lang: lang.into(),
            register,
        }
    }

    pub fn username(&self) -> &str {
        &self.username
    }

    pub fn password(&self) -> &str {
        &self.password
    }

    pub fn lang(&self) -> &str {
        &self.lang
    }

    pub fn mut_init_pkt(&mut self) -> Option<&mut ToSrvPkt> {
        if let AuthState::Init(pkt, _) = &mut self.state {
            Some(pkt)
        } else {
            None
        }
    }

    pub async fn poll(&mut self) {
        match &mut self.state {
            AuthState::Init(pkt, interval) => {
                loop {
                    // cancel safety: since init pkt is unreliable, cancelation is not an issue
                    self.tx.send(pkt).await.unwrap();
                    interval.tick().await;
                }
            }
            AuthState::Verify(_, _) | AuthState::Done(false) => futures::future::pending().await,
            AuthState::Done(unconsumed) => {
                *unconsumed = false;
            }
        }
    }

    pub async fn handle_pkt(&mut self, pkt: &ToCltPkt) {
        use ToCltPkt::*;
        match pkt {
            Hello {
                auth_methods,
                username: name,
                ..
            } => {
                use mt_net::AuthMethod;

                if !matches!(self.state, AuthState::Init(_, _)) {
                    return;
                }

                let srp = SrpClient::<Sha256>::new(&G_2048);

                let mut rand_bytes = vec![0; 32];
                rand::thread_rng().fill_bytes(&mut rand_bytes);

                // Only use the server-provided username if it's not empty
                if &self.username != name {
                    eprintln!("Warning: username mismatch: expected '{}', got '{}'", self.username, name);
                    
                    // If server sent an empty username, keep our original username
                    if name.is_empty() {
                        eprintln!("Server returned empty username, keeping original username '{}'", self.username);
                    } else {
                        eprintln!("Username case: original='{}', server='{}'", self.username.to_lowercase(), name.to_lowercase());
                        // Only use the server-provided username if it's not empty
                        self.username = name.clone();
                    }
                }

                // Debug info about available auth methods
                eprintln!("Server supports auth methods: {:?}", auth_methods);
                
                // First time registering: use FirstSrp if available
                if self.register && auth_methods.contains(AuthMethod::FirstSrp) {
                    eprintln!("Registering new account for '{}' using FirstSrp", self.username);
                    let verifier = srp.compute_verifier(
                        self.username.to_lowercase().as_bytes(),
                        self.password.as_bytes(),
                        &rand_bytes,
                    );

                    self.tx
                        .send(&ToSrvPkt::FirstSrp {
                            salt: rand_bytes,
                            verifier,
                            empty_passwd: self.password.is_empty(),
                        })
                        .await
                        .unwrap();

                    self.state = AuthState::Done(false);
                // Existing account: use Srp if available
                } else if !self.register && auth_methods.contains(AuthMethod::Srp) {
                    eprintln!("Logging in as existing user '{}' using Srp", self.username);
                    
                    // Ensure we're using the original username for authentication
                    let username_lower = self.username.to_lowercase();
                    let username_bytes = username_lower.as_bytes();
                    eprintln!("Using username bytes: {:?}", username_bytes);
                    
                    let a = srp.compute_public_ephemeral(&rand_bytes);

                    self.tx
                        .send(&ToSrvPkt::SrpBytesA { a, no_sha1: true })
                        .await
                        .unwrap();

                    self.state = AuthState::Verify(rand_bytes, srp);
                // Special case: if server returns empty username but we have one, try registering again
                } else if self.username != "" && name == "" && auth_methods.contains(AuthMethod::FirstSrp) {
                    eprintln!("Server returned empty username but we have '{}', trying registration mode", self.username);
                    let verifier = srp.compute_verifier(
                        self.username.to_lowercase().as_bytes(),
                        self.password.as_bytes(),
                        &rand_bytes,
                    );

                    self.tx
                        .send(&ToSrvPkt::FirstSrp {
                            salt: rand_bytes,
                            verifier,
                            empty_passwd: self.password.is_empty(),
                        })
                        .await
                        .unwrap();

                    self.state = AuthState::Done(false);
                // Fallback behavior: try FirstSrp if available
                } else if auth_methods.contains(AuthMethod::FirstSrp) {
                    eprintln!("Fallback: Using FirstSrp for '{}'", self.username);
                    let verifier = srp.compute_verifier(
                        self.username.to_lowercase().as_bytes(),
                        self.password.as_bytes(),
                        &rand_bytes,
                    );

                    self.tx
                        .send(&ToSrvPkt::FirstSrp {
                            salt: rand_bytes,
                            verifier,
                            empty_passwd: self.password.is_empty(),
                        })
                        .await
                        .unwrap();

                    self.state = AuthState::Done(false);
                // Last resort: try Srp
                } else if auth_methods.contains(AuthMethod::Srp) {
                    eprintln!("Fallback: Using Srp for '{}'", self.username);
                    let a = srp.compute_public_ephemeral(&rand_bytes);

                    self.tx
                        .send(&ToSrvPkt::SrpBytesA { a, no_sha1: true })
                        .await
                        .unwrap();

                    self.state = AuthState::Verify(rand_bytes, srp);
                } else {
                    panic!("unsupported auth methods: {auth_methods:?}");
                }
            }
            SrpBytesSaltB { salt, b } => {
                if let AuthState::Verify(a, srp) = &self.state {
                    eprintln!("Received server SrpBytesSaltB, processing reply for username '{}'", self.username);
                    
                    // Use lowercase username consistently for authentication
                    let username_lower = self.username.to_lowercase();
                    let username_bytes = username_lower.as_bytes();
                    eprintln!("Using username bytes: {:?}", username_bytes);
                    
                    let srp_result = srp
                        .process_reply(
                            a,
                            username_bytes,
                            self.password.as_bytes(),
                            salt,
                            b,
                        );
                    
                    match srp_result {
                        Ok(proof) => {
                            let m = proof.proof().into();
                            eprintln!("Successfully generated proof for username '{}'", self.username);
                            
                            self.tx.send(&ToSrvPkt::SrpBytesM { m }).await.unwrap();
                            self.state = AuthState::Done(false);
                        },
                        Err(e) => {
                            eprintln!("SRP process_reply failed: {:?}", e);
                            panic!("SRP authentication failed: {:?}", e);
                        }
                    }
                }
            }
            AcceptAuth { .. } => {
                self.tx
                    .send(&ToSrvPkt::Init2 {
                        lang: self.lang.clone(),
                    })
                    .await
                    .unwrap();

                self.state = AuthState::Done(true);
            }
            _ => {}
        }
    }
}
