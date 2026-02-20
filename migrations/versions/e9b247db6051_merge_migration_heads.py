"""Merge migration heads

Revision ID: e9b247db6051
Revises: 73f105e41782, a1b2c3d4e5f6
Create Date: 2026-02-20 16:31:50.613072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9b247db6051'
down_revision = ('73f105e41782', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
