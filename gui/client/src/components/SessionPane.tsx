import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Button, Icon } from '@chakra-ui/react';
import { LuPackage, LuFlaskConical, LuSquareTerminal, LuChartBar, LuCloud } from 'react-icons/lu';
import type { IconType } from 'react-icons';
import { createSocket } from '../socket';
import useYardstick from '../hooks/useYardstick';
import { SocketProvider } from '../context/SocketContext';
import type { SshConnectOptions, StepStatus } from '../hooks/useYardstick';
import ConnectForm from './ConnectForm';
import PipelineView from './PipelineView';
import ExperimentView from './ExperimentView';
import ResultsView from './ResultsView';
import ManualCommand from './ManualCommand';
import LogPanel from './LogPanel';
import CloudPanel from './cloud/CloudPanel';
import AwsCloudContent from './cloud/AwsCloudContent';
import type { CloudInstanceHandoff } from '../lib/cloud/types';
import { c, radii, cardProps } from '../theme';

export type SessionStatus = 'idle' | 'connecting' | 'connected' | 'running' | 'done' | 'error';

type TabId = 'setup' | 'experiment' | 'results' | 'terminal' | 'cloud';

interface TabDef {
  id: TabId;
  label: string;
  icon: IconType;
  statusKey: string | null;
}

const TABS: TabDef[] = [
  { id: 'setup',      label: 'Setup',      icon: LuPackage,        statusKey: 'setup' },
  { id: 'experiment', label: 'Experiment', icon: LuFlaskConical,   statusKey: 'experiment' },
  { id: 'results',    label: 'Results',    icon: LuChartBar,       statusKey: null },
  { id: 'cloud',      label: 'Cloud',      icon: LuCloud,          statusKey: null },
  { id: 'terminal',   label: 'Terminal',   icon: LuSquareTerminal, statusKey: null },
];

function OutlineBtn({ children, ...props }: React.ComponentProps<typeof Button>) {
  return (
    <Button
      variant="plain"
      bg="transparent"
      border="1px solid"
      borderColor={c.border}
      color={c.text}
      borderRadius={radii.sm}
      px={4}
      py={2}
      fontSize="0.9rem"
      fontWeight={600}
      h="auto"
      _hover={{ bg: c.surface2 }}
      {...props}
    >
      {children}
    </Button>
  );
}

interface SessionPaneProps {
  onStatusChange: (status: SessionStatus) => void;
  onLabelChange: (label: string) => void;
}

