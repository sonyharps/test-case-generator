"""Add orchestrator_sessions.drive_file_link (Google Drive export)

Revision ID: 008
Revises: 007
Create Date: 2026-09-06

Stores the webViewLink of the .xlsx uploaded to the QA shared drive, so the
Riwayat page can link straight to the Drive file.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'orchestrator_sessions'
                  AND column_name = 'drive_file_link'
            ) THEN
                ALTER TABLE orchestrator_sessions
                    ADD COLUMN drive_file_link varchar(512);
            END IF;
        END$$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS drive_file_link")
