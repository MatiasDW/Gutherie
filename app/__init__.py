import os
from flask import Flask
from dotenv import load_dotenv

# I import the shared db instance and models
from .models import db, Bot
from .routes import bp as main_bp


def create_app():
    # Load env vars from .env so I keep config outside the code
    load_dotenv()

    app = Flask(__name__)

    # Basic secret key for sessions
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    # Make sure the instance folder exists so SQLite has a stable place to live
    os.makedirs(app.instance_path, exist_ok=True)

    # Database config. Default to an absolute SQLite file under instance/ to avoid
    # creating a new DB when the working directory changes.
    default_db_path = os.path.join(app.instance_path, "chatroom.db")
    db_url = os.environ.get("DATABASE_URL", f"sqlite:///{default_db_path}")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Attach SQLAlchemy to this Flask app instance
    db.init_app(app)

    # Register main blueprint
    app.register_blueprint(main_bp)

    # Create tables and seed default bots once at startup
    with app.app_context():
        # Important: importing models here makes sure metadata is loaded
        print("DEBUG - calling db.create_all() on", app.config["SQLALCHEMY_DATABASE_URI"])
        from .models import Conversation, Message, ConversationBot

        # This creates the tables in chatroom.db if they do not exist
        db.create_all()
        # And this inserts the 4 default bots only if bots table is empty
        seed_default_bots()

    return app


def seed_default_bots():
    # If there is already at least one bot, I skip the seed
    if Bot.query.count() > 0:
        return

    default_bots = [
        {
            "name": "EmailBot",
            "role": "email",
            "system_prompt": (
                "You help me draft and polish professional emails in clear English or Spanish, "
                "keeping the tone friendly and concise."
            ),
            "model_name": "llama3",
        },
        {
            "name": "CodeBot",
            "role": "code",
            "system_prompt": (
                "You help me read, debug, and explain code. "
                "Keep answers short and practical, with code blocks when needed."
            ),
            "model_name": "llama3",
        },
        {
            "name": "AccountingBot",
            "role": "accounting",
            "system_prompt": (
                "You answer basic accounting, invoicing, and tax questions. "
                "Explain things step by step in simple language."
            ),
            "model_name": "llama3",
        },
        {
            "name": "JokeBot",
            "role": "joke",
            "system_prompt": (
                "You tell short, harmless jokes. One or two lines max, family friendly."
            ),
            "model_name": "llama3",
        },
    ]

    # I persist the default bots into the database
    for b in default_bots:
        db.session.add(
            Bot(
                name=b["name"],
                role=b["role"],
                system_prompt=b["system_prompt"],
                model_name=b["model_name"],
            )
        )
    db.session.commit()
