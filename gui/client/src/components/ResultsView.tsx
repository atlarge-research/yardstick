import { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import { Box, Flex, Text, Heading, Button, Icon, Spinner } from '@chakra-ui/react';
import { LuRefreshCw, LuDownload, LuTriangleAlert, LuLoader } from 'react-icons/lu';
import socket from '../socket';
import { c, radii, cardProps, inputProps, StyledSelect } from '../theme';

interface MetricRecord {
  t: number;
  [key: string]: number | string;
}

interface ChartData {
  nodes: string[];
  cpu: MetricRecord[];
  mem: MetricRecord[];
  tick: Array<{ t: number; dur: number }>;
}

interface ResultsViewProps {
  connected: boolean;
  sessionId: string | null;
  mode: string;
  username: string;
}

const NODE_COLORS = [
  '#6c5ce7', '#00b894', '#e17055', '#74b9ff',
  '#fdcb6e', '#a29bfe', '#55efc4', '#fab1a0',
  '#81ecec', '#ffeaa7', '#dfe6e9', '#fd79a8',
];

function pivotByTime(records: MetricRecord[], valueKey: string, groupKey: string): Record<string, unknown>[] {
  const map = new Map<number, Record<string, unknown>>();
  for (const r of records) {
    const t = r.t as number;
    if (!map.has(t)) map.set(t, { t });
    map.get(t)![r[groupKey] as string] = r[valueKey];
  }
  return Array.from(map.values()).sort((a, b) => (a.t as number) - (b.t as number));
}

const tooltipStyle = { background: c.surface2, border: `1px solid ${c.border}`, borderRadius: radii.sm };
const axisProps = { tick: { fill: c.textDim, fontSize: 11 }, stroke: c.border };

export default function ResultsView({ connected, sessionId, mode, username }: ResultsViewProps) {
  const [runs, setRuns] = useState<string[]>([]);
  const [scratchDir, setScratchDir] = useState('');
  const [selectedRun, setSelectedRun] = useState('');
  const [loading, setLoading] = useState(false);
  const [listing, setListing] = useState(false);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const listRuns = useCallback(() => {
    setListing(true);
    setError(null);
    socket.emit('results:list', { sessionId, mode, username });
  }, [sessionId, mode, username]);

  const loadRun = useCallback(() => {
    if (!selectedRun) return;
    setLoading(true);
    setError(null);
    setChartData(null);
    socket.emit('results:load', { sessionId, runId: selectedRun, mode, username });
  }, [sessionId, selectedRun, mode, username]);

  useEffect(() => {
    const onList = ({ runs: r, scratchDir: sd }: { runs: string[]; scratchDir: string }) => {
      setRuns(r);
      setScratchDir(sd);
      setListing(false);
      if (r.length > 0 && !selectedRun) setSelectedRun(r[0]);
    };
    const onData = ({ data }: { data: ChartData }) => { setChartData(data); setLoading(false); };
    const onLoading = () => setLoading(true);
    const onError = ({ message }: { message: string }) => { setError(message); setLoading(false); setListing(false); };

    socket.on('results:list-ok', onList);
    socket.on('results:data', onData);
    socket.on('results:loading', onLoading);
    socket.on('results:error', onError);

    return () => {
      socket.off('results:list-ok', onList);
      socket.off('results:data', onData);
      socket.off('results:loading', onLoading);
      socket.off('results:error', onError);
    };
  }, [selectedRun]);

  useEffect(() => {
    if (connected && sessionId) listRuns();
  }, [connected, sessionId]);

  const nodes = chartData?.nodes || [];
  const cpuPivot = chartData?.cpu ? pivotByTime(chartData.cpu, 'util', 'node') : [];
  const memPivot = chartData?.mem ? pivotByTime(chartData.mem, 'pct', 'node') : [];
  const tickSorted = chartData?.tick ? [...chartData.tick].sort((a, b) => a.t - b.t) : [];

  const hasCpu = cpuPivot.length > 0;
  const hasTick = tickSorted.length > 0;
  const hasMem = memPivot.length > 0;

  return (
    <Box>
      <Box {...cardProps}>
        <Heading fontSize="1rem" fontWeight={600} mb={3}>Experiment Results</Heading>
        <Flex gap={2} align="center" flexWrap="wrap">
          <Button
            variant="plain"
            bg="transparent"
            border="1px solid"
            borderColor={c.border}
            color={c.text}
            borderRadius={radii.sm}
            fontSize="0.9rem"
            fontWeight={600}
            px={4}
            py={2}
            h="auto"
            gap={1.5}
            _hover={{ bg: c.surface2 }}
            _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
            onClick={listRuns}
            disabled={listing || !connected}
          >
            {listing ? <Icon as={LuLoader} boxSize="14px" className="spin" /> : <Icon as={LuRefreshCw} boxSize="14px" />}
            {listing ? 'Scanning...' : 'Refresh'}
          </Button>

          {runs.length > 0 && (
            <>
              <StyledSelect
                flex={1}
                minW="200px"
                {...inputProps}
                value={selectedRun}
                onChange={(e) => setSelectedRun(e.target.value)}
              >
                {runs.map((r) => <option key={r} value={r}>{r}</option>)}
              </StyledSelect>

              <Button
                variant="plain"
                bg={c.accent}
                color="white"
                borderRadius={radii.sm}
                fontSize="0.9rem"
                fontWeight={600}
                px={4}
                py={2}
                h="auto"
                gap={1.5}
                _hover={{ bg: c.accentLight }}
                _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
                onClick={loadRun}
                disabled={loading || !selectedRun}
              >
                {loading ? <Icon as={LuLoader} boxSize="14px" className="spin" /> : <Icon as={LuDownload} boxSize="14px" />}
                {loading ? 'Parsing...' : 'Load'}
              </Button>
            </>
          )}
        </Flex>

        {scratchDir && (
          <Text color={c.textDim} mt={2} fontSize="0.8rem">Results directory: {scratchDir}</Text>
        )}
        {runs.length === 0 && !listing && (
          <Text color={c.textDim} mt={3}>No experiment runs found. Run an experiment first, then come back here.</Text>
        )}
      </Box>

      {error && (
        <Flex {...cardProps} borderColor={c.error} mt={4} gap={2.5} align="flex-start">
          <Icon as={LuTriangleAlert} boxSize="18px" color={c.error} flexShrink={0} mt="2px" />
          <Box>
            <Text fontWeight={700} color={c.error}>Error</Text>
            <Text as="pre" whiteSpace="pre-wrap" mt={1} color={c.textDim} fontSize="0.82rem">{error}</Text>
          </Box>
        </Flex>
      )}

      {loading && (
        <Box {...cardProps} mt={4} textAlign="center" p={10}>
          <Spinner size="lg" color={c.accent} />
          <Text mt={3} color={c.textDim}>Parsing CSV data and generating charts...</Text>
        </Box>
      )}

      {chartData && !loading && (
        <Flex direction="column" gap={5} mt={4}>
          {hasCpu && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>CPU Utilization</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Percentage of active CPU time per node (cpu-total)</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={cpuPivot}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis domain={[0, 100]} label={{ value: 'Utilization %', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Legend />
                  {nodes.map((node, i) => (
                    <Line key={node} type="monotone" dataKey={node} stroke={NODE_COLORS[i % NODE_COLORS.length]} dot={false} strokeWidth={1.5} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {hasTick && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Minecraft Tick Duration</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Server tick processing time (lower is better, 50 ms = real-time threshold)</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={tickSorted}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis label={{ value: 'Tick (ms)', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Line type="monotone" dataKey="dur" name="Tick Duration" stroke="#e17055" dot={false} strokeWidth={1.5} />
                  <Line type="monotone" dataKey={() => 50} name="50 ms threshold" stroke="#fdcb6e" strokeDasharray="5 5" dot={false} strokeWidth={1} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {hasMem && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Memory Utilization</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Used memory percentage per node</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={memPivot}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis domain={[0, 100]} label={{ value: 'Used %', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Legend />
                  {nodes.map((node, i) => (
                    <Line key={node} type="monotone" dataKey={node} stroke={NODE_COLORS[i % NODE_COLORS.length]} dot={false} strokeWidth={1.5} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {!hasCpu && !hasTick && !hasMem && (
            <Box {...cardProps} textAlign="center" p={10}>
              <Text color={c.textDim}>No chart data found for this run. The experiment may not have collected metrics.</Text>
            </Box>
          )}
        </Flex>
      )}
    </Box>
  );
}
