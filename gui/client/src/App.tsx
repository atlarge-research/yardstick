import { useState, useCallback } from 'react';
import { Box, Flex, Text, Button } from '@chakra-ui/react';
import { LuPlus, LuX } from 'react-icons/lu';
import SessionPane from './components/SessionPane';
import type { SessionStatus } from './components/SessionPane';
import { c, radii } from './theme';

interface SessionMeta {
  id: string;
  label: string;
  status: SessionStatus;
}

const STATUS_COLOR: Record<SessionStatus, string> = {
  idle:       c.textDim,
  connecting: c.warning,
  connected:  c.success,
  running:    c.accentLight,
  done:       c.success,
  error:      c.error,
};

function newSession(n: number): SessionMeta {
  return { id: crypto.randomUUID(), label: `Session ${n}`, status: 'idle' };
}

export default function App() {
  const [sessions, setSessions] = useState<SessionMeta[]>([newSession(1)]);
  const [activeId, setActiveId] = useState<string>(sessions[0].id);

  const addSession = () => {
    if (sessions.length >= 8) return;
    const s = newSession(sessions.length + 1);
    setSessions((prev) => [...prev, s]);
    setActiveId(s.id);
  };

  const removeSession = (id: string) => {
    setSessions((prev) => {
      if (prev.length === 1) {
        // Reset the last session instead of removing it
        return [newSession(1)];
      }
      const next = prev.filter((s) => s.id !== id);
      if (id === activeId) {
        const idx = prev.findIndex((s) => s.id === id);
        setActiveId(next[Math.max(0, idx - 1)].id);
      }
      return next;
    });
  };

  const updateStatus = useCallback((id: string, status: SessionStatus) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, status } : s)));
  }, []);

  const updateLabel = useCallback((id: string, label: string) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, label } : s)));
  }, []);

  return (
    <Flex direction="column" minH="100vh" bg={c.bg}>
      {/* Session tab bar */}
      <Flex
        align="center"
        gap={1}
        px={3}
        py="6px"
        bg={c.surface}
        borderBottom="1px solid"
        borderColor={c.border}
        flexWrap="nowrap"
        overflowX="auto"
      >
        {sessions.map((s) => {
          const isActive = s.id === activeId;
          const dotColor = STATUS_COLOR[s.status];
          const pulsing = s.status === 'connecting' || s.status === 'running';
          return (
            <Flex
              key={s.id}
              align="center"
              gap={1.5}
              px={3}
              py="5px"
              borderRadius={radii.sm}
              border="1px solid"
              borderColor={isActive ? c.accent : c.border}
              bg={isActive ? c.surface2 : 'transparent'}
              cursor="pointer"
              flexShrink={0}
              onClick={() => setActiveId(s.id)}
              _hover={!isActive ? { bg: c.surface2, borderColor: c.textDim } : {}}
            >
              <Box
                w="7px"
                h="7px"
                borderRadius="full"
                flexShrink={0}
                bg={dotColor}
                style={pulsing ? { animation: 'pulse 1.5s infinite' } : undefined}
              />
              <Text fontSize="0.78rem" fontWeight={isActive ? 600 : 400} color={isActive ? c.text : c.textDim} userSelect="none">
                {s.label}
              </Text>
              <Button
                variant="plain"
                p={0}
                h="auto"
                minW="auto"
                color={c.textDim}
                fontSize="0.7rem"
                _hover={{ color: c.error }}
                onClick={(e) => { e.stopPropagation(); removeSession(s.id); }}
                aria-label="Close session"
              >
                <LuX size={11} />
              </Button>
            </Flex>
          );
        })}

        {sessions.length < 8 && (
          <Button
            variant="plain"
            p={0}
            h="28px"
            w="28px"
            minW="28px"
            borderRadius={radii.sm}
            border="1px solid"
            borderColor={c.border}
            color={c.textDim}
            _hover={{ bg: c.surface2, color: c.text, borderColor: c.textDim }}
            onClick={addSession}
            aria-label="New session"
            flexShrink={0}
          >
            <LuPlus size={13} />
          </Button>
        )}
      </Flex>

      {/* Session panes — all mounted, only active one visible */}
      <Flex flex={1} direction="column" overflow="hidden" position="relative">
        {sessions.map((s) => (
          <Box
            key={s.id}
            display={s.id === activeId ? 'flex' : 'none'}
            flexDirection="column"
            flex="1"
            overflow="hidden"
          >
            <SessionPane
              onStatusChange={(status) => updateStatus(s.id, status)}
              onLabelChange={(label) => updateLabel(s.id, label)}
            />
          </Box>
        ))}
      </Flex>
    </Flex>
  );
}
