const { Client } = require('ssh2');
const { v4: uuidv4 } = require('uuid');
const os = require('os');
const { sessions } = require('../session');
const { runLocal, runCmd } = require('../transport');
const { isHomeMode, buildPipelineCommands, runEnvChecks } = require('../environment');

function registerConnectionHandlers(socket) {
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
      if (sock) o.sock = sock;
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
            if (err) { emitError(err, 'target-via-jump'); jumpConn.end(); return; }

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
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }

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
            if (filtered.length > 0) origEmit(event, { ...data, data: filtered.join('\n') });
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
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }

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

  // Legacy handlers — kept for backwards compatibility with useYardstick hook
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
      const waitCmd = `aws ec2 wait instance-running --region ${region} --instance-ids ${instanceIds.join(' ')}`;
      await runLocal(waitCmd, socket, 'aws-wait-running');
      const descCmd = `aws ec2 describe-instances --region ${region} --instance-ids ${instanceIds.join(' ')} --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,PublicIp:PublicIpAddress}' --output json`;
      const descRes = await runLocal(descCmd, socket, 'aws-describe');
      socket.emit('aws:launched', { instances: descRes.stdout });
    } catch (err) {
      socket.emit('aws:error', { message: err.message, detail: { stdout: err.stdout, stderr: err.stderr } });
      socket.emit('log', { message: `AWS launch error: ${err.message}`, level: 'error' });
    }
  });

  socket.on('aws:terminate-instances', async ({ region = 'us-east-1', instanceIds = [] }) => {
    try {
      if (!instanceIds.length) throw new Error('No instance IDs provided');
      socket.emit('log', { message: `Terminating instances: ${instanceIds.join(', ')}...`, level: 'cmd' });
      const termCmd = `aws ec2 terminate-instances --region ${region} --instance-ids ${instanceIds.join(' ')} --query 'TerminatingInstances[*].InstanceId' --output text`;
      const termRes = await runLocal(termCmd, socket, 'aws-terminate');
      socket.emit('aws:terminated', { instances: termRes.stdout.trim().split(/\s+/).filter(Boolean) });
    } catch (err) {
      socket.emit('aws:error', { message: err.message, detail: { stdout: err.stdout, stderr: err.stderr } });
      socket.emit('log', { message: `AWS terminate error: ${err.message}`, level: 'error' });
    }
  });
}

module.exports = { registerConnectionHandlers };
