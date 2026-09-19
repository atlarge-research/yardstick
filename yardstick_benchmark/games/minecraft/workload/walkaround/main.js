// WalkAround workload entry point.
//
// Spawns one worker thread per emulated player on this node (worker.js), one
// every BOTS_JOIN_DELAY seconds until BOTS_PER_NODE of them are connected,
// and keeps that many running. Each player walks between random points in a
// box of BOX_WIDTH blocks centred on (BOX_X, BOX_Z) using mineflayer-
// pathfinder -- ordinary survival-mode walking, no server-side privileges of
// any kind. The process exits after DURATION seconds, which is the completion
// signal the headnode's MineflayerWorkload.run() waits on.
//
// There used to be an extra bot ("jeff") that joined first, flew to the box
// centre in *creative* mode and quit, with the worker-spawning loop hung off
// that flight's promise. The server's default gamemode is survival, so the
// flight always failed there and no player ever joined: the run looked
// healthy and measured an idle server. Nothing else depended on jeff -- it
// placed no blocks (its "constructs have been placed" message is vestigial;
// no version in this repo's history ever built anything), it left the server
// before the workers arrived, and the box sits next to the world spawn the
// deployment sets, so it did not usefully preload chunks either. The workers
// are started directly instead.

const path = require('path');
const v = require('vec3');
const { Worker } = require('worker_threads');

const host = process.env.MC_HOST;
const port = parseInt(process.env.MC_PORT || '25565');
const version = process.env.MC_VERSION || undefined;
const timeout_s = parseInt(process.env.DURATION);
const num_bots = parseInt(process.env.BOTS_PER_NODE);
const box_width = parseInt(process.env.BOX_WIDTH);
const bot_join_delay_s = parseInt(process.env.BOTS_JOIN_DELAY);
const bot_index = parseInt(process.env.BOT_INDEX);
// parseInt, not the raw strings: these end up as vec3 components that
// worker.js does arithmetic on, and '-16' + 7 is the string '-167'.
const box_x = parseInt(process.env.BOX_X);
const box_z = parseInt(process.env.BOX_Z);

// How long to wait for the *first* player to join before declaring the run a
// failure. Joining is fast; if nothing is connected by now the bots can't get
// in at all (wrong version, server full, whitelist, server down) and there is
// nothing to be gained from idling for the rest of DURATION.
const JOIN_GRACE_MS = 60000;

const start = Date.now();
// Live worker threads, keyed by username, so `workers.size` is the number of
// players currently connected from this node.
const workers = new Map();
// Players that made it into the world at least once. Zero of these by the end
// means the workload measured nothing.
let ever_joined = 0;

const center = v(box_x, 90, box_z);

const WORKER_SCRIPT = path.join(__dirname, 'worker.js');

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function start_worker(username) {
    const workerData = {
        host: host,
        port: port,
        version: version,
        username: username,
        time_left_ms: timeout_s * 1000 - (Date.now() - start),
        box_center: center,
        box_width: box_width,
    };
    const worker = new Worker(WORKER_SCRIPT, { workerData });
    workers.set(username, worker);
    worker.on('message', (msg) => {
        if (msg && msg.event === 'spawn') {
            ever_joined++;
            console.log(`${Date.now() / 1000} - ${username} joined the world`);
        }
    });
    // A worker that dies (connection refused, kicked, pathfinder blowing up)
    // must not take the whole run down: log it loudly and let the loop below
    // replace it, so the node keeps offering num_bots of load.
    worker.on('error', (err) => {
        console.error(`bot ${username} failed: ${err && err.stack ? err.stack : err}`);
        workers.delete(username);
    });
    worker.on('exit', (code) => {
        workers.delete(username);
        if (code !== 0) {
            console.error(`bot ${username} stopped with exit code ${code}`);
        }
    });
    return worker;
}

// Top up to num_bots players, one every bot_join_delay_s seconds, forever --
// run() ends the process once DURATION has elapsed.
async function spawn_bots() {
    let b = 0;
    // Stagger the nodes so a multi-node run doesn't hit the server with
    // every node's first join at the same instant.
    await sleep(bot_index * 1000);
    while (true) {
        const ts = Date.now() / 1000;
        console.log(`${ts} - bots: ${workers.size}`);
        if (workers.size < num_bots) {
            console.log(`target bots: ${num_bots}, current bots: ${workers.size} --> Adding new bot!`);
            start_worker(`N${bot_index}B${b++}`);
        } else {
            console.log(`target bots: ${num_bots}, current bots: ${workers.size} --> Enough bots connected`);
        }
        await sleep(bot_join_delay_s * 1000);
    }
}

function fail(message) {
    console.error(`walkaround: ${message}`);
    process.exit(1);
}

async function run() {
    const ts = Date.now() / 1000;
    console.log(
        `hi! Started at ${ts}. ${num_bots} player(s) will walk around a ` +
        `${box_width}-block box centred on (${box_x}, ${box_z}). ` +
        `I will exit after ${timeout_s} seconds.`
    );

    spawn_bots();

    // Fail fast, and loudly, if the players can't get in at all.
    const join_deadline = setTimeout(() => {
        if (ever_joined === 0) {
            fail(
                `no emulated player joined within ` +
                `${(bot_index * 1000 + JOIN_GRACE_MS) / 1000}s; giving up ` +
                `instead of measuring an idle server`
            );
        }
    }, bot_index * 1000 + JOIN_GRACE_MS);

    await sleep(timeout_s * 1000);
    clearTimeout(join_deadline);
    if (ever_joined === 0) {
        fail('no emulated player ever joined; the run measured an idle server');
    }
    console.log(`bye! ${ever_joined} player session(s) over ${timeout_s} seconds.`);
    process.exit(0);
}

run();
