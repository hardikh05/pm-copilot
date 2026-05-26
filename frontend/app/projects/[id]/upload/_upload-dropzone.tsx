'use client';
import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';
import { apiUpload } from '@/lib/api';
import { Loader2, Upload } from 'lucide-react';

export default function UploadDropzone({ projectId }: { projectId: number }) {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ inserted: number; skipped: number; total: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await apiUpload<{ inserted: number; skipped: number; total: number }>(
        `/api/projects/${projectId}/feedback/upload`,
        fd
      );
      setResult(r);
      router.refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className={`card p-6 space-y-4 transition-colors ${dragOver ? 'border-accent/60 bg-accent/5' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) void handleFile(f);
      }}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-accent/10 text-accent flex items-center justify-center">
          <Upload className="w-4 h-4" />
        </div>
        <div>
          <div className="font-medium">Upload CSV or JSON</div>
          <div className="muted text-xs">Drag and drop, or click to browse.</div>
        </div>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept=".csv,.json,application/json,text/csv"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) void handleFile(f); }}
      />
      <button
        className="btn w-full justify-center"
        onClick={() => fileRef.current?.click()}
        disabled={loading}
      >
        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Choose file'}
      </button>
      {result && (
        <div className="text-sm">
          <span className="text-good">Inserted {result.inserted}</span>
          {result.skipped > 0 && <span className="muted"> · skipped {result.skipped}</span>}
        </div>
      )}
      {error && <div className="text-bad text-sm">{error}</div>}
    </div>
  );
}
