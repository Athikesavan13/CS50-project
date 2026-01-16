from flask import Flask, render_template, request, redirect, session
from cs50 import SQL
from helpers import login_required, apology, trait_vector, similarity, DisjointSet,admin_required
from functools import wraps
from flask import session, redirect, render_template


# -------------------------------
# App configuration
# -------------------------------
app = Flask(__name__)
app.secret_key = "super-secret-key"

# -------------------------------
# Database connections
# -------------------------------
auth_db = SQL("sqlite:///databases/auth.db")
occupancy_db = SQL("sqlite:///databases/occupancy.db")
profile_db = SQL("sqlite:///databases/profile.db")
traits_db = SQL("sqlite:///databases/traits.db")
occupancy_db = SQL("sqlite:///databases/occupancy.db")

def no_room_assigned_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")

        if occupancy_db.execute(
            "SELECT 1 FROM room_members WHERE student_id = ?",
            user_id
        ):
            return redirect("/dashboard")

        return f(*args, **kwargs)
    return wrapper


# -------------------------------
# Landing Page (Hostel Selection)
# -------------------------------
@app.route("/")
@login_required
def index():
    hostels = occupancy_db.execute(
        "SELECT id, name FROM hostels ORDER BY id"
    )
    return render_template("index.html", hostels=hostels)

# -------------------------------
# Student Dashboard
# -------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]

    # Fetch user info (auth.db)
    user = auth_db.execute(
        "SELECT sr, name, photo FROM users WHERE id = ?",
        user_id
    )[0]

    # Fetch current room + hostel details (occupancy.db)
    room_info = occupancy_db.execute("""
        SELECT
            h.name AS hostel_name,
            f.floor_number,
            r.room_number
        FROM room_members rm
        JOIN rooms r ON rm.room_id = r.id
        JOIN floors f ON r.floor_id = f.id
        JOIN hostels h ON r.hostel_id = h.id
        WHERE rm.student_id = ?
    """, user_id)

    # If student not yet assigned a room
    address = None
    if room_info:
        address = room_info[0]

    return render_template(
        "dashboard.html",
        user=user,
        address=address
    )

# -------------------------------
# Logout
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session.clear()


    if request.method == "POST":
        sr = request.form["sr"]
        password = request.form["password"]
        role = request.form["role"]

        rows = auth_db.execute(
            "SELECT * FROM users WHERE sr = ? AND role = ?",
            sr, role
        )

        if len(rows) != 1:
            return apology("Invalid ID or role")

        user = rows[0]

        # Student rule
        # Student rule
        if role == "student":
            if password != sr[-5:]:
                return apology("Invalid password")

        # Admin rule
        if role == "admin":
            if password != user["password"]:
                return apology("Invalid password")

        # SET SESSION (FOR BOTH)
        session["user_id"] = user["id"]
        session["role"] = user["role"]

        # REDIRECT BASED ON ROLE
        if role == "admin":
            return redirect("/admin/dashboard")

        return redirect("/dashboard")


    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    sr = request.form.get("sr")

    # Check missing fields
    if not name or not sr:
        return apology("Missing registration details",return_to="/login?tab=student-register")

    # Validate name: only letters and spaces
    cleaned_name = name.replace(" ", "")
    if not cleaned_name.isalpha():
        return apology("Name must contain only letters and spaces", return_to="/login?tab=student-register")

    # Validate SR
    if not sr.isdigit() or len(sr) != 10:
        return apology("SR number must be exactly 10 digits", return_to="/login?tab=student-register")

    # Check unique SR
    existing = auth_db.execute(
        "SELECT id FROM users WHERE sr = ?",
        sr
    )
    if existing:
        return apology("Student already registered", return_to="/login?tab=student-register")

    # Deterministic password
    password = sr[-5:]

    # Insert student (NO session set here)
    auth_db.execute(
        "INSERT INTO users (sr, name, password, role) VALUES (?, ?, ?, 'student')",
        sr, name.strip(), password
    )

    # Store one-time success message
    session.clear()
    session["message"] = "Registration successful. Please login."

    # Redirect to login page
    return redirect("/login")

