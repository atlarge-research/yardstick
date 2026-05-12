import { useState } from 'react';
import { Box, Button, Flex, Heading, Icon, Spinner, Text } from '@chakra-ui/react';
import { LuPlay, LuSquare, LuTrash2, LuLink, LuRefreshCw } from 'react-icons/lu';
import type { CloudInstance } from '../../lib/cloud/types';
import { c, cardProps, radii } from '../../theme';

interface Props {
  instances: CloudInstance[];
  loading: boolean;
  onRefresh: () => void;
  onStart: (ids: string[]) => Promise<void>;
  onStop: (ids: string[]) => Promise<void>;
  onTerminate: (ids: string[]) => Promise<void>;
  onUse: (inst: CloudInstance) => void;
}

function stateColor(s: string): string {
  if (s === 'running') return c.success;
  if (s === 'pending' || s === 'stopping' || s === 'shutting-down') return c.warning;
  if (s === 'stopped') return c.info;
  if (s === 'terminated') return c.textDim;
  return c.textDim;
}

export default function InstanceList({ instances, loading, onRefresh, onStart, onStop, onTerminate, onUse }: Props) {
  const [busy, setBusy] = useState<string | null>(null);

  const wrap = async (id: string, fn: () => Promise<void>) => {
    setBusy(id);
    try { await fn(); } finally { setBusy(null); }
  };

  return (
    <Box {...cardProps}>
      <Flex justify="space-between" align="center" mb={3}>
        <Heading fontSize="1.05rem" fontWeight={600}>Instances</Heading>
        <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} borderRadius={radii.sm} px={3.5} py={2} h="auto" fontSize="0.82rem" _hover={{ bg: c.surface2 }} onClick={onRefresh} disabled={loading}>
          {loading ? <Spinner size="xs" /> : <Icon as={LuRefreshCw} boxSize="13px" />} <Box as="span" ml={1.5}>Refresh</Box>
        </Button>
      </Flex>

      {instances.length === 0 && !loading && (
        <Text color={c.textDim} fontSize="0.88rem">No instances in this region.</Text>
      )}

      <Box border={instances.length ? '1px solid' : 'none'} borderColor={c.border} borderRadius={radii.sm} overflow="hidden">
        {instances.map((it) => {
          const canStart = it.state === 'stopped';
          const canStop = it.state === 'running';
          const canUse = it.state === 'running' && !!it.publicIp;
          const canTerminate = it.state !== 'terminated';
          const isBusy = busy === it.id;
          return (
            <Box key={it.id} px={3.5} py={3} borderBottom="1px solid" borderColor={c.bg} _last={{ borderBottom: 'none' }}>
              <Flex align="center" gap={3} wrap="wrap">
                <Box flex={1} minW="200px">
                  <Flex align="center" gap={2}>
                    <Text fontFamily="monospace" fontSize="0.85rem" fontWeight={600}>{it.id}</Text>
                    {it.name && <Text color={c.textDim} fontSize="0.82rem">• {it.name}</Text>}
                  </Flex>
                  <Flex gap={3} mt={1} fontSize="0.78rem" color={c.textDim} wrap="wrap">
                    <Text>{it.instanceType}</Text>
                    <Text>•</Text>
                    <Text color={stateColor(it.state)} fontWeight={600}>{it.state}</Text>
                    {it.publicIp && <><Text>•</Text><Text fontFamily="monospace">{it.publicIp}</Text></>}
                    {it.keyName && <><Text>•</Text><Text>key: {it.keyName}</Text></>}
                  </Flex>
                </Box>

                <Flex gap={1.5}>
                  <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.success} borderRadius={radii.sm}
                    px={2.5} py={1.5} h="auto" fontSize="0.78rem" _hover={{ bg: c.surface2 }}
                    disabled={!canUse || isBusy} onClick={() => onUse(it)} title="Use for benchmark">
                    <Icon as={LuLink} boxSize="13px" /> <Box as="span" ml={1}>Use</Box>
                  </Button>
                  <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} borderRadius={radii.sm}
                    px={2.5} py={1.5} h="auto" fontSize="0.78rem" _hover={{ bg: c.surface2 }}
                    disabled={!canStart || isBusy} onClick={() => wrap(it.id, () => onStart([it.id]))}>
                    <Icon as={LuPlay} boxSize="13px" /> <Box as="span" ml={1}>Start</Box>
                  </Button>
                  <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} borderRadius={radii.sm}
                    px={2.5} py={1.5} h="auto" fontSize="0.78rem" _hover={{ bg: c.surface2 }}
                    disabled={!canStop || isBusy} onClick={() => wrap(it.id, () => onStop([it.id]))}>
                    <Icon as={LuSquare} boxSize="13px" /> <Box as="span" ml={1}>Stop</Box>
                  </Button>
                  <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.error} borderRadius={radii.sm}
                    px={2.5} py={1.5} h="auto" fontSize="0.78rem" _hover={{ bg: c.surface2 }}
                    disabled={!canTerminate || isBusy} onClick={() => {
                      if (window.confirm(`Terminate ${it.id}? This is irreversible.`)) wrap(it.id, () => onTerminate([it.id]));
                    }}>
                    <Icon as={LuTrash2} boxSize="13px" /> <Box as="span" ml={1}>Terminate</Box>
                  </Button>
                </Flex>
              </Flex>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
