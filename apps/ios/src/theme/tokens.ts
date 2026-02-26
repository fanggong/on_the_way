export const tokens = {
  color: {
    bgCanvas: '#F6F3ED',
    bgSurface: '#EFE8DC',
    bgCard: '#FBF9F4',
    textPrimary: '#2F2A24',
    textSecondary: '#6B645A',
    borderDefault: '#D8D0C4',
    accentSoft: '#8A7E70',
    stateDisabled: '#B8B1A7',
  },
  spacing: {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 20,
    xl: 24,
  },
  radius: {
    card: 12,
    pill: 999,
  },
  typography: {
    h1: 28,
    h2: 20,
    body: 16,
    caption: 13,
    lineHeightH1: 34,
    lineHeightH2: 26,
    lineHeightBody: 24,
    lineHeightCaption: 18,
  },
  motion: {
    fast: 160,
    standard: 200,
  },
} as const;
