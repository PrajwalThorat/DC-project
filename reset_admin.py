from werkzeug.security import generate_password_hash
from app import app, db, User
with app.app_context():
    admin = User.query.filter_by(username="admin").first()
    if admin:
        admin.pwd_hash = generate_password_hash("admin")
        db.session.commit()
        print("Admin password reset to: admin")
    else:
        u = User(username="admin", pwd_hash=generate_password_hash("admin"), role="admin", display_name="Administrator")
        db.session.add(u)
        db.session.commit()
        print("Created admin/admin")
