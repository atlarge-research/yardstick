// Shared helpers for Mineflayer-based workloads. Required from each
// workload's entry script via `require('../lib.js')`.

const mineflayer = require('mineflayer');

const DEFAULT_MC_PORT = 25565;

function createBot({ host, username, port = DEFAULT_MC_PORT, version }) {
    // Pass an explicit `version` to skip Mineflayer's autoVersion ping and,
    // more importantly, to fail fast if the server runs a Minecraft version
    // the bundled minecraft-data doesn't support. Omit it (falsy) to let
    // Mineflayer auto-detect.
    const opts = { host, username, port };
    if (version) {
        opts.version = version;
    }
    const bot = mineflayer.createBot(opts);
    bot.on('kicked', console.log);
    bot.on('error', console.log);
    return bot;
}

module.exports = { createBot };
