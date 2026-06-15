const { spawn } = require('child_process');
const os = require('os');
const { sessions } = require('../session');
const { isHomeMode, buildPipelineCommands } = require('../environment');

const PARSE_SCRIPT = `
import glob, json, sys, os
from pathlib import Path

run_dir = os.path.expandvars(os.path.expanduser(os.environ.get('YS_RUN_DIR', '')))
print(f"DEBUG:RESOLVED_RUN_DIR:{run_dir}", file=sys.stderr)
if not os.path.isdir(run_dir):
    print(f"DEBUG:RUN_DIR_MISSING:{run_dir}", file=sys.stderr)
    print(json.dumps({"cpu": [], "tick": [], "mem": [], "nodes": []}))
    sys.exit(0)

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
for cpu_file in glob.glob(f"{run_dir}/**/cpu.csv", recursive=True):
    node_name = Path(cpu_file).parent.parent.name
    with open(cpu_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 17 or parts[3] != "cpu-total":
                continue
            ts = int(parts[0])
            time_active = float(parts[6]) if parts[6] else 0
            time_idle = float(parts[9]) if parts[9] else 0
            total = time_active + time_idle
            util = round(100 * time_active / total, 2) if total > 0 else 0
            cpu_data.append({"ts": ts, "node": node_name, "util": util})

tick_data = []
for tick_file in glob.glob(f"{run_dir}/**/minecraft_tick_times.csv", recursive=True):
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
for mem_file in glob.glob(f"{run_dir}/**/mem.csv", recursive=True):
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
print(json.dumps({"cpu": cpu_data, "tick": tick_data, "mem": mem_data, "nodes": nodes_found}))
`;

function execOnce(session, command) {
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
      const wrappedCmd = `bash -l <<'__YS_EXEC__'\n${command}\n__YS_EXEC__`;
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

function registerResultsHandlers(socket) {
  socket.on('results:list', async ({ sessionId, mode: clientMode, username: dasUsername }) => {
    const session = sessions.get(sessionId);
    if (!session) { socket.emit('results:error', { message: 'No active session.' }); return; }

    const m = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const scratchDir = isHomeMode(m) ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
    const basePath = isHomeMode(m) ? 'str(Path.home() / "yardstick")' : JSON.stringify(`/var/scratch/${user}/yardstick`);

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

    try {
      const { stdout: raw } = await execOnce(session, cmd);
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
    if (!session) { socket.emit('results:error', { message: 'No active session.' }); return; }

    const m = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const scratchDir = isHomeMode(m) ? '$HOME/yardstick' : `/var/scratch/${user}/yardstick`;
    const runDir = `${scratchDir}/${runId}`;

    try {
      socket.emit('results:loading');
      const cmds = buildPipelineCommands(m, user);
      const pythonBin = `${cmds.condaDir}/envs/yardstick/bin/python3`;
      const command = `YS_RUN_DIR="${runDir}" ${pythonBin} <<'__YS_PYTHON__'\n${PARSE_SCRIPT}\n__YS_PYTHON__`;

      const { stdout: raw, stderr: debugStderr } = await execOnce(session, command);

      if (debugStderr) {
        const debugLines = debugStderr.split('\n').filter((l) => l.startsWith('DEBUG:') || l.startsWith('  '));
        if (debugLines.length > 0) {
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
}

module.exports = { registerResultsHandlers };
