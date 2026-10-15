from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from database import get_conn, row_to_dict

def hash_password(password: str) -> str: return generate_password_hash(password)
def verify_password(password: str, password_hash: str) -> bool: return check_password_hash(password_hash, password)
def create_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user["id"], "role": user["role"], "email": user["email"], "exp": now + timedelta(hours=Config.TOKEN_HOURS), "iat": now}
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
def decode_token(token: str) -> dict: return jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
def public_user(user: dict) -> dict:
    return {"id":user["id"],"name":user["name"],"email":user["email"],"role":user["role"],"department":user.get("department"),"phone":user.get("phone")}
def get_user_by_id(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row_to_dict(row)
def require_auth(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "): return jsonify({"error":"Authentication required"}),401
            try: payload = decode_token(header.split(" ",1)[1])
            except jwt.ExpiredSignatureError: return jsonify({"error":"Session expired. Sign in again."}),401
            except jwt.InvalidTokenError: return jsonify({"error":"Invalid token"}),401
            user = get_user_by_id(payload["sub"])
            if not user: return jsonify({"error":"Account not found"}),401
            if roles and user["role"] not in roles: return jsonify({"error":"You do not have permission for this action"}),403
            g.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator
