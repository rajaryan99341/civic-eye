"""Seed demo accounts and sample records for local development."""
from config import Config
from database import get_conn, init_db, utcnow
from auth_util import hash_password

def seed_if_empty():
    init_db()
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if count:
        conn.close()
        return
    now = utcnow()
    users = [
        ("Asha Citizen","citizen@civiceye.local","Citizen@123","citizen",None,"9000000001"),
        ("Ravi Resident","ravi@civiceye.local","Citizen@123","citizen",None,"9000000002"),
        ("Meera Officer","officer@civiceye.local","Officer@123","officer","Roads & Lighting","9000000010"),
        ("Kabir Officer","kabir@civiceye.local","Officer@123","officer","Sanitation","9000000011"),
        ("CIVIC EYE Admin","admin@civiceye.local","Admin@123","admin","Command Centre","9000000099"),
    ]
    ids = {}
    for name,email,password,role,dept,phone in users:
        cur = conn.execute("INSERT INTO users (name,email,password_hash,role,department,phone,created_at) VALUES (?,?,?,?,?,?,?)",(name,email,hash_password(password),role,dept,phone,now))
        ids[email] = cur.lastrowid
    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_if_empty()
    print("CIVIC EYE demo accounts ready.")
