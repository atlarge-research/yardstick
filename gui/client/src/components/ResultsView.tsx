import { useState, useEffect, useCallback, type ChangeEvent } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, BarChart, Bar,
} from 'recharts';
import { Box, Flex, Text, Heading, Button, Icon, Spinner, Grid } from '@chakra-ui/react';
import { LuRefreshCw, LuDownload, LuTriangleAlert, LuLoader } from 'react-icons/lu';
import { useSocket } from '../context/SocketContext';
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

type GraphId = 'cpu' | 'tick' | 'mem' | 'tick-hist' | 'tick-cdf' | 'cpu-hist';

interface ResultTemplate {
  id: string;
  label: string;
  graphs: GraphId[];
}

interface SummaryStats {
  avg: number;
  max: number;
  p95: number;
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

const GRAPH_LABELS: Record<GraphId, string> = {
  cpu: 'CPU Utilization',
  tick: 'Tick Duration',
  mem: 'Memory Utilization',
  'tick-hist': 'Tick Distribution (Histogram)',
  'tick-cdf': 'Tick Distribution (CDF)',
  'cpu-hist': 'CPU Distribution (Histogram)',
};

const RESULT_TEMPLATES: ResultTemplate[] = [
  {
    id: 'paper-baseline',
    label: 'Yardstick / Meterstick baseline',
    graphs: ['cpu', 'tick', 'mem', 'tick-hist', 'tick-cdf'],
  },
  {
    id: 'stability-focus',
    label: 'Stability focus',
    graphs: ['tick', 'tick-hist', 'tick-cdf'],
  },
  {
    id: 'capacity-planning',
    label: 'Capacity planning',
    graphs: ['cpu', 'mem', 'cpu-hist'],
  },
  {
    id: 'custom',
    label: 'Custom selection',
    graphs: [],
  },
];

function percentile(values: number[], pct: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((pct / 100) * sorted.length) - 1));
  return sorted[idx];
}

function summarize(values: number[]): SummaryStats {
  if (values.length === 0) {
    return { avg: 0, max: 0, p95: 0 };
  }
  const sum = values.reduce((acc, v) => acc + v, 0);
  return {
    avg: sum / values.length,
    max: Math.max(...values),
    p95: percentile(values, 95),
  };
}

function toPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function toNumber(value: number): string {
  return value.toFixed(2);
}

function buildHistogram(values: number[], bins = 16): Array<{ label: string; start: number; end: number; count: number; pct: number }> {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{
      label: `${min.toFixed(2)}`,
      start: min,
      end: max,
      count: values.length,
      pct: 100,
    }];
  }

  const width = (max - min) / bins;
  const hist = Array.from({ length: bins }, (_, i) => {
    const start = min + (i * width);
    const end = i === bins - 1 ? max : start + width;
    return { start, end, count: 0 };
  });

  values.forEach((v) => {
    const idx = Math.min(bins - 1, Math.floor((v - min) / width));
    hist[idx].count += 1;
  });

  return hist.map((b) => ({
    label: `${b.start.toFixed(1)}-${b.end.toFixed(1)}`,
    start: Number(b.start.toFixed(2)),
    end: Number(b.end.toFixed(2)),
    count: b.count,
    pct: Number(((b.count / values.length) * 100).toFixed(2)),
  }));
}

