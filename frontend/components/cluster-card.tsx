'use client';
import { useState } from 'react';
import type { Cluster, ClusterDetail } from '@/lib/api';
import { api } from '@/lib/api';
import { ChevronDown, Loader2 } from 'lucide-react';
import { cn, formatPct, sentimentColor } from '@/lib/utils';

export default function ClusterCard({ projectId, cluster }: { projectId: number; cluster: Cluster }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<ClusterDetail | null>(null);
  const [loading, setLoading] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !detail) {
      setLoading(true);
      try {
        const d = await api<ClusterDetail>(`/api/projects/${projectId}/clusters/${cluster.id}`);
        setDetail(d);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="card overflow-hidden">
      <button className="w-full p-4 text-left card-hover" onClick={toggle}>
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <div className="font-medium truncate">{cluster.label}</div>
            {cluster.summary && <p className="muted text-xs line-clamp-2">{cluster.summary}</p>}
          </div>
          <ChevronDown className={cn('w-4 h-4 transition-transform shrink-0', open && 'rotate-180')} />
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span className="badge">{cluster.size} items</span>
          <SentimentBar cluster={cluster} />
        </div>
      </button>
      {open && (
        <div className="border-t border-border p-4 space-y-2">
          {loading && <div className="flex items-center gap-2 muted text-xs"><Loader2 className="w-3 h-3 animate-spin" /> Loading samples…</div>}
          {detail?.sample_feedback.map((s) => (
            <div key={s.id} className="text-sm p-2 rounded-md bg-panel2 border border-border">
              <div className="flex items-center gap-2 text-[11px] mb-1">
                {s.source && <span className="badge">{s.source}</span>}
                {s.rating !== null && <span className="badge">★ {s.rating}</span>}
                {s.user_segment && <span className="badge">{s.user_segment}</span>}
                <span className={cn('badge', sentimentColor(s.sentiment))}>{s.sentiment ?? 'unrated'}</span>
              </div>
              <div className="text-text">{s.text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SentimentBar({ cluster }: { cluster: Cluster }) {
  return (
    <div className="flex-1 flex h-1.5 rounded-full overflow-hidden bg-panel2">
      <div className="bg-good" style={{ width: `${cluster.positive_pct * 100}%` }} title={`positive ${formatPct(cluster.positive_pct)}`} />
      <div className="bg-muted/60" style={{ width: `${cluster.neutral_pct * 100}%` }} title={`neutral ${formatPct(cluster.neutral_pct)}`} />
      <div className="bg-bad" style={{ width: `${cluster.negative_pct * 100}%` }} title={`negative ${formatPct(cluster.negative_pct)}`} />
    </div>
  );
}
