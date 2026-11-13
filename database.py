"""SQLite storage layer. All SQL lives here; every query is parameterised."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "patients.db"))

COLUMNS = "id, full_name, dob, email, glucose, haemoglobin, cholesterol, remarks"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                glucose REAL NOT NULL,
                haemoglobin REAL NOT NULL,
                cholesterol REAL NOT NULL,
                remarks TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (full_name, dob)
            )"""
        )


def find_duplicate(full_name, dob, email, exclude_id=None):
    """Return a message if another record shares the email, or the same name + DOB."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, full_name, dob, email FROM patients WHERE email = ? "
            "OR (lower(full_name) = lower(?) AND dob = ?)",
            (email, full_name, dob),
        ).fetchall()
    for row in rows:
        if exclude_id is not None and row["id"] == exclude_id:
            continue
        if row["email"] == email:
            return "email", "A record with this email already exists."
        return "full_name", "A patient with this name and date of birth already exists."
    return None


def list_patients():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(f"SELECT {COLUMNS} FROM patients ORDER BY id")]


def get_patient(patient_id):
    with get_connection() as conn:
        row = conn.execute(f"SELECT {COLUMNS} FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return dict(row) if row else None


def create_patient(d):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d["full_name"], d["dob"], d["email"], d["glucose"], d["haemoglobin"], d["cholesterol"], d["remarks"]),
        )
        return cur.lastrowid


def update_patient(patient_id, d):
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, cholesterol=?, remarks=? "
            "WHERE id=?",
            (d["full_name"], d["dob"], d["email"], d["glucose"], d["haemoglobin"], d["cholesterol"], d["remarks"], patient_id),
        )
        return cur.rowcount > 0


def delete_patient(patient_id):
    with get_connection() as conn:
        return conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,)).rowcount > 0
