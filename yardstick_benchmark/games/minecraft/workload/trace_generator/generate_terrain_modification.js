const fs = require('fs');

function generateLog() {
    const args = process.argv.slice(2);
    const numPlayers = args[0] ? parseInt(args[0], 10) : 5;
    const buildInterval = parseFloat(args[1]) * 1000;
    const blocksAtATime = parseInt(args[2]);
    const duration = parseInt(args[3]);
    const fpath = args[4];

    const log = [];
    const possibleBuildingDirection = [[1, 0, 0], [1, 0, 1], [0, 0, 1], [-1, 0, 1], [-1, 0, 0], [-1, 0, -1], [0, 0, -1], [1, 0, -1]];
    let timestamp = 0;

    if(args.length < 5){
        console.error('Not enough arguments');
        process.exit(1);
    }
    
    if(blocksAtATime < 1 || blocksAtATime > 8){
        console.error('Blocks at a time should be between 1 and 9');
        process.exit(1);
    }

    const joinInterval = 1000;
    const buildingStartDelay = 10000;

    for (let i = 1; i <= numPlayers; i++) {
        log.push(`${timestamp} player_${i} join`);
        timestamp += joinInterval;
    }

    timestamp += buildingStartDelay;

    while(timestamp < duration * 1000) {
        for(let i = 0; i < blocksAtATime; i++){
            for (let j = 1; j <= numPlayers; j++) {
                const player = `player_${j}`;
                const [x, y, z] = possibleBuildingDirection[i];
                log.push(`${timestamp} ${player} place_block 1 ${x} ${y} ${z} 0 1 0`);
            }

            timestamp += Math.trunc(buildInterval / (2 * blocksAtATime) );
        }

        for(let i = 0; i < blocksAtATime; i++){
            for (let j = 1; j <= numPlayers; j++) {
                const player = `player_${j}`;
                const [x, y, z] = possibleBuildingDirection[i];
                log.push(`${timestamp} ${player} remove_block ${x} ${y} ${z}`);
            }

            timestamp += Math.trunc(buildInterval / (2 * blocksAtATime) );
        }
    }

    fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();
