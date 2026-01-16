"""rename_screenshots_to_evidence

Revision ID: 555462243bf4
Revises: 006
Create Date: 2026-01-15 22:27:09.581052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '555462243bf4'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the screenshots column to evidence in test_results table
    op.alter_column('test_results', 'screenshots', new_column_name='evidence')


def downgrade() -> None:
    # Rename back to screenshots
    op.alter_column('test_results', 'evidence', new_column_name='screenshots')
