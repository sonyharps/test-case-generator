"""Phase 2 collaboration features

Revision ID: 003
Revises: 002
Create Date: 2026-01-04

Adds:
- Test case approval workflow (status, approved_by, approved_at)
- Test case editing tracking (edited_by, edited_at, edit_count)
- Comments system for test cases
- Email notifications system
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add approval workflow columns to test_cases table
    op.add_column('test_cases', sa.Column('status', sa.String(20), server_default='draft', nullable=False))
    op.add_column('test_cases', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('test_cases', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('test_cases', sa.Column('rejection_reason', sa.Text(), nullable=True))

    # Add editing tracking columns to test_cases table
    op.add_column('test_cases', sa.Column('edited_by', sa.Integer(), nullable=True))
    op.add_column('test_cases', sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('test_cases', sa.Column('edit_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('test_cases', sa.Column('original_content', postgresql.JSON(), nullable=True))

    # Create foreign keys for approval and editing
    op.create_foreign_key('fk_test_cases_approved_by', 'test_cases', 'users', ['approved_by'], ['id'])
    op.create_foreign_key('fk_test_cases_edited_by', 'test_cases', 'users', ['edited_by'], ['id'])

    # Create index on status for filtering
    op.create_index('ix_test_cases_status', 'test_cases', ['status'])

    # Create test_case_comments table
    op.create_table(
        'test_case_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),  # For threaded comments
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['test_case_comments.id'], ondelete='CASCADE')
    )
    op.create_index('ix_test_case_comments_id', 'test_case_comments', ['id'])
    op.create_index('ix_test_case_comments_test_case_id', 'test_case_comments', ['test_case_id'])
    op.create_index('ix_test_case_comments_user_id', 'test_case_comments', ['user_id'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),  # 'generation_complete', 'comment_added', 'approval_requested'
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_session_id', sa.String(36), nullable=True),
        sa.Column('related_test_case_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('is_emailed', sa.Boolean(), default=False),
        sa.Column('emailed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_test_case_id'], ['test_cases.id'], ondelete='SET NULL')
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    # Drop notifications table
    op.drop_index('ix_notifications_created_at', 'notifications')
    op.drop_index('ix_notifications_is_read', 'notifications')
    op.drop_index('ix_notifications_user_id', 'notifications')
    op.drop_index('ix_notifications_id', 'notifications')
    op.drop_table('notifications')

    # Drop test_case_comments table
    op.drop_index('ix_test_case_comments_user_id', 'test_case_comments')
    op.drop_index('ix_test_case_comments_test_case_id', 'test_case_comments')
    op.drop_index('ix_test_case_comments_id', 'test_case_comments')
    op.drop_table('test_case_comments')

    # Remove columns from test_cases table
    op.drop_index('ix_test_cases_status', 'test_cases')
    op.drop_constraint('fk_test_cases_edited_by', 'test_cases', type_='foreignkey')
    op.drop_constraint('fk_test_cases_approved_by', 'test_cases', type_='foreignkey')

    op.drop_column('test_cases', 'original_content')
    op.drop_column('test_cases', 'edit_count')
    op.drop_column('test_cases', 'edited_at')
    op.drop_column('test_cases', 'edited_by')
    op.drop_column('test_cases', 'rejection_reason')
    op.drop_column('test_cases', 'approved_at')
    op.drop_column('test_cases', 'approved_by')
    op.drop_column('test_cases', 'status')
