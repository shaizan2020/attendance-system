import bcrypt
from datetime import datetime, timezone
from bson import ObjectId
from config import get_db


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_user(name: str, email: str, password: str, role: str,
                student_id: str = None, enrolled_courses: list = None) -> dict:
    db = get_db()
    doc = {
        'name': name,
        'email': email.lower().strip(),
        'password_hash': hash_password(password),
        'role': role,  # admin | faculty | student
        'student_id': student_id,
        'enrolled_courses': enrolled_courses or [],
        'created_at': datetime.now(timezone.utc),
    }
    result = db.users.insert_one(doc)
    doc['_id'] = result.inserted_id
    return doc


def get_user_by_email(email: str) -> dict | None:
    db = get_db()
    return db.users.find_one({'email': email.lower().strip()})


def get_user_by_id(user_id) -> dict | None:
    db = get_db()
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.find_one({'_id': user_id})


def get_all_users(role: str = None) -> list:
    db = get_db()
    query = {'role': role} if role else {}
    return list(db.users.find(query).sort('created_at', -1))


def update_user(user_id, updates: dict) -> bool:
    db = get_db()
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    if 'password' in updates:
        updates['password_hash'] = hash_password(updates.pop('password'))
    result = db.users.update_one({'_id': user_id}, {'$set': updates})
    return result.modified_count > 0


def delete_user(user_id) -> bool:
    db = get_db()
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    result = db.users.delete_one({'_id': user_id})
    return result.deleted_count > 0


def enroll_student_in_course(student_id, course_id) -> bool:
    db = get_db()
    if isinstance(student_id, str):
        student_id = ObjectId(student_id)
    if isinstance(course_id, str):
        course_id = ObjectId(course_id)
    result = db.users.update_one(
        {'_id': student_id},
        {'$addToSet': {'enrolled_courses': course_id}}
    )
    return result.modified_count > 0


def count_users_by_role() -> dict:
    db = get_db()
    pipeline = [
        {'$group': {'_id': '$role', 'count': {'$sum': 1}}}
    ]
    return {doc['_id']: doc['count'] for doc in db.users.aggregate(pipeline)}
