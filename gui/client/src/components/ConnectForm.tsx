import { useState, useEffect, type FormEvent, type ChangeEvent } from 'react';
import { Box, Flex, Grid, Text, Heading, Button, Badge, Icon, Spinner } from '@chakra-ui/react';
import { LuMonitor, LuGlobe, LuHash, LuServer, LuCloud } from 'react-icons/lu';
import type { IconType } from 'react-icons';
import type { SshConnectOptions, StepStatus } from '../hooks/useYardstick';
import { c, fonts, radii, cardProps, inputProps, labelProps, StyledInput, StyledTextarea } from '../theme';

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
  azure: LuCloud,
  custom: LuGlobe,
};

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
  azure: {
    host: '',
    port: '22',
    label: 'Azure VM',
    description: 'Connect to an Azure virtual machine over SSH using the public IP or DNS name from the portal.',
    defaultJump: false,
    preferredAuthMethod: 'key',
    hostPlaceholder: 'your-vm.westus.cloudapp.azure.com',
    usernamePlaceholder: 'azureuser',
  },
  custom: { host: '', port: '22', label: 'Custom SSH', description: 'Connect to any remote host via SSH.', defaultJump: false },
};

type AuthMethod = 'password' | 'key';

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
}

export default function ConnectForm({ onConnect, status, mode, onModeChange }: ConnectFormProps) {
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

  const isRunning = status === 'running';
  const isConnected = status === 'completed';
  const isLocal = mode === 'local';
  const isSSH = !isLocal;
  const preset = MODE_PRESETS[mode] || MODE_PRESETS.das5;
  const hostPlaceholder = preset.hostPlaceholder || 'hostname';
  const usernamePlaceholder = preset.usernamePlaceholder || `Your ${preset.label} username`;
  const cloudHint = mode === 'aws'
    ? {
        title: 'AWS EC2 quick setup',
        lines: [
          'Use the instance public DNS or Elastic IP as the hostname.',
          'Make sure port 22 is allowed in the security group.',
          'SSH key authentication is recommended for EC2 images.',
        ],
      }
    : mode === 'azure'
      ? {
          title: 'Azure VM quick setup',
          lines: [
            'Use the VM public IP or DNS name from the Azure portal.',
            'Allow inbound SSH on port 22 in the network security group.',
            'Key-based SSH login is the safest option for Azure VMs.',
          ],
        }
      : null;

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

  return (
    <Box {...cardProps}>
      <Heading fontSize="1.15rem" fontWeight={600} mb={1.5}>Connection</Heading>
      <Text color={c.textDim} fontSize="0.9rem" mb={5}>{preset.description}</Text>

      {cloudHint && (
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
        <Grid templateColumns={{ base: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }} gap={2.5} mb={5}>
          {Object.entries(MODE_PRESETS).map(([key, val]) => (
            <Button
              key={key}
              variant="plain"
              display="flex"
              flexDirection="column"
              alignItems="center"
              gap={1.5}
              py={3.5}
              px={2.5}
              h="auto"
              bg={mode === key ? 'rgba(108, 92, 231, 0.12)' : c.bg}
              border="2px solid"
              borderColor={mode === key ? c.accent : c.border}
              borderRadius={radii.md}
              color={mode === key ? c.accentLight : c.textDim}
              fontSize="0.82rem"
              fontWeight={600}
              _hover={{ bg: c.surface2, borderColor: c.textDim }}
              onClick={() => onModeChange(key)}
            >
              <Flex align="center" justify="center" fontSize="1.1rem" fontWeight={700}>
                {key === 'das5' ? '5' : key === 'das6' ? '6' : (() => { const Ic = MODE_ICONS[key]; return Ic ? <Icon as={Ic} boxSize="16px" /> : null; })()}
              </Flex>
              <Text fontSize="0.8rem">{val.label}</Text>
            </Button>
          ))}
        </Grid>
      )}

      {isConnected ? (
        <Badge bg="rgba(0, 184, 148, 0.15)" color={c.success} px={2.5} py={1} borderRadius="full" fontSize="0.75rem" fontWeight={600}>
          {isLocal ? 'Local session active' : `Connected to ${host}`}
        </Badge>
      ) : (
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

          {isSSH && (
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

          <Flex gap={2.5} mt={5}>
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
              disabled={isRunning || (isSSH && !username) || (isSSH && useJumpHost && !jumpUsername)}
            >
              {isRunning ? (
                <>
                  <Spinner size="sm" /> {useJumpHost ? 'Connecting via jump host...' : 'Connecting...'}
                </>
              ) : isLocal ? (
                'Start Local Session'
              ) : (
                `Connect to ${preset.label}`
              )}
            </Button>
          </Flex>
        </Box>
      )}
    </Box>
  );
}
