const fs = require('fs');

function gaussianRandom(mu = 0, sigma = 1) {
  let randomNumber = Math.random() * ((mu + sigma) - (mu - sigma)) + (mu - sigma);

  return (parseInt(randomNumber) * 512) - 256;
}

function generateLog() {
  const args = process.argv.slice(2);
  const numPlayers = parseInt(args[0]);
  const leavesPerSecond = parseFloat(args[1]);
  const burstiness = parseInt(args[2]);
  const fpath = args[3];

  const log = [];
  let timestamp = 0;
  const leaveInterval = parseInt(1000 / leavesPerSecond);
  const joinInterval = 10000;

  for(var i = 0; i < numPlayers; i++){
    const player = `player_${i}`;
    log.push(`${timestamp} ${player} join`);

    timestamp += joinInterval / 2;
    log.push(`${timestamp} ${player} tp ${gaussianRandom(0, 1000)} ${gaussianRandom(0, 1000)}`);

    timestamp += joinInterval / 2;
  }

  timestamp += 10000

  let playersLogged = numPlayers - 1;

  while (playersLogged >= 0){
    for(var j = 0; j < burstiness; j++){
        const player = `player_${playersLogged}`;
        log.push(`${timestamp} ${player} leave`);
        playersLogged--;

        if(playersLogged > 0) break;
    }

    timestamp += leaveInterval * burstiness;
  }

  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();
