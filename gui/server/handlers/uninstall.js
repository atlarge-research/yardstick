const fs = require('fs');
const path = require('path');
const { sessions } = require('../session');
const { runCmd } = require('../transport');
const { isHomeMode, runEnvChecks } = require('../environment');

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
    // keepProcesses stays off so the preview lists the processes that would be
    // stopped; a dry run exits before anything is actually killed.
    const cmd = buildCommand({
      dryRun: true,
      purge,
      nvm,
      keepProcesses: false,
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

      // Re-probe rather than assuming: the Setup tab must show what is actually
      // on the host, and this also catches a removal that reported success but
      // left the installation in place.
      const user = username || session.username;
      const condaDir = isHomeMode(mode) ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
      const { checks } = await runEnvChecks(session, condaDir, socket);

      if (checks.miniconda || checks.condaEnv || checks.packages) {
        const still = Object.entries(checks).filter(([, v]) => v).map(([k]) => k).join(', ');
        socket.emit('uninstall:error', {
          message: `Uninstall reported success but the installation is still present (${still}). Nothing was left in a half-removed state that the Setup tab cannot fix, but the removal did not take effect.`,
        });
        return;
      }

      socket.emit('uninstall:complete', {});
      socket.emit('log', { message: 'Uninstall complete.' });
    } catch (err) {
      socket.emit('uninstall:error', { message: err.message });
      socket.emit('log', { message: `Uninstall failed: ${err.message}`, level: 'error' });
    }
  });
}

module.exports = { registerUninstallHandlers };
