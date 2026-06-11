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
        bot.on('chunkColumnLoad', onLoad);
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

async function run() {
    const rcon = await Rcon.connect({
        host: rcon_host,
        port: rcon_port,
        password: rcon_password,
    });

    const bot = lib.createBot({ host, username, port, version });

    bot.once('spawn', async () => {
        // Spectator keeps the player loading chunks while immune to fall
        // damage/suffocation, so the teleport sequence can't be broken by
        // death/respawn.
        await rcon.send(`gamemode spectator ${username}`);

        // Readiness guard: don't start teleporting until the bot is fully
        // settled in the world. The first `tp` issued while the post-login
        // position/teleport-confirm handshake is still in flight never gets
        // its destination chunks streamed, so teleport #1 would otherwise eat
        // the whole timeout. Waiting for the spawn-area chunks to load (this
        // is mineflayer's own readiness check; safe to use here because the
        // bot's real position is its actual spawn, not a lagging post-`tp`
        // position) puts the first teleport in the same settled state as
        // every later one. Wrapped so a slow/at-cap spawn load degrades to
        // the fixed settle below rather than aborting the run.
        try {
            await bot.waitForChunksToLoad();
        } catch (e) {
            console.log(`${username}: waitForChunksToLoad guard: ${e.message}`);
        }
        // Conservative extra buffer on top of the guard (waitForChunksToLoad
        // can return immediately if spawn chunks were already present).
        await sleep(2000);

        const tags = `player=${username},bots=${total_bots},node_index=${global_index}`;
        const lines = [];
        const latencies = [];
        const runStart = Date.now();

        for (let k = 0; k < teleports; k++) {
            const target = targetFor(k);
            const t0 = Date.now();
            // Attach the chunk waiter *before* teleporting so we can't miss
            // the load event.
            const loadedP = waitForChunk(bot, target, chunk_load_timeout_ms);
            await rcon.send(`tp ${username} ${target.x} ${target.y} ${target.z}`);
            const loaded = await loadedP;
            const load_ms = Date.now() - t0;
            latencies.push(load_ms);

            const dist = start_distance + k * step_distance;
            console.log(
                `${username}: teleport ${k + 1}/${teleports} to ` +
                `(${target.x}, ${target.y}, ${target.z}) [dist ${dist}] ` +
                `loaded in ${load_ms}ms${loaded ? '' : ' (TIMEOUT)'}`
            );
            const ts_ms = Date.now();
            lines.push(
                `minecraft_worldgen_teleport,${tags},teleport=${k} ` +
                `load_ms=${load_ms},distance=${dist}i,timed_out=${loaded ? 0 : 1}i ${ts_ms}`
            );
        }

        const total_ms = Date.now() - runStart;
        const mean_ms = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        const max_ms = Math.max(...latencies);
        console.log(
            `${username}: done. ${teleports} teleports in ${total_ms}ms ` +
            `(mean ${mean_ms.toFixed(0)}ms, max ${max_ms}ms).`
        );
        lines.push(
            `minecraft_worldgen,${tags} ` +
            `total_duration_ms=${total_ms},teleports=${teleports}i,` +
            `mean_load_ms=${mean_ms},max_load_ms=${max_ms} ${Date.now()}`
        );

        await commitMetrics(lines);
        await rcon.end().catch(() => {});
        bot.quit('worldgen: teleports complete');
        parentPort.postMessage({
            username,
            total_ms,
            teleports,
            mean_ms,
            max_ms,
        });
    });
}

run();
