from flask import Flask, request, jsonify, send_from_directory, session, redirect
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os


# ============================================================
# PATH CONFIGURATION
# ============================================================

# app.py:
#
# main/
# └── backend/
#     └── app.py
#
# Therefore:
# parent       = backend
# parent.parent = main

BASE_DIR = Path(__file__).resolve().parent.parent

# Your frontend is now directly inside main/
HTDOCS_DIR = BASE_DIR

# Database will be:
# main/datasaves.db
DB_PATH = BASE_DIR / "datasaves.db"


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=str(HTDOCS_DIR / "static"),
    static_url_path="/static"
)


# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = os.environ.get(
    "data11ict_SECRET",
    "data11ict-development-secret-change-this"
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            section TEXT DEFAULT 'ICT 11-2',
            role TEXT DEFAULT 'student',
            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # NOTES TABLE
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,
            content TEXT DEFAULT '',

            subject TEXT DEFAULT 'ICT 11-2',

            color TEXT DEFAULT 'blue',

            important INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            pinned INTEGER DEFAULT 0,

            author TEXT DEFAULT '',

            due_date TEXT,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    # ========================================================
    # DEFAULT USERS
    # ========================================================

    users = [
        (
            "2026-STJAMES-5831",
            "B1-2026-2354",
            "Zyrille Cruz",
            "ICT 11-2",
            "student"
        ),
        (
            "2026-STJAMES-5213",
            "B2-2026-5432",
            "Ceejay Garcia",
            "ICT 11-2",
            "student"
        ),
        (
            "2026-STJAMES-3475",
            "B3-2026-3475",
            "Andrei Villarama",
            "ICT 11-2",
            "student"
        )
    ]

    for username, password, full_name, section, role in users:

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if not existing:

            conn.execute("""
                INSERT INTO users (
                    username,
                    password,
                    full_name,
                    section,
                    role,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username,
                generate_password_hash(password),
                full_name,
                section,
                role,
                datetime.now().isoformat(
                    timespec="seconds"
                )
            ))

    conn.commit()

    # ========================================================
    # CREATE PERSONAL WELCOME NOTE FOR EACH ACCOUNT
    # ========================================================

    registered_users = conn.execute("""
        SELECT
            id,
            username,
            full_name,
            section
        FROM users
        ORDER BY id ASC
    """).fetchall()

    for user in registered_users:

        note_count = conn.execute("""
            SELECT COUNT(*)
            FROM notes
            WHERE user_id = ?
        """, (
            user["id"],
        )).fetchone()[0]

        # Only create the welcome note if the user
        # doesn't have any notes yet.

        if note_count == 0:

            now = datetime.now().isoformat(
                timespec="seconds"
            )

            conn.execute("""
                INSERT INTO notes (
                    user_id,
                    title,
                    content,
                    subject,
                    color,
                    important,
                    completed,
                    pinned,
                    author,
                    due_date,
                    created_at,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                user["id"],

                "ICT100",

                (
                    f"Welcome {user['full_name']}! "
                    "This is your personal NotePlan workspace."
                ),

                user["section"],

                "blue",

                0,
                0,
                1,

                user["full_name"],

                None,

                now,
                now
            ))

    conn.commit()
    conn.close()


# ============================================================
# SERIALIZE NOTE
# ============================================================

def serialize_note(row):

    note = dict(row)

    note["important"] = bool(
        note["important"]
    )

    note["completed"] = bool(
        note["completed"]
    )

    note["pinned"] = bool(
        note["pinned"]
    )

    return note


# ============================================================
# AUTH HELPERS
# ============================================================

def login_required():

    return "user_id" in session


