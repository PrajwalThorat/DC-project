# app.py - DC Projects (complete single-file server)
import os
import csv
import shutil
import subprocess
import platform
import re
from datetime import datetime
from io import StringIO
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify, session, redirect,
    url_for, send_file, abort, make_response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates")
)

# Configuration from environment
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG_MODE = os.environ.get("DEBUG", "True").lower() == "true"
DEV_PORT = int(os.environ.get("DEV_PORT", 5000))
PROD_PORT = int(os.environ.get("PROD_PORT", 8000))

app.config["SECRET_KEY"] = os.environ.get("DC_SECRET_KEY", "dc_projects_secret_change")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'dc_projects.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# MODELS
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    pwd_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), default="artist")  # admin, producer, supervisor, artist, it, lead
    display_name = db.Column(db.String(200), nullable=True)

    def check_password(self, raw):
        return check_password_hash(self.pwd_hash, raw)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "role": self.role, "display_name": self.display_name}


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    short = db.Column(db.String(60), nullable=True)
    start_date = db.Column(db.String(20), nullable=True)
    details_text = db.Column(db.Text, nullable=True)
    folder_path = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "short": self.short, "start_date": self.start_date, "details_text": self.details_text, "folder_path": self.folder_path}


class Shot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)

    code = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    assigned_to = db.Column(db.String(500), nullable=True)
    start_date = db.Column(db.String(20), nullable=True)
    due_date = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(80), default="Not Started")

    plate_path = db.Column(db.String(800), nullable=True)
    mov_path = db.Column(db.String(800), nullable=True)
    exr_path = db.Column(db.String(800), nullable=True)
    version = db.Column(db.String(40), nullable=True)
    nuke_path = db.Column(db.String(800), nullable=True)

    def extract_version(self):
        """Extract version from shot code like V001, v01, etc."""
        if not self.code:
            return self.version or ""
        import re
        # Match pattern like V001, v01, V1, etc.
        match = re.search(r'[Vv](\d+)', self.code)
        if match:
            return f"V{match.group(1)}"
        return self.version or ""

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "code": self.code,
            "description": self.description or "",
            "assigned_to": self.assigned_to or "",
            "start_date": self.start_date or "",
            "due_date": self.due_date or "",
            "status": self.status or "",
            "plate_path": self.plate_path or "",
            "mov_path": self.mov_path or "",
            "exr_path": self.exr_path or "",
            "version": self.extract_version() or "",
            "nuke_path": self.nuke_path or "",
        }


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shot_id = db.Column(db.Integer, db.ForeignKey("shot.id"), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    author_role = db.Column(db.String(80), nullable=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String(40), nullable=False)

    def to_dict(self):
        return {"id": self.id, "shot_id": self.shot_id, "author": self.author, "author_role": self.author_role, "text": self.text, "created_at": self.created_at}


# -------------------------
# SAFE DB INIT (call at startup)
# -------------------------
def ensure_db():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", pwd_hash=generate_password_hash("admin"), role="admin", display_name="Administrator")
        db.session.add(u)
        db.session.commit()


# -------------------------
# UI routes
# -------------------------
@app.route("/")
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    # Ensure database is initialized
    try:
        with app.app_context():
            ensure_db()
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")
    
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if not username or not password:
        return "username & password required", 400
    try:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return "Invalid credentials", 401
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Login error: {e}")
        return f"Login failed: {str(e)}", 500


# API-compatible login for AJAX
@app.route("/api/login", methods=["POST"])
def api_login():
    if request.is_json:
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
    else:
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role
    return jsonify({"ok": True, "username": user.username, "role": user.role})


@app.route("/logout", methods=["POST"])
def logout_route():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)
    return jsonify({"ok": True})


# -------------------------
# API: session/users/projects/shots/comments
# -------------------------
@app.route("/api/session")
def api_session():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"logged_in": False})
    user = User.query.get(uid)
    if not user:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": user.username, "role": user.role, "display_name": user.display_name})


