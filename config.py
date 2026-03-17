import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_secret_key_change_in_production')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'attendance_management')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    QR_EXPIRY_MINUTES = 10  # default QR expiry in minutes

# MongoDB connection
_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(Config.MONGO_URI)
        _db = _client[Config.MONGO_DB]
        _setup_indexes(_db)
    return _db

def _setup_indexes(db):
    """Create necessary indexes for performance and constraints."""
    # Users: unique email index
    db.users.create_index([('email', ASCENDING)], unique=True)
    db.users.create_index([('student_id', ASCENDING)])
    db.users.create_index([('role', ASCENDING)])

    # Courses: unique course_code index
    db.courses.create_index([('course_code', ASCENDING)], unique=True)
    db.courses.create_index([('faculty_id', ASCENDING)])

    # Attendance Sessions: token index + expiry
    db.attendance_sessions.create_index([('session_token', ASCENDING)], unique=True)
    db.attendance_sessions.create_index([('course_id', ASCENDING)])
    db.attendance_sessions.create_index([('faculty_id', ASCENDING)])
    db.attendance_sessions.create_index([('status', ASCENDING)])
    db.attendance_sessions.create_index([('expires_at', ASCENDING)])

    # Attendance Records: compound unique index prevents duplicates
    db.attendance_records.create_index(
        [('session_id', ASCENDING), ('student_id', ASCENDING)],
        unique=True
    )
    db.attendance_records.create_index([('course_id', ASCENDING)])
    db.attendance_records.create_index([('student_id', ASCENDING)])
    db.attendance_records.create_index([('marked_at', DESCENDING)])
