import { chakra } from '@chakra-ui/react';

export const c = {
  bg: '#0f1117',
  surface: '#1a1d27',
  surface2: '#232734',
  border: '#2e3348',
  text: '#e2e4ed',
  textDim: '#8b8fa3',
  accent: '#6c5ce7',
  accentLight: '#a29bfe',
  success: '#00b894',
  error: '#e17055',
  warning: '#fdcb6e',
  info: '#74b9ff',
} as const;

export const fonts = {
  sans: "'Inter', system-ui, -apple-system, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const radii = { md: '10px', sm: '6px' } as const;

export const cardProps = {
  bg: c.surface,
  border: '1px solid',
  borderColor: c.border,
  borderRadius: radii.md,
  p: 6,
  mb: 5,
} as const;

export const inputProps = {
  w: '100%',
  px: 3.5,
  py: 2.5,
  bg: c.bg,
  border: '1px solid',
  borderColor: c.border,
  borderRadius: radii.sm,
  color: c.text,
  fontSize: '0.92rem',
  fontFamily: fonts.sans,
  transition: 'border-color 0.15s',
  _focus: { outline: 'none', borderColor: c.accent },
  _placeholder: { color: c.textDim },
  _disabled: { opacity: 0.6 },
} as const;

export const labelProps = {
  as: 'label' as const,
  display: 'block',
  fontSize: '0.82rem',
  fontWeight: 600,
  mb: 1.5,
  color: c.textDim,
  textTransform: 'uppercase' as const,
  letterSpacing: '0.04em',
};

export const StyledInput = chakra('input');
export const StyledTextarea = chakra('textarea');
export const StyledSelect = chakra('select');
