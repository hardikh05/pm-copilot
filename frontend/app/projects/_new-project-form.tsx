'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, type Project } from '@/lib/api';
import { Loader2, Plus } from 'lucide-react';

export default function NewProjectForm() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const proj = await api<Project>('/api/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description: description || null }),
      });
      router.push(`/projects/${proj.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <button className="btn btn-primary" onClick={() => setOpen(true)}>
        <Plus className="w-4 h-4" /> New project
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="card p-4 space-y-3">
      <div className="space-y-1">
        <label className="label">Name</label>
        <input
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Recipe app — Q1 feedback"
          required
        />
      </div>
      <div className="space-y-1">
        <label className="label">Description (optional)</label>
        <textarea
          className="input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What product is this about? Anything that helps the agents."
          rows={2}
        />
      </div>
      {error && <div className="text-bad text-sm">{error}</div>}
      <div className="flex gap-2">
        <button className="btn btn-primary" disabled={loading}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create project'}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </form>
  );
}
