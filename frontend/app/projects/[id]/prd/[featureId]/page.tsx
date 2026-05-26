import Link from 'next/link';
import { api, type Feature, type PRD, type Project } from '@/lib/api';
import PrdWorkspace from './_prd-workspace';

export default async function PRDPage({ params }: { params: Promise<{ id: string; featureId: string }> }) {
  const { id, featureId } = await params;
  const projectId = Number(id);
  const fid = Number(featureId);

  const [project, features, prds] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<Feature[]>(`/api/projects/${projectId}/features`),
    api<PRD[]>(`/api/projects/${projectId}/features/${fid}/prds`),
  ]);

  const feature = features.find((f) => f.id === fid);
  if (!feature) {
    return (
      <div className="space-y-4">
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <div className="card p-6 text-sm">Feature not found.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}/prioritization`} className="text-xs muted hover:text-text">
          ← {project.name} · Prioritization
        </Link>
        <h1 className="h1 mt-1">{feature.title}</h1>
        <div className="muted text-xs mt-1 flex items-center gap-2">
          <span>RICE {feature.rice_score.toFixed(1)}</span>
          <span>·</span>
          <span>{feature.reach} affected users</span>
          <span>·</span>
          <span>{feature.effort}w effort</span>
        </div>
      </div>

      <PrdWorkspace projectId={projectId} featureId={fid} initialPrds={prds} />
    </div>
  );
}
