var RCON = require('./rcon/RCON');
var rcon = new RCON();

const host = process.env.MC_HOST;
const spawn_x = process.env.SPAWN_X;
const spawn_z = process.env.SPAWN_Y;

rcon.connect(host, 25575, 'password')
    .then(() => {
        console.log('Connected and authenticated.');
        return rcon.send(`setworldspawn ${spawn_x} 4 ${spawn_z}`);
    })
    .then(response => {
        console.log(`Response: ${response}`);
        rcon.end();
    })
    .catch(error => {
        console.error(`An error occured: ${error}`);
    });
