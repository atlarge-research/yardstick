const { sessions } = require('../session');
const { runCmd } = require('../transport');
const { isHomeMode, buildPipelineCommands, runEnvChecks, queryImds } = require('../environment');
const { buildDasScript, buildCloudScript, buildLocalScript, buildExperimentCmd } = require('../scripts');
const { getSocketAws } = require('../cloud');

function registerExperimentHandlers(socket) {
  socket.on('ssh:run-experiment', async ({ sessionId, username: dasUsername, numNodes = 2, botsPerNode = 10, sleepTime = 10, runName = '', mode: clientMode, workload = 'walkaround' }) => {
    const session = sessions.get(sessionId);
    if (!session) { socket.emit('ssh:error', { message: 'No active session.' }); return; }

    const mode = clientMode || session.mode || 'das5';
    const user = dasUsername || session.username;
    const cmds = buildPipelineCommands(mode, user);
    const useHome = isHomeMode(mode);
    const condaDir = useHome ? '$HOME/miniconda3' : `/var/scratch/${user}/miniconda3`;
    const safeName = runName.replace(/[^a-zA-Z0-9_-]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').slice(0, 60);

    // Pre-flight gate
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

    const isLocalMode = mode === 'local';
    const isCloudMode = ['aws', 'custom-ssh'].includes(mode);
    let workerInstanceIds = [];

    try {
      let experimentScript;

      if (isLocalMode) {
        experimentScript = buildLocalScript({ numNodes, botsPerNode, sleepTime, safeName, workload });
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
          if (meta.securityGroupIds?.length > 0 && session.securityGroupIds.length === 0) {
            session.securityGroupIds = meta.securityGroupIds;
          }
          if (meta.keyName && !session.keyName) session.keyName = meta.keyName;
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

            if (session.securityGroupIds?.length > 0) {
              socket.emit('log', { message: 'Ensuring security group allows intra-SG SSH...' });
              await awsProv.ensureSelfIngressSSH(reg, session.securityGroupIds);
            }

            socket.emit('log', { message: 'Waiting for worker private IPs...' });
            const deadline = Date.now() + 300_000;
            while (Date.now() < deadline) {
              const workers = await awsProv.describeInstances(reg, workerInstanceIds);
              const ips = workers.map((w) => w.privateIp).filter(Boolean);
              if (ips.length === workerInstanceIds.length) { workerIps.push(...ips); break; }
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

        experimentScript = buildCloudScript({
          botsPerNode,
          sleepTime,
          safeName,
          workerIps,
          workerUser: session.username || 'ubuntu',
          workload,
        });
      } else {
        experimentScript = buildDasScript({
          numNodes,
          botsPerNode,
          sleepTime,
          safeName,
          scratchDir: cmds.scratchDir,
          workload,
        });
      }

      const experimentCmd = buildExperimentCmd(experimentScript, cmds.condaDir);
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
  });
}

module.exports = { registerExperimentHandlers };
