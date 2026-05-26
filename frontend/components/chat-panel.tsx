'use client';
import { useEffect, useRef, useState } from 'react';
import { api, type ChatMessage } from '@/lib/api';
import { HelpCircle, Loader2, MessageSquare, RefreshCw, Send, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

// Suggestion buttons split into the two things the Copilot actually does:
// ask questions about the data, or re-run an agent with PM guidance.
const ASK_SUGGESTIONS = [
  'Which cluster has the worst sentiment?',
  'Why is the top feature a Quick Win?',
  "What's on the roadmap for next quarter?",
];

const RERUN_SUGGESTIONS = [
  'Re-prioritize weighting enterprise users 2×',
  'Reassign strategy buckets focusing on retention',
  'Rebuild the roadmap with a 6-engineer-week capacity per horizon',
];

export default function ChatPanel({ projectId }: { projectId: number }) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<ChatMessage[]>(`/api/projects/${projectId}/chat`).then(setMessages).catch(() => {});
  }, [projectId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api<ChatMessage[]>(`/api/projects/${projectId}/chat`, {
        method: 'POST',
        body: JSON.stringify({ content: text }),
      });
      setMessages((m) => [...m, ...res]);
      setInput('');
      router.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <MessageSquare className="w-4 h-4 text-accent" />
        <h2 className="h2">Copilot</h2>
        <span className="badge ml-auto">Conversational layer</span>
      </div>

      <div className="text-xs muted leading-relaxed">
        The Copilot does two things:
        <span className="block mt-1.5">
          <span className="text-text font-medium inline-flex items-center gap-1"><HelpCircle className="w-3 h-3" /> Answer</span>{' '}
          questions about your project, grounded in the actual data (clusters, RICE scores, roadmap).
        </span>
        <span className="block mt-1">
          <span className="text-text font-medium inline-flex items-center gap-1"><RefreshCw className="w-3 h-3" /> Re-run</span>{' '}
          an agent with your guidance — your instruction is passed as a hint to the agent's prompt.
        </span>
      </div>

      <div
        ref={scrollRef}
        className="max-h-72 overflow-y-auto space-y-3 border border-border rounded-md p-3 bg-panel2"
      >
        {messages.length === 0 && (
          <div className="muted text-xs text-center py-4">
            No messages yet. Try a suggestion below.
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`text-sm ${m.role === 'user' ? '' : ''}`}>
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider mb-1">
              {m.role === 'user' ? (
                <span className="text-muted">You</span>
              ) : (
                <span className="text-accent flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> Copilot
                </span>
              )}
              {m.triggered_agent && (
                <span className="badge text-[10px] text-accent border-accent/40 bg-accent/5">
                  re-ran: {m.triggered_agent}
                </span>
              )}
            </div>
            <div className={m.role === 'user' ? 'text-text' : 'text-text leading-relaxed'}>
              {m.content}
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <div className="label flex items-center gap-1"><HelpCircle className="w-3 h-3" /> Ask</div>
        <div className="flex flex-wrap gap-2">
          {ASK_SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="badge hover:border-accent/60 disabled:opacity-50"
              onClick={() => send(s)}
              disabled={loading}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="label flex items-center gap-1 mt-3"><RefreshCw className="w-3 h-3" /> Re-run with guidance</div>
        <div className="flex flex-wrap gap-2">
          {RERUN_SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="badge hover:border-accent/60 disabled:opacity-50"
              onClick={() => send(s)}
              disabled={loading}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); void send(input); }}
        className="flex gap-2"
      >
        <input
          className="input"
          placeholder="Ask a question, or tell the copilot to re-run something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button className="btn btn-primary" disabled={loading || !input.trim()}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
      {error && <div className="text-bad text-xs">{error}</div>}
    </div>
  );
}
