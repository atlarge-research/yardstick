import { useRef, useEffect } from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import type { LogEntry } from '../hooks/useJoystick';
import { c, fonts, radii } from '../theme';

interface LogPanelProps {
  logs: LogEntry[];
}

export default function LogPanel({ logs }: LogPanelProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const colorFor = (level: string): string => {
    switch (level) {
      case 'error': return c.error;
      case 'cmd': return c.accentLight;
      case 'success': return c.success;
      default: return c.textDim;
    }
  };

  return (
    <Box bg="#0a0c10" border="1px solid" borderColor={c.border} borderRadius={radii.md} overflow="hidden" mt={5}>
      <Flex align="center" gap={2} px={4} py={2.5} bg={c.surface2} borderBottom="1px solid" borderBottomColor={c.border} fontSize="0.8rem" color={c.textDim} fontFamily={fonts.mono}>
        <Box w="10px" h="10px" borderRadius="full" bg={c.error} />
        <Box w="10px" h="10px" borderRadius="full" bg={c.warning} />
        <Box w="10px" h="10px" borderRadius="full" bg={c.success} />
        <Text fontSize="0.8rem">Activity Log</Text>
      </Flex>
      <Box p={4} fontFamily={fonts.mono} fontSize="0.82rem" lineHeight={1.7} maxH="220px" overflowY="auto">
        {logs.length === 0 && <Text color={c.textDim}>No events.</Text>}
        {logs.map((entry, i) => (
          <Box key={i} color={colorFor(entry.level)}>
            <Text as="span" color={c.textDim} mr={2} fontSize="0.75rem">
              {new Date(entry.ts).toLocaleTimeString()}
            </Text>
            {entry.message}
          </Box>
        ))}
        <div ref={endRef} />
      </Box>
    </Box>
  );
}
