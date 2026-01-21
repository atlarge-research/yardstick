const fs = require('fs');

function generateLog() {
  const args = process.argv.slice(2);
  const numPlayers = parseInt(args[0]);
  const joinsPerSecond = parseFloat(args[1]);
  const burstiness = parseInt(args[2]);
  const fpath = args[3];

  const log = [];
  let timestamp = 0;
  const joinInterval = parseInt(1000 / joinsPerSecond);

  let playersLogged = 0;

  while(playersLogged < numPlayers){
    for(let j = 0; j < burstiness; j++){
        const player = `player_${playersLogged + 1}`;
        log.push(`${timestamp} ${player} join`);

        playersLogged += 1;
    }
    timestamp += joinInterval * burstiness;
  }

  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();
