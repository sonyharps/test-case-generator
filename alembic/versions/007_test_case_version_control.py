"""test_case_version_control

Revision ID: 007
Revises: 555462243bf4
Create Date: 2026-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '555462243bf4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_case_versions table using raw SQL to avoid enum issues
    op.execute("""
        CREATE TABLE test_case_versions (
            id SERIAL PRIMARY KEY,
            test_case_id INTEGER NOT NULL REFERENCES repository_test_cases(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            title VARCHAR(500) NOT NULL,
            description TEXT,
            tc_type VARCHAR(50) NOT NULL,
            priority VARCHAR(50) NOT NULL,
            automation_status VARCHAR(50) NOT NULL,
            estimated_minutes INTEGER,
            preconditions JSONB,
            steps JSONB,
            expected_result TEXT,
            tags JSONB,
            custom_fields JSONB,
            change_summary TEXT,
            changed_by_id INTEGER REFERENCES users(id),
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX ix_test_case_versions_test_case_id ON test_case_versions(test_case_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_test_case_versions_test_case_id")
    op.execute("DROP TABLE IF EXISTS test_case_versions")
