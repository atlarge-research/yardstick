const { spawn } = require('child_process');
const os = require('os');

const ANSI_RE = /\x1b\[[0-9;]*[a-zA-Z]/g;
function stripAnsi(s) { return s.replace(ANSI_RE, ''); }

function runLocal(command, socket, stepId) {
  return new Promise((resolve, reject) => {
    if (stepId) socket.emit('step:start', { stepId });

    const proc = spawn('bash', ['-lc', command], {
      env: { ...process.env, HOME: os.homedir(), ANSIBLE_NOCOLOR: '1', NO_COLOR: '1' },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      const text = data.toString();
      stdout += text;
      socket.emit('terminal:data', { stepId, data: stripAnsi(text) });
    });

    proc.stderr.on('data', (data) => {
      const text = data.toString();
      stderr += text;
      socket.emit('terminal:data', { stepId, data: stripAnsi(text), isStderr: true });
    });

    // A signal-killed process reports code === null, which must not read as
    // success: the command died partway through whatever it was doing.
    proc.on('close', (code, signal) => {
      if (signal) {
        const msg = `Command terminated by ${signal}`;
        if (stepId) socket.emit('step:error', { stepId, stdout, stderr, code, signal });
        socket.emit('log', { message: `[FAIL] ${msg}`, level: 'error' });
        const err = new Error(msg);
        err.stdout = stdout;
        err.stderr = stderr;
        return reject(err);
      }
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
        socket.emit('terminal:data', { stepId, data: stripAnsi(text) });
      });

      stream.stderr.on('data', (data) => {
        const text = data.toString();
        stderr += text;
        socket.emit('terminal:data', { stepId, data: stripAnsi(text), isStderr: true });
      });

      // As in runLocal: an explicit signal means the remote command was killed.
      // A null code with no signal still counts as success, since some servers
      // close the channel without sending an exit status. ssh2 reports that same
      // case as undefined rather than null, so accept both.
      stream.on('close', (code, signal) => {
        if (signal) {
          const msg = `Remote command terminated by ${signal}`;
          if (stepId) socket.emit('step:error', { stepId, stdout, stderr, code, signal });
          socket.emit('log', { message: `[FAIL] ${msg}`, level: 'error' });
          const err = new Error(msg);
          err.stdout = stdout;
          err.stderr = stderr;
          return reject(err);
        }
        if (code === 0 || code === null || code === undefined) {
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

module.exports = { runLocal, runSSH, runCmd };