export default function SessionPane({ onStatusChange, onLabelChange }: SessionPaneProps) {
  const [socket] = useState(() => createSocket());
  const {
    connected, sessionId, mode, setMode, stepStatuses, logs,
    terminalOutput, pipelineRunning, pipelineDone, error, setError,
    envChecks, envReady, detecting, detectingItem,
    experimentRunning, experimentError, experimentDone,
    sshConnect, localConnect, sshDisconnect, detectEnv,
    runPipeline, runExperiment, runSingleCommand, awsLaunch, awsTerminate,
    connectToCloudInstance,
  } = useYardstick(socket);

  const [tab, setTab] = useState<TabId>('setup');
  const [sshUsername, setSshUsername] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [connectPrefill, setConnectPrefill] = useState<Partial<SshConnectOptions> | null>(null);

  // Report status to parent
  useEffect(() => {
    let status: SessionStatus;
    if (error !== null) status = 'error';
    else if (experimentRunning) status = 'running';
    else if (experimentDone) status = 'done';
    else if (connected) status = 'connected';
    else if (stepStatuses.connect === 'running') status = 'connecting';
    else status = 'idle';
    onStatusChange(status);
  }, [error, experimentRunning, experimentDone, connected, stepStatuses.connect, onStatusChange]);

  // Report label when connection established
  useEffect(() => {
    if (connected) {
      const modeLabels: Record<string, string> = {
        local: 'Local', das5: 'DAS-5', das6: 'DAS-6', aws: 'AWS', custom: 'Custom SSH',
      };
      onLabelChange(modeLabels[mode] ?? mode);
    }
  }, [connected, mode, onLabelChange]);

  const handleUseInstance = (h: CloudInstanceHandoff) => {
    if (connected) {
      setError('Disconnect from the current session before connecting to a cloud instance.');
      return;
    }
    setConnectPrefill({
      mode: h.provider,
      host: h.host,
      port: '22',
      username: h.username,
      privateKey: h.privateKey || undefined,
    });
    setMode(h.provider);
    if (h.privateKey) {
      setSshUsername(h.username);
      connectToCloudInstance(h);
    }
  };

  const handleConnect = (opts: SshConnectOptions) => {
    if (opts.mode === 'local') {
      setSshUsername('');
      localConnect();
    } else {
      setSshUsername(opts.username || '');
      sshConnect(opts);
    }
  };

  const modeLabel = ({ local: 'Local', das5: 'DAS-5', das6: 'DAS-6', aws: 'AWS', custom: 'Custom SSH' } as Record<string, string>)[mode] || mode;

  if (!connected) {
    return (
      <SocketProvider value={socket}>
        <Flex direction="column" flex="1" bg={c.bg}>
          <Flex flex={1} justify="center" p={8}>
            <Box w="100%" maxW="720px">
              <Box textAlign="center" mb={8}>
                <Heading fontSize="2.4rem" fontWeight={800} color={c.accentLight} letterSpacing="-0.02em" mb={1.5}>
                  Yardstick
                </Heading>
                <Text color={c.textDim} fontSize="1rem">Minecraft-like Game Benchmark</Text>
              </Box>

              {error && (
                <Flex {...cardProps} borderColor={c.error} justify="space-between" align="center">
                  <Text color={c.error}>{error}</Text>
                  <OutlineBtn onClick={() => setError(null)}>Dismiss</OutlineBtn>
                </Flex>
              )}

              <ConnectForm
                onConnect={handleConnect}
                status={stepStatuses.connect}
                mode={mode}
                onModeChange={setMode}
                prefill={connectPrefill}
                onPrefillConsumed={() => setConnectPrefill(null)}
                cloudContent={(sshForm) => (
                  <AwsCloudContent
                    onUseInstance={handleUseInstance}
                    connectSlot={sshForm}
                  />
                )}
              />
            </Box>
          </Flex>
        </Flex>
      </SocketProvider>
    );
  }

  return (
    <SocketProvider value={socket}>
    <Flex direction="column" flex="1" bg={c.bg} overflow="hidden">
      <Flex as="header" align="center" gap={3.5} px={8} py="18px" borderBottom="1px solid" borderColor={c.border} bg={c.surface}>
        <Heading fontSize="1.5rem" fontWeight={700} color={c.accentLight}>Yardstick</Heading>
        <Text color={c.textDim} fontSize="0.9rem">Benchmark</Text>
        <Flex as="nav" ml="auto" gap={1.5}>
          {TABS.map((t) => {
            const status: StepStatus | null = t.statusKey ? ((stepStatuses[t.statusKey] || 'idle') as StepStatus) : null;
            const active = tab === t.id;
            return (
              <Button
                key={t.id}
                variant="plain"
                display="flex"
                alignItems="center"
                gap={1.5}
                px={4}
                py="7px"
                h="auto"
                bg={active ? c.accent : 'transparent'}
                border="1px solid"
                borderColor={active ? c.accent : c.border}
                borderRadius={radii.sm}
                color={active ? 'white' : c.textDim}
                fontSize="0.82rem"
                fontWeight={500}
                _hover={!active ? { bg: c.surface2, color: c.text, borderColor: c.textDim } : {}}
                onClick={() => setTab(t.id)}
              >
                {status && status !== 'idle' && (
                  <Box
                    w="7px" h="7px" borderRadius="full" flexShrink={0}
                    bg={status === 'completed' ? c.success : status === 'running' ? c.accentLight : c.error}
                    style={status === 'running' ? { animation: 'pulse 1.5s infinite' } : undefined}
                  />
                )}
                <Icon as={t.icon} boxSize="15px" />
                {t.label}
              </Button>
            );
          })}
        </Flex>
      </Flex>

      <Flex flex={1} direction="column" overflow="hidden">
        <Box flex={1} p={8} maxW="960px" mx="auto" w="100%" overflowY="auto" pb={showLogs ? '400px' : '0'}>
          {error && (
            <Flex {...cardProps} borderColor={c.error} justify="space-between" align="center">
              <Text color={c.error}>{error}</Text>
              <OutlineBtn onClick={() => setError(null)}>Dismiss</OutlineBtn>
            </Flex>
          )}

          {tab === 'setup' && (
            <PipelineView
              stepStatuses={stepStatuses}
              terminalOutput={terminalOutput}
              pipelineRunning={pipelineRunning}
              pipelineDone={pipelineDone}
              onRunPipeline={runPipeline}
              onDetectEnv={detectEnv}
              connected={connected}
              username={sshUsername}
              mode={mode}
              envChecks={envChecks}
              envReady={envReady}
              detecting={detecting}
              detectingItem={detectingItem}
            />
          )}

          {tab === 'experiment' && (
            <ExperimentView
              connected={connected}
              onRunExperiment={runExperiment}
              terminalOutput={terminalOutput}
              username={sshUsername}
              mode={mode}
              experimentRunning={experimentRunning}
              experimentError={experimentError}
              experimentDone={experimentDone}
              onSwitchTab={setTab}
            />
          )}

          {tab === 'results' && (
            <ResultsView
              connected={connected}
              sessionId={sessionId}
              mode={mode}
              username={sshUsername}
            />
          )}

          {tab === 'cloud' && (
            <CloudPanel onUseInstance={handleUseInstance} />
          )}

          {tab === 'terminal' && (
            <ManualCommand
              connected={connected}
              onRunCommand={runSingleCommand}
              terminalOutput={terminalOutput}
            />
          )}
        </Box>

        {showLogs && (
          <Box
            position="relative"
            borderTop="1px solid"
            borderColor={c.border}
            bg={c.surface}
            h="380px"
            overflowY="auto"
            w="100%"
          >
            <LogPanel logs={logs} />
          </Box>
        )}
      </Flex>

      <Flex as="footer" align="center" justify="space-between" px={8} py={2} bg={c.surface} borderTop="1px solid" borderColor={c.border} fontSize="0.78rem" color={c.textDim}>
        <Flex align="center" gap={2}>
          <Box w="8px" h="8px" borderRadius="full" bg={c.success} boxShadow={`0 0 6px ${c.success}`} />
          <Text fontSize="0.78rem">{modeLabel} - {mode === 'local' ? 'Local session' : sshUsername}</Text>
        </Flex>
        <Flex align="center" gap={3}>
          <OutlineBtn onClick={() => setShowLogs(!showLogs)} fontSize="0.75rem">
            {showLogs ? 'Hide' : 'Show'} Logs
          </OutlineBtn>
          <Button
            variant="plain"
            bg={c.error}
            color="white"
            px={3}
            py={1}
            borderRadius={radii.sm}
            fontSize="0.75rem"
            fontWeight={600}
            h="auto"
            _hover={{ filter: 'brightness(1.1)' }}
            onClick={sshDisconnect}
          >
            Disconnect
          </Button>
        </Flex>
      </Flex>
    </Flex>
    </SocketProvider>
  );
}
