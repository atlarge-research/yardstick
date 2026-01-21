const fs = require('node:fs');
const readline = require('readline');
const { Worker, isMainThread } = require("worker_threads");
const { appendFile } = require('node:fs/promises');
const Rcon = require('rcon');

const host = process.env.MC_HOST;
var rcon = new Rcon(host, 25575, 'password');
const trace = process.env.TRACE;

const trace_start_timestamp = parseInt(process.env.START_TIMESTAMP);
const timeout_s = parseInt(process.env.DURATION);

const players = {};

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function tp(player, arguments){
    const [x, z] = arguments;
    rcon.send(`tp ${player} ${x} -60 ${z}`);

    rcon.once('response', (response) => {
        if (response.includes(player)) {
            players[player].postMessage({ action: 'tp', arguments: arguments });
        }
    });
}

async function run(){
    console.log('script starts');

    rcon.on('auth', async () => {
        const fileStream = fs.createReadStream(trace);
        const rl = readline.createInterface({
            input: fileStream,
            output: process.stdout
        });

        const benchmark_starting_time = new Date();
        console.log('authenticated');
        let benchmark_starting_timestamp = benchmark_starting_time.valueOf();

        rl.on("line", async (line) => {
            let [timestamp, player, action, ...arguments] = line.split(' ');

            timestamp = Number(timestamp);

            while(true) {
                const current_time = new Date();
                let current_timestamp = current_time.valueOf();

                if((current_timestamp - benchmark_starting_timestamp) > (timestamp - trace_start_timestamp)){
                    break;
                }

                await sleep(1000);
            }

            if(action == 'tp'){
                tp(player, arguments);
            } else if(!players[player]){
                console.log('initalizing a new one!');
                const worker = new Worker("./trace_bot.js");
                players[player] = worker;

                worker.on('message', (result) => {
                    console.log(`Received from worker (player: ${player}): ${result}`);
                });

                worker.on('error', (error) => {
                    console.error(`Worker error for player ${player}:`, error);
                });

                worker.on('exit', (code) => {
                    if (code !== 0) {
                        console.error(`Worker stopped with exit code ${code} for player ${player}`);
                    }
                });

                players[player].postMessage({ action, arguments: [player] });
            } else{
                players[player].postMessage({ action, arguments });
            }
        });
    });
    
    rcon.on('end', () => {
        console.log("RCON connection closed.");
    });
    
    rcon.on('error', (err) => {
        console.error("RCON error:", err);
    });
    
    rcon.connect();

    await sleep(timeout_s * 1000)
    process.exit(0);
}

if (isMainThread) {
    run();
}