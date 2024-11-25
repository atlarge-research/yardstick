const mineflayer = require('mineflayer');
const { parentPort } = require("worker_threads");
const Item = require('prismarine-item')('1.20.1')
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const { GoalXZ } = require('mineflayer-pathfinder').goals
const Vec3 = require('vec3');

const ACTION_HANDLERS = {
    'join': join,
    'move': move,
    'remove_block': remove_block,
    'place_block': place_block,
    'attack_entity': attack_entity,
    'attack_player': attack_player
}

const host = process.env.MC_HOST;
const trace = process.env.TRACE;
const trace_start_timestamp = process.env.START_TIMESTAMP;
const workers = new Set();

let bot;

async function join(bot, args){
    parentPort.postMessage(`joining the bot in the game`);
    return new Promise((resolve, reject) => {
        console.log('waiting');
        bot.once("spawn", () => {
            bot.waitForChunksToLoad().then(() => {
                console.log('spawned');
                const endTime = Date.now();
                resolve(endTime);
            });
        });

        bot.on('death', () => {
            console.log('Bot died, respawning...');
            bot.respawn();
        });
    });
}

function calc_distance(pos1, pos2){
    const { x: x1, y: y1, z: z1 } = pos1;
    const { x: x2, y: y2, z: z2 } = pos2;

    return Math.sqrt( 
        Math.pow((x1 - x2), 2) + Math.pow((y1 - y2), 2) + Math.pow((z1 - z2), 2)
    )
}

async function remove_block(bot, args){
    return new Promise((resolve, reject) => {
        if (bot.targetDigBlock) {
            reject('bot is already removing the block');
        }
        const [x, y, z] = args;

        if(!(x & y & z)){
            reject('Block coordinates are not specified');
        }

        const target = bot.blockAt(Vec3(x, y, z));

        if(!(target & bot.canDigBlock(target))){
            reject('Cannot dig specified block');
        }

        bot.dig(target).then(() => {
            resolve();
        });
    })
}

async function place_block(bot, args){
    const INVENTORY_SLOT = 36;

    return new Promise((resolve, reject) => {
        let [itemId, x, y, z, xFaceAgainst, yFaceAgainst, zFaceAgainst] = args;
        itemId = Number(itemId);

        if(!(itemId)){
            reject('Item is not specified');
        }

        if(!(x & y & z)){
            reject('Coordinates to place block are not speicified');
        }

        if(!(xFaceAgainst & yFaceAgainst & zFaceAgainst)){
            reject('Coordinates to place block against are not speicified');
        }

        const item = new Item(itemId, 1);

        bot.creative.clearInventory().then(() => {
            bot.creative.setInventorySlot(INVENTORY_SLOT, item).then(() => {
                const inventoryItem = bot.inventory.findInventoryItem(itemId, null);
    
                bot.equip(inventoryItem, 'hand').then(() => {
                    var targetBlock = bot.blockAt(Vec3(x, y, z));
                    bot.placeBlock(targetBlock, new Vec3(xFaceAgainst, yFaceAgainst, zFaceAgainst)).then(() => {
                        resolve('Success');
                    });
                });
            });
        });
    });
}

async function attack_entity(bot, args){
    return new Promise((resolve, reject) => {
        const [entityType] = args;

        const entity = bot.nearestEntity(entity => entity.name.toLowerCase() === entityType);
        if(!entity){
            reject('requested entity was not found');
        }

        const moveAndAttack = async () => {
            try {
                while (calc_distance(entity.position, bot.entity.position) > 2) {
                    const { x, z } = entity.position;
                    await move(player_name, [x, z]);
                }

                bot.attack(entity);
                resolve();
            } catch (error) {
                reject(error);
            }
        };

        moveAndAttack();
    });
}

async function attack_player(player_name, args){
    return new Promise((resolve, reject) => {
        const [attackedPlayerName] = args;

        const entity = bot.nearestEntity(entity => entity.type === 'player' && entity.username.toLowerCase() === attackedPlayerName.toLowerCase());
        if(!entity){
            reject('requested entity was not found');
        }

        const moveAndAttack = async () => {
            try {
                while (calc_distance(entity.position, bot.entity.position) > 2) {
                    const { x, z } = entity.position;
                    await move(player_name, [x, z]);
                }

                bot.attack(entity);
                resolve();
            } catch (error) {
                reject(error);
            }
        };

        moveAndAttack();
    });
}

async function move(bot, args){
    return new Promise((resolve, reject) => {
        const [x, z] = args;
        if (!(x && z)){
            resolve('Coordinates are not specified');
        }

        const defaultMove = new Movements(bot);
        bot.pathfinder.setMovements(defaultMove);
        bot.pathfinder.setGoal(new GoalXZ(x, z));

        bot.once('goal_reached', () => {
            resolve();
        });

        bot.once('path_update', (r) => {
            if (r.status === 'noPath') {
                console.log('No path to goal');
                reject('No path to goal');
            }
        });

        bot.once('pathfinder_error', (error) => {
            reject(error);
        });
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function player_worker(queue){
    parentPort.postMessage(`Started player worker`);
    parentPort.on('message', (message) => {
        console.log('Message received from main thread:', message);
        
        queue.push(message);
    });

    while(true){
        if(queue.length > 0){
            const {action, arguments} = queue.shift();
            parentPort.postMessage(`there is a new action to process: ${action} ${arguments}`);
            if(!bot){
                const [player_name] = arguments;
                bot = mineflayer.createBot({
                    host: host,
                    username: player_name,
                    port: 25565,                // only set if you need a port that isn't 25565
                });
                bot.loadPlugin(pathfinder);            
            }

            const handler = ACTION_HANDLERS[action];

            if(!handler){
                continue;
            }
            try{
                await handler(bot, arguments);
            } catch (error){
                parentPort.postMessage(`Error processing action ${action}: ${error.message}`);
            }
        } else{
            await sleep(200);
        }
    }
}

parentPort.postMessage(`script was started`);

player_worker([]);