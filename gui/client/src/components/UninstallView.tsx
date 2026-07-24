import { useState } from 'react';
import { Box, Flex, Text, Heading, Button, Icon, Spinner } from '@chakra-ui/react';
import { LuTrash2, LuTriangleAlert, LuCheck } from 'react-icons/lu';
import Terminal from './Terminal';
import type { TerminalOutputMap } from '../hooks/useJoystick';
import { c, radii, cardProps, inputProps, StyledInput } from '../theme';

interface UninstallViewProps {
  connected: boolean;
  username: string;
  mode: string;
  terminalOutput: TerminalOutputMap;
  uninstallRunning: boolean;
  uninstallDone: boolean;
  uninstallError: string | null;
  uninstallPreview: string | null;
  uninstallPreviewing: boolean;
  onPreview: (opts: { username: string; purge: boolean; nvm: boolean }) => void;
  onUninstall: (opts: { username: string; purge: boolean; nvm: boolean }) => void;
}

const REMOVED_ITEMS = [
  "The 'yardstick' conda environment, and the Miniconda that hosts it if setup installed it",
  'The conda initialize block in ~/.bashrc',
  'Per-run working directories (~/yardstick/run)',
  'Local-mode Docker containers and the yardstick-node image',
  'Leftover PaperMC, Telegraf and bot processes',
];

const KEPT_ITEMS = [
  'Experiment results in ~/experiments, unless you tick the option below',
  'System packages shared with the rest of the machine (java, node, rsync, wget, git)',
  'A Miniconda that already held other conda environments before setup ran',
];

function CheckRow({
  checked, onChange, label, help, disabled, danger,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  help: string;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <Flex
      as="label"
      align="flex-start"
      gap={3}
      px={3.5}
      py={3}
      border="1px solid"
      borderColor={checked && danger ? c.error : c.border}
      borderRadius={radii.sm}
      bg={checked && danger ? 'rgba(225,112,85,0.06)' : 'transparent'}
      cursor={disabled ? 'not-allowed' : 'pointer'}
      opacity={disabled ? 0.6 : 1}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
        style={{ width: 16, height: 16, marginTop: 2, accentColor: danger ? c.error : c.accent }}
      />
      <Box>
        <Text fontSize="0.88rem" fontWeight={600} color={c.text}>{label}</Text>
        <Text fontSize="0.8rem" color={c.textDim}>{help}</Text>
      </Box>
    </Flex>
  );
}

