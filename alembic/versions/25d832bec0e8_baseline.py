"""baseline

Revision ID: 25d832bec0e8
Revises:
Create Date: 2026-04-19 21:47:30.993231

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "25d832bec0e8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
