import { useEffect } from 'react';
import { Box, Flex, Grid, Text, Heading, Button, Icon, Spinner } from '@chakra-ui/react';
import { LuCheck, LuX, LuSearch, LuPackageCheck, LuCircleDot } from 'react-icons/lu';
import Terminal from './Terminal';
import type { StepStatus, EnvChecks, TerminalOutputMap } from '../hooks/useJoystick';
import { c, radii, cardProps } from '../theme';

type DetectStatus = 'checking' | 'ok' | 'missing' | 'waiting';

interface CheckItem {
  key: string;
  label: string;
}

interface InstallSubstep {
  id: string;
  label: string;
}

const CHECK_ITEMS: CheckItem[] = [
  { key: 'miniconda', label: 'Miniconda' },
  { key: 'condaEnv', label: 'Conda environment' },
  { key: 'packages', label: 'Python packages' },
  { key: 'ansible', label: 'Ansible CLI' },
  { key: 'workspace', label: 'Experiments workspace' },
];

const INSTALL_SUBSTEPS: InstallSubstep[] = [
  { id: 'install-miniconda', label: 'Miniconda' },
  { id: 'create-env', label: 'Conda Environment' },
  { id: 'install-deps', label: 'Dependencies' },
  { id: 'setup-workspace', label: 'Workspace' },
  { id: 'verify-install', label: 'Verification' },
];

function statusColor(s: DetectStatus): string {
  return s === 'ok' ? c.success : s === 'missing' ? c.warning : s === 'checking' ? c.info : c.textDim;
}

function statusBg(s: DetectStatus): string {
  return s === 'ok' ? 'rgba(0,184,148,0.06)' : s === 'missing' ? 'rgba(253,203,110,0.06)' : s === 'checking' ? 'rgba(116,185,255,0.06)' : 'transparent';
}

function StatusIcon({ status }: { status: DetectStatus }) {
  if (status === 'checking') return <><Spinner size="xs" color={c.info} /> Checking</>;
  if (status === 'ok') return <><Icon as={LuCheck} boxSize="13px" /> Found</>;
  if (status === 'missing') return <><Icon as={LuX} boxSize="13px" /> Not found</>;
  return <><Icon as={LuCircleDot} boxSize="13px" /> Waiting</>;
}

interface PipelineViewProps {
  stepStatuses: Record<string, StepStatus>;
  terminalOutput: TerminalOutputMap;
  pipelineRunning: boolean;
  pipelineDone: boolean;
  onRunPipeline: (username: string) => void;
  onDetectEnv: (username: string) => void;
  connected: boolean;
  username: string;
  mode?: string;
  envChecks: EnvChecks | null;
  envReady: boolean;
  detecting: boolean;
  detectingItem: string | null;
}

