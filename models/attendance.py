from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from config import get_db


def mark_attendance(session_id, course_id, student_id, ip_address: str = None) -> dict:
    """
    Insert an attendance record. Raises DuplicateKeyError if already marked.
    Returns the inserted document.
    """
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)

    doc = {
        'session_id': session_id,
        'course_id': course_id,
        'student_id': student_id,
        'marked_at': datetime.now(timezone.utc),
        'ip_address': ip_address,
        'status': 'present',
    }
    result = db.attendance_records.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def is_already_marked(session_id, student_id) -> bool:
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    return db.attendance_records.count_documents({
        'session_id': session_id,
        'student_id': student_id
    }) > 0


def get_records_by_session(session_id) -> list:
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    return list(db.attendance_records.find({'session_id': session_id}).sort('marked_at', 1))


def get_records_by_student(student_id) -> list:
    db = get_db()
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    return list(db.attendance_records.find({'student_id': student_id}).sort('marked_at', -1))


def get_records_by_course_and_student(course_id, student_id) -> list:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    return list(db.attendance_records.find({
        'course_id': course_id,
        'student_id': student_id
    }).sort('marked_at', -1))


def get_attendance_percentage(student_id, course_id) -> float:
    """
    Aggregation: How many sessions the student attended vs total sessions in that course.
    """
    db = get_db()
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)

    # Total sessions for this course
    total_sessions = db.attendance_sessions.count_documents({'course_id': course_id})
    if total_sessions == 0:
        return 0.0

    # Sessions attended
    attended = db.attendance_records.count_documents({
        'student_id': student_id,
        'course_id': course_id
    })
    return round((attended / total_sessions) * 100, 2)


def get_course_attendance_report(course_id) -> list:
    """
    Returns aggregated report: for each student enrolled, their attendance count and percentage.
    """
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)

    total_sessions = db.attendance_sessions.count_documents({'course_id': course_id})

    pipeline = [
        {'$match': {'enrolled_courses': course_id}},
        {'$lookup': {
            'from': 'attendance_records',
            'let': {'sid': '$_id'},
            'pipeline': [
                {'$match': {
                    '$expr': {
                        '$and': [
                            {'$eq': ['$course_id', course_id]},
                            {'$eq': ['$student_id', '$$sid']}
                        ]
                    }
                }}
            ],
            'as': 'attendance_info'
        }},
        {'$project': {
            'student_id': '$_id',
            'name': 1,
            'email': 1,
            'student_id_num': '$student_id',
            'attended': {'$size': '$attendance_info'},
            'last_attended': {'$max': '$attendance_info.marked_at'},
            'total_sessions': {'$literal': total_sessions},
            'percentage': {
                '$cond': [
                    {'$eq': [total_sessions, 0]},
                    0,
                    {'$multiply': [{'$divide': [{'$size': '$attendance_info'}, total_sessions]}, 100]}
                ]
            }
        }},
        {'$sort': {'name': 1}}
    ]
    return list(db.users.aggregate(pipeline))


def get_session_attendance_count(session_id) -> int:
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    return db.attendance_records.count_documents({'session_id': session_id})


def get_total_attendance_count() -> int:
    db = get_db()
    return db.attendance_records.count_documents({})


def get_daily_attendance_stats(days: int = 30) -> list:
    """Returns daily attendance counts for the last N days."""
    from datetime import timedelta
    db = get_db()
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {'$match': {'marked_at': {'$gte': start_date}}},
        {'$group': {
            '_id': {
                'year': {'$year': '$marked_at'},
                'month': {'$month': '$marked_at'},
                'day': {'$dayOfMonth': '$marked_at'}
            },
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]
    return list(db.attendance_records.aggregate(pipeline))