@app.route("/rooms")
@no_room_assigned_required
@login_required
def rooms():
    hostels = occupancy_db.execute(
        "SELECT id, name FROM hostels ORDER BY id"
    )
    return render_template("rooms_hostels.html", hostels=hostels)


@app.route("/rooms/<int:hostel_id>")
@no_room_assigned_required
@login_required
def hostel_floors(hostel_id):
    hostel = occupancy_db.execute(
        "SELECT id, name FROM hostels WHERE id = ?",
        hostel_id
    )

    if not hostel:
        return apology("Invalid hostel")

    floors = occupancy_db.execute(
        "SELECT id, floor_number FROM floors WHERE hostel_id = ? ORDER BY floor_number ASC",
        hostel_id
    )

    return render_template(
        "rooms_floors.html",
        hostel=hostel[0],
        floors=floors
    )


@app.route("/rooms/<int:hostel_id>/<int:floor_id>")
@no_room_assigned_required
@login_required
def floor_rooms(hostel_id, floor_id):
    rooms = occupancy_db.execute("""
        SELECT
            r.id,
            r.room_number,
            r.capacity,
            r.is_locked,
            COUNT(rm.student_id) AS occupied
        FROM rooms r
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.floor_id = ?
        GROUP BY r.id
        ORDER BY r.room_number ASC
    """, floor_id)

    floor = occupancy_db.execute(
        "SELECT floor_number FROM floors WHERE id = ?",
        floor_id
    )

    if not floor:
        return apology("Invalid floor")

    return render_template(
        "rooms_grid.html",
        rooms=rooms,
        floor=floor[0],
        hostel_id=hostel_id,
        floor_id=floor_id
    )

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    user = auth_db.execute(
        "SELECT sr, name, photo FROM users WHERE id = ?",
        user_id
    )[0]
    print(user)

    profile = profile_db.execute(
        "SELECT * FROM profiles WHERE student_id = ?",
        user_id
    )

    return render_template(
        "profile.html",
        user=user,
        profile=profile[0] if profile else None
    )

@app.route("/profile", methods=["POST"])
@login_required
def save_profile():
    user_id = session["user_id"]

    phone = request.form.get("phone")
    parent_name = request.form.get("parent_name")
    parent_phone = request.form.get("parent_phone")
    id_proof = request.form.get("id_proof")

    if not phone or not parent_name or not parent_phone or not id_proof:
        return apology("All profile fields are required", "/profile")

    existing = profile_db.execute(
        "SELECT student_id FROM profiles WHERE student_id = ?",
        user_id
    )

    if existing:
        profile_db.execute("""
            UPDATE profiles
            SET phone=?, parent_name=?, parent_phone=?, id_proof=?, updated_at=CURRENT_TIMESTAMP
            WHERE student_id=?
        """, phone, parent_name, parent_phone, id_proof, user_id)
    else:
        profile_db.execute("""
            INSERT INTO profiles (student_id, phone, parent_name, parent_phone, id_proof)
            VALUES (?, ?, ?, ?, ?)
        """, user_id, phone, parent_name, parent_phone, id_proof)

    return redirect("/profile")


@app.route("/profile/photo", methods=["POST"])
@login_required
def upload_photo():
    file = request.files.get("photo")

    if not file:
        return apology("No file selected", "/profile")

    filename = f"{session['user_id']}.jpg"
    path1 = f"images/profiles/{filename}"
    path = f"static/images/profiles/{filename}"
    file.save(path)

    auth_db.execute(
        "UPDATE users SET photo = ? WHERE id = ?",
        path1,
        session["user_id"]
    )

    return redirect("/profile")

