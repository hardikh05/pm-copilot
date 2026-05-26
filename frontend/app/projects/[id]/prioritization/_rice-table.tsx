'use client';
import Link from 'next/link';
import { useState } from 'react';
import { api, type Feature } from '@/lib/api';
import { Check, FileText, Loader2 } from 'lucide-react';
import { bucketColor, bucketLabel, cn } from '@/lib/utils';

export default function RiceTable({ projectId, initial }: { projectId: number; initial: Feature[] }) {
  const [features, setFeatures] = useState(initial);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [savingId, setSavingId] = useState<number | null>(null);

  function startEdit(f: Feature) {
    setEditingId(f.id);
    setEditValue(String(f.effort));
  }

  async function save(f: Feature) {
    const n = parseFloat(editValue);
    if (!isFinite(n) || n < 0.5) return;
    setSavingId(f.id);
    try {
      const updated = await api<Feature>(`/api/projects/${projectId}/features/${f.id}/effort`, {
        method: 'PATCH',
        body: JSON.stringify({ effort: n }),
      });
      setFeatures((arr) =>
        arr.map((x) => (x.id === f.id ? updated : x)).sort((a, b) => b.rice_score - a.rice_score)
      );
      setEditingId(null);
    } finally {
      setSavingId(null);
    }
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-panel2 border-b border-border">
          <tr className="text-left">
            <Th>Feature</Th>
            <Th className="w-24 text-right">RICE</Th>
            <Th className="w-20 text-right">Reach</Th>
            <Th className="w-20 text-right">Impact</Th>
            <Th className="w-24 text-right">Confidence</Th>
            <Th className="w-28 text-right">Effort (w)</Th>
            <Th className="w-28">Bucket</Th>
            <Th className="w-24" />
          </tr>
        </thead>
        <tbody>
          {features.map((f) => (
            <tr key={f.id} className="border-b border-border last:border-b-0 hover:bg-panel2/50">
              <Td>
                <div className="font-medium">{f.title}</div>
                {f.description && <div className="muted text-xs line-clamp-1">{f.description}</div>}
              </Td>
              <Td className="text-right font-mono tabular-nums">{f.rice_score.toFixed(1)}</Td>
              <Td className="text-right font-mono tabular-nums">{f.reach}</Td>
              <Td className="text-right font-mono tabular-nums">{f.impact}</Td>
              <Td className="text-right font-mono tabular-nums">{f.confidence.toFixed(2)}</Td>
              <Td className="text-right">
                {editingId === f.id ? (
                  <div className="flex items-center justify-end gap-1">
                    <input
                      type="number"
                      min={0.5}
                      step={0.5}
                      className="input w-16 text-right font-mono"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      autoFocus
                    />
                    <button className="btn p-1" onClick={() => save(f)} disabled={savingId === f.id}>
                      {savingId === f.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                    </button>
                  </div>
                ) : (
                  <button className="font-mono tabular-nums hover:text-accent" onClick={() => startEdit(f)}>
                    {f.effort.toFixed(1)}{f.effort_overridden && <span className="text-accent ml-1">*</span>}
                  </button>
                )}
              </Td>
              <Td>
                <span className={cn('badge', bucketColor(f.strategy_bucket))}>{bucketLabel(f.strategy_bucket)}</span>
              </Td>
              <Td className="text-right">
                <Link href={`/projects/${projectId}/prd/${f.id}`} className="btn btn-ghost text-xs">
                  <FileText className="w-3 h-3" /> PRD
                </Link>
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-4 py-2 text-xs muted border-t border-border bg-panel2/40">
        <span className="text-accent">*</span> Effort manually overridden. AI-estimated otherwise.
      </div>
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={cn('px-4 py-2 text-xs uppercase tracking-wider text-muted font-medium', className)}>{children}</th>;
}
function Td({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <td className={cn('px-4 py-3 align-top', className)}>{children}</td>;
}
