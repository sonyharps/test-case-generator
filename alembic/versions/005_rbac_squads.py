"""RBAC: squads table, userrole enum, role & squad_id columns

Revision ID: 005
Revises: 004
Create Date: 2026-08-04

Adds:
- squads table (name, description, timestamps)
- userrole PG enum type (admin, kabag, qa_lead, qa_staff)
- users.role column (NOT NULL, default qa_staff)
- users.squad_id column (nullable, FK to squads.id)

Idempotent: the role/squad_id columns may already exist in the live DB
(they were added to the model before this migration existed), so we use
DO blocks / IF NOT EXISTS guards.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create squads table (idempotent)
    op.execute("""
        CREATE TABLE IF NOT EXISTS squads (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_squads_name ON squads (name)")

    # 2. Create userrole enum type (idempotent)
    # Use a DO block so we don't error if the type already exists.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('admin', 'kabag', 'qa_lead', 'qa_staff');
            END IF;
        END$$
    """)

    # 3. Add users.role column if missing (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'role'
            ) THEN
                ALTER TABLE users
                    ADD COLUMN role userrole NOT NULL DEFAULT 'qa_staff';
            END IF;
        END$$
    """)
    # Ensure default is set even if column pre-existed
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'qa_staff'")

    # Backfill any NULL roles (safety)
    op.execute("UPDATE users SET role = 'qa_staff' WHERE role IS NULL")

    # 4. Add users.squad_id column + FK if missing (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'squad_id'
            ) THEN
                ALTER TABLE users ADD COLUMN squad_id INTEGER;
            END IF;
        END$$
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_squad_id ON users (squad_id)")

    # Add FK constraint (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_squad_id'
            ) THEN
                ALTER TABLE users
                    ADD CONSTRAINT fk_users_squad_id
                    FOREIGN KEY (squad_id) REFERENCES squads(id);
            END IF;
        END$$
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_squad_id")
    op.execute("DROP INDEX IF EXISTS ix_users_squad_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS squad_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TABLE IF EXISTS squads")
