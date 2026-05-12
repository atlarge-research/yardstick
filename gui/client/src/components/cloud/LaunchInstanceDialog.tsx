import { useEffect, useState } from 'react';
import { Box, Button, Flex, Grid, Heading, Spinner, Text } from '@chakra-ui/react';
import type { CloudAdapter } from '../../lib/cloud/adapter';
import type {
  CloudImage,
  CloudLaunchRequest,
  CloudRegion,
  CloudSecurityGroup,
} from '../../lib/cloud/types';
import { c, cardProps, inputProps, labelProps, radii, StyledInput, StyledSelect } from '../../theme';

interface Props {
  adapter: CloudAdapter;
  region: string;
  onRegionChange: (region: string) => void;
  onLaunch: (req: CloudLaunchRequest) => Promise<string[]>;
  onClose?: () => void;
}

export default function LaunchInstanceDialog({ adapter, region, onRegionChange, onLaunch, onClose }: Props) {
  const [regions, setRegions] = useState<CloudRegion[]>([]);
  const [images, setImages] = useState<CloudImage[]>([]);
  const [instanceTypes, setInstanceTypes] = useState<string[]>([]);
  const [keyPairs, setKeyPairs] = useState<string[]>([]);
  const [securityGroups, setSecurityGroups] = useState<CloudSecurityGroup[]>([]);

  const [imageId, setImageId] = useState('');
  const [instanceType, setInstanceType] = useState('t3.micro');
  const [keyName, setKeyName] = useState('');
  const [sgIds, setSgIds] = useState<string[]>([]);
  const [name, setName] = useState('yardstick-benchmark');
  const [imageSearch, setImageSearch] = useState('ubuntu');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await adapter.listRegions();
        if (!cancelled) setRegions(list);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      }
    })();
    return () => { cancelled = true; };
  }, [adapter]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setImages([]);
    setInstanceTypes([]);
    setKeyPairs([]);
    setSecurityGroups([]);
    (async () => {
      try {
        const [imgs, types, keys, sgs] = await Promise.all([
          adapter.listImages(region, { search: imageSearch }),
          adapter.listInstanceTypes(region),
          adapter.listKeyPairs(region),
          adapter.listSecurityGroups(region),
        ]);
        if (cancelled) return;
        setImages(imgs);
        setInstanceTypes(types);
        setKeyPairs(keys);
        setSecurityGroups(sgs);
        if (imgs[0] && !imageId) setImageId(imgs[0].id);
        if (keys[0] && !keyName) setKeyName(keys[0]);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [adapter, region, imageSearch]);

  const launch = async () => {
    setError(null);
    if (!imageId) { setError('Pick an image'); return; }
    if (!instanceType) { setError('Pick an instance type'); return; }
    setSubmitting(true);
    try {
      await onLaunch({
        region,
        imageId,
        instanceType,
        keyName: keyName || undefined,
        securityGroupIds: sgIds,
        count: 1,
        name: name || undefined,
      });
      onClose?.();
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSg = (id: string) => {
    setSgIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  return (
    <Box {...cardProps}>
      <Flex justify="space-between" align="center" mb={3}>
        <Heading fontSize="1.05rem" fontWeight={600}>Launch instance</Heading>
        {onClose && (
          <Button variant="plain" bg="transparent" color={c.textDim} _hover={{ color: c.text }} onClick={onClose}>×</Button>
        )}
      </Flex>

      <Grid templateColumns="1fr 1fr" gap={4}>
        <Box>
          <Text {...labelProps}>Region</Text>
          <StyledSelect {...inputProps} value={region} onChange={(e) => onRegionChange(e.target.value)}>
            {(regions.length ? regions : [{ id: region, name: region }]).map((r) => (
              <option key={r.id} value={r.id} style={{ backgroundColor: c.bg }}>{r.id}</option>
            ))}
          </StyledSelect>
        </Box>
        <Box>
          <Text {...labelProps}>Name tag</Text>
          <StyledInput {...inputProps} value={name} onChange={(e) => setName(e.target.value)} />
        </Box>
      </Grid>

      <Grid templateColumns="1fr 1fr" gap={4} mt={3}>
        <Box>
          <Text {...labelProps}>Image search</Text>
          <StyledInput {...inputProps} value={imageSearch} onChange={(e) => setImageSearch(e.target.value)} placeholder="ubuntu / al2023-ami / ..." />
        </Box>
        <Box>
          <Text {...labelProps}>Instance type</Text>
          <StyledSelect {...inputProps} value={instanceType} onChange={(e) => setInstanceType(e.target.value)} disabled={loading}>
            {instanceTypes.length === 0 && <option value={instanceType} style={{ backgroundColor: c.bg }}>{instanceType}</option>}
            {instanceTypes.map((t) => (
              <option key={t} value={t} style={{ backgroundColor: c.bg }}>{t}</option>
            ))}
          </StyledSelect>
        </Box>
      </Grid>

      <Box mt={3}>
        <Text {...labelProps}>AMI {loading && <Spinner size="xs" ml={2} />}</Text>
        <StyledSelect {...inputProps} value={imageId} onChange={(e) => setImageId(e.target.value)} disabled={loading || images.length === 0}>
          {images.length === 0 && <option value="" style={{ backgroundColor: c.bg }}>—</option>}
          {images.map((i) => (
            <option key={i.id} value={i.id} style={{ backgroundColor: c.bg }}>{i.name} ({i.id})</option>
          ))}
        </StyledSelect>
      </Box>

      <Box mt={3}>
        <Text {...labelProps}>SSH key pair</Text>
        <StyledSelect {...inputProps} value={keyName} onChange={(e) => setKeyName(e.target.value)} disabled={loading}>
          <option value="" style={{ backgroundColor: c.bg }}>— none —</option>
          {keyPairs.map((k) => (
            <option key={k} value={k} style={{ backgroundColor: c.bg }}>{k}</option>
          ))}
        </StyledSelect>
      </Box>

      <Box mt={3}>
        <Text {...labelProps}>Security groups</Text>
        <Box border="1px solid" borderColor={c.border} borderRadius={radii.sm} maxH="160px" overflowY="auto" bg={c.bg}>
          {securityGroups.length === 0 && <Text px={3} py={2} color={c.textDim} fontSize="0.85rem">No security groups in this region.</Text>}
          {securityGroups.map((g) => (
            <Flex key={g.id} as="label" align="center" gap={2.5} px={3} py={1.5} cursor="pointer" _hover={{ bg: c.surface2 }} fontSize="0.85rem">
              <input type="checkbox" checked={sgIds.includes(g.id)} onChange={() => toggleSg(g.id)} style={{ accentColor: c.accent }} />
              <Text flex={1}>{g.name}</Text>
              <Text color={c.textDim}>{g.id}</Text>
            </Flex>
          ))}
        </Box>
      </Box>

      {error && <Text color={c.error} fontSize="0.85rem" mt={3}>{error}</Text>}

      <Flex mt={4} gap={2.5}>
        <Button variant="plain" bg={c.accent} color="white" borderRadius={radii.sm}
          px={5} py="10px" h="auto" fontSize="0.9rem" fontWeight={600}
          _hover={{ bg: c.accentLight }} disabled={submitting || loading} onClick={launch}>
          {submitting ? (<><Spinner size="sm" /> Launching…</>) : 'Launch'}
        </Button>
        {onClose && (
          <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} borderRadius={radii.sm} px={5} py="10px" h="auto" _hover={{ bg: c.surface2 }} onClick={onClose}>
            Cancel
          </Button>
        )}
      </Flex>
    </Box>
  );
}
