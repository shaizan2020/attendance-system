from datetime import datetime, timezone
from bson import ObjectId
from config import get_db


def create_course(course_code: str, course_name: str, faculty_id) -> dict:
    db = get_db()
    if isinstance(faculty_id, str):
        faculty_id = ObjectId(faculty_id)
    doc = {
        'course_code': course_code.upper().strip(),
        'course_name': course_name.strip(),
        'faculty_id': faculty_id,
        'enrolled_students': [],
        'created_at': datetime.now(timezone.utc),
    }
    result = db.courses.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def get_course_by_id(course_id) -> dict | None:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    return db.courses.find_one({'_id': course_id})


def get_all_courses() -> list:
    db = get_db()
    return list(db.courses.find().sort('created_at', -1))


def get_courses_by_faculty(faculty_id) -> list:
    db = get_db()
    if isinstance(faculty_id, str):
        faculty_id = ObjectId(faculty_id)
    return list(db.courses.find({'faculty_id': faculty_id}).sort('course_code', 1))


def get_courses_by_student(student_id) -> list:
    db = get_db()
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    return list(db.courses.find({'enrolled_students': student_id}).sort('course_code', 1))


def update_course(course_id, updates: dict) -> bool:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    result = db.courses.update_one({'_id': course_id}, {'$set': updates})
    return result.modified_count > 0


def delete_course(course_id) -> bool:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    result = db.courses.delete_one({'_id': course_id})
    return result.deleted_count > 0


def enroll_student(course_id, student_id) -> bool:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    result = db.courses.update_one(
        {'_id': course_id},
        {'$addToSet': {'enrolled_students': student_id}}
    )
    # Also update the user's enrolled_courses
    db.users.update_one(
        {'_id': student_id},
        {'$addToSet': {'enrolled_courses': course_id}}
    )
    return result.modified_count >= 0


def unenroll_student(course_id, student_id) -> bool:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    result = db.courses.update_one(
        {'_id': course_id},
        {'$pull': {'enrolled_students': student_id}}
    )
    db.users.update_one(
        {'_id': student_id},
        {'$pull': {'enrolled_courses': course_id}}
    )
    return result.modified_count >= 0


def get_enrolled_count(course_id) -> int:
    db = get_db()
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    course = db.courses.find_one({'_id': course_id}, {'enrolled_students': 1})
    if course:
        return len(course.get('enrolled_students', []))
    return 0
