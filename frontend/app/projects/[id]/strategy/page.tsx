import Link from 'next/link';
import { api, type Feature, type Project } from '@/lib/api';
import { bucketLabel, cn } from '@/lib/utils';
import { ArrowUpRight, Lightbulb, Rocket, ShieldAlert } from 'lucide-react';

const BUCKETS = [
  { key: 'quick_win', label: 'Quick Wins', icon: Lightbulb, blurb: 'Low effort, high impact — ship next.', tone: 'good' },
  { key: 'bet', label: 'Long-Term Bets', icon: Rocket, blurb: 'High effort, high upside but uncertain.', tone: 'accent' },
  { key: 'risk', label: 'Risks', icon: ShieldAlert, blurb: 'Churn drivers and operational/regulatory risk.', tone: 'warn' },
] as const;

export default async function StrategyPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);
  const [project, features] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<Feature[]>(`/api/projects/${projectId}/features`),
  ]);

  const grouped: Record<string, Feature[]> = { quick_win: [], bet: [], risk: [] };
  for (const f of features) {
    if (f.strategy_bucket && grouped[f.strategy_bucket]) grouped[f.strategy_bucket].push(f);
  }
  for (const k of Object.keys(grouped)) {
    grouped[k].sort((a, b) => b.rice_score - a.rice_score);
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <h1 className="h1 mt-1">Product Strategy</h1>
        <p className="muted text-sm mt-1">Features bucketed by strategic role, ranked by RICE within each bucket.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {BUCKETS.map((b) => {
          const Icon = b.icon;
          const items = grouped[b.key];
          return (
            <div key={b.key} className="card p-5 space-y-3">
              <div className="flex items-center gap-3">
                <div className={cn('w-9 h-9 rounded-md flex items-center justify-center',
                  b.tone === 'good' && 'bg-good/10 text-good',
                  b.tone === 'accent' && 'bg-accent/10 text-accent',
                  b.tone === 'warn' && 'bg-warn/10 text-warn')}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-medium">{b.label}</div>
                  <div className="muted text-xs">{b.blurb}</div>
                </div>
                <span className="badge ml-auto">{items.length}</span>
              </div>
              <ul className="space-y-2">
                {items.length === 0 && <li className="muted text-xs">No features in this bucket.</li>}
                {items.map((f) => (
                  <li key={f.id}>
                    <Link
                      href={`/projects/${projectId}/prd/${f.id}`}
                      className="block p-3 rounded-md border border-border bg-panel2 hover:border-accent/40"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="font-medium text-sm truncate">{f.title}</div>
                          <div className="muted text-xs mt-0.5 flex items-center gap-2">
                            <span>RICE {f.rice_score.toFixed(1)}</span>
                            <span>·</span>
                            <span>{f.reach} users</span>
                            <span>·</span>
                            <span>{f.effort}w effort</span>
                          </div>
                        </div>
                        <ArrowUpRight className="w-3.5 h-3.5 muted shrink-0" />
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
