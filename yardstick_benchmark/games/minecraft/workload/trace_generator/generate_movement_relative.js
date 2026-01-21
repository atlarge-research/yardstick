const fs = require('fs');

function gaussianRandom(mu = 0, sigma = 1) {
  let u1 = 1 - Math.random();
  let u2 = 1 - Math.random();
  let z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mu + z0 * sigma;
}

function generateLog() {
  const args = process.argv.slice(2); // Skip the first two arguments (node and script name)
  const numPlayers = args[0] ? parseInt(args[0], 10) : 5; // Default to 5 if not provided
  const globalAttachment = args[1] ? parseInt(args[1], 10) : 5000; // Default to 5000 if not provided
  const localAttachment = args[2] ? parseFloat(args[2]) : 0; // Default to 0 if not provided
  const fpath = args[3];

  const log = [];
  let timestamp = 0;
  const joinInterval = 1000;
  const moveInterval = Math.round(1000 / 4);
  const maxTime = 20 * 60 * 1000;

  function getRandomCoordinates() {
    const x = Math.round(gaussianRandom(0, globalAttachment));
    const y = Math.round(gaussianRandom(0, globalAttachment));
    return [x, y];
  }

  function getMovementSteps(fromX, fromY, toX, toY) {
    const distanceX = toX - fromX;
    const distanceY = toY - fromY;

    const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);

    let stepX = 0;
    let stepY = 0;
    if (distance > 0) {
      stepX = Math.round(distanceX / distance);
      stepY = Math.round(distanceY / distance);
    }
  
    return [stepX, stepY];
  }

  // Players join the game
  for (let i = 1; i <= numPlayers; i++) {
    log.push(`${timestamp} player_${i} join`);
    timestamp += joinInterval;
  }

  const playerDestinations = [];

  for (let i = 0; i < numPlayers; i++) {

    if(i > 0){

      const rand = Math.random()
      if (rand < localAttachment){
        playerDestinations.push(playerDestinations[i - 1]);
        continue;
      }
      
    }
    playerDestinations.push(getRandomCoordinates());
  }

  const playerPositions = new Array(numPlayers).fill(null).map(() => ({
    currentX: 0,
    currentY: 0
  }));

  // Move players at the same time until maxTime
  while (timestamp < maxTime) {
    timestamp += moveInterval;

    // Move all players simultaneously
    for (let i = 0; i < numPlayers; i++) {
      const player = playerDestinations[i];
      const position = playerPositions[i];

      // Move the player one step at a time
      if (position.currentX !== player.endX || position.currentY !== player.endY) {
        const [stepX, stepY] = getMovementSteps(position.currentX, position.currentY, player[0], player[1]);
        log.push(`${timestamp} player_${i + 1} move_relative ${stepX} ${stepY}`);
      }
    }
  }

  fs.writeFileSync(fpath, log.join('\n'), 'utf8');
}

generateLog();

