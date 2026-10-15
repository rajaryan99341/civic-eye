import sqlite3
from datetime import datetime, timezone
from config import Config

def utcnow(): return datetime.now(timezone.utc).isoformat()
def get_conn():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('citizen','officer','admin')),
      department TEXT, phone TEXT, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS complaints (
      id INTEGER PRIMARY KEY AUTOINCREMENT, public_id TEXT NOT NULL UNIQUE, citizen_id INTEGER NOT NULL,
      title TEXT NOT NULL, description TEXT NOT NULL, category TEXT NOT NULL, ai_category TEXT,
      ai_confidence REAL, ai_scores TEXT, status TEXT NOT NULL DEFAULT 'submitted',
      priority TEXT NOT NULL DEFAULT 'medium', latitude REAL NOT NULL, longitude REAL NOT NULL,
      address TEXT NOT NULL, image_path TEXT, image_hash TEXT, assigned_officer_id INTEGER,
      duplicate_of INTEGER, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      FOREIGN KEY (citizen_id) REFERENCES users(id), FOREIGN KEY (assigned_officer_id) REFERENCES users(id),
      FOREIGN KEY (duplicate_of) REFERENCES complaints(id)
    );
    CREATE TABLE IF NOT EXISTS status_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id INTEGER NOT NULL, actor_id INTEGER,
      old_status TEXT, new_status TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL,
      FOREIGN KEY (complaint_id) REFERENCES complaints(id), FOREIGN KEY (actor_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_complaints_citizen ON complaints(citizen_id);
    CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
    CREATE INDEX IF NOT EXISTS idx_complaints_category ON complaints(category);
    """)
    conn.commit()
    conn.close()
def row_to_dict(row):
    return None if row is None else dict(row)
