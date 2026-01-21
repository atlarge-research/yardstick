const mineflayer = require('mineflayer');
const { parentPort } = require("worker_threads");
const Item = require('prismarine-item')('1.20.1')
const pathfinder = require('mineflayer-pathfinder').pathfinder
const Movements = require('mineflayer-pathfinder').Movements
const { GoalXZ } = require('mineflayer-pathfinder').goals
const Vec3 = require('vec3');
const { appendFile } = require('node:fs');
const { resolve } = require('node:path');

const ACTION_HANDLERS = {
    'join': join,
    'move': move,
    'remove_block': remove_block,
    'place_block': place_block,
    'attack_entity': attack_entity,
    'attack_player': attack_player,
    'move_relative': move_relative,
    'leave': leave,
    'tp': tp,
}

const host = process.env.MC_HOST;
const trace = process.env.TRACE;
const trace_start_timestamp = process.env.START_TIMESTAMP;
const workers = new Set();

let bot;
let lastHealth;
let lastFood;

function appendLog(fname, issuer, receiver, action){
    const time = Date.now();
    appendFile(fname, `${time}, ${issuer}, ${receiver}, ${action} \n`, (error) => {
        if(error){
            parentPort.postMessage(`Error appending an update to a file ${error.message}`); 
        }
    });
}

async function tp(bot, args){
    bot.waitForChunksToLoad().then(() => {
        appendLog('received.csv', bot._client.username, bot._client.username, 'tp');
    })
}

async function join(bot, args){
    parentPort.postMessage(`joining the bot in the game`);
    return new Promise((resolve, reject) => {
        bot.once("spawn", () => {
            bot.waitForChunksToLoad().then(() => {
                appendLog('received.csv', bot._client.username, bot._client.username, 'join');

                bot.loadPlugin(pathfinder);
                const defaultMove = new Movements(bot);
                bot.pathfinder.setMovements(defaultMove);

                bot.on('health', () => {
                    if (bot.health !== lastHealth || bot.food !== lastFood) {
                        lastHealth = bot.health;
                        lastFood = bot.food;

                        appendLog('received.csv', bot._client.username, bot._client.username, 'health_change');
                    }
                });
                
                bot.on('death', () => {
                    bot.respawn()
                })

                resolve();
            });
        });
    });
}

async function leave(bot, args){
    bot.end();
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
        let [x, y, z] = args;
        x = Number(x);
        y = Number(y);
        z = Number(z);

        console.log(args);

        if(!(x & y & z)){
            reject('Block coordinates are not specified');
        }
        console.log('2');

        const xBot = bot.entity.position.x;
        const yBot = bot.entity.position.y;
        const zBot = bot.entity.position.z;
        console.log('3');
        const target = bot.blockAt(Vec3(xBot + x, yBot + y, zBot + z));
        console.log(xBot + x, yBot + y, zBot + z);

        if(!(target & bot.canDigBlock(target))){
            reject('Cannot dig specified block');
        }

        bot.dig(target).then(() => {
            console.log('4');
            resolve();
        });
    })
}

function is_slot_occupied(bot, slot) {
    const item = bot.inventory.slots[slot];
    return item !== null && item !== undefined;
}

async function place_block(bot, args){
    const INVENTORY_SLOT = 36;
    console.log("I am executing place block");

    return new Promise((resolve, reject) => {
        let [itemId, x, y, z, xFaceAgainst, yFaceAgainst, zFaceAgainst] = args;

        itemId = Number(itemId);
        x = Number(x);
        y = Number(y);
        z = Number(z);

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
                    const xBot = bot.entity.position.x;
                    const yBot = bot.entity.position.y;
                    const zBot = bot.entity.position.z;

                    var targetBlock = bot.blockAt(Vec3(Math.floor(xBot + x), Math.floor(yBot + y), Math.floor((zBot + z))));
                    console.log(Math.floor(xBot + x), Math.floor(yBot + y), Math.floor((zBot + z)));
                    bot.placeBlock(targetBlock, new Vec3(xFaceAgainst, yFaceAgainst, zFaceAgainst)).catch((error) => { resolve();}).then(() => {resolve();});
                });
            }).catch((error) => {
                const inventoryItem = bot.inventory.findInventoryItem(itemId, null);

                bot.equip(inventoryItem, 'hand').then(() => {
                    const xBot = bot.entity.position.x;
                    const yBot = bot.entity.position.y;
                    const zBot = bot.entity.position.z;

                    var targetBlock = bot.blockAt(Vec3(Math.floor(xBot + x), Math.floor(yBot + y), Math.floor((zBot + z))));
                    console.log(Math.floor(xBot + x), Math.floor(yBot + y), Math.floor((zBot + z)));
                    bot.placeBlock(targetBlock, new Vec3(xFaceAgainst, yFaceAgainst, zFaceAgainst)).catch((error) => { resolve();}).then(() => {resolve();});
                });
            });
        });
    });
}

