const pathfinder = require('mineflayer-pathfinder').pathfinder;
const Movements = require('mineflayer-pathfinder').Movements;
const { GoalXZ } = require('mineflayer-pathfinder').goals;
const v = require('vec3');
const { workerData } = require('worker_threads');

const lib = require('../lib.js');

const host = workerData.host;
const username = workerData.username;
const box_center = workerData.box_center;
const box_width = workerData.box_width;

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

function nextGoal(bot) {
    const x = box_center.x + getRandomInt(box_width) - (box_width / 2);
    const z = box_center.z + getRandomInt(box_width) - (box_width / 2);
    const ts = Date.now() / 1000;
    console.log(`${ts} - bot ${bot.username} should walk from ${bot.entity.position} to ${v(x, bot.entity.position.y, z)}`);
    return new GoalXZ(x, z);
}

const worker_bot = lib.createBot({ host, username });
worker_bot.loadPlugin(pathfinder);
worker_bot.once('spawn', async () => {
    const defaultMove = new Movements(worker_bot);
    defaultMove.allowSprinting = false;
    defaultMove.canDig = false;
    worker_bot.pathfinder.setMovements(defaultMove);
    while (true) {
        const goal = nextGoal(worker_bot);
        try {
            await worker_bot.pathfinder.goto(goal);
        } catch (e) {
            if (e.name !== 'NoPath' && e.name !== 'Timeout') {
                throw e;
            }
        }
    }
});
