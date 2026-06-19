import { useState, useEffect, useCallback, type FormEvent, type ChangeEvent, type ReactNode } from 'react';
import { Box, Flex, Grid, Text, Heading, Button, Badge, Icon, Spinner } from '@chakra-ui/react';
import { LuMonitor, LuGlobe, LuHash, LuServer, LuCloud, LuBookmark, LuTrash2 } from 'react-icons/lu';
import type { IconType } from 'react-icons';
import type { SshConnectOptions, StepStatus } from '../hooks/useYardstick';
import { c, fonts, radii, cardProps, inputProps, labelProps, StyledInput, StyledTextarea } from '../theme';

type AuthMethod = 'password' | 'key';

const DAS_PROFILES_KEY = 'yardstick_das_profiles';

interface DasProfile {
  name: string;
  username: string;
  authMethod: AuthMethod;
  password: string;
  privateKey: string;
  useJumpHost: boolean;
  jumpHost: string;
  jumpPort: string;
  jumpUsername: string;
  jumpAuthMethod: AuthMethod;
  jumpPassword: string;
  jumpPrivateKey: string;
}

function loadDasProfiles(): DasProfile[] {
  try {
    return JSON.parse(localStorage.getItem(DAS_PROFILES_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveDasProfilesToStorage(profiles: DasProfile[]) {
  localStorage.setItem(DAS_PROFILES_KEY, JSON.stringify(profiles));
}

interface ModePreset {
  host: string;
  port: string;
  label: string;
  description: string;
  defaultJump: boolean;
  jumpHost?: string;
  preferredAuthMethod?: AuthMethod;
  hostPlaceholder?: string;
  usernamePlaceholder?: string;
}

const MODE_ICONS: Record<string, IconType> = {
  local: LuMonitor,
  das5: LuHash,
  das6: LuHash,
  aws: LuServer,
  custom: LuGlobe,
};

type Group = 'cloud' | 'das' | 'ssh' | 'local';

interface GroupDef {
  id: Group;
  label: string;
  icon: IconType;
}

interface SubProviderDef {
  mode: string;
  label: string;
  shortLabel?: string;
  disabled?: boolean;
  hint?: string;
}

const GROUPS: GroupDef[] = [
  { id: 'das',   label: 'DAS',   icon: LuHash },
  { id: 'cloud', label: 'Cloud', icon: LuCloud },
  { id: 'ssh',   label: 'SSH',   icon: LuGlobe },
  { id: 'local', label: 'Local', icon: LuMonitor },
];

const SUB_PROVIDERS: Partial<Record<Group, SubProviderDef[]>> = {
  cloud: [
    { mode: 'aws', label: 'AWS', shortLabel: 'AWS' },
  ],
  das: [
    { mode: 'das5', label: 'DAS-5', shortLabel: '5' },
    { mode: 'das6', label: 'DAS-6', shortLabel: '6' },
  ],
};

function groupForMode(mode: string): Group {
  if (mode === 'aws') return 'cloud';
  if (mode === 'das5' || mode === 'das6') return 'das';
  if (mode === 'local') return 'local';
  return 'ssh';
}

function defaultModeForGroup(g: Group): string {
  if (g === 'cloud') return 'aws';
  if (g === 'das') return 'das5';
  if (g === 'ssh') return 'custom';
  return 'local';
}

const MODE_PRESETS: Record<string, ModePreset> = {
  local: { host: '', port: '', label: 'Local Machine', description: 'Run everything on this machine - no SSH needed.', defaultJump: false },
  das5: { host: 'fs0.das5.cs.vu.nl', port: '22', label: 'DAS-5', description: 'Connect to DAS-5 via SSH. Enable ProxyJump if off-campus.', defaultJump: false, jumpHost: 'ssh.data.vu.nl' },
  das6: { host: 'fs0.das6.cs.vu.nl', port: '22', label: 'DAS-6', description: 'Connect to DAS-6 via SSH. Enable ProxyJump if off-campus.', defaultJump: false, jumpHost: 'ssh.data.vu.nl' },
  aws: {
    host: '',
    port: '22',
    label: 'AWS EC2',
    description: 'Connect to an AWS EC2 instance over SSH using the instance public DNS or Elastic IP.',
    defaultJump: false,
    preferredAuthMethod: 'key',
    hostPlaceholder: 'ec2-203-0-113-10.compute-1.amazonaws.com',
    usernamePlaceholder: 'ec2-user',
  },
  custom: { host: '', port: '22', label: 'Custom SSH', description: 'Connect to any remote host via SSH.', defaultJump: false },
};

interface AuthToggleProps {
  value: AuthMethod;
  onChange: (m: AuthMethod) => void;
}

function AuthToggle({ value, onChange }: AuthToggleProps) {
  return (
    <Flex mb={4} border="1px solid" borderColor={c.border} borderRadius={radii.sm} overflow="hidden">
      {(['password', 'key'] as const).map((m) => (
        <Button
          key={m}
          variant="plain"
          flex={1}
          bg={value === m ? c.accent : c.bg}
          color={value === m ? 'white' : c.textDim}
          borderRadius={0}
          border="none"
          fontSize="0.85rem"
          fontWeight={500}
          py={2}
          h="auto"
          _hover={value !== m ? { bg: c.surface2 } : {}}
          onClick={() => onChange(m)}
        >
          {m === 'password' ? 'Password' : 'SSH Key'}
        </Button>
      ))}
    </Flex>
  );
}

interface ConnectFormProps {
  onConnect: (opts: SshConnectOptions) => void;
  status: StepStatus;
  mode: string;
  onModeChange: (mode: string) => void;
  prefill?: Partial<SshConnectOptions> | null;
  onPrefillConsumed?: () => void;
  /**
   * When provided and mode==='aws', this render prop is called with the SSH form
   * as its argument. The result replaces the normal form, allowing custom cloud
   * UI (tabs, instance list, etc.) to embed the form as a slot.
   */
  cloudContent?: (sshForm: ReactNode) => ReactNode;
}

export default function ConnectForm({ onConnect, status, mode, onModeChange, prefill, onPrefillConsumed, cloudContent }: ConnectFormProps) {
  const [host, setHost] = useState(MODE_PRESETS[mode]?.host || '');
  const [port, setPort] = useState(MODE_PRESETS[mode]?.port || '22');
  const [username, setUsername] = useState('');
  const [authMethod, setAuthMethod] = useState<AuthMethod>('password');
  const [password, setPassword] = useState('');
  const [privateKey, setPrivateKey] = useState('');
  const [useJumpHost, setUseJumpHost] = useState(MODE_PRESETS[mode]?.defaultJump || false);
  const [jumpHost, setJumpHost] = useState(MODE_PRESETS[mode]?.jumpHost || '');
  const [jumpPort, setJumpPort] = useState('22');
  const [jumpUsername, setJumpUsername] = useState('');
  const [jumpAuthMethod, setJumpAuthMethod] = useState<AuthMethod>('password');
  const [jumpPassword, setJumpPassword] = useState('');
  const [jumpPrivateKey, setJumpPrivateKey] = useState('');

  const [dasProfiles, setDasProfiles] = useState<DasProfile[]>(loadDasProfiles);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileName, setProfileName] = useState('');

  const loadProfile = useCallback((name: string) => {
    const profile = dasProfiles.find((p) => p.name === name);
    if (!profile) return;
    setUsername(profile.username);
    setAuthMethod(profile.authMethod);
    setPassword(profile.password);
    setPrivateKey(profile.privateKey);
    setUseJumpHost(profile.useJumpHost);
    setJumpHost(profile.jumpHost || MODE_PRESETS[mode]?.jumpHost || '');
    setJumpPort(profile.jumpPort);
    setJumpUsername(profile.jumpUsername);
    setJumpAuthMethod(profile.jumpAuthMethod);
    setJumpPassword(profile.jumpPassword);
    setJumpPrivateKey(profile.jumpPrivateKey);
    setSelectedProfile(name);
  }, [dasProfiles, mode]);

  const saveProfile = useCallback(() => {
    const name = profileName.trim();
    if (!name) return;
    const profile: DasProfile = {
      name, username, authMethod, password, privateKey,
      useJumpHost, jumpHost, jumpPort, jumpUsername,
      jumpAuthMethod, jumpPassword, jumpPrivateKey,
    };
    const updated = [...dasProfiles.filter((p) => p.name !== name), profile];
    setDasProfiles(updated);
    saveDasProfilesToStorage(updated);
    setSelectedProfile(name);
    setSavingProfile(false);
    setProfileName('');
  }, [profileName, username, authMethod, password, privateKey, useJumpHost, jumpHost, jumpPort, jumpUsername, jumpAuthMethod, jumpPassword, jumpPrivateKey, dasProfiles]);

  const deleteProfile = useCallback((name: string) => {
    const updated = dasProfiles.filter((p) => p.name !== name);
    setDasProfiles(updated);
    saveDasProfilesToStorage(updated);
    if (selectedProfile === name) setSelectedProfile('');
  }, [dasProfiles, selectedProfile]);

  useEffect(() => {
    const preset = MODE_PRESETS[mode];
    if (preset) {
      setHost(preset.host);
      setPort(preset.port);
      setUseJumpHost(preset.defaultJump || false);
      setJumpHost(preset.jumpHost || '');
      setJumpPort('22');
      if (preset.preferredAuthMethod) {
        setAuthMethod(preset.preferredAuthMethod);
      }
    }
  }, [mode]);

  useEffect(() => {
    if (!prefill) return;
    if (prefill.host !== undefined) setHost(prefill.host || '');
    if (prefill.port !== undefined) setPort(prefill.port || '22');
    if (prefill.username !== undefined) setUsername(prefill.username || '');
    if (prefill.privateKey !== undefined) {
      setPrivateKey(prefill.privateKey || '');
      setAuthMethod('key');
    } else if (prefill.password !== undefined) {
      setPassword(prefill.password || '');
      setAuthMethod('password');
    }
    onPrefillConsumed?.();
  }, [prefill, onPrefillConsumed]);

  const isRunning = status === 'running';
  const isConnected = status === 'completed';
  const isLocal = mode === 'local';
  const isSSH = !isLocal;
  const group = groupForMode(mode);
  const subProviders = SUB_PROVIDERS[group];
  const preset = MODE_PRESETS[mode] || MODE_PRESETS.das5;
  const hostPlaceholder = preset.hostPlaceholder || 'hostname';
  const usernamePlaceholder = preset.usernamePlaceholder || `Your ${preset.label} username`;
  const cloudHint = mode === 'aws' ? {
    title: 'AWS EC2 quick setup',
    lines: [
      'Use the instance public DNS or Elastic IP as the hostname.',
      'Port 22 must be open in the instance security group.',
      'EC2 AMIs disable password auth by default — use SSH key.',
    ],
  } : null;

  const selectGroup = (g: Group) => {
    if (g === group) return;
    onModeChange(defaultModeForGroup(g));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (isLocal) {
      onConnect({ mode: 'local' });
    } else {
      const payload: SshConnectOptions = {
        mode, host, port, username,
        password: authMethod === 'password' ? password : undefined,
        privateKey: authMethod === 'key' ? privateKey : undefined,
      };
      if (useJumpHost && jumpHost && jumpUsername) {
        payload.jumpHost = jumpHost;
        payload.jumpPort = jumpPort;
        payload.jumpUsername = jumpUsername;
        payload.jumpPassword = jumpAuthMethod === 'password' ? jumpPassword : undefined;
        payload.jumpPrivateKey = jumpAuthMethod === 'key' ? jumpPrivateKey : undefined;
      }
      onConnect(payload);
    }
  };

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPrivateKey(ev.target?.result as string);
    reader.readAsText(file);
  };

  const handleJumpFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setJumpPrivateKey(ev.target?.result as string);
    reader.readAsText(file);
  };

  const sshForm = (
    <Box as="form" onSubmit={handleSubmit}>
      {isSSH && (
        <>
          <Grid templateColumns="1fr 1fr" gap={4}>
            <Box mb={4}>
              <Text {...labelProps}>Hostname</Text>
              <StyledInput {...inputProps} value={host} onChange={(e) => setHost(e.target.value)} placeholder={hostPlaceholder} required />
            </Box>
            <Box mb={4}>
              <Text {...labelProps}>Port</Text>
              <StyledInput {...inputProps} value={port} onChange={(e) => setPort(e.target.value)} placeholder="22" />
            </Box>
          </Grid>

          <Box mb={4}>
            <Text {...labelProps}>Username</Text>
            <StyledInput {...inputProps} value={username} onChange={(e) => setUsername(e.target.value)} placeholder={usernamePlaceholder} required />
          </Box>

          <AuthToggle value={authMethod} onChange={setAuthMethod} />

          {authMethod === 'password' ? (
            <Box mb={4}>
              <Text {...labelProps}>Password</Text>
              <StyledInput {...inputProps} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" />
            </Box>
          ) : (
            <Box mb={4}>
              <Text {...labelProps}>Private Key</Text>
              <Flex direction="column" gap={2.5}>
                <input type="file" onChange={handleFileUpload} accept=".pem,.key,*" />
                <StyledTextarea {...inputProps} fontFamily={fonts.mono} fontSize="0.82rem" resize="vertical" minH="120px" value={privateKey} onChange={(e) => setPrivateKey(e.target.value)} placeholder="Or paste your private key here..." rows={5} />
              </Flex>
            </Box>
          )}
        </>
      )}

      {group === 'das' && dasProfiles.length > 0 && (
        <Box mb={4} p={3} bg={c.bg} border="1px solid" borderColor={c.border} borderRadius={radii.md}>
          <Text {...labelProps} mb={2}>Saved profiles</Text>
          <Flex gap={2} align="center" flexWrap="wrap">
            <select
              value={selectedProfile}
              onChange={(e) => loadProfile(e.target.value)}
              style={{
                flex: 1, minWidth: 0, background: c.surface2, color: c.text,
                border: `1px solid ${c.border}`, borderRadius: 6,
                padding: '6px 10px', fontSize: '0.85rem',
              }}
            >
              <option value="">— select a profile —</option>
              {dasProfiles.map((p) => (
                <option key={p.name} value={p.name} style={{ backgroundColor: c.bg }}>{p.name}</option>
              ))}
            </select>
            {selectedProfile && (
              <Button
                variant="plain" h="auto" py="6px" px={2.5}
                bg="transparent" color={c.error} borderRadius={radii.sm}
                border="1px solid" borderColor={c.border}
                fontSize="0.82rem" fontWeight={500}
                _hover={{ bg: 'rgba(255,82,82,0.08)' }}
                onClick={() => deleteProfile(selectedProfile)}
                title="Delete this profile"
              >
                <Icon as={LuTrash2} boxSize="14px" />
              </Button>
            )}
          </Flex>
        </Box>
      )}

      {group === 'das' && (
        <Box my={4} p={3.5} bg={c.bg} border="1px solid" borderColor={c.border} borderRadius={radii.md}>
          <Flex as="label" align="center" flexWrap="wrap" gap={2} cursor="pointer" fontSize="0.9rem" fontWeight={600} color={c.text}>
            <input
              type="checkbox"
              checked={useJumpHost}
              onChange={(e) => setUseJumpHost(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: c.accent, cursor: 'pointer' }}
            />
            <Text fontWeight={600}>Use Jump Host (ProxyJump)</Text>
            <Text fontSize="0.75rem" fontWeight={400} color={c.textDim} w="100%" ml="26px">
              Required when not on VU campus - tunnels via a gateway
            </Text>
          </Flex>

          {useJumpHost && (
            <Box mt={3.5} pt={3.5} borderTop="1px solid" borderColor={c.border}>
              <Grid templateColumns="1fr 1fr" gap={4}>
                <Box mb={4}>
                  <Text {...labelProps}>Jump Hostname</Text>
                  <StyledInput {...inputProps} value={jumpHost} onChange={(e) => setJumpHost(e.target.value)} placeholder="ssh.data.vu.nl" required />
                </Box>
                <Box mb={4}>
                  <Text {...labelProps}>Jump Port</Text>
                  <StyledInput {...inputProps} value={jumpPort} onChange={(e) => setJumpPort(e.target.value)} placeholder="22" />
                </Box>
              </Grid>

              <Box mb={4}>
                <Text {...labelProps}>Jump Username</Text>
                <StyledInput {...inputProps} value={jumpUsername} onChange={(e) => setJumpUsername(e.target.value)} placeholder="Your VUnet ID (e.g. abc123)" required />
              </Box>

              <AuthToggle value={jumpAuthMethod} onChange={setJumpAuthMethod} />

              {jumpAuthMethod === 'password' ? (
                <Box mb={4}>
                  <Text {...labelProps}>Jump Password</Text>
                  <StyledInput {...inputProps} type="password" value={jumpPassword} onChange={(e) => setJumpPassword(e.target.value)} placeholder="VUnet password" />
                </Box>
              ) : (
                <Box mb={4}>
                  <Text {...labelProps}>Jump Private Key</Text>
                  <Flex direction="column" gap={2.5}>
                    <input type="file" onChange={handleJumpFileUpload} accept=".pem,.key,*" />
                    <StyledTextarea {...inputProps} fontFamily={fonts.mono} fontSize="0.82rem" resize="vertical" minH="100px" value={jumpPrivateKey} onChange={(e) => setJumpPrivateKey(e.target.value)} placeholder="Or paste your private key here..." rows={4} />
                  </Flex>
                </Box>
              )}
            </Box>
          )}
        </Box>
      )}

      <Flex gap={2.5} mt={isLocal ? 0 : 5} align="flex-start" direction="column">
        <Flex gap={2.5} align="center" flexWrap="wrap">
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
            disabled={isRunning || (isSSH && !username) || (isSSH && useJumpHost && !jumpUsername) || (mode === 'aws' && !host)}
          >
            {isRunning ? (
              <>
                <Spinner size="sm" /> {useJumpHost ? 'Connecting via jump host...' : 'Connecting...'}
              </>
            ) : isLocal ? (
              'Start Local Session'
            ) : (
              mode === 'aws' ? `Connect to AWS instance` : `Connect to ${preset.label}`
            )}
          </Button>

          {group === 'das' && !savingProfile && (
            <Button
              type="button"
              variant="plain"
              bg="transparent"
              color={c.textDim}
              border="1px solid"
              borderColor={c.border}
              borderRadius={radii.sm}
              fontSize="0.85rem"
              fontWeight={500}
              px={3.5}
              py="9px"
              h="auto"
              _hover={{ bg: c.surface2, color: c.text }}
              onClick={() => { setSavingProfile(true); setProfileName(''); }}
            >
              <Icon as={LuBookmark} boxSize="14px" mr={1.5} />
              Save profile
            </Button>
          )}
        </Flex>

        {group === 'das' && savingProfile && (
          <Flex gap={2} align="center" mt={1} flexWrap="wrap">
            <StyledInput
              {...inputProps}
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="Profile name (e.g. Campus DAS-5)"
              w="240px"
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); saveProfile(); } if (e.key === 'Escape') setSavingProfile(false); }}
              autoFocus
            />
            <Button
              type="button" variant="plain" bg={c.accent} color="white"
              borderRadius={radii.sm} fontSize="0.85rem" fontWeight={600}
              px={3} py="7px" h="auto" _hover={{ bg: c.accentLight }}
              disabled={!profileName.trim()}
              onClick={saveProfile}
            >
              Save
            </Button>
            <Button
              type="button" variant="plain" bg="transparent" color={c.textDim}
              borderRadius={radii.sm} fontSize="0.85rem" fontWeight={500}
              px={2.5} py="7px" h="auto" border="1px solid" borderColor={c.border}
              _hover={{ bg: c.surface2 }}
              onClick={() => setSavingProfile(false)}
            >
              Cancel
            </Button>
          </Flex>
        )}
      </Flex>
    </Box>
  );

  return (
    <Box {...cardProps}>
      <Heading fontSize="1.15rem" fontWeight={600} mb={1.5}>Connection</Heading>
      <Text color={c.textDim} fontSize="0.9rem" mb={5}>{preset.description}</Text>

      {cloudHint && !cloudContent && (
        <Box mb={5} p={3.5} bg={c.bg} border="1px solid" borderColor={c.border} borderRadius={radii.md}>
          <Heading fontSize="0.92rem" fontWeight={700} mb={2}>{cloudHint.title}</Heading>
          <Flex direction="column" gap={1.5} color={c.textDim} fontSize="0.85rem" lineHeight={1.5}>
            {cloudHint.lines.map((line) => (
              <Text key={line}>• {line}</Text>
            ))}
          </Flex>
        </Box>
      )}

      {!isConnected && (
        <>
          <Grid templateColumns="repeat(4, 1fr)" gap={2.5} mb={subProviders ? 3 : 5}>
            {GROUPS.map((g) => (
              <Button
                key={g.id}
                variant="plain"
                display="flex"
                flexDirection="column"
                alignItems="center"
                gap={1.5}
                py={3.5}
                px={2.5}
                h="auto"
                bg={group === g.id ? 'rgba(108, 92, 231, 0.12)' : c.bg}
                border="2px solid"
                borderColor={group === g.id ? c.accent : c.border}
                borderRadius={radii.md}
                color={group === g.id ? c.accentLight : c.textDim}
                fontSize="0.82rem"
                fontWeight={600}
                _hover={{ bg: c.surface2, borderColor: c.textDim }}
                onClick={() => selectGroup(g.id)}
              >
                <Icon as={g.icon} boxSize="18px" />
                <Text fontSize="0.85rem">{g.label}</Text>
              </Button>
            ))}
          </Grid>

          {subProviders && subProviders.length > 1 && (
            <Grid templateColumns={`repeat(${subProviders.length}, 1fr)`} gap={2} mb={5}>
              {subProviders.map((sp) => {
                const active = mode === sp.mode;
                const Ic = MODE_ICONS[sp.mode];
                return (
                  <Button
                    key={sp.mode}
                    variant="plain"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    gap={2}
                    py={2.5}
                    px={3}
                    h="auto"
                    bg={active ? 'rgba(108, 92, 231, 0.08)' : 'transparent'}
                    border="1px solid"
                    borderColor={active ? c.accent : c.border}
                    borderRadius={radii.sm}
                    color={sp.disabled ? c.textDim : (active ? c.accentLight : c.text)}
                    fontSize="0.85rem"
                    fontWeight={600}
                    opacity={sp.disabled ? 0.6 : 1}
                    cursor={sp.disabled ? 'not-allowed' : 'pointer'}
                    _hover={sp.disabled ? {} : { bg: c.surface2, borderColor: c.textDim }}
                    onClick={() => { if (!sp.disabled) onModeChange(sp.mode); }}
                    title={sp.hint}
                  >
                    {Ic && <Icon as={Ic} boxSize="14px" />}
                    <Text fontSize="0.85rem">{sp.label}</Text>
                    {sp.hint && (
                      <Text as="span" fontSize="0.7rem" color={c.textDim} fontWeight={500} ml={1}>
                        ({sp.hint})
                      </Text>
                    )}
                  </Button>
                );
              })}
            </Grid>
          )}
        </>
      )}

      {isConnected ? (
        <Badge bg="rgba(0, 184, 148, 0.15)" color={c.success} px={2.5} py={1} borderRadius="full" fontSize="0.75rem" fontWeight={600}>
          {isLocal ? 'Local session active' : `Connected to ${host}`}
        </Badge>
      ) : mode === 'aws' && cloudContent ? (
        cloudContent(sshForm)
      ) : (
        sshForm
      )}
    </Box>
  );
}
