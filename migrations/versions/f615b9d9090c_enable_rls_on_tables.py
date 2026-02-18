"""Enable RLS on tables

Revision ID: f615b9d9090c
Revises: 6a2c75806db5
Create Date: 2026-02-18 17:17:56.713097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f615b9d9090c'
down_revision = '6a2c75806db5'
branch_labels = None
depends_on = None


def upgrade():
    # Enable RLS on all tables to change "UNRESTRICTED" status to "SECURED" in Supabase
    tables = [
        'users', 'bookings', 'reports', 'test_categories', 'tests', 
        'test_parameters', 'report_templates', 'testimonials', 
        'doctor_referrals', 'contact_enquiries', 'activity_logs', 
        'site_settings', 'blocked_slots'
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")


def downgrade():
    tables = [
        'users', 'bookings', 'reports', 'test_categories', 'tests', 
        'test_parameters', 'report_templates', 'testimonials', 
        'doctor_referrals', 'contact_enquiries', 'activity_logs', 
        'site_settings', 'blocked_slots'
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
