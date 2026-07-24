const fs = require('fs');
const path = require('path');
const { sessions } = require('../session');
const { runCmd } = require('../transport');

const SCRIPT_PATH = path.join(__dirname, '..', 'uninstall.sh');

// The script is shipped as a file rather than a template string so it stays
// runnable standalone; the GUI feeds it options through YS_* env vars.
function buildCommand({ dryRun, purge, nvm, keepProcesses, scratchUser }) {
  const env = [
    `YS_DRY_RUN=${dryRun ? 1 : 0}`,
    `YS_YES=1`,
    `YS_PURGE=${purge ? 1 : 0}`,
    `YS_NVM=${nvm ? 1 : 0}`,
    `YS_KEEP_PROCESSES=${keepProcesses ? 1 : 0}`,
  ];
  if (scratchUser) env.push(`YS_SCRATCH_USER=${JSON.stringify(scratchUser)}`);
  const script = fs.readFileSync(SCRIPT_PATH, 'utf8');
  return `${env.map((e) => `export ${e}`).join('\n')}\n${script}`;
}

function registerUninstallHandlers(socket) {
  // Dry run: report what would be removed, change nothing.
  socket.on('uninstall:preview', async ({ sessionId, username, mode, purge, nvm }) => {
    const session = sessions.get(sessionId);
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }

    const isDas = mode === 'das5' || mode === 'das6';
    const cmd = buildCommand({
      dryRun: true,
      purge,
      nvm,
      keepProcesses: true,
      scratchUser: isDas ? (username || session.username) : null,
    });

    try {
      const res = await runCmd(session, cmd, socket, 'uninstall-preview');
      socket.emit('uninstall:preview-ready', { output: res.stdout });
    } catch (err) {
      socket.emit('uninstall:error', { message: `Preview failed: ${err.message}` });
    }
  });

  socket.on('uninstall:run', async ({ sessionId, username, mode, purge, nvm }) => {
    const session = sessions.get(sessionId);
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }

    const isDas = mode === 'das5' || mode === 'das6';
    const cmd = buildCommand({
      dryRun: false,
      purge,
      nvm,
      keepProcesses: false,
      scratchUser: isDas ? (username || session.username) : null,
    });

    socket.emit('log', { message: 'Uninstalling Yardstick from the connected host...' });
    try {
      await runCmd(session, cmd, socket, 'uninstall');
      // Whatever was there is gone: reset the Setup tab's view of the host.
      const gone = { miniconda: false, condaEnv: false, packages: false, ansible: false, workspace: !purge };
      socket.emit('env:detected', { checks: gone, allReady: false });
      socket.emit('uninstall:complete', {});
      socket.emit('log', { message: 'Uninstall complete.' });
    } catch (err) {
      socket.emit('uninstall:error', { message: err.message });
      socket.emit('log', { message: `Uninstall failed: ${err.message}`, level: 'error' });
    }
  });
}

module.exports = { registerUninstallHandlers };
