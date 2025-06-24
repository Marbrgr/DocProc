"""add_ai_analysis_fields_and_document_type_enum

Revision ID: 12ac9c8bd490
Revises: ac44fca20d73
Create Date: 2025-06-24 14:36:51.863097

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '12ac9c8bd490'  # ← Changed this line!
down_revision = 'ac44fca20d73'
branch_labels = None
depends_on = None

def upgrade():
    # First, create the enum type
    op.execute("CREATE TYPE documenttype AS ENUM ('INVOICE', 'CONTRACT', 'RECEIPT', 'FORM', 'LETTER', 'REPORT', 'OTHER', 'UNKNOWN')")
    
    # Now add the columns that use the enum
    op.add_column('documents', sa.Column('ai_document_type', postgresql.ENUM('INVOICE', 'CONTRACT', 'RECEIPT', 'FORM', 'LETTER', 'REPORT', 'OTHER', 'UNKNOWN', name='documenttype'), nullable=True))
    op.add_column('documents', sa.Column('ai_confidence', sa.Float(), nullable=True))
    op.add_column('documents', sa.Column('ai_key_information', postgresql.JSON(), nullable=True))
    op.add_column('documents', sa.Column('ai_analysis_method', sa.String(length=50), nullable=True))
    op.add_column('documents', sa.Column('ai_model_used', sa.String(length=100), nullable=True))

def downgrade():
    # Remove the columns first
    op.drop_column('documents', 'ai_model_used')
    op.drop_column('documents', 'ai_analysis_method')
    op.drop_column('documents', 'ai_key_information')
    op.drop_column('documents', 'ai_confidence')
    op.drop_column('documents', 'ai_document_type')
    
    # Then drop the enum type
    op.execute("DROP TYPE documenttype")