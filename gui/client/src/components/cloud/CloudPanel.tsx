import { useEffect, useState } from 'react';
import { Box, Button, Flex, Heading, Icon, Text } from '@chakra-ui/react';
import { LuCloud, LuPlus } from 'react-icons/lu';
import useCloudProvider from '../../hooks/useCloudProvider';
import type { CloudInstance, CloudInstanceHandoff } from '../../lib/cloud/types';
import { c, cardProps, radii } from '../../theme';
import AwsAuth from './AwsAuth';
import LaunchInstanceDialog from './LaunchInstanceDialog';
import InstanceList from './InstanceList';

type Tab = 'signin' | 'instances';

interface Props {
  onUseInstance: (handoff: CloudInstanceHandoff) => void;
}

export default function CloudPanel({ onUseInstance }: Props) {
  const cp = useCloudProvider('aws');
  const [tab, setTab] = useState<Tab>('signin');
  const [showLaunch, setShowLaunch] = useState(false);

  useEffect(() => {
    if (cp.authenticated) {
      setTab('instances');
      cp.refreshInstances();
      cp.startPolling();
      return () => cp.stopPolling();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cp.authenticated, cp.region]);

  const handleUse = async (inst: CloudInstance) => {
    let privateKey: string | null = null;
    if (inst.keyName) {
      try {
        privateKey = await cp.adapter?.getKeyMaterial(inst.keyName) ?? null;
      } catch {
        privateKey = null;
      }
    }
    onUseInstance({
      provider: inst.provider,
      region: inst.region,
      host: inst.publicIp || '',
      username: inst.defaultUsername || 'ec2-user',
      keyName: inst.keyName,
      privateKey,
      instanceId: inst.id,
      imageId: inst.imageId,
      instanceType: inst.instanceType,
      securityGroupIds: inst.securityGroupIds || [],
    });
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'signin', label: 'Sign In' },
    { id: 'instances', label: 'Instances' },
  ];

  return (
    <Box>
      <Box {...cardProps}>
        <Flex align="center" gap={2} mb={3}>
          <Icon as={LuCloud} boxSize="18px" color={c.accentLight} />
          <Heading fontSize="1.15rem" fontWeight={600}>AWS Cloud</Heading>
        </Flex>
        <Flex border="1px solid" borderColor={c.border} borderRadius={radii.sm} overflow="hidden">
          {tabs.map((t) => (
            <Button key={t.id} variant="plain" flex={1} h="auto" py={2}
              bg={tab === t.id ? c.accent : 'transparent'}
              color={tab === t.id ? 'white' : c.textDim}
              borderRadius={0} fontSize="0.85rem" fontWeight={500}
              _hover={tab !== t.id ? { bg: c.surface2, color: c.text } : {}}
              onClick={() => setTab(t.id)}>
              {t.label}
            </Button>
          ))}
        </Flex>
      </Box>

      {cp.error && (
        <Box {...cardProps} borderColor={c.error}>
          <Flex justify="space-between" align="center">
            <Text color={c.error} fontSize="0.88rem">{cp.error}</Text>
            <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} px={3} py={1.5} h="auto" fontSize="0.78rem" borderRadius={radii.sm} _hover={{ bg: c.surface2 }} onClick={cp.clearError}>
              Dismiss
            </Button>
          </Flex>
        </Box>
      )}

      {tab === 'signin' && cp.adapter && (
        <AwsAuth
          profiles={cp.profiles}
          activeProfileId={cp.activeProfileId}
          authenticated={cp.authenticated}
          authenticating={cp.authenticating}
          defaultRegion={cp.region}
          onAuthenticate={cp.authenticate}
          onLogout={cp.logout}
          onDeleteProfile={async (id) => { await cp.adapter!.deleteProfile(id); await cp.refreshProfiles(); }}
        />
      )}

      {tab === 'instances' && cp.adapter && (
        cp.authenticated ? (
          <>
            <Box {...cardProps}>
              <Flex justify="space-between" align="center">
                <Box>
                  <Heading fontSize="1rem" fontWeight={600} mb={1}>Region</Heading>
                  <Text color={c.textDim} fontSize="0.85rem">All actions below run against this region.</Text>
                </Box>
                <Flex gap={2.5} align="center">
                  <RegionPicker region={cp.region} onChange={cp.setRegion} adapter={cp.adapter} />
                  <Button variant="plain" bg={c.accent} color="white" borderRadius={radii.sm} px={4} py={2} h="auto" fontSize="0.85rem" fontWeight={600} _hover={{ bg: c.accentLight }} onClick={() => setShowLaunch((v) => !v)}>
                    <Icon as={LuPlus} boxSize="14px" /><Box as="span" ml={1.5}>{showLaunch ? 'Hide' : 'New instance'}</Box>
                  </Button>
                </Flex>
              </Flex>
            </Box>
            {showLaunch && (
              <LaunchInstanceDialog
                adapter={cp.adapter}
                region={cp.region}
                onRegionChange={cp.setRegion}
                onLaunch={cp.launch}
                onClose={() => setShowLaunch(false)}
              />
            )}
            <InstanceList
              instances={cp.instances}
              loading={cp.loadingInstances}
              onRefresh={cp.refreshInstances}
              onStart={cp.start}
              onStop={cp.stop}
              onTerminate={cp.terminate}
              onUse={handleUse}
            />
          </>
        ) : (
          <Box {...cardProps}>
            <Text color={c.textDim} fontSize="0.88rem">Sign in first to manage instances.</Text>
          </Box>
        )
      )}
    </Box>
  );
}

function RegionPicker({ region, onChange, adapter }: { region: string; onChange: (r: string) => void; adapter: import('../../lib/cloud/adapter').CloudAdapter }) {
  const [regions, setRegions] = useState<string[]>([region]);
  useEffect(() => {
    let cancelled = false;
    adapter.listRegions().then((rs) => { if (!cancelled) setRegions(rs.map((r) => r.id)); }).catch(() => {});
    return () => { cancelled = true; };
  }, [adapter]);
  return (
    <select
      value={region}
      onChange={(e) => onChange(e.target.value)}
      style={{
        background: c.bg, color: c.text, border: `1px solid ${c.border}`,
        borderRadius: 6, padding: '6px 10px', fontSize: '0.85rem',
      }}
    >
      {regions.map((r) => <option key={r} value={r} style={{ backgroundColor: c.bg }}>{r}</option>)}
    </select>
  );
}
