"""Enable RLS on alembic_version

Revision ID: 73f105e41782
Revises: f615b9d9090c
Create Date: 2026-02-18 17:20:48.339635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73f105e41782'
down_revision = 'f615b9d9090c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;")


def downgrade():
    op.execute("ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY;")
