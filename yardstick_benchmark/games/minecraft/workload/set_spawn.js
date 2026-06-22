var RCON = require('./RCON');
var rcon = new RCON();

const host = process.env.MC_HOST;

// On a normal (non-superflat) world the generator already places the world
// spawn on a safe surface block near the origin, which is where the WalkAround
// box is centred. We therefore do not override it. Pinning a fixed Y (the old
// behaviour used y=4, correct only for the flat world) would bury the bots
// underground on normal terrain, where WalkAround (canDig=false) cannot move.
rcon.connect(host, 25575, 'password')
    .then(() => {
        console.log('Connected and authenticated. Using natural surface spawn.');
        rcon.end();
    })
    .catch(error => {
        console.error(`An error occured: ${error}`);
    });
