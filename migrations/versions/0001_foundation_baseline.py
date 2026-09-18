"""Infrastructure-only migration baseline.

Revision ID: 0001_foundation_baseline
Revises:
Create Date: 2026-09-16

This revision intentionally creates no product tables or domain entities. It
establishes the immutable Alembic baseline for the generic starter. Future
challenge-specific schema changes must use new revisions that depend on it;
do not edit this revision after it is merged.
"""

from typing import Sequence, Union

revision: str = "0001_foundation_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Establish the versioned migration baseline without adding schema."""


def downgrade() -> None:
    """Return to an unversioned, schema-free database."""
