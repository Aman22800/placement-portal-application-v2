from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """Unified user model for Admin, Company, and Student roles."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' | 'company' | 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship(
        'StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )
    company_profile = db.relationship(
        'CompanyProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )


class StudentProfile(db.Model):
    __tablename__ = 'student_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    branch = db.Column(db.String(80))
    cgpa = db.Column(db.Float)
    year = db.Column(db.Integer)
    skills = db.Column(db.String(255))       # NEW: comma-separated skills, e.g. "Python,SQL"
    resume_path = db.Column(db.String(255))
    is_placed = db.Column(db.Boolean, default=False)   # NEW: flips true once an offer is accepted
    is_blacklisted = db.Column(db.Boolean, default=False)  # NEW: admin can blacklist a student

    applications = db.relationship('Application', backref='student', cascade='all, delete-orphan')


class CompanyProfile(db.Model):
    __tablename__ = 'company_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(150), nullable=False)
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(255))
    approval_status = db.Column(db.String(20), default='Pending')  # Pending | Approved | Rejected
    is_blacklisted = db.Column(db.Boolean, default=False)

    drives = db.relationship('PlacementDrive', backref='company', cascade='all, delete-orphan')


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text)
    eligibility_branch = db.Column(db.String(120))
    eligibility_min_cgpa = db.Column(db.Float, default=0.0)
    eligibility_year = db.Column(db.Integer)
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending | Approved | Closed

    applications = db.relationship('Application', backref='drive', cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')
    # Applied | Shortlisted | Interview Scheduled | Selected | Offer Accepted | Rejected

    # NEW: interview scheduling fields
    interview_datetime = db.Column(db.DateTime)
    interview_link = db.Column(db.String(255))

    # NEW: offer fields
    offer_salary = db.Column(db.Float)
    offer_joining_date = db.Column(db.Date)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='uq_student_drive'),
    )