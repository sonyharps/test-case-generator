"""Add uploaded_documents table

Revision ID: 002
Revises: 001
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create uploaded_documents table
    op.create_table(
        'uploaded_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_type', sa.Enum('pdf', 'docx', 'md', 'txt', 'figma', 'jira', 'linear', name='documenttype'), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('file_path', sa.String(1000)),
        sa.Column('source_url', sa.String(1000)),
        sa.Column('processing_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='processingstatus'), server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('title', sa.String(500)),
        sa.Column('content_preview', sa.Text()),
        sa.Column('full_text', sa.Text()),
        sa.Column('sections', postgresql.JSON()),
        sa.Column('extracted_requirements', postgresql.JSON()),
        sa.Column('chunk_count', sa.Integer(), server_default='0'),
        sa.Column('qdrant_collection', sa.String(100), server_default='documents'),
        sa.Column('qdrant_point_ids', postgresql.JSON()),
        sa.Column('requirement_count', sa.Integer(), server_default='0'),
        sa.Column('test_case_count', sa.Integer(), server_default='0'),
        sa.Column('doc_metadata', postgresql.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index('ix_uploaded_documents_id', 'uploaded_documents', ['id'])
    op.create_index('ix_uploaded_documents_user_id', 'uploaded_documents', ['user_id'])
    op.create_index('ix_uploaded_documents_processing_status', 'uploaded_documents', ['processing_status'])
    op.create_index('ix_uploaded_documents_file_type', 'uploaded_documents', ['file_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_uploaded_documents_file_type', 'uploaded_documents')
    op.drop_index('ix_uploaded_documents_processing_status', 'uploaded_documents')
    op.drop_index('ix_uploaded_documents_user_id', 'uploaded_documents')
    op.drop_index('ix_uploaded_documents_id', 'uploaded_documents')

    # Drop table
    op.drop_table('uploaded_documents')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS documenttype')
    op.execute('DROP TYPE IF EXISTS processingstatus')