@app.route("/rooms/<int:hostel_id>/<int:floor_id>/<int:room_id>")
@no_room_assigned_required
@login_required
def room_detail(hostel_id, floor_id, room_id):

    # Validate room
    room = occupancy_db.execute("""
        SELECT id, room_number, capacity, is_locked
        FROM rooms
        WHERE id = ? AND hostel_id = ? AND floor_id = ?
    """, room_id, hostel_id, floor_id)

    if not room:
        return apology("Invalid room")

    room = room[0]

    # Get student IDs from occupancy DB
    members = occupancy_db.execute("""
        SELECT student_id
        FROM room_members
        WHERE room_id = ?
        ORDER BY joined_at ASC
    """, room_id)

    # Fetch student details from auth DB
    slots = []

    for m in members:
        user = auth_db.execute("""
            SELECT id, name, photo
            FROM users
            WHERE id = ?
        """, m["student_id"])

        if user:
            slots.append({
                "filled": True,
                "name": user[0]["name"],
                "photo": user[0]["photo"]
            })

    # Fill remaining slots
    while len(slots) < room["capacity"]:
        slots.append({"filled": False})

    return render_template(
        "room_detail.html",
        room=room,
        hostel_id=hostel_id,
        floor_id=floor_id,
        room_id=room_id,
        slots=slots
    )


