// WorldGeneration worker: one emulated player.
//
// Joins the server, switches to spectator mode (so it keeps loading chunks
// around itself but is immune to fall damage/suffocation, and the teleport
// sequence is never interrupted by death), then teleports `teleports` times.
//
// Each teleport targets a fresh location: the player owns a fixed angular
// sector (so players spread out away from each other) and marches outward by
// `step_distance` blocks per teleport (so every target is ungenerated terrain
// away from spawn). After issuing the teleport we wait for the target chunk
// column to load in -- which forces the server to generate it -- and then
// immediately teleport again.
//
// Teleports and the gamemode change go over RCON so they run as the server
// console (full permissions, no op needed). When all teleports are done we
// commit the timing to InfluxDB and report back to the parent.

const v = require('vec3');
const { Rcon } = require('rcon-client');
const { workerData, parentPort } = require('worker_threads');

const lib = require('../lib.js');

const {
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
    chunk_load_timeout_ms,
    influx,
} = workerData;

// Each player gets a distinct angular sector so targets fan out away from
// each other; distance grows each teleport so every target is fresh terrain.
const angle = (2 * Math.PI * global_index) / total_bots;

function targetFor(teleportIndex) {
    const dist = start_distance + teleportIndex * step_distance;
    const x = Math.round(Math.cos(angle) * dist);
    const z = Math.round(Math.sin(angle) * dist);
    return v(x, teleport_y, z);
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

// Resolve once the chunk column containing (x, z) is loaded, or after
// `timeoutMs` (resolving false). Listens for the chunkColumnLoad event and
// also polls the world in case the column loads before/around our listener.
function waitForChunk(bot, target, timeoutMs) {
    const chunkX = Math.floor(target.x / 16);
    const chunkZ = Math.floor(target.z / 16);
    return new Promise((resolve) => {
        let done = false;
        const finish = (loaded) => {
            if (done) return;
            done = true;
            bot.removeListener('chunkColumnLoad', onLoad);
            bot.removeListener('end', onEnd);
            clearInterval(poll);
            clearTimeout(timer);
            resolve(loaded);
        };
        // mineflayer versions differ on whether the emitted point is in
        // block-corner coords (chunk*16) or chunk-index coords; accept both
        // so the event path fires precisely instead of leaning on the poll.
        const onLoad = (point) => {
            const px = point.x % 16 === 0 ? point.x / 16 : point.x;
            const pz = point.z % 16 === 0 ? point.z / 16 : point.z;
            if (px === chunkX && pz === chunkZ) {
                finish(true);
            }
        };
        // If the bot disconnects mid-wait, chunks will never arrive -- resolve
        // immediately (as not-loaded) instead of burning the whole timeout.
        const onEnd = () => finish(false);
        bot.on('chunkColumnLoad', onLoad);
        bot.once('end', onEnd);
        const poll = setInterval(() => {
            try {
                if (bot.world.getColumnAt(target)) {
                    finish(true);
                }
            } catch (e) {
                // getColumnAt can throw before the world is set up; ignore.
            }
        }, 200);
        const timer = setTimeout(() => finish(false), timeoutMs);
    });
}

// Set Player Position movement flags (u8 bitfield) for the 1.21.x protocol.
const MOVE_FLAGS = { onGround: false, hasHorizontalCollision: false };

// After an RCON `/tp` the (spectator) bot sits frozen and never reports a
// position, so the server doesn't recenter this player's chunk loading and the
// destination chunks never stream -- worst on the very first teleport, which
// would otherwise eat the whole timeout. Send a short burst of position
// packets that actually *move* the bot so the server recenters and generates
// the area. Returns the interval id; the caller clears it once chunks load.
function startNudging(bot, target) {
    let n = 0;
    let y = target.y;
    const id = setInterval(() => {
        // Cap the burst (~2s) so a slow load doesn't drift the bot far down;
        // by then the recenter has been triggered and the chunk wait covers
        // the rest.
        if (n++ >= 20) {
            clearInterval(id);
            return;
        }
        try {
            y -= 0.08;
            bot._client.write('position', {
                x: target.x, y, z: target.z, flags: MOVE_FLAGS,
            });
        } catch (e) {
            clearInterval(id); // protocol mismatch -- stop trying
        }
    }, 100);
    return id;
}

// Write line-protocol points to InfluxDB v2's HTTP write API. No-op if no
// InfluxDB URL was configured.
async function commitMetrics(lines) {
    if (!influx || !influx.url) {
        console.log(`${username}: no InfluxDB configured, skipping metric commit.`);
        return;
    }
    const url =
        `${influx.url}/api/v2/write` +
        `?org=${encodeURIComponent(influx.org)}` +
        `&bucket=${encodeURIComponent(influx.bucket)}` +
        `&precision=ms`;
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                Authorization: `Token ${influx.token}`,
                'Content-Type': 'text/plain; charset=utf-8',
            },
            body: lines.join('\n'),
        });
        if (!res.ok) {
            console.log(`${username}: InfluxDB write failed ${res.status}: ${await res.text()}`);
        }
    } catch (e) {
        console.log(`${username}: InfluxDB write error: ${e}`);
    }
}

// Per-command RCON deadline. Under heavy world-gen load the server's main
// thread is busy and slow to answer RCON; the rcon-client default (~5s) trips
// constantly. Generous here, and rconSend() retries anyway.
const RCON_TIMEOUT_MS = 30000;

