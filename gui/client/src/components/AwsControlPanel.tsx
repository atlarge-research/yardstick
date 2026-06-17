import { useState, useEffect } from 'react';
import { Box, Flex, Text, Heading, Input, Button, Icon } from '@chakra-ui/react';
import { LuCloud } from 'react-icons/lu';
import { c, cardProps, radii, inputProps, labelProps } from '../theme';
import { useSocket } from '../context/SocketContext';

interface Props {
  onLaunch: (opts: Record<string, any>) => void;
  onTerminate: (opts: Record<string, any>) => void;
}

export default function AwsControlPanel({ onLaunch, onTerminate }: Props) {
  const socket = useSocket();
  const [region, setRegion] = useState('eu-west-2');
  const [count, setCount] = useState(1);
  const [instanceType, setInstanceType] = useState('t3.micro');
  const [amiId, setAmiId] = useState('');
  const [keyName, setKeyName] = useState('yardstick-test');
  const [sgIds, setSgIds] = useState('');
  const [terminateIds, setTerminateIds] = useState('');
  const [instances, setInstances] = useState<Array<{ InstanceId: string; PublicIp: string }>>([]);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    function onLaunched(payload: { instances: string }) {
      try {
        const json = JSON.parse(payload.instances);
        // json is an array of Reservations -> Instances nested; normalize
        const items: Array<{ InstanceId?: string; PublicIpAddress?: string }>= [];
        json.forEach((resArr: any) => resArr.forEach((inst: any) => items.push(inst)));
        const parsed = items.map((i) => ({ InstanceId: i.InstanceId || '', PublicIp: i.PublicIpAddress || '' }));
        setInstances(parsed);
        setStatusMsg(`Launched ${parsed.length} instance(s).`);
      } catch (e) {
        setStatusMsg('Launched (raw output received)');
      }
    }
    function onTerminated(payload: { instances: string[] } | any) {
      setStatusMsg('Terminated: ' + (payload.instances ? payload.instances.join(', ') : JSON.stringify(payload)));
      // remove terminated ids from instances list
      if (payload.instances && Array.isArray(payload.instances)) {
        setInstances((prev) => prev.filter((it) => !payload.instances.includes(it.InstanceId)));
      }
    }
    function onError(payload: { message: string }) {
      setStatusMsg('Error: ' + payload.message);
    }

    socket.on('aws:launched', onLaunched);
    socket.on('aws:terminated', onTerminated);
    socket.on('aws:error', onError);
    return () => {
      socket.off('aws:launched', onLaunched);
      socket.off('aws:terminated', onTerminated);
      socket.off('aws:error', onError);
    };
  }, []);

  const launch = () => {
    const payload = { region, count: Number(count), instanceType, amiId: amiId || null, keyName: keyName || null, securityGroupIds: sgIds ? sgIds.split(',').map(s => s.trim()) : [] };
    onLaunch(payload);
  };

  const terminate = () => {
    const ids = terminateIds.split(',').map((s) => s.trim()).filter(Boolean);
    onTerminate({ region, instanceIds: ids });
  };

  return (
    <Box {...cardProps} mt={4}>
      <Flex align="center" gap={2} mb={2}>
        <Icon as={LuCloud} boxSize="18px" />
        <Heading fontSize="1.05rem" fontWeight={600}>AWS Instances</Heading>
      </Flex>

      <Text color={c.textDim} fontSize="0.9rem" mb={3}>Quickly launch or terminate EC2 instances using server-side AWS CLI credentials.</Text>

      <Flex gap={3} mb={3}>
        <Box flex={1}>
          <Text {...labelProps}>Region</Text>
          <Input {...inputProps} value={region} onChange={(e) => setRegion(e.target.value)} />
        </Box>
        <Box w="120px">
          <Text {...labelProps}>Count</Text>
          <Input {...inputProps} value={String(count)} onChange={(e) => setCount(Number(e.target.value))} />
        </Box>
        <Box w="180px">
          <Text {...labelProps}>Instance Type</Text>
          <Input {...inputProps} value={instanceType} onChange={(e) => setInstanceType(e.target.value)} />
        </Box>
      </Flex>

      <Flex gap={3} mb={3}>
        <Box flex={1}>
          <Text {...labelProps}>AMI ID (optional)</Text>
          <Input {...inputProps} value={amiId} onChange={(e) => setAmiId(e.target.value)} placeholder="ami-..." />
        </Box>
        <Box w="240px">
          <Text {...labelProps}>Key Pair</Text>
          <Input {...inputProps} value={keyName} onChange={(e) => setKeyName(e.target.value)} />
        </Box>
      </Flex>

      <Box mb={3}>
        <Text {...labelProps}>Security Group IDs (comma separated)</Text>
        <Input {...inputProps} value={sgIds} onChange={(e) => setSgIds(e.target.value)} placeholder="sg-... , sg-..." />
      </Box>

      <Flex gap={2} mb={4}>
        <Button variant="plain" bg={c.accent} color="white" onClick={launch}>Launch</Button>
        <Button variant="outline" onClick={() => { setAmiId(''); setSgIds(''); setInstances([]); setStatusMsg(null); }}>Reset</Button>
      </Flex>

      {statusMsg && <Text color={c.textDim} mb={3}>{statusMsg}</Text>}

      {instances.length > 0 && (
        <Box mb={3}>
          <Text {...labelProps}>Launched instances</Text>
          <Box mt={2} borderRadius={4} border="1px solid" borderColor={c.border} overflow="hidden">
            {instances.map((it) => (
              <Flex key={it.InstanceId} px={3} py={2} align="center" justify="space-between" borderBottom="1px solid" borderColor={c.bg}>
                <Text fontFamily="monospace" fontSize="0.85rem">{it.InstanceId}</Text>
                <Text fontSize="0.85rem" color={c.textDim}>{it.PublicIp || '-'}</Text>
              </Flex>
            ))}
          </Box>
        </Box>
      )}

      <Box borderTop="1px solid" borderColor={c.border} pt={3}>
        <Text {...labelProps}>Terminate Instances (comma-separated IDs)</Text>
        <Input {...inputProps} value={terminateIds} onChange={(e) => setTerminateIds(e.target.value)} placeholder="i-01234..., i-..." mb={3} />
        <Flex gap={2}>
          <Button variant="plain" bg={c.error} color="white" onClick={terminate}>Terminate</Button>
        </Flex>
      </Box>
    </Box>
  );
}
