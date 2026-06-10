// WorldGeneration workload entry point.
//
// Spawns one worker thread per emulated player on this node. Each worker
// joins the server, switches to spectator mode, and teleports to a fresh,
// far-away location TELEPORTS times, waiting for each area's chunks to load
// in between teleports (see worker.js). The process exits as soon as every
// worker has finished its teleports -- this workload is completion-based,
// not duration-based. TIMEOUT is only a safety net for a stuck run.

const path = require('path');
const { Worker } = require('worker_threads');

const host = process.env.MC_HOST;
const port = parseInt(process.env.MC_PORT);
const version = process.env.MC_VERSION;
const rcon_host = process.env.RCON_HOST;
const rcon_port = parseInt(process.env.RCON_PORT);
const rcon_password = process.env.RCON_PASSWORD;
const teleports = parseInt(process.env.TELEPORTS);
const num_bots = parseInt(process.env.BOTS_PER_NODE);
const total_bots = parseInt(process.env.TOTAL_BOTS);
const start_distance = parseInt(process.env.START_DISTANCE);
const step_distance = parseInt(process.env.STEP_DISTANCE);
const teleport_y = parseInt(process.env.TELEPORT_Y);
const chunk_load_timeout_s = parseInt(process.env.CHUNK_LOAD_TIMEOUT);
const bot_join_delay_s = parseInt(process.env.BOTS_JOIN_DELAY);
const bot_index = parseInt(process.env.BOT_INDEX);
const timeout_s = parseInt(process.env.TIMEOUT);

const influx = {
    url: process.env.INFLUXDB_URL,
    token: process.env.INFLUXDB_TOKEN,
    org: process.env.INFLUXDB_ORG,
    bucket: process.env.INFLUXDB_BUCKET,
};

const WORKER_SCRIPT = path.join(__dirname, 'worker.js');

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function start_worker(username, global_index) {
    const workerData = {
        host,
        port,
        version,
        rcon_host,
        rcon_port,
        rcon_password,
        username,
        global_index,
        total_bots,
        teleports,
        start_distance,
        step_distance,
        teleport_y,
        chunk_load_timeout_ms: chunk_load_timeout_s * 1000,
        influx,
    };
    return new Promise((resolve, reject) => {
        const worker = new Worker(WORKER_SCRIPT, { workerData });
        // The worker posts its per-player result when done; resolve on that.
        worker.on('message', resolve);
        worker.on('error', reject);
        worker.on('exit', (code) => {
            if (code !== 0) {
                reject(new Error(`worker ${username} exited with code ${code}`));
            }
        });
    });
}

async function run() {
    const ts = Date.now() / 1000;
    console.log(
        `worldgen: started at ${ts} - ${num_bots} player(s) on node ${bot_index}, ` +
        `${teleports} teleports each, ${total_bots} player(s) total.`
    );

    const done = [];
    for (let i = 0; i < num_bots; i++) {
        const username = `N${bot_index}B${i}`;
        const global_index = bot_index * num_bots + i;
        console.log(`worldgen: launching player ${username} (global ${global_index})`);
        done.push(start_worker(username, global_index));
        if (i < num_bots - 1) {
            await sleep(bot_join_delay_s * 1000);
        }
    }

    // Safety net: if a worker gets permanently stuck, don't hang forever.
    const safety = sleep(timeout_s * 1000).then(() => {
        console.log(`worldgen: TIMEOUT (${timeout_s}s) reached before all players finished.`);
        return 'timeout';
    });

    const result = await Promise.race([
        Promise.allSettled(done).then(() => 'complete'),
        safety,
    ]);

    console.log(`worldgen: finished (${result}).`);
    process.exit(0);
}

run();
