import Link from 'next/link';
import { api, type Feature, type Project, type Roadmap } from '@/lib/api';
import RoadmapBoard from '@/components/roadmap-board';

export default async function RoadmapPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const projectId = Number(id);
  const [project, roadmap, features] = await Promise.all([
    api<Project>(`/api/projects/${projectId}`),
    api<Roadmap>(`/api/projects/${projectId}/roadmap`),
    api<Feature[]>(`/api/projects/${projectId}/features`),
  ]);

  const featureMap = Object.fromEntries(features.map((f) => [f.id, f]));
  const hasAny = roadmap.now.length + roadmap.next.length + roadmap.later.length > 0;

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/projects/${projectId}`} className="text-xs muted hover:text-text">← {project.name}</Link>
        <h1 className="h1 mt-1">Roadmap</h1>
        <p className="muted text-sm mt-1">
          Capacity budget: {roadmap.capacity_weeks_per_horizon}w per horizon.
          {roadmap.themes.length > 0 && (
            <> · Themes: {roadmap.themes.map((t) => (
              <span key={t} className="badge ml-1">{t}</span>
            ))}</>
          )}
        </p>
      </div>

      {!hasAny ? (
        <div className="card p-8 text-center muted text-sm">
          Roadmap is empty. Run the pipeline from the project dashboard.
        </div>
      ) : (
        <RoadmapBoard projectId={projectId} roadmap={roadmap} featureMap={featureMap} />
      )}
    </div>
  );
}
