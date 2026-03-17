"""
Seed Data Script - run once to populate MongoDB with demo data.
Usage: python seed_data.py
"""
import sys
import io
# Force UTF-8 on Windows to avoid cp1252 emoji errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from config import get_db
from models.user import create_user
from models.course import create_course, enroll_student

def seed():
    db = get_db()
    print("Clearing existing data...")
    db.users.delete_many({})
    db.courses.delete_many({})
    db.attendance_sessions.delete_many({})
    db.attendance_records.delete_many({})

    print("Seeding users...")
    admin = create_user("System Admin", "admin@ams.com", "admin123", "admin")
    print("  [OK] Admin: admin@ams.com / admin123")

    faculty1 = create_user("Dr. Sarah Johnson", "faculty@ams.com", "faculty123", "faculty")
    faculty2 = create_user("Prof. Michael Chen", "faculty2@ams.com", "faculty123", "faculty")
    print("  [OK] Faculty: faculty@ams.com / faculty123")
    print("  [OK] Faculty: faculty2@ams.com / faculty123")

    students = []
    student_data = [
        ("Alice Thompson", "student@ams.com",  "student123", "STU-2024-001"),
        ("Bob Martinez",   "student2@ams.com", "student123", "STU-2024-002"),
        ("Carol Williams", "student3@ams.com", "student123", "STU-2024-003"),
        ("David Lee",      "student4@ams.com", "student123", "STU-2024-004"),
        ("Emma Davis",     "student5@ams.com", "student123", "STU-2024-005"),
    ]
    for name, email, pwd, sid in student_data:
        s = create_user(name=name, email=email, password=pwd, role="student", student_id=sid)
        students.append(s)
        print(f"  [OK] Student: {email} / {pwd}")

    print("\nSeeding courses...")
    course1 = create_course("CS101", "Introduction to Computer Science", faculty1['_id'])
    course2 = create_course("DS201", "Data Structures and Algorithms",   faculty1['_id'])
    course3 = create_course("DB301", "Database Management Systems",      faculty2['_id'])
    course4 = create_course("WD401", "Web Development",                  faculty2['_id'])
    print("  [OK] Courses: CS101, DS201, DB301, WD401")

    print("\nEnrolling students...")
    for s in students:
        enroll_student(course1['_id'], s['_id'])
        enroll_student(course3['_id'], s['_id'])
    for s in students[:3]:
        enroll_student(course2['_id'], s['_id'])
    for s in students[2:]:
        enroll_student(course4['_id'], s['_id'])
    print("  [OK] Enrollments complete")

    print("\n" + "="*50)
    print("[SUCCESS] Database seeded!")
    print("="*50)
    print("  Admin:   admin@ams.com / admin123")
    print("  Faculty: faculty@ams.com / faculty123")
    print("  Student: student@ams.com / student123")
    print("Open: http://localhost:5000")

if __name__ == '__main__':
    seed()
