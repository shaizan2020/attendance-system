# 📋 AttendMS — NoSQL-Based Attendance Management System

A scalable attendance tracking system for educational institutions using **MongoDB**, **Flask**, and **QR code-based attendance marking**.

---

## 🏗️ Architecture

- **Frontend**: HTML5 + CSS3 (premium dark theme) + JavaScript
- **Backend**: Python Flask with Blueprint-based REST API
- **Database**: MongoDB (NoSQL, document-based)
- **QR Scanning**: html5-qrcode (browser-based camera scanning)

---

## 📂 Folder Structure

```
NO-SQL PROJECT/
├── app.py                # Flask entry point
├── config.py             # Configuration + MongoDB connection
├── seed_data.py          # DB seed script (run once)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── models/               # MongoDB collection helpers
│   ├── user.py
│   ├── course.py
│   ├── session.py
│   └── attendance.py
├── routes/               # Flask Blueprints
│   ├── auth.py           # Login / logout
│   ├── admin.py          # Admin CRUD endpoints
│   ├── faculty.py        # Session + QR + reports
│   └── student.py        # Scan + mark + history
├── utils/
│   ├── qr_generator.py   # QR base64 generator
│   ├── validators.py     # 7-layer QR validation
│   └── reports.py        # CSV export + analytics
├── static/
│   ├── css/style.css     # Global styles
│   └── js/main.js        # Common JS
└── templates/            # Jinja2 HTML templates
    ├── base.html / login.html / 404.html / 500.html
    ├── admin/  (dashboard, users, courses)
    ├── faculty/(dashboard, create_session, view_session, reports)
    └── student/(dashboard, scan, history)
```

---

## 🚀 Deployment Instructions

### Prerequisites

1. **Python 3.10+** installed
2. **MongoDB 6.0+** installed and running on `localhost:27017`
   - Windows: Start MongoDB service → `net start MongoDB`
   - Or start manually: `mongod --dbpath "C:\data\db"`

### Setup Steps

```powershell
# 1. Navigate to project
cd "c:\Users\syeds\Desktop\NO-SQL PROJECT"

# 2. Install dependencies (already done)
pip install -r requirements.txt

# 3. Seed the database (run once)
python seed_data.py

# 4. Start the Flask server
python app.py
```

### 5. Open in browser
```
http://localhost:5000
```

---

## 🔑 Demo Credentials

| Role    | Email              | Password    |
|---------|--------------------|-------------|
| 👨‍💼 Admin   | admin@ams.com      | admin123    |
| 👨‍🏫 Faculty | faculty@ams.com    | faculty123  |
| 👨‍🏫 Faculty | faculty2@ams.com   | faculty123  |
| 👨‍🎓 Student | student@ams.com    | student123  |
| 👨‍🎓 Student | student2@ams.com   | student123  |
| 👨‍🎓 Student | student3@ams.com   | student123  |

---

## 📊 API Endpoints

### Auth
| Method | Endpoint       | Description |
|--------|---------------|-------------|
| POST   | /auth/login   | Login       |
| GET    | /auth/logout  | Logout      |

### Admin
| Method | Endpoint                       | Description         |
|--------|-------------------------------|---------------------|
| GET    | /admin/dashboard              | Analytics overview  |
| GET    | /admin/users                  | List users          |
| POST   | /admin/users/create           | Create user         |
| POST   | /admin/users/\<id>/edit       | Edit user           |
| POST   | /admin/users/\<id>/delete     | Delete user         |
| GET    | /admin/courses                | List courses        |
| POST   | /admin/courses/create         | Create course       |
| POST   | /admin/courses/\<id>/delete   | Delete course       |
| POST   | /admin/courses/\<id>/enroll   | Enroll student      |

### Faculty
| Method | Endpoint                            | Description              |
|--------|-------------------------------------|--------------------------|
| GET    | /faculty/dashboard                  | Faculty home             |
| POST   | /faculty/sessions/create            | Create session + QR      |
| GET    | /faculty/sessions/\<id>             | Live attendance view     |
| POST   | /faculty/sessions/\<id>/close       | Close session            |
| GET    | /faculty/reports?course_id=\<id>   | Attendance report        |
| GET    | /faculty/reports/\<id>/export      | Download CSV             |
| GET    | /faculty/api/sessions/\<id>/live   | Live count (JSON)        |

### Student
| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | /student/dashboard | Home + attendance %      |
| GET    | /student/scan      | QR scanner page          |
| POST   | /student/mark      | Mark attendance (JSON)   |
| GET    | /student/history   | Attendance history       |

---

## 🗄️ MongoDB Collections

| Collection           | Key Fields                                     |
|----------------------|------------------------------------------------|
| `users`             | email (unique), role, student_id, enrolled_courses |
| `courses`           | course_code (unique), faculty_id, enrolled_students |
| `attendance_sessions` | session_token (unique), expires_at, status  |
| `attendance_records` | (session_id + student_id) compound unique index |

---

## 🔐 QR Validation Flow

1. Parse JSON payload from QR
2. Check `expires_at` in payload vs current UTC
3. Lookup session by token in MongoDB
4. Verify session `status == 'active'`
5. Verify server-side `expires_at`
6. Verify student is enrolled in the course
7. Check no duplicate attendance record

---

## 📤 Sample Request/Response

### Mark Attendance
**POST** `/student/mark`
```json
// Request
{ "qr_data": "{\"token\":\"abc123...\",\"expires_at\":\"2024-01-01T10:00:00+00:00\"}" }

// Success Response
{ "success": true, "message": "Attendance marked successfully for Database Management!" }

// Error Response
{ "success": false, "message": "QR code has expired." }
```
