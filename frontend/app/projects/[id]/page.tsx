import Link from 'next/link';
import { api, type Project, type ProjectStats } from '@/lib/api';
import StepProgress from '@/components/step-progress';
import RunPipelineButton from './_run-pipeline-button';
import ChatPanel from '@/components/chat-panel';

export default async function ProjectDashboard({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);

  const [project, stats] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<ProjectStats>(`/api/projects/${projectId}/stats`),
  ]);

  const steps = [
    { key: 'upload', label: 'Upload feedback', href: `/projects/${projectId}/upload`, done: stats.feedback_count > 0 },
    { key: 'cluster', label: 'Cluster & sentiment', href: `/projects/${projectId}/feedback`, done: stats.cluster_count > 0 },
    { key: 'rice', label: 'Prioritize (RICE)', href: `/projects/${projectId}/prioritization`, done: stats.feature_count > 0 },
    { key: 'strategy', label: 'Strategy', href: `/projects/${projectId}/strategy`, done: stats.feature_count > 0 },
    { key: 'prd', label: 'PRDs', href: `/projects/${projectId}/prioritization`, done: stats.prd_count > 0 },
    { key: 'roadmap', label: 'Roadmap', href: `/projects/${projectId}/roadmap`, done: stats.roadmap_item_count > 0 },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <Link href="/projects" className="text-xs muted hover:text-text">← Projects</Link>
          <h1 className="h1 mt-1">{project.name}</h1>
          {project.description && <p className="muted text-sm mt-1 max-w-2xl">{project.description}</p>}
        </div>
        <div className="flex gap-2">
          <Link href={`/projects/${projectId}/upload`} className="btn">Add feedback</Link>
          <RunPipelineButton projectId={projectId} />
        </div>
      </div>

      <StepProgress steps={steps} />

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Stat label="Feedback" value={stats.feedback_count} href={`/projects/${projectId}/feedback`} />
        <Stat label="Clusters" value={stats.cluster_count} href={`/projects/${projectId}/feedback`} />
        <Stat label="Features" value={stats.feature_count} href={`/projects/${projectId}/prioritization`} />
        <Stat label="PRDs" value={stats.prd_count} href={`/projects/${projectId}/prioritization`} />
        <Stat label="Roadmap items" value={stats.roadmap_item_count} href={`/projects/${projectId}/roadmap`} />
      </div>

      <ChatPanel projectId={projectId} />
    </div>
  );
}

function Stat({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link href={href} className="card card-hover p-4 block">
      <div className="label">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </Link>
  );
}
