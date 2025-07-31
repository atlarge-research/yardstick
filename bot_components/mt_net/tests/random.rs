use libtest_mimic::{Arguments, Trial};

use mt_net::{generate_random::GenerateRandomVariant, rand, ToCltPkt, ToSrvPkt};
use mt_ser::{DefCfg, MtDeserialize, MtSerialize};
use std::{
    error::Error,
    fmt::Debug,
    io::{Cursor, Write},
    path::Path,
    process::{Command, Stdio},
};

fn test_reserialize<'a, T>(type_name: &'static str, reserialize: &Path) -> Vec<Trial>
where
    T: MtSerialize + MtDeserialize + GenerateRandomVariant + PartialEq + Debug,
{
    (0..T::num_variants())
        .flat_map(move |i| {
            let pkt_name = format!("{type_name}::{}", T::variant_name(i));
            let reserialize = reserialize.as_os_str().to_os_string();

            if pkt_name == "ToSrvPkt::Disco" {
                return None;
            }

            Some(
                Trial::test(pkt_name.clone(), move || {
                    let mut rng = rand::thread_rng();
                    let mut printed_stderr = false;

                    for _ in 0..100 {
                        // use buffered IO instead of directly reading from the process
                        // this enables printing out payloads for debugging

                        let input = T::generate_random_variant(&mut rng, i);

                        let mut input_payload = Vec::new();
                        input
                            .mt_serialize::<DefCfg>(&mut input_payload)
                            .map_err(|e| format!("serialize error: {e}\ninput: {input:?}"))?;

                        let mut child = Command::new(&reserialize)
                            .arg(type_name)
                            .stdin(Stdio::piped())
                            .stdout(Stdio::piped())
                            .stderr(Stdio::piped())
                            .spawn()
                            .expect("failed to spawn reserialize");

                        let mut stdin = child.stdin.take().unwrap();
                        let stdin_payload = input_payload.clone();
                        std::thread::spawn(move || {
                            stdin.write_all(&stdin_payload).unwrap();
                        });

                        let command_out = child.wait_with_output().unwrap();

                        let stderr = String::from_utf8_lossy(&command_out.stderr);
                        if command_out.status.success() {
                            if stderr.len() > 0 && !printed_stderr {
                                printed_stderr = true;
                                eprintln!("stderr for {pkt_name}: {stderr}");
                            }
                        } else {
                            return Err(format!(
                                "reserialize returned failure\n\
								input: {input:?}\n\
								input payload: {input_payload:?}\n\
								stderr: {stderr}"
                            )
                            .into());
                        }

                        let mut reader = Cursor::new(command_out.stdout);
                        let output = T::mt_deserialize::<DefCfg>(&mut reader).map_err(|e| {
                            format!(
                                "deserialize error: {e}\n\
								input: {input:?}\n\
								input payload: {input_payload:?}\n\
								output payload: {:?}\n\
								stderr: {stderr}",
                                reader.get_ref()
                            )
                        })?;

                        if input != output {
                            return Err(format!(
                                "output does not match input\n\
								input: {input:?}\n\
								output: {output:?}\n\
								input payload: {input_payload:?}\n\
								output payload: {:?}\n\
								stderr: {stderr}",
                                reader.get_ref(),
                            )
                            .into());
                        }
                    }

                    Ok(())
                })
                .with_kind("random"),
            )
        })
        .collect()
}

fn main() -> Result<(), Box<dyn Error>> {
    let reserialize = Path::new(file!()).with_file_name("reserialize/reserialize");

    if !reserialize.exists() {
        if !Command::new("go")
            .arg("build")
            .current_dir(reserialize.parent().unwrap())
            .spawn()
            .expect("go is required for random tests")
            .wait()
            .expect("go build didn't run")
            .success()
        {
            panic!("go build failed");
        }
    }

    let args = Arguments::from_args();

    let mut tests = Vec::new();
    tests.extend(test_reserialize::<ToSrvPkt>("ToSrvPkt", &reserialize));
    tests.extend(test_reserialize::<ToCltPkt>("ToCltPkt", &reserialize));

    libtest_mimic::run(&args, tests).exit();
}
