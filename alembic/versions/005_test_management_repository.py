"""Test Management / Repository

Revision ID: 005
Revises: 004
Create Date: 2026-01-15

Adds:
- Projects table for organizing test work
- Test suites table for hierarchical test case organization
- Repository test cases table for reusable test cases
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # Create projects table
    # ========================================
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_id', 'projects', ['id'])
    op.create_index('ix_projects_name', 'projects', ['name'])
    op.create_foreign_key('fk_projects_created_by', 'projects', 'users', ['created_by_id'], ['id'])

    # ========================================
    # Create test_suites table
    # ========================================
    op.create_table(
        'test_suites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), default=0, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_suites_id', 'test_suites', ['id'])
    op.create_index('ix_test_suites_project_id', 'test_suites', ['project_id'])
    op.create_index('ix_test_suites_parent_id', 'test_suites', ['parent_id'])
    op.create_foreign_key('fk_test_suites_project', 'test_suites', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_test_suites_parent', 'test_suites', 'test_suites', ['parent_id'], ['id'])
    op.create_foreign_key('fk_test_suites_created_by', 'test_suites', 'users', ['created_by_id'], ['id'])

    # ========================================
    # Create repository_test_cases table
    # ========================================
    op.create_table(
        'repository_test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tc_type', sa.Enum(
            'functional', 'negative', 'boundary', 'ui', 'api', 'integration',
            'performance', 'security', 'usability', 'other',
            name='repositorytestcasetype'
        ), default='functional', nullable=False),
        sa.Column('priority', sa.Enum(
            'critical', 'high', 'medium', 'low',
            name='priority'
        ), default='medium', nullable=False),
        sa.Column('automation_status', sa.Enum(
            'automated', 'manual', 'to_be_automated', 'none',
            name='automationstatus'
        ), default='manual', nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('preconditions', postgresql.JSON(), nullable=True),
        sa.Column('steps', postgresql.JSON(), nullable=True),
        sa.Column('expected_result', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(), nullable=True),
        sa.Column('position', sa.Integer(), default=0, nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('is_draft', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('source_session_id', sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_repository_test_cases_id', 'repository_test_cases', ['id'])
    op.create_index('ix_repository_test_cases_external_id', 'repository_test_cases', ['external_id'])
    op.create_index('ix_repository_test_cases_suite_id', 'repository_test_cases', ['suite_id'])
    op.create_index('ix_repository_test_cases_tc_type', 'repository_test_cases', ['tc_type'])
    op.create_index('ix_repository_test_cases_priority', 'repository_test_cases', ['priority'])
    op.create_foreign_key('fk_repo_test_cases_suite', 'repository_test_cases', 'test_suites', ['suite_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_repo_test_cases_created_by', 'repository_test_cases', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_repo_test_cases_updated_by', 'repository_test_cases', 'users', ['updated_by_id'], ['id'])


def downgrade() -> None:
    # Drop foreign keys and tables in reverse order
    op.drop_table('repository_test_cases')
    op.drop_table('test_suites')
    op.drop_table('projects')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS repositorytestcasetype')
    op.execute('DROP TYPE IF EXISTS priority')
    op.execute('DROP TYPE IF EXISTS automationstatus')
