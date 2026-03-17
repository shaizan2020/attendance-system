from flask import (Blueprint, request, session, redirect, url_for,
                   render_template, flash, jsonify, make_response)
from bson import ObjectId
from routes.auth import role_required
from models.course import get_courses_by_faculty, get_course_by_id, get_all_courses
from models.session import (
    create_session, get_session_by_id, get_sessions_by_faculty,
    get_active_sessions_by_faculty, close_session
)
from models.attendance import (
    get_records_by_session, get_course_attendance_report,
    get_session_attendance_count
)
from utils.qr_generator import generate_qr_base64
from utils.reports import generate_course_csv

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')


@faculty_bp.route('/dashboard')
@role_required('faculty')
def dashboard():
    faculty_id = session['user_id']
    my_courses = get_courses_by_faculty(faculty_id)
    active_sessions = get_active_sessions_by_faculty(faculty_id)
    recent_sessions = get_sessions_by_faculty(faculty_id)[:5]

    # Enrich recent sessions with course names
    course_map = {str(c['_id']): c for c in my_courses}
    for s in recent_sessions:
        cid = str(s['course_id'])
        s['course_name'] = course_map.get(cid, {}).get('course_name', 'Unknown')
        s['course_code'] = course_map.get(cid, {}).get('course_code', '')
        s['attendance_count'] = get_session_attendance_count(s['_id'])

    return render_template('faculty/dashboard.html',
                           courses=my_courses,
                           active_sessions=active_sessions,
                           recent_sessions=recent_sessions)


@faculty_bp.route('/sessions/create', methods=['GET', 'POST'])
@role_required('faculty')
def create_session_route():
    faculty_id = session['user_id']
    my_courses = get_courses_by_faculty(faculty_id)

    if request.method == 'POST':
        course_id = request.form.get('course_id')
        expiry_minutes = int(request.form.get('expiry_minutes', 10))

        if not course_id:
            flash('Please select a course.', 'danger')
            return render_template('faculty/create_session.html', courses=my_courses)

        # Validate expiry
        if expiry_minutes < 1 or expiry_minutes > 120:
            flash('Expiry must be between 1 and 120 minutes.', 'danger')
            return render_template('faculty/create_session.html', courses=my_courses)

        att_session = create_session(course_id, faculty_id, expiry_minutes)
        qr_image = generate_qr_base64(att_session['qr_data'])

        flash('Attendance session created! Share the QR code with your students.', 'success')
        return render_template('faculty/create_session.html',
                               courses=my_courses,
                               att_session=att_session,
                               qr_image=qr_image,
                               session_id=str(att_session['_id']))

    return render_template('faculty/create_session.html', courses=my_courses)


@faculty_bp.route('/sessions/<session_id>')
@role_required('faculty')
def view_session(session_id):
    att_session = get_session_by_id(session_id)
    if not att_session:
        flash('Session not found.', 'danger')
        return redirect(url_for('faculty.dashboard'))

    # Verify this faculty owns the session
    if str(att_session['faculty_id']) != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('faculty.dashboard'))

    records = get_records_by_session(session_id)
    qr_image = None
    if att_session['status'] == 'active':
        qr_image = generate_qr_base64(att_session['qr_data'])

    course = get_course_by_id(att_session['course_id'])

    # Enrich records with student names
    from config import get_db
    db = get_db()
    enriched_records = []
    for rec in records:
        student = db.users.find_one({'_id': rec['student_id']}, {'name': 1, 'email': 1, 'student_id': 1})
        if student:
            rec['student_name'] = student.get('name', 'Unknown')
            rec['student_email'] = student.get('email', '')
            rec['student_num'] = student.get('student_id', '')
        enriched_records.append(rec)

    return render_template('faculty/view_session.html',
                           att_session=att_session,
                           records=enriched_records,
                           qr_image=qr_image,
                           course=course)


@faculty_bp.route('/sessions/<session_id>/close', methods=['POST'])
@role_required('faculty')
def close_session_route(session_id):
    att_session = get_session_by_id(session_id)
    if att_session and str(att_session['faculty_id']) == session['user_id']:
        close_session(session_id)
        flash('Session closed successfully.', 'success')
    else:
        flash('Cannot close session.', 'danger')
    return redirect(url_for('faculty.view_session', session_id=session_id))


@faculty_bp.route('/reports')
@role_required('faculty')
def reports():
    faculty_id = session['user_id']
    my_courses = get_courses_by_faculty(faculty_id)
    selected_course_id = request.args.get('course_id')
    report_data = []
    selected_course = None

    if selected_course_id:
        selected_course = get_course_by_id(selected_course_id)
        if selected_course and str(selected_course['faculty_id']) == faculty_id:
            report_data = get_course_attendance_report(selected_course_id)

    return render_template('faculty/reports.html',
                           courses=my_courses,
                           report_data=report_data,
                           selected_course=selected_course,
                           selected_course_id=selected_course_id)


@faculty_bp.route('/reports/<course_id>/export')
@role_required('faculty')
def export_csv(course_id):
    course = get_course_by_id(course_id)
    if not course or str(course['faculty_id']) != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('faculty.reports'))

    csv_data = generate_course_csv(course_id)
    response = make_response(csv_data)
    filename = f"attendance_{course['course_code']}_{course['course_name'].replace(' ', '_')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv'
    return response


@faculty_bp.route('/api/sessions/<session_id>/live')
@role_required('faculty')
def live_count(session_id):
    """API endpoint for live attendance count polling."""
    count = get_session_attendance_count(session_id)
    att_session = get_session_by_id(session_id)
    from datetime import datetime, timezone
    data = {
        'count': count,
        'status': att_session['status'] if att_session else 'unknown',
    }
    if att_session:
        expires = att_session['expires_at']
        if expires.tzinfo is None:
            from datetime import timezone
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = (expires - datetime.now(timezone.utc)).total_seconds()
        data['remaining_seconds'] = max(0, int(remaining))
    return jsonify(data)