@app.route("/api/users", methods=["GET", "POST"])
def api_users():
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if request.method == "GET":
        users = User.query.order_by(User.username).all()
        return jsonify([u.to_dict() for u in users])
    if not current or current.role != "admin":
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password", "changeme")
    role = data.get("role", "artist")
    display_name = data.get("display_name", "")
    if not username:
        return jsonify({"error": "username required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username exists"}), 400
    u = User(username=username, pwd_hash=generate_password_hash(password), role=role, display_name=display_name)
    db.session.add(u)
    db.session.commit()
    return jsonify(u.to_dict()), 201


@app.route("/api/users/<int:user_id>", methods=["PUT", "DELETE"])
def api_user_edit(user_id):
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current or current.role != "admin":
        return jsonify({"error": "forbidden"}), 403
    u = User.query.get_or_404(user_id)
    if request.method == "DELETE":
        db.session.delete(u)
        db.session.commit()
        return jsonify({"ok": True})
    data = request.get_json() or {}
    if "password" in data:
        u.pwd_hash = generate_password_hash(data["password"])
    if "role" in data:
        u.role = data["role"]
    if "display_name" in data:
        u.display_name = data["display_name"]
    db.session.commit()
    return jsonify(u.to_dict())


@app.route("/api/projects", methods=["GET", "POST"])
def api_projects():
    if request.method == "GET":
        projects = Project.query.order_by(Project.name).all()
        return jsonify([p.to_dict() for p in projects])
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current or current.role not in ("admin", "producer"):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    name = data.get("name")
    start_date = data.get("start_date", "")
    short = data.get("short") or (name[:6].upper() if name else "")
    folder_path = data.get("folder_path", "")
    details_text = data.get("details_text", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    p = Project(name=name, short=short, start_date=start_date, folder_path=folder_path, details_text=details_text)
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@app.route("/api/projects/<int:project_id>", methods=["GET", "PUT", "DELETE"])
def api_project_edit(project_id):
    p = Project.query.get_or_404(project_id)
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if request.method == "GET":
        return jsonify(p.to_dict())
    if not current or current.role not in ("admin", "producer"):
        return jsonify({"error": "forbidden"}), 403
    if request.method == "DELETE":
        db.session.delete(p)
        db.session.commit()
        return jsonify({"ok": True})
    data = request.get_json() or {}
    if "name" in data:
        p.name = data["name"]
    if "short" in data:
        p.short = data["short"]
    if "start_date" in data:
        p.start_date = data["start_date"]
    if "details_text" in data:
        p.details_text = data["details_text"]
    if "folder_path" in data:
        p.folder_path = data["folder_path"]
    db.session.commit()
    return jsonify(p.to_dict())


@app.route("/api/projects/<int:project_id>/shots", methods=["GET", "POST"])
def project_shots(project_id):
    proj = Project.query.get_or_404(project_id)
    if request.method == "POST":
        uid = session.get("user_id")
        current = User.query.get(uid) if uid else None
        if not current or current.role not in ("admin", "producer", "supervisor"):
            return jsonify({"error": "forbidden"}), 403
        if request.content_type and request.content_type.startswith("multipart"):
            code = request.form.get("code")
            description = request.form.get("description")
            assigned_to = request.form.get("assigned_to")
            start_date = request.form.get("start_date")
            due_date = request.form.get("due_date")
            status = request.form.get("status") or "Not Started"
            plate_path = request.form.get("plate_path") or ""
            mov_path = request.form.get("mov_path") or ""
            exr_path = request.form.get("exr_path") or ""
            version = request.form.get("version") or ""
        else:
            data = request.get_json() or {}
            code = data.get("code")
            description = data.get("description")
            assigned_to = data.get("assigned_to")
            start_date = data.get("start_date")
            due_date = data.get("due_date")
            status = data.get("status") or "Not Started"
            plate_path = data.get("plate_path") or ""
            mov_path = data.get("mov_path") or ""
            exr_path = data.get("exr_path") or ""
            version = data.get("version") or ""
        if not code:
            return jsonify({"error": "code required"}), 400
        
        # Auto-extract version from code if not provided
        if not version:
            import re
            match = re.search(r'[Vv](\d+)', code)
            if match:
                version = f"V{match.group(1)}"
        
        s = Shot(project_id=project_id, code=code, description=description, assigned_to=assigned_to, start_date=start_date, due_date=due_date, status=status, plate_path=plate_path, mov_path=mov_path, exr_path=exr_path, version=version)
        db.session.add(s)
        db.session.commit()
        return jsonify({"ok": True, "id": s.id}), 201

    q = Shot.query.filter_by(project_id=project_id)
    reel = request.args.get("reel")
    if reel:
        q = q.filter(Shot.code.contains(reel))
    code = request.args.get("code")
    if code:
        q = q.filter(Shot.code.contains(code))
    description = request.args.get("description")
    if description:
        q = q.filter(Shot.description.contains(description))
    artist = request.args.get("artist")
    if artist:
        q = q.filter(Shot.assigned_to.contains(artist))
    due = request.args.get("due")
    if due:
        q = q.filter(Shot.due_date == due)
    status = request.args.get("status")
    if status:
        q = q.filter(Shot.status == status)
    shots = q.order_by(Shot.id).all()
    return jsonify([shot.to_dict() for shot in shots])


@app.route("/api/shots/<int:shot_id>", methods=["GET", "PUT", "DELETE"])
def api_shot(shot_id):
    s = Shot.query.get_or_404(shot_id)
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if request.method == "GET":
        return jsonify(s.to_dict())
    if request.method == "DELETE":
        if not current or current.role not in ("admin", "producer", "supervisor"):
            return jsonify({"error": "forbidden"}), 403
        db.session.delete(s)
        db.session.commit()
        return jsonify({"ok": True})
    if not current or current.role not in ("admin", "producer", "supervisor"):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    allowed = ["assigned_to", "status", "description", "due_date", "plate_path", "mov_path", "exr_path", "nuke_path", "code"]
    # allow updating version as well
    allowed.append("version")
    changed = False
    for k in allowed:
        if k in data:
            setattr(s, k, data[k])
            changed = True
    if changed:
        db.session.commit()
    return jsonify(s.to_dict())


@app.route("/api/shots/<int:shot_id>/comments", methods=["GET", "POST"])
def api_shot_comments(shot_id):
    shot = Shot.query.get_or_404(shot_id)
    if request.method == "GET":
        comments = Comment.query.filter_by(shot_id=shot_id).order_by(Comment.id).all()
        return jsonify([c.to_dict() for c in comments])
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current:
        return jsonify({"error": "login required"}), 403
    data = request.get_json() or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": "text required"}), 400
    c = Comment(shot_id=shot_id, author=current.username, author_role=current.role, text=text, created_at=datetime.utcnow().isoformat())
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@app.route("/api/comments/<int:comment_id>", methods=["PUT", "DELETE"])
def api_comment_edit(comment_id):
    c = Comment.query.get_or_404(comment_id)
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current:
        return jsonify({"error": "login required"}), 403
    if current.role != "admin" and current.username != c.author:
        return jsonify({"error": "forbidden"}), 403
    if request.method == "DELETE":
        db.session.delete(c)
        db.session.commit()
        return jsonify({"ok": True})
    data = request.get_json() or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": "text required"}), 400
    c.text = text
    db.session.commit()
    return jsonify(c.to_dict())


@app.route("/api/shot_thumb/<int:shot_id>")
def api_shot_thumb(shot_id):
    s = Shot.query.get_or_404(shot_id)
    for p in (s.plate_path, s.mov_path, s.exr_path):
        if not p:
            continue
        candidate = os.path.normpath(p)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            try:
                return send_file(candidate, conditional=True)
            except Exception:
                continue
    return abort(404)

@app.route("/api/shot_media/<int:shot_id>")
def api_shot_media(shot_id):
    """Stream video/media files from disk"""
    media_type = request.args.get("type", "plate")  # plate, mov, exr
    s = Shot.query.get_or_404(shot_id)
    
    # Get the appropriate path based on media_type
    path = None
    if media_type == "plate":
        path = s.plate_path
    elif media_type == "mov":
        path = s.mov_path
    elif media_type == "exr":
        path = s.exr_path
    
    if not path:
        app.logger.warning(f"No {media_type} path for shot {shot_id}")
        return abort(404)
    
    # Normalize the path (handles both Windows UNC paths and regular paths)
    candidate = os.path.normpath(path)
    
    # Check if file exists
    if not os.path.exists(candidate):
        app.logger.warning(f"File not found: {candidate}")
        return abort(404)
    
    if not os.path.isfile(candidate):
        app.logger.warning(f"Not a file: {candidate}")
        return abort(404)
    
    try:
        # Determine MIME type based on file extension
        file_ext = os.path.splitext(candidate)[1].lower()
        mime_type = 'video/mp4'
        
        if file_ext in ['.mov', '.qt']:
            mime_type = 'video/quicktime'
        elif file_ext == '.mkv':
            mime_type = 'video/x-matroska'
        elif file_ext == '.avi':
            mime_type = 'video/x-msvideo'
        elif file_ext == '.webm':
            mime_type = 'video/webm'
        elif file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        
        app.logger.info(f"Streaming: {candidate} as {mime_type}")
        
        # Send file with conditional headers for range requests (video scrubbing)
        return send_file(candidate, conditional=True, mimetype=mime_type)
    except Exception as e:
        app.logger.exception(f"shot_media failed for {candidate}: {str(e)}")
        return jsonify({"error": "Failed to stream file", "detail": str(e)}), 500

@app.route("/api/stream_file")
def api_stream_file():
    """Stream any file by full path (for local playback)"""
    file_path = request.args.get("path", "")
    
    if not file_path:
        return jsonify({"error": "path parameter required"}), 400
    
    # Normalize and secure the path
    candidate = os.path.normpath(file_path)
    
    # Verify file exists
    if not os.path.exists(candidate):
        app.logger.warning(f"File not found: {candidate}")
        return abort(404)
    
    if not os.path.isfile(candidate):
        app.logger.warning(f"Not a file: {candidate}")
        return abort(404)
    
    try:
        # Determine MIME type based on file extension
        file_ext = os.path.splitext(candidate)[1].lower()
        mime_type = 'application/octet-stream'
        
        # Video types
        if file_ext in ['.mp4', '.m4v']:
            mime_type = 'video/mp4'
        elif file_ext in ['.mov', '.qt']:
            mime_type = 'video/quicktime'
        elif file_ext == '.mkv':
            mime_type = 'video/x-matroska'
        elif file_ext == '.avi':
            mime_type = 'video/x-msvideo'
        elif file_ext == '.webm':
            mime_type = 'video/webm'
        elif file_ext == '.flv':
            mime_type = 'video/x-flv'
        # Image types
        elif file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.gif':
            mime_type = 'image/gif'
        elif file_ext == '.webp':
            mime_type = 'image/webp'
        
        app.logger.info(f"Streaming file: {candidate} ({mime_type})")
        
        # Send file with range request support for seeking
        return send_file(candidate, conditional=True, mimetype=mime_type)
    except Exception as e:
        app.logger.exception(f"stream_file failed: {str(e)}")
        return jsonify({"error": "Failed to stream file", "detail": str(e)}), 500

@app.route("/api/shots/<int:shot_id>/nuke_path")
def api_shot_nuke_path(shot_id):
    s = Shot.query.get_or_404(shot_id)
    if s.nuke_path:
        return jsonify({"path": s.nuke_path})
    proj = Project.query.get(s.project_id)
    if proj and proj.folder_path:
        parts = (s.code or "").split("_")
        reel = parts[1] if len(parts) >= 2 else "REEL"
        shot_folder = s.code or f"shot_{s.id}"
        comp_dir = os.path.join(proj.folder_path, "Comp", reel, shot_folder)
        os.makedirs(comp_dir, exist_ok=True)
        nkname = f"{s.code}_comp_v001.nk"
        nkpath = os.path.join(comp_dir, nkname)
        return jsonify({"path": nkpath})
    return jsonify({"path": ""}), 404


@app.route("/api/shots/<int:shot_id>/generate_comp", methods=["POST"])
def api_generate_comp(shot_id):
    s = Shot.query.get_or_404(shot_id)
    proj = Project.query.get(s.project_id)
    if not proj or not proj.folder_path:
        return jsonify({"error": "project folder_path not configured"}), 400
    parts = (s.code or "").split("_")
    reel = parts[1] if len(parts) >= 2 else "REEL"
    shot_folder = s.code or f"shot_{s.id}"
    comp_dir = os.path.join(proj.folder_path, "Comp", reel, shot_folder)
    os.makedirs(comp_dir, exist_ok=True)
    base_name = f"{s.code}_comp_v"
    existing = [f for f in os.listdir(comp_dir) if f.startswith(base_name) and f.endswith(".nk")]
    v = 1
    if existing:
        nums = []
        for fn in existing:
            try:
                numpart = fn.split("_v")[-1].split(".nk")[0]
                nums.append(int(numpart))
            except:
                pass
        if nums:
            v = max(nums) + 1
    fname = f"{s.code}_comp_v{v:03d}.nk"
    path = os.path.join(comp_dir, fname)
    content = f"# Nuke placeholder\n# shot: {s.code}\n# created: {datetime.utcnow().isoformat()}Z\n"
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        s.nuke_path = path
        db.session.commit()
        return jsonify({"created": True, "path": path})
    except Exception as e:
        app.logger.exception("generate_comp failed")
        return jsonify({"error": "could not create nuke file", "detail": str(e)}), 500


@app.route("/api/shots/<int:shot_id>/send_to_client", methods=["POST"])
def api_send_to_client(shot_id):
    s = Shot.query.get_or_404(shot_id)
    proj = Project.query.get(s.project_id)
    if not proj or not proj.folder_path:
        return jsonify({"error": "project folder_path not configured"}), 400
    today = datetime.utcnow().strftime("%Y%m%d")
    label_suffix = "A"
    target_base = os.path.join(proj.folder_path, "Client", f"{today}{label_suffix}")
    mov_target = os.path.join(target_base, "MOV")
    exr_target = os.path.join(target_base, "EXR")
    os.makedirs(mov_target, exist_ok=True)
    os.makedirs(exr_target, exist_ok=True)
    result = {"mov_copied": None, "exr_copied": None, "target_folder": target_base}
    try:
        if s.mov_path and os.path.exists(s.mov_path) and os.path.isfile(s.mov_path):
            fname = os.path.basename(s.mov_path)
            tpath = os.path.join(mov_target, fname)
            shutil.copy2(s.mov_path, tpath)
            result["mov_copied"] = tpath
        if s.exr_path:
            if os.path.isdir(s.exr_path):
                for f in os.listdir(s.exr_path):
                    if f.lower().endswith(".exr"):
                        shutil.copy2(os.path.join(s.exr_path, f), os.path.join(exr_target, f))
                result["exr_copied"] = exr_target
            elif os.path.isfile(s.exr_path):
                fname = os.path.basename(s.exr_path)
                tpath = os.path.join(exr_target, fname)
                shutil.copy2(s.exr_path, tpath)
                result["exr_copied"] = tpath
        return jsonify(result)
    except Exception as e:
        app.logger.exception("send_to_client failed")
        return jsonify({"error": "copy failed", "detail": str(e)}), 500


@app.route("/api/projects/<int:project_id>/export_csv")
def api_export_csv(project_id):
    proj = Project.query.get_or_404(project_id)
    q = Shot.query.filter_by(project_id=project_id)
    reel = request.args.get("reel")
    if reel:
        q = q.filter(Shot.code.contains(reel))
    code = request.args.get("code")
    if code:
        q = q.filter(Shot.code.contains(code))
    description = request.args.get("description")
    if description:
        q = q.filter(Shot.description.contains(description))
    artist = request.args.get("artist")
    if artist:
        q = q.filter(Shot.assigned_to == artist)
    due = request.args.get("due")
    if due:
        q = q.filter(Shot.due_date == due)
    status = request.args.get("status")
    if status:
        q = q.filter(Shot.status == status)
    shots = q.order_by(Shot.id).all()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["id", "code", "reel", "version", "description", "assigned_to", "due_date", "status", "plate_path", "mov_path", "exr_path"])
    for s in shots:
        reel = (s.code or "").split("_")[1] if "_" in (s.code or "") else ""
        # Use extracted version to ensure consistency with UI/display logic
        cw.writerow([s.id, s.code, reel, s.extract_version() or "", s.description, s.assigned_to, s.due_date, s.status, s.plate_path, s.mov_path, s.exr_path])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={proj.name}_shots_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/api/projects/<int:project_id>/import_csv", methods=["POST"])
