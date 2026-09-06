"""Projects table + squads.project_id + project stamps on sessions/documents

Revision ID: 010
Revises: 009
Create Date: 2026-09-06

A QA's project is determined by their squad (squads.project_id). Sessions and
documents get their project stamped at creation time so history survives
later remapping. Existing rows stay NULL = "(Tanpa proyek)".
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'projects'
            ) THEN
                CREATE TABLE projects (
                    id serial PRIMARY KEY,
                    name varchar(120) NOT NULL UNIQUE,
                    code varchar(30) UNIQUE,
                    description text,
                    is_active boolean NOT NULL DEFAULT true,
                    created_at timestamp DEFAULT now(),
                    updated_at timestamp DEFAULT now()
                );
                CREATE INDEX ix_projects_id ON projects (id);
                CREATE INDEX ix_projects_name ON projects (name);
            END IF;
        END$$
    """)
    conn = op.get_bind()

    def add_col(table: str, col: str, ddl: str):
        exists = conn.execute(sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ), {"t": table, "c": col}).scalar()
        if not exists:
            op.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")

    add_col("squads", "project_id", "integer REFERENCES projects(id)")
    add_col("orchestrator_sessions", "project_id", "integer REFERENCES projects(id)")
    add_col("uploaded_documents", "project_id", "integer REFERENCES projects(id)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_squads_project_id ON squads (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sessions_project_id ON orchestrator_sessions (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_project_id ON uploaded_documents (project_id)")


def downgrade() -> None:
    op.execute("ALTER TABLE squads DROP COLUMN IF EXISTS project_id")
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS project_id")
    op.execute("ALTER TABLE uploaded_documents DROP COLUMN IF EXISTS project_id")
    op.execute("DROP TABLE IF EXISTS projects")
