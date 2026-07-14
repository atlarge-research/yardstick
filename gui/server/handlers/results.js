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
    print(json.dumps({"cpu": [], "tick": [], "mem": [], "jvm": [], "heap": [], "tps": 0, "nodes": [], "server_node": None, "window": None}))
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
            active = float(parts[6]) if parts[6] else 0
            idle = float(parts[9]) if parts[9] else 0
            total = active + idle
            # Telegraf emits two cpu-total rows per timestamp: a cumulative
            # time_* counter row (active+idle is thousands of seconds, giving a
            # meaningless since-boot average) and a usage_* percentage row
            # (active+idle == 100). Keep only the percentage row, which is the
            # real instantaneous utilisation; usage_active is that utilisation.
            if not (99.0 <= total <= 101.0):
                continue
            cpu_data.append({"ts": ts, "node": node_name, "util": round(active, 2)})

# Ticks come from execd.csv: the helper scrapes the server's 100-tick ring buffer
# and emits EVERY individual tick (~2000 per run). The alternative,
# minecraft_tick_times.csv, is the server's own averageTickTime sampled once per
# telegraf interval: ~25 values per run, each already an average over ~100 ticks.
# Percentiles of 25 averages are not tick percentiles, and "share of ticks over
# the 50ms budget" is only meaningful against individual ticks.
# execd rows: ts, "execd", host, computed_ts, loop_iteration, measurement,
#             tick_duration_ms, tick_number, timestamp_ms
# The row timestamp is the scrape-batch time, so one ~2.5s batch of ticks
# shares a single value. That granularity is accepted here: the computed_ts
# column that was meant to time individual ticks mixes units at the source
# (seconds plus nanosecond increments) and cannot be trusted.
tick_data = []
tick_ts = []
server_node = None
for tick_file in glob.glob(f"{run_dir}/**/execd.csv", recursive=True):
    with open(tick_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 7 or parts[5] != "minecraft_tick_duration":
                continue
            try:
                ts, dur = int(parts[0]), float(parts[6])
            except ValueError:
                continue
            if server_node is None:
                server_node = Path(tick_file).parent.parent.name
            tick_data.append({"ts": ts, "dur": dur})
            tick_ts.append(ts)

# Fall back to the averaged series only if a run predates the per-tick collector,
# so old runs still render rather than showing nothing.
if not tick_data:
    for tick_file in glob.glob(f"{run_dir}/**/minecraft_tick_times.csv", recursive=True):
        if server_node is None:
            server_node = Path(tick_file).parent.parent.name
        with open(tick_file) as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 5:
                    continue
                try:
                    ts, dur = int(parts[0]), float(parts[4])
                except ValueError:
                    continue
                tick_data.append({"ts": ts, "dur": dur})
                tick_ts.append(ts)

# Delivered-load window. Telegraf runs longer than the workload (deploy, bot
# process setup, teardown), and every one of those extra seconds is an idle,
# fast tick. Statistics over the whole collection window therefore mix the
# loaded server with an unloaded one and understate overload. The bot managers
# log their live bot count once per second ("<epoch> - bots: N"), so the window
# in which every worker node held its full bot count is recoverable exactly:
# it starts when the slowest node reaches its target and ends when the first
# node drops off it. Summary statistics are computed over that window; the
# full time series is still emitted so charts can show the ramp around it.
import re as _re
_node_windows = []
for bot_log in glob.glob(f"{run_dir}/**/bot-*.log", recursive=True):
    target = 0
    full_ts = []
    try:
        with open(bot_log, errors="replace") as f:
            for line in f:
                # [0-9] instead of backslash classes: this script is consumed both
                # through a JS template literal (which unescapes backslashes) and
                # verbatim by the CLI export tool, and must mean the same in both.
                m = _re.match(r"target bots: ([0-9]+)", line)
                if m:
                    target = max(target, int(m.group(1)))
                    continue
                m = _re.match(r"([0-9]+(?:[.][0-9]+)?) - bots: ([0-9]+)", line)
                if m and target and int(m.group(2)) >= target:
                    full_ts.append(float(m.group(1)))
    except OSError:
        continue
    if full_ts:
        _node_windows.append((min(full_ts), max(full_ts)))

window_start = window_end = None
if _node_windows:
    window_start = max(w[0] for w in _node_windows)
    window_end = min(w[1] for w in _node_windows)
    if window_end <= window_start:
        window_start = window_end = None

def _in_window(ts):
    return window_start is None or (window_start <= ts <= window_end)

# Throughput: a healthy server ticks 20x per second, and shedding ticks is the
# most direct statement of overload there is. Counted over the delivered-load
# window and divided by the window's duration: dividing by the tick-timestamp
# span instead would shrink the denominator whenever the collector stalls
# under load, and report an overloaded server as faster than real time.
if window_start is not None and tick_ts:
    _n = sum(1 for t in tick_ts if _in_window(t))
    tps = round(_n / max(1.0, window_end - window_start), 2)
elif tick_ts:
    tps = round(len(tick_ts) / max(1, (max(tick_ts) - min(tick_ts))), 2)
else:
    tps = 0

# Node CPU% averages over every core, but the Minecraft tick loop is effectively
# single-threaded, so a pinned main thread reads as ~3% on a 32-core node. The
# JVM reports what it actually uses: ProcessCpuLoad is the fraction of the whole
# machine, so multiplying by AvailableProcessors gives cores actually busy, which
# is comparable across a 2-vCPU cloud box and a 32-core cluster node.
jvm_data = []
for os_file in glob.glob(f"{run_dir}/**/java_lang_OperatingSystem.csv", recursive=True):
    if server_node is not None and Path(os_file).parent.parent.name != server_node:
        continue
    with open(os_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 16:
                continue
            try:
                ts = int(parts[0])
                ncpu = int(float(parts[4]))          # AvailableProcessors
                load = float(parts[10])              # ProcessCpuLoad, 0..1 of whole machine
            except (ValueError, IndexError):
                continue
            if load < 0:                             # JVM reports -1 before it has a sample
                continue
            jvm_data.append({"ts": ts, "cores": round(load * ncpu, 3), "ncpu": ncpu})

# Node RAM% is diluted the same way (a 2GB server on a 64GB node). JVM heap is
# the number that means something, and it is what fills up and triggers GC.
heap_data = []
for heap_file in glob.glob(f"{run_dir}/**/jvm_memory.csv", recursive=True):
    if server_node is not None and Path(heap_file).parent.parent.name != server_node:
        continue
    with open(heap_file) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 8:
                continue
            try:
                ts = int(parts[0])
                used = float(parts[7])               # HeapMemoryUsage.used, bytes
                hmax = float(parts[6])               # HeapMemoryUsage.max, bytes
            except (ValueError, IndexError):
                continue
            heap_data.append({"ts": ts, "gb": round(used / 1e9, 3), "maxgb": round(hmax / 1e9, 2)})

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

# Normalise every series against a single shared t0 so the cross-series charts
# line up on one time axis.
_all_ts = ([d["ts"] for d in cpu_data]
           + [d["ts"] for d in tick_data]
           + [d["ts"] for d in mem_data]
           + [d["ts"] for d in jvm_data]
           + [d["ts"] for d in heap_data])
t0 = min(_all_ts) if _all_ts else 0
for series in (cpu_data, tick_data, mem_data, jvm_data, heap_data):
    for d in series:
        d["t"] = round((d["ts"] - t0) / 60, 2)
        del d["ts"]

# Relabel node directories to friendly roles so DAS hostnames (node034, ...)
# display the same way as local/AWS runs (server / client1..N). The server is
# the node that produced the tick metric; everything else is a client, numbered
# in sorted order. This is idempotent for local/AWS dirs that are already named
# server/clientN.
all_node_names = set(d["node"] for d in cpu_data) | set(d["node"] for d in mem_data)
name_map = {}
if server_node is not None:
    name_map[server_node] = "server"
for i, n in enumerate(sorted(n for n in all_node_names if n != server_node), start=1):
    name_map[n] = f"client{i}"
for d in cpu_data:
    d["node"] = name_map.get(d["node"], d["node"])
for d in mem_data:
    d["node"] = name_map.get(d["node"], d["node"])
if server_node is not None:
    server_node = "server"

nodes_found = sorted(set(d["node"] for d in cpu_data)) if cpu_data else []
window = None
if window_start is not None:
    window = {"start": round((window_start - t0) / 60, 2),
              "end": round((window_end - t0) / 60, 2)}
print(json.dumps({"cpu": cpu_data, "tick": tick_data, "mem": mem_data, "jvm": jvm_data,
                  "heap": heap_data, "tps": tps, "nodes": nodes_found,
                  "server_node": server_node, "window": window}))
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
    const scratchDir = isHomeMode(m) ? '$HOME/experiments' : `/var/scratch/${user}/yardstick`;
    const basePath = isHomeMode(m) ? 'str(Path.home() / "experiments")' : JSON.stringify(`/var/scratch/${user}/yardstick`);

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
    const scratchDir = isHomeMode(m) ? '$HOME/experiments' : `/var/scratch/${user}/yardstick`;
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