def api_import_csv(project_id):
    """Import shots from uploaded CSV file. Accepts multipart/form-data with field 'file'.

    CSV may include a header row. If headers exist, column names will be mapped
    to known fields (code, description, assigned_to, start_date, due_date,
    status, plate_path, mov_path, exr_path, version). If no headers, positional
    columns are used (same order as previous client import).
    """
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current or current.role not in ("admin", "producer", "supervisor"):
        return jsonify({"error": "forbidden"}), 403

    if "file" not in request.files:
        return jsonify({"error": "file field required"}), 400

    f = request.files["file"]
    try:
        raw = f.read()
        # Support files with BOM
        try:
            text = raw.decode("utf-8-sig")
        except Exception:
            text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": "could not read file", "detail": str(e)}), 400

    si = StringIO(text)
    errors = []
    imported = 0

    # Helper aliases
    aliases = {
        "code": ["code", "shot_code", "shot", "shotcode"],
        "description": ["description", "desc", "notes"],
        "assigned_to": ["assigned_to", "assigned", "artist", "assignee"],
        "start_date": ["start_date", "start"],
        "due_date": ["due_date", "due"],
        "status": ["status", "state"],
        "plate_path": ["plate_path", "plate"],
        "mov_path": ["mov_path", "mov", "movie"],
        "exr_path": ["exr_path", "exr"],
        "version": ["version", "ver", "v"]
    }

    # Try DictReader first (handles headers and quoted commas)
    si.seek(0)
    reader = csv.DictReader(si)
    has_headers = reader.fieldnames is not None and any(h.strip() for h in reader.fieldnames)

    si.seek(0)
    to_insert = []
    if has_headers:
        dr = csv.DictReader(StringIO(text))
        line_no = 1
        for row in dr:
            line_no += 1
            # normalize keys
            row_lc = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k is not None}

            def get_alias(field):
                for a in aliases.get(field, []):
                    if a in row_lc and row_lc[a] != "":
                        return row_lc[a]
                return ""

            code = get_alias("code")
            description = get_alias("description")
            assigned_to = get_alias("assigned_to")
            start_date = get_alias("start_date")
            due_date = get_alias("due_date")
            status = get_alias("status") or "Not Started"
            plate_path = get_alias("plate_path")
            mov_path = get_alias("mov_path")
            exr_path = get_alias("exr_path")
            version = get_alias("version")

            if not code:
                errors.append({"line": line_no, "error": "missing code"})
                continue

            if not version:
                m = re.search(r"[Vv](\d+)", code)
                if m:
                    version = f"V{m.group(1)}"

            # build mapping for bulk insert
            mapping = {
                "project_id": project_id,
                "code": code,
                "description": description,
                "assigned_to": assigned_to,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
                "plate_path": plate_path,
                "mov_path": mov_path,
                "exr_path": exr_path,
                "version": version,
            }
            to_insert.append(mapping)
    else:
        # No headers - fallback to positional mapping (legacy behavior)
        si2 = StringIO(text)
        rows_list = list(csv.reader(si2))

        # filter out empty rows
        filtered = [r for r in rows_list if any((c or '').strip() for c in r)]

        # detect numeric index column in first position (common when exported from Excel)
        sample = filtered[:6]
        first_col_vals = [r[0].strip() for r in sample if len(r) > 0]
        numeric_first = sum(1 for v in first_col_vals if re.match(r"^\d+$", v))
        skip_index = False
        if first_col_vals and numeric_first >= max(1, len(first_col_vals) - 1):
            skip_index = True

        line_no = 0
        for vals in filtered:
            line_no += 1
            # If first column is an index, shift columns by one
            idx = 1 if skip_index else 0
            code = vals[idx].strip() if len(vals) > idx else ""
            description = vals[idx+1].strip() if len(vals) > idx+1 else ""
            assigned_to = vals[idx+2].strip() if len(vals) > idx+2 else ""
            start_date = vals[idx+3].strip() if len(vals) > idx+3 else ""
            due_date = vals[idx+4].strip() if len(vals) > idx+4 else ""
            status = vals[idx+5].strip() if len(vals) > idx+5 and vals[idx+5].strip() else "Not Started"
            plate_path = vals[idx+6].strip() if len(vals) > idx+6 else ""
            mov_path = vals[idx+7].strip() if len(vals) > idx+7 else ""
            exr_path = vals[idx+8].strip() if len(vals) > idx+8 else ""
            version = vals[idx+9].strip() if len(vals) > idx+9 else ""

            if not code:
                errors.append({"line": line_no, "error": "missing code"})
                continue

            if not version:
                m = re.search(r"[Vv](\d+)", code)
                if m:
                    version = f"V{m.group(1)}"

            mapping = {
                "project_id": project_id,
                "code": code,
                "description": description,
                "assigned_to": assigned_to,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
                "plate_path": plate_path,
                "mov_path": mov_path,
                "exr_path": exr_path,
                "version": version,
            }
            to_insert.append(mapping)

    # Perform bulk insert for speed
    if to_insert:
        try:
            # Use bulk_insert_mappings to bypass per-object overhead
            db.session.bulk_insert_mappings(Shot, to_insert)
            db.session.commit()
            imported = len(to_insert)
        except Exception as e:
            db.session.rollback()
            errors.append({"error": "bulk insert failed", "detail": str(e)})

    return jsonify({"imported": imported, "errors": errors})


