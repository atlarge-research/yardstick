const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const { Client } = require('ssh2');
const { spawn } = require('child_process');
const { v4: uuidv4 } = require('uuid');
const os = require('os');
const path = require('path');
const { register: registerCloud, getSocketAws } = require('./cloud');

const app = express();
app.use(cors());
app.use(express.json());

const clientDist = path.join(__dirname, '..', 'client', 'dist');
app.use(express.static(clientDist));

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] },
});

registerCloud(io);

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
        const err = new Error(`Command failed with exit code ${code}`);
        err.stdout = stdout;
        err.stderr = stderr;
        reject(err);
      }
    });

    proc.on('error', (err) => {
      if (stepId) socket.emit('step:error', { stepId, message: err.message });
      socket.emit('log', { message: `[FAIL] ${err.message}`, level: 'error' });
      const e = new Error(err.message);
      e.stdout = '';
      e.stderr = err.message;
      reject(e);
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
          const err = new Error(`Command failed with exit code ${code}`);
          err.stdout = stdout;
          err.stderr = stderr;
          reject(err);
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

// Query EC2 instance metadata service (IMDS) over SSH to auto-detect AMI/region
// when the user connected via plain SSH instead of the Cloud panel "Use" flow.
// Supports both IMDSv1 and IMDSv2 (token-required) transparently.
function queryImds(session) {
  if (session.type !== 'ssh') return Promise.resolve({});
  const cmd = `python3 -c "
import urllib.request, json
def _get(path):
    try:
        try:
            treq = urllib.request.Request('http://169.254.169.254/latest/api/token', headers={'X-aws-ec2-metadata-token-ttl-seconds':'21600'}, method='PUT')
            tok = urllib.request.urlopen(treq, timeout=3).read().decode().strip()
            req = urllib.request.Request('http://169.254.169.254/latest/meta-data/'+path, headers={'X-aws-ec2-metadata-token':tok})
        except:
            req = 'http://169.254.169.254/latest/meta-data/'+path
        return urllib.request.urlopen(req, timeout=3).read().decode().strip()
    except:
        return None
mac = (_get('network/interfaces/macs/') or '').strip().strip('/')
sg_ids = [s.strip() for s in (_get(f'network/interfaces/macs/{mac}/security-group-ids') or '').splitlines() if s.strip()]
key_raw = _get('public-keys/') or ''
key_name = key_raw.split('=',1)[1].strip() if '=' in key_raw else None
print(json.dumps({'imageId':_get('ami-id'),'region':_get('placement/region'),'instanceType':_get('instance-type'),'securityGroupIds':sg_ids,'keyName':key_name}))
"`;
  return new Promise((resolve) => {
    session.conn.exec(cmd, (err, stream) => {
      if (err) return resolve({});
      let out = '';
      stream.on('data', (d) => { out += d.toString(); });
      stream.stderr.on('data', () => {});
      stream.on('close', () => {
        try { resolve(JSON.parse(out.trim())); } catch { resolve({}); }
      });
    });
  });
}

// Path layout: DAS uses /var/scratch/<user>/...; everything else (local, aws,
// azure, custom-ssh) uses $HOME-relative paths since /var/scratch only exists
// on the DAS clusters.
function isHomeMode(mode) {
  return mode === 'local' || mode === 'aws' || mode === 'azure' || mode === 'custom-ssh';
}

function buildPipelineCommands(mode, user) {
  const useHome = isHomeMode(mode);
  const condaDir = useHome ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
  const scratchDir = useHome ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;

  return {
    installMiniconda: [
      `set -e`,
      `free_gb=$(df -BG "$HOME" | awk 'NR==2{gsub(/G/,""); print $4+0}')`,
      `echo "Disk space available: \${free_gb}GB"`,
      `if [ "\${free_gb:-0}" -lt 8 ]; then`,
      `  echo "[FAIL] Only \${free_gb}GB free disk space. At least 8GB required (recommend 20GB). Resize the root volume in the AWS console and try again." >&2`,
      `  exit 1`,
      `fi`,
      `target_dir=${condaDir}`,
      `if [ -f "$target_dir/bin/conda" ]; then`,
      `  echo "[OK] Miniconda already installed at $target_dir -- skipping."`,
      `else`,
      `  echo "Downloading Miniconda..."`,
      `  mkdir -p "$target_dir"`,
      `  url=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`,
      `  if command -v wget >/dev/null 2>&1; then`,
      `    wget -q "$url" -O "$target_dir/miniconda.sh"`,
      `  elif command -v curl >/dev/null 2>&1; then`,
      `    curl -fsSL "$url" -o "$target_dir/miniconda.sh"`,
      `  else`,
      `    echo "[FAIL] Neither wget nor curl is available on this host." >&2`,
      `    exit 1`,
      `  fi`,
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
      `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true`,
      `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true`,
      `if conda env list | grep -q "^yardstick "; then`,
      `  echo "[OK] Conda env 'yardstick' already exists -- skipping creation."`,
      `else`,
      `  echo "Creating conda env 'yardstick' with Python 3.10..."`,
      `  conda create -n yardstick python=3.10 -y 2>&1`,
      `  echo "[OK] Env created."`,
      `fi`,
    ].join('\n'),

    installDeps: [
      `set -e`,
      // Ensure at least 2 GB of swap so conda metadata + solve doesn't OOM on
      // small instances (t3.micro = 1 GB RAM). Safe to run repeatedly.
      `swap_mb=$(free -m | awk '/^Swap:/{print $2}')`,
      `if [ "\${swap_mb:-0}" -lt 2048 ]; then`,
      `  echo "Swap is \${swap_mb}MB — creating 2GB swapfile..."`,
      `  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 2>/dev/null`,
      `  sudo chmod 600 /swapfile`,
      `  sudo mkswap /swapfile`,
      `  sudo swapon /swapfile`,
      `  echo "[OK] Swap enabled: $(free -m | awk '/^Swap:/{print $2}')MB"`,
      `fi`,
      `export PATH="${condaDir}/bin:$PATH"`,
      `eval "$(conda shell.bash hook)"`,
      `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true`,
      `conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true`,
      `conda activate yardstick`,
      `if python -c "import yardstick_benchmark" 2>/dev/null; then`,
      `  echo "[OK] yardstick-benchmark already installed."`,
      `else`,
      `  echo "Installing packages..."`,
      `  conda install -y jupyter pandas seaborn 2>&1`,
      `  python -m pip install yardstick-benchmark 2>&1`,
      `  echo "[OK] Packages installed."`,
      `fi`,
      `if ! test -f "$CONDA_PREFIX/bin/ansible-playbook"; then`,
      `  echo "Installing Ansible CLI..."`,
      `  python -m pip install "ansible>=8,<9" 2>&1`,
      `fi`,
      // PaperMC requires Java. On DAS, compute nodes load java via 'module load'.
      // On cloud/local hosts install Java via the system package manager so we get
      // a plain OpenJDK — conda-forge's openjdk brings in GraalVM which injects its
      // own GraalPy site-packages into sys.path and breaks ansible_runner's fcntl.
      `if conda list -n yardstick openjdk 2>/dev/null | grep -q '^openjdk'; then`,
      `  echo "Removing conda-forge openjdk (GraalVM) from yardstick env..."`,
      `  conda remove -n yardstick -y openjdk 2>&1 || true`,
      `fi`,
      `if ! command -v java >/dev/null 2>&1; then`,
      `  echo "Installing Java..."`,
      `  if command -v apt-get >/dev/null 2>&1; then`,
      `    sudo -n apt-get update -q 2>&1 || true`,
      `    sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-17-jdk-headless 2>&1`,
      `  elif command -v dnf >/dev/null 2>&1; then`,
      `    sudo -n dnf install -y java-latest-openjdk-headless 2>&1`,
      `  elif command -v yum >/dev/null 2>&1; then`,
      `    sudo -n yum install -y java-latest-openjdk-headless 2>&1`,
      `  else`,
      `    echo "[WARN] No supported package manager found to install Java. PaperMC will fail." >&2`,
      `  fi`,
      `fi`,
      // Cloud/local hosts also need system tools the WalkAround Ansible playbook
      // assumes are already there: rsync (for fetch/synchronize), wget (for the
      // nvm-installer task), git (for the node-rcon clone), and Node.js >=18 +
      // npm so 'node walkaround_bot.js' and 'npm install mineflayer' work even
      // when the playbook's 'source ~/.bashrc; nvm use 18' chain fails silently
      // on non-interactive shells. DAS is excluded — head-node sudo isn't
      // available and compute nodes provide these via 'module load'.
      ...(useHome ? [
        `echo "Checking system tools required by the workload..."`,
        // Install node/npm via NodeSource FIRST so we get node 20 + bundled npm
        // in one shot, avoiding distro nodejs 12 which drags in libnode-dev and
        // then conflicts when NodeSource tries to upgrade.
        `node_major=0`,
        `if command -v node >/dev/null 2>&1; then`,
        `  node_major=$(node -e 'process.stdout.write(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)`,
        `fi`,
        `if [ "\${node_major:-0}" -lt 18 ]; then`,
        `  echo "Node.js is $node_major (<18); installing Node 20 from NodeSource..."`,
        `  if command -v dnf >/dev/null 2>&1; then`,
        `    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo -n bash - && sudo -n dnf install -y nodejs`,
        `  elif command -v apt-get >/dev/null 2>&1; then`,
        `    sudo -n DEBIAN_FRONTEND=noninteractive apt-get remove -y libnode-dev nodejs npm 2>/dev/null || true`,
        `    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -nE bash - && sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs`,
        `  else`,
        `    echo "[WARN] Cannot upgrade Node.js automatically. Install Node >=18 manually." >&2`,
        `  fi`,
        `fi`,
        // Now install remaining tools (rsync, wget, git). npm/nodejs handled above.
        `need=""`,
        `command -v rsync >/dev/null 2>&1 || need="$need rsync"`,
        `command -v wget  >/dev/null 2>&1 || need="$need wget"`,
        `command -v git   >/dev/null 2>&1 || need="$need git"`,
        `if [ -n "$need" ]; then`,
        `  echo "Installing system packages:$need"`,
        `  if command -v dnf >/dev/null 2>&1; then`,
        `    sudo -n dnf install -y $need 2>&1 || { echo "[WARN] dnf install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v apt-get >/dev/null 2>&1; then`,
        `    sudo -n apt-get update -q 2>&1 || true`,
        `    sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y $need 2>&1 || { echo "[WARN] apt install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v yum >/dev/null 2>&1; then`,
        `    sudo -n yum install -y $need 2>&1 || { echo "[WARN] yum install failed; you may need to install manually:$need" >&2; }`,
        `  else`,
        `    echo "[WARN] No supported package manager (dnf/apt/yum) found. Install manually:$need" >&2`,
        `  fi`,
        `else`,
        `  echo "[OK] System tools already present."`,
        `fi`,
      ] : []),
    ].join('\n'),

    setupWorkspace: [
      `set -e`,
      `mkdir -p ~/experiments`,
      `echo "[OK] Workspace directory ready: ~/experiments"`,
      `ls -la ~/experiments`,
    ].join('\n'),

    verifyInstall: [
      `set -e`,
      `export PATH="${condaDir}/bin:$PATH"`,
      `eval "$(conda shell.bash hook)"`,
      `conda activate yardstick`,
      `python -c "import yardstick_benchmark; print('[OK] yardstick-benchmark imported successfully')" 2>&1`,
      `test -f "$CONDA_PREFIX/bin/ansible-playbook" || { echo '[FAIL] ansible-playbook is not in the yardstick env.' >&2; exit 1; }`,
      `if java -version >/dev/null 2>&1; then`,
      `  echo "[OK] java: $(java -version 2>&1 | head -1)"`,
      `else`,
      `  echo "[WARN] java is not on PATH. PaperMC will fail to start." >&2`,
      `fi`,
      ...(useHome ? [
        `for tool in rsync wget git node npm; do`,
        `  if command -v "$tool" >/dev/null 2>&1; then`,
        `    case "$tool" in`,
        `      node) echo "[OK] node $(node --version)" ;;`,
        `      npm)  echo "[OK] npm $(npm --version 2>/dev/null)" ;;`,
        `      *)    echo "[OK] $tool ($(command -v $tool))" ;;`,
        `    esac`,
        `  else`,
        `    echo "[WARN] $tool not found -- the WalkAround workload will fail." >&2`,
        `  fi`,
        `done`,
      ] : []),
    ].join('\n'),

    condaDir,
    scratchDir,
  };
}

async function runEnvChecks(session, condaDir, socket) {
  const checks = { miniconda: false, condaEnv: false, packages: false, ansible: false, workspace: false };

  function probe(label, cmd, timeoutMs = 15000) {
    return new Promise((resolve) => {
      let settled = false;
      const timer = setTimeout(() => {
        if (!settled) { settled = true; socket.emit('log', { message: `  [TIMEOUT] ${label}: timed out after ${timeoutMs / 1000}s`, level: 'warn' }); resolve(false); }
      }, timeoutMs);
      function done(ok, detail) {
        if (!settled) {
          settled = true; clearTimeout(timer);
          socket.emit('log', { message: `  ${ok ? '[OK]' : '[MISS]'} ${label}${detail ? ': ' + detail : ''}` });
          resolve(ok);
        }
      }
      if (session.type === 'local') {
        const proc = spawn('bash', ['-lc', cmd], { env: { ...process.env, HOME: os.homedir() } });
        proc.on('close', (code) => done(code === 0, `exit ${code}`));
        proc.on('error', (e) => done(false, e.message));
      } else {
        const wrappedCmd = `bash -l <<'__YS_PROBE__'\n${cmd}\n__YS_PROBE__`;
        session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
          if (err) return done(false, `exec error: ${err.message}`);
          let stderrBuf = '';
          stream.stderr.on('data', (d) => { stderrBuf += d.toString(); });
          stream.on('exit', (code) => { done(code === 0, `exit ${code}${stderrBuf ? ', stderr: ' + stderrBuf.trim().slice(0, 100) : ''}`); });
          stream.on('close', () => { if (!settled) done(false, 'stream closed without exit code'); });
        });
      }
    });
  }

  function emitProgress(key) {
    socket.emit('env:check-progress', { checks: { ...checks }, checking: key });
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
      checks.packages = await probe('Packages', `"${condaDir}/bin/conda" run -n yardstick python -c "import yardstick_benchmark" 2>/dev/null`, 30000);
    }
    emitProgress(null);

    emitProgress('ansible');
    if (checks.packages) {
      checks.ansible = await probe('Ansible', `test -f "${condaDir}/envs/yardstick/bin/ansible-playbook"`);
    }
    emitProgress(null);

    emitProgress('workspace');
    checks.workspace = await probe('Workspace', 'test -d ~/experiments');
    emitProgress(null);
  } catch (e) {
    // defaults are fine
  }

  const allReady = checks.miniconda && checks.condaEnv && checks.packages && checks.ansible && checks.workspace;
  socket.emit('env:detected', { checks, allReady });
  socket.emit('log', {
    message: allReady
      ? 'Environment fully set up -- ready to run experiments.'
      : `Environment check: miniconda=${checks.miniconda ? 'OK' : 'MISS'} env=${checks.condaEnv ? 'OK' : 'MISS'} packages=${checks.packages ? 'OK' : 'MISS'} ansible=${checks.ansible ? 'OK' : 'MISS'} workspace=${checks.workspace ? 'OK' : 'MISS'}`,
  });
  return { checks, allReady };
}

