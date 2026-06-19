const { get } = require('http');
const mineflayer = require('mineflayer');
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const { GoalNear, GoalXZ } = require('mineflayer-pathfinder').goals
const v = require("vec3");

// sub.js
const { workerData, parentPort } = require("worker_threads");

const host = workerData.host
const username = workerData.username

function getRandomInt(min, max) {
  return Math.random() * (max - min) + min;
}


let worker_bot = mineflayer.createBot({
    host: host, // minecraft server ip
    username: username, // minecraft username
    port: 25565,                // only set if you need a port that isn't 25565
});
worker_bot.on('kicked', console.log)
worker_bot.on('error', console.log)

worker_bot.loadPlugin(pathfinder)

worker_bot.once("spawn", async () => {
    let defaultMove = new Movements(worker_bot)
    defaultMove.allowSprinting = true
    worker_bot.pathfinder.setMovements(defaultMove)

    await worker_bot.waitForChunksToLoad()

    let x = getRandomInt(-2000, 2000)
    let z = getRandomInt(-2000, 2000)

    let increment

    while (true) {
        await worker_bot.pathfinder.goto(new GoalXZ(x, z))

        increment = getRandomInt(0,  2000)
        x = x + getRandomInt(-increment, increment)
        z = z + getRandomInt(-increment, increment)
    }

});

