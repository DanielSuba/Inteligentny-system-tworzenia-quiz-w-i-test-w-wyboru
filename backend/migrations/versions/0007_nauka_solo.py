"""nauka solo

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-12 16:54:36.304395
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# nauka solo: postep w pytaniach (pudelka Leitnera) i sesje nauki (etap 5)
def upgrade() -> None:
    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("quiz_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answered", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("current_question_id", sa.Uuid(), nullable=True),
        sa.Column("recent", sa.ARRAY(sa.Uuid()), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_learning_sessions_quiz_id"), "learning_sessions", ["quiz_id"], unique=False)
    op.create_index(op.f("ix_learning_sessions_user_id"), "learning_sessions", ["user_id"], unique=False)
    op.create_table(
        "learning_progress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("box", sa.SmallInteger(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_result", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "question_id"),
    )
    op.create_index(
        op.f("ix_learning_progress_question_id"), "learning_progress", ["question_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_progress_question_id"), table_name="learning_progress")
    op.drop_table("learning_progress")
    op.drop_index(op.f("ix_learning_sessions_user_id"), table_name="learning_sessions")
    op.drop_index(op.f("ix_learning_sessions_quiz_id"), table_name="learning_sessions")
    op.drop_table("learning_sessions")
