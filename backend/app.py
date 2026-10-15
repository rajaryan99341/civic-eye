"""Flask API entry point for CIVIC EYE."""
import os, re, json, uuid
from pathlib import Path
from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from database import get_conn, init_db, row_to_dict, utcnow
from auth_util import create_token, hash_password, public_user, require_auth, verify_password
from ai_classifier import average_hash, classify_image
from duplicates import find_duplicate
from seed import seed_if_empty

def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    Path(Config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    init_db()
    if not testing: seed_if_empty()

    def serialize(row):
        data = dict(row)
        try: data["ai_scores"] = json.loads(data.get("ai_scores") or "{}")
        except (ValueError, TypeError): pass
        data["image_url"] = f"/api/uploads/{data['image_path']}" if data.get("image_path") else None
        data.pop("image_hash", None)
        return data

    @app.get("/api/health")
    def health(): return jsonify({"ok":True,"product":"CIVIC EYE","tagline":"SEE THE ISSUE. TRIGGER THE ACTION."})

    @app.post("/api/auth/register")
    def register():
        body=request.get_json(silent=True) or {}
        name=(body.get("name") or "").strip(); email=(body.get("email") or "").strip().lower(); password=body.get("password") or ""; phone=(body.get("phone") or "").strip() or None
        if not name or not email or len(password)<8 or not re.match(r"^[^@]+@[^@]+\.[^@]+$",email): return jsonify({"error":"Enter a name, valid email, and password of at least 8 characters"}),400
        conn=get_conn()
        if conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone(): conn.close(); return jsonify({"error":"An account with this email already exists"}),409
        cur=conn.execute("INSERT INTO users(name,email,password_hash,role,phone,created_at) VALUES(?,?,?,'citizen',?,?)",(name,email,hash_password(password),phone,utcnow()))
        user=row_to_dict(conn.execute("SELECT * FROM users WHERE id=?",(cur.lastrowid,)).fetchone()); conn.commit(); conn.close()
        return jsonify({"token":create_token(user),"user":public_user(user)}),201

    @app.post("/api/auth/login")
    def login():
        body=request.get_json(silent=True) or {}; email=(body.get("email") or "").strip().lower(); password=body.get("password") or ""; portal=body.get("portal") or "citizen"
        conn=get_conn(); user=row_to_dict(conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()); conn.close()
        if not user or not verify_password(password,user["password_hash"]): return jsonify({"error":"Invalid email or password"}),401
        if portal=="authority" and user["role"] not in {"officer","admin"}: return jsonify({"error":"This account cannot access the municipal portal"}),403
        if portal=="citizen" and user["role"]!="citizen": return jsonify({"error":"Municipal accounts must sign in through the authority portal"}),403
        return jsonify({"token":create_token(user),"user":public_user(user)})

    @app.get("/api/auth/me")
    @require_auth()
    def me(): return jsonify({"user":public_user(g.user)})

    @app.get("/api/complaints/mine")
    @require_auth("citizen")
    def mine():
        conn=get_conn(); rows=conn.execute("SELECT * FROM complaints WHERE citizen_id=? ORDER BY datetime(created_at) DESC",(g.user["id"],)).fetchall(); conn.close()
        return jsonify([serialize(r) for r in rows])

    @app.get("/api/complaints/track/<public_id>")
    def track(public_id):
        conn=get_conn(); row=conn.execute("SELECT * FROM complaints WHERE public_id=?",(public_id,)).fetchone()
        if not row: conn.close(); return jsonify({"error":"Complaint not found"}),404
        history=conn.execute("SELECT * FROM status_history WHERE complaint_id=? ORDER BY datetime(created_at)",(row["id"],)).fetchall(); conn.close()
        data=serialize(row); data["history"]=[dict(h) for h in history]; return jsonify(data)

    @app.post("/api/complaints")
    @require_auth("citizen")
    def create_complaint():
        form=request.form; title=(form.get("title") or "").strip(); description=(form.get("description") or "").strip(); address=(form.get("address") or "").strip()
        try: lat=float(form.get("latitude")); lng=float(form.get("longitude"))
        except (TypeError,ValueError): return jsonify({"error":"A valid location is required"}),400
        image=request.files.get("image")
        if not title or not description or not address or not image or not image.filename: return jsonify({"error":"Title, description, address, and photograph are required"}),400
        ext=image.filename.rsplit(".",1)[-1].lower() if "." in image.filename else ""
        if ext not in Config.ALLOWED_EXTENSIONS: return jsonify({"error":"Upload a JPG, PNG, or WEBP photograph"}),400
        stored=secure_filename(uuid.uuid4().hex+"."+ext); dest=Path(Config.UPLOAD_FOLDER)/stored; image.save(dest)
        result=classify_image(dest); image_hash=average_hash(dest); category=(form.get("category") or result["category"]).lower()
        if category not in {"pothole","garbage","streetlight","waterlogging"}: category=result["category"]
        conn=get_conn(); duplicate=find_duplicate(conn,category=category,latitude=lat,longitude=lng,image_hash=image_hash)
        year=utcnow()[:4]; row=conn.execute("SELECT COUNT(*) AS c FROM complaints WHERE public_id LIKE ?",(f"CEYE-{year}-%",)).fetchone(); public_id=f"CEYE-{year}-{row['c']+1:06d}"; now=utcnow()
        priority="high" if category in {"pothole","waterlogging"} else "medium"
        cur=conn.execute("""INSERT INTO complaints(public_id,citizen_id,title,description,category,ai_category,ai_confidence,ai_scores,status,priority,latitude,longitude,address,image_path,image_hash,duplicate_of,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?, 'submitted',?,?,?,?,?,?,?, ?,?)""",(public_id,g.user["id"],title,description,category,result["category"],result["confidence"],json.dumps(result["scores"]),priority,lat,lng,address,stored,image_hash,duplicate["id"] if duplicate else None,now,now))
        conn.execute("INSERT INTO status_history(complaint_id,actor_id,old_status,new_status,note,created_at) VALUES(?,?,NULL,'submitted','Citizen submitted a new issue through CIVIC EYE.',?)",(cur.lastrowid,g.user["id"],now))
        conn.commit(); item=conn.execute("SELECT * FROM complaints WHERE id=?",(cur.lastrowid,)).fetchone(); conn.close()
        data=serialize(item); data["classification"]=result; data["duplicate"]=duplicate; return jsonify(data),201

    @app.get("/api/officer/stats")
    @require_auth("officer","admin")
    def stats():
        conn=get_conn(); total=conn.execute("SELECT COUNT(*) c FROM complaints WHERE status NOT IN ('resolved','rejected')").fetchone()["c"]; resolved=conn.execute("SELECT COUNT(*) c FROM complaints WHERE status='resolved'").fetchone()["c"]; duplicates=conn.execute("SELECT COUNT(*) c FROM complaints WHERE duplicate_of IS NOT NULL").fetchone()["c"]
        by_status={r["status"]:r["c"] for r in conn.execute("SELECT status,COUNT(*) c FROM complaints GROUP BY status")}; by_category={r["category"]:r["c"] for r in conn.execute("SELECT category,COUNT(*) c FROM complaints GROUP BY category")}; by_priority={r["priority"]:r["c"] for r in conn.execute("SELECT priority,COUNT(*) c FROM complaints GROUP BY priority")}; conn.close()
        return jsonify({"open":total,"resolved":resolved,"duplicates":duplicates,"by_status":by_status,"by_category":by_category,"by_priority":by_priority})

    @app.get("/api/officer/complaints")
    @require_auth("officer","admin")
    def officer_complaints():
        conn=get_conn(); rows=conn.execute("SELECT * FROM complaints ORDER BY datetime(created_at) DESC").fetchall(); conn.close(); return jsonify([serialize(r) for r in rows])

    @app.get("/api/officer/map")
    @require_auth("officer","admin")
    def officer_map():
        conn=get_conn(); rows=conn.execute("SELECT id,public_id,title,category,status,priority,latitude,longitude,address FROM complaints").fetchall(); conn.close(); return jsonify([dict(r) for r in rows])

    @app.get("/api/complaints/<int:complaint_id>")
    @require_auth()
    def complaint_detail(complaint_id):
        conn=get_conn(); row=conn.execute("SELECT * FROM complaints WHERE id=?",(complaint_id,)).fetchone()
        if not row: conn.close(); return jsonify({"error":"Complaint not found"}),404
        if g.user["role"]=="citizen" and row["citizen_id"]!=g.user["id"]: conn.close(); return jsonify({"error":"Not found"}),404
        history=conn.execute("SELECT * FROM status_history WHERE complaint_id=? ORDER BY datetime(created_at)",(complaint_id,)).fetchall(); conn.close(); data=serialize(row); data["history"]=[dict(h) for h in history]; return jsonify(data)

    @app.post("/api/officer/complaints/<int:complaint_id>/status")
    @require_auth("officer","admin")
    def update_status(complaint_id):
        body=request.get_json(silent=True) or {}; status=body.get("status"); priority=body.get("priority"); category=body.get("category"); note=(body.get("note") or "").strip()
        if status and status not in {"submitted","under_review","assigned","in_progress","resolved","rejected"}: return jsonify({"error":"Invalid status"}),400
        conn=get_conn(); row=conn.execute("SELECT * FROM complaints WHERE id=?",(complaint_id,)).fetchone()
        if not row: conn.close(); return jsonify({"error":"Complaint not found"}),404
        updates=[]; vals=[]
        for key,value,allowed in [("status",status,{"submitted","under_review","assigned","in_progress","resolved","rejected"}),("priority",priority,{"low","medium","high","critical"}),("category",category,{"pothole","garbage","streetlight","waterlogging"})]:
            if value:
                if value not in allowed: conn.close(); return jsonify({"error":f"Invalid {key}"}),400
                updates.append(key+"=?"); vals.append(value)
        if not updates: conn.close(); return jsonify({"error":"No updates provided"}),400
        updates.append("updated_at=?"); vals.extend([utcnow(),complaint_id]); conn.execute("UPDATE complaints SET "+",".join(updates)+" WHERE id=?",vals)
        if status and status!=row["status"]: conn.execute("INSERT INTO status_history(complaint_id,actor_id,old_status,new_status,note,created_at) VALUES(?,?,?,?,?,?)",(complaint_id,g.user["id"],row["status"],status,note or f"Status changed to {status}.",utcnow()))
        conn.commit(); updated=conn.execute("SELECT * FROM complaints WHERE id=?",(complaint_id,)).fetchone(); conn.close(); return jsonify(serialize(updated))

    @app.get("/api/officers")
    @require_auth("officer","admin")
    def officers():
        conn=get_conn(); rows=conn.execute("SELECT id,name,email,department,role,phone FROM users WHERE role IN ('officer','admin') ORDER BY name").fetchall(); conn.close(); return jsonify([dict(r) for r in rows])

    @app.post("/api/officers")
    @require_auth("admin")
    def create_officer():
        body=request.get_json(silent=True) or {}; name=(body.get("name") or "").strip(); email=(body.get("email") or "").strip().lower(); password=body.get("password") or "Officer@123"; dept=(body.get("department") or "").strip() or None; phone=(body.get("phone") or "").strip() or None
        if not name or not email: return jsonify({"error":"Name and email are required"}),400
        conn=get_conn()
        if conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone(): conn.close(); return jsonify({"error":"Email already in use"}),409
        cur=conn.execute("INSERT INTO users(name,email,password_hash,role,department,phone,created_at) VALUES(?,?,?,'officer',?,?,?)",(name,email,hash_password(password),dept,phone,utcnow())); conn.commit(); user=dict(conn.execute("SELECT id,name,email,department,role,phone FROM users WHERE id=?",(cur.lastrowid,)).fetchone()); conn.close(); return jsonify(user),201

    @app.get("/api/uploads/<path:filename>")
    def uploads(filename): return send_from_directory(Config.UPLOAD_FOLDER,filename)
    return app

if __name__=="__main__": create_app().run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=True)
