"""materialy generowanie media

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02 22:03:36.936583
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# materialy, generowanie AI, recenzja; kadr i zrodla muzyki w media (etap 4)
def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("mime", sa.String(length=100), server_default="", nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_documents_owner_id"), "source_documents", ["owner_id"], unique=False)
    op.create_table(
        "source_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_chunks_document_id"), "source_chunks", ["document_id"], unique=False)
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("quiz_id", sa.Uuid(), nullable=False),
        sa.Column("source_mode", sa.String(length=8), nullable=False),
        sa.Column("strategy", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("actual_provider", sa.String(length=60), nullable=True),
        sa.Column("key_source", sa.String(length=8), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("document_ids", sa.ARRAY(sa.Uuid()), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("retries", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generation_jobs_quiz_id"), "generation_jobs", ["quiz_id"], unique=False)
    op.create_index(op.f("ix_generation_jobs_user_id"), "generation_jobs", ["user_id"], unique=False)
    op.create_table(
        "generated_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=True),
        sa.Column("raw_output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("parsed", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("grounded", sa.Boolean(), nullable=True),
        sa.Column("grounding_score", sa.Float(), nullable=True),
        sa.Column("duplicate_of", sa.String(length=500), nullable=True),
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["source_chunks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_questions_job_id"), "generated_questions", ["job_id"], unique=False)
    op.create_table(
        "question_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("generated_question_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("final", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("edit_distance", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["generated_question_id"], ["generated_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_reviews_generated_question_id"),
        "question_reviews",
        ["generated_question_id"],
        unique=False,
    )
    op.add_column("media", sa.Column("embed_id", sa.String(length=80), nullable=True))
    op.add_column("media", sa.Column("crop", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("media", sa.Column("display_width", sa.Integer(), nullable=True))
    op.add_column("media", sa.Column("hide_video", sa.Boolean(), server_default="false", nullable=False))
    op.alter_column(
        "media",
        "source",
        existing_type=sa.VARCHAR(length=8),
        type_=sa.String(length=10),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "media",
        "source",
        existing_type=sa.String(length=10),
        type_=sa.VARCHAR(length=8),
        existing_nullable=False,
    )
    op.drop_column("media", "hide_video")
    op.drop_column("media", "display_width")
    op.drop_column("media", "crop")
    op.drop_column("media", "embed_id")
    op.drop_index(op.f("ix_question_reviews_generated_question_id"), table_name="question_reviews")
    op.drop_table("question_reviews")
    op.drop_index(op.f("ix_generated_questions_job_id"), table_name="generated_questions")
    op.drop_table("generated_questions")
    op.drop_index(op.f("ix_generation_jobs_user_id"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_quiz_id"), table_name="generation_jobs")
    op.drop_table("generation_jobs")
    op.drop_index(op.f("ix_source_chunks_document_id"), table_name="source_chunks")
    op.drop_table("source_chunks")
    op.drop_index(op.f("ix_source_documents_owner_id"), table_name="source_documents")
    op.drop_table("source_documents")
