const { spawn } = require('child_process');
const os = require('os');

function isHomeMode(mode) {
  return mode === 'local' || mode === 'aws' || mode === 'custom-ssh';
}

function buildPipelineCommands(mode, user) {
  const useHome = isHomeMode(mode);
  const condaDir = useHome ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
  const scratchDir = useHome ? '$HOME/experiments' : `/var/scratch/${user}/yardstick`;

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
      `if conda list -n yardstick openjdk 2>/dev/null | grep -q '^openjdk'; then`,
      `  echo "Removing conda-forge openjdk (GraalVM) from yardstick env..."`,
      `  conda remove -n yardstick -y openjdk 2>&1 || true`,
      `fi`,
      `if ! command -v java >/dev/null 2>&1; then`,
      `  echo "Installing Java..."`,
      `  if command -v apt-get >/dev/null 2>&1; then`,
      `    sudo -n apt-get update -q 2>&1 || true`,
      `    sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y openjdk-17-jdk-headless 2>&1 || true`,
      `  elif command -v dnf >/dev/null 2>&1; then`,
      `    sudo -n dnf install -y java-latest-openjdk-headless 2>&1 || true`,
      `  elif command -v yum >/dev/null 2>&1; then`,
      `    sudo -n yum install -y java-latest-openjdk-headless 2>&1 || true`,
      `  elif command -v pacman >/dev/null 2>&1; then`,
      `    sudo -n pacman -S --noconfirm --needed jre-openjdk-headless 2>&1 || true`,
      `  elif command -v brew >/dev/null 2>&1; then`,
      `    brew install openjdk 2>&1 && sudo -n ln -sfn "$(brew --prefix openjdk)/libexec/openjdk.jdk" /Library/Java/JavaVirtualMachines/openjdk.jdk 2>/dev/null || true`,
      `  elif command -v choco >/dev/null 2>&1; then`,
      `    choco install -y openjdk 2>&1 || true`,
      `  fi`,
      `fi`,
      `# Fallback: if java still missing, install via conda into the yardstick env (no sudo needed)`,
      `if ! command -v java >/dev/null 2>&1 && command -v conda >/dev/null 2>&1; then`,
      `  echo "Package manager could not install Java (no sudo?). Trying conda..."`,
      `  conda install -y -n yardstick -c conda-forge 'openjdk>=17' 2>&1 || true`,
      `  # Expose it for the rest of this script`,
      `  _cjava=$(conda run -n yardstick bash -c 'which java' 2>/dev/null || true)`,
      `  [ -n "$_cjava" ] && export PATH="$(dirname "$_cjava"):$PATH"`,
      `fi`,
      ...(useHome ? [
        `echo "Checking system tools required by the workload..."`,
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
        `need=""`,
        `command -v rsync >/dev/null 2>&1 || need="$need rsync"`,
        `command -v wget  >/dev/null 2>&1 || need="$need wget"`,
        `command -v git   >/dev/null 2>&1 || need="$need git"`,
        `if [ -n "$need" ]; then`,
        `  echo "Installing system packages:$need"`,
        `  if command -v apt-get >/dev/null 2>&1; then`,
        `    sudo -n apt-get update -q 2>&1 || true`,
        `    sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y $need 2>&1 || { echo "[WARN] apt install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v dnf >/dev/null 2>&1; then`,
        `    sudo -n dnf install -y $need 2>&1 || { echo "[WARN] dnf install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v yum >/dev/null 2>&1; then`,
        `    sudo -n yum install -y $need 2>&1 || { echo "[WARN] yum install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v pacman >/dev/null 2>&1; then`,
        `    sudo -n pacman -S --noconfirm --needed $need 2>&1 || { echo "[WARN] pacman install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v brew >/dev/null 2>&1; then`,
        `    brew install $need 2>&1 || { echo "[WARN] brew install failed; you may need to install manually:$need" >&2; }`,
        `  elif command -v choco >/dev/null 2>&1; then`,
        `    choco install -y $need 2>&1 || { echo "[WARN] choco install failed; you may need to install manually:$need" >&2; }`,
        `  else`,
        `    echo "[WARN] No supported package manager found (apt/dnf/yum/pacman/brew/choco). Install manually:$need" >&2`,
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
      `  echo "[INFO] java not on PATH — OK for local mode (Docker provides it); required for AWS/DAS nodes."`,
      `fi`,
      `if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then`,
      `  echo "[OK] docker: $(docker --version)"`,
      `else`,
      `  echo "[WARN] Docker not running — local multi-node mode requires Docker." >&2`,
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
        const wrappedCmd = `bash -l <<'__YS_PROBE__'\n${cmd}\n__YS_PROBE__`;
        session.conn.exec(wrappedCmd, { pty: false }, (err, stream) => {
          if (err) return done(false, `exec error: ${err.message}`);
          let stderrBuf = '';
          stream.stderr.on('data', (d) => { stderrBuf += d.toString(); });
          stream.on('exit', (code) => {
            done(code === 0, `exit ${code}${stderrBuf ? ', stderr: ' + stderrBuf.trim().slice(0, 100) : ''}`);
          });
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

// Queries EC2 IMDS to auto-detect AMI/region when the user connected via plain
// SSH instead of the Cloud panel. Supports both IMDSv1 and IMDSv2 transparently.
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

module.exports = { isHomeMode, buildPipelineCommands, runEnvChecks, queryImds };
