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
from urllib.parse import quote_plus
from sqlalchemy import func
try:
    # Load .env file if present so environment variables in .env are available
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates")
)

# Base path on server where project folders should be created. Can be set via env var `DC_PROJECTS_ROOT` or `PROJECT_ROOT`.
_env_root = os.environ.get("DC_PROJECTS_ROOT") or os.environ.get("PROJECT_ROOT")
# Preferred network path (Windows UNC). We'll attempt a few variants and pick the first that exists.
_unc_win = r"\\169.254.8.57\Data"
_unc_posix = "//169.254.8.57/Data"
_local_default = str(BASE_DIR / "projects")

PROJECT_ROOT = None
for _candidate in filter(None, [_env_root, _unc_win, _unc_posix, _local_default]):
    try:
        if os.path.exists(_candidate):
            PROJECT_ROOT = _candidate
            break
    except Exception:
        continue

if not PROJECT_ROOT:
    # If nothing exists, prefer env value if provided, otherwise fall back to UNC (as requested) then local
    PROJECT_ROOT = _env_root or _unc_win or _local_default


# Configuration from environment
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG_MODE = os.environ.get("DEBUG", "True").lower() == "true"
DEV_PORT = int(os.environ.get("DEV_PORT", 5000))
PROD_PORT = int(os.environ.get("PROD_PORT", 8000))

app.config["SECRET_KEY"] = os.environ.get("DC_SECRET_KEY", "dc_projects_secret_change")

# Database Configuration - MySQL only
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "dc_projects")

# URL-encode credentials (passwords may contain '@' or other special chars)
db_user_esc = quote_plus(DB_USER)
db_pass_esc = quote_plus(DB_PASSWORD)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user_esc}:{db_pass_esc}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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
    __table_args__ = (db.UniqueConstraint('project_id', 'code', name='uk_shot_project_code'),)
    reel = db.Column(db.String(100), nullable=True)
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
            "reel": self.reel or "",
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
    """Ensure default admin user exists."""
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
    # If folder_path not supplied, build one using PROJECT_ROOT and project short/code
    try:
        if not folder_path:
            safe_short = (short or name or f"project_{p.id}").replace(' ', '_')
            project_dir = os.path.join(PROJECT_ROOT, safe_short)
            os.makedirs(project_dir, exist_ok=True)
            # create standard subfolders
            subfolders = [
                "Annotation",
                "Assets",
                "Comps",
                "From Client",
                "Plates",
                "Render",
                "Send to client template",
            ]
            for sf in subfolders:
                try:
                    os.makedirs(os.path.join(project_dir, sf), exist_ok=True)
                except Exception:
                    pass
            p.folder_path = project_dir
            db.session.commit()
        else:
            # ensure provided path exists
            try:
                os.makedirs(folder_path, exist_ok=True)
            except Exception:
                pass
    except Exception as e:
        app.logger.exception(f"Failed to create project folders: {e}")
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
        
        # Check for duplicate code in same project
        existing = Shot.query.filter_by(project_id=project_id, code=code).first()
        if existing:
            return jsonify({"error": f"Shot code '{code}' already exists in this project"}), 400
        
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

    # new: filter by reel param
    q = Shot.query.filter_by(project_id=project_id)

    reel = request.args.get('reel')
    if reel:
        q = q.filter(Shot.reel == reel)

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
    
    # support grouping
    group_by = request.args.get('group_by')
    if group_by == 'reel':
        groups_q = db.session.query(Shot.reel, func.count(Shot.id)).filter(Shot.project_id == project_id)
        if reel:
            groups_q = groups_q.filter(Shot.reel == reel)
        groups_q = groups_q.group_by(Shot.reel).order_by(Shot.reel)
        groups = groups_q.all()
        res = [{'reel': (r if r is not None else ''), 'count': c} for r, c in groups]
        return jsonify(res)

    # pagination / sorting / return list as before
    shots = q.order_by(Shot.id).all()
    return jsonify([s.to_dict() for s in shots])


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
    allowed = ["assigned_to", "status", "description", "due_date", "plate_path", "mov_path", "exr_path", "nuke_path", "code", "reel"]
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