function buildCdf(values: number[]): Array<{ value: number; cdf: number }> {
  if (values.length === 0) return [];
  const sorted = [...values].sort((a, b) => a - b);
  return sorted.map((v, i) => ({
    value: Number(v.toFixed(2)),
    cdf: Number((((i + 1) / sorted.length) * 100).toFixed(2)),
  }));
}

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
  const socket = useSocket();
  const [runs, setRuns] = useState<string[]>([]);
  const [scratchDir, setScratchDir] = useState('');
  const [selectedRun, setSelectedRun] = useState('');
  const [loading, setLoading] = useState(false);
  const [listing, setListing] = useState(false);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('paper-baseline');
  const [selectedGraphs, setSelectedGraphs] = useState<Set<GraphId>>(new Set(RESULT_TEMPLATES[0].graphs));

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
    const onChanged = () => { if (connected && sessionId) listRuns(); };

    socket.on('results:list-ok', onList);
    socket.on('results:data', onData);
    socket.on('results:loading', onLoading);
    socket.on('results:error', onError);
    socket.on('results:changed', onChanged);

    return () => {
      socket.off('results:list-ok', onList);
      socket.off('results:data', onData);
      socket.off('results:loading', onLoading);
      socket.off('results:error', onError);
      socket.off('results:changed', onChanged);
    };
  }, [selectedRun, connected, sessionId, listRuns]);

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

  const visibleGraphs = new Set<GraphId>(
    Array.from(selectedGraphs).filter((graph) => (
      (graph === 'cpu' && hasCpu)
      || (graph === 'tick' && hasTick)
      || (graph === 'mem' && hasMem)
      || (graph === 'tick-hist' && hasTick)
      || (graph === 'tick-cdf' && hasTick)
      || (graph === 'cpu-hist' && hasCpu)
    ))
  );

  const cpuValues = chartData?.cpu.map((d) => Number(d.util || 0)).filter((v) => Number.isFinite(v)) || [];
  const memValues = chartData?.mem.map((d) => Number(d.pct || 0)).filter((v) => Number.isFinite(v)) || [];
  const tickValues = tickSorted.map((d) => d.dur).filter((v) => Number.isFinite(v));

  const cpuStats = summarize(cpuValues);
  const memStats = summarize(memValues);
  const tickStats = summarize(tickValues);
  const tickOver50Pct = tickValues.length > 0
    ? (tickValues.filter((v) => v > 50).length / tickValues.length) * 100
    : 0;

  const tickHistogram = buildHistogram(tickValues, 20);
  const cpuHistogram = buildHistogram(cpuValues, 16);
  const tickCdf = buildCdf(tickValues);

  const applyTemplate = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = RESULT_TEMPLATES.find((t) => t.id === templateId);
    if (!template || template.id === 'custom') return;
    setSelectedGraphs(new Set(template.graphs));
  };

  const toggleGraph = (graph: GraphId) => {
    setSelectedGraphs((prev) => {
      const next = new Set(prev);
      if (next.has(graph)) next.delete(graph);
      else next.add(graph);
      return next;
    });
    setSelectedTemplate('custom');
  };

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
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedRun(e.target.value)}
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
          <Text color={c.textDim} mt={3}>No runs found in results directory.</Text>
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
          <Text mt={3} color={c.textDim}>Parsing metrics...</Text>
        </Box>
      )}

      {chartData && !loading && (
        <Flex direction="column" gap={5} mt={4}>
          <Box {...cardProps}>
            <Heading fontSize="1rem" fontWeight={600} mb={3}>Analysis Template & Graphs</Heading>
            <Grid templateColumns={{ base: '1fr' }} gap={4}>
              <Box>
                <Text color={c.textDim} fontSize="0.8rem" mb={1.5}>Template</Text>
                <StyledSelect
                  {...inputProps}
                  value={selectedTemplate}
                  onChange={(e: ChangeEvent<HTMLSelectElement>) => applyTemplate(e.target.value)}
                >
                  {RESULT_TEMPLATES.map((t) => (
                    <option key={t.id} value={t.id}>{t.label}</option>
                  ))}
                </StyledSelect>
              </Box>

              <Box as="details" bg={c.bg} border="1px solid" borderColor={c.border} borderRadius={radii.sm} p={3}>
                <Text as="summary" color={c.text} fontSize="0.88rem" fontWeight={600} cursor="pointer" userSelect="none">
                  Advanced options
                </Text>
                <Box mt={3}>
                  <Text color={c.textDim} fontSize="0.8rem" mb={1.5}>Visible diagrams</Text>
                  <Flex gap={2} flexWrap="wrap">
                    {(Object.keys(GRAPH_LABELS) as GraphId[]).map((graph) => {
                      const selected = selectedGraphs.has(graph);
                      return (
                        <Button
                          key={graph}
                          variant="plain"
                          h="auto"
                          px={3}
                          py={1.5}
                          borderRadius={radii.sm}
                          fontSize="0.82rem"
                          fontWeight={600}
                          border="1px solid"
                          borderColor={selected ? c.accent : c.border}
                          bg={selected ? 'rgba(108, 92, 231, 0.2)' : 'transparent'}
                          color={selected ? c.accentLight : c.textDim}
                          _hover={{ bg: c.surface2, color: c.text }}
                          onClick={() => toggleGraph(graph)}
                        >
                          {selected ? '✓ ' : ''}{GRAPH_LABELS[graph]}
                        </Button>
                      );
                    })}
                  </Flex>
                </Box>
              </Box>
            </Grid>
          </Box>

          <Grid templateColumns={{ base: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }} gap={3}>
            <Box {...cardProps} mb={0} p={4}>
              <Text color={c.textDim} fontSize="0.75rem">CPU p95</Text>
              <Heading fontSize="1.15rem" mt={1}>{hasCpu ? toPercent(cpuStats.p95) : 'N/A'}</Heading>
            </Box>
            <Box {...cardProps} mb={0} p={4}>
              <Text color={c.textDim} fontSize="0.75rem">Memory p95</Text>
              <Heading fontSize="1.15rem" mt={1}>{hasMem ? toPercent(memStats.p95) : 'N/A'}</Heading>
            </Box>
            <Box {...cardProps} mb={0} p={4}>
              <Text color={c.textDim} fontSize="0.75rem">Tick p95</Text>
              <Heading fontSize="1.15rem" mt={1}>{hasTick ? `${toNumber(tickStats.p95)} ms` : 'N/A'}</Heading>
            </Box>
            <Box {...cardProps} mb={0} p={4}>
              <Text color={c.textDim} fontSize="0.75rem">Tick &gt; 50 ms</Text>
              <Heading fontSize="1.15rem" mt={1}>{hasTick ? toPercent(tickOver50Pct) : 'N/A'}</Heading>
            </Box>
          </Grid>

          {hasCpu && visibleGraphs.has('cpu') && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>CPU Utilization</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Percentage of active CPU time per node (cpu-total)</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={cpuPivot}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" type="number" domain={['dataMin', 'dataMax']} allowDecimals label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis domain={[0, 100]} label={{ value: 'Utilization %', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Legend />
                  {nodes.map((node, i) => (
                    <Line key={node} type="monotone" dataKey={node} stroke={NODE_COLORS[i % NODE_COLORS.length]} dot={false} strokeWidth={1.5} isAnimationActive={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {hasTick && visibleGraphs.has('tick') && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Minecraft Tick Duration</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Server tick processing time (lower is better, 50 ms = real-time threshold)</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={tickSorted}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" type="number" domain={['dataMin', 'dataMax']} allowDecimals label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis label={{ value: 'Tick (ms)', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Line type="monotone" dataKey="dur" name="Tick Duration" stroke="#e17055" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                  <ReferenceLine y={50} stroke="#fdcb6e" strokeDasharray="5 5" ifOverflow="extendDomain" label={{ value: '50 ms', position: 'insideTopRight', fill: c.warning }} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {hasMem && visibleGraphs.has('mem') && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Memory Utilization</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Used memory percentage per node</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={memPivot}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="t" type="number" domain={['dataMin', 'dataMax']} allowDecimals label={{ value: 'Time (min)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis domain={[0, 100]} label={{ value: 'Used %', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `${v} min`} />
                  <Legend />
                  {nodes.map((node, i) => (
                    <Line key={node} type="monotone" dataKey={node} stroke={NODE_COLORS[i % NODE_COLORS.length]} dot={false} strokeWidth={1.5} isAnimationActive={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {visibleGraphs.has('tick-hist') && tickHistogram.length > 0 && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Tick Duration Distribution</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Histogram of tick times for variability analysis</Text>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={tickHistogram}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="label" interval="preserveStartEnd" angle={-28} textAnchor="end" height={64} {...axisProps} />
                  <YAxis label={{ value: 'Samples', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value) => [value ?? 0, 'Samples']}
                    labelFormatter={(label) => `Tick range: ${label} ms`}
                  />
                  <Bar dataKey="count" fill="#e17055" isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}

          {visibleGraphs.has('tick-cdf') && tickCdf.length > 0 && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>Tick Duration CDF</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Cumulative distribution of tick duration (lower is better)</Text>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={tickCdf}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="value" type="number" domain={[0, 'dataMax']} allowDecimals tickFormatter={(v) => toNumber(Number(v))} label={{ value: 'Tick duration (ms)', position: 'insideBottom', offset: -5, fill: c.textDim }} {...axisProps} />
                  <YAxis domain={[0, 100]} label={{ value: 'CDF (%)', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value) => [`${toNumber(Number(value ?? 0))}%`, 'CDF']}
                    labelFormatter={(v) => `${v} ms`}
                  />
                  <Line type="monotone" dataKey="cdf" stroke="#fdcb6e" dot={false} strokeWidth={1.6} name="Tick CDF" isAnimationActive={false} />
                  {tickCdf.length > 0 && tickCdf[tickCdf.length - 1].value >= 50 && (
                    <ReferenceLine x={50} stroke="#e17055" strokeDasharray="5 5" label={{ value: '50 ms threshold', position: 'top', fill: c.error }} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {visibleGraphs.has('cpu-hist') && cpuHistogram.length > 0 && (
            <Box {...cardProps} pb={6}>
              <Heading fontSize="1rem" fontWeight={600} mb={0.5}>CPU Utilization Distribution</Heading>
              <Text color={c.textDim} fontSize="0.8rem" mb={3}>Histogram of CPU utilization samples across nodes</Text>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={cpuHistogram}>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.border} />
                  <XAxis dataKey="label" interval="preserveStartEnd" angle={-28} textAnchor="end" height={64} {...axisProps} />
                  <YAxis label={{ value: 'Samples', angle: -90, position: 'insideLeft', fill: c.textDim }} {...axisProps} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value) => [value ?? 0, 'Samples']}
                    labelFormatter={(label) => `CPU range: ${label}%`}
                  />
                  <Bar dataKey="count" fill="#6c5ce7" isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          )}

          {!hasCpu && !hasTick && !hasMem && (
            <Box {...cardProps} textAlign="center" p={10}>
              <Text color={c.textDim}>No metrics found for this run.</Text>
            </Box>
          )}
        </Flex>
      )}
    </Box>
  );
}
