"""Fix TestCaseStatus enum values to lowercase

Revision ID: 004
Revises: 003
Create Date: 2026-01-04

Fixes enum case mismatch - changes DRAFT/APPROVED/REJECTED to draft/approved/rejected
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the enum type constraint if it exists and convert to varchar
    # This avoids the enum case sensitivity issue

    # First, update any existing values (though there shouldn't be any yet)
    op.execute("""
        UPDATE test_cases
        SET status = LOWER(status)
        WHERE status IN ('DRAFT', 'APPROVED', 'REJECTED')
    """)

    # Drop the enum type if it exists (PostgreSQL specific)
    op.execute("DROP TYPE IF EXISTS testcasestatus CASCADE")

    # The column is already String(20), so no schema change needed
    # Just ensure the default is lowercase
    op.execute("ALTER TABLE test_cases ALTER COLUMN status SET DEFAULT 'draft'")


def downgrade() -> None:
    # Revert to uppercase
    op.execute("""
        UPDATE test_cases
        SET status = UPPER(status)
        WHERE status IN ('draft', 'approved', 'rejected')
    """)

    op.execute("ALTER TABLE test_cases ALTER COLUMN status SET DEFAULT 'DRAFT'")
