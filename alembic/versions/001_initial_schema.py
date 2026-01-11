"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create orchestrator_sessions table
    op.create_table(
        'orchestrator_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('generate_boundary', sa.Boolean(), default=True),
        sa.Column('include_risk', sa.Boolean(), default=True),
        sa.Column('summary', postgresql.JSON()),
        sa.Column('coverage_matrix', postgresql.JSON()),
        sa.Column('risk_assessment', postgresql.JSON()),
        sa.Column('session_metadata', postgresql.JSON()),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orchestrator_sessions_id', 'orchestrator_sessions', ['id'])
    op.create_index('ix_orchestrator_sessions_session_id', 'orchestrator_sessions', ['session_id'], unique=True)

    # Create test_cases table
    op.create_table(
        'test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tc_id', sa.String(50), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('tc_type', sa.Enum('FUNCTIONAL', 'NEGATIVE', 'BOUNDARY', name='testcasetype'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('preconditions', postgresql.JSON()),
        sa.Column('steps', postgresql.JSON()),
        sa.Column('expected_result', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['orchestrator_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_cases_id', 'test_cases', ['id'])
    op.create_index('ix_test_cases_tc_id', 'test_cases', ['tc_id'])

    # Create requirements table
    op.create_table(
        'requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tags', sa.String(500)),
        sa.Column('is_template', sa.Boolean(), default=False),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_requirements_id', 'requirements', ['id'])

    # Create usage_analytics table
    op.create_table(
        'usage_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(100), nullable=False),
        sa.Column('model_used', sa.String(100)),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('test_cases_generated', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_usage_analytics_id', 'usage_analytics', ['id'])


def downgrade() -> None:
    op.drop_table('usage_analytics')
    op.drop_table('requirements')
    op.drop_table('test_cases')
    op.drop_table('orchestrator_sessions')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS testcasetype')
