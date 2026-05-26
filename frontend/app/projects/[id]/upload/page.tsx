import Link from 'next/link';
import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import { api, type Project } from '@/lib/api';
import UploadDropzone from './_upload-dropzone';
import SeedDemoButton from './_seed-demo-button';

const SAMPLES = [
  { href: '/data/sample_feedback_50.csv',  label: '50 items', sub: 'quick test', icon: FileSpreadsheet, size: '7 KB' },
  { href: '/data/sample_feedback_500.csv', label: '500 items', sub: 'full demo', icon: FileSpreadsheet, size: '66 KB' },
  { href: '/data/sample_feedback.json',    label: '500 items', sub: 'JSON format', icon: FileJson, size: '129 KB' },
];

export default async function UploadPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);
  const project = await api<Project>(`/api/projects/${projectId}`);

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <h1 className="h1 mt-1">Add feedback</h1>
        <p className="muted text-sm mt-1">
          Upload a CSV or JSON file, or seed the demo dataset (500 synthetic recipe-app items).
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <UploadDropzone projectId={projectId} />
        <SeedDemoButton projectId={projectId} />
      </div>

      <div className="card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="h2">Sample datasets</h2>
            <p className="muted text-xs mt-0.5">Download a file to inspect the expected format, then drop it into the uploader above.</p>
          </div>
          <Link href="/samples" className="btn btn-ghost text-xs">View sample agent output →</Link>
        </div>
        <ul className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {SAMPLES.map((s) => {
            const Icon = s.icon;
            return (
              <li key={s.href}>
                <a href={s.href} download className="card card-hover p-3 flex items-center gap-3 text-sm">
                  <Icon className="w-4 h-4 text-accent shrink-0" />
                  <div className="min-w-0">
                    <div className="font-medium truncate">{s.label}</div>
                    <div className="muted text-xs">{s.sub} · {s.size}</div>
                  </div>
                  <Download className="w-3.5 h-3.5 muted ml-auto" />
                </a>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="card p-5 space-y-3">
        <h2 className="h2">Accepted formats</h2>
        <div className="text-sm text-muted space-y-2">
          <p><span className="text-text font-medium">CSV:</span> any header row. Recognized columns (case-insensitive):</p>
          <ul className="list-disc list-inside ml-2 space-y-1">
            <li><code>text / body / comment / review / feedback / message / content</code> — required</li>
            <li><code>source / channel / platform</code> — e.g. app_store, play_store, zendesk, nps</li>
            <li><code>rating / stars / score</code> — 1–5</li>
            <li><code>user_segment / segment / persona / tier</code></li>
            <li><code>author / user / name</code></li>
            <li><code>created_at / date / timestamp</code> — ISO 8601</li>
          </ul>
          <p><span className="text-text font-medium">JSON:</span> array of objects with the same keys, or {`{"items": [...]}`}.</p>
        </div>
      </div>
    </div>
  );
}
