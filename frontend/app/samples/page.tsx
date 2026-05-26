import Link from 'next/link';
import { ArrowRight, Database, FileCheck2, FileText, GitBranch, Layers, Sparkles, Target } from 'lucide-react';

// Server-rendered: reads the snapshot JSONs from /public/data so it works
// without any backend at all. Useful as a "see what it produces" preview.

type Cluster = {
  id: number;
  label: string;
  summary: string | null;
  size: number;
  sentiment: { positive_pct: number; neutral_pct: number; negative_pct: number; avg_score: number };
  sample_feedback_ids: number[];
};

type Feature = {
  id: number;
  title: string;
  description: string | null;
  rice_score: number;
  rice_breakdown: { reach: number; impact: number; confidence: number; effort_weeks: number };
  strategy_bucket: string | null;
  rationale: string | null;
  from_cluster_id: number | null;
};

type RoadmapItem = {
  feature_id: number;
  feature_title: string;
  theme: string | null;
  estimated_weeks: number;
  depends_on: number[];
};

type Roadmap = { now: RoadmapItem[]; next: RoadmapItem[]; later: RoadmapItem[] };

type CritiqueNote = {
  section: string;
  severity: 'low' | 'medium' | 'high';
  category: string;
  message: string;
  suggestion: string | null;
  status: string;
};

type PRDContent = {
  problem: string;
  goal: string;
  user_stories: string[];
  success_metrics: string[];
  requirements: string[];
  edge_cases: string[];
  out_of_scope: string[];
};

type PRD = {
  id: number;
  feature_id: number;
  feature_title: string | null;
  feature_rice_score: number | null;
  version: number;
  status: string;
  title: string | null;
  summary: string | null;
  content: PRDContent;
  source_feedback_ids: number[];
  critique_notes: CritiqueNote[];
  _meta?: { note?: string };
};

async function loadSamples(): Promise<{ clusters: Cluster[]; features: Feature[]; roadmap: Roadmap; prds: PRD[] } | null> {
  try {
    const fs = await import('node:fs/promises');
    const path = await import('node:path');
    const dir = path.join(process.cwd(), 'public', 'data');
    const [clusters, features, roadmap, prds] = await Promise.all([
      fs.readFile(path.join(dir, 'sample_output_clusters.json'), 'utf-8').then(JSON.parse),
      fs.readFile(path.join(dir, 'sample_output_features.json'), 'utf-8').then(JSON.parse),
      fs.readFile(path.join(dir, 'sample_output_roadmap.json'), 'utf-8').then(JSON.parse),
      fs.readFile(path.join(dir, 'sample_output_prds.json'), 'utf-8').then(JSON.parse).catch(() => []),
    ]);
    return { clusters, features, roadmap, prds };
  } catch {
    return null;
  }
}

const SEV_TONE: Record<string, string> = {
  high: 'text-bad border-bad/50 bg-bad/10',
  medium: 'text-warn border-warn/40 bg-warn/10',
  low: 'text-muted border-border bg-panel2',
};

function bucketTone(b: string | null) {
  if (b === 'quick_win') return 'text-good border-good/40 bg-good/10';
  if (b === 'bet') return 'text-accent border-accent/40 bg-accent/10';
  if (b === 'risk') return 'text-warn border-warn/40 bg-warn/10';
  return 'text-muted';
}
function bucketLabel(b: string | null) {
  return b === 'quick_win' ? 'Quick Win' : b === 'bet' ? 'Bet' : b === 'risk' ? 'Risk' : '—';
}

