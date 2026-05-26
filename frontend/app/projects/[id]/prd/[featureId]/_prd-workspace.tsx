'use client';
import { useMemo, useState } from 'react';
import { api, type CritiqueNote, type PRD, type PRDContent } from '@/lib/api';
import { Check, Download, FileText, Loader2, Sparkles, X } from 'lucide-react';
import { cn } from '@/lib/utils';

const SECTIONS: { key: keyof PRDContent; label: string; multi: boolean }[] = [
  { key: 'problem', label: 'Problem', multi: false },
  { key: 'goal', label: 'Goal', multi: false },
  { key: 'user_stories', label: 'User Stories', multi: true },
  { key: 'success_metrics', label: 'Success Metrics', multi: true },
  { key: 'requirements', label: 'Requirements', multi: true },
  { key: 'edge_cases', label: 'Edge Cases', multi: true },
  { key: 'out_of_scope', label: 'Out of Scope', multi: true },
];

const SEVERITY_TONE: Record<string, string> = {
  high: 'text-bad border-bad/50 bg-bad/10',
  medium: 'text-warn border-warn/40 bg-warn/10',
  low: 'text-muted border-border bg-panel2',
};

export default function PrdWorkspace({
  projectId,
  featureId,
  initialPrds,
}: {
  projectId: number;
  featureId: number;
  initialPrds: PRD[];
}) {
  const [prds, setPrds] = useState<PRD[]>(initialPrds);
  const [selectedId, setSelectedId] = useState<number | null>(initialPrds[0]?.id ?? null);
  const [notes, setNotes] = useState<CritiqueNote[]>([]);
  const [generating, setGenerating] = useState(false);
  const [critiquing, setCritiquing] = useState(false);
  const [pipelineEvents, setPipelineEvents] = useState<{ step: string; status: string }[]>([]);
  const [editedContent, setEditedContent] = useState<PRDContent | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const current = useMemo(() => prds.find((p) => p.id === selectedId) ?? null, [prds, selectedId]);

  // Reset edits when selection changes
  function selectPrd(id: number) {
    setSelectedId(id);
    setEditedContent(null);
    setSavedAt(null);
    void loadNotes(id);
  }

  async function loadNotes(prdId: number) {
    const n = await api<CritiqueNote[]>(`/api/projects/${projectId}/prds/${prdId}/critique`);
    setNotes(n);
  }

  async function generate() {
    setGenerating(true);
    try {
      const p = await api<PRD>(`/api/projects/${projectId}/features/${featureId}/prds`, { method: 'POST' });
      setPrds((arr) => [p, ...arr]);
      setSelectedId(p.id);
      setEditedContent(null);
      setNotes([]);
    } finally {
      setGenerating(false);
    }
  }

  function runWithCriticStream() {
    setPipelineEvents([{ step: 'start', status: 'running' }]);
    const base = process.env.NEXT_PUBLIC_API_URL || '';
    const es = new EventSource(
      `${base}/api/projects/${projectId}/features/${featureId}/prd/run-with-critic/stream?max_iterations=2`
    );
    es.onmessage = async (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setPipelineEvents((p) => [...p, { step: data.step, status: data.status }]);
        if (data.step === 'done' || data.status === 'failed') {
          es.close();
          // Refresh PRDs + notes
          const list = await api<PRD[]>(`/api/projects/${projectId}/features/${featureId}/prds`);
          setPrds(list);
          if (list[0]) {
            setSelectedId(list[0].id);
            await loadNotes(list[0].id);
          }
        }
      } catch {}
    };
    es.onerror = () => es.close();
  }

  async function runCritique() {
    if (!current) return;
    setCritiquing(true);
    try {
      const n = await api<CritiqueNote[]>(`/api/projects/${projectId}/prds/${current.id}/critique`, { method: 'POST' });
      setNotes(n);
    } finally {
      setCritiquing(false);
    }
  }

  async function updateNoteStatus(noteId: number, status: 'accepted' | 'dismissed') {
    const updated = await api<CritiqueNote>(`/api/projects/${projectId}/critique/${noteId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
    setNotes((arr) => arr.map((n) => (n.id === noteId ? updated : n)));
  }

  async function save() {
    if (!current || !editedContent) return;
    const updated = await api<PRD>(`/api/projects/${projectId}/prds/${current.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ content: editedContent }),
    });
    setPrds((arr) => arr.map((p) => (p.id === updated.id ? updated : p)));
    setEditedContent(null);
    setSavedAt(new Date().toLocaleTimeString());
  }

  async function setStatus(status: 'accepted' | 'rejected' | 'draft') {
    if (!current) return;
    const updated = await api<PRD>(`/api/projects/${projectId}/prds/${current.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
    setPrds((arr) => arr.map((p) => (p.id === updated.id ? updated : p)));
  }

  function exportMarkdown() {
    if (!current) return;
    const c = (editedContent ?? current.content) as PRDContent;
    const lines: string[] = [];
    lines.push(`# ${current.title || 'PRD'}`);
    if (current.summary) lines.push('', current.summary);
    for (const s of SECTIONS) {
      const v = c[s.key];
      if (!v) continue;
      lines.push('', `## ${s.label}`);
      if (Array.isArray(v)) for (const item of v) lines.push(`- ${item}`);
      else lines.push(String(v));
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${(current.title || 'prd').replace(/[^a-z0-9-_]+/gi, '_')}_v${current.version}.md`;
    a.click();
  }

  if (prds.length === 0) {
    return (
      <div className="card p-8 space-y-5 text-center">
        <div className="space-y-1">
          <div className="font-medium">No PRD yet for this feature</div>
          <p className="muted text-sm">Generate one, or run with the Critic for iterative refinement.</p>
        </div>
        <div className="flex justify-center gap-2">
          <button className="btn" onClick={generate} disabled={generating}>
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            Generate PRD
          </button>
          <button className="btn btn-primary" onClick={runWithCriticStream}>
            <Sparkles className="w-4 h-4" />
            Generate + Critic (loop)
          </button>
        </div>
        {pipelineEvents.length > 0 && (
          <ol className="text-xs muted text-left max-w-xs mx-auto space-y-1">
            {pipelineEvents.map((e, i) => (
              <li key={i}>· {e.step} — {e.status}</li>
            ))}
          </ol>
        )}
      </div>
    );
  }

  const content = (editedContent ?? current?.content) as PRDContent | undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr,360px] gap-4">
      {/* Main column */}
      <div className="space-y-4 min-w-0">
        {/* Toolbar */}
        <div className="card p-3 flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 text-sm">
            <FileText className="w-4 h-4 text-accent" />
            <span className="font-medium truncate max-w-[16rem]">{current?.title || 'Untitled PRD'}</span>
            {current && <span className="badge">v{current.version}</span>}
            {current && <StatusBadge status={current.status} />}
          </div>
          <div className="flex-1" />
          <select
            value={selectedId ?? ''}
            onChange={(e) => selectPrd(Number(e.target.value))}
            className="input w-auto"
          >
            {prds.map((p) => (
              <option key={p.id} value={p.id}>v{p.version} · {p.status}</option>
            ))}
          </select>
          <button className="btn" onClick={generate} disabled={generating}>
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Regenerate'}
          </button>
          <button className="btn" onClick={runCritique} disabled={critiquing || !current}>
            {critiquing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Run critique'}
          </button>
          <button className="btn" onClick={exportMarkdown}><Download className="w-3.5 h-3.5" /> Markdown</button>
          {current?.status !== 'accepted' && (
            <button className="btn btn-primary" onClick={() => setStatus('accepted')}>
              <Check className="w-4 h-4" /> Accept
            </button>
          )}
        </div>

        {/* Summary */}
        {current?.summary && (
          <div className="card p-4 text-sm muted">{current.summary}</div>
        )}

        {/* Sections */}
        {content && (
          <div className="space-y-3">
            {SECTIONS.map((s) => (
              <SectionEditor
                key={s.key}
                label={s.label}
                multi={s.multi}
                value={content[s.key] as string | string[]}
                onChange={(v) =>
                  setEditedContent({ ...(content as PRDContent), [s.key]: v } as PRDContent)
                }
              />
            ))}
          </div>
        )}

        {editedContent && (
          <div className="sticky bottom-4 flex items-center justify-end gap-2">
            <button className="btn" onClick={() => setEditedContent(null)}>Discard</button>
            <button className="btn btn-primary" onClick={save}>Save changes</button>
          </div>
        )}
        {savedAt && <div className="text-xs muted text-right">Saved at {savedAt}</div>}
      </div>

      {/* Side panel: Critic */}
      <aside className="space-y-3">
        <div className="card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-accent" />
              <span className="font-medium">Critic</span>
            </div>
            <span className="badge">{notes.length} notes</span>
          </div>
          <div className="muted text-xs">
            Reviews the PRD for ambiguity, missing metrics, untestable requirements.
          </div>
          {notes.length === 0 && <div className="muted text-xs">No notes yet — run critique to populate.</div>}
          <ul className="space-y-2">
            {notes.map((n) => (
              <li key={n.id} className={cn('p-3 rounded-md border text-xs space-y-1', SEVERITY_TONE[n.severity])}>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="uppercase tracking-wider text-[10px] font-semibold">{n.severity}</span>
                  <span className="badge text-[10px]">{n.section}</span>
                  <span className="badge text-[10px]">{n.category}</span>
                </div>
                <div className="text-text">{n.message}</div>
                {n.suggestion && <div className="muted"><span className="text-text">Suggestion:</span> {n.suggestion}</div>}
                {n.status === 'open' ? (
                  <div className="flex gap-1 pt-1">
                    <button className="btn btn-ghost text-[11px] py-1" onClick={() => updateNoteStatus(n.id, 'accepted')}>
                      <Check className="w-3 h-3" /> Accept
                    </button>
                    <button className="btn btn-ghost text-[11px] py-1" onClick={() => updateNoteStatus(n.id, 'dismissed')}>
                      <X className="w-3 h-3" /> Dismiss
                    </button>
                  </div>
                ) : (
                  <div className="text-[10px] uppercase tracking-wider muted">{n.status}</div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}

function SectionEditor({
  label,
  multi,
  value,
  onChange,
}: {
  label: string;
  multi: boolean;
  value: string | string[];
  onChange: (v: string | string[]) => void;
}) {
  return (
    <div className="card p-4 space-y-2">
      <div className="label">{label}</div>
      {multi ? (
        <ListEditor value={Array.isArray(value) ? value : value ? [String(value)] : []} onChange={onChange} />
      ) : (
        <textarea
          className="input min-h-[6rem] font-mono text-[13px]"
          value={typeof value === 'string' ? value : String(value ?? '')}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}

function ListEditor({ value, onChange }: { value: string[]; onChange: (v: string[]) => void }) {
  return (
    <div className="space-y-1.5">
      {value.map((item, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="muted text-xs pt-2.5">{i + 1}.</span>
          <textarea
            className="input min-h-[2.25rem] text-[13px]"
            value={item}
            onChange={(e) => {
              const next = [...value];
              next[i] = e.target.value;
              onChange(next);
            }}
            rows={1}
          />
          <button
            className="btn btn-ghost p-1 mt-1"
            onClick={() => onChange(value.filter((_, idx) => idx !== i))}
            title="Remove"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
      <button className="btn btn-ghost text-xs" onClick={() => onChange([...value, ''])}>
        + Add
      </button>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === 'accepted' ? 'text-good border-good/40 bg-good/10' :
    status === 'rejected' ? 'text-bad border-bad/40 bg-bad/10' :
    'text-muted';
  return <span className={cn('badge', tone)}>{status}</span>;
}
