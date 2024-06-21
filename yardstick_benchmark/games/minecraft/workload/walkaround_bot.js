
const mineflayer = require('mineflayer');
const v = require("vec3");
const { Worker } = require("worker_threads");

const host = process.env.MC_HOST;
const timeout_s = parseInt(process.env.DURATION);
const num_bots = parseInt(process.env.BOTS_PER_NODE);
const box_width = parseInt(process.env.BOX_WIDTH);
const bot_join_delay = process.env.BOTS_JOIN_DELAY;
const bot_index = process.env.BOT_INDEX;
const box_x = process.env.BOX_X;
const box_z = process.env.BOX_Z;

const start = Date.now()

const workers = new Set();

const center = v(box_x, 90, box_z);

function sleep(ms) {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

function start_worker(username) {
    let workerData = {
        host: host,
        username: username,
        time_left_ms: timeout_s * 1000 - (Date.now() - start),
        box_center: center,
        box_width: box_width,
    }
    return new Promise((resolve, reject) => {
        const worker = new Worker("./walkaround_worker_bot.js", { workerData });

        worker.on("message", resolve);
        worker.on("error", reject);
        worker.on("exit", (code) => {
            workers.delete(username)
            if (code !== 0) {
                reject(new Error(`stopped with exit code ${code}`));
            }
        });
    });
}

async function run() {
    let bot = mineflayer.createBot({
        host: host, // minecraft server ip
        username: `jeff-${bot_index}`, // minecraft username
        port: 25565,                // only set if you need a port that isn't 25565
    })
    // bot.on("message", (jsonMsg, position, sender, verified) => console.log(jsonMsg))
    // bot._client.on("packet", (jsonMsg, meta, sender, verified) => {
    //     if (meta.name != "map_chunk") {
    //         console.log(meta)
    //         console.log(jsonMsg)
    //     }
    // });
    bot.once("spawn", async () => {
        bot.creative.startFlying()
        bot.creative
            .flyTo(center) // in view range of the constructs we will spawn in
            .then(async () => {
                bot.quit("constructs have been placed. jeff's job is done")
                let b = 0;
                // Create x new bots that connect and walk around.
                await sleep(bot_index * 1000)
                while (true) {
                    let ts = Date.now() / 1000;
                    console.log(`${ts} - bots: ${workers.size}`)
                    if (workers.size < num_bots) {
                        console.log(`target bots: ${num_bots}, current bots: ${workers.size} --> Adding new bot!`);
                        workers.add(start_worker(`N${bot_index}B${b++}`))
                    } else {
                        console.log(`target bots: ${num_bots}, current bots: ${workers.size} --> Enough bots connected`);
                    }
                    await sleep(bot_join_delay * 1000)
                }
            })
    });
    // Log errors and kick reasons:
    bot.on('kicked', console.log)
    bot.on('error', console.log)

    let ts = Date.now() / 1000;
    console.log(`hi! Started at ${ts}. I will exit after ${timeout_s} seconds.`);
    await sleep(timeout_s * 1000)
    process.exit(0)
}

run()