export default async function SamplesPage() {
  const data = await loadSamples();

  if (!data) {
    return (
      <div className="card p-8 text-center muted text-sm">
        Sample data files not found. Run <code>python backend/scripts/export_demo_data.py</code> to generate them.
      </div>
    );
  }

  const { clusters, features, roadmap, prds } = data;
  const prd = prds[0];

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <span className="badge text-accent border-accent/30 bg-accent/10">Snapshot</span>
        <h1 className="h1">What the agents produced</h1>
        <p className="muted max-w-2xl">
          This page is rendered from a real pipeline run on the 500-item synthetic dataset.
          No backend or API key required — useful for a quick look at what PM Copilot
          actually outputs before you spin it up yourself.
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Link href="/projects" className="btn btn-primary">Try it on your own data <ArrowRight className="w-4 h-4" /></Link>
          <a href="/data/sample_feedback_500.csv" download className="btn">Download the input CSV</a>
        </div>
      </section>

      {/* Pipeline summary strip */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat icon={Database} label="Feedback items" value="500" />
        <Stat icon={Layers} label="Clusters" value={String(clusters.length)} />
        <Stat icon={Target} label="Features (RICE)" value={String(features.length)} />
        <Stat icon={GitBranch} label="Roadmap items" value={String(roadmap.now.length + roadmap.next.length + roadmap.later.length)} />
      </section>

      {/* Clusters */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-accent" />
          <h2 className="h2">Feedback Intelligence — discovered clusters</h2>
        </div>
        <p className="muted text-sm">
          HDBSCAN density-based clustering over Gemini embeddings. Each cluster cites source feedback IDs (traceability).
          Sentiment is a separate classifier, not "ask the LLM how it feels."
        </p>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {clusters.map((c) => (
            <li key={c.id} className="card p-4 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="font-medium">{c.label}</div>
                <span className="badge">{c.size} items</span>
              </div>
              {c.summary && <p className="muted text-xs">{c.summary}</p>}
              <div className="flex h-1.5 rounded-full overflow-hidden bg-panel2">
                <div className="bg-good" style={{ width: `${c.sentiment.positive_pct * 100}%` }} />
                <div className="bg-muted/60" style={{ width: `${c.sentiment.neutral_pct * 100}%` }} />
                <div className="bg-bad" style={{ width: `${c.sentiment.negative_pct * 100}%` }} />
              </div>
              <div className="flex gap-3 text-[11px] muted">
                <span><span className="text-good">●</span> {Math.round(c.sentiment.positive_pct * 100)}%</span>
                <span><span className="text-muted">●</span> {Math.round(c.sentiment.neutral_pct * 100)}%</span>
                <span><span className="text-bad">●</span> {Math.round(c.sentiment.negative_pct * 100)}%</span>
                <span className="ml-auto">avg {c.sentiment.avg_score >= 0 ? '+' : ''}{c.sentiment.avg_score.toFixed(2)}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* Features */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-accent" />
          <h2 className="h2">Opportunity Scoring — features by RICE</h2>
        </div>
        <p className="muted text-sm">
          Reach = cluster size. Confidence = log-scaled size combined with sentiment variance.
          Impact + Effort are LLM-suggested; Effort is overridable by the PM (the live app re-ranks instantly when you edit).
        </p>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-panel2 border-b border-border">
              <tr className="text-left">
                <Th>Feature</Th>
                <Th className="w-20 text-right">RICE</Th>
                <Th className="w-16 text-right">Reach</Th>
                <Th className="w-16 text-right">Impact</Th>
                <Th className="w-20 text-right">Conf.</Th>
                <Th className="w-20 text-right">Effort</Th>
                <Th className="w-24">Bucket</Th>
              </tr>
            </thead>
            <tbody>
              {features.map((f) => (
                <tr key={f.id} className="border-b border-border last:border-b-0">
                  <Td>
                    <div className="font-medium">{f.title}</div>
                    {f.rationale && <div className="muted text-xs line-clamp-2 mt-0.5">{f.rationale}</div>}
                  </Td>
                  <Td className="text-right font-mono tabular-nums">{f.rice_score.toFixed(1)}</Td>
                  <Td className="text-right font-mono tabular-nums">{f.rice_breakdown.reach}</Td>
                  <Td className="text-right font-mono tabular-nums">{f.rice_breakdown.impact}</Td>
                  <Td className="text-right font-mono tabular-nums">{f.rice_breakdown.confidence.toFixed(2)}</Td>
                  <Td className="text-right font-mono tabular-nums">{f.rice_breakdown.effort_weeks}w</Td>
                  <Td><span className={`badge ${bucketTone(f.strategy_bucket)}`}>{bucketLabel(f.strategy_bucket)}</span></Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Roadmap */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-accent" />
          <h2 className="h2">Roadmap — Now / Next / Later</h2>
        </div>
        <p className="muted text-sm">Capacity-aware placement with themes and dependencies.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(['now', 'next', 'later'] as const).map((h) => {
            const items = roadmap[h];
            const total = items.reduce((s, i) => s + i.estimated_weeks, 0);
            return (
              <div key={h} className="card p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="font-semibold capitalize">{h}</div>
                  <span className="badge">{total.toFixed(1)}w</span>
                </div>
                <ul className="space-y-1.5">
                  {items.map((it) => (
                    <li key={it.feature_id} className="p-2 rounded-md border border-border bg-panel2 text-xs">
                      <div className="font-medium text-sm">{it.feature_title}</div>
                      <div className="muted flex flex-wrap gap-2 mt-1">
                        {it.theme && <span>· {it.theme}</span>}
                        <span>· {it.estimated_weeks}w</span>
                      </div>
                    </li>
                  ))}
                  {items.length === 0 && <li className="muted text-xs">(empty)</li>}
                </ul>
              </div>
            );
          })}
        </div>
      </section>

      {/* PRD + Critic */}
      {prd && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-accent" />
            <h2 className="h2">PRD Generator + Critic — example output</h2>
          </div>
          <p className="muted text-sm">
            One feature's PRD draft from the Generator agent, with the Critic agent's review notes alongside.
            {prd._meta?.note && <span className="block mt-1 text-xs italic">{prd._meta.note}</span>}
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr,360px] gap-4">
            {/* PRD body */}
            <div className="card p-5 space-y-4 min-w-0">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="badge">v{prd.version}</span>
                  <span className="badge">{prd.status}</span>
                  {prd.feature_rice_score !== null && (
                    <span className="badge">RICE {prd.feature_rice_score.toFixed(1)}</span>
                  )}
                  <span className="badge">Source feedback: {prd.source_feedback_ids.length} items</span>
                </div>
                <h3 className="text-lg font-semibold mt-2">{prd.title}</h3>
                {prd.summary && <p className="muted text-sm">{prd.summary}</p>}
              </div>

              <PrdSection label="Problem" body={prd.content.problem} />
              <PrdSection label="Goal" body={prd.content.goal} />
              <PrdList label="User Stories" items={prd.content.user_stories} />
              <PrdList label="Success Metrics" items={prd.content.success_metrics} />
              <PrdList label="Requirements" items={prd.content.requirements} />
              <PrdList label="Edge Cases" items={prd.content.edge_cases} />
              <PrdList label="Out of Scope" items={prd.content.out_of_scope} />
            </div>

            {/* Critic panel */}
            <aside className="card p-4 space-y-3 h-fit lg:sticky lg:top-20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-accent" />
                  <span className="font-medium">Critic</span>
                </div>
                <span className="badge">{prd.critique_notes.length} notes</span>
              </div>
              <p className="muted text-xs">
                Second-pass review. Flags ambiguity, missing metrics, untestable requirements — like a strict editor.
              </p>
              <ul className="space-y-2">
                {prd.critique_notes.map((n, i) => (
                  <li key={i} className={`p-3 rounded-md border text-xs space-y-1 ${SEV_TONE[n.severity]}`}>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="uppercase tracking-wider text-[10px] font-semibold">{n.severity}</span>
                      <span className="badge text-[10px]">{n.section}</span>
                      <span className="badge text-[10px]">{n.category}</span>
                    </div>
                    <div className="text-text">{n.message}</div>
                    {n.suggestion && (
                      <div className="muted"><span className="text-text">Suggestion:</span> {n.suggestion}</div>
                    )}
                  </li>
                ))}
              </ul>
              <div className="pt-2 border-t border-border flex items-center gap-2 text-xs muted">
                <FileCheck2 className="w-3.5 h-3.5" />
                In the live app these are accept/dismiss-able and feed into a revision loop.
              </div>
            </aside>
          </div>
        </section>
      )}

      <section className="card p-5 space-y-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent" />
          <h2 className="h2">Raw JSON snapshots</h2>
        </div>
        <p className="muted text-sm">These are the actual files behind everything above — drop them into a code review or a portfolio writeup.</p>
        <ul className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
          {[
            ['/data/sample_output_clusters.json', 'clusters'],
            ['/data/sample_output_features.json', 'features'],
            ['/data/sample_output_roadmap.json', 'roadmap'],
            ['/data/sample_output_prds.json', 'prds'],
          ].map(([href, label]) => (
            <li key={href}>
              <a href={href} download className="card card-hover p-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-accent" />
                <span className="font-medium">{label}.json</span>
                <span className="muted text-xs ml-auto">download</span>
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function PrdSection({ label, body }: { label: string; body: string }) {
  return (
    <div className="space-y-1">
      <div className="label">{label}</div>
      <p className="text-sm leading-relaxed">{body}</p>
    </div>
  );
}

function PrdList({ label, items }: { label: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <div className="space-y-1.5">
      <div className="label">{label}</div>
      <ul className="space-y-1.5">
        {items.map((it, i) => (
          <li key={i} className="text-sm leading-relaxed flex gap-2">
            <span className="muted text-xs pt-0.5">{i + 1}.</span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 muted text-xs uppercase tracking-wider">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={`px-4 py-2 text-xs uppercase tracking-wider text-muted font-medium ${className ?? ''}`}>{children}</th>;
}
function Td({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-3 align-top ${className ?? ''}`}>{children}</td>;
}
