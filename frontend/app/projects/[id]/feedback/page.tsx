import Link from 'next/link';
import { api, type Cluster, type Project } from '@/lib/api';
import ClusterCard from '@/components/cluster-card';

export default async function FeedbackPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);
  const [project, clusters] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<Cluster[]>(`/api/projects/${projectId}/clusters`),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <h1 className="h1 mt-1">Feedback Intelligence</h1>
        <p className="muted text-sm mt-1">
          {clusters.length} clusters discovered by HDBSCAN over Gemini embeddings.
          Click a cluster to see source feedback.
        </p>
      </div>

      {clusters.length === 0 ? (
        <div className="card p-8 text-center muted text-sm">
          No clusters yet. Run the pipeline from the project dashboard.
        </div>
      ) : (
        <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {clusters.map((c) => (
            <li key={c.id}>
              <ClusterCard projectId={projectId} cluster={c} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
