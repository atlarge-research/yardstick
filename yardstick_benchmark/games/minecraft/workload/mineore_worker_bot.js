const mineflayer = require('mineflayer');
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const collectBlock = require('mineflayer-collectblock').plugin
const toolPlugin = require('mineflayer-tool').plugin
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
worker_bot.on('kicked', (event) => {
  console.log("kicked event:", event);
})
worker_bot.on('error', (event) => {
  console.log("error event:", event);
})

let mcData

worker_bot.loadPlugin(pathfinder)
worker_bot.loadPlugin(collectBlock)
worker_bot.loadPlugin(toolPlugin)

function sayItems (items = worker_bot.inventory.items()) {
  const output = items.map(itemToString).join(', ')
  if (output) {
    worker_bot.chat(output)
  } else {
    worker_bot.chat('empty')
  }
}

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

    let block
    let distance = 2

    while (true) {

        try {

          block = worker_bot.findBlock({
              point: worker_bot.entity.position,
              matching: ore_ids,
              maxDistance: distance
            })

          if (block == null) {
            // We want to expand our search space if we do not find at matching block 
            distance *= 2
            continue;
          }

          let goal = new GoalNear(block.position.x, block.position.y, block.position.z, 1)
          await worker_bot.pathfinder.goto(goal)
          await worker_bot.dig(worker_bot.blockAt(block.position))
            
        } catch (e) {
            // (console.error || console.log).call(console, e.stack || e);
            console.log("caught error:", e, e.stack);
        }
    }
});

