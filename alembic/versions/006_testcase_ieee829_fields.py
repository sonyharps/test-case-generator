"""Add IEEE 829 fields to test_cases (priority, module, test_data, postconditions)

Revision ID: 006
Revises: 005
Create Date: 2026-08-21

The V8 pipeline generates IEEE 829 / ISTQB test cases with priority,
module, test_data and postconditions. These were previously dropped when
persisting to the DB (the model lacked columns), so session exports
rendered empty columns.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

_COLUMNS = [
    ("priority", "VARCHAR(4)"),
    ("module", "VARCHAR(200)"),
    ("test_data", "JSON"),
    ("postconditions", "JSON"),
]


def upgrade() -> None:
    for col_name, col_sql_type in _COLUMNS:
        op.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'test_cases' AND column_name = '{col_name}'
                ) THEN
                    ALTER TABLE test_cases ADD COLUMN {col_name} {col_sql_type};
                END IF;
            END$$
        """)


def downgrade() -> None:
    for col_name, _ in _COLUMNS:
        op.execute(f"ALTER TABLE test_cases DROP COLUMN IF EXISTS {col_name}")