@app.route("/api/projects/<int:project_id>/import_preview", methods=["POST"])
def api_import_preview(project_id):
    """Preview an uploaded CSV and suggest column mapping.

    Returns detected headers (if any), first 3 data rows, and a suggested mapping
    from canonical field names to header names or positional indexes.
    """
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current:
        return jsonify({"error": "login required"}), 403

    if "file" not in request.files:
        return jsonify({"error": "file field required"}), 400

    f = request.files["file"]
    try:
        raw = f.read()
        try:
            text = raw.decode("utf-8-sig")
        except Exception:
            text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": "could not read file", "detail": str(e)}), 400

    si = StringIO(text)
    # Use csv module to safely parse first few rows
    try:
        rdr = csv.reader(si)
        rows = []
        for i, r in enumerate(rdr):
            if i >= 5:
                break
            rows.append([c.strip() for c in r])
    except Exception as e:
        return jsonify({"error": "csv parse failed", "detail": str(e)}), 400

    # Determine if first row looks like headers (non-numeric or contains letters)
    headers = None
    if rows:
        first = rows[0]
        # Heuristic: if any cell in first row contains a letter and not all are numeric, treat as header
        if any(re.search(r"[A-Za-z]", (c or "")) for c in first):
            headers = first
            data_rows = rows[1:4]
        else:
            headers = None
            data_rows = rows[0:3]
    else:
        data_rows = []

    # canonical fields and aliases (reuse from import_csv)
    aliases = {
        # avoid mapping generic 'id' header to code — index columns often contain numeric ids
        "code": ["code", "shot_code", "shot", "shotcode"],
        "description": ["description", "desc", "notes"],
        "assigned_to": ["assigned_to", "assigned", "artist", "assignee"],
        "start_date": ["start_date", "start"],
        "due_date": ["due_date", "due"],
        "status": ["status", "state"],
        "plate_path": ["plate_path", "plate"],
        "mov_path": ["mov_path", "mov", "movie"],
        "exr_path": ["exr_path", "exr"],
        "version": ["version", "ver", "v"]
    }

    suggested = {}
    if headers:
        lowered = [h.strip().lower() for h in headers]
        for field, al in aliases.items():
            found = None
            for a in al:
                if a in lowered:
                    # map to the original header string (preserve case)
                    idx = lowered.index(a)
                    found = headers[idx]
                    break
            suggested[field] = found
    else:
        # positional suggestion (index-based)
        # default positional mapping: code,description,assigned_to,start_date,due_date,status,plate_path,mov_path,exr_path,version
        posmap = ["code","description","assigned_to","start_date","due_date","status","plate_path","mov_path","exr_path","version"]
        # detect numeric index column in first position and advise shifting if present
        sample = data_rows[:6]
        first_col_vals = [r[0] for r in sample if len(r) > 0]
        numeric_first = sum(1 for v in first_col_vals if re.match(r"^\d+$", (v or "")))
        skip_index = False
        if first_col_vals and numeric_first >= max(1, len(first_col_vals) - 1):
            skip_index = True

        for i, p in enumerate(posmap):
            if skip_index:
                suggested[p] = {"pos": i + 1}
            else:
                suggested[p] = {"pos": i}

    # Quick check whether code column detected
    code_found = bool(suggested.get("code"))

    return jsonify({"has_headers": bool(headers), "headers": headers or [], "sample": data_rows, "suggested_mapping": suggested, "code_found": code_found})