@app.route("/api/shots/bulk_delete", methods=["POST"])
def api_shots_bulk_delete():
    """Delete multiple shots. Expects JSON body: {"ids": [1,2,3]}"""
    uid = session.get("user_id")
    current = User.query.get(uid) if uid else None
    if not current or current.role not in ("admin", "producer", "supervisor"):
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json() or {}
    ids = data.get("ids")
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "ids (list) required"}), 400

    try:
        deleted = Shot.query.filter(Shot.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"deleted": deleted})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "delete failed", "detail": str(e)}), 500


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
        reel = s.reel if s.reel else (parts[1] if len(parts) >= 2 else "REEL")
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
    reel = s.reel if s.reel else (parts[1] if len(parts) >= 2 else "REEL")
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


@app.route("/api/shots/<int:shot_id>/create_folders", methods=["POST"])
def api_shot_create_folders(shot_id):
    """Create a set of folders for a shot. Accepts JSON {"names": ["A","B"]} or uses defaults."""
    s = Shot.query.get_or_404(shot_id)
    proj = Project.query.get(s.project_id)
    if not proj or not proj.folder_path:
        return jsonify({"error": "project folder_path not configured"}), 400

    data = {}
    if request.is_json:
        data = request.get_json() or {}
    names = data.get("names") or []
    # default shot folders
    if not names:
        names = ["Plates", "Comp", "Render", "Assets", "Deliverables"]

    created = []
    errors = []
    shot_folder_name = s.code or f"shot_{s.id}"
    # create folders under project folder -> Shots -> <shot_code> -> <name>
    shots_base = os.path.join(proj.folder_path, "Shots")
    for nm in names:
        try:
            target = os.path.join(shots_base, shot_folder_name, nm)
            os.makedirs(target, exist_ok=True)
            created.append(target)
        except Exception as e:
            errors.append({"name": nm, "error": str(e)})

    return jsonify({"created": created, "errors": errors})


