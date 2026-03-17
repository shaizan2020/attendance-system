from flask import (Blueprint, request, session, redirect, url_for,
                   render_template, flash, jsonify)
from bson import ObjectId
from routes.auth import role_required
from models.course import get_courses_by_student, get_course_by_id
from models.attendance import (
    get_records_by_student, get_attendance_percentage,
    mark_attendance, get_records_by_course_and_student
)
from utils.validators import validate_qr_payload

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    student_id = session['user_id']
    my_courses = get_courses_by_student(student_id)

    # Calculate attendance percentage per course
    courses_with_stats = []
    for course in my_courses:
        pct = get_attendance_percentage(student_id, course['_id'])
        courses_with_stats.append({
            **course,
            '_id': course['_id'],
            'percentage': pct,
            'status_class': 'success' if pct >= 75 else ('warning' if pct >= 50 else 'danger')
        })

    recent_records = get_records_by_student(student_id)[:5]

    # Enrich with course names
    course_map = {str(c['_id']): c for c in my_courses}
    for rec in recent_records:
        cid = str(rec['course_id'])
        rec['course_name'] = course_map.get(cid, {}).get('course_name', 'Unknown')
        rec['course_code'] = course_map.get(cid, {}).get('course_code', '')

    return render_template('student/dashboard.html',
                           courses=courses_with_stats,
                           recent_records=recent_records)


@student_bp.route('/scan', methods=['GET', 'POST'])
@role_required('student')
def scan():
    return render_template('student/scan.html')


@student_bp.route('/mark', methods=['POST'])
@role_required('student')
def mark():
    """
    Mark attendance via QR code JSON payload.
    Accepts JSON body: { "qr_data": "..." }
    or form body: qr_data=...
    """
    student_id = session['user_id']

    if request.is_json:
        qr_data = request.json.get('qr_data', '')
    else:
        qr_data = request.form.get('qr_data', '')

    if not qr_data:
        return jsonify({'success': False, 'message': 'No QR data provided.'}), 400

    ip_address = request.remote_addr

    # Validate the QR payload
    valid, message, att_session = validate_qr_payload(qr_data, student_id)

    if not valid:
        return jsonify({'success': False, 'message': message}), 400

    # Mark the attendance
    try:
        mark_attendance(
            session_id=att_session['_id'],
            course_id=att_session['course_id'],
            student_id=ObjectId(student_id),
            ip_address=ip_address
        )
        from models.course import get_course_by_id
        course = get_course_by_id(att_session['course_id'])
        course_name = course['course_name'] if course else 'the course'
        return jsonify({
            'success': True,
            'message': f'Attendance marked successfully for {course_name}!'
        })
    except Exception as e:
        if '11000' in str(e) or 'duplicate' in str(e).lower():
            return jsonify({'success': False, 'message': 'Attendance already marked for this session.'}), 409
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@student_bp.route('/history')
@role_required('student')
def history():
    student_id = session['user_id']
    my_courses = get_courses_by_student(student_id)
    selected_course_id = request.args.get('course_id')

    if selected_course_id:
        records = get_records_by_course_and_student(selected_course_id, student_id)
        pct = get_attendance_percentage(student_id, selected_course_id)
        selected_course = get_course_by_id(selected_course_id)
    else:
        records = get_records_by_student(student_id)
        pct = None
        selected_course = None

    # Enrich records with course info
    course_map = {str(c['_id']): c for c in my_courses}
    for rec in records:
        cid = str(rec['course_id'])
        rec['course_name'] = course_map.get(cid, {}).get('course_name', 'Unknown')
        rec['course_code'] = course_map.get(cid, {}).get('course_code', '')

    return render_template('student/history.html',
                           records=records,
                           courses=my_courses,
                           selected_course=selected_course,
                           selected_course_id=selected_course_id,
                           percentage=pct)
