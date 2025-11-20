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

let mcData

worker_bot.loadPlugin(pathfinder)
worker_bot.loadPlugin(require('mineflayer-collectblock').plugin)

worker_bot.once("spawn", async () => {
    let defaultMove = new Movements(worker_bot)
    defaultMove.allowSprinting = false
    defaultMove.canDig = true
    worker_bot.pathfinder.setMovements(defaultMove)

    mcData = require('minecraft-data')(worker_bot.version)

    await worker_bot.waitForChunksToLoad()

    let x = getRandomInt(-20, 20)
    let z = getRandomInt(-20, 20)

    await worker_bot.pathfinder.goto(new GoalXZ(x, z))

    let ore_ids = [
        mcData.blocksByName['coal_ore'].id,
        mcData.blocksByName['copper_ore'].id,
        mcData.blocksByName['lapis_ore'].id,
        mcData.blocksByName['iron_ore'].id,     
        ]

    let block = 0

    while (true) {

        try {

            block = worker_bot.findBlock({
                point: worker_bot.entity.position,
                matching: ore_ids,
                maxDistance: 128
            })

            let goal = new GoalNear(block.position.x, block.position.y, block.position.z, 1)
            await worker_bot.pathfinder.goto(goal)
            await worker_bot.dig(worker_bot.blockAt(block.position))
        } catch (e) {


            (console.error || console.log).call(console, e.stack || e);
        }
    }
});

