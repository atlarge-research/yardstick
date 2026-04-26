// Shared helpers for Mineflayer-based workloads. Required from each
// workload's entry script via `require('../lib.js')`.

const mineflayer = require('mineflayer');

const DEFAULT_MC_PORT = 25565;

function createBot({ host, username, port = DEFAULT_MC_PORT }) {
    const bot = mineflayer.createBot({ host, username, port });
    bot.on('kicked', console.log);
    bot.on('error', console.log);
    return bot;
}

module.exports = { createBot };
