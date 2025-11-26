from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Single db instance used by the whole app
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversations = db.relationship("Conversation", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Just a human readable title for the chat
    title = db.Column(db.String(120), nullable=False, default="New conversation")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="conversations")
    # All messages that belong to this conversation
    messages = db.relationship("Message", backref="conversation", lazy=True)
    # Link table to know which bots are attached to this conversation
    bots = db.relationship(
        "ConversationBot",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Bot(db.Model):
    __tablename__ = "bots"

    id = db.Column(db.Integer, primary_key=True)
    # Display name of the bot in the UI
    name = db.Column(db.String(80), unique=True, nullable=False)
    # Simple role tag so the router can pick a bot
    role = db.Column(db.String(50), nullable=False)
    # System prompt used when calling the LLM
    system_prompt = db.Column(db.Text, nullable=False)
    # Ollama model name for this bot
    model_name = db.Column(db.String(80), nullable=False)

    # Conversations that use this bot
    conversations = db.relationship(
        "ConversationBot",
        back_populates="bot",
        cascade="all, delete-orphan",
    )


class ConversationBot(db.Model):
    __tablename__ = "conversation_bots"

    id = db.Column(db.Integer, primary_key=True)
    # Many to many link, conversation <-> bot
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False
    )
    bot_id = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=False)

    conversation = db.relationship("Conversation", back_populates="bots")
    bot = db.relationship("Bot", back_populates="conversations")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    # The conversation this message belongs to
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("conversations.id"), nullable=False
    )
    # If sender is a bot, this points to that bot, otherwise null
    bot_id = db.Column(db.Integer, db.ForeignKey("bots.id"), nullable=True)
    # Quick relationship to read bot attributes on templates
    bot = db.relationship("Bot", lazy="joined")
    # Just "user" or "bot"
    sender_type = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
