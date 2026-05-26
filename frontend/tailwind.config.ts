import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0b0d12',
        panel: '#11141b',
        panel2: '#161a23',
        border: '#1f2430',
        muted: '#8b93a6',
        text: '#e7ecf3',
        accent: '#7c9cff',
        accent2: '#5dd6c4',
        warn: '#f0b75b',
        bad: '#ef6b78',
        good: '#5fd47e',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
