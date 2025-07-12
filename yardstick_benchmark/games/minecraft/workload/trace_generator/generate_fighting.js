const fs = require('fs');

function generateLog() {
  const log = [];
  let timestamp = 0;
  const args = process.argv.slice(2);
  const numPlayers = args[0] ? parseInt(args[0], 10) : 5;
  const attackInterval = args[1] ? parseFloat(args[1]) : 0;
  const fpath = args[2];

  const joinInterval = 1000;
  const battleStartDelay = 10000;

  const maxTime = 20 * 60 * 1000;

  // Ensure the number of players is even for pairing
  if (numPlayers % 2 !== 0) {
    throw new Error("Number of players must be even to create pairs.");
  }

  // Players join the game
  for (let i = 1; i <= numPlayers; i++) {
    log.push(`${timestamp} player_${i} join`);
    timestamp += joinInterval;
  }

  // Reset timestamp for synchronized battles
  timestamp += battleStartDelay;

  // Players start battling in pairs
  while(timestamp < maxTime) {
    for (let i = 1; i <= numPlayers; i += 2) {
      const player1 = `player_${i}`;
      const player2 = `player_${i + 1}`;
      log.push(`${timestamp} ${player1} attack_player ${player2}`);
      log.push(`${timestamp} ${player2} attack_player ${player1}`);
    }
    timestamp += attackInterval * 1000; // Increment timestamp after each round of attacks
  }

  // Write the log to a file
  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

// Generate the log file
generateLog();