@app.route("/api/shots/<int:shot_id>/generate_structure", methods=["POST"])
def api_shot_generate_structure(shot_id):
    """Create standard comp structure for a shot inside the project's Comps/<reel>/<shot_code>/ folder.

    Creates: Annotations, CG Assets, comp, DeNoise, MM, Paint, precomp, Roto
    """
    s = Shot.query.get_or_404(shot_id)
    proj = Project.query.get(s.project_id)
    if not proj or not proj.folder_path:
        return jsonify({"error": "project folder_path not configured"}), 400

    # Determine reel (prefer stored `reel`, fallback to shot.code second segment)
    parts = (s.code or "").split("_")
    raw_reel = s.reel if s.reel and str(s.reel).strip() else (parts[1] if len(parts) >= 2 and parts[1] else "01")
    # Normalize reel folder name: prefix with 'Reel_' unless already contains 'reel'
    if isinstance(raw_reel, str) and raw_reel.strip():
        rr = raw_reel.strip()
    else:
        rr = "01"
    if rr.lower().startswith("reel"):
        reel_folder_name = rr
    else:
        reel_folder_name = f"Reel_{rr}"

    shot_folder = s.code or f"shot_{s.id}"

    comp_base = os.path.join(proj.folder_path, "Comps")
    reel_dir = os.path.join(comp_base, reel_folder_name)
    shot_dir = os.path.join(reel_dir, shot_folder)

    subfolders = ["Annotations", "CG Assets", "comp", "DeNoise", "MM", "Paint", "precomp", "Roto"]

    created = []
    errors = []
    try:
        for p in [comp_base, reel_dir, shot_dir]:
            try:
                os.makedirs(p, exist_ok=True)
            except Exception as e:
                errors.append({"path": p, "error": str(e)})
        for sf in subfolders:
            try:
                target = os.path.join(shot_dir, sf)
                os.makedirs(target, exist_ok=True)
                created.append(target)
            except Exception as e:
                errors.append({"name": sf, "error": str(e)})
    except Exception as e:
        app.logger.exception("generate_structure failed")
        return jsonify({"error": "failed", "detail": str(e)}), 500

    return jsonify({"created": created, "errors": errors})


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
        # Use reel column from database
        cw.writerow([s.id, s.code, s.reel or "", s.extract_version() or "", s.description, s.assigned_to, s.due_date, s.status, s.plate_path, s.mov_path, s.exr_path])
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
        "reel": ["reel", "reel_code", "reelcode"],
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
            reel = get_alias("reel")

            if not code:
                errors.append({"line": line_no, "error": "missing code"})
                continue

            if not version:
                m = re.search(r"[Vv](\d+)", code)
                if m:
                    version = f"V{m.group(1)}"

            # build mapping for bulk insert (reel stored separately, code unchanged)
            mapping = {
                "project_id": project_id,
                "code": code,
                "reel": reel or "",
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

        # attempt to detect a reel column position (headerless) by heuristics
        reel_pos = None
        if filtered:
            max_cols = max(len(r) for r in filtered)
            # search candidate positions within first 6 columns (after idx)
            candidates = range(0, min(6, max_cols))
            best = None
            for c in candidates:
                vals_c = [r[c].strip() for r in filtered if len(r) > c and (r[c] or '').strip()]
                if not vals_c:
                    continue
                # reel-like: short, no spaces, alnum/underscore/dash, not a date, not purely numeric
                reel_like = [v for v in vals_c if re.match(r"^[A-Za-z0-9_-]{1,8}$", v) and not re.match(r"^\d{4}-\d{2}-\d{2}$", v) and not v.isdigit()]
                ratio = len(reel_like) / len(vals_c)
                if ratio >= 0.6 and len(vals_c) >= 2:
                    best = c
                    break
            if best is not None:
                reel_pos = best

        line_no = 0
        for vals in filtered:
            line_no += 1
            # If first column is an index, shift columns by one
            idx = 1 if skip_index else 0
            code = vals[idx].strip() if len(vals) > idx else ""
            # If a separate reel column detected, extract it
            reel = None
            if reel_pos is not None and len(vals) > reel_pos:
                reel = vals[reel_pos].strip()
            # assume positions: code, reel, description, assigned_to, start_date, due_date, status, plate, mov, exr, version
            if reel_pos is not None and reel_pos == idx+1:
                description = vals[idx+2].strip() if len(vals) > idx+2 else ""
                assigned_to = vals[idx+3].strip() if len(vals) > idx+3 else ""
                start_date = vals[idx+4].strip() if len(vals) > idx+4 else ""
                due_date = vals[idx+5].strip() if len(vals) > idx+5 else ""
                status = vals[idx+6].strip() if len(vals) > idx+6 and vals[idx+6].strip() else "Not Started"
                plate_path = vals[idx+7].strip() if len(vals) > idx+7 else ""
                mov_path = vals[idx+8].strip() if len(vals) > idx+8 else ""
                exr_path = vals[idx+9].strip() if len(vals) > idx+9 else ""
                version = vals[idx+10].strip() if len(vals) > idx+10 else ""
            else:
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
                "reel": reel or "",
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
            # Filter out duplicate codes within same project
            existing_codes = set(s.code for s in Shot.query.filter_by(project_id=project_id).all())
            filtered_rows = []
            skipped_duplicates = 0
            for mapping in to_insert:
                code = mapping.get('code', '').strip()
                if code in existing_codes:
                    skipped_duplicates += 1
                    errors.append({"error": f"Skipped duplicate code: {code}"})
                    continue
                filtered_rows.append(mapping)
                existing_codes.add(code)  # track newly added codes to skip duplicates within import file
            
            # Use bulk_insert_mappings to bypass per-object overhead
            if filtered_rows:
                db.session.bulk_insert_mappings(Shot, filtered_rows)
                db.session.commit()
                imported = len(filtered_rows)
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
        "reel": ["reel", "reel_code", "reelcode"],
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
        # default positional mapping: code,reel,description,assigned_to,start_date,due_date,status,plate_path,mov_path,exr_path,version
        posmap = ["code","reel","description","assigned_to","start_date","due_date","status","plate_path","mov_path","exr_path","version"]
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
