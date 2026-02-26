export type ThemeKey =
  | 'health'
  | 'time'
  | 'income'
  | 'finance'
  | 'capability'
  | 'relationship'
  | 'lifestyle'
  | 'security';

export type ThemeDefinition = {
  key: ThemeKey;
  title: string;
  description: string;
  statusText: string;
};

export const DEFAULT_THEME_KEY: ThemeKey = 'health';

export const HOME_THEMES: ThemeDefinition[] = [
  {
    key: 'health',
    title: '健康',
    description: '身体状态与恢复',
    statusText: '即将开放',
  },
  {
    key: 'time',
    title: '时间',
    description: '时间分配与节奏',
    statusText: '即将开放',
  },
  {
    key: 'income',
    title: '收入',
    description: '机会与转化过程',
    statusText: '即将开放',
  },
  {
    key: 'finance',
    title: '财务',
    description: '收支与资产结构',
    statusText: '即将开放',
  },
  {
    key: 'capability',
    title: '能力',
    description: '学习与可复用资产',
    statusText: '即将开放',
  },
  {
    key: 'relationship',
    title: '关系',
    description: '人际网络与协作',
    statusText: '即将开放',
  },
  {
    key: 'lifestyle',
    title: '生活',
    description: '日常运行与后勤',
    statusText: '即将开放',
  },
  {
    key: 'security',
    title: '保障',
    description: '风险与底线保护',
    statusText: '即将开放',
  },
];
