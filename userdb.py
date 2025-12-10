import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create users table and default admin if not exists."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()

    # Ensure one default admin exists
    cur.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    row = cur.fetchone()
    if row is None:
        admin_hash = generate_password_hash("admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash, role, approved) VALUES (?,?,?,?)",
            ("admin", admin_hash, "admin", 1),
        )
        conn.commit()

    conn.close()


def get_user_by_username(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash, role, approved FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "approved": row[4],
    }


def register_user(username: str, password: str):
    """Create new user with role 'user' and approved=0."""
    username = username.strip()
    if not username:
        return False, "Username cannot be empty."

    conn = get_conn()
    cur = conn.cursor()
    try:
        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role, approved) VALUES (?,?,?,?)",
            (username, pwd_hash, "user", 0),
        )
        conn.commit()
        return True, "Registration successful! Wait for admin approval."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()


def list_users():
    """Return list of all users as dicts."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, approved FROM users ORDER BY id ASC"
    )
    rows = cur.fetchall()
    conn.close()
    users = []
    for r in rows:
        users.append(
            {
                "id": r[0],
                "username": r[1],
                "role": r[2],
                "approved": r[3],
            }
        )
    return users


def approve_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user_role(user_id: int, role: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
