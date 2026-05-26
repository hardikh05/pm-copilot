import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import type { Feature, Roadmap, RoadmapItem } from '@/lib/api';
import { bucketColor, bucketLabel, cn } from '@/lib/utils';

const COLS: { key: 'now' | 'next' | 'later'; label: string; blurb: string }[] = [
  { key: 'now', label: 'Now', blurb: 'Next 4-6 weeks' },
  { key: 'next', label: 'Next', blurb: 'Next quarter' },
  { key: 'later', label: 'Later', blurb: 'Beyond' },
];

export default function RoadmapBoard({
  projectId,
  roadmap,
  featureMap,
}: {
  projectId: number;
  roadmap: Roadmap;
  featureMap: Record<number, Feature>;
}) {
  // Group by theme within each horizon
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {COLS.map((col) => {
        const items = roadmap[col.key];
        const totalWeeks = items.reduce((s, i) => s + i.estimated_weeks, 0);
        const over = totalWeeks > roadmap.capacity_weeks_per_horizon;
        return (
          <div key={col.key} className="card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">{col.label}</div>
                <div className="muted text-xs">{col.blurb}</div>
              </div>
              <span className={cn('badge', over && 'text-warn border-warn/40 bg-warn/10')}>
                {totalWeeks.toFixed(1)} / {roadmap.capacity_weeks_per_horizon}w
              </span>
            </div>

            {groupByTheme(items).map(({ theme, items }) => (
              <div key={theme || '__none'} className="space-y-2">
                {theme && <div className="label">{theme}</div>}
                <ul className="space-y-2">
                  {items.map((it) => (
                    <li key={it.id}>
                      <Card projectId={projectId} item={it} feature={featureMap[it.feature_id]} featureMap={featureMap} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function groupByTheme(items: RoadmapItem[]) {
  const groups: Record<string, RoadmapItem[]> = {};
  for (const it of items) {
    const k = it.theme || '__none';
    (groups[k] ??= []).push(it);
  }
  return Object.entries(groups).map(([theme, items]) => ({
    theme: theme === '__none' ? null : theme,
    items: items.sort((a, b) => a.order_index - b.order_index),
  }));
}

function Card({
  projectId,
  item,
  feature,
  featureMap,
}: {
  projectId: number;
  item: RoadmapItem;
  feature?: Feature;
  featureMap: Record<number, Feature>;
}) {
  if (!feature) {
    return (
      <div className="p-3 rounded-md border border-border bg-panel2 text-xs muted">
        Feature #{item.feature_id} (missing)
      </div>
    );
  }
  return (
    <Link
      href={`/projects/${projectId}/prd/${feature.id}`}
      className="block p-3 rounded-md border border-border bg-panel2 hover:border-accent/40 space-y-1.5"
    >
      <div className="text-sm font-medium leading-snug">{feature.title}</div>
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className={cn('badge text-[10px]', bucketColor(feature.strategy_bucket))}>
          {bucketLabel(feature.strategy_bucket)}
        </span>
        <span className="badge text-[10px]">RICE {feature.rice_score.toFixed(0)}</span>
        <span className="badge text-[10px]">{item.estimated_weeks}w</span>
      </div>
      {item.depends_on.length > 0 && (
        <div className="muted text-[10px] flex items-center gap-1 pt-1">
          <ArrowRight className="w-2.5 h-2.5" /> needs:
          {item.depends_on.map((d) => (
            <span key={d} className="badge text-[10px]">{featureMap[d]?.title ?? `#${d}`}</span>
          ))}
        </div>
      )}
    </Link>
  );
}
