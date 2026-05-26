import Link from 'next/link';
import { ArrowRight, FileText, GitBranch, Layers, ListTree, MessageSquare, Target } from 'lucide-react';

const STEPS = [
  { icon: Layers, title: 'Feedback Intelligence', body: 'Embeds & clusters thousands of reviews / tickets / NPS comments. Sentiment per item. Every cluster cites source.' },
  { icon: Target, title: 'Opportunity Scoring', body: 'RICE per cluster. Reach & confidence from data; Effort overridable by you.' },
  { icon: GitBranch, title: 'Product Strategy', body: 'Quick Wins, Long-Term Bets, and Risks — synthesized from scored features.' },
  { icon: FileText, title: 'PRD Generator', body: 'Drafts a structured PRD per feature: problem, goal, stories, metrics, requirements, edges.' },
  { icon: MessageSquare, title: 'PRD Critic', body: 'Second-pass review flags ambiguity, missing metrics, untestable requirements.' },
  { icon: ListTree, title: 'Roadmap Generator', body: 'Themes + Now / Next / Later, capacity-aware, with dependencies.' },
];

export default function Home() {
  return (
    <div className="space-y-14">
      <section className="space-y-6 pt-6">
        <span className="badge text-accent border-accent/30 bg-accent/10">Multi-agent · LangGraph · Gemini</span>
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight leading-tight">
          From raw user feedback to a prioritized roadmap
          <span className="block text-muted text-2xl md:text-3xl font-normal mt-2">
            An AI copilot for the workflow PMs actually run every week.
          </span>
        </h1>
        <p className="text-muted max-w-2xl">
          Upload support tickets, App Store reviews, or NPS comments. PM Copilot clusters them,
          scores opportunities with RICE, writes PRDs, runs a critic agent over each draft, and
          places features on a roadmap. You stay in the loop at every step.
        </p>
        <div className="flex gap-3 flex-wrap">
          <Link href="/projects" className="btn btn-primary">
            Start a project <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/samples" className="btn">View sample output</Link>
          <a href="#how" className="btn btn-ghost">How it works</a>
        </div>
      </section>

      <section id="how" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {STEPS.map(({ icon: Icon, title, body }, i) => (
          <div key={title} className="card card-hover p-5 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-md bg-accent/10 text-accent flex items-center justify-center">
                <Icon className="w-4 h-4" />
              </div>
              <div className="space-y-0.5">
                <div className="label">Step {i + 1}</div>
                <div className="font-medium">{title}</div>
              </div>
            </div>
            <p className="text-sm text-muted">{body}</p>
          </div>
        ))}
      </section>

      <section className="card p-6 space-y-3">
        <h2 className="h2">Why it's not another RAG chatbot</h2>
        <ul className="text-sm text-muted space-y-2 list-disc list-inside">
          <li><span className="text-text">Grounded methodology.</span> Embeddings + HDBSCAN for clusters. Sentiment is a classifier. Numbers can be checked.</li>
          <li><span className="text-text">Traceability.</span> Every insight, score, and PRD line links back to the raw feedback it came from.</li>
          <li><span className="text-text">Human-in-the-loop.</span> PRDs are editable. Critic notes can be accepted or dismissed. RICE Effort is overridable.</li>
          <li><span className="text-text">Conversational refinement.</span> "Re-prioritize weighting enterprise users 2×" re-runs the relevant agent.</li>
        </ul>
      </section>
    </div>
  );
}
