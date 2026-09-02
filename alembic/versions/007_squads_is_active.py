"""Add squads.is_active (sync manual DB state into migrations)

Revision ID: 007
Revises: 006
Create Date: 2026-08-28

The squads table was originally created manually (pre-migration era) WITH an
is_active column; migration 005 recreated it WITHOUT the column. This drift
broke data restores. Align the schema: add is_active everywhere.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'squads' AND column_name = 'is_active'
            ) THEN
                ALTER TABLE squads
                    ADD COLUMN is_active boolean NOT NULL DEFAULT true;
            END IF;
        END$$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE squads DROP COLUMN IF EXISTS is_active")
