"""
Report generation utility: CSV export and aggregation helpers.
"""
import csv
import io
from datetime import datetime, timezone
from bson import ObjectId
from models.attendance import get_course_attendance_report
from models.session import get_sessions_by_course
from config import get_db


def generate_course_csv(course_id) -> str:
    """
    Generate a CSV string for attendance report of a given course.
    Columns: Student ID, Name, Email, Sessions Attended, Total Sessions, Percentage
    """
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)

    report_data = get_course_attendance_report(course_id)
    total_sessions = len(get_sessions_by_course(course_id))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Student ID', 'Name', 'Email',
        'Sessions Attended', 'Total Sessions', 'Attendance %'
    ])

    for row in report_data:
        writer.writerow([
            row.get('student_id_num', 'N/A'),
            row.get('name', 'N/A'),
            row.get('email', 'N/A'),
            row.get('attended', 0),
            total_sessions,
            f"{row.get('percentage', 0):.1f}%"
        ])

    return output.getvalue()


def get_admin_analytics() -> dict:
    """Returns system-wide analytics for the admin dashboard."""
    db = get_db()

    total_users = db.users.count_documents({})
    total_students = db.users.count_documents({'role': 'student'})
    total_faculty = db.users.count_documents({'role': 'faculty'})
    total_courses = db.courses.count_documents({})
    total_sessions = db.attendance_sessions.count_documents({})
    total_attendance = db.attendance_records.count_documents({})
    active_sessions = db.attendance_sessions.count_documents({
        'status': 'active',
        'expires_at': {'$gt': datetime.now(timezone.utc)}
    })

    # Course-wise attendance summary
    course_pipeline = [
        {'$lookup': {
            'from': 'attendance_records',
            'localField': '_id',
            'foreignField': 'course_id',
            'as': 'records'
        }},
        {'$lookup': {
            'from': 'users',
            'localField': 'faculty_id',
            'foreignField': '_id',
            'as': 'faculty_info'
        }},
        {'$project': {
            'course_code': 1,
            'course_name': 1,
            'faculty_name': {'$arrayElemAt': ['$faculty_info.name', 0]},
            'enrolled_count': {'$size': '$enrolled_students'},
            'attendance_count': {'$size': '$records'},
        }},
        {'$limit': 10}
    ]
    top_courses = list(db.courses.aggregate(course_pipeline))

    return {
        'total_users': total_users,
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_courses': total_courses,
        'total_sessions': total_sessions,
        'total_attendance': total_attendance,
        'active_sessions': active_sessions,
        'top_courses': top_courses,
    }
