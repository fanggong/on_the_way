export type SystemCode =
  | 'health'
  | 'time'
  | 'income'
  | 'finance'
  | 'ability'
  | 'relationship'
  | 'life'
  | 'security';

export const SYSTEMS: Array<{ code: SystemCode; label: string; path: string }> = [
  { code: 'health', label: '健康', path: '/app/health/overview' },
  { code: 'time', label: '时间', path: '/app/time' },
  { code: 'income', label: '收入', path: '/app/income' },
  { code: 'finance', label: '财务', path: '/app/finance' },
  { code: 'ability', label: '能力', path: '/app/ability' },
  { code: 'relationship', label: '关系', path: '/app/relationship' },
  { code: 'life', label: '生活', path: '/app/life' },
  { code: 'security', label: '保障', path: '/app/security' },
];
