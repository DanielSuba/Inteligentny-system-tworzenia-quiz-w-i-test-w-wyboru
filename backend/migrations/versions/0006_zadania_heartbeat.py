"""zadania heartbeat

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-12 17:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# znak zycia zadania generowania (przerwane zadania nie wisza w stanie running)
def upgrade() -> None:
    op.add_column("generation_jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("generation_jobs", "heartbeat_at")
