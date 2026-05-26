import Link from 'next/link';
import { api, type Project } from '@/lib/api';
import { Plus } from 'lucide-react';
import NewProjectForm from './_new-project-form';

export default async function ProjectsPage() {
  let projects: Project[] = [];
  let error: string | null = null;
  try {
    projects = await api<Project[]>('/api/projects');
  } catch (e) {
    error = (e as Error).message;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="h1">Projects</h1>
          <p className="muted text-sm">Each project holds its own feedback corpus, clusters, features, and PRDs.</p>
        </div>
      </div>

      <NewProjectForm />

      {error && (
        <div className="card p-4 border-bad/40 bg-bad/5 text-sm">
          Couldn't reach the backend: <span className="text-bad font-mono">{error}</span>
          <div className="muted mt-2">Make sure the backend is running on <code>localhost:8000</code> and your <code>.env</code> is configured.</div>
        </div>
      )}

      {!error && projects.length === 0 && (
        <div className="card p-8 text-center">
          <div className="muted text-sm">No projects yet. Create one above to get started.</div>
        </div>
      )}

      {projects.length > 0 && (
        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {projects.map((p) => (
            <li key={p.id}>
              <Link href={`/projects/${p.id}`} className="card card-hover p-4 block">
                <div className="flex items-center gap-2 justify-between">
                  <div className="font-medium truncate">{p.name}</div>
                  <span className="badge">#{p.id}</span>
                </div>
                {p.description && <p className="muted text-sm mt-1 line-clamp-2">{p.description}</p>}
                <div className="muted text-xs mt-3">Created {new Date(p.created_at).toLocaleDateString()}</div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
