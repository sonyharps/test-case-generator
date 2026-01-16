"""Test Runs & Execution

Revision ID: 006
Revises: 005
Create Date: 2026-01-15

Adds:
- Milestones table for project milestones
- Test runs table for test execution sessions
- Test results table for tracking test execution results
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # Create milestones table
    # ========================================
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_milestones_id', 'milestones', ['id'])
    op.create_index('ix_milestones_project_id', 'milestones', ['project_id'])
    op.create_index('ix_milestones_is_completed', 'milestones', ['is_completed'])
    op.create_foreign_key('fk_milestones_project', 'milestones', 'projects', ['project_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_milestones_created_by', 'milestones', 'users', ['created_by_id'], ['id'])

    # ========================================
    # Create test_runs table
    # ========================================
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum(
            'planned', 'in_progress', 'completed', 'cancelled',
            name='testrunstatus'
        ), default='planned', nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('completed_by_id', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('include_all', sa.Boolean(), default=False, nullable=False),
        sa.Column('included_case_ids', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_runs_id', 'test_runs', ['id'])
    op.create_index('ix_test_runs_project_id', 'test_runs', ['project_id'])
    op.create_index('ix_test_runs_milestone_id', 'test_runs', ['milestone_id'])
    op.create_index('ix_test_runs_status', 'test_runs', ['status'])
    op.create_foreign_key('fk_test_runs_project', 'test_runs', 'projects', ['project_id'], ['id'])
    op.create_foreign_key('fk_test_runs_milestone', 'test_runs', 'milestones', ['milestone_id'], ['id'])
    op.create_foreign_key('fk_test_runs_created_by', 'test_runs', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_test_runs_completed_by', 'test_runs', 'users', ['completed_by_id'], ['id'])

    # ========================================
    # Create test_results table
    # ========================================
    op.create_table(
        'test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_run_id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum(
            'passed', 'failed', 'blocked', 'skipped', 'retest', 'pending',
            name='testresultstatus'
        ), default='pending', nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('actual_result', sa.Text(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('defects', postgresql.JSON(), nullable=True),
        sa.Column('execution_seconds', sa.Integer(), nullable=True),
        sa.Column('screenshots', postgresql.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_results_id', 'test_results', ['id'])
    op.create_index('ix_test_results_test_run_id', 'test_results', ['test_run_id'])
    op.create_index('ix_test_results_test_case_id', 'test_results', ['test_case_id'])
    op.create_index('ix_test_results_status', 'test_results', ['status'])
    op.create_foreign_key('fk_test_results_test_run', 'test_results', 'test_runs', ['test_run_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_test_results_test_case', 'test_results', 'repository_test_cases', ['test_case_id'], ['id'])
    op.create_foreign_key('fk_test_results_assigned_to', 'test_results', 'users', ['assigned_to_id'], ['id'])
    op.create_foreign_key('fk_test_results_executed_by', 'test_results', 'users', ['executed_by_id'], ['id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('test_results')
    op.drop_table('test_runs')
    op.drop_table('milestones')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS testresultstatus')
    op.execute('DROP TYPE IF EXISTS testrunstatus')
