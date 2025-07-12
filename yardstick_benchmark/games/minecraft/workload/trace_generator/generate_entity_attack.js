const fs = require('fs');

function generateLog() {
  const log = [];
  let timestamp = 0;
  const args = process.argv.slice(2);
  const numPlayers = args[0] ? parseInt(args[0], 10) : 5;
  const attackInterval = args[1] ? parseFloat(args[1]) : 0;
  const duration = args[2] ? parseInt(args[2]) * 1000 : 0;
  const fpath = args[3];

  const joinInterval = 1000;
  const battleStartDelay = 10000;

  for (let i = 1; i <= numPlayers; i++) {
    log.push(`${timestamp} player_${i} join`);
    timestamp += joinInterval;
  }

  timestamp += battleStartDelay;

  while(timestamp < duration) {
    for (let i = 1; i <= numPlayers; i++) {
      const player = `player_${i}`;
      log.push(`${timestamp} ${player} attack_entity pig`);
    }
    timestamp += attackInterval * 1000; 
  }

  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();
