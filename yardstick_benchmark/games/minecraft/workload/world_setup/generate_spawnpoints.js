const Rcon = require('rcon');
const mineflayer = require('mineflayer');
const host = process.env.MC_HOST;
var rcon = new Rcon(host, 25575, 'password');

const globalSpread = process.env.GLOBAL_SPREAD;
const numPlayers = process.env.NUM_PLAYERS;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function gaussianRandom(mu = 0, sigma = 1) {
    let u1 = 1 - Math.random();
    let u2 = 1 - Math.random();
    let z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mu + z0 * sigma;
}

function getRandomCoordinates() {
    const x = Math.round(gaussianRandom(0, globalSpread));
    const y = Math.round(gaussianRandom(0, globalSpread));
    return [x, y];
}

function sendRconCommand(command) {
    return new Promise((resolve, reject) => {
        rcon.send(command);
        rcon.once('response', (response) => {
            console.log(`RCON Response: ${response}`);
            resolve(response);
        });
        rcon.once('error', (err) => {
            reject(err);
        });
    });
}

async function run() {
    rcon.on('auth', async () => {
        for (let i = 1; i <= numPlayers; i++) {
            console.log('hello');
            const bot = mineflayer.createBot({
                host: host,
                username: `player_${i}`,
                port: 25565,
                version: '1.20.1',
                checkTimeoutInterval: 1000 * 1000
            });

            bot.on('death', () => {
                bot.respawn();
            });

            bot.once("spawn", async () => {
                const [x, y] = getRandomCoordinates();
                await bot.waitForChunksToLoad();

                try {
                    await sendRconCommand(`spawnpoint player_${i} ${x} 80 ${y}`);
                    await sendRconCommand(`kill player_${i}`);
                    console.log("Player killed to test spawnpoint.");
                } catch (err) {
                    console.error("Error while sending RCON commands:", err);
                }
            });
                await sleep(10000);
        }
        process.exit(0);
    });

    rcon.on('end', () => {
        console.log("RCON connection closed.");
    });

    rcon.on('error', (err) => {
        console.error("RCON error:", err);
    });

    console.log("Attempting to connect to RCON...");
    rcon.connect();
}

run();

