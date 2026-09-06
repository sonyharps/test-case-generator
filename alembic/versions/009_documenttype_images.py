"""Add png/jpg/jpeg to documenttype enum (image/Figma mockup uploads)

Revision ID: 009
Revises: 008
Create Date: 2026-09-06

Users upload Figma exports / UI mockups alongside PRDs. The Python enums
(models, schemas, processing) gained PNG/JPG/JPEG; this syncs the native
Postgres enum. ALTER TYPE ADD VALUE cannot run inside a transaction block.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'png'")
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'jpg'")
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'jpeg'")


def downgrade() -> None:
    # Postgres cannot remove values from an enum — leave them in place.
    pass
