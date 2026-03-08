"""create all tables

Revision ID: 0001_create_all
Revises: 
Create Date: 2026-03-08 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0001_create_all'
down_revision = None
branch_labels = None
depend_on = None


def upgrade():
    # Use SQLAlchemy's metadata to create all tables
    bind = op.get_bind()
    try:
        from backend.database.models import Base
        Base.metadata.create_all(bind=bind)
    except Exception:
        # If import fails, raise to make migration visible
        raise


def downgrade():
    bind = op.get_bind()
    try:
        from backend.database.models import Base
        Base.metadata.drop_all(bind=bind)
    except Exception:
        raise
