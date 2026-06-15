import { useEffect, useState, type FormEvent } from 'react';
import { Box, Button, Flex, Grid, Heading, Spinner, Text } from '@chakra-ui/react';
import type { AwsCredentials, CloudProfile } from '../../lib/cloud/types';
import { c, cardProps, inputProps, labelProps, radii, StyledInput, StyledSelect } from '../../theme';

interface Props {
  profiles: CloudProfile[];
  activeProfileId: string | null;
  authenticated: boolean;
  authenticating: boolean;
  defaultRegion: string;
  onAuthenticate: (creds: AwsCredentials) => Promise<void>;
  onLogout: () => Promise<void>;
  onDeleteProfile: (id: string) => Promise<void>;
  /** When true, renders content without a card wrapper (for embedding inside another card). */
  bare?: boolean;
}

const REGIONS_FALLBACK = [
  'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
  'eu-west-1', 'eu-west-2', 'eu-central-1', 'eu-north-1',
  'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
];

export default function AwsAuth({
  profiles, activeProfileId, authenticated, authenticating,
  defaultRegion, onAuthenticate, onLogout, onDeleteProfile, bare = false,
}: Props) {
  const [mode, setMode] = useState<'new' | 'existing'>(profiles.length > 0 ? 'existing' : 'new');
  const [accessKeyId, setAccessKeyId] = useState('');
  const [secretAccessKey, setSecretAccessKey] = useState('');
  const [sessionToken, setSessionToken] = useState('');
  const [region, setRegion] = useState(defaultRegion);
  const [profileName, setProfileName] = useState('');
  const [save, setSave] = useState(true);
  const [profileId, setProfileId] = useState<string>(activeProfileId || profiles[0]?.id || '');
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (profiles.length > 0 && !profileId) setProfileId(profiles[0].id);
    if (profiles.length === 0 && mode === 'existing') setMode('new');
  }, [profiles, profileId, mode]);

  useEffect(() => { setRegion(defaultRegion); }, [defaultRegion]);

  if (authenticated) {
    const active = profiles.find((p) => p.id === activeProfileId);
    const signedInContent = (
      <Flex justify="space-between" align="center" mb={bare ? 0 : 2}>
        <Box>
          {!bare && <Heading fontSize="1rem" fontWeight={600} mb={0.5}>AWS — Signed in</Heading>}
          <Text color={c.textDim} fontSize="0.88rem">
            {active ? `${active.name} • ` : ''}Region: <Text as="span" color={c.text}>{defaultRegion}</Text>
          </Text>
        </Box>
        <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.text} borderRadius={radii.sm} px={3.5} py={2} h="auto" fontSize="0.82rem" _hover={{ bg: c.surface2 }} onClick={onLogout}>
          Sign out
        </Button>
      </Flex>
    );
    return bare ? signedInContent : <Box {...cardProps}>{signedInContent}</Box>;
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    try {
      if (mode === 'existing') {
        if (!profileId) { setLocalError('Pick a profile'); return; }
        await onAuthenticate({ profileId, region });
      } else {
        if (!accessKeyId || !secretAccessKey) { setLocalError('Access key & secret are required'); return; }
        await onAuthenticate({
          accessKeyId,
          secretAccessKey,
          sessionToken: sessionToken || undefined,
          region,
          save,
          profileName: profileName || undefined,
        });
      }
    } catch (err: any) {
      setLocalError(err?.message || String(err));
    }
  };

  const formBody = (
    <>
      {profiles.length > 0 && (
        <Flex mb={4} border="1px solid" borderColor={c.border} borderRadius={radii.sm} overflow="hidden">
          {(['existing', 'new'] as const).map((m) => (
            <Button key={m} variant="plain" flex={1} h="auto" py={2}
              bg={mode === m ? c.accent : c.bg} color={mode === m ? 'white' : c.textDim}
              borderRadius={0} fontSize="0.85rem" fontWeight={500}
              _hover={mode !== m ? { bg: c.surface2 } : {}}
              onClick={() => setMode(m)}>
              {m === 'existing' ? 'Saved profile' : 'New credentials'}
            </Button>
          ))}
        </Flex>
      )}

      <Box as="form" onSubmit={submit}>
        {mode === 'existing' ? (
          <Box mb={4}>
            <Text {...labelProps}>Profile</Text>
            <Flex gap={2.5}>
              <StyledSelect
                {...inputProps}
                value={profileId}
                onChange={(e) => setProfileId(e.target.value)}
                flex={1}
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id} style={{ backgroundColor: c.bg }}>
                    {p.name}{p.defaultRegion ? ` (${p.defaultRegion})` : ''}
                  </option>
                ))}
              </StyledSelect>
              <Button variant="plain" bg="transparent" border="1px solid" borderColor={c.border} color={c.error} borderRadius={radii.sm} px={3} py={2} h="auto" fontSize="0.82rem"
                onClick={async (e) => { e.preventDefault(); if (profileId) await onDeleteProfile(profileId); }}>
                Delete
              </Button>
            </Flex>
          </Box>
        ) : (
          <>
            <Box mb={4}>
              <Text {...labelProps}>Access Key ID</Text>
              <StyledInput {...inputProps} value={accessKeyId} onChange={(e) => setAccessKeyId(e.target.value)} placeholder="AKIA..." autoComplete="off" />
            </Box>
            <Box mb={4}>
              <Text {...labelProps}>Secret Access Key</Text>
              <StyledInput {...inputProps} type="password" value={secretAccessKey} onChange={(e) => setSecretAccessKey(e.target.value)} placeholder="••••••••" autoComplete="off" />
            </Box>
            <Box mb={4}>
              <Text {...labelProps}>Session Token (optional, for STS)</Text>
              <StyledInput {...inputProps} value={sessionToken} onChange={(e) => setSessionToken(e.target.value)} placeholder="" autoComplete="off" />
            </Box>
          </>
        )}

        <Grid templateColumns="1fr 1fr" gap={4}>
          <Box mb={4}>
            <Text {...labelProps}>Default Region</Text>
            <StyledSelect {...inputProps} value={region} onChange={(e) => setRegion(e.target.value)}>
              {REGIONS_FALLBACK.map((r) => (
                <option key={r} value={r} style={{ backgroundColor: c.bg }}>{r}</option>
              ))}
            </StyledSelect>
          </Box>
          {mode === 'new' && (
            <Box mb={4}>
              <Text {...labelProps}>Profile Name (optional)</Text>
              <StyledInput {...inputProps} value={profileName} onChange={(e) => setProfileName(e.target.value)} placeholder="e.g. lab-ec2-us-east-1" />
            </Box>
          )}
        </Grid>

        {mode === 'new' && (
          <Flex as="label" align="center" gap={2} mb={4} cursor="pointer" fontSize="0.88rem" color={c.text}>
            <input type="checkbox" checked={save} onChange={(e) => setSave(e.target.checked)} style={{ width: 16, height: 16, accentColor: c.accent }} />
            Save these credentials (encrypted locally)
          </Flex>
        )}

        {localError && (
          <Text color={c.error} fontSize="0.85rem" mb={3}>{localError}</Text>
        )}

        <Button type="submit" variant="plain" bg={c.accent} color="white" borderRadius={radii.sm}
          px={5} py="10px" h="auto" fontSize="0.9rem" fontWeight={600}
          _hover={{ bg: c.accentLight }} disabled={authenticating}>
          {authenticating ? (<><Spinner size="sm" /> Signing in…</>) : 'Sign in to AWS'}
        </Button>
      </Box>
    </>
  );

  if (bare) return formBody;
  return (
    <Box {...cardProps}>
      <Heading fontSize="1.05rem" fontWeight={600} mb={1.5}>AWS — Sign in</Heading>
      <Text color={c.textDim} fontSize="0.88rem" mb={4}>
        Credentials are stored encrypted on this machine only and used to call the AWS SDK from the local server.
      </Text>
      {formBody}
    </Box>
  );
}
