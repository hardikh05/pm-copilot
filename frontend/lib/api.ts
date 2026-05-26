// All API calls go through Next.js rewrite -> FastAPI.
// Server components fetch from absolute URL when running on the server.

const SERVER_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function url(path: string) {
  if (typeof window === 'undefined') return `${SERVER_API_URL}${path}`;
  return path;
}

export async function api<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    cache: 'no-store',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return null as T;
  return (await res.json()) as T;
}

export async function apiUpload<T = unknown>(path: string, form: FormData): Promise<T> {
  const res = await fetch(url(path), { method: 'POST', body: form, cache: 'no-store' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  return (await res.json()) as T;
}

// ----- Types -----

export type Project = {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
};

export type ProjectStats = {
  feedback_count: number;
  cluster_count: number;
  feature_count: number;
  prd_count: number;
  roadmap_item_count: number;
};

export type FeedbackItem = {
  id: number;
  text: string;
  source: string | null;
  rating: number | null;
  user_segment: string | null;
  author: string | null;
  created_at: string | null;
  sentiment: 'positive' | 'neutral' | 'negative' | null;
  sentiment_score: number | null;
  cluster_id: number | null;
};

export type Cluster = {
  id: number;
  label: string;
  summary: string | null;
  size: number;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  avg_sentiment: number;
};

export type ClusterDetail = Cluster & {
  sample_feedback: Array<{
    id: number;
    text: string;
    source: string | null;
    rating: number | null;
    sentiment: string | null;
    user_segment: string | null;
  }>;
};

export type Feature = {
  id: number;
  cluster_id: number | null;
  title: string;
  description: string | null;
  reach: number;
  impact: number;
  confidence: number;
  effort: number;
  effort_overridden: boolean;
  rice_score: number;
  rationale: string | null;
  strategy_bucket: 'quick_win' | 'bet' | 'risk' | null;
};

export type PRDContent = {
  problem: string;
  goal: string;
  user_stories: string[];
  success_metrics: string[];
  requirements: string[];
  edge_cases: string[];
  out_of_scope: string[];
};

export type PRD = {
  id: number;
  feature_id: number;
  version: number;
  content: PRDContent;
  source_feedback_ids: number[];
  status: 'draft' | 'accepted' | 'rejected';
  title: string | null;
  summary: string | null;
  created_at: string;
};

export type CritiqueNote = {
  id: number;
  prd_id: number;
  section: string;
  severity: 'low' | 'medium' | 'high';
  category: 'ambiguity' | 'missing_metric' | 'unclear_requirement' | 'untestable';
  message: string;
  suggestion: string | null;
  status: 'open' | 'accepted' | 'dismissed';
};

export type RoadmapItem = {
  id: number;
  feature_id: number;
  horizon: 'now' | 'next' | 'later';
  theme: string | null;
  order_index: number;
  depends_on: number[];
  estimated_weeks: number;
};

export type Roadmap = {
  now: RoadmapItem[];
  next: RoadmapItem[];
  later: RoadmapItem[];
  capacity_weeks_per_horizon: number;
  themes: string[];
};

export type ChatMessage = {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  triggered_agent: string | null;
};