io.on('connection', (socket) => {
  console.log(`[ws] client connected: ${socket.id}`);

  socket.on('ssh:connect', (opts) => {
    const {
      host, port = 22, username, password, privateKey, mode = 'das5',
      jumpHost, jumpPort = 22, jumpUsername, jumpPassword, jumpPrivateKey,
      region, imageId, instanceType, keyName: instKeyName, securityGroupIds,
    } = opts;
    const sessionId = uuidv4();
    const useJump = !!(jumpHost && jumpUsername);

    function emitError(err, context) {
      const msg = err.message || String(err);
      let hint = '';
      const unreachable = msg.includes('EHOSTUNREACH') || msg.includes('ETIMEDOUT') || msg.includes('ECONNREFUSED') || msg.includes('Timed out');
      if (unreachable) {
        if (context === 'jump') {
          hint = ` - Cannot reach jump host ${jumpHost}. Make sure you are on the VU campus network or connected to eduVPN.`;
        } else if (context === 'target-via-jump') {
          hint = ` - Reached the jump host but cannot tunnel to ${host}:${port}. Check that the target host is correct.`;
        } else {
          hint = ` - Cannot reach ${host}:${port}. Check the host address, port, and that the server is running.`;
        }
      } else if (msg.includes('All configured authentication methods failed') || msg.includes('No supported authentication methods')) {
        hint = ' - Authentication failed. Check your username and SSH key or password.';
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
      sessions.set(sessionId, {
        type: 'ssh', conn, jumpConn, host, username, mode, cwd: '~',
        privateKey: privateKey || null,
        region: region || null,
        imageId: imageId || null,
        instanceType: instanceType || null,
        keyName: instKeyName || null,
        securityGroupIds: securityGroupIds || [],
      });
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
              emitError(err, 'target-via-jump');
              jumpConn.end();
              return;
            }

            const targetConn = new Client();

            targetConn.on('ready', () => onTargetReady(targetConn, jumpConn));
            targetConn.on('error', (err) => { emitError(err, 'target-via-jump'); jumpConn.end(); });
            targetConn.on('close', () => {
              sessions.delete(sessionId);
              jumpConn.end();
              socket.emit('ssh:disconnected', { sessionId });
              socket.emit('log', { message: 'Connection closed.' });
            });

            targetConn.connect(targetConnectOpts(stream));
          });
        });

        jumpConn.on('error', (err) => emitError(err, 'jump'));
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
        conn.on('error', (err) => emitError(err, 'direct'));
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
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }
    const mode = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const condaDir = isHomeMode(mode) ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
    socket.emit('log', { message: 'Detecting existing environment...' });
    await runEnvChecks(session, condaDir, socket);
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

      const allChecks = { miniconda: true, condaEnv: true, packages: true, ansible: true, workspace: true };
      socket.emit('env:detected', { checks: allChecks, allReady: true });
      socket.emit('pipeline:complete', { message: 'All steps completed successfully!' });
      socket.emit('log', { message: 'Full installation pipeline complete.' });
    } catch (err) {
      socket.emit('pipeline:error', { message: err.message });
      socket.emit('log', { message: `Pipeline failed: ${err.message}`, level: 'error' });
    }
  });

  socket.on('aws:launch-instances', async ({ region = 'us-east-1', count = 1, instanceType = 't3.micro', amiId = null, keyName = null, securityGroupIds = [] }) => {
    try {
      socket.emit('log', { message: `Launching ${count} instance(s) in ${region}...`, level: 'cmd' });
      const amiArg = amiId ? `--image-id ${amiId}` : '';
      const sgArg = securityGroupIds.length ? `--security-group-ids ${securityGroupIds.join(' ')}` : '';
      const keyArg = keyName ? `--key-name ${keyName}` : '';

      const runCmdStr = `aws ec2 run-instances --region ${region} ${amiArg} --count ${count} --instance-type ${instanceType} ${keyArg} ${sgArg} --query 'Instances[*].InstanceId' --output text`;
      const runRes = await runLocal(runCmdStr, socket, 'aws-launch');
      const instanceIds = runRes.stdout.trim().split(/\s+/).filter(Boolean);
      if (!instanceIds.length) throw new Error('No instance IDs returned');
      socket.emit('log', { message: `Launched instances: ${instanceIds.join(', ')}` });

      // Wait for running state
      const waitCmd = `aws ec2 wait instance-running --region ${region} --instance-ids ${instanceIds.join(' ')}`;
      await runLocal(waitCmd, socket, 'aws-wait-running');

      // Fetch public IPs
      const descCmd = `aws ec2 describe-instances --region ${region} --instance-ids ${instanceIds.join(' ')} --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,PublicIp:PublicIpAddress}' --output json`;
      const descRes = await runLocal(descCmd, socket, 'aws-describe');
      socket.emit('aws:launched', { instances: descRes.stdout });
    } catch (err) {
      const msg = err && err.message ? err.message : String(err);
      const extra = { stdout: err && err.stdout ? err.stdout : undefined, stderr: err && err.stderr ? err.stderr : undefined };
      socket.emit('log', { message: `AWS launch error: ${msg}`, level: 'error' });
      socket.emit('aws:error', { message: msg, detail: extra });
    }
  });

  socket.on('aws:terminate-instances', async ({ region = 'us-east-1', instanceIds = [] }) => {
    try {
      if (!instanceIds || instanceIds.length === 0) {
        throw new Error('No instance IDs provided');
      }
      socket.emit('log', { message: `Terminating instances: ${instanceIds.join(', ')}...`, level: 'cmd' });
      const termCmd = `aws ec2 terminate-instances --region ${region} --instance-ids ${instanceIds.join(' ')} --query 'TerminatingInstances[*].InstanceId' --output text`;
      const termRes = await runLocal(termCmd, socket, 'aws-terminate');
      socket.emit('aws:terminated', { instances: termRes.stdout.trim().split(/\s+/).filter(Boolean) });
    } catch (err) {
      const msg = err && err.message ? err.message : String(err);
      const extra = { stdout: err && err.stdout ? err.stdout : undefined, stderr: err && err.stderr ? err.stderr : undefined };
      socket.emit('log', { message: `AWS terminate error: ${msg}`, level: 'error' });
      socket.emit('aws:error', { message: msg, detail: extra });
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
    const useHome = isHomeMode(mode);
    const condaDir = useHome ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;

    try {
      socket.emit('log', { message: 'Running pre-flight checks...' });
      const { checks, allReady } = await runEnvChecks(session, condaDir, socket);
      if (!allReady) {
        const missing = [];
        if (!checks.miniconda) missing.push('Miniconda');
        if (!checks.condaEnv)  missing.push('Conda environment (yardstick)');
        if (!checks.packages)  missing.push('Python packages (yardstick-benchmark)');
        if (!checks.ansible)   missing.push('Ansible CLI');
        if (!checks.workspace) missing.push('Experiments workspace (~/experiments)');
        socket.emit('experiment:preflight-failed', { missing });
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

    const buildCloudScript = (workerIps) => `
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.minecraft.server import PaperMC
from yardstick_benchmark.games.minecraft.workload import WalkAround
import yardstick_benchmark
import yardstick_benchmark.model as _ym
from datetime import datetime, timedelta
from pathlib import Path
import os, shutil, socket as _socket, time as _time, subprocess as _sp, threading as _threading, urllib.request, shutil as _sh, glob as _glob

# Patch installed walkaround playbooks to load nvm via NVM_DIR instead of
# 'source ~/.bashrc', which is a no-op in non-interactive shells (Ubuntu dash).
try:
    import yardstick_benchmark.games.minecraft.workload as _wl_mod
    _wl_dir = os.path.dirname(_wl_mod.__file__)
    for _yml in _glob.glob(f'{_wl_dir}/*.yml'):
        _txt = open(_yml).read()
        if 'source ~/.bashrc' in _txt:
            _fixed = _txt.replace(
                'source ~/.bashrc',
                'export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"'
            )
            open(_yml, 'w').write(_fixed)
            print(f'[patch] fixed nvm loading in {os.path.basename(_yml)}', flush=True)
except Exception as _e:
    print(f'[warn] could not patch walkaround playbooks: {_e}', flush=True)

# Worker IPs injected by GUI server (empty list = single-instance mode)
_worker_ips = ${JSON.stringify(workerIps)}
_worker_user = ${JSON.stringify(session.username || 'ubuntu')}

# Resolve this instance's private IP so Ansible shows a real host name and
# WalkAround bots on worker instances can reach PaperMC via private VPC routing.
try:
    _main_ip = _socket.gethostbyname(_socket.gethostname())
except Exception:
    _main_ip = '127.0.0.1'
_local_addrs = {'localhost', '127.0.0.1', _main_ip}

# Patch Ansible inventory: main instance uses local connection, workers use SSH with injected key
_orig_gen_inv = _ym._gen_inv
def _patched_gen_inv(name, nodes):
    inv = _orig_gen_inv(name, nodes)
    for host, hvars in inv['all']['hosts'].items():
        if host in _local_addrs:
            hvars['ansible_host'] = 'localhost'
            hvars['ansible_connection'] = 'local'
            hvars['ansible_shell_executable'] = '/bin/bash'
        else:
            hvars['ansible_user'] = _worker_user
            hvars['ansible_ssh_private_key_file'] = os.path.expanduser('~/.ssh/yardstick_exp.pem')
            hvars['ansible_ssh_common_args'] = '-o StrictHostKeyChecking=no'
            hvars['ansible_shell_executable'] = '/bin/bash'
    return inv
_ym._gen_inv = _patched_gen_inv

from yardstick_benchmark.model import Node
home = os.path.expanduser('~')
wd_base = Path(home) / 'yardstick' / 'run'

papermc_node = Node(host=_main_ip, wd=wd_base / 'node000')
worker_nodes = [
    Node(host=ip, wd=Path(f'/home/{_worker_user}/yardstick/run/node{i+1:03d}'))
    for i, ip in enumerate(_worker_ips)
]
nodes = [papermc_node] + worker_nodes
wl_nodes = worker_nodes if worker_nodes else [papermc_node]

# Wait for SSH to be reachable on each worker before Ansible tries to connect
def _wait_ssh(host, timeout=300, interval=5):
    print(f'[wait-ssh] waiting for {host}:22...', flush=True)
    deadline = _time.time() + timeout
    last_report = _time.time()
    while _time.time() < deadline:
        try:
            s = _socket.create_connection((host, 22), timeout=interval)
            s.close()
            print(f'[wait-ssh] {host}:22 ready ({int(_time.time() - (deadline - timeout))}s)', flush=True)
            return
        except OSError:
            _time.sleep(interval)
            if _time.time() - last_report >= 10:
                elapsed = int(_time.time() - (deadline - timeout))
                print(f'[wait-ssh] still waiting for {host}:22 ({elapsed}s elapsed)...', flush=True)
                last_report = _time.time()
    raise RuntimeError(f'Timed out waiting {timeout}s for SSH on {host}:22')
for _ip in _worker_ips:
    _wait_ssh(_ip)

# Fresh Ubuntu instances don't ship with rsync or git; install both before Ansible runs.
_ssh_base = ['ssh', '-i', os.path.expanduser('~/.ssh/yardstick_exp.pem'),
             '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
for _ip in _worker_ips:
    print(f'[worker {_ip}] installing base tools (rsync, git)...', flush=True)
    _r = _sp.run(_ssh_base + [f'{_worker_user}@{_ip}', r"""
        # Wait up to 120s for cloud-init / unattended-upgrades to release apt locks
        i=0; while sudo fuser /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock >/dev/null 2>&1 && [ $i -lt 60 ]; do sleep 2; i=$((i+1)); done
        # Repair any interrupted dpkg state
        sudo dpkg --configure -a -q 2>/dev/null || true
        sudo apt-get install -f -y -qq 2>/dev/null || true
        # Install missing tools
        (which rsync && which git) || (sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y rsync git)
    """], capture_output=True, text=True, timeout=180)
    print(f'[worker {_ip}] base tools {"ready" if _r.returncode == 0 else "install failed: " + _r.stderr.strip()}', flush=True)

# Ansible get_url defaults to a 10s timeout with no retries. PaperMC ~50MB and
# Maven Central redirects are flaky on small instances, so pre-fetch into a
# stable cache and stage into the per-run wd. get_url with force=no (default)
# will then see the dest exists and skip.
CACHE = Path(home) / '.yardstick-cache'
CACHE.mkdir(parents=True, exist_ok=True)
DOWNLOADS = [
    ('paper-1.20.1-58.jar',
     'https://api.papermc.io/v2/projects/paper/versions/1.20.1/builds/58/downloads/paper-1.20.1-58.jar',
     1_000_000),
    ('jolokia-agent-jvm-2.0.3-javaagent.jar',
     'https://search.maven.org/remotecontent?filepath=org/jolokia/jolokia-agent-jvm/2.0.3/jolokia-agent-jvm-2.0.3-javaagent.jar',
     100_000),
]

def _ensure_cached(fname, url, min_size, retries=5, timeout=60):
    dest = CACHE / fname
    if dest.exists() and dest.stat().st_size >= min_size:
        print(f'[cache] using {dest} ({dest.stat().st_size} bytes)', flush=True)
        return dest
    last = None
    for attempt in range(1, retries + 1):
        try:
            print(f'[fetch] {url} (attempt {attempt}/{retries})', flush=True)
            tmp = dest.with_suffix(dest.suffix + '.part')
            with urllib.request.urlopen(url, timeout=timeout) as resp, open(tmp, 'wb') as f:
                shutil.copyfileobj(resp, f, length=64 * 1024)
            if tmp.stat().st_size < min_size:
                raise IOError(f'downloaded file is too small ({tmp.stat().st_size} bytes)')
            tmp.replace(dest)
            print(f'[OK] cached {dest} ({dest.stat().st_size} bytes)', flush=True)
            return dest
        except Exception as e:
            last = e
            print(f'[retry] {e}', flush=True)
            if attempt < retries:
                _time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f'failed to fetch {url}: {last}')

for fname, url, sz in DOWNLOADS:
    _ensure_cached(fname, url, sz)

def _run(label, fn):
    print(f'[>>] {label}...', flush=True)
    try:
        result = fn()
        print(f'[OK] {label}', flush=True)
        return result
    except Exception as e:
        msg = str(e)
        # ansible_runner errors include the full runner output in the message;
        # extract just the last meaningful line to keep the summary readable.
        lines = [l.strip() for l in msg.splitlines() if l.strip()]
        summary = lines[-1] if lines else msg
        print(f'[FAIL] {label}: {summary}', flush=True)
        raise RuntimeError(f'{label} failed: {summary}') from e

papermc = None
try:
    _run('Clean nodes', lambda: yardstick_benchmark.clean(nodes))

    telegraf = Telegraf(nodes)
    telegraf.add_input_jolokia_agent(nodes[0])
    telegraf.add_input_execd_minecraft_ticks(nodes[0])
    _run('Deploy Telegraf', telegraf.deploy)

    papermc = PaperMC(nodes[:1])

    # Pre-stage cached jars into the per-run wd before deploy runs so the
    # Ansible get_url tasks short-circuit.
    host = nodes[0].host
    try:
        run_wd = Path(papermc.deploy_action.inv['all']['hosts'][host]['wd'])
        run_wd.mkdir(parents=True, exist_ok=True)
        for fname, _u, _s in DOWNLOADS:
            src = CACHE / fname
            dst = run_wd / fname
            if not dst.exists() and src.exists():
                shutil.copy2(src, dst)
                print(f'[stage] {src.name} -> {dst}', flush=True)
    except Exception as e:
        print(f'[warn] pre-stage failed; Ansible will download instead: {e}', flush=True)

    _run('Deploy PaperMC', papermc.deploy)

    try:
        _run('Start PaperMC', papermc.start)
    except Exception as e:
        # Dump server log so the GUI shows the actual cause
        try:
            run_wd = Path(papermc.start_action.inv['all']['hosts'][host]['wd'])
            log_file = run_wd / 'logs' / 'latest.log'
            if log_file.exists():
                print('--- PaperMC logs/latest.log (last 80 lines) ---', flush=True)
                for line in log_file.read_text(errors='replace').splitlines()[-80:]:
                    print(line, flush=True)
                print('--- end log ---', flush=True)
            else:
                java = _sh.which('java')
                print(f'No PaperMC log found. java on PATH: {java or "(not found)"}', flush=True)
                if java:
                    out = _sp.run([java, '-version'], capture_output=True, text=True, timeout=10)
                    print((out.stderr or out.stdout).strip(), flush=True)
        except Exception:
            pass
        raise

    _run('Start Telegraf', telegraf.start)

    wl = WalkAround(wl_nodes, papermc_node.host, bots_per_node=${botsPerNode}, duration=timedelta(seconds=${sleepTime}))
    _run('Deploy WalkAround', wl.deploy)

    # Stream bot logs from each worker live while wl.start() blocks.
    # The log file (bot-{hostname}.log) is created by Ansible once the bot starts,
    # so the remote command polls for it before tailing.
    _log_stop = _threading.Event()
    def _tail_worker(ip, wd):
        remote_cmd = (
            f'for i in $(seq 0 120); do '
            f'  f=$(ls {wd}/bot-*.log 2>/dev/null | head -1); '
            f'  if [ -n "$f" ]; then exec tail -F "$f"; fi; '
            f'  sleep 1; '
            f'done'
        )
        cmd = ['ssh', '-i', os.path.expanduser('~/.ssh/yardstick_exp.pem'),
               '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
               '-o', 'ServerAliveInterval=15',
               f'{_worker_user}@{ip}', remote_cmd]
        try:
            proc = _sp.Popen(cmd, stdout=_sp.PIPE, stderr=_sp.DEVNULL, text=True, bufsize=1)
            while not _log_stop.is_set():
                line = proc.stdout.readline()
                if not line:
                    break
                print(f'[worker {ip}] {line}', end='', flush=True)
            proc.terminate()
        except Exception as e:
            print(f'[worker {ip}] log tail error: {e}', flush=True)
    _log_threads = []
    for _wip, _wnode in zip(_worker_ips, worker_nodes):
        _t = _threading.Thread(target=_tail_worker, args=(_wip, str(_wnode.wd)), daemon=True)
        _t.start()
        _log_threads.append(_t)

    try:
        _run('Run WalkAround bots', wl.start)
    finally:
        _log_stop.set()
        for _t in _log_threads:
            _t.join(timeout=3)

    _run('Stop PaperMC', papermc.stop)
    _run('Stop Telegraf', telegraf.stop)

    timestamp = datetime.now().isoformat(timespec='minutes').replace('-','').replace(':','')
    run_label = '${safeName}_' + timestamp if '${safeName}' else timestamp
    dest = Path(os.path.expanduser('~')) / 'yardstick' / run_label
    _run('Fetch results', lambda: yardstick_benchmark.fetch(dest, nodes))
    print(f'Results saved to {dest}')
finally:
    try:
        yardstick_benchmark.clean(nodes)
    except Exception as e:
        print(f'[warn] cleanup failed: {e}', flush=True)
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
            hvars['ansible_shell_executable'] = '/bin/bash'
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
      const isCloudMode = ['aws', 'azure', 'custom-ssh'].includes(mode);
      let experimentScript;
      let workerInstanceIds = [];

      try {
        if (isLocalMode) {
          experimentScript = localExperimentScript;
        } else if (isCloudMode) {
          const workerIps = [];

          let { imageId: imgId, region: reg, instanceType: instType } = session;
          if ((!imgId || !reg) && numNodes > 1) {
            socket.emit('log', { message: 'Querying instance metadata...' });
            const meta = await queryImds(session);
            imgId = imgId || meta.imageId || null;
            reg = reg || meta.region || null;
            instType = instType || meta.instanceType || null;
            if (imgId) session.imageId = imgId;
            if (reg) session.region = reg;
            if (instType) session.instanceType = instType;
            if (meta.securityGroupIds && meta.securityGroupIds.length > 0 && session.securityGroupIds.length === 0) {
              session.securityGroupIds = meta.securityGroupIds;
            }
            if (meta.keyName && !session.keyName) {
              session.keyName = meta.keyName;
            }
            socket.emit('log', { message: `Instance metadata: region=${reg} keyName=${session.keyName || 'none'} sgs=${session.securityGroupIds.join(',')}` });
          }

          if (numNodes > 1 && imgId && reg) {
            const awsProv = getSocketAws(socket.id);
            if (!awsProv) {
              socket.emit('log', { message: 'Warning: Not authenticated to AWS — launching in single-instance mode.', level: 'warn' });
            } else {
              socket.emit('log', { message: `Launching ${numNodes - 1} worker instance(s)...` });
              workerInstanceIds = await awsProv.launch({
                region: reg,
                imageId: imgId,
                instanceType: instType || 't3.small',
                keyName: session.keyName || undefined,
                securityGroupIds: session.securityGroupIds || [],
                count: numNodes - 1,
                name: 'yardstick-worker',
                diskSizeGb: 20,
              });

              // Allow SSH between instances in the same security group so the
              // main instance can Ansible into workers without internet routing.
              if (session.securityGroupIds && session.securityGroupIds.length > 0) {
                socket.emit('log', { message: 'Ensuring security group allows intra-SG SSH...' });
                await awsProv.ensureSelfIngressSSH(reg, session.securityGroupIds);
              }

              // Use private IPs — workers share a VPC so no internet routing needed.
              socket.emit('log', { message: 'Waiting for worker private IPs...' });
              const deadline = Date.now() + 300_000;
              while (Date.now() < deadline) {
                const workers = await awsProv.describeInstances(reg, workerInstanceIds);
                const ips = workers.map((w) => w.privateIp).filter(Boolean);
                if (ips.length === workerInstanceIds.length) {
                  workerIps.push(...ips);
                  break;
                }
                await new Promise((r) => setTimeout(r, 3000));
              }
              if (workerIps.length < workerInstanceIds.length) {
                throw new Error('Timed out waiting for worker instances to get private IPs');
              }
              socket.emit('log', { message: `Workers ready (private IPs): ${workerIps.join(', ')}` });

              if (session.privateKey) {
                const keyB64 = Buffer.from(session.privateKey).toString('base64');
                const writeKeyCmd = `python3 -c "import base64,os,stat; k=base64.b64decode('${keyB64}').decode(); p=os.path.expanduser('~/.ssh/yardstick_exp.pem'); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(k); os.chmod(p,0o600)"`;
                await runCmd(session, writeKeyCmd, socket, 'setup-workers');
              }
            }
          }

          experimentScript = buildCloudScript(workerIps);
        } else {
          experimentScript = dasExperimentScript;
        }

        const envBin = `${cmds.condaDir}/envs/yardstick/bin`;
        // Put the yardstick env first on PATH so Ansible local-shell tasks (used
        // in cloud mode for PaperMC/Telegraf) can resolve java and other env
        // binaries. Harmless on DAS — ansible there runs over SSH to compute
        // nodes whose PATH is set independently.
        const experimentCmd = `export PATH="${envBin}:$PATH"; cd ~/experiments && "${envBin}/python" <<'__YS_EXPERIMENT__'
${experimentScript}
__YS_EXPERIMENT__`;

        await runCmd(session, experimentCmd, socket, 'run-experiment');

        socket.emit('experiment:complete', { message: 'Experiment finished!' });
        socket.emit('results:changed');
        socket.emit('log', { message: 'Experiment completed successfully.' });
      } catch (err) {
        socket.emit('experiment:error', { message: err.message });
        socket.emit('log', { message: `Experiment failed: ${err.message}`, level: 'error' });
      } finally {
        if (workerInstanceIds.length > 0) {
          const awsProv = getSocketAws(socket.id);
          if (awsProv) {
            try {
              await awsProv.terminate(session.region, workerInstanceIds);
              socket.emit('log', { message: `Terminated ${workerInstanceIds.length} worker instance(s).` });
            } catch (e) {
              socket.emit('log', { message: `Warning: failed to terminate workers: ${e.message}`, level: 'warn' });
            }
          }
          try { await runCmd(session, 'rm -f ~/.ssh/yardstick_exp.pem', socket, 'cleanup-workers'); } catch {}
        }
      }
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
    const useHome = isHomeMode(m);
    const scratchDir = useHome ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
    // Use python3 to list directories reliably (no shell variable expansion issues,
    // follows symlinks, portable across distros)
    const basePath = useHome ? 'str(Path.home() / "yardstick")' : JSON.stringify(`/var/scratch/${user}/yardstick`);
    const cmd = `python3 - <<'__YS_PY__'
import os, sys, json
from pathlib import Path
base = Path(${basePath})
if not base.is_dir():
    print(json.dumps([]))
    sys.exit(0)
runs = sorted([d.name for d in base.iterdir() if d.is_dir() or d.is_symlink()], reverse=True)
print(json.dumps(runs))
__YS_PY__`;

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
            // only resolve on 'close' — data events may still be in flight at 'exit'
            stream.on('close', () => resolve(out.trim()));
          });
        }
      });
    }

    try {
      const raw = await execOnce(cmd);
      // output is JSON array from python3
      let runs = [];
      const jsonStart = raw.indexOf('[');
      if (jsonStart !== -1) {
        try { runs = JSON.parse(raw.slice(jsonStart)); } catch { runs = []; }
      }
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
    const useHome = isHomeMode(m);
    const scratchDir = useHome ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
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
run_dir = os.path.expandvars(os.path.expanduser(run_dir))
print(f"DEBUG:RESOLVED_RUN_DIR:{run_dir}", file=sys.stderr)
if not os.path.isdir(run_dir):
    print(f"DEBUG:RUN_DIR_MISSING:{run_dir}", file=sys.stderr)
    print(json.dumps({"cpu": [], "tick": [], "mem": [], "nodes": []}))
    sys.exit(0)

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
