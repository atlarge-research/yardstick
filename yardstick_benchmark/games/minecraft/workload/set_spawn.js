const { Rcon } = require('rcon-client');

const host = process.env.MC_HOST;
const spawn_x = process.env.SPAWN_X;
const spawn_z = process.env.SPAWN_Y;
const password = process.env.RCON_PASSWORD || 'password';
const port = parseInt(process.env.RCON_PORT || '25575', 10);

async function main() {
    const rcon = await Rcon.connect({ host, port, password });
    console.log('Connected and authenticated.');
    const response = await rcon.send(`setworldspawn ${spawn_x} 4 ${spawn_z}`);
    console.log(`Response: ${response}`);
    await rcon.end();
}

main().catch((error) => {
    console.error(`set_spawn failed: ${error}`);
    process.exit(1);
});
