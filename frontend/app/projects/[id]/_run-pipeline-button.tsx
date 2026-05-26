'use client';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Loader2, Wand2 } from 'lucide-react';

const STEPS_ORDER = ['feedback_intel', 'opportunity', 'strategy', 'roadmap'];
const LABELS: Record<string, string> = {
  start: 'Starting…',
  feedback_intel: 'Feedback Intelligence',
  opportunity: 'Opportunity Scoring',
  strategy: 'Product Strategy',
  roadmap: 'Roadmap Generator',
  done: 'Done',
};

export default function RunPipelineButton({ projectId }: { projectId: number }) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<{ step: string; status: string }[]>([]);
  const [error, setError] = useState<string | null>(null);

  function run() {
    setRunning(true);
    setError(null);
    setProgress([{ step: 'start', status: 'running' }]);
    const base = process.env.NEXT_PUBLIC_API_URL || '';
    const es = new EventSource(`${base}/api/projects/${projectId}/agents/pipeline/stream`);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setProgress((p) => [...p, { step: data.step, status: data.status }]);
        if (data.step === 'done' || data.status === 'failed') {
          es.close();
          setRunning(false);
          if (data.status === 'failed') setError(data.data?.error || 'Pipeline failed');
          else router.refresh();
        }
      } catch (e) {
        setError((e as Error).message);
      }
    };
    es.onerror = () => {
      es.close();
      setRunning(false);
      setError('Stream lost — check the backend logs.');
    };
  }

  if (!running && progress.length === 0) {
    return (
      <button className="btn btn-primary" onClick={run}>
        <Wand2 className="w-4 h-4" /> Run all agents
      </button>
    );
  }

  return (
    <div className="card p-3 min-w-[280px] space-y-2">
      <div className="flex items-center gap-2 text-sm">
        {running ? <Loader2 className="w-4 h-4 animate-spin text-accent" /> : <Wand2 className="w-4 h-4" />}
        <span className="font-medium">{running ? 'Running pipeline…' : 'Pipeline complete'}</span>
      </div>
      <ol className="space-y-1">
        {STEPS_ORDER.map((s) => {
          const done = progress.some((p) => p.step === s && p.status === 'completed');
          const active = !done && running;
          return (
            <li key={s} className="flex items-center gap-2 text-xs">
              <span className={`w-1.5 h-1.5 rounded-full ${done ? 'bg-good' : active ? 'bg-accent animate-pulse' : 'bg-border'}`} />
              <span className={done ? 'text-text' : 'muted'}>{LABELS[s]}</span>
            </li>
          );
        })}
      </ol>
      {error && <div className="text-bad text-xs">{error}</div>}
      {!running && (
        <button className="btn btn-ghost text-xs" onClick={run}>Run again</button>
      )}
    </div>
  );
}
