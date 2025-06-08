use byteorder::{BigEndian, WriteBytesExt};
use mt_rudp::{RemoteSrv, RudpReceiver, RudpSender};
use pretty_hex::PrettyHex;
use std::io::{self, Write};

async fn example(tx: &RudpSender<RemoteSrv>, rx: &mut RudpReceiver<RemoteSrv>) -> io::Result<()> {
    // send hello packet
    let mut pkt = vec![];
    pkt.write_u16::<BigEndian>(2)?; // high level type
    pkt.write_u8(29)?; // serialize ver
    pkt.write_u16::<BigEndian>(0)?; // compression modes
    pkt.write_u16::<BigEndian>(40)?; // MinProtoVer
    pkt.write_u16::<BigEndian>(40)?; // MaxProtoVer
    pkt.write_u16::<BigEndian>(3)?; // player name length
    pkt.write_all(b"foo")?; // player name

    tx.send(mt_rudp::Pkt {
        unrel: true,
        chan: 1,
        data: pkt.into(),
    })
    .await?;

    // handle incoming packets
    while let Some(result) = rx.recv().await {
        match result {
            Ok(pkt) => {
                println!("{}", pkt.data.hex_dump());
            }
            Err(err) => eprintln!("Error: {}", err),
        }
    }

    Ok(())
}

#[tokio::main]
async fn main() -> io::Result<()> {
    let (tx, mut rx) = mt_rudp::connect("127.0.0.1:30000").await?;

    tokio::select! {
        _ = tokio::signal::ctrl_c() => println!("canceled"),
        res = example(&tx, &mut rx) => {
            res?;
            println!("disconnected");
        }
    }

    // close either the receiver or the sender
    // this shuts down associated tasks
    rx.close().await;

    Ok(())
}
