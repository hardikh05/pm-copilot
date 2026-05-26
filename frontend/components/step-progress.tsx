import Link from 'next/link';
import { Check, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

type Step = { key: string; label: string; href?: string; done: boolean };

export default function StepProgress({ steps, currentKey }: { steps: Step[]; currentKey?: string }) {
  return (
    <ol className="grid grid-cols-1 md:grid-cols-6 gap-2">
      {steps.map((s, i) => {
        const active = s.key === currentKey;
        const content = (
          <div
            className={cn(
              'card p-3 text-sm flex items-center gap-3 transition-colors',
              s.done && 'border-good/40 bg-good/5',
              active && 'border-accent/60'
            )}
          >
            {s.done ? (
              <Check className="w-4 h-4 text-good shrink-0" />
            ) : (
              <Circle className={cn('w-4 h-4 shrink-0', active ? 'text-accent' : 'text-muted')} />
            )}
            <span className="space-y-0.5">
              <span className="block label">Step {i + 1}</span>
              <span className="block font-medium">{s.label}</span>
            </span>
          </div>
        );
        return (
          <li key={s.key}>{s.href ? <Link href={s.href}>{content}</Link> : content}</li>
        );
      })}
    </ol>
  );
}
