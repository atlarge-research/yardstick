import { useRef, useEffect } from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { c, fonts, radii } from '../theme';

interface TerminalProps {
  lines?: string;
  title?: string;
}

export default function Terminal({ lines = '', title = 'Terminal' }: TerminalProps) {
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [lines]);

  const parsed = typeof lines === 'string' ? lines : '';

  return (
    <Box bg="#0a0c10" border="1px solid" borderColor={c.border} borderRadius={radii.md} overflow="hidden">
      <Flex align="center" gap={2} px={4} py={2.5} bg={c.surface2} borderBottom="1px solid" borderBottomColor={c.border} fontSize="0.8rem" color={c.textDim} fontFamily={fonts.mono}>
        <Box w="10px" h="10px" borderRadius="full" bg={c.error} />
        <Box w="10px" h="10px" borderRadius="full" bg={c.warning} />
        <Box w="10px" h="10px" borderRadius="full" bg={c.success} />
        <Text fontSize="0.8rem">{title}</Text>
      </Flex>
      <Box ref={bodyRef} p={4} fontFamily={fonts.mono} fontSize="0.82rem" lineHeight={1.7} maxH="400px" overflowY="auto" whiteSpace="pre-wrap" wordBreak="break-all">
        {parsed.length === 0 ? (
          <Text color={c.textDim}>No output.</Text>
        ) : (
          parsed.split('\n').map((line, i) => {
            const color = line.startsWith('$')
              ? c.accentLight
              : (line.startsWith('[OK]') || line.toLowerCase().includes('success'))
                ? c.success
                : (line.startsWith('[FAIL]') || line.toLowerCase().includes('error'))
                  ? c.error
                  : c.text;
            return <Box key={i} color={color}>{line}</Box>;
          })
        )}
      </Box>
    </Box>
  );
}
