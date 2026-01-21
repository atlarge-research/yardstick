const fs = require('fs');

function gaussianRandom(mu = 0, sigma = 1) {
  let randomNumber = Math.random() * ((mu + sigma) - (mu - sigma)) + (mu - sigma);

  return (parseInt(randomNumber) * 512) - 256;
}


function generateLog() {
  const args = process.argv.slice(2);
  const numPlayers = parseInt(args[0]);
  const globalSpread = parseInt(args[1]);
  const numTpsPerSecond = parseFloat(args[2]);
  const duration = parseInt(args[3]) * 1000;
  const fpath = args[4];

  const log = [];
  let timestamp = 0;
  const joinInterval = 1000;

  const tpInterval = parseInt((1 / numTpsPerSecond) * 1000);

  function getRandomCoordinates() {
    const x = Math.round(gaussianRandom(0, globalSpread));
    const y = Math.round(gaussianRandom(0, globalSpread));
    return [x, y];
  }

  for (let i = 1; i <= numPlayers; i++) {
    log.push(`${timestamp} player_${i} join`);
    timestamp += joinInterval;
  }

  players_tped = 0;
  while (timestamp < duration){
    const currentPlayer = (players_tped % numPlayers) + 1;

    let [tpX, tpY] = getRandomCoordinates();
    log.push(`${timestamp} player_${currentPlayer} tp ${tpX} ${tpY}`);

    players_tped += 1; 
    timestamp += tpInterval;
  }

  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();
