// WalkAround worker: one emulated player.
//
// Joins the server and walks, on foot, between random points inside a box of
// `box_width` blocks centred on `box_center`. Plain survival-mode movement:
// mineflayer-pathfinder walks the bot there, no flying, no digging, no
// server-side commands, so this works on a default server.

const pathfinder = require('mineflayer-pathfinder').pathfinder;
const Movements = require('mineflayer-pathfinder').Movements;
const { GoalXZ } = require('mineflayer-pathfinder').goals;
const v = require('vec3');
const { workerData, parentPort } = require('worker_threads');

const lib = require('../lib.js');

const host = workerData.host;
const port = workerData.port;
const version = workerData.version;
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

const worker_bot = lib.createBot({ host, port, version, username });
worker_bot.loadPlugin(pathfinder);
// If this player loses its connection there is nothing left to do here: end
// the thread so the parent can replace it and the node keeps its target
// number of players.
worker_bot.once('end', (reason) => {
    console.log(`${Date.now() / 1000} - bot ${username} disconnected (${reason})`);
    process.exit(0);
});
worker_bot.once('spawn', async () => {
    // Tell the parent this player actually made it into the world; a run
    // where nobody does is a failed run, not an idle one.
    parentPort.postMessage({ event: 'spawn', username });
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
