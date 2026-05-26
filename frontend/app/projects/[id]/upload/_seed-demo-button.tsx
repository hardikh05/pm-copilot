'use client';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { api } from '@/lib/api';
import { Loader2, Sparkles } from 'lucide-react';

export default function SeedDemoButton({ projectId }: { projectId: number }) {
  const router = useRouter();
  const [n, setN] = useState(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function seed() {
    setLoading(true);
    setError(null);
    try {
      const r = await api<{ inserted: number }>(
        `/api/projects/${projectId}/feedback/seed-demo?n=${n}`,
        { method: 'POST' }
      );
      setResult(r.inserted);
      router.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card p-6 space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-accent2/10 text-accent2 flex items-center justify-center">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <div className="font-medium">Seed demo data</div>
          <div className="muted text-xs">Synthetic recipe-app feedback across 8 themes — payments, onboarding, recipe gen, search, sync, pricing, dark mode, praise.</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <label className="label">Items</label>
        <input
          type="number"
          min={10}
          max={2000}
          value={n}
          onChange={(e) => setN(Number(e.target.value))}
          className="input w-24"
        />
        <button className="btn btn-primary ml-auto" onClick={seed} disabled={loading}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Seed'}
        </button>
      </div>
      {result !== null && <div className="text-good text-sm">Inserted {result} items.</div>}
      {error && <div className="text-bad text-sm">{error}</div>}
    </div>
  );
}
