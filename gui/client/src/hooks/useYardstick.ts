import { useState, useCallback, useEffect } from 'react';
import socket from '../socket';

export interface Step {
  id: string;
  label: string;
  description: string;
}

export type StepStatus = 'idle' | 'running' | 'completed' | 'error';

export interface LogEntry {
  message: string;
  level: string;
  ts: string;
}

export interface EnvChecks {
  miniconda: boolean;
  condaEnv: boolean;
  packages: boolean;
  workspace: boolean;
  [key: string]: boolean;
}

export interface SshConnectOptions {
  mode: string;
  host?: string;
  port?: string;
  username?: string;
  password?: string;
  privateKey?: string;
  jumpHost?: string;
  jumpPort?: string;
  jumpUsername?: string;
  jumpPassword?: string;
  jumpPrivateKey?: string;
}

export interface ExperimentConfig {
  dasUsername: string;
  numNodes: number;
  botsPerNode: number;
  sleepTime: number;
  runName: string;
}

export type TerminalOutputMap = Record<string, string>;

const STEPS: Step[] = [
  { id: 'connect',    label: 'Login',      description: 'Connect to the target host' },
  { id: 'setup',      label: 'Setup',      description: 'Install tools & prepare the environment' },
  { id: 'experiment', label: 'Experiment', description: 'Run a benchmark experiment' },
];

