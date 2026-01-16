```markdown
# 🏠Smart Hostel Room Allocation & Roommate Matching System

# Name : Athikesvan Velsamy
# EdX Username : AthiK7_Velsamy
# Github Username : Athikesavan13
# Location : Bangalore, Karnataka, India
# Date of Submission : 03-Jan-2026

# Unlisted Youtube Video Link : https://www.youtube.com/watch?v=IScOjFz1DJY

## CS50 Final Project

A web-based hostel accommodation system that allows students to register, fill a roommate questionnaire, receive compatibility-based recommendations, and choose rooms, while providing administrators full control over student accommodations.

---

## 📌 Project Overview

This system solves the problem of **fair and structured hostel room allocation** by combining:

- Authentication & role-based access (Student / Admin)
- Profile management
- Questionnaire-based roommate matching
- Controlled room selection
- Administrative override and management

The project is built using **Flask**, **SQLite**, and **Jinja2 templates**.

---

## 🧠 High-Level System Design

The system is intentionally split into **multiple databases** to maintain separation of concerns:

| Database | Purpose |
|--------|---------|
| `auth.db` | User authentication (students & admins) |
| `profile.db` | Student personal details |
| `traits.db` | Questionnaire responses |
| `occupancy.db` | Hostels, floors, rooms, room assignments |

This design avoids tight coupling between authentication, personal data, and room allocation logic.

---

## 🔁 Application Flow (Student)

```

Login
↓
Dashboard
↓
(If not assigned)
Choose Hostel
↓
Choose Floor
↓
Questionnaire
↓
Roommate Recommendations
↓
Choose Room
↓
Assigned → Dashboard (locked)

```

Once a student is assigned a room, **all room-selection routes are disabled**.

---

## 🔐 Application Flow (Admin)

```

Admin Login
↓
Admin Dashboard
↓
View All Assigned Students
↓
[Expel Student] OR [Modify Room]

```

Admins can:
- Remove a student from accommodation
- Reassign students to different rooms
- Override all student restrictions

---

## 🧩 Core Components

### 1️⃣ Authentication System
- Students login using SR number + derived password
- Admins login using manually created credentials
- Session-based authentication
- Role stored in session (`student` / `admin`)

---

### 2️⃣ Decorator-Based Access Control

Custom decorators enforce system rules:

- `login_required` → user must be logged in
- `admin_required` → admin-only routes
- `no_room_assigned_required` → blocks room flow once assigned

These decorators together form a **finite-state machine** for user actions.

---

### 3️⃣ Questionnaire & Matching Engine

Students fill a questionnaire covering:
- Cleanliness
- Sleep schedule
- Noise tolerance
- Study habits
- Sharing preference
- Laundry frequency
- Language preference

Traits are stored as numerical values and compared using **Euclidean distance** to compute compatibility scores.
Top matches are shown before room selection.

---

### 4️⃣ Room Allocation Logic

- Rooms have fixed capacity
- Only rooms with free slots are displayed
- Assignment happens via POST requests
- Duplicate assignment is prevented at database level

Once assigned:
- Student cannot re-enter questionnaire or room selection
- Dashboard displays final hostel, floor, and room

---

### 5️⃣ Admin Management System

Admins see a table containing:
- Student name and SR number
- Hostel, floor, and room details

Admin actions:
- **Expel** → removes room assignment
- **Modify** → assign a new room via a new tab

Admins bypass all student flow restrictions.

---

## 🗂️ Project Structure

```project/
│
├── app.py                  # Main Flask application
├── helpers.py              # Decorators & utilities
│
├── databases/
│   ├── auth.db             # Authentication database
│   ├── profile.db          # User profile data
│   ├── traits.db           # Questionnaire & traits
│   └── occupancy.db        # Room occupancy & locks
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── rooms_hostels.html
│   ├── rooms_floors.html
│   ├── rooms_grid.html
│   ├── questionnaire.html
│   ├── recommendations.html
│   ├── choose_room.html
│   ├── admin_dashboard.html
│   └── admin_modify_room.html
│
├── static/
│   ├── css/
│   │   └── styles.css
│   └── images/
│       ├── profiles/
│       └── Hostels/
│
└── README.md


```

---

## 🧪 Error Handling & Debugging

The project includes:
- Graceful redirects for invalid access
- Protection against session loss
- Prevention of duplicate room assignments
- Clear separation of read-only vs state-changing routes

Several real-world integration bugs were identified and fixed during development, including:
- Session clearing at incorrect times
- Redirects before session initialization
- Incorrect database usage across modules
- Route responsibility mismatches

---

## ⚠️ Known Limitations

- No password hashing (educational scope)
- No concurrent transaction locking
- No email notifications
- SQLite used instead of a production database

These trade-offs are acceptable for a CS50 final project.

---

## 🎯 Learning Outcomes

Through this project, I learned:
- Flask routing and decorators
- Session management
- Database normalization and separation
- Multi-role system design
- Debugging real-world backend issues
- Structuring a complete web application

---

## ✅ Final Notes

This project focuses on **system design, correctness, and understanding**, rather than line-by-line originality.
All components were integrated, debugged, and extended with a clear understanding of how the system works.
```
