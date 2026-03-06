import { useState, type FormEvent } from 'react';
import { Box, Flex, Text, Heading, Button } from '@chakra-ui/react';
import Terminal from './Terminal';
import type { TerminalOutputMap } from '../hooks/useYardstick';
import { c, radii, cardProps, inputProps, StyledInput } from '../theme';

interface ManualCommandProps {
  connected: boolean;
  onRunCommand: (command: string, stepId: string) => void;
  terminalOutput: TerminalOutputMap;
}

export default function ManualCommand({ connected, onRunCommand, terminalOutput }: ManualCommandProps) {
  const [command, setCommand] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    onRunCommand(command, 'custom');
    setCommand('');
  };

  return (
    <Box>
      <Box {...cardProps}>
        <Heading fontSize="1.15rem" fontWeight={600} mb={1.5}>Manual Command</Heading>
        <Text color={c.textDim} fontSize="0.9rem" mb={5}>
          Run arbitrary commands on the remote host via SSH.
        </Text>

        {!connected ? (
          <Text color={c.warning}>Please connect via SSH first.</Text>
        ) : (
          <Flex as="form" onSubmit={handleSubmit} gap={2.5}>
            <StyledInput {...inputProps} flex={1} value={command} onChange={(e) => setCommand(e.target.value)} placeholder="e.g., ls -la ~/yardstick-tutorial" />
            <Button
              type="submit"
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
              disabled={!command.trim()}
            >
              Run
            </Button>
          </Flex>
        )}
      </Box>

      {terminalOutput['custom'] && (
        <Terminal lines={terminalOutput['custom']} title="Command Output" />
      )}
    </Box>
  );
}