def get_current_user_id():

    return session.get("user_id")


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def home():

    if not login_required():

        return redirect("/login/")

    return send_from_directory(
        HTDOCS_DIR,
        "index.html"
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/login/")
def login_page():

    if login_required():

        return redirect("/")

    return send_from_directory(
        HTDOCS_DIR / "login",
        "index.html"
    )


# ============================================================
# IMAGES
# ============================================================

@app.route("/images/<path:filename>")
def images(filename):

    return send_from_directory(
        HTDOCS_DIR / "images",
        filename
    )


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/api/me")
def get_current_user():

    if not login_required():

        return jsonify({
            "authenticated": False
        }), 401

    conn = get_db()

    user = conn.execute("""
        SELECT
            id,
            username,
            full_name,
            section,
            role
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    conn.close()

    if not user:

        session.clear()

        return jsonify({
            "authenticated": False
        }), 401

    return jsonify({
        "authenticated": True,
        "user": dict(user)
    })


# ============================================================
# LOGIN API
# ============================================================

@app.post("/api/login")
def login():

    data = request.get_json(
        silent=True
    ) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:

        return jsonify({
            "error": "Username and password are required."
        }), 400

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (
        username,
    )).fetchone()

    conn.close()

    if not user:

        return jsonify({
            "error": "Invalid username or password."
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "error": "Invalid username or password."
        }), 401

    # Clear previous session
    session.clear()

    # Create new session
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]

    return jsonify({
        "success": True,

        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "section": user["section"],
            "role": user["role"]
        }
    })


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


# ============================================================
# GET NOTES
# ============================================================

@app.get("/api/notes")
def get_notes():

    if not login_required():

        return jsonify({
            "error": "Authentication required."
        }), 401

    search = request.args.get(
        "q",
        ""
    ).strip()

    subject = request.args.get(
        "subject",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    user_id = get_current_user_id()

    conn = get_db()

    # IMPORTANT:
    # Only retrieve notes belonging to the
    # currently logged-in user.

    query = """
        SELECT *
        FROM notes
        WHERE user_id = ?
    """

    params = [
        user_id
    ]

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        query += """
            AND (
                title LIKE ?
                OR content LIKE ?
                OR subject LIKE ?
            )
        """

        value = f"%{search}%"

        params.extend([
            value,
            value,
            value
        ])

    # --------------------------------------------------------
    # SUBJECT
    # --------------------------------------------------------

    if subject and subject != "all":

        query += """
            AND subject = ?
        """

        params.append(subject)

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if status == "important":

        query += """
            AND important = 1
        """

    elif status == "completed":

        query += """
            AND completed = 1
        """

    elif status == "active":

        query += """
            AND completed = 0
        """

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    query += """
        ORDER BY
            pinned DESC,
            updated_at DESC,
            id DESC
    """

    rows = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return jsonify([
        serialize_note(row)
        for row in rows
    ])


# ============================================================
# CREATE NOTE
# ============================================================

@app.post("/api/notes")
def create_note():

    if not login_required():

        return jsonify({
            "error": "Authentication required."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get("title", "")
    ).strip()

    content = str(
        data.get("content", "")
    ).strip()

    if not title:

        return jsonify({
            "error": "Note title is required."
        }), 400

    user_id = get_current_user_id()

    conn = get_db()

    # Get current user
    user = conn.execute("""
        SELECT
            id,
            full_name,
            section
        FROM users
        WHERE id = ?
    """, (
        user_id,
    )).fetchone()

    if not user:

        conn.close()

        session.clear()

        return jsonify({
            "error": "User account not found."
        }), 401

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    cursor = conn.execute("""
        INSERT INTO notes (
            user_id,
            title,
            content,
            subject,
            color,
            important,
            completed,
            pinned,
            author,
            due_date,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        user_id,

        title,

        content,

        data.get(
            "subject",
            user["section"]
        ),

        data.get(
            "color",
            "blue"
        ),

        int(bool(
            data.get(
                "important",
                False
            )
        )),

        int(bool(
            data.get(
                "completed",
                False
            )
        )),

        int(bool(
            data.get(
                "pinned",
                False
            )
        )),

        user["full_name"],

        data.get(
            "due_date"
        ) or None,

        now,
        now
    ))

    note_id = cursor.lastrowid

    conn.commit()

    row = conn.execute("""
        SELECT *
        FROM notes
        WHERE id = ?
        AND user_id = ?
    """, (
        note_id,
        user_id
    )).fetchone()

    conn.close()

    return jsonify(
        serialize_note(row)
    ), 201


# ============================================================
# UPDATE NOTE
# ============================================================

@app.put("/api/notes/<int:note_id>")
def update_note(note_id):

    if not login_required():

        return jsonify({
            "error": "Authentication required."
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    user_id = get_current_user_id()

    allowed_fields = [
        "title",
        "content",
        "subject",
        "color",
        "important",
        "completed",
        "pinned",
        "due_date"
    ]

    updates = []
    values = []

    for field in allowed_fields:

        if field not in data:
            continue

        value = data[field]

        if field in [
            "important",
            "completed",
            "pinned"
        ]:

            value = int(
                bool(value)
            )

        updates.append(
            f"{field} = ?"
        )

        values.append(value)

    if not updates:

        return jsonify({
            "error": "Nothing to update."
        }), 400

    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    # Security:
    # note_id AND user_id must match.

    values.extend([
        note_id,
        user_id
    ])

    conn = get_db()

    cursor = conn.execute(
        f"""
        UPDATE notes

        SET {", ".join(updates)}

        WHERE id = ?
        AND user_id = ?
        """,
        values
    )

    if cursor.rowcount == 0:

        conn.close()

        return jsonify({
            "error": "Note not found."
        }), 404

    conn.commit()

    row = conn.execute("""
        SELECT *
        FROM notes
        WHERE id = ?
        AND user_id = ?
    """, (
        note_id,
        user_id
    )).fetchone()

    conn.close()

    return jsonify(
        serialize_note(row)
    )


# ============================================================
# DELETE NOTE
# ============================================================

@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):

    if not login_required():

        return jsonify({
            "error": "Authentication required."
        }), 401

    user_id = get_current_user_id()

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM notes
        WHERE id = ?
        AND user_id = ?
    """, (
        note_id,
        user_id
    ))

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:

        return jsonify({
            "error": "Note not found."
        }), 404

    return jsonify({
        "success": True
    })


# ============================================================
# STATS
# ============================================================

@app.get("/api/stats")
def get_stats():

    if not login_required():

        return jsonify({
            "error": "Authentication required."
        }), 401

    user_id = get_current_user_id()

    conn = get_db()

    # Total notes
    total = conn.execute("""
        SELECT COUNT(*)
        FROM notes
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]

    # Important
    important = conn.execute("""
        SELECT COUNT(*)
        FROM notes
        WHERE user_id = ?
        AND important = 1
    """, (
        user_id,
    )).fetchone()[0]

    # Completed
    completed = conn.execute("""
        SELECT COUNT(*)
        FROM notes
        WHERE user_id = ?
        AND completed = 1
    """, (
        user_id,
    )).fetchone()[0]

    # Subjects
    subjects = conn.execute("""
        SELECT COUNT(DISTINCT subject)
        FROM notes
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()[0]

    conn.close()

    return jsonify({
        "total": total,
        "important": important,
        "completed": completed,
        "subjects": subjects
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    init_db()

    print()
    print("======================================")
    print("          DEVELOPED BY DREI")
    print("======================================")
    print()
    print("Project directory:")
    print(BASE_DIR)
    print()
    print("Local Login:")
    print("http://127.0.0.1:5000/login/")
    print()
    print("Local Dashboard:")
    print("http://127.0.0.1:5000/")
    print()
    print("Database:")
    print(DB_PATH)
    print()
    print("======================================")
    print()
    print("Registered accounts:")
    print()

    print("1. Zyrille Cruz")
    print("   Username: 2026-STJAMES-5831")
    print("   Password: B1-2026-2354")
    print()

    print("2. Ceejay Garcia")
    print("   Username: 2026-STJAMES-5213")
    print("   Password: B2-2026-5432")
    print()

    print("3. Andrei Villarama")
    print("   Username: 2026-STJAMES-3475")
    print("   Password: B3-2026-3475")
    print()

    print("======================================")

    # Hosting platforms such as Render/Railway/etc.
    # commonly provide PORT automatically.

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )