"""Add report_id and metadata fields to Report model

Revision ID: 59dd16e7eabf
Revises: 
Create Date: 2026-02-17 16:05:18.698887

"""
from alembic import op
import sqlalchemy as sa
import random


# revision identifiers, used by Alembic.
revision = '59dd16e7eabf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add report_id as nullable first to handle existing rows
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('report_id', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('age', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('gender', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('doctor_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('test_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('test_results_json', sa.Text(), nullable=True))

    # Backfill existing rows with unique report_id values
    conn = op.get_bind()
    results = conn.execute(sa.text("SELECT id FROM reports WHERE report_id IS NULL"))
    for row in results:
        rid = f"RID{random.randint(100000, 999999)}"
        conn.execute(sa.text("UPDATE reports SET report_id = :rid WHERE id = :id"), {"rid": rid, "id": row[0]})

    # Now make report_id non-nullable and add constraints
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.alter_column('report_id', nullable=False)
        batch_op.create_unique_constraint('uq_reports_report_id', ['report_id'])
        batch_op.create_foreign_key('fk_reports_user_id', 'users', ['user_id'], ['id'])


def downgrade():
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_constraint('fk_reports_user_id', type_='foreignkey')
        batch_op.drop_constraint('uq_reports_report_id', type_='unique')
        batch_op.drop_column('test_results_json')
        batch_op.drop_column('test_name')
        batch_op.drop_column('doctor_name')
        batch_op.drop_column('gender')
        batch_op.drop_column('age')
        batch_op.drop_column('user_id')
        batch_op.drop_column('report_id')
