import secrets
import json
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from config import get_db


def create_session(course_id, faculty_id, expiry_minutes: int = 10) -> dict:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    if isinstance(faculty_id, str):
        faculty_id = ObjectId(faculty_id)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    qr_payload = json.dumps({
        'session_id': str(course_id) + '_' + token[:8],  # human-readable prefix
        'token': token,
        'expires_at': expires_at.isoformat(),
    })

    doc = {
        'course_id': course_id,
        'faculty_id': faculty_id,
        'session_token': token,
        'qr_data': qr_payload,
        'expires_at': expires_at,
        'status': 'active',
        'created_at': datetime.now(timezone.utc),
        'expiry_minutes': expiry_minutes,
    }
    result = db.attendance_sessions.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def get_session_by_id(session_id) -> dict | None:
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    return db.attendance_sessions.find_one({'_id': session_id})


def get_session_by_token(token: str) -> dict | None:
    db = get_db()
    return db.attendance_sessions.find_one({'session_token': token})


def get_sessions_by_course(course_id) -> list:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    return list(db.attendance_sessions.find({'course_id': course_id}).sort('created_at', -1))


def get_sessions_by_faculty(faculty_id) -> list:
    db = get_db()
    if isinstance(faculty_id, str):
        faculty_id = ObjectId(faculty_id)
    return list(
        db.attendance_sessions.find({'faculty_id': faculty_id}).sort('created_at', -1)
    )


def get_active_sessions_by_faculty(faculty_id) -> list:
    db = get_db()
    if isinstance(faculty_id, str):
        faculty_id = ObjectId(faculty_id)
    now = datetime.now(timezone.utc)
    return list(db.attendance_sessions.find({
        'faculty_id': faculty_id,
        'status': 'active',
        'expires_at': {'$gt': now}
    }).sort('created_at', -1))


def close_session(session_id) -> bool:
    db = get_db()
    if isinstance(session_id, str):
        session_id = ObjectId(session_id)
    result = db.attendance_sessions.update_one(
        {'_id': session_id},
        {'$set': {'status': 'closed'}}
    )
    return result.modified_count > 0


def expire_old_sessions() -> int:
    """Mark sessions past their expiry time as 'expired'."""
    db = get_db()
    now = datetime.now(timezone.utc)
    result = db.attendance_sessions.update_many(
        {'status': 'active', 'expires_at': {'$lte': now}},
        {'$set': {'status': 'expired'}}
    )
    return result.modified_count


def count_all_sessions() -> int:
    db = get_db()
    return db.attendance_sessions.count_documents({})
