import Link from 'next/link';
import { api, type Feature, type Project } from '@/lib/api';
import RiceTable from './_rice-table';

export default async function PrioritizationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);
  const [project, features] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<Feature[]>(`/api/projects/${projectId}/features`),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <h1 className="h1 mt-1">Prioritization · RICE</h1>
        <p className="muted text-sm mt-1">
          Reach & Confidence are derived from your data; Effort is AI-estimated and can be overridden.
          Sorting recomputes on every change.
        </p>
      </div>

      {features.length === 0 ? (
        <div className="card p-8 text-center muted text-sm">
          No features yet. Run the pipeline from the project dashboard.
        </div>
      ) : (
        <RiceTable projectId={projectId} initial={features} />
      )}
    </div>
  );
}
