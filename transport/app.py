from flask import Flask
from flask_migrate import Migrate  # ➕ Import
from transport.models import db
from transport.routes.admin import admin_bp
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Absolute path for DB file
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Register Blueprint
app.register_blueprint(admin_bp, url_prefix='/admin')

# Initialize DB with app context
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    try:
        db.create_all()
        print("✅ Tables created or already exist.")
    except Exception as e:
        print("❌ Error during DB creation:", e)

# Test route
@app.route("/test")
def test():
    return f"App is working - {datetime.utcnow()}"

# Optional: CLI command to reset DB
@app.cli.command("reset-db")
def reset_db():
    """Drop and recreate all database tables."""
    from transport.models import db
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database has been reset.")
