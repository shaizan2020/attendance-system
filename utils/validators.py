"""
Validation utilities for QR token and session integrity checks.
"""
import json
from datetime import datetime, timezone
from bson import ObjectId
from models.session import get_session_by_id, get_session_by_token
from models.attendance import is_already_marked
from config import get_db


def validate_qr_payload(qr_json: str, student_id) -> tuple[bool, str, dict | None]:
    """
    Validate a QR code payload string.

    Returns:
        (success: bool, message: str, session_doc: dict | None)
    """
    # 1. Parse the JSON payload
    try:
        payload = json.loads(qr_json)
    except (json.JSONDecodeError, TypeError):
        return False, 'Invalid QR code format.', None

    token = payload.get('token')
    expires_at_str = payload.get('expires_at')

    if not token or not expires_at_str:
        return False, 'QR code is missing required fields.', None

    # 2. Check expiry timestamp in payload
    try:
        from dateutil import parser as dateutil_parser
        expires_at = dateutil_parser.parse(expires_at_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except Exception:
        return False, 'Invalid expiry timestamp in QR code.', None

    if datetime.now(timezone.utc) > expires_at:
        return False, 'QR code has expired. Please ask your faculty to refresh it.', None

    # 3. Look up session by token
    session = get_session_by_token(token)
    if not session:
        return False, 'Session not found. Invalid QR code.', None

    # 4. Verify session is still active
    if session['status'] != 'active':
        return False, f"Session is {session['status']}. Attendance cannot be marked.", None

    # 5. Confirm server-side expiry (double check)
    server_expiry = session['expires_at']
    if server_expiry.tzinfo is None:
        server_expiry = server_expiry.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > server_expiry:
        return False, 'Session has expired on the server.', None

    # 6. Verify student enrollment in the course
    db = get_db()
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    course_id = session['course_id']
    course = db.courses.find_one({'_id': course_id, 'enrolled_students': student_id})
    if not course:
        return False, 'You are not enrolled in this course.', None

    # 7. Check for duplicate attendance
    if is_already_marked(session['_id'], student_id):
        return False, 'You have already marked attendance for this session.', None

    return True, 'Validation successful.', session
