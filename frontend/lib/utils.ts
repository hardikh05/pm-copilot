import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(n: number) {
  return `${Math.round(n * 100)}%`;
}

export function formatNumber(n: number) {
  return new Intl.NumberFormat('en-US').format(n);
}

export function sentimentColor(s: string | null | undefined) {
  if (s === 'positive') return 'text-good';
  if (s === 'negative') return 'text-bad';
  return 'text-muted';
}

export function bucketColor(b: string | null | undefined) {
  if (b === 'quick_win') return 'text-good border-good/40 bg-good/10';
  if (b === 'bet') return 'text-accent border-accent/40 bg-accent/10';
  if (b === 'risk') return 'text-warn border-warn/40 bg-warn/10';
  return 'text-muted';
}

export function bucketLabel(b: string | null | undefined) {
  if (b === 'quick_win') return 'Quick Win';
  if (b === 'bet') return 'Bet';
  if (b === 'risk') return 'Risk';
  return '—';
}
