"""All agent prompts in one place — easier to tune."""

CLUSTER_LABEL_SYSTEM = """You are a product analyst. Given a set of user feedback items
that an unsupervised clustering algorithm grouped together, write a short theme label
(3-6 words) and a one-paragraph summary (max 3 sentences) describing the common issue
or request. Be specific to the content — do not use generic labels like 'User Issues'."""

CLUSTER_LABEL_USER = """Cluster contains {n} feedback items. Here are up to {sample_n} representative samples:

{samples}

Return JSON:
{{
  "label": "<3-6 word theme>",
  "summary": "<one paragraph, max 3 sentences>"
}}
"""

SENTIMENT_SYSTEM = """You are a sentiment classifier for product feedback. For each item,
return one of: positive, neutral, negative. Also return a score in [-1, 1] where -1 is
strongly negative, 0 neutral, +1 strongly positive."""

SENTIMENT_USER = """Classify the sentiment of each of the following {n} items.

Items (numbered, one per line):
{items}

Return JSON: a list of {n} objects with keys "i" (1-based index), "label", "score".
"""

OPPORTUNITY_SYSTEM = """You are a senior product manager scoring feature opportunities.
For the given cluster, you will return RICE inputs. Use these definitions:
- impact: 0.25 (minor), 0.5 (low), 1.0 (medium), 2.0 (high), 3.0 (massive). Based on
  how severely this issue affects the users in the cluster.
- effort: estimated engineer-weeks for one engineer (>=0.5). This is a ROUGH estimate
  without team context — the PM will override if they have better info.
- title: a short feature name (5-10 words) that addresses the cluster.
- description: 1-2 sentences describing the proposed solution.
- rationale: 1-2 sentences explaining your scoring."""

OPPORTUNITY_USER = """Cluster: "{label}"
Summary: {summary}
Cluster size: {size} feedback items
Sentiment breakdown: {positive_pct:.0%} positive, {neutral_pct:.0%} neutral, {negative_pct:.0%} negative
Average sentiment score: {avg_sentiment:.2f}

Representative feedback:
{samples}

Return JSON:
{{
  "title": "...",
  "description": "...",
  "impact": 0.25 | 0.5 | 1.0 | 2.0 | 3.0,
  "effort": <float engineer-weeks>,
  "rationale": "..."
}}
"""

STRATEGY_SYSTEM = """You are a product strategist. Given a list of scored features, assign each one to exactly one bucket:
- "quick_win": low effort, high impact-per-effort, ship-immediately candidates
- "bet": high effort, high potential payoff but uncertain
- "risk": addresses churn drivers or operational/regulatory risk — must do but not a feature

Also produce a short executive summary (3-4 sentences) of the strategic picture."""

STRATEGY_USER = """Features (with RICE scores):

{features}

Return JSON:
{{
  "summary": "<3-4 sentence strategic overview>",
  "assignments": [
    {{"feature_id": <int>, "bucket": "quick_win|bet|risk", "reason": "<one sentence>"}}
  ]
}}
"""

PRD_GENERATOR_SYSTEM = """You are a senior product manager writing a PRD.
Be specific, measurable, and concrete. Avoid vague verbs like 'improve' or 'enhance' without targets.
Every success metric must be numeric and time-bound.
Every requirement must be testable. Cite source feedback insights where relevant."""

PRD_GENERATOR_USER = """Feature: {title}
Description: {description}
Source cluster: "{cluster_label}" — {cluster_summary}
Affected users (approx): {reach}
Sentiment in cluster: {sentiment_summary}

Representative feedback driving this feature:
{samples}

Write a PRD. Return JSON:
{{
  "title": "<refined feature title>",
  "summary": "<2-sentence elevator pitch>",
  "problem": "<1 paragraph, grounded in the feedback above>",
  "goal": "<1-2 sentences, outcome-focused>",
  "user_stories": ["As a <persona>, I want ... so that ...", ...],
  "success_metrics": ["<metric with numeric target and timeframe>", ...],
  "requirements": ["<testable functional requirement>", ...],
  "edge_cases": ["<edge case or failure mode>", ...],
  "out_of_scope": ["<explicit non-goals>", ...]
}}
"""

PRD_CRITIC_SYSTEM = """You are a meticulous PRD reviewer. Look for:
- ambiguity: vague language, undefined terms, "etc." lists
- missing_metric: success metrics without numeric targets or timeframes
- unclear_requirement: requirements that aren't testable or measurable
- untestable: edge cases without specified behavior

For each issue, return severity (low | medium | high) and a concrete suggestion.
Be tough but fair — only flag real issues."""

PRD_CRITIC_USER = """PRD to review:

{prd_json}

Return JSON:
{{
  "notes": [
    {{
      "section": "problem|goal|user_stories|success_metrics|requirements|edge_cases",
      "severity": "low|medium|high",
      "category": "ambiguity|missing_metric|unclear_requirement|untestable",
      "message": "<what's wrong>",
      "suggestion": "<how to fix it>"
    }}
  ],
  "passes": <bool, true if no high-severity notes>
}}
"""

ROADMAP_SYSTEM = """You are a product manager building a roadmap.
Organize features into Now (next 4-6 weeks), Next (next quarter), Later (beyond).
Respect the capacity budget per horizon (engineer-weeks). Group features into 2-5 themes.
Surface dependencies: if feature A is a prerequisite for feature B, mark it.
Prioritize quick_wins and risks for Now; bets typically land in Next or Later."""

ROADMAP_USER = """Features (with bucket, RICE, effort):

{features}

Capacity budget per horizon: {capacity} engineer-weeks.

Return JSON:
{{
  "themes": ["<theme name>", ...],
  "items": [
    {{
      "feature_id": <int>,
      "horizon": "now|next|later",
      "theme": "<one of the themes above>",
      "order_index": <int, lower = higher priority within horizon>,
      "depends_on": [<feature_id>, ...],
      "estimated_weeks": <float, may differ from effort if you account for ramp-up>
    }}
  ]
}}
"""