async function attack_entity(bot, args) {
    return new Promise(async (resolve, reject) => {
        const [entityType] = args;

        const entity = bot.nearestEntity(entity => entity.name.toLowerCase() === entityType);
        if (!entity) {
            return reject('Requested entity was not found');
        }

        const moveAndAttack = async () => {
            try {
                // Move towards the entity until in attack range
                while (calc_distance(entity.position, bot.entity.position) > 3) {
                    console.log('Moving towards the entity');
                    const { x: targetX, z: targetZ } = entity.position;
                    const { x: botX, z: botZ } = bot.entity.position;

                    const dx = targetX - botX;
                    const dz = targetZ - botZ;

                    const length = Math.sqrt(dx * dx + dz * dz);
                    const stepX = dx / length;
                    const stepZ = dz / length;

                    const nextX = botX + stepX;
                    const nextZ = botZ + stepZ;

                    await move(bot, [nextX, nextZ]);
                }

                bot.stopDigging();
                bot.attack(entity);
            } catch (error) {
                reject(error);
            }
        };

        while (entity.isValid) {
            console.log('Attacking entity');
            console.log(entity.health);
            await moveAndAttack();
            
            await sleep(100);
        }

        resolve('');
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
                    const { x: targetX, z: targetZ } = entity.position;
                    const { x: botX, z: botZ } = bot.entity.position;

                    const dx = targetX - botX;
                    const dz = targetZ - botZ;

                    const length = Math.sqrt(dx * dx + dz * dz);
                    const stepX = dx / length;
                    const stepZ = dz / length;

                    const nextX = botX + stepX;
                    const nextZ = botZ + stepZ;

                    await move(player_name, [nextX, nextZ]);
                }

                bot.stopDigging();
                bot.attack(entity);
                resolve('');
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

        bot.pathfinder.setGoal(new GoalXZ(x, z));
        bot.pathfinder.movements.canDig = false;
        bot.pathfinder.movements.canPlace = false;

        const cleanup = () => {
            bot.removeListener('goal_reached', onGoalReached);
            bot.removeListener('path_update', onPathUpdate);
            bot.removeListener('pathfinder_error', onPathfinderError);
        };

        const onGoalReached = () => {
            cleanup();
            appendLog('received.csv', bot._client.username, bot._client.username, 'goal_reached');
            resolve();
        };
    
        const onPathUpdate = (r) => {
            if (r.status === 'noPath') {
                cleanup();
                console.log('No path to goal');
                reject('No path to goal');
            }
        };
    
        const onPathfinderError = (error) => {
            cleanup();
            reject(error);
        };
    
        bot.once('goal_reached', onGoalReached);
        bot.once('path_update', onPathUpdate);
        bot.once('pathfinder_error', onPathfinderError);
    });
}

async function move_relative(bot, args){
    return new Promise((resolve, reject) => {
        let [x, z] = args;
        x = Number(x);
        z = Number(z);

        const xBot = bot.entity.position.x;
        const zBot = bot.entity.position.z;

        if (!(x && z)){
            resolve('Coordinates are not specified');
        }

        bot.pathfinder.setGoal(new GoalXZ(xBot + x, zBot + z));
        bot.pathfinder.movements.canDig = false;
        bot.pathfinder.movements.canPlace = false;

        const cleanup = () => {
            bot.removeListener('goal_reached', onGoalReached);
            bot.removeListener('path_update', onPathUpdate);
            bot.removeListener('pathfinder_error', onPathfinderError);
        };

        const onGoalReached = () => {
            cleanup();
            appendLog('received.csv', bot._client.username, bot._client.username, 'goal_reached');
            resolve();
        };
    
        const onPathUpdate = (r) => {
            if (r.status === 'noPath') {
                cleanup();
                console.log('No path to goal');
                reject('No path to goal');
            }
        };
    
        const onPathfinderError = (error) => {
            cleanup();
            reject(error);
        };
    
        bot.once('goal_reached', onGoalReached);
        bot.once('path_update', onPathUpdate);
        bot.once('pathfinder_error', onPathfinderError);
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
                appendLog('issued.csv', player_name, player_name, action);
                bot = mineflayer.createBot({
                    host: host,
                    username: player_name,
                    port: 25565,                // only set if you need a port that isn't 25565
                    version: '1.20.1',
                    checkTimeoutInterval: 1000 * 100000
                });        
            } else{
                appendLog('issued.csv', bot._client.username, arguments, action);
            }

            const handler = ACTION_HANDLERS[action];

            if(!handler){
                console.log('there is no handler');
                continue;
            }
            try{
                await handler(bot, arguments);
            } catch (error){
                parentPort.postMessage(`Error processing action ${action}: ${error.message}`);
            }
        } else{
            await sleep(1000);
        }
    }
}

parentPort.postMessage(`script was started`);

player_worker([]);