@app.route("/api/projects/<int:project_id>/raw")
def api_project_raw(project_id):
    p = Project.query.get_or_404(project_id)
    shots = Shot.query.filter_by(project_id=project_id).all()
    return jsonify({"project": p.to_dict(), "shots": [s.to_dict() for s in shots]})


@app.route("/api/open_folder", methods=["POST"])
def api_open_folder():
    data = request.get_json() or {}
    path = data.get("path")
    
    if not path:
        return jsonify({"error": "path required"}), 400
    
    path = os.path.normpath(path)
    
    try:
        if platform.system() == "Windows":
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                subprocess.Popen(f'explorer "{path}"')
        elif platform.system() == "Darwin":
            if os.path.isfile(path):
                subprocess.Popen(["open", "-R", path])
            else:
                subprocess.Popen(["open", path])
        else:
            if os.path.isfile(path):
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
            else:
                subprocess.Popen(["xdg-open", path])
        return jsonify({"ok": True})
    except Exception as e:
        app.logger.exception("open_folder failed")
        return jsonify({"error": str(e)}), 500


@app.route("/_health")
def health():
    return jsonify({"ok": True})


# -------------------------
# STARTUP
# -------------------------
if __name__ == "__main__":
    # ensure base data folder exists
    try:
        os.makedirs(BASE_DIR / "data", exist_ok=True)
    except Exception:
        pass

    with app.app_context():
        ensure_db()

# -------------------------
# STARTUP
# -------------------------
if __name__ == "__main__":
    # ensure base data folder exists
    try:
        os.makedirs(BASE_DIR / "data", exist_ok=True)
    except Exception:
        pass

    with app.app_context():
        try:
            ensure_db()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Database initialization error: {e}")
            import traceback
            traceback.print_exc()

    # Determine port and host based on environment
    if ENVIRONMENT == "production":
        # Production mode - Gunicorn will handle this, but set defaults
        port = PROD_PORT
        host = "0.0.0.0"
        debug = False
    else:
        # Development mode
        port = DEV_PORT
        host = "127.0.0.1"
        debug = DEBUG_MODE

    app.run(host=host, port=port, debug=debug)
