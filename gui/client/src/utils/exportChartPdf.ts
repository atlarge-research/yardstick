import { jsPDF } from 'jspdf';
import 'svg2pdf.js';

export interface LegendEntry {
  label: string;
  color: string;
}

export type ExportTheme = 'dark' | 'light';

export interface ExportChartPdfOptions {
  container: HTMLElement;
  title: string;
  subtitle?: string;
  legend?: LegendEntry[];
  theme: ExportTheme;
  fileName: string;
}

// Light-mode replacements for every color the charts use, validated for
// lightness, chroma, CVD separation, and >= 3:1 contrast on white. Same hue
// per slot as the dark palette so exported charts stay recognizable.
const LIGHT_COLOR_MAP: Record<string, string> = {
  // Series palette (NODE_COLORS order)
  '#6c5ce7': '#5b4bd1',
  '#00b894': '#00916f',
  '#e17055': '#d1543a',
  '#74b9ff': '#2e7dd1',
  '#fdcb6e': '#b7791f',
  '#a29bfe': '#8a7ae8',
  '#55efc4': '#0ca678',
  '#fab1a0': '#9e4a32',
  '#81ecec': '#0e9aa7',
  '#ffeaa7': '#a8871a',
  '#dfe6e9': '#3d4451', // box-plot median/cap lines must stay visible on white
  '#fd79a8': '#d6336c',
  // Fixed accents
  '#0984e3': '#0670c2', // server highlight
  '#b2bec3': '#7a828e', // box-plot whisker stems
  // Structural theme colors
  '#2e3348': '#d5d9e0', // c.border: grid and axis strokes
  '#8b8fa3': '#495062', // c.textDim: tick text and axis labels
};

const DARK_BG = '#1a1d27'; // c.surface, so the export matches the on-screen card
const LIGHT_BG = '#ffffff';

const INK = {
  dark: { title: '#e2e4ed', subtitle: '#8b8fa3' },
  light: { title: '#1a1d27', subtitle: '#495062' },
};

const PAGE_MARGIN = 24;
const TITLE_SIZE = 13;
const SUBTITLE_SIZE = 9;
const LEGEND_SIZE = 9;
const LEGEND_SWATCH = 8;
const LEGEND_ROW_H = 16;
const LEGEND_GAP = 18;

function mapColor(value: string, theme: ExportTheme): string {
  if (theme === 'dark') return value;
  return LIGHT_COLOR_MAP[value.trim().toLowerCase()] ?? value;
}

