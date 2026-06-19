import { type ReactNode, useEffect, useState } from 'react';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import useCloudProvider from '../../hooks/useCloudProvider';
import type { CloudInstance, CloudInstanceHandoff } from '../../lib/cloud/types';
import { c, radii } from '../../theme';
import AwsAuth from './AwsAuth';
import InstanceList from './InstanceList';
import LaunchInstanceDialog from './LaunchInstanceDialog';
import type { CloudAdapter } from '../../lib/cloud/adapter';

type AwsTab = 'account' | 'instances';

interface Props {
  onUseInstance: (h: CloudInstanceHandoff) => void;
  /** SSH connect form rendered inside the Instances tab, below the instance list. */
  connectSlot: ReactNode;
}

export default function AwsCloudContent({ onUseInstance, connectSlot }: Props) {
  const cp = useCloudProvider('aws');
  const [awsTab, setAwsTab] = useState<AwsTab>(() => (cp.authenticated ? 'instances' : 'account'));
  const [showLaunch, setShowLaunch] = useState(false);

  useEffect(() => {
    if (cp.authenticated) {
      setAwsTab('instances');
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
    setAwsTab('instances');
  };

  return (
    <>
      <Flex mt={4} mb={4} border="1px solid" borderColor={c.border} borderRadius={radii.sm} overflow="hidden">
        {(['account', 'instances'] as const).map((t) => (
          <Button key={t} variant="plain" flex={1} h="auto" py={2}
            bg={awsTab === t ? c.accent : 'transparent'}
            color={awsTab === t ? 'white' : c.textDim}
            borderRadius={0} fontSize="0.85rem" fontWeight={500}
            _hover={awsTab !== t ? { bg: c.surface2, color: c.text } : {}}
            onClick={() => setAwsTab(t)}>
            {t === 'account' ? 'Account' : 'Instances'}
          </Button>
        ))}
      </Flex>

      {cp.error && (
        <Text color={c.error} fontSize="0.85rem" mb={3}>{cp.error}</Text>
      )}

      {awsTab === 'account' && cp.adapter && (
        <AwsAuth
          bare
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

      {awsTab === 'instances' && (
        <>
          {cp.authenticated && cp.adapter ? (
            <>
              <Flex align="center" gap={3} mb={4}>
                <Text fontSize="0.85rem" fontWeight={600} color={c.textDim} flexShrink={0}>Region</Text>
                <RegionPicker region={cp.region} onChange={cp.setRegion} adapter={cp.adapter} />
              </Flex>
              <Flex justify="flex-end" mb={3}>
                <Button variant="plain" bg={c.accent} color="white" borderRadius={radii.sm}
                  px={4} py="7px" h="auto" fontSize="0.85rem" fontWeight={600}
                  _hover={{ bg: c.accentLight }} onClick={() => setShowLaunch((v) => !v)}>
                  {showLaunch ? 'Cancel' : '+ Create instance'}
                </Button>
              </Flex>
              {showLaunch && cp.adapter && (
                <Box mb={4}>
                  <LaunchInstanceDialog
                    adapter={cp.adapter}
                    region={cp.region}
                    onRegionChange={cp.setRegion}
                    onLaunch={async (req) => { const ids = await cp.launch(req); await cp.refreshInstances(); return ids; }}
                    onClose={() => setShowLaunch(false)}
                  />
                </Box>
              )}
              <InstanceList
                bare
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
            <Text color={c.textDim} fontSize="0.88rem" mb={2}>
              Sign in first (Account tab) to see your instances.
            </Text>
          )}

          <Box mt={4} pt={4} borderTop="1px solid" borderColor={c.border}>
            {connectSlot}
          </Box>
        </>
      )}
    </>
  );
}

function RegionPicker({ region, onChange, adapter }: { region: string; onChange: (r: string) => void; adapter: CloudAdapter }) {
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
