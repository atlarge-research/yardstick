import { useState } from 'react';
import { Box, Flex, Grid, Text, Heading, Button, Icon, Spinner } from '@chakra-ui/react';
import { LuTriangleAlert, LuCircleCheck } from 'react-icons/lu';
import Terminal from './Terminal';
import type { ExperimentConfig, TerminalOutputMap } from '../hooks/useYardstick';
import { c, fonts, radii, cardProps, inputProps, labelProps, StyledInput } from '../theme';

interface ExperimentViewProps {
  connected: boolean;
  onRunExperiment: (config: ExperimentConfig) => void;
  terminalOutput: TerminalOutputMap;
  username: string;
  mode?: string;
  experimentRunning: boolean;
  experimentError: string | null;
  experimentDone: boolean;
  onSwitchTab?: (tab: 'setup' | 'experiment' | 'results' | 'terminal') => void;
}

export default function ExperimentView({
  connected, onRunExperiment, terminalOutput, username,
  mode = 'das5', experimentRunning, experimentError, experimentDone, onSwitchTab,
}: ExperimentViewProps) {
  const modeLabel = ({ local: 'locally', das5: 'on DAS-5', das6: 'on DAS-6', aws: 'on AWS', azure: 'on Azure', custom: 'on the remote host' } as Record<string, string>)[mode] || 'remotely';
  const [runName, setRunName] = useState('');
  const [numNodes, setNumNodes] = useState(2);
  const [botsPerNode, setBotsPerNode] = useState(10);
  const [sleepTime, setSleepTime] = useState(60);

  const handleRun = () => {
    onRunExperiment({ dasUsername: username, numNodes, botsPerNode, sleepTime, runName: runName.trim() });
  };

  return (
    <Box>
      <Box {...cardProps}>
        <Heading fontSize="1.15rem" fontWeight={600} mb={1.5}>Run Experiment</Heading>
        <Text color={c.textDim} fontSize="0.9rem" mb={5}>
          Provision nodes {modeLabel}, deploy PaperMC &amp; WalkAround bots, run the benchmark, and collect results.
        </Text>

        {experimentError && (
          <Flex
            align="flex-start" gap={3} p="14px 16px" borderRadius={radii.sm} mb={5}
            bg="rgba(225, 112, 85, 0.1)" border="1px solid" borderColor={c.error} color={c.error}
            lineHeight={1.5}
          >
            <Icon as={LuTriangleAlert} boxSize="18px" flexShrink={0} mt="2px" />
            <Box>
              <Text fontWeight={600} mb={1}>Experiment failed</Text>
              <Text as="pre" fontSize="0.85rem" whiteSpace="pre-wrap" fontFamily={fonts.sans} color={c.textDim} m={0}>
                {experimentError}
              </Text>
              {experimentError.includes('Setup') && onSwitchTab && (
                <Button
                  variant="plain"
                  bg="transparent"
                  border="1px solid"
                  borderColor={c.border}
                  color={c.text}
                  borderRadius={radii.sm}
                  px={4}
                  py={2}
                  h="auto"
                  mt={2.5}
                  fontSize="0.9rem"
                  fontWeight={600}
                  _hover={{ bg: c.surface2 }}
                  onClick={() => onSwitchTab('setup')}
                >
                  Go to Setup
                </Button>
              )}
            </Box>
          </Flex>
        )}

        {experimentDone && !experimentError && (
          <Flex
            align="flex-start" gap={3} p="14px 16px" borderRadius={radii.sm} mb={5}
            bg="rgba(0, 184, 148, 0.1)" border="1px solid" borderColor={c.success} color={c.success}
            lineHeight={1.5}
          >
            <Icon as={LuCircleCheck} boxSize="18px" flexShrink={0} mt="2px" />
            <Box>
              <Text fontWeight={600} mb={1}>Experiment completed</Text>
              <Text fontSize="0.85rem" color={c.textDim}>Results have been saved. Check the terminal output below for the path.</Text>
            </Box>
          </Flex>
        )}

        <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={4} mb={4}>
          <Box gridColumn={{ base: '1', md: '1 / -1' }}>
            <Text {...labelProps}>Run Name</Text>
            <StyledInput {...inputProps} type="text" placeholder="e.g. baseline-2nodes-10bots" value={runName} onChange={(e) => setRunName(e.target.value)} disabled={experimentRunning} />
            <Text fontSize="0.75rem" color={c.textDim} mt={1}>
              Optional. Used as the results folder name. A timestamp is added automatically.
            </Text>
          </Box>
          <Box>
            <Text {...labelProps}>Number of Nodes</Text>
            <StyledInput {...inputProps} type="number" min={2} max={16} value={numNodes} onChange={(e) => setNumNodes(Number(e.target.value))} disabled={experimentRunning} />
          </Box>
          <Box>
            <Text {...labelProps}>Bots per Node</Text>
            <StyledInput {...inputProps} type="number" min={1} max={100} value={botsPerNode} onChange={(e) => setBotsPerNode(Number(e.target.value))} disabled={experimentRunning} />
          </Box>
          <Box>
            <Text {...labelProps}>Duration (seconds)</Text>
            <StyledInput {...inputProps} type="number" min={10} max={3600} value={sleepTime} onChange={(e) => setSleepTime(Number(e.target.value))} disabled={experimentRunning} />
          </Box>
        </Grid>

        <Flex gap={2.5} mt={5}>
          <Button
            variant="plain"
            bg={c.accent}
            color="white"
            borderRadius={radii.sm}
            fontSize="0.9rem"
            fontWeight={600}
            px={5}
            py="10px"
            h="auto"
            _hover={{ bg: c.accentLight }}
            _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
            onClick={handleRun}
            disabled={experimentRunning}
          >
            {experimentRunning ? (
              <><Spinner size="sm" /> Experiment Running...</>
            ) : (
              'Launch Experiment'
            )}
          </Button>
        </Flex>
      </Box>

      {terminalOutput['run-experiment'] && (
        <Terminal lines={terminalOutput['run-experiment']} title="Experiment Output" />
      )}
    </Box>
  );
}
