import os
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from flask_mail import Mail
from models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from celery_config import make_celery

load_dotenv()  # reads the .env file and makes MAIL_USERNAME etc. available via os.environ

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, 'frontend', 'dist')
RESUME_DIR = os.path.join(BASE_DIR, 'static', 'resumes')
os.makedirs(RESUME_DIR, exist_ok=True)

# static_folder=None disables Flask's automatic static-file route, which was
# silently intercepting requests like /admin/dashboard and returning 404
# before our own catch-all route below ever got a chance to run.
app = Flask(__name__, static_folder=None)
CORS(app)

INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(INSTANCE_DIR, "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
if not app.config['JWT_SECRET_KEY']:
    raise RuntimeError(
        'JWT_SECRET_KEY is not set. Add it to your .env file (see .env.example).'
    )

# Flask-Mail config -- reads real credentials from the .env file via os.environ,
# so no email password ever sits directly in this source file.
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False') == 'True'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

db.init_app(app)
mail = Mail(app)
jwt = JWTManager(app)

# Celery must be created here, AFTER app.config is set, so it inherits
# the same config. tasks.py imports this 'celery' object.
celery = make_celery(app)


# ---------- ROLE-BASED ACCESS DECORATOR ----------
def role_required(required_role):
    def decorator(original_function):
        @wraps(original_function)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != required_role:
                return jsonify({'error': f'Forbidden: {required_role} access only'}), 403
            return original_function(*args, **kwargs)
        return wrapper
    return decorator


# ---------- STUDENT REGISTRATION ----------
@app.route('/api/register/student', methods=['POST'])
def register_student():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='student'
    )
    db.session.add(new_user)
    db.session.flush()

    profile = StudentProfile(
        user_id=new_user.id,
        name=data['name'],
        branch=data.get('branch'),
        cgpa=data.get('cgpa'),
        year=data.get('year')
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({'message': 'Student registered successfully'}), 201


# ---------- COMPANY REGISTRATION ----------
@app.route('/api/register/company', methods=['POST'])
def register_company():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='company'
    )
    db.session.add(new_user)
    db.session.flush()

    profile = CompanyProfile(
        user_id=new_user.id,
        company_name=data['company_name'],
        hr_contact=data.get('hr_contact'),
        website=data.get('website')
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({'message': 'Company registered successfully, pending admin approval'}), 201


# ---------- LOGIN (shared by all roles) ----------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    return jsonify({'access_token': access_token, 'role': user.role}), 200


# ---------- SERVE THE BUILT VUE FRONTEND ----------
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serves the compiled JS/CSS bundles Vite produced in dist/assets/."""
    return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Catch-all: any non-API, non-asset path gets index.html, and Vue Router
    (running in the browser) decides what to actually display. This is what
    makes refreshing a URL like /admin/dashboard work correctly, instead of 404."""
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    requested_file = os.path.join(FRONTEND_DIST, path)
    if path and os.path.isfile(requested_file):
        return send_from_directory(FRONTEND_DIST, path)

    return send_from_directory(FRONTEND_DIST, 'index.html')


# ---------- WHOAMI ----------
@app.route('/api/whoami', methods=['GET'])
@jwt_required()
def whoami():
    claims = get_jwt()
    return jsonify({'role': claims['role']}), 200


# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/companies', methods=['GET'])
@jwt_required()
@role_required('admin')
def view_all_companies():
    companies = CompanyProfile.query.all()
    result = [{
        'id': c.id, 'company_name': c.company_name, 'hr_contact': c.hr_contact,
        'website': c.website, 'approval_status': c.approval_status,
        'is_blacklisted': c.is_blacklisted
    } for c in companies]
    return jsonify(result), 200


@app.route('/api/admin/companies/<int:company_id>/status', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_company_status(company_id):
    data = request.get_json()
    new_status = data.get('approval_status')
    if new_status not in ('Approved', 'Rejected'):
        return jsonify({'error': "approval_status must be 'Approved' or 'Rejected'"}), 400

    company = CompanyProfile.query.get(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    company.approval_status = new_status
    db.session.commit()
    return jsonify({'message': f'Company {new_status.lower()} successfully'}), 200


# ---------- NEW: BLACKLIST / UN-BLACKLIST A COMPANY ----------
@app.route('/api/admin/companies/<int:company_id>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def blacklist_company(company_id):
    data = request.get_json()
    is_blacklisted = data.get('is_blacklisted')  # expects true or false

    if not isinstance(is_blacklisted, bool):
        return jsonify({'error': 'is_blacklisted must be true or false'}), 400

    company = CompanyProfile.query.get(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    company.is_blacklisted = is_blacklisted
    db.session.commit()
    action = 'blacklisted' if is_blacklisted else 'un-blacklisted'
    return jsonify({'message': f'Company {action} successfully'}), 200


@app.route('/api/admin/drives', methods=['GET'])
@jwt_required()
@role_required('admin')
def view_all_drives():
    drives = PlacementDrive.query.all()
    result = [{
        'id': d.id, 'company_id': d.company_id, 'job_title': d.job_title,
        'status': d.status,
        'application_deadline': str(d.application_deadline) if d.application_deadline else None
    } for d in drives]
    return jsonify(result), 200


@app.route('/api/admin/drives/<int:drive_id>/status', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_drive_status(drive_id):
    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('Approved', 'Closed'):
        return jsonify({'error': "status must be 'Approved' or 'Closed'"}), 400

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404

    drive.status = new_status
    db.session.commit()
    return jsonify({'message': f'Drive status updated to {new_status}'}), 200


# ---------- NEW: VIEW ALL STUDENTS ----------
@app.route('/api/admin/students', methods=['GET'])
@jwt_required()
@role_required('admin')
def view_all_students():
    students = StudentProfile.query.all()
    result = [{
        'id': s.id,
        'name': s.name,
        'email': s.user.email,
        'branch': s.branch,
        'cgpa': s.cgpa,
        'year': s.year,
        'is_placed': s.is_placed,
        'is_blacklisted': s.is_blacklisted
    } for s in students]
    return jsonify(result), 200


# ---------- NEW: BLACKLIST / UN-BLACKLIST A STUDENT ----------
@app.route('/api/admin/students/<int:student_id>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def blacklist_student(student_id):
    data = request.get_json()
    is_blacklisted = data.get('is_blacklisted')

    if not isinstance(is_blacklisted, bool):
        return jsonify({'error': 'is_blacklisted must be true or false'}), 400

    student = StudentProfile.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    student.is_blacklisted = is_blacklisted
    db.session.commit()
    action = 'blacklisted' if is_blacklisted else 'un-blacklisted'
    return jsonify({'message': f'Student {action} successfully'}), 200


# ---------- NEW: ADMIN DASHBOARD OVERVIEW STATS ----------
@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_stats():
    return jsonify({
        'total_students': StudentProfile.query.count(),
        'total_companies': CompanyProfile.query.count(),
        'approved_companies': CompanyProfile.query.filter_by(approval_status='Approved').count(),
        'total_drives': PlacementDrive.query.count(),
        'approved_drives': PlacementDrive.query.filter_by(status='Approved').count(),
        'total_applications': Application.query.count(),
        'total_placed': StudentProfile.query.filter_by(is_placed=True).count()
    }), 200


# ==================== COMPANY ROUTES ====================

def get_current_company_profile():
    user_id = get_jwt_identity()
    return CompanyProfile.query.filter_by(user_id=int(user_id)).first()


@app.route('/api/company/drives', methods=['POST'])
@jwt_required()
@role_required('company')
def create_drive():
    company = get_current_company_profile()

    if company.approval_status != 'Approved':
        return jsonify({'error': 'Your company is not yet approved by admin'}), 403
    if company.is_blacklisted:
        return jsonify({'error': 'Your company has been blacklisted and cannot post drives'}), 403

    data = request.get_json()
    deadline_str = data.get('application_deadline')
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None

    new_drive = PlacementDrive(
        company_id=company.id,
        job_title=data['job_title'],
        job_description=data.get('job_description'),
        eligibility_branch=data.get('eligibility_branch'),
        eligibility_min_cgpa=data.get('eligibility_min_cgpa', 0.0),
        eligibility_year=data.get('eligibility_year'),
        application_deadline=deadline
    )
    db.session.add(new_drive)
    db.session.commit()
    return jsonify({'message': 'Drive created, pending admin approval', 'drive_id': new_drive.id}), 201


@app.route('/api/company/drives', methods=['GET'])
@jwt_required()
@role_required('company')
def view_my_drives():
    company = get_current_company_profile()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    result = [{
        'id': d.id, 'job_title': d.job_title, 'status': d.status,
        'application_deadline': str(d.application_deadline) if d.application_deadline else None
    } for d in drives]
    return jsonify(result), 200


@app.route('/api/company/drives/<int:drive_id>/applicants', methods=['GET'])
@jwt_required()
@role_required('company')
def view_applicants(drive_id):
    company = get_current_company_profile()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({'error': 'Drive not found or not owned by your company'}), 404

    applications = Application.query.filter_by(drive_id=drive_id).all()
    result = [{
        'application_id': a.id,
        'student_name': a.student.name,
        'student_cgpa': a.student.cgpa,
        'status': a.status,
        'applied_on': str(a.applied_on),
        'interview_datetime': str(a.interview_datetime) if a.interview_datetime else None,
        'offer_salary': a.offer_salary
    } for a in applications]
    return jsonify(result), 200


@app.route('/api/company/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_application_status(application_id):
    company = get_current_company_profile()
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ('Shortlisted', 'Rejected'):
        return jsonify({'error': "status must be 'Shortlisted' or 'Rejected'"}), 400

    application = Application.query.get(application_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    if application.drive.company_id != company.id:
        return jsonify({'error': 'This application does not belong to your company'}), 403

    application.status = new_status
    db.session.commit()

    # Fire-and-forget email -- .delay() queues it on Celery and returns immediately,
    # so this HTTP response doesn't wait for the SMTP send to finish.
    from tasks import send_email_task
    send_email_task.delay(
        subject=f"Application Update: {application.drive.job_title}",
        recipient=application.student.user.email,
        body=(
            f"Hi {application.student.name},\n\n"
            f"Your application for '{application.drive.job_title}' at "
            f"{application.drive.company.company_name} has been updated to: {new_status}.\n\n"
            f"Placement Portal Team"
        )
    )

    return jsonify({'message': f'Application status updated to {new_status}'}), 200


# ---------- NEW: SCHEDULE AN INTERVIEW ----------
@app.route('/api/company/applications/<int:application_id>/schedule-interview', methods=['PUT'])
@jwt_required()
@role_required('company')
def schedule_interview(application_id):
    company = get_current_company_profile()
    data = request.get_json()

    application = Application.query.get(application_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    if application.drive.company_id != company.id:
        return jsonify({'error': 'This application does not belong to your company'}), 403

    # e.g. "2026-07-20 18:30"
    dt_str = data.get('interview_datetime')
    try:
        interview_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return jsonify({'error': "interview_datetime must be in format 'YYYY-MM-DD HH:MM'"}), 400

    application.interview_datetime = interview_dt
    application.interview_link = data.get('interview_link')
    application.status = 'Interview Scheduled'
    db.session.commit()

    from tasks import send_email_task
    send_email_task.delay(
        subject=f"Interview Scheduled: {application.drive.job_title}",
        recipient=application.student.user.email,
        body=(
            f"Hi {application.student.name},\n\n"
            f"Your interview for '{application.drive.job_title}' has been scheduled "
            f"for {interview_dt}.\n"
            f"Meeting link: {application.interview_link or 'To be shared'}\n\n"
            f"Good luck!\nPlacement Portal Team"
        )
    )

    return jsonify({'message': 'Interview scheduled successfully'}), 200


# ---------- NEW: RELEASE AN OFFER ----------
@app.route('/api/company/applications/<int:application_id>/release-offer', methods=['PUT'])
@jwt_required()
@role_required('company')
def release_offer(application_id):
    company = get_current_company_profile()
    data = request.get_json()

    application = Application.query.get(application_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    if application.drive.company_id != company.id:
        return jsonify({'error': 'This application does not belong to your company'}), 403

    joining_str = data.get('offer_joining_date')
    try:
        joining_date = datetime.strptime(joining_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': "offer_joining_date must be in format 'YYYY-MM-DD'"}), 400

    application.offer_salary = data.get('offer_salary')
    application.offer_joining_date = joining_date
    application.status = 'Selected'
    db.session.commit()

    from tasks import send_email_task
    send_email_task.delay(
        subject=f"Offer Released: {application.drive.job_title}",
        recipient=application.student.user.email,
        body=(
            f"Hi {application.student.name},\n\n"
            f"Congratulations! You've received an offer for '{application.drive.job_title}' "
            f"at {application.drive.company.company_name}.\n"
            f"Salary: {application.offer_salary}\n"
            f"Joining Date: {application.offer_joining_date}\n\n"
            f"Log in to the portal to accept or view details.\nPlacement Portal Team"
        )
    )

    return jsonify({'message': 'Offer released successfully'}), 200


# ==================== STUDENT ROUTES ====================

def get_current_student_profile():
    user_id = get_jwt_identity()
    return StudentProfile.query.filter_by(user_id=int(user_id)).first()


@app.route('/api/student/drives', methods=['GET'])
@jwt_required()
@role_required('student')
def view_eligible_drives():
    student = get_current_student_profile()
    approved_drives = PlacementDrive.query.filter_by(status='Approved').all()

    result = []
    for d in approved_drives:
        if d.eligibility_min_cgpa and student.cgpa is not None and student.cgpa < d.eligibility_min_cgpa:
            continue
        if d.eligibility_year and student.year is not None and student.year != d.eligibility_year:
            continue
        if d.eligibility_branch and student.branch and student.branch.strip().lower() not in d.eligibility_branch.lower():
            continue  # wrong branch (case-insensitive, whitespace-trimmed compare) -- skip

        result.append({
            'id': d.id,
            'job_title': d.job_title,
            'job_description': d.job_description,
            'eligibility_branch': d.eligibility_branch,
            'eligibility_min_cgpa': d.eligibility_min_cgpa,
            'eligibility_year': d.eligibility_year,
            'application_deadline': str(d.application_deadline) if d.application_deadline else None
        })
    return jsonify(result), 200


@app.route('/api/student/drives/<int:drive_id>/apply', methods=['POST'])
@jwt_required()
@role_required('student')
def apply_to_drive(drive_id):
    student = get_current_student_profile()

    if student.is_blacklisted:
        return jsonify({'error': 'Your account has been blacklisted and cannot apply to drives'}), 403

    drive = PlacementDrive.query.filter_by(id=drive_id, status='Approved').first()
    if not drive:
        return jsonify({'error': 'Drive not found or not open for applications'}), 404

    new_application = Application(student_id=student.id, drive_id=drive_id)
    db.session.add(new_application)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'You have already applied to this drive'}), 400

    return jsonify({'message': 'Applied successfully', 'application_id': new_application.id}), 201


@app.route('/api/student/applications', methods=['GET'])
@jwt_required()
@role_required('student')
def view_my_applications():
    student = get_current_student_profile()
    applications = Application.query.filter_by(student_id=student.id).all()
    result = [{
        'application_id': a.id,
        'job_title': a.drive.job_title,
        'status': a.status,
        'applied_on': str(a.applied_on),
        'interview_datetime': str(a.interview_datetime) if a.interview_datetime else None,
        'offer_salary': a.offer_salary
    } for a in applications]
    return jsonify(result), 200


# ---------- NEW: ACCEPT AN OFFER (cascades reject on all other applications) ----------
@app.route('/api/student/applications/<int:application_id>/accept-offer', methods=['PUT'])
@jwt_required()
@role_required('student')
def accept_offer(application_id):
    student = get_current_student_profile()

    application = Application.query.get(application_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    if application.student_id != student.id:
        return jsonify({'error': 'This application does not belong to you'}), 403
    if application.status != 'Selected':
        return jsonify({'error': 'This application does not have an active offer to accept'}), 400

    # Step 1: accept this one
    application.status = 'Offer Accepted'

    # Step 2: cascade -- reject every OTHER application this student has, regardless of stage
    other_applications = Application.query.filter(
        Application.student_id == student.id,
        Application.id != application.id
    ).all()
    for other in other_applications:
        other.status = 'Rejected'

    # Step 3: mark the student as placed
    student.is_placed = True

    db.session.commit()
    return jsonify({'message': 'Offer accepted. All other applications have been rejected.'}), 200


# ---------- VIEW MY STUDENT PROFILE ----------
@app.route('/api/student/profile', methods=['GET'])
@jwt_required()
@role_required('student')
def get_student_profile():
    student = get_current_student_profile()
    return jsonify({
        'name': student.name,
        'branch': student.branch,
        'cgpa': student.cgpa,
        'year': student.year,
        'skills': student.skills,
        'resume_uploaded': bool(student.resume_path),
        'is_placed': student.is_placed,
        'email': student.user.email
    }), 200


# ---------- UPDATE MY STUDENT PROFILE (branch, cgpa, year, skills) ----------
@app.route('/api/student/profile', methods=['PUT'])
@jwt_required()
@role_required('student')
def update_student_profile():
    student = get_current_student_profile()
    data = request.get_json()

    if 'skills' in data:
        student.skills = data['skills']
    if 'cgpa' in data:
        student.cgpa = data['cgpa']
    if 'branch' in data:
        student.branch = data['branch']
    if 'year' in data:
        student.year = data['year']

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


# ---------- UPLOAD MY RESUME ----------
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_resume_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS

@app.route('/api/student/profile/resume', methods=['POST'])
@jwt_required()
@role_required('student')
def upload_resume():
    student = get_current_student_profile()

    if 'resume' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_resume_file(file.filename):
        return jsonify({'error': 'Only PDF, DOC, or DOCX files are allowed'}), 400

    # Prefix with student id so filenames never collide between students
    filename = secure_filename(f"student_{student.id}_{file.filename}")
    filepath = os.path.join(RESUME_DIR, filename)
    file.save(filepath)

    student.resume_path = filename
    db.session.commit()

    return jsonify({'message': 'Resume uploaded successfully', 'filename': filename}), 200


# ---------- DOWNLOAD MY OWN RESUME (student) ----------
@app.route('/api/student/profile/resume', methods=['GET'])
@jwt_required()
@role_required('student')
def download_own_resume():
    student = get_current_student_profile()
    if not student.resume_path:
        return jsonify({'error': 'No resume uploaded yet'}), 404
    return send_from_directory(RESUME_DIR, student.resume_path, as_attachment=True)


# ---------- DOWNLOAD AN APPLICANT'S RESUME (company) ----------
@app.route('/api/company/applications/<int:application_id>/resume', methods=['GET'])
@jwt_required()
@role_required('company')
def download_applicant_resume(application_id):
    company = get_current_company_profile()

    application = Application.query.get(application_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    if application.drive.company_id != company.id:
        return jsonify({'error': 'This application does not belong to your company'}), 403
    if not application.student.resume_path:
        return jsonify({'error': 'This student has not uploaded a resume'}), 404

    return send_from_directory(RESUME_DIR, application.student.resume_path, as_attachment=True)


# ---------- VIEW MY COMPANY PROFILE ----------
@app.route('/api/company/profile', methods=['GET'])
@jwt_required()
@role_required('company')
def get_company_profile():
    company = get_current_company_profile()
    return jsonify({
        'company_name': company.company_name,
        'hr_contact': company.hr_contact,
        'website': company.website,
        'approval_status': company.approval_status,
        'is_blacklisted': company.is_blacklisted,
        'email': company.user.email
    }), 200


# ---------- UPDATE MY COMPANY PROFILE ----------
@app.route('/api/company/profile', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_company_profile():
    company = get_current_company_profile()
    data = request.get_json()

    if 'company_name' in data:
        company.company_name = data['company_name']
    if 'hr_contact' in data:
        company.hr_contact = data['hr_contact']
    if 'website' in data:
        company.website = data['website']

    db.session.commit()
    return jsonify({'message': 'Company profile updated successfully'}), 200


# ---------- NEW: MANUALLY TRIGGER INTERVIEW REMINDERS (Celery background job) ----------
@app.route('/api/admin/trigger-reminders', methods=['POST'])
@jwt_required()
@role_required('admin')
def trigger_interview_reminders():
    from tasks import send_interview_reminders  # lazy import avoids the circular import at Flask startup
    task = send_interview_reminders.delay()  # .delay() queues it for Celery -- returns immediately
    return jsonify({'message': 'Reminder task queued', 'task_id': task.id}), 202


if __name__ == '__main__':
    # host='0.0.0.0' so the dev server accepts connections from outside the
    # container when running under Docker; harmless for local (non-Docker) use.
    app.run(host='0.0.0.0', debug=True, port=5000)