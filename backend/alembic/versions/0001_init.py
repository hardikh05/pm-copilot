"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBED_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "clusters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("positive_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("neutral_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("negative_pct", sa.Float, nullable=False, server_default="0"),
        sa.Column("avg_sentiment", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "feedback_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("user_segment", sa.String(80), nullable=True),
        sa.Column("author", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("cluster_id", sa.Integer, sa.ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True),
    )

    op.create_table(
        "features",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("cluster_id", sa.Integer, sa.ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("reach", sa.Integer, nullable=False, server_default="0"),
        sa.Column("impact", sa.Float, nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("effort", sa.Float, nullable=False, server_default="1"),
        sa.Column("effort_overridden", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("rice_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("strategy_bucket", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "prds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("feature_id", sa.Integer, sa.ForeignKey("features.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("source_feedback_ids", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "critique_notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("prd_id", sa.Integer, sa.ForeignKey("prds.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("section", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("suggestion", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("feature_id", sa.Integer, sa.ForeignKey("features.id", ondelete="CASCADE"), nullable=False),
        sa.Column("horizon", sa.String(20), nullable=False),
        sa.Column("theme", sa.String(120), nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("depends_on", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("estimated_weeks", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("triggered_agent", sa.String(50), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("roadmap_items")
    op.drop_table("critique_notes")
    op.drop_table("prds")
    op.drop_table("features")
    op.drop_table("feedback_items")
    op.drop_table("clusters")
    op.drop_table("projects")