function connectRcon() {
    return Rcon.connect({
        host: rcon_host,
        port: rcon_port,
        password: rcon_password,
        timeout: RCON_TIMEOUT_MS,
    });
}

async function run() {
    let rcon = await connectRcon();

    // Send an RCON command, retrying forever (reconnecting on failure, with
    // capped backoff) until it succeeds. A benchmark must run to the end no
    // matter how slow the server is: under load the server can miss the RCON
    // response deadline ("Timeout for packet id N"), and we must never drop a
    // teleport or lose a bot over it -- the slowness instead shows up as a
    // larger total time. Ultimately bounded by the entry script's overall
    // safety timeout.
    async function rconSend(cmd) {
        for (let attempt = 1; ; attempt++) {
            try {
                return await rcon.send(cmd);
            } catch (e) {
                console.log(
                    `${username}: rcon '${cmd}' attempt ${attempt} failed ` +
                    `(${e.message}); reconnecting and retrying`
                );
                await sleep(Math.min(500 * attempt, 5000));
                try { await rcon.end(); } catch (_) { /* already closed */ }
                try {
                    rcon = await connectRcon();
                } catch (ce) {
                    console.log(`${username}: rcon reconnect failed (${ce.message})`);
                }
            }
        }
    }

    const bot = lib.createBot({ host, username, port, version });

    bot.once('spawn', async () => {
        const tags = `player=${username},bots=${total_bots},node_index=${global_index}`;
        const lines = [];
        const latencies = [];
        let completed = 0;
        let runStart = Date.now();
        let alive = true;
        let finishing = false;
        // If the bot gets kicked/disconnected mid-run, chunks stop arriving;
        // stop teleporting instead of grinding every remaining teleport into a
        // full chunk-load timeout (RCON `tp` of an absent player is a no-op).
        bot.once('end', (reason) => {
            alive = false;
            if (!finishing) {
                console.log(`${username}: bot disconnected mid-run (${reason})`);
            }
        });

        try {
            // Spectator keeps the player loading chunks while immune to fall
            // damage/suffocation, so the sequence can't be broken by death.
            await rconSend(`gamemode spectator ${username}`);

            // Settle: let the bot finish loading its spawn area before the
            // first teleport. (The first-teleport stall itself is fixed by the
            // post-teleport position nudge -- see startNudging; this just gives
            // the bot a clean starting state.)
            try {
                await bot.waitForChunksToLoad();
            } catch (e) {
                console.log(`${username}: waitForChunksToLoad guard: ${e.message}`);
            }
            await sleep(2000);

            runStart = Date.now();
            for (let k = 0; k < teleports; k++) {
                if (!alive) {
                    console.log(
                        `${username}: aborting after ${completed}/${teleports} ` +
                        `teleports -- bot disconnected`
                    );
                    break;
                }
                const target = targetFor(k);
                const t0 = Date.now();
                // Reliably issue the teleport first (retrying through RCON
                // timeouts), *then* wait for the destination chunks. Waiting
                // first would let the chunk-load timer be eaten by RCON
                // retries; waitForChunk's getColumnAt poll covers the tiny
                // window between the tp landing and the listener attaching.
                await rconSend(`tp ${username} ${target.x} ${target.y} ${target.z}`);
                const loadedP = waitForChunk(bot, target, chunk_load_timeout_ms);
                // Nudge the bot so the server recenters chunk loading (see
                // startNudging); stop once the chunks have loaded.
                const nudge = startNudging(bot, target);
                const loaded = await loadedP;
                clearInterval(nudge);
                const load_ms = Date.now() - t0;
                latencies.push(load_ms);
                completed++;

                const dist = start_distance + k * step_distance;
                console.log(
                    `${username}: teleport ${k + 1}/${teleports} to ` +
                    `(${target.x}, ${target.y}, ${target.z}) [dist ${dist}] ` +
                    `loaded in ${load_ms}ms${loaded ? '' : ' (TIMEOUT)'}`
                );
                lines.push(
                    `minecraft_worldgen_teleport,${tags},teleport=${k} ` +
                    `load_ms=${load_ms},distance=${dist}i,timed_out=${loaded ? 0 : 1}i ${Date.now()}`
                );
            }
        } catch (e) {
            // Log and fall through to finally so partial metrics are still
            // committed -- a bot that dies mid-run (e.g. an RCON/connection
            // drop under load) must not silently vanish.
            console.log(
                `${username}: ERROR after ${completed}/${teleports} teleports: ` +
                `${e && e.stack ? e.stack : e}`
            );
        } finally {
            if (latencies.length) {
                const total_ms = Date.now() - runStart;
                const mean_ms =
                    latencies.reduce((a, b) => a + b, 0) / latencies.length;
                const max_ms = Math.max(...latencies);
                console.log(
                    `${username}: done. ${completed}/${teleports} teleports in ` +
                    `${total_ms}ms (mean ${mean_ms.toFixed(0)}ms, max ${max_ms}ms).`
                );
                lines.push(
                    `minecraft_worldgen,${tags} ` +
                    `total_duration_ms=${total_ms},teleports=${completed}i,` +
                    `mean_load_ms=${mean_ms},max_load_ms=${max_ms} ${Date.now()}`
                );
            } else {
                console.log(`${username}: no teleports completed; nothing to commit.`);
            }
            await commitMetrics(lines);
            await rcon.end().catch(() => {});
            finishing = true;
            try {
                bot.quit('worldgen: done');
            } catch (e) { /* bot already disconnected */ }
            parentPort.postMessage({ username, completed });
        }
    });
}

run();