function remapSvgColors(root: SVGElement, theme: ExportTheme) {
  if (theme === 'dark') return;
  const elements = [root, ...Array.from(root.querySelectorAll<SVGElement>('*'))];
  for (const el of elements) {
    for (const attr of ['stroke', 'fill'] as const) {
      const value = el.getAttribute(attr);
      if (value) el.setAttribute(attr, mapColor(value, theme));
      const styleValue = el.style?.[attr];
      if (styleValue) el.style[attr] = mapColor(styleValue, theme);
    }
  }
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

// Rows of "swatch + label" entries, wrapped to the available width.
function drawLegend(
  doc: jsPDF,
  legend: LegendEntry[],
  theme: ExportTheme,
  x: number,
  y: number,
  maxWidth: number,
): void {
  doc.setFontSize(LEGEND_SIZE);
  doc.setFont('helvetica', 'normal');
  let cx = x;
  let cy = y;
  for (const entry of legend) {
    const labelWidth = doc.getTextWidth(entry.label);
    const entryWidth = LEGEND_SWATCH + 5 + labelWidth;
    if (cx + entryWidth > x + maxWidth && cx > x) {
      cx = x;
      cy += LEGEND_ROW_H;
    }
    doc.setFillColor(...hexToRgb(mapColor(entry.color, theme)));
    doc.rect(cx, cy - LEGEND_SWATCH + 1, LEGEND_SWATCH, LEGEND_SWATCH, 'F');
    doc.setTextColor(...hexToRgb(INK[theme].title));
    doc.text(entry.label, cx + LEGEND_SWATCH + 5, cy);
    cx += entryWidth + LEGEND_GAP;
  }
}

function legendHeight(doc: jsPDF, legend: LegendEntry[], x: number, maxWidth: number): number {
  doc.setFontSize(LEGEND_SIZE);
  doc.setFont('helvetica', 'normal');
  let cx = x;
  let rows = 1;
  for (const entry of legend) {
    const entryWidth = LEGEND_SWATCH + 5 + doc.getTextWidth(entry.label);
    if (cx + entryWidth > x + maxWidth && cx > x) {
      cx = x;
      rows += 1;
    }
    cx += entryWidth + LEGEND_GAP;
  }
  return rows * LEGEND_ROW_H;
}

export async function exportChartPdf({
  container,
  title,
  subtitle,
  legend,
  theme,
  fileName,
}: ExportChartPdfOptions): Promise<void> {
  // The wrapper also contains small legend-icon SVGs, so take the main chart
  // surface: the direct child of the wrapper, falling back to the largest SVG.
  const svg = container.querySelector<SVGSVGElement>('.recharts-wrapper > svg.recharts-surface')
    ?? Array.from(container.querySelectorAll<SVGSVGElement>('svg'))
      .sort((a, b) => {
        const ra = a.getBoundingClientRect();
        const rb = b.getBoundingClientRect();
        return rb.width * rb.height - ra.width * ra.height;
      })[0];
  if (!svg) throw new Error('No chart SVG found to export');

  const rect = svg.getBoundingClientRect();
  const width = Math.max(1, Math.round(rect.width));
  const height = Math.max(1, Math.round(rect.height));

  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute('width', String(width));
  clone.setAttribute('height', String(height));
  // Text nodes without an explicit font-family would fall back to Times in
  // the PDF; inherit a sans font matching the on-screen look instead.
  clone.setAttribute('font-family', 'Helvetica, Arial, sans-serif');
  remapSvgColors(clone, theme);

  const titleBlock = PAGE_MARGIN + TITLE_SIZE + (subtitle ? SUBTITLE_SIZE + 6 : 0) + 10;

  // Measure with a throwaway doc so the real page can be sized exactly.
  const probe = new jsPDF({ unit: 'pt', format: [10, 10] });
  const legendH = legend && legend.length > 0
    ? legendHeight(probe, legend, PAGE_MARGIN, width - PAGE_MARGIN)
    : 0;

  const pageW = width + 2 * PAGE_MARGIN;
  const pageH = titleBlock + height + legendH + PAGE_MARGIN;

  const doc = new jsPDF({
    unit: 'pt',
    format: [pageW, pageH],
    orientation: pageW >= pageH ? 'landscape' : 'portrait',
  });

  doc.setFillColor(...hexToRgb(theme === 'light' ? LIGHT_BG : DARK_BG));
  doc.rect(0, 0, pageW, pageH, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(TITLE_SIZE);
  doc.setTextColor(...hexToRgb(INK[theme].title));
  doc.text(title, PAGE_MARGIN, PAGE_MARGIN + TITLE_SIZE - 2);

  if (subtitle) {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(SUBTITLE_SIZE);
    doc.setTextColor(...hexToRgb(INK[theme].subtitle));
    doc.text(subtitle, PAGE_MARGIN, PAGE_MARGIN + TITLE_SIZE + SUBTITLE_SIZE + 2, {
      maxWidth: pageW - 2 * PAGE_MARGIN,
    });
  }

  await doc.svg(clone, { x: PAGE_MARGIN, y: titleBlock, width, height });

  if (legend && legend.length > 0) {
    drawLegend(doc, legend, theme, PAGE_MARGIN, titleBlock + height + LEGEND_ROW_H - 4, width - PAGE_MARGIN);
  }

  doc.save(fileName);
}

export function exportFileName(runId: string, exportName: string, theme: ExportTheme): string {
  const safeRun = (runId || 'run').replace(/[^\w.-]+/g, '_');
  return `${safeRun}-${exportName}-${theme}.pdf`;
}
