from flask import Blueprint, request, session, redirect, url_for, render_template, flash, jsonify
from bson import ObjectId
from routes.auth import role_required
from models.user import (
    create_user, get_all_users, get_user_by_id, update_user, delete_user
)
from models.course import (
    create_course, get_all_courses, get_course_by_id,
    update_course, delete_course, enroll_student, unenroll_student
)
from utils.reports import get_admin_analytics

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    analytics = get_admin_analytics()
    return render_template('admin/dashboard.html', analytics=analytics)


# ─── User Management ────────────────────────────────────────────────────────

@admin_bp.route('/users')
@role_required('admin')
def users():
    all_users = get_all_users()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/create', methods=['POST'])
@role_required('admin')
def create_user_route():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'student')
    student_id = request.form.get('student_id', '').strip() or None

    if not all([name, email, password, role]):
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        create_user(name, email, password, role, student_id=student_id)
        flash(f'User "{name}" created successfully.', 'success')
    except Exception as e:
        if 'duplicate' in str(e).lower() or '11000' in str(e):
            flash('Email already exists.', 'danger')
        else:
            flash(f'Error creating user: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/edit', methods=['POST'])
@role_required('admin')
def edit_user(user_id):
    updates = {}
    if request.form.get('name'):
        updates['name'] = request.form.get('name').strip()
    if request.form.get('email'):
        updates['email'] = request.form.get('email').strip().lower()
    if request.form.get('password'):
        updates['password'] = request.form.get('password')
    if request.form.get('role'):
        updates['role'] = request.form.get('role')

    if updates:
        update_user(user_id, updates)
        flash('User updated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user_route(user_id):
    user = get_user_by_id(user_id)
    if user:
        delete_user(user_id)
        flash(f'User "{user["name"]}" deleted.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('admin.users'))


# ─── Course Management ────────────────────────────────────────────────────────

@admin_bp.route('/courses')
@role_required('admin')
def courses():
    all_courses = get_all_courses()
    faculty_list = get_all_users(role='faculty')
    student_list = get_all_users(role='student')

    # Enrich courses with faculty name
    faculty_map = {str(f['_id']): f['name'] for f in faculty_list}
    for c in all_courses:
        c['faculty_name'] = faculty_map.get(str(c['faculty_id']), 'Unknown')
        c['enrolled_count'] = len(c.get('enrolled_students', []))

    return render_template('admin/courses.html',
                           courses=all_courses,
                           faculty_list=faculty_list,
                           student_list=student_list)


@admin_bp.route('/courses/create', methods=['POST'])
@role_required('admin')
def create_course_route():
    code = request.form.get('course_code', '').strip()
    name = request.form.get('course_name', '').strip()
    faculty_id = request.form.get('faculty_id', '').strip()

    if not all([code, name, faculty_id]):
        flash('All course fields are required.', 'danger')
        return redirect(url_for('admin.courses'))

    try:
        create_course(code, name, faculty_id)
        flash(f'Course "{name}" created.', 'success')
    except Exception as e:
        if '11000' in str(e):
            flash('Course code already exists.', 'danger')
        else:
            flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<course_id>/delete', methods=['POST'])
@role_required('admin')
def delete_course_route(course_id):
    course = get_course_by_id(course_id)
    if course:
        delete_course(course_id)
        flash(f'Course "{course["course_name"]}" deleted.', 'success')
    else:
        flash('Course not found.', 'danger')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<course_id>/enroll', methods=['POST'])
@role_required('admin')
def enroll_route(course_id):
    student_id = request.form.get('student_id')
    action = request.form.get('action', 'enroll')

    if action == 'enroll':
        enroll_student(course_id, student_id)
        flash('Student enrolled.', 'success')
    else:
        unenroll_student(course_id, student_id)
        flash('Student unenrolled.', 'info')

    return redirect(url_for('admin.courses'))


# ─── Analytics API ────────────────────────────────────────────────────────────

@admin_bp.route('/api/analytics')
@role_required('admin')
def api_analytics():
    data = get_admin_analytics()
    # Convert ObjectId for JSON
    for c in data.get('top_courses', []):
        c['_id'] = str(c['_id'])
        if 'faculty_id' in c:
            c['faculty_id'] = str(c['faculty_id'])
    return jsonify(data)
