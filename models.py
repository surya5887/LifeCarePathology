from datetime import datetime
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


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    home_collection = db.Column(db.Boolean, default=False)
    collection_address = db.Column(db.Text, default='')
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    token_number = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(300), nullable=False)
    remarks = db.Column(db.Text, default='')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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
