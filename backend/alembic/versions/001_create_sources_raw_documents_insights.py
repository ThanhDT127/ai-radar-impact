"""create sources raw_documents insights

Revision ID: 001
Revises:
Create Date: 2026-05-04 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- sources ---
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("feed_url", sa.Text(), nullable=True),
        sa.Column("trust_tier", sa.String(20), nullable=False),
        sa.Column("topics", postgresql.ARRAY(sa.String()), nullable=True, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- raw_documents ---
    op.create_table(
        "raw_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("normalized_content", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint"),
    )
    op.create_index("idx_raw_documents_source_id", "raw_documents", ["source_id"])
    op.create_index("idx_raw_documents_fingerprint", "raw_documents", ["fingerprint"])

    # --- insights ---
    op.create_table(
        "insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("raw_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary_short", sa.String(300), nullable=True),
        sa.Column("summary_medium", sa.Text(), nullable=True),
        sa.Column("topics", postgresql.ARRAY(sa.String()), nullable=True, server_default="{}"),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("nature", sa.String(50), nullable=True),
        sa.Column("trust_score", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("impact_label", sa.String(20), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="published"),
        sa.Column("ai_raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_insights_created_at", "insights", ["created_at"], postgresql_using="btree")


def downgrade() -> None:
    op.drop_index("idx_insights_created_at", table_name="insights")
    op.drop_table("insights")
    op.drop_index("idx_raw_documents_fingerprint", table_name="raw_documents")
    op.drop_index("idx_raw_documents_source_id", table_name="raw_documents")
    op.drop_table("raw_documents")
    op.drop_table("sources")
