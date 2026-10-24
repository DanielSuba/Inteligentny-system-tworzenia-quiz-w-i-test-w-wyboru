"""quizy pytania media

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-01 17:28:53.721106
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# tabele quizow, pytan, odpowiedzi i mediow (etap 2)
def upgrade() -> None:
    op.create_table(
        "media",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("source", sa.String(length=8), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=True),
        sa.Column("youtube_id", sa.String(length=16), nullable=True),
        sa.Column("start_s", sa.Integer(), nullable=True),
        sa.Column("end_s", sa.Integer(), nullable=True),
        sa.Column("mime", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_owner_id"), "media", ["owner_id"], unique=False)
    op.create_table(
        "quizzes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=1000), server_default="", nullable=False),
        sa.Column("language", sa.String(length=2), server_default="pl", nullable=False),
        sa.Column("visibility", sa.String(length=10), server_default="private", nullable=False),
        sa.Column("share_token", sa.String(length=32), nullable=False),
        sa.Column("cover_media_id", sa.Uuid(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String(length=30)), server_default="{}", nullable=False),
        sa.Column("origin_quiz_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cover_media_id"], ["media.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["origin_quiz_id"], ["quizzes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_token"),
    )
    op.create_index(op.f("ix_quizzes_owner_id"), "quizzes", ["owner_id"], unique=False)
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("quiz_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=12), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("explanation", sa.String(length=1000), server_default="", nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), server_default="2", nullable=False),
        sa.Column("time_limit_s", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("media_id", sa.Uuid(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("origin", sa.String(length=8), server_default="manual", nullable=False),
        sa.Column("generation_job_id", sa.Uuid(), nullable=True),
        sa.Column("source_chunk_id", sa.Uuid(), nullable=True),
        sa.Column("source_quote", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_quiz_id"), "questions", ["quiz_id"], unique=False)
    op.create_table(
        "answer_options",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=200), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_answer_options_question_id"), "answer_options", ["question_id"], unique=False)
    op.create_table(
        "open_answers",
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("accepted", sa.ARRAY(sa.String(length=200)), nullable=False),
        sa.Column("fuzzy_threshold", sa.SmallInteger(), nullable=False),
        sa.Column("case_sensitive", sa.Boolean(), nullable=False),
        sa.Column("ignore_accents", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("question_id"),
    )


def downgrade() -> None:
    op.drop_table("open_answers")
    op.drop_index(op.f("ix_answer_options_question_id"), table_name="answer_options")
    op.drop_table("answer_options")
    op.drop_index(op.f("ix_questions_quiz_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_quizzes_owner_id"), table_name="quizzes")
    op.drop_table("quizzes")
    op.drop_index(op.f("ix_media_owner_id"), table_name="media")
    op.drop_table("media")