export default function UninstallView({
  connected, username, mode, terminalOutput,
  uninstallRunning, uninstallDone, uninstallError, uninstallPreview, uninstallPreviewing,
  onPreview, onUninstall,
}: UninstallViewProps) {
  const [purge, setPurge] = useState(false);
  const [nvm, setNvm] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const modeLabel = ({ local: 'this machine', das5: 'DAS-5', das6: 'DAS-6', aws: 'the AWS instance', custom: 'the remote host' } as Record<string, string>)[mode] || 'the connected host';
  const opts = { username, purge, nvm };
  const busy = uninstallRunning || uninstallPreviewing;
  const confirmed = confirmText.trim().toUpperCase() === 'UNINSTALL';

  if (uninstallDone) {
    return (
      <Box>
        <Box {...cardProps} borderColor={c.success}>
          <Flex align="center" gap={2} mb={2}>
            <Icon as={LuCheck} boxSize="18px" color={c.success} />
            <Heading fontSize="1.15rem" fontWeight={600} color={c.success}>Uninstall Complete</Heading>
          </Flex>
          <Text color={c.textDim} fontSize="0.9rem">
            Yardstick has been removed from {modeLabel}. The <Text as="strong">Setup</Text> tab can reinstall it at any time.
            {purge && ' The Joystick app itself is not removed by this: uninstall the desktop app through your package manager.'}
          </Text>
        </Box>
        {terminalOutput['uninstall'] && <Terminal lines={terminalOutput['uninstall']} title="Uninstall" />}
      </Box>
    );
  }

  return (
    <Box>
      <Box {...cardProps}>
        <Flex align="center" gap={2} mb={1.5}>
          <Icon as={LuTrash2} boxSize="18px" />
          <Heading fontSize="1.15rem" fontWeight={600}>Uninstall Yardstick</Heading>
        </Flex>
        <Text color={c.textDim} fontSize="0.9rem" mb={5}>
          Removes everything the Setup tab installed on {modeLabel}. Runs on the host you are connected to right now.
        </Text>

        <Flex gap={5} direction={{ base: 'column', md: 'row' }} mb={5}>
          <Box flex={1}>
            <Text fontSize="0.78rem" fontWeight={700} color={c.textDim} textTransform="uppercase" letterSpacing="0.04em" mb={2}>
              Will be removed
            </Text>
            {REMOVED_ITEMS.map((item) => (
              <Flex key={item} gap={2} mb={1.5} align="flex-start">
                <Text color={c.error} fontSize="0.85rem" lineHeight={1.6}>-</Text>
                <Text color={c.text} fontSize="0.85rem" lineHeight={1.6}>{item}</Text>
              </Flex>
            ))}
          </Box>
          <Box flex={1}>
            <Text fontSize="0.78rem" fontWeight={700} color={c.textDim} textTransform="uppercase" letterSpacing="0.04em" mb={2}>
              Will be kept
            </Text>
            {KEPT_ITEMS.map((item) => (
              <Flex key={item} gap={2} mb={1.5} align="flex-start">
                <Text color={c.success} fontSize="0.85rem" lineHeight={1.6}>+</Text>
                <Text color={c.text} fontSize="0.85rem" lineHeight={1.6}>{item}</Text>
              </Flex>
            ))}
          </Box>
        </Flex>

        <Flex direction="column" gap={2.5} mb={5}>
          <CheckRow
            checked={purge}
            onChange={setPurge}
            disabled={busy}
            danger
            label="Also delete experiment results"
            help="Removes ~/experiments with every run it holds, the saved AWS key ~/.ssh/yardstick_exp.pem, the swapfile setup created, and the app's saved connection profiles. This cannot be undone."
          />
          <CheckRow
            checked={nvm}
            onChange={setNvm}
            disabled={busy}
            label="Remove ~/.nvm"
            help="Node installed for the bot workload. Skip this if you had nvm on this host before using Yardstick."
          />
        </Flex>

        {uninstallError && (
          <Box {...cardProps} borderColor={c.error} p={4} mb={4}>
            <Text color={c.error} fontSize="0.88rem" whiteSpace="pre-wrap">{uninstallError}</Text>
          </Box>
        )}

        <Flex gap={2.5} align="center" wrap="wrap">
          <Button
            variant="plain"
            bg="transparent"
            border="1px solid"
            borderColor={c.border}
            color={c.text}
            borderRadius={radii.sm}
            fontSize="0.9rem"
            fontWeight={600}
            px={5}
            py="10px"
            h="auto"
            _hover={{ bg: c.surface2 }}
            _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
            onClick={() => onPreview(opts)}
            disabled={!connected || busy}
          >
            {uninstallPreviewing ? <><Spinner size="xs" mr={2} /> Checking...</> : 'Preview what will be removed'}
          </Button>
        </Flex>
      </Box>

      {uninstallPreview !== null && !uninstallRunning && (
        <Box {...cardProps}>
          <Heading fontSize="1rem" fontWeight={600} mb={3}>Preview</Heading>
          <Terminal lines={uninstallPreview} title="Dry run - nothing was changed" />
        </Box>
      )}

      <Box {...cardProps} borderColor={c.error}>
        <Flex align="center" gap={2} mb={1.5}>
          <Icon as={LuTriangleAlert} boxSize="18px" color={c.error} />
          <Heading fontSize="1rem" fontWeight={600} color={c.error}>Confirm</Heading>
        </Flex>
        <Text color={c.textDim} fontSize="0.88rem" mb={3}>
          Type <Text as="strong" color={c.text}>UNINSTALL</Text> to enable the button.
          {purge && ' Experiment results will be deleted along with the installation.'}
        </Text>
        <Flex gap={2.5} align="center" wrap="wrap">
          <StyledInput
            {...inputProps}
            w="200px"
            placeholder="UNINSTALL"
            value={confirmText}
            disabled={busy}
            onChange={(e) => setConfirmText(e.target.value)}
          />
          <Button
            variant="plain"
            bg={c.error}
            color="white"
            borderRadius={radii.sm}
            fontSize="0.9rem"
            fontWeight={600}
            px={5}
            py="10px"
            h="auto"
            _hover={{ filter: 'brightness(1.1)' }}
            _disabled={{ opacity: 0.5, cursor: 'not-allowed' }}
            onClick={() => onUninstall(opts)}
            disabled={!connected || busy || !confirmed}
          >
            {uninstallRunning ? <><Spinner size="xs" mr={2} /> Uninstalling...</> : 'Uninstall Yardstick'}
          </Button>
        </Flex>
      </Box>

      {terminalOutput['uninstall'] && <Terminal lines={terminalOutput['uninstall']} title="Uninstall" />}
    </Box>
  );
}
