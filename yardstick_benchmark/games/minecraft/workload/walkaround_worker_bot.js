
const mineflayer = require('mineflayer');
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const { GoalNear, GoalXZ } = require('mineflayer-pathfinder').goals
const v = require("vec3");

// sub.js
const { workerData, parentPort } = require("worker_threads");

const host = workerData.host
const username = workerData.username
const time_left_ms = workerData.time_left_ms
const box_center = workerData.box_center
const box_width = workerData.box_width

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

function nextGoal(bot) {
    let x = box_center.x + getRandomInt(box_width) - (box_width / 2);
    let z = box_center.z + getRandomInt(box_width) - (box_width / 2);
    let ts = Date.now() / 1000;
    console.log(`${ts} - bot ${bot.username} should walk from ${bot.entity.position} to ${v(x, bot.entity.position.y, z)}`)
    return new GoalXZ(x, z);
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
    defaultMove.allowSprinting = false
    defaultMove.canDig = false
    worker_bot.pathfinder.setMovements(defaultMove)
    // worker_bot.pathfinder.thinkTimeout = 60000 // max 60 seconds to find path from start to finish
    while (true) {
        let goal = nextGoal(worker_bot);
        try {
            await worker_bot.pathfinder.goto(goal)
        } catch (e) {
            // if the bot cannot find a path, carry on and let it try to move somewhere else
            if (e.name != "NoPath" && e.name != "Timeout") {
                throw e
            }
        }
    }
});

// parentPort.postMessage({});