export default function PipelineView({
  stepStatuses, terminalOutput, pipelineRunning, pipelineDone,
  onRunPipeline, onDetectEnv, connected, username, mode = 'das5',
  envChecks, envReady, detecting, detectingItem,
}: PipelineViewProps) {
  const modeLabel = ({ local: 'locally', das5: 'on DAS-5', das6: 'on DAS-6', aws: 'on AWS', custom: 'on the remote host' } as Record<string, string>)[mode] || 'remotely';

  useEffect(() => {
    if (connected && envChecks === null && !detecting) onDetectEnv(username);
  }, [connected, envChecks, detecting, onDetectEnv, username]);

  const detectStatus = (key: string): DetectStatus => {
    if (detectingItem === key) return 'checking';
    if (!envChecks) return 'waiting';
    if (envChecks[key] === true) return 'ok';
    if (envChecks[key] === false && detectingItem !== key) {
      const order = CHECK_ITEMS.map((ci) => ci.key);
      const myIdx = order.indexOf(key);
      const curIdx = detectingItem ? order.indexOf(detectingItem) : order.length;
      if (curIdx > myIdx) return 'missing';
    }
    return 'waiting';
  };

  if (detecting) {
    return (
      <Box {...cardProps}>
        <Flex align="center" gap={2} mb={1.5}>
          <Icon as={LuSearch} boxSize="18px" />
          <Heading fontSize="1.15rem" fontWeight={600}>Checking environment{modeLabel ? ` ${modeLabel}` : ''}</Heading>
        </Flex>
        <Text color={c.textDim} fontSize="0.9rem" mb={4}>
          Probing the remote host to see what's already installed.
        </Text>
        <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={2.5}>
          {CHECK_ITEMS.map((item) => {
            const st = detectStatus(item.key);
            return (
              <Flex key={item.key} align="center" gap={2.5} px={3.5} py={3} bg={statusBg(st)} border="1px solid" borderColor={statusColor(st)} borderRadius={radii.sm}>
                <Text flex={1} fontWeight={600} fontSize="0.85rem">{item.label}</Text>
                <Flex align="center" gap={1.5} fontSize="0.75rem" fontWeight={600} color={statusColor(st)} whiteSpace="nowrap">
                  <StatusIcon status={st} />
                </Flex>
              </Flex>
            );
          })}
        </Grid>
      </Box>
    );
  }

  const showChecklist = envChecks !== null && !pipelineRunning;

  return (
    <Box>
      {showChecklist && (
        <Box {...cardProps}>
          <Flex align="center" gap={2} mb={1.5}>
            {envReady && <Icon as={LuPackageCheck} boxSize="18px" />}
            <Heading fontSize="1.15rem" fontWeight={600}>
              {envReady ? 'Environment Ready' : 'Environment Status'}
            </Heading>
          </Flex>
          <Text color={c.textDim} fontSize="0.9rem" mb={5}>
            {envReady
              ? `All components installed ${modeLabel}.`
              : `Some components are missing ${modeLabel}.`}
          </Text>

          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={2.5}>
            {CHECK_ITEMS.map((item) => {
              const ok = envChecks?.[item.key];
              return (
                <Flex key={item.key} align="center" gap={2.5} px={3.5} py={3} bg={ok ? 'rgba(0,184,148,0.06)' : 'rgba(253,203,110,0.06)'} border="1px solid" borderColor={ok ? c.success : c.warning} borderRadius={radii.sm}>
                  <Text flex={1} fontWeight={600} fontSize="0.85rem">{item.label}</Text>
                  <Flex align="center" gap={1.5} fontSize="0.75rem" fontWeight={600} color={ok ? c.success : c.warning} whiteSpace="nowrap">
                    {ok ? <><Icon as={LuCheck} boxSize="13px" /> Installed</> : <><Icon as={LuX} boxSize="13px" /> Missing</>}
                  </Flex>
                </Flex>
              );
            })}
          </Grid>

          <Flex gap={2.5} mt={4}>
            {!envReady && (
              <Button
                variant="plain"
                bg={c.success}
                color="white"
                borderRadius={radii.sm}
                fontSize="0.9rem"
                fontWeight={600}
                px={5}
                py="10px"
                h="auto"
                _hover={{ filter: 'brightness(1.1)' }}
                _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
                onClick={() => onRunPipeline(username)}
                disabled={pipelineRunning}
              >
                {pipelineDone ? 'Re-run Setup' : 'Install Missing Components'}
              </Button>
            )}
            <Button
              variant="plain"
              bg="transparent"
              border="1px solid"
              borderColor={c.border}
              color={c.text}
              borderRadius={radii.sm}
              fontSize="0.9rem"
              fontWeight={600}
              px={5}
              py="10px"
              h="auto"
              _hover={{ bg: c.surface2 }}
              onClick={() => onDetectEnv(username)}
            >
              Re-check
            </Button>
          </Flex>
        </Box>
      )}

      {pipelineRunning && (
        <Box {...cardProps}>
          <Flex align="center" gap={2.5} mb={1.5}>
            <Spinner size="sm" color={c.accent} />
            <Heading fontSize="1.15rem" fontWeight={600}>Installing...</Heading>
          </Flex>
          <Text color={c.textDim} fontSize="0.9rem">
            Installing {modeLabel}. Installed components will be skipped.
          </Text>
        </Box>
      )}

      {INSTALL_SUBSTEPS.map((step) =>
        terminalOutput[step.id] ? (
          <Box key={step.id} mb={4}>
            <Terminal lines={terminalOutput[step.id]} title={step.label} />
          </Box>
        ) : null
      )}

      {pipelineDone && (
        <Box {...cardProps} borderColor={c.success}>
          <Heading fontSize="1rem" fontWeight={600} color={c.success} mb={2}>Setup Complete</Heading>
          <Text color={c.textDim}>
            Ready. Go to the <Text as="strong">Experiment</Text> tab.
          </Text>
        </Box>
      )}
    </Box>
  );
}