export default function useYardstick() {
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [mode, setMode] = useState('das5');
  const [activeStep, setActiveStep] = useState(0);
  const [stepStatuses, setStepStatuses] = useState<Record<string, StepStatus>>(() =>
    Object.fromEntries(STEPS.map((s) => [s.id, 'idle' as StepStatus]))
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [terminalOutput, setTerminalOutput] = useState<TerminalOutputMap>({});
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineDone, setPipelineDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [envChecks, setEnvChecks] = useState<EnvChecks | null>(null);
  const [envReady, setEnvReady] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectingItem, setDetectingItem] = useState<string | null>(null);

  const addLog = useCallback((entry: Omit<LogEntry, 'ts'>) => {
    setLogs((prev) => [...prev, { ...entry, ts: new Date().toISOString() }]);
  }, []);

  useEffect(() => {
    socket.connect();

    socket.on('connect', () => addLog({ message: 'WebSocket connected', level: 'info' }));
    socket.on('disconnect', () => addLog({ message: 'WebSocket disconnected', level: 'error' }));

    socket.on('ssh:connected', ({ sessionId: sid, mode: serverMode }: { sessionId: string; mode?: string }) => {
      setConnected(true);
      setSessionId(sid);
      if (serverMode) setMode(serverMode);
      setStepStatuses((prev) => ({ ...prev, connect: 'completed' }));
      setActiveStep(1);
    });

    socket.on('ssh:error', ({ message }: { message: string }) => {
      setError(message);
      addLog({ message, level: 'error' });
      setStepStatuses((prev) => ({ ...prev, connect: 'error' }));
    });

    socket.on('ssh:disconnected', () => {
      setConnected(false);
      setSessionId(null);
      setEnvChecks(null);
      setEnvReady(false);
      setStepStatuses((prev) => ({ ...prev, connect: 'idle', setup: 'idle', experiment: 'idle' }));
      setActiveStep(0);
    });

    socket.on('log', ({ message, level }: { message: string; level?: string }) => addLog({ message, level: level || 'info' }));

    socket.on('env:check-progress', ({ checks, checking }: { checks: EnvChecks; checking: string }) => {
      setEnvChecks(checks);
      setDetectingItem(checking);
    });

    socket.on('env:detected', ({ checks, allReady }: { checks: EnvChecks; allReady: boolean }) => {
      setEnvChecks(checks);
      setEnvReady(allReady);
      setDetecting(false);
      setDetectingItem(null);
      if (allReady) {
        setStepStatuses((prev) => ({ ...prev, setup: 'completed', experiment: 'idle' }));
        setActiveStep(2);
      } else {
        setStepStatuses((prev) => ({ ...prev, setup: 'idle' }));
        setActiveStep(1);
      }
    });

    socket.on('step:start', (_data: { stepId: string }) => {
      setStepStatuses((prev) => ({ ...prev, setup: 'running' }));
    });

    socket.on('step:complete', (_data: { stepId: string }) => {
      // individual sub-step done - setup stays running until pipeline:complete
    });

    socket.on('step:error', ({ stepId, code }: { stepId: string; stderr: string; code: number }) => {
      setStepStatuses((prev) => ({ ...prev, setup: 'error' }));
      setError(`Setup step "${stepId}" failed (exit ${code})`);
    });

    socket.on('terminal:data', ({ stepId, data }: { stepId: string; data: string; isStderr: boolean }) => {
      setTerminalOutput((prev) => ({
        ...prev,
        [stepId]: (prev[stepId] || '') + data,
      }));
    });

    socket.on('pipeline:complete', () => {
      setPipelineRunning(false);
      setPipelineDone(true);
      setStepStatuses((prev) => ({ ...prev, setup: 'completed' }));
      setActiveStep(2);
    });

    socket.on('pipeline:error', ({ message }: { message: string }) => {
      setPipelineRunning(false);
      setStepStatuses((prev) => ({ ...prev, setup: 'error' }));
      setError(message);
    });

    return () => {
      socket.off();
      socket.disconnect();
    };
  }, [addLog]);

  const sshConnect = useCallback(
    ({ host, port, username, password, privateKey, mode: connectMode,
       jumpHost, jumpPort, jumpUsername, jumpPassword, jumpPrivateKey }: SshConnectOptions) => {
      setError(null);
      setStepStatuses((prev) => ({ ...prev, connect: 'running' }));
      if (connectMode) setMode(connectMode);
      socket.emit('ssh:connect', {
        host, port, username, password, privateKey, mode: connectMode,
        jumpHost, jumpPort, jumpUsername, jumpPassword, jumpPrivateKey,
      });
    },
    []
  );

  const localConnect = useCallback(() => {
    setError(null);
    setMode('local');
    setStepStatuses((prev) => ({ ...prev, connect: 'running' }));
    socket.emit('local:connect');
  }, []);

  const sshDisconnect = useCallback(() => {
    if (sessionId) socket.emit('ssh:disconnect', { sessionId });
  }, [sessionId]);

  const detectEnv = useCallback(
    (dasUsername: string) => {
      if (!sessionId) return;
      setDetecting(true);
      setEnvChecks(null);
      socket.emit('ssh:detect-env', { sessionId, username: dasUsername, mode });
    },
    [sessionId, mode]
  );

  const runPipeline = useCallback(
    (dasUsername: string) => {
      if (!sessionId) return;
      setError(null);
      setPipelineRunning(true);
      setPipelineDone(false);
      setTerminalOutput({});
      setStepStatuses((prev) => ({ ...prev, setup: 'running' }));
      socket.emit('ssh:run-pipeline', { sessionId, username: dasUsername, mode });
    },
    [sessionId, mode]
  );

  const [experimentRunning, setExperimentRunning] = useState(false);
  const [experimentError, setExperimentError] = useState<string | null>(null);
  const [experimentDone, setExperimentDone] = useState(false);

  useEffect(() => {
    const onComplete = () => {
      setExperimentRunning(false);
      setExperimentDone(true);
      setExperimentError(null);
      setStepStatuses((prev) => ({ ...prev, experiment: 'completed' }));
    };
    const onError = ({ message }: { message: string }) => {
      setExperimentRunning(false);
      setExperimentError(message);
      setStepStatuses((prev) => ({ ...prev, experiment: 'error' }));
    };
    const onPreflightFailed = ({ missing }: { missing: string[] }) => {
      setExperimentRunning(false);
      setExperimentError(`Setup incomplete - the following are missing:\n${missing.map((m) => `  - ${m}`).join('\n')}\n\nGo to the Setup tab to install everything first.`);
      setStepStatuses((prev) => ({ ...prev, experiment: 'error' }));
    };

    socket.on('experiment:complete', onComplete);
    socket.on('experiment:error', onError);
    socket.on('experiment:preflight-failed', onPreflightFailed);
    return () => {
      socket.off('experiment:complete', onComplete);
      socket.off('experiment:error', onError);
      socket.off('experiment:preflight-failed', onPreflightFailed);
    };
  }, []);

  const runExperiment = useCallback(
    ({ dasUsername, numNodes, botsPerNode, sleepTime, runName }: ExperimentConfig) => {
      if (!sessionId) return;
      setExperimentError(null);
      setExperimentDone(false);
      setExperimentRunning(true);
      setStepStatuses((prev) => ({ ...prev, experiment: 'running' }));
      setTerminalOutput((prev) => ({ ...prev, 'run-experiment': '' }));
      socket.emit('ssh:run-experiment', {
        sessionId,
        username: dasUsername,
        numNodes,
        botsPerNode,
        sleepTime,
        runName,
        mode,
      });
    },
    [sessionId, mode]
  );

  const runSingleCommand = useCallback(
    (command: string, stepId: string = 'custom') => {
      if (!sessionId) return;
      socket.emit('ssh:exec', { sessionId, command, stepId });
    },
    [sessionId]
  );

  return {
    STEPS,
    connected,
    sessionId,
    mode,
    setMode,
    activeStep,
    setActiveStep,
    stepStatuses,
    logs,
    terminalOutput,
    pipelineRunning,
    pipelineDone,
    error,
    setError,
    envChecks,
    envReady,
    detecting,
    detectingItem,
    experimentRunning,
    experimentError,
    experimentDone,
    sshConnect,
    localConnect,
    sshDisconnect,
    detectEnv,
    runPipeline,
    runExperiment,
    runSingleCommand,
  };
}
