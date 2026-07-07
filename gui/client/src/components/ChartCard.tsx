import { useRef, useState, type ReactNode } from 'react';
import { Box, Flex, Text, Heading, Button, Icon } from '@chakra-ui/react';
import { LuFileDown, LuLoader } from 'react-icons/lu';
import { c, radii, cardProps } from '../theme';
import { exportChartPdf, exportFileName, type ExportTheme, type LegendEntry } from '../utils/exportChartPdf';

interface ChartCardProps {
  title: string;
  subtitle: string;
  exportName: string;
  runId: string;
  legend?: LegendEntry[];
  children: ReactNode;
}

// Card wrapper for a single results chart: heading, dim subtitle, and an
// export dropdown that saves the chart as a vector PDF in the current dark
// look or a light (white background) variant.
export default function ChartCard({ title, subtitle, exportName, runId, legend, children }: ChartCardProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDetailsElement>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const doExport = async (theme: ExportTheme) => {
    menuRef.current?.removeAttribute('open');
    if (!chartRef.current || exporting) return;
    setExporting(true);
    setExportError(null);
    try {
      await exportChartPdf({
        container: chartRef.current,
        title,
        subtitle,
        legend,
        theme,
        fileName: exportFileName(runId, exportName, theme),
      });
    } catch (err) {
      setExportError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(false);
    }
  };

  const optionProps = {
    variant: 'plain' as const,
    w: '100%',
    justifyContent: 'flex-start' as const,
    h: 'auto',
    px: 3,
    py: 1.5,
    borderRadius: radii.sm,
    fontSize: '0.82rem',
    fontWeight: 600,
    color: c.text,
    bg: 'transparent',
    _hover: { bg: c.surface2 },
    disabled: exporting,
  };

  return (
    <Box {...cardProps} pb={6}>
      <Flex justify="space-between" align="flex-start" gap={3} mb={3}>
        <Box>
          <Heading fontSize="1rem" fontWeight={600} mb={0.5}>{title}</Heading>
          <Text color={c.textDim} fontSize="0.8rem">{subtitle}</Text>
        </Box>
        <Box as="details" ref={menuRef} position="relative" flexShrink={0}>
          <Flex
            as="summary"
            align="center"
            gap={1.5}
            px={3}
            py={1.5}
            border="1px solid"
            borderColor={c.border}
            borderRadius={radii.sm}
            color={c.textDim}
            fontSize="0.82rem"
            fontWeight={600}
            cursor="pointer"
            userSelect="none"
            listStyleType="none"
            css={{ '&::-webkit-details-marker': { display: 'none' } }}
            _hover={{ bg: c.surface2, color: c.text }}
          >
            <Icon as={exporting ? LuLoader : LuFileDown} boxSize="13px" className={exporting ? 'spin' : undefined} />
            Export
          </Flex>
          <Box
            position="absolute"
            right={0}
            mt={1}
            zIndex={10}
            minW="140px"
            bg={c.surface2}
            border="1px solid"
            borderColor={c.border}
            borderRadius={radii.sm}
            p={1}
            boxShadow="0 8px 24px rgba(0, 0, 0, 0.4)"
          >
            <Button {...optionProps} onClick={() => doExport('dark')}>PDF (dark)</Button>
            <Button {...optionProps} onClick={() => doExport('light')}>PDF (light)</Button>
          </Box>
        </Box>
      </Flex>
      {exportError && (
        <Text color={c.error} fontSize="0.8rem" mb={2}>Export failed: {exportError}</Text>
      )}
      <Box ref={chartRef}>{children}</Box>
    </Box>
  );
}
