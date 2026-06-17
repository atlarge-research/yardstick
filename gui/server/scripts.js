function buildDasScript({ numNodes, botsPerNode, sleepTime, safeName, scratchDir }) {
  return `
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

    import random as _rnd; timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(_rnd.randint(1000,9999))
    run_label = '${safeName}_' + timestamp if '${safeName}' else timestamp
    dest = Path('${scratchDir}/' + run_label)
    yardstick_benchmark.fetch(dest, nodes)
    print(f'Results saved to {dest}')
finally:
    yardstick_benchmark.clean(nodes)
    das.release(nodes)
    print('Done!')
`;
}

function buildCloudScript({ botsPerNode, sleepTime, safeName, workerIps, workerUser }) {
  return `
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

_worker_ips = ${JSON.stringify(workerIps)}
_worker_user = ${JSON.stringify(workerUser)}

try:
    _main_ip = _socket.gethostbyname(_socket.gethostname())
except Exception:
    _main_ip = '127.0.0.1'
_local_addrs = {'localhost', '127.0.0.1', _main_ip}

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

papermc_node = Node(host=_main_ip, wd=wd_base / 'server')
worker_nodes = [
    Node(host=ip, wd=Path(f'/home/{_worker_user}/yardstick/run/client{i+1}'))
    for i, ip in enumerate(_worker_ips)
]
nodes = [papermc_node] + worker_nodes
wl_nodes = worker_nodes if worker_nodes else [papermc_node]

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

_ssh_base = ['ssh', '-i', os.path.expanduser('~/.ssh/yardstick_exp.pem'),
             '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
for _ip in _worker_ips:
    print(f'[worker {_ip}] installing base tools (rsync, git)...', flush=True)
    _r = _sp.run(_ssh_base + [f'{_worker_user}@{_ip}', r"""
        i=0; while sudo fuser /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock >/dev/null 2>&1 && [ $i -lt 60 ]; do sleep 2; i=$((i+1)); done
        sudo dpkg --configure -a -q 2>/dev/null || true
        sudo apt-get install -f -y -qq 2>/dev/null || true
        (which rsync && which git) || (sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y rsync git)
    """], capture_output=True, text=True, timeout=180)
    print(f'[worker {_ip}] base tools {"ready" if _r.returncode == 0 else "install failed: " + _r.stderr.strip()}', flush=True)

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

    import random as _rnd; timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(_rnd.randint(1000,9999))
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
}

function buildLocalScript({ numNodes, botsPerNode, sleepTime, safeName }) {
  return `
from yardstick_benchmark.model import Node
from yardstick_benchmark.monitoring import Telegraf
from yardstick_benchmark.games.minecraft.server import PaperMC
from yardstick_benchmark.games.minecraft.workload import WalkAround
import yardstick_benchmark
import yardstick_benchmark.model as _ym
from time import sleep
from datetime import datetime
from pathlib import Path
import os, shutil as _shutil, subprocess as _sp, urllib.request, time as _time, glob as _glob

# Fix nvm loading in walkaround playbooks (non-interactive shells ignore ~/.bashrc)
try:
    import yardstick_benchmark.games.minecraft.workload as _wl_mod
    _wl_dir = os.path.dirname(_wl_mod.__file__)
    for _yml in _glob.glob(f'{_wl_dir}/*.yml'):
        _txt = open(_yml).read()
        if 'source ~/.bashrc' in _txt:
            open(_yml, 'w').write(_txt.replace(
                'source ~/.bashrc',
                'export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"'
            ))
except Exception as _e:
    print(f'[warn] walkaround patch: {_e}', flush=True)

# Patch PaperMC start playbook: increase wait_for timeout and add JVM heap flags
try:
    import yardstick_benchmark.games.minecraft.server as _pmc_mod
    _pmc_dir = os.path.dirname(_pmc_mod.__file__)
    _start_yml = os.path.join(_pmc_dir, 'papermc_start.yml')
    _txt = open(_start_yml).read()
    _changed = False
    if 'timeout:' not in _txt:
        _txt = _txt.rstrip() + chr(10) + '        timeout: 900' + chr(10)
        _changed = True
    if '-Xms' not in _txt:
        _txt = _txt.replace(
            'nohup java -javaagent:',
            'nohup java -Xms512m -Xmx1g -javaagent:'
        )
        _changed = True
    if _changed:
        open(_start_yml, 'w').write(_txt)
        print('[patch] PaperMC start: timeout=900s, JVM heap 512m-1g', flush=True)
except Exception as _e:
    print(f'[warn] PaperMC patch: {_e}', flush=True)

home = os.path.expanduser('~')
wd_base = Path(home) / 'yardstick' / 'run'

# One node per Docker container; host names just need to be unique for yardstick inventory.
server_node = Node(host='localhost', wd=wd_base / 'server')
client_nodes = [
    Node(host=f'127.0.0.{i + 1}', wd=wd_base / f'client{i}')
    for i in range(1, ${numNodes})
]
nodes = [server_node] + client_nodes

# Map each node host -> Docker container name
_container_map = {node.host: f'ys-local-{i}' for i, node in enumerate(nodes)}

# Route all Ansible plays through 'docker exec' into the matching container.
# community.docker is bundled with ansible>=8.
_orig_gen_inv = _ym._gen_inv
def _patched_gen_inv(name, nodes_arg):
    inv = _orig_gen_inv(name, nodes_arg)
    for host, hvars in inv['all']['hosts'].items():
        hvars['ansible_connection'] = 'community.docker.docker'
        hvars['ansible_host'] = _container_map.get(host, host)
        hvars['ansible_python_interpreter'] = '/usr/bin/python3'
    return inv
_ym._gen_inv = _patched_gen_inv

# Cache JARs locally to avoid re-downloading on every run
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

def _ensure_cached(fname, url, min_size, retries=3, timeout=60):
    dest = CACHE / fname
    if dest.exists() and dest.stat().st_size >= min_size:
        print(f'[cache] {fname}', flush=True)
        return dest
    for attempt in range(1, retries + 1):
        try:
            print(f'[fetch] {fname} (attempt {attempt}/{retries})', flush=True)
            tmp = dest.with_suffix(dest.suffix + '.part')
            with urllib.request.urlopen(url, timeout=timeout) as resp, open(tmp, 'wb') as f:
                _shutil.copyfileobj(resp, f, length=64 * 1024)
            if tmp.stat().st_size < min_size:
                raise IOError(f'file too small ({tmp.stat().st_size} bytes)')
            tmp.replace(dest)
            return dest
        except Exception as e:
            print(f'[retry] {e}', flush=True)
            if attempt < retries:
                _time.sleep(min(2 ** attempt, 10))
    raise RuntimeError(f'failed to fetch {url}')

for fname, url, sz in DOWNLOADS:
    _ensure_cached(fname, url, sz)

# Build the node image on first run; cached by Docker layer cache afterwards.
# Embedded inline so no external Dockerfile is needed at runtime.
_dockerfile = (
    b"FROM ubuntu:22.04\\n"
    b"ENV DEBIAN_FRONTEND=noninteractive\\n"
    b"RUN apt-get update && apt-get install -y --no-install-recommends"
    b" openjdk-17-jre-headless python3 rsync wget curl git"
    b" && rm -rf /var/lib/apt/lists/*\\n"
    b"RUN ln -sf /usr/bin/python3 /usr/bin/python\\n"
    b'CMD ["tail", "-f", "/dev/null"]\\n'
)
_img = 'yardstick-node:latest'
try:
    if _sp.run(['docker', 'image', 'inspect', _img], capture_output=True).returncode != 0:
        print('[docker] Building yardstick-node image (first run, ~1 min)...', flush=True)
        _b = _sp.run(['docker', 'build', '-t', _img, '-'], input=_dockerfile)
        if _b.returncode != 0:
            raise RuntimeError('docker build failed')
        print('[docker] Image ready.', flush=True)
except FileNotFoundError:
    raise RuntimeError('Docker is not installed or not on PATH. Install Docker then reconnect.')

def _run(label, fn):
    print(f'[>>] {label}...', flush=True)
    try:
        result = fn()
        print(f'[OK] {label}', flush=True)
        return result
    except Exception as e:
        msg = str(e)
        lines = [l.strip() for l in msg.splitlines() if l.strip()]
        summary = lines[-1] if lines else msg
        print(f'[FAIL] {label}: {summary}', flush=True)
        raise RuntimeError(f'{label} failed: {summary}') from e

papermc = None
_started = []
try:
    # Start one Docker container per node with --network host so all processes
    # share the host network stack (PaperMC binds to 0.0.0.0 and bots on other
    # containers reach it via localhost). The working directory is bind-mounted
    # at the same host path so Ansible file paths work unchanged.
    for node in nodes:
        _cname = _container_map[node.host]
        node.wd.mkdir(parents=True, exist_ok=True)
        _r = _sp.run([
            'docker', 'run', '-d',
            '--name', _cname,
            '--network', 'host',
            '-v', f'{node.wd}:{node.wd}',
            '-v', f'{CACHE}:{CACHE}:ro',
            _img,
        ], capture_output=True, text=True)
        if _r.returncode != 0:
            raise RuntimeError(f'docker run {_cname}: {_r.stderr.strip()}')
        _started.append(_cname)
        print(f'[docker] Started {_cname}', flush=True)

    _run('Clean nodes', lambda: yardstick_benchmark.clean(nodes))

    telegraf = Telegraf(nodes)
    telegraf.add_input_jolokia_agent(nodes[0])
    telegraf.add_input_execd_minecraft_ticks(nodes[0])
    _run('Deploy Telegraf', telegraf.deploy)

    papermc = PaperMC(nodes[:1])

    # Pre-stage cached JARs into the server working directory so Ansible skips download
    try:
        _inv_hosts = papermc.deploy_action.inv['all']['hosts']
        run_wd = Path(_inv_hosts[next(iter(_inv_hosts))]['wd'])
        run_wd.mkdir(parents=True, exist_ok=True)
        for fname, _u, _s in DOWNLOADS:
            src = CACHE / fname
            dst = run_wd / fname
            if not dst.exists() and src.exists():
                _shutil.copy2(src, dst)
                print(f'[stage] {fname}', flush=True)
    except Exception as e:
        print(f'[warn] pre-stage: {e}', flush=True)

    _run('Deploy PaperMC', papermc.deploy)

    # Stream PaperMC log lines every 15 s while Ansible waits for startup.
    # The actual wd has a random suffix (papermc-XXXXXX) so use a glob.
    import threading as _threading_pmc
    _pmc_stop = _threading_pmc.Event()
    _pmc_pos = [0]
    def _pmc_log_tail():
        while not _pmc_stop.wait(15):
            try:
                _matches = _glob.glob(str(wd_base / 'server' / 'papermc-*' / 'logs' / 'latest.log'))
                if _matches:
                    with open(_matches[0], errors='replace') as _f:
                        _f.seek(_pmc_pos[0])
                        _new = _f.read()
                        _pmc_pos[0] = _f.tell()
                    for _l in _new.splitlines():
                        if _l.strip():
                            print(f'[server] {_l}', flush=True)
                else:
                    print('[server] waiting for logs/latest.log to appear...', flush=True)
            except Exception:
                pass
    _pmc_tail = _threading_pmc.Thread(target=_pmc_log_tail, daemon=True)
    _pmc_tail.start()
    try:
        _run('Start PaperMC', papermc.start)
    except Exception as e:
        try:
            _log_matches = _glob.glob(str(wd_base / 'server' / 'papermc-*' / 'logs' / 'latest.log'))
            log_file = Path(_log_matches[0]) if _log_matches else None
            if log_file and log_file.exists():
                print('--- PaperMC logs/latest.log (last 60 lines) ---', flush=True)
                for line in log_file.read_text(errors='replace').splitlines()[-60:]:
                    print(line, flush=True)
                print('--- end log ---', flush=True)
            else:
                print('No PaperMC log found — Java may have crashed before writing logs.', flush=True)
        except Exception:
            pass
        raise
    finally:
        _pmc_stop.set()
        _pmc_tail.join(timeout=5)

    _run('Start Telegraf', telegraf.start)

    wl_nodes = client_nodes if client_nodes else [server_node]
    wl = WalkAround(wl_nodes, server_node.host, bots_per_node=${botsPerNode})
    _run('Deploy WalkAround', wl.deploy)
    _run('Run WalkAround bots', wl.start)

    print('Experiment running, sleeping for ${sleepTime}s...')
    sleep(${sleepTime})

    try:
        _run('Stop PaperMC', papermc.stop)
    except Exception as e:
        print(f'[warn] stop PaperMC: {e}', flush=True)
    try:
        _run('Stop Telegraf', telegraf.stop)
    except Exception as e:
        print(f'[warn] stop Telegraf: {e}', flush=True)

    import random as _rnd; timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + str(_rnd.randint(1000,9999))
    run_label = '${safeName}_' + timestamp if '${safeName}' else timestamp
    dest = Path(home) / 'yardstick' / run_label
    dest.mkdir(parents=True, exist_ok=True)
    # With Docker bind-mounts the node wds are already on the host filesystem,
    # so copy directly instead of going through rsync-based fetch.
    for node in nodes:
        if node.wd.exists():
            _shutil.copytree(str(node.wd), str(dest / node.wd.name), dirs_exist_ok=True)
    print(f'Results saved to {dest}')
finally:
    for _c in _started:
        _sp.run(['docker', 'rm', '-f', _c], capture_output=True)
        print(f'[docker] Removed {_c}', flush=True)
    try:
        for node in nodes:
            _shutil.rmtree(node.wd, ignore_errors=True)
    except Exception as _e:
        print(f'[warn] host cleanup: {_e}', flush=True)
    print('Done!')
`;
}

function buildExperimentCmd(script, condaDir) {
  const envBin = `${condaDir}/envs/yardstick/bin`;
  return `export PATH="${envBin}:$PATH"; cd ~/experiments && "${envBin}/python" <<'__YS_EXPERIMENT__'\n${script}\n__YS_EXPERIMENT__`;
}

module.exports = { buildDasScript, buildCloudScript, buildLocalScript, buildExperimentCmd };
