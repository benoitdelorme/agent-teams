"""SQLite access layer: one connection per request, schema and seed data at startup.

The database file is `data.db` next to this package, or the path in `SAMPLE_DB`.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("SAMPLE_DB") or Path(__file__).resolve().parent.parent / "data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo','doing','done')),
  priority INTEGER NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SEED_PROJECTS = [
    ("Website redesign", "New marketing site with a refreshed brand.", [
        ("Audit the current pages", "done", 2),
        ("Wireframe the home page", "done", 1),
        ("Write the hero copy", "doing", 1),
        ("Build the pricing page", "todo", 2),
        ("Set up analytics", "todo", 3),
    ]),
    ("Mobile app", "iOS and Android client for existing customers.", [
        ("Login screen", "doing", 1),
        ("Offline mode for the task list", "todo", 2),
        ("Push notifications", "todo", 3),
    ]),
    ("Internal tools", "Small utilities for the support team.", [
        ("Export tickets to CSV", "done", 2),
        ("Bulk-close resolved tickets", "todo", 2),
    ]),
]

DEMO_USER = ("admin@example.com", "admin", "Alex")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create the schema and, on an empty database, the demo data."""
    with connect() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            seed_projects(conn)
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed_user(conn)


def seed_user(conn: sqlite3.Connection) -> None:
    from .auth import hash_password

    email, password, name = DEMO_USER
    conn.execute("INSERT INTO users(email, password_hash, name) VALUES (?,?,?)", (email, hash_password(password), name))


def seed_projects(conn: sqlite3.Connection) -> None:
    for name, description, tasks in SEED_PROJECTS:
        project_id = conn.execute("INSERT INTO projects(name, description) VALUES (?,?)", (name, description)).lastrowid
        conn.executemany(
            "INSERT INTO tasks(project_id, title, status, priority) VALUES (?,?,?,?)",
            [(project_id, title, status, priority) for title, status, priority in tasks],
        )


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
