from datetime import datetime
import random
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='patient')  # patient / admin
    address = db.Column(db.Text, default='')
    profile_picture = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='user', lazy=True)
    testimonials = db.relationship('Testimonial', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


class TestCategory(db.Model):
    __tablename__ = 'test_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='🧪')
    description = db.Column(db.Text, default='')
    tests = db.relationship('Test', backref='category', lazy=True)


class Test(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('test_categories.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, default='')
    sample_type = db.Column(db.String(50), default='Blood')
    report_time = db.Column(db.String(50), default='24 Hours')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('Booking', backref='test', lazy=True)
    parameters = db.relationship('TestParameter', backref='test', lazy=True,
                                  cascade='all, delete-orphan',
                                  order_by='TestParameter.display_order')


class TestParameter(db.Model):
    __tablename__ = 'test_parameters'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    parameter_name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(50), default='')
    normal_range_text = db.Column(db.String(100), default='')  # e.g. "12.0 - 17.5"
    normal_range_min = db.Column(db.Float, nullable=True)       # For auto-flag
    normal_range_max = db.Column(db.Float, nullable=True)
    display_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'parameter_name': self.parameter_name,
            'unit': self.unit,
            'normal_range_text': self.normal_range_text,
            'normal_range_min': self.normal_range_min,
            'normal_range_max': self.normal_range_max,
            'display_order': self.display_order
        }


class ReportTemplate(db.Model):
    __tablename__ = 'report_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, completed, cancelled
    
    # Enhanced Patient Details (Snapshotted at booking time)
    patient_name = db.Column(db.String(100), nullable=True)
    patient_phone = db.Column(db.String(20), nullable=True)
    patient_email = db.Column(db.String(120), nullable=True)
    patient_address = db.Column(db.Text, default='')
    
    # Referral & Payment
    referral_type = db.Column(db.String(20), default='self') # self, doctor
    referral_doctor = db.Column(db.String(100), default='')
    payment_mode = db.Column(db.String(20), default='Offline') # Cash/Offline
    payment_status = db.Column(db.String(20), default='pending')

    home_collection = db.Column(db.Boolean, default=False)
    collection_address = db.Column(db.Text, default='') # Keeping for backwards compatibility if needed, or alias to patient_address
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlockedSlot(db.Model):
    """Model to manage availability (Admin Blocks)."""
    __tablename__ = 'blocked_slots'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=True) # If NULL, block entire day
    reason = db.Column(db.String(200), default='Unavailable')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(20), unique=True, nullable=False)  # RID format
    patient_name = db.Column(db.String(100), nullable=False)
    token_number = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    remarks = db.Column(db.Text, default='')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # New fields for admin-created reports
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    doctor_name = db.Column(db.String(100), default='')
    test_name = db.Column(db.String(200), default='')
    test_results_json = db.Column(db.Text, default='[]')  # JSON string

    user = db.relationship('User', backref='reports', foreign_keys=[user_id])

    @staticmethod
    def generate_report_id():
        """Generate a unique Report ID in RID + 6 digits format."""
        while True:
            rid = f"RID{random.randint(100000, 999999)}"
            if not Report.query.filter_by(report_id=rid).first():
                return rid

    @staticmethod
    def generate_password_from_name(name):
        """Generate password: first 4 letters of name in UPPERCASE."""
        cleaned = ''.join(c for c in name if c.isalpha())
        return cleaned[:4].upper() if len(cleaned) >= 4 else cleaned.upper().ljust(4, 'X')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_test_results(self):
        """Parse test results JSON."""
        try:
            return json.loads(self.test_results_json) if self.test_results_json else []
        except (json.JSONDecodeError, TypeError):
            return []

    def set_test_results(self, results):
        """Store test results as JSON."""
        self.test_results_json = json.dumps(results)


class ContactEnquiry(db.Model):
    __tablename__ = 'contact_enquiries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), default='')
    phone = db.Column(db.String(15), default='')
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Testimonial(db.Model):
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewer_name = db.Column(db.String(100), default='Anonymous')
    rating = db.Column(db.Integer, default=5)
    review = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DoctorReferral(db.Model):
    __tablename__ = 'doctor_referrals'

    id = db.Column(db.Integer, primary_key=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    doctor_phone = db.Column(db.String(15), default='')
    patient_name = db.Column(db.String(100), default='')
    test_name = db.Column(db.String(150), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User', backref='activity_logs')


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