@app.route("/questionnaire", methods=["POST"])
@login_required
def submit_questionnaire():
    floor_id = session.get("floor_id")

    if not floor_id:
        return apology("Invalid flow", "/rooms")


    user_id = session["user_id"]

    # Save traits EXACTLY as schema defines
    traits_db.execute("""
        INSERT OR REPLACE INTO traits
        (student_id, cleanliness, sleep, noise, calls, study, sharing, laundary, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        user_id,
        float(request.form.get("cleanliness")),
        float(request.form.get("sleep")),
        float(request.form.get("noise")),
        float(request.form.get("calls")),
        float(request.form.get("study")),
        float(request.form.get("sharing")),
        float(request.form.get("laundary")),
        float(request.form.get("language"))
    )



    # --- GET MY TRAITS ---
    me = traits_db.execute(
        "SELECT * FROM traits WHERE student_id = ?",
        user_id
    )[0]

    my_vec = trait_vector(me)

    # --- GET FLOOR CANDIDATES ---
    candidates = occupancy_db.execute("""
        SELECT DISTINCT rm.student_id
        FROM room_members rm
        JOIN rooms r ON rm.room_id = r.id
        WHERE r.floor_id = ?
    """, floor_id)

    if not candidates:
        # No students yet on this floor
        session["top_matches"] = []
        return redirect(f"/choose-room/floor/{floor_id}")

    dsu = DisjointSet()
    results = []

    for c in candidates:
        other = traits_db.execute(
            "SELECT * FROM traits WHERE student_id = ?",
            c["student_id"]
        )

        if not other:
            continue

        other_vec = trait_vector(other[0])
        score = similarity(my_vec, other_vec)

        results.append({
            "student_id": c["student_id"],
            "score": round(score * 100, 1)  # percentage
        })

        if score >= 0.6:
            dsu.union(user_id, c["student_id"])

    # --- TOP 3 ---
    top3 = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

    session["top_matches"] = top3
    session["cluster"] = dsu.find(user_id)

    return redirect(f"/recommendations/floor/{floor_id}")



@app.route("/recommendations/floor/<int:floor_id>")
@no_room_assigned_required
@login_required

def recommendations_floor(floor_id):

    matches = session.get("top_matches", [])

    enriched = []
    for m in matches:
        user = auth_db.execute(
            "SELECT name, photo FROM users WHERE id = ?",
            m["student_id"]
        )
        if user:
            enriched.append({
                "name": user[0]["name"],
                "photo": user[0]["photo"],
                "score": m["score"]
            })

    return render_template(
        "recommendations.html",
        matches=enriched,
        floor_id=floor_id
    )


@app.route("/questionnaire/floor/<int:floor_id>")
@no_room_assigned_required
@login_required

def questionnaire_floor(floor_id):

    user_id = session["user_id"]

    # Check if student already assigned
    if occupancy_db.execute(
        "SELECT 1 FROM room_members WHERE student_id = ?",
        user_id
    ):
        return apology("You are already assigned to a room", "/dashboard")

    # Check if floor has ANY free slot
    free = occupancy_db.execute("""
        SELECT 1
        FROM rooms r
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.floor_id = ?
        GROUP BY r.id
        HAVING COUNT(rm.student_id) < r.capacity
        LIMIT 1
    """, floor_id)

    if not free:
        return apology("No available slots on this floor", "/rooms")

    # Store floor in session (important)
    session["floor_id"] = floor_id
    existing_traits = traits_db.execute(
        "SELECT 1 FROM traits WHERE student_id = ?",
        user_id
    )
    if existing_traits:
        return redirect(f"/recommendations/floor/{floor_id}")

    return render_template("questionnaire.html")

@app.route("/choose-room/floor/<int:floor_id>")
@no_room_assigned_required
@login_required

def choose_room_floor(floor_id):

    rooms = occupancy_db.execute("""
        SELECT r.id, r.room_number, r.capacity,
               COUNT(rm.student_id) AS occupied
        FROM rooms r
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.floor_id = ?
        GROUP BY r.id
        HAVING occupied < r.capacity
    """, floor_id)

    return render_template(
        "choose_room.html",
        rooms=rooms,
        floor_id=floor_id
    )

@app.route("/assign-room/<int:room_id>", methods=["POST"])
@no_room_assigned_required
@login_required

def assign_room(room_id):
    user_id = session["user_id"]

    already = occupancy_db.execute(
        "SELECT 1 FROM room_members WHERE student_id = ?",
        user_id
    )
    if already:
        return apology("You are already assigned", "/dashboard")

    occupancy_db.execute(
        "INSERT INTO room_members (room_id, student_id) VALUES (?, ?)",
        room_id, user_id
    )

    return redirect("/dashboard")

@app.route("/admin/dashboard")
@admin_required
@login_required

def admin_dashboard():
    students = occupancy_db.execute("""
        SELECT
            rm.student_id,
            h.name AS hostel,
            f.floor_number,
            r.room_number
        FROM room_members rm
        JOIN rooms r ON rm.room_id = r.id
        JOIN floors f ON r.floor_id = f.id
        JOIN hostels h ON r.hostel_id = h.id
        ORDER BY h.name, f.floor_number, r.room_number
    """)

    # enrich with auth.db data
    for s in students:
        user = auth_db.execute(
            "SELECT name, sr FROM users WHERE id = ?",
            s["student_id"]
        )[0]
        s["name"] = user["name"]
        s["sr"] = user["sr"]

    return render_template("admin_dashboard.html", students=students)


@app.route("/admin/expel/<int:student_id>", methods=["POST"])
@admin_required
@login_required

def admin_expel(student_id):
    occupancy_db.execute(
        "DELETE FROM room_members WHERE student_id = ?",
        student_id
    )
    return redirect("/admin/dashboard")

@app.route("/admin/modify/<int:student_id>")
@admin_required
@login_required

def admin_modify(student_id):

    student = auth_db.execute(
        "SELECT id, name, sr FROM users WHERE id = ?",
        student_id
    )[0]

    rooms = occupancy_db.execute("""
        SELECT r.id, h.name AS hostel, f.floor_number, r.room_number,
               COUNT(rm.student_id) AS occupied, r.capacity
        FROM rooms r
        JOIN floors f ON r.floor_id = f.id
        JOIN hostels h ON r.hostel_id = h.id
        LEFT JOIN room_members rm ON r.id = rm.room_id
        GROUP BY r.id
        HAVING occupied < capacity
    """)

    return render_template(
        "admin_modify_room.html",
        student=student,
        rooms=rooms
    )


@app.route("/admin/assign/<int:student_id>/<int:room_id>", methods=["POST"])
@admin_required
@login_required

def admin_assign(student_id, room_id):

    occupancy_db.execute(
        "DELETE FROM room_members WHERE student_id = ?",
        student_id
    )

    occupancy_db.execute(
        "INSERT INTO room_members (room_id, student_id) VALUES (?, ?)",
        room_id, student_id
    )

    return redirect("/admin/dashboard")



# -------------------------------
# App runner (CS50 style)
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)

