const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const { Client } = require('ssh2');
const { spawn } = require('child_process');
const { v4: uuidv4 } = require('uuid');
const os = require('os');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const clientDist = path.join(__dirname, '..', 'client', 'dist');
app.use(express.static(clientDist));

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
});

const sessions = new Map();

function runLocal(command, socket, stepId) {
  return new Promise((resolve, reject) => {
    if (stepId) socket.emit('step:start', { stepId });

    const proc = spawn('bash', ['-lc', command], {
      env: { ...process.env, HOME: os.homedir() },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      const text = data.toString();
      stdout += text;
      socket.emit('terminal:data', { stepId, data: text });
    });

    proc.stderr.on('data', (data) => {
      const text = data.toString();
      stderr += text;
      socket.emit('terminal:data', { stepId, data: text, isStderr: true });
    });

    proc.on('close', (code) => {
      if (code === 0 || code === null) {
        if (stepId) {
          socket.emit('step:complete', { stepId, code });
          socket.emit('log', { message: `[OK] Step ${stepId} done` });
        } else {
          socket.emit('step:complete', { stepId, stdout, stderr, code });
          socket.emit('log', { message: `[OK] Command finished (exit ${code})` });
        }
        resolve({ stdout, stderr, code });
      } else {
        if (stepId) {
          socket.emit('step:error', { stepId, stdout, stderr, code });
          socket.emit('log', { message: `[FAIL] Step ${stepId} failed (exit ${code})`, level: 'error' });
        } else {
          socket.emit('step:error', { stepId, stdout, stderr, code });
          socket.emit('log', { message: `[FAIL] Command failed (exit ${code})`, level: 'error' });
        }
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    proc.on('error', (err) => {
      if (stepId) socket.emit('step:error', { stepId, message: err.message });
      socket.emit('log', { message: `[FAIL] ${err.message}`, level: 'error' });
      reject(err);
    });
  });
}

function runSSH(session, command, socket, stepId) {
  return new Promise((resolve, reject) => {
    if (stepId) socket.emit('step:start', { stepId });

    const wrapped = `bash -l <<'__YARDSTICK_SCRIPT__'
${command}
__YARDSTICK_SCRIPT__`;

    session.conn.exec(wrapped, (err, stream) => {
      if (err) {
        if (stepId) socket.emit('step:error', { stepId, message: err.message });
        socket.emit('log', { message: `[FAIL] ${err.message}`, level: 'error' });
        return reject(err);
      }

      let stdout = '';
      let stderr = '';

      stream.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        socket.emit('terminal:data', { stepId, data: text });
      });

      stream.stderr.on('data', (data) => {
        const text = data.toString();
        stderr += text;
        socket.emit('terminal:data', { stepId, data: text, isStderr: true });
      });

      stream.on('close', (code) => {
        if (code === 0 || code === null) {
          if (stepId) {
            socket.emit('step:complete', { stepId, code });
            socket.emit('log', { message: `[OK] Step ${stepId} done` });
          } else {
            socket.emit('step:complete', { stepId, stdout, stderr, code });
            socket.emit('log', { message: `[OK] Command finished (exit ${code})` });
          }
          resolve({ stdout, stderr, code });
        } else {
          if (stepId) {
            socket.emit('step:error', { stepId, stdout, stderr, code });
            socket.emit('log', { message: `[FAIL] Step ${stepId} failed (exit ${code})`, level: 'error' });
          } else {
            socket.emit('step:error', { stepId, stdout, stderr, code });
            socket.emit('log', { message: `[FAIL] Command failed (exit ${code})`, level: 'error' });
          }
          reject(new Error(`Command failed with exit code ${code}`));
        }
      });
    });
  });
}

function runCmd(session, command, socket, stepId) {
  socket.emit('log', { message: `$ ${command}`, level: 'cmd' });
  if (session.type === 'local') {
    return runLocal(command, socket, stepId);
  }
  return runSSH(session, command, socket, stepId);
}

function buildPipelineCommands(mode, user) {
  const isLocal = mode === 'local';
  const condaDir = isLocal ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
  const scratchDir = isLocal ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;

  return {
    installMiniconda: [
      `set -e`,
      `target_dir=${condaDir}`,
      `if [ -f "$target_dir/bin/conda" ]; then`,
      `  echo "[OK] Miniconda already installed at $target_dir -- skipping."`,
      `else`,
      `  echo "Downloading Miniconda..."`,
      `  mkdir -p "$target_dir"`,
      `  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O "$target_dir/miniconda.sh"`,
      `  bash "$target_dir/miniconda.sh" -b -u -p "$target_dir"`,
      `  rm -rf "$target_dir/miniconda.sh"`,
      `  echo "[OK] Miniconda installed."`,
      `fi`,
      `"$target_dir/bin/conda" init bash 2>/dev/null || true`,
    ].join('\n'),

    createEnv: [
      `set -e`,
      `export PATH="${condaDir}/bin:$PATH"`,
      `eval "$(conda shell.bash hook)"`,
      `if conda env list | grep -q "^yardstick "; then`,
      `  echo "[OK] Conda env 'yardstick' already exists -- skipping creation."`,
      `else`,
      `  echo "Creating conda env 'yardstick' with Python 3.9..."`,
      `  conda create -n yardstick python=3.9 -y 2>&1`,
      `  echo "[OK] Env created."`,
      `fi`,
    ].join('\n'),

    installDeps: [
      `set -e`,
      `export PATH="${condaDir}/bin:$PATH"`,
      `eval "$(conda shell.bash hook)"`,
      `conda activate yardstick`,
      `if python -c "import yardstick_benchmark" 2>/dev/null; then`,
      `  echo "[OK] yardstick-benchmark already installed."`,
      `else`,
      `  echo "Installing packages..."`,
      `  conda install -y jupyter pandas seaborn 2>&1`,
      `  pip install yardstick-benchmark 2>&1`,
      `  echo "[OK] Packages installed."`,
      `fi`,
    ].join('\n'),

    setupWorkspace: [
      `set -e`,
      `mkdir -p ~/yardstick-tutorial`,
      `cd ~/yardstick-tutorial`,
      `if [ -f "example.ipynb" ]; then`,
      `  echo "[OK] example.ipynb already exists -- skipping download."`,
      `else`,
      `  echo "Downloading example notebook..."`,
      `  wget -q https://raw.githubusercontent.com/atlarge-research/yardstick/master/example.ipynb -O example.ipynb 2>&1 || echo "[WARN] Download failed, you can copy it manually."`,
      `  echo "[OK] Workspace set up."`,
      `fi`,
      `ls -la ~/yardstick-tutorial`,
    ].join('\n'),

    verifyInstall: [
      `set -e`,
      `export PATH="${condaDir}/bin:$PATH"`,
      `eval "$(conda shell.bash hook)"`,
      `conda activate yardstick`,
      `python -c "import yardstick_benchmark; print('[OK] yardstick-benchmark imported successfully')" 2>&1`,
    ].join('\n'),

    condaDir,
    scratchDir,
  };
}

io.on('connection', (socket) => {
  console.log(`[ws] client connected: ${socket.id}`);

  socket.on('ssh:connect', (opts) => {
    const {
      host, port = 22, username, password, privateKey, mode = 'das5',
      jumpHost, jumpPort = 22, jumpUsername, jumpPassword, jumpPrivateKey,
    } = opts;
    const sessionId = uuidv4();
    const useJump = !!(jumpHost && jumpUsername);

    function emitError(err) {
      let hint = '';
      const msg = err.message || String(err);
      if (msg.includes('EHOSTUNREACH') || msg.includes('ETIMEDOUT') || msg.includes('ECONNREFUSED') || msg.includes('Timed out')) {
        hint = ' - The host is unreachable. Make sure you are on the VU campus network or connected to eduVPN, and that the jump host is correct.';
      }
      socket.emit('ssh:error', { message: msg + hint });
      socket.emit('log', { message: `[FAIL] SSH error: ${msg}${hint}`, level: 'error' });
    }

    function targetConnectOpts(sock) {
      const o = { host, port: parseInt(port, 10), username };
      if (sock) o.sock = sock;          // tunnel stream from jump host
      if (privateKey) o.privateKey = privateKey;
      else if (password) o.password = password;
      o.hostVerifier = () => true;
      o.readyTimeout = 15000;
      return o;
    }

    function onTargetReady(conn, jumpConn) {
      sessions.set(sessionId, { type: 'ssh', conn, jumpConn, host, username, mode, cwd: '~' });
      socket.emit('ssh:connected', { sessionId, mode });
      socket.emit('log', { message: `[OK] Connected to ${host} as ${username}${useJump ? ` (via ${jumpHost})` : ''}` });
    }

    try {
      if (useJump) {
        socket.emit('log', { message: `Connecting to jump host ${jumpHost}...` });
        const jumpConn = new Client();

        jumpConn.on('ready', () => {
          socket.emit('log', { message: `[OK] Jump host connected, tunnelling to ${host}:${port}...` });

          jumpConn.forwardOut('127.0.0.1', 0, host, parseInt(port, 10), (err, stream) => {
            if (err) {
              emitError(err);
              jumpConn.end();
              return;
            }

            const targetConn = new Client();

            targetConn.on('ready', () => onTargetReady(targetConn, jumpConn));
            targetConn.on('error', (err) => { emitError(err); jumpConn.end(); });
            targetConn.on('close', () => {
              sessions.delete(sessionId);
              jumpConn.end();
              socket.emit('ssh:disconnected', { sessionId });
              socket.emit('log', { message: 'Connection closed.' });
            });

            targetConn.connect(targetConnectOpts(stream));
          });
        });

        jumpConn.on('error', (err) => emitError(err));
        jumpConn.on('close', () => {
          if (sessions.has(sessionId)) {
            sessions.delete(sessionId);
            socket.emit('ssh:disconnected', { sessionId });
            socket.emit('log', { message: 'Jump host connection closed.' });
          }
        });

        const jumpOpts = {
          host: jumpHost,
          port: parseInt(jumpPort, 10),
          username: jumpUsername,
          hostVerifier: () => true,
          readyTimeout: 15000,
        };
        if (jumpPrivateKey) jumpOpts.privateKey = jumpPrivateKey;
        else if (jumpPassword) jumpOpts.password = jumpPassword;

        jumpConn.connect(jumpOpts);
      } else {
        socket.emit('log', { message: `Connecting to ${host}...` });
        const conn = new Client();

        conn.on('ready', () => onTargetReady(conn, null));
        conn.on('error', (err) => emitError(err));
        conn.on('close', () => {
          sessions.delete(sessionId);
          socket.emit('ssh:disconnected', { sessionId });
          socket.emit('log', { message: 'Connection closed.' });
        });

        conn.connect(targetConnectOpts());
      }
    } catch (err) {
      socket.emit('ssh:error', { message: err.message });
    }
  });

  socket.on('local:connect', () => {
    const sessionId = uuidv4();
    const username = os.userInfo().username;
    sessions.set(sessionId, { type: 'local', host: 'localhost', username, mode: 'local', cwd: os.homedir() });
    socket.emit('log', { message: `[OK] Local mode active (${username}@localhost)` });
    socket.emit('ssh:connected', { sessionId, mode: 'local' });
  });

  socket.on('ssh:exec', ({ sessionId, command, stepId }) => {
    const session = sessions.get(sessionId);
    if (!session) {
      socket.emit('ssh:error', { message: 'No active session.' });
      return;
    }

    const CWD_MARKER = '::__CWD__::';
    const isManual = stepId === 'custom';
    let wrappedCmd = command;
    if (isManual && session.cwd) {
      wrappedCmd = `cd ${JSON.stringify(session.cwd)} 2>/dev/null; ${command}\n__yg_ec=$?; echo "${CWD_MARKER}$(pwd)"; exit $__yg_ec`;
    }

    if (isManual) {
      const origEmit = socket.emit.bind(socket);
      const patchedSocket = {
        emit: (event, data) => {
          if (event === 'terminal:data' && data && typeof data.data === 'string') {
            const lines = data.data.split('\n');
            const filtered = lines.filter((line) => {
              if (line.startsWith(CWD_MARKER)) {
                session.cwd = line.slice(CWD_MARKER.length).trim();
                return false;
              }
              return true;
            });
            if (filtered.length > 0) {
              origEmit(event, { ...data, data: filtered.join('\n') });
            }
            return;
          }
          origEmit(event, data);
        },
      };
      runCmd(session, wrappedCmd, patchedSocket, stepId).catch(() => {});
    } else {
      runCmd(session, command, socket, stepId).catch(() => {});
    }
  });

  socket.on('ssh:detect-env', async ({ sessionId, username: dasUsername, mode: clientMode }) => {
    const session = sessions.get(sessionId);
    if (!session) {
      socket.emit('ssh:error', { message: 'No active session.' });
      return;
    }

    const mode = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const isLocal = mode === 'local';
    const condaDir = isLocal ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;

    socket.emit('log', { message: 'Detecting existing environment...' });

    const checks = {
      miniconda: false,
      condaEnv: false,
      packages: false,
      workspace: false,
    };

    function probe(label, cmd, timeoutMs = 15000) {
      return new Promise((resolve) => {
        let settled = false;
        const timer = setTimeout(() => {
          if (!settled) {
            settled = true;
            socket.emit('log', { message: `  [TIMEOUT] ${label}: timed out after ${timeoutMs / 1000}s`, level: 'warn' });
            resolve(false);
          }
        }, timeoutMs);
        function done(ok, detail) {
          if (!settled) {
            settled = true;
            clearTimeout(timer);
            socket.emit('log', { message: `  ${ok ? '[OK]' : '[MISS]'} ${label}${detail ? ': ' + detail : ''}` });
            resolve(ok);
          }
        }
        if (session.type === 'local') {
          const proc = spawn('bash', ['-lc', cmd], { env: { ...process.env, HOME: os.homedir() } });
          proc.on('close', (code) => done(code === 0, `exit ${code}`));
          proc.on('error', (e) => done(false, e.message));
        } else {
          const wrappedCmd = `bash -l <<'__YS_PROBE__'
${cmd}
__YS_PROBE__`;
          session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
            if (err) return done(false, `exec error: ${err.message}`);
            let stdoutBuf = '';
            let stderrBuf = '';
            stream.on('data', (d) => { stdoutBuf += d.toString(); });
            stream.stderr.on('data', (d) => { stderrBuf += d.toString(); });
            stream.on('exit', (code, signal) => {
              done(code === 0, `exit ${code}${stderrBuf ? ', stderr: ' + stderrBuf.trim().slice(0, 100) : ''}`);
            });
            stream.on('close', () => {
              // fallback if 'exit' never fired
              if (!settled) done(false, 'stream closed without exit code');
            });
          });
        }
      });
    }

    const checkOrder = [
      { key: 'miniconda', label: 'Miniconda' },
      { key: 'condaEnv',  label: 'Conda environment' },
      { key: 'packages',  label: 'Python packages' },
      { key: 'workspace', label: 'Tutorial workspace' },
    ];

    function emitProgress(currentKey) {
      socket.emit('env:check-progress', { checks: { ...checks }, checking: currentKey });
    }

    try {
      emitProgress('miniconda');
      checks.miniconda = await probe('Miniconda', `test -f "${condaDir}/bin/conda"`);
      emitProgress(null);

      emitProgress('condaEnv');
      if (checks.miniconda) {
        checks.condaEnv = await probe('Conda env', `"${condaDir}/bin/conda" env list 2>/dev/null | grep -q "^yardstick "`);
      }
      emitProgress(null);

      emitProgress('packages');
      if (checks.condaEnv) {
        checks.packages = await probe(
          'Packages',
          `"${condaDir}/envs/yardstick/bin/python" -c "import yardstick_benchmark" 2>/dev/null`,
          20000
        );
      }
      emitProgress(null);

      emitProgress('workspace');
      checks.workspace = await probe('Workspace', 'test -f ~/yardstick-tutorial/example.ipynb');
      emitProgress(null);
    } catch (e) {
      // defaults are fine
    }

    const allReady = checks.miniconda && checks.condaEnv && checks.packages && checks.workspace;

    socket.emit('env:detected', { checks, allReady });
    socket.emit('log', {
      message: allReady
        ? 'Environment fully set up -- ready to run experiments.'
        : `Environment check: miniconda=${checks.miniconda ? 'OK' : 'MISS'} env=${checks.condaEnv ? 'OK' : 'MISS'} packages=${checks.packages ? 'OK' : 'MISS'} workspace=${checks.workspace ? 'OK' : 'MISS'}`,  
    });
  });

  socket.on('ssh:run-pipeline', async ({ sessionId, username: dasUsername, mode: clientMode }) => {
    const session = sessions.get(sessionId);
    if (!session) {
      socket.emit('ssh:error', { message: 'No active session.' });
      return;
    }

    const mode = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const cmds = buildPipelineCommands(mode, user);

    try {
      await runCmd(session, cmds.installMiniconda, socket, 'install-miniconda');
      await runCmd(session, cmds.createEnv, socket, 'create-env');
      await runCmd(session, cmds.installDeps, socket, 'install-deps');
      await runCmd(session, cmds.setupWorkspace, socket, 'setup-workspace');
      await runCmd(session, cmds.verifyInstall, socket, 'verify-install');

      socket.emit('pipeline:complete', { message: 'All steps completed successfully!' });
      socket.emit('log', { message: 'Full installation pipeline complete.' });
    } catch (err) {
      socket.emit('pipeline:error', { message: err.message });
      socket.emit('log', { message: `Pipeline failed: ${err.message}`, level: 'error' });
    }
  });

  socket.on('ssh:run-experiment', async ({ sessionId, username: dasUsername, numNodes = 2, botsPerNode = 10, sleepTime = 10, runName = '', mode: clientMode }) => {
    const session = sessions.get(sessionId);
    if (!session) {
      socket.emit('ssh:error', { message: 'No active session.' });
      return;
    }

    const mode = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const cmds = buildPipelineCommands(mode, user);
    const isLocal = mode === 'local';
    const condaDir = isLocal ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;

    function quickProbe(cmd) {
      return new Promise((resolve) => {
        let settled = false;
        const timer = setTimeout(() => { if (!settled) { settled = true; resolve(false); } }, 8000);
        function done(ok) { if (!settled) { settled = true; clearTimeout(timer); resolve(ok); } }
        if (session.type === 'local') {
          const proc = spawn('bash', ['-lc', cmd], { env: { ...process.env, HOME: os.homedir() } });
          proc.on('close', (code) => done(code === 0));
          proc.on('error', () => done(false));
        } else {
          const wrappedCmd = `bash -l <<'__YS_PROBE__'
${cmd}
__YS_PROBE__`;
          session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
            if (err) return done(false);
            stream.on('exit', (code) => done(code === 0));
            stream.on('close', () => { if (!settled) done(false); });
          });
        }
      });
    }

    try {
      socket.emit('log', { message: 'Running pre-flight checks...' });
      const pf = {
        miniconda:  await quickProbe(`test -f "${condaDir}/bin/conda"`),
        condaEnv:   false,
        packages:   false,
        workspace:  await quickProbe('test -f ~/yardstick-tutorial/example.ipynb'),
      };
      if (pf.miniconda) {
        pf.condaEnv = await quickProbe(`"${condaDir}/bin/conda" env list 2>/dev/null | grep -q "^yardstick "`);
      }
      if (pf.condaEnv) {
        pf.packages = await quickProbe(`"${condaDir}/envs/yardstick/bin/python" -c "import yardstick_benchmark" 2>/dev/null`);
      }

      const missing = [];
      if (!pf.miniconda)  missing.push('Miniconda');
      if (!pf.condaEnv)   missing.push('Conda environment (yardstick)');
      if (!pf.packages)   missing.push('Python packages (yardstick-benchmark)');
      if (!pf.workspace)  missing.push('Tutorial workspace (~/yardstick-tutorial)');

      if (missing.length > 0) {
        socket.emit('experiment:preflight-failed', { missing });
        socket.emit('log', { message: `Pre-flight failed - missing: ${missing.join(', ')}`, level: 'error' });
        return;
      }
      socket.emit('log', { message: '[OK] Pre-flight checks passed.' });
    } catch (pfErr) {
      socket.emit('experiment:preflight-failed', { missing: ['Unable to verify environment - run Setup first.'] });
      socket.emit('log', { message: `Pre-flight error: ${pfErr.message}`, level: 'error' });
      return;
    }

    try {
      const isLocalMode = mode === 'local';
      const safeName = runName.replace(/[^a-zA-Z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').slice(0, 60);

      const dasExperimentScript = `
from yardstick_benchmark.provisioning import Das
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.minecraft.server import PaperMC
from yardstick_benchmark.games.minecraft.workload import WalkAround
import yardstick_benchmark
from time import sleep
from datetime import datetime
from pathlib import Path
import os

das = Das()
nodes = das.provision(num=${numNodes})
try:
    yardstick_benchmark.clean(nodes)

    telegraf = Telegraf(nodes)
    telegraf.add_input_jolokia_agent(nodes[0])
    telegraf.add_input_execd_minecraft_ticks(nodes[0])
    telegraf.deploy()

    papermc = PaperMC(nodes[:1])
    papermc.deploy()
    papermc.start()

    telegraf.start()

    wl = WalkAround(nodes[1:], nodes[0].host, bots_per_node=${botsPerNode})
    wl.deploy()
    wl.start()
    print('Experiment running, sleeping for ${sleepTime}s...')
    sleep(${sleepTime})

    papermc.stop()
    telegraf.stop()

    timestamp = datetime.now().isoformat(timespec='minutes').replace('-','').replace(':','')
    run_label = '${safeName}_' + timestamp if '${safeName}' else timestamp
    dest = Path(f'${cmds.scratchDir.replace(/\$/g, '')}/' + run_label)
    yardstick_benchmark.fetch(dest, nodes)
    print(f'Results saved to {dest}')
finally:
    yardstick_benchmark.clean(nodes)
    das.release(nodes)
    print('Done!')
`;

      const localExperimentScript = `
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.minecraft.server import PaperMC
from yardstick_benchmark.games.minecraft.workload import WalkAround
import yardstick_benchmark
import yardstick_benchmark.model as _ym
from time import sleep
from datetime import datetime
from pathlib import Path
import os

_orig_gen_inv = _ym._gen_inv
def _patched_gen_inv(name, nodes):
    inv = _orig_gen_inv(name, nodes)
    for host, hvars in inv['all']['hosts'].items():
        if host in ('localhost', '127.0.0.1'):
            hvars['ansible_connection'] = 'local'
    return inv
_ym._gen_inv = _patched_gen_inv

home = os.path.expanduser('~')
wd_base = Path(home) / 'yardstick' / 'run'

nodes = [
    Node(host='localhost', wd=wd_base / f'node{i:03d}')
    for i in range(${numNodes})
]

try:
    yardstick_benchmark.clean(nodes)

    telegraf = Telegraf(nodes)
    telegraf.add_input_jolokia_agent(nodes[0])
    telegraf.add_input_execd_minecraft_ticks(nodes[0])
    telegraf.deploy()

    papermc = PaperMC(nodes[:1])
    papermc.deploy()
    papermc.start()

    telegraf.start()

    wl = WalkAround(nodes[1:], nodes[0].host, bots_per_node=${botsPerNode})
    wl.deploy()
    wl.start()
    print('Experiment running, sleeping for ${sleepTime}s...')
    sleep(${sleepTime})

    papermc.stop()
    telegraf.stop()

    timestamp = datetime.now().isoformat(timespec='minutes').replace('-','').replace(':','')
    run_label = '${safeName}_' + timestamp if '${safeName}' else timestamp
    dest = Path(home) / 'yardstick' / run_label
    yardstick_benchmark.fetch(dest, nodes)
    print(f'Results saved to {dest}')
finally:
    yardstick_benchmark.clean(nodes)
    print('Done!')
`;

      const experimentScript = isLocalMode ? localExperimentScript : dasExperimentScript;

      const pythonBin = `${cmds.condaDir}/envs/yardstick/bin/python`;
      const experimentCmd = `cd ~/yardstick-tutorial && ${pythonBin} <<'__YS_EXPERIMENT__'
${experimentScript}
__YS_EXPERIMENT__`;

      await runCmd(session, experimentCmd, socket, 'run-experiment');

      socket.emit('experiment:complete', { message: 'Experiment finished!' });
      socket.emit('log', { message: 'Experiment completed successfully.' });
    } catch (err) {
      socket.emit('experiment:error', { message: err.message });
      socket.emit('log', { message: `Experiment failed: ${err.message}`, level: 'error' });
    }
  });

  socket.on('results:list', async ({ sessionId, mode: clientMode, username: dasUsername }) => {
    const session = sessions.get(sessionId);
    if (!session) return socket.emit('results:error', { message: 'No active session.' });

    const m = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const isLocal = m === 'local';
    const scratchDir = isLocal ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
    const cmd = `ls -1d ${scratchDir}/*/ 2>/dev/null | while read d; do basename "$d"; done`;

    function execOnce(command) {
      return new Promise((resolve, reject) => {
        if (session.type === 'local') {
          let out = '';
          const proc = spawn('bash', ['-lc', command], { env: { ...process.env, HOME: os.homedir() } });
          proc.stdout.on('data', (d) => { out += d.toString(); });
          proc.stderr.on('data', () => {});
          proc.on('close', (code) => resolve(out.trim()));
          proc.on('error', (e) => reject(e));
        } else {
          const wrappedCmd = `bash -l <<'__YS_EXEC__'
${command}
__YS_EXEC__`;
          session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
            if (err) return reject(err);
            let out = '';
            stream.on('data', (d) => { out += d.toString(); });
            stream.stderr.on('data', () => {});
            stream.on('exit', () => resolve(out.trim()));
            stream.on('close', () => resolve(out.trim()));
          });
        }
      });
    }

    try {
      const raw = await execOnce(cmd);
      const runs = raw ? raw.split('\n').filter(Boolean).reverse() : [];
      socket.emit('results:list-ok', { runs, scratchDir });
    } catch (err) {
      socket.emit('results:error', { message: err.message });
    }
  });

  socket.on('results:load', async ({ sessionId, runId, mode: clientMode, username: dasUsername }) => {
    const session = sessions.get(sessionId);
    if (!session) return socket.emit('results:error', { message: 'No active session.' });

    const m = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const isLocal = m === 'local';
    const scratchDir = isLocal ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
    const runDir = `${scratchDir}/${runId}`;

    function execOnce(command) {
      return new Promise((resolve, reject) => {
        if (session.type === 'local') {
          let out = '';
          let errOut = '';
          const proc = spawn('bash', ['-lc', command], { env: { ...process.env, HOME: os.homedir() } });
          proc.stdout.on('data', (d) => { out += d.toString(); });
          proc.stderr.on('data', (d) => { errOut += d.toString(); });
          proc.on('close', () => resolve({ stdout: out, stderr: errOut }));
          proc.on('error', (e) => reject(e));
        } else {
          const wrappedCmd = `bash -l <<'__YS_EXEC__'
${command}
__YS_EXEC__`;
          session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
            if (err) return reject(err);
            let out = '';
            let errOut = '';
            stream.on('data', (d) => { out += d.toString(); });
            stream.stderr.on('data', (d) => { errOut += d.toString(); });
            stream.on('exit', () => resolve({ stdout: out, stderr: errOut }));
            stream.on('close', () => resolve({ stdout: out, stderr: errOut }));
          });
        }
      });
    }

    try {
      socket.emit('results:loading');

      const parseScript = `
import glob, json, sys, os
from pathlib import Path

run_dir = "${runDir}"

# Debug: list all files in the run directory
all_files = glob.glob(f"{run_dir}/**/*", recursive=True)
print(f"DEBUG:FILES_IN_RUN_DIR:{len(all_files)}", file=sys.stderr)
for f in all_files[:50]:
    print(f"  {f}", file=sys.stderr)

raw_files = glob.glob(f"{run_dir}/**/metrics-*.csv", recursive=True)
print(f"DEBUG:RAW_METRICS_FILES:{len(raw_files)}", file=sys.stderr)
for f in raw_files:
    print(f"  {f}", file=sys.stderr)

for raw_file in raw_files:
    p = Path(raw_file)
    keys = {}
    with open(p) as fin:
        for line in fin:
            first = line.find(",")
            second = line.find(",", first + 1)
            key = line[first+1:second]
            if key not in keys:
                keys[key] = open(p.parent / f"{key}.csv", "w")
            keys[key].write(line)
    for fd in keys.values():
        fd.close()

cpu_data = []
cpu_files = glob.glob(f"{run_dir}/**/cpu.csv", recursive=True)
for cpu_file in cpu_files:
    node_name = Path(cpu_file).parent.parent.name
    with open(cpu_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 17:
                continue
            cpu_label = parts[3]
            if cpu_label != "cpu-total":
                continue
            ts = int(parts[0])
            time_active = float(parts[6]) if parts[6] else 0
            time_idle = float(parts[9]) if parts[9] else 0
            total = time_active + time_idle
            util = round(100 * time_active / total, 2) if total > 0 else 0
            cpu_data.append({"ts": ts, "node": node_name, "util": util})

tick_data = []
tick_files = glob.glob(f"{run_dir}/**/minecraft_tick_times.csv", recursive=True)
for tick_file in tick_files:
    with open(tick_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 5:
                continue
            ts = int(parts[0])
            try:
                dur = float(parts[4])
            except ValueError:
                continue
            tick_data.append({"ts": ts, "dur": dur})

mem_data = []
mem_files = glob.glob(f"{run_dir}/**/mem.csv", recursive=True)
for mem_file in mem_files:
    node_name = Path(mem_file).parent.parent.name
    with open(mem_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            ts = int(parts[0])
            try:
                used_pct = float(parts[5])
            except (ValueError, IndexError):
                continue
            mem_data.append({"ts": ts, "node": node_name, "pct": round(used_pct, 2)})

if cpu_data:
    t0 = min(d["ts"] for d in cpu_data)
    for d in cpu_data:
        d["t"] = round((d["ts"] - t0) / 60, 2)
        del d["ts"]
if tick_data:
    t0 = min(d["ts"] for d in tick_data)
    for d in tick_data:
        d["t"] = round((d["ts"] - t0) / 60, 2)
        del d["ts"]
if mem_data:
    t0 = min(d["ts"] for d in mem_data)
    for d in mem_data:
        d["t"] = round((d["ts"] - t0) / 60, 2)
        del d["ts"]

nodes_found = sorted(set(d["node"] for d in cpu_data)) if cpu_data else []

result = {"cpu": cpu_data, "tick": tick_data, "mem": mem_data, "nodes": nodes_found}
print(json.dumps(result))
`;

      const cmds = buildPipelineCommands(m, user);
      const pythonBin = `${cmds.condaDir}/envs/yardstick/bin/python3`;
      const command = `${pythonBin} <<'__YS_PYTHON__'
${parseScript}
__YS_PYTHON__`;

      const result = await execOnce(command);
      const raw = result.stdout || '';
      const debugStderr = result.stderr || '';

      // Log debug info from the parse script
      if (debugStderr) {
        const debugLines = debugStderr.split('\n').filter(l => l.startsWith('DEBUG:') || l.startsWith('  '));
        if (debugLines.length > 0) {
          console.log('[results:load] parse debug:', debugLines.join('\n'));
          socket.emit('log', { message: `Parse debug: ${debugLines.slice(0, 5).join('; ')}`, level: 'info' });
        }
      }

      const jsonStart = raw.indexOf('{');
      if (jsonStart === -1) {
        const hint = debugStderr ? ` Debug: ${debugStderr.slice(0, 300)}` : '';
        socket.emit('results:error', { message: `No data found for this run. The experiment may not have produced metrics.${hint}` });
        return;
      }
      const data = JSON.parse(raw.slice(jsonStart));
      socket.emit('results:data', { runId, data });
    } catch (err) {
      socket.emit('results:error', { message: `Failed to load results: ${err.message}` });
    }
  });

  socket.on('ssh:disconnect', ({ sessionId }) => {
    const session = sessions.get(sessionId);
    if (session) {
      if (session.type === 'ssh') {
        if (session.conn) session.conn.end();
        if (session.jumpConn) session.jumpConn.end();
      }
      sessions.delete(sessionId);
    }
    socket.emit('ssh:disconnected', { sessionId });
  });

  socket.on('disconnect', () => {
    console.log(`[ws] client disconnected: ${socket.id}`);
  });
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', activeSessions: sessions.size });
});

// SPA fallback - serve index.html for any non-API route
app.get('*', (req, res) => {
  res.sendFile(path.join(clientDist, 'index.html'));
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Yardstick GUI server running on http://localhost:${PORT}`);
});

module.exports = server;
