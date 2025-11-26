import os
from flask import Flask
from dotenv import load_dotenv

# Import db and models from models module
from .models import db, Conversation, Bot, Message, ConversationBot, User
from .routes import bp as main_bp
from .seed_bots import build_default_bots


def create_app():
    # Load env vars from .env so I do not hardcode secrets
    load_dotenv()

    app = Flask(__name__)

    # Basic secret key for sessions
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    # DB connection, default to local sqlite file
    db_url = os.environ.get("DATABASE_URL", "sqlite:///chatroom.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Attach SQLAlchemy to this app
    db.init_app(app)

    with app.app_context():
        # Make sure tables exist in the DB
        db.create_all()
        # Seed default bots only if there are none
        seed_default_bots()

    # Register main blueprint with all routes
    app.register_blueprint(main_bp)

    return app


def seed_default_bots():
    # Insert default bots if they are missing (idempotent)
    existing_names = {b.name for b in Bot.query.all()}

    default_bots = build_default_bots()

    created = False
    # Insert default bots into DB
    for b in default_bots:
        if b["name"] in existing_names:
            continue
        created = True
        db.session.add(
            Bot(
                name=b["name"],
                role=b["role"],
                system_prompt=b["system_prompt"],
                model_name=b["model_name"],
            )
        )

    if created:
        db.session.commit()
