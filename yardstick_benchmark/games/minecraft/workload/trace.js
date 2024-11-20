const fs = require('node:fs');
const readline = require('readline');
const { Worker, isMainThread } = require("worker_threads");

const trace = process.env.TRACE;
const trace_start_timestamp = parseInt(process.env.START_TIMESTAMP);
const timeout_s = parseInt(process.env.DURATION);

const players = {};

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function run(){
    const fileStream = fs.createReadStream(trace);
    const rl = readline.createInterface({
        input: fileStream,
        output: process.stdout
    });

    const benchmark_starting_time = new Date();
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

            await sleep(100);
        }

        if(!players[player]){
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

    rl.on("error", () => {
        console.log('Error while reading a trace file');
        process.exit(1);
    });

    rl.on("end", async () => {
        console.log("we have reached the end of the line");
        process.exit(0);
    })

    await sleep(timeout_s * 1000)
    process.exit(0);
}

if (isMainThread) {
    run();
}