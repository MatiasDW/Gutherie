from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    g,
    flash,
)
from .models import db, Conversation, Message, Bot, ConversationBot, User
from .ollama_client import OllamaClient
from .router import RouterBot

bp = Blueprint("main", __name__)
ollama = OllamaClient()
router_bot = RouterBot()


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@bp.before_app_request
def load_current_user():
    g.current_user = get_current_user()


@bp.route("/")
def index():
    if not g.current_user:
        return redirect(url_for("main.login"))

    # Load all conversations for the left sidebar
    conversations = (
        Conversation.query.filter(
            (Conversation.user_id == g.current_user.id)
            | (Conversation.user_id.is_(None))
        )
        .order_by(Conversation.created_at.desc())
        .all()
    )
    # Load all bots defined in the system
    bots = Bot.query.order_by(Bot.name).all()

    # Just pick the latest conversation as current, or create one
    if conversations:
        current = conversations[0]
    else:
        current = Conversation(title="General", user_id=g.current_user.id)
        db.session.add(current)
        db.session.commit()

    # All messages of the current conversation
    messages = (
        Message.query.filter_by(conversation_id=current.id)
        .order_by(Message.created_at)
        .all()
    )

    # Bots that are attached to this conversation
    conv_bots = (
        ConversationBot.query.filter_by(conversation_id=current.id)
        .join(Bot)
        .all()
    )

    # If this conversation has no bots yet, attach all bots by default
    if not conv_bots:
        for b in bots:
            db.session.add(ConversationBot(conversation_id=current.id, bot_id=b.id))
        db.session.commit()
        conv_bots = (
            ConversationBot.query.filter_by(conversation_id=current.id)
            .join(Bot)
            .all()
        )

    # Pre compute which bot ids are attached, easier to use in template
    attached_bot_ids = [cb.bot_id for cb in conv_bots]

    return render_template(
        "index.html",
        conversations=conversations,
        current_conversation=current,
        messages=messages,
        bots=bots,
        conv_bots=conv_bots,
        attached_bot_ids=attached_bot_ids,
    )


@bp.route("/conversations/<int:conv_id>", methods=["GET"])
def show_conversation(conv_id):
    if not g.current_user:
        return redirect(url_for("main.login"))

    current = Conversation.query.get_or_404(conv_id)
    if current.user_id and current.user_id != g.current_user.id:
        return redirect(url_for("main.index"))

    conversations = (
        Conversation.query.filter(
            (Conversation.user_id == g.current_user.id)
            | (Conversation.user_id.is_(None))
        )
        .order_by(Conversation.created_at.desc())
        .all()
    )
    bots = Bot.query.order_by(Bot.name).all()

    messages = (
        Message.query.filter_by(conversation_id=current.id)
        .order_by(Message.created_at)
        .all()
    )

    conv_bots = (
        ConversationBot.query.filter_by(conversation_id=current.id)
        .join(Bot)
        .all()
    )
    if not conv_bots:
        for b in bots:
            db.session.add(ConversationBot(conversation_id=current.id, bot_id=b.id))
        db.session.commit()
        conv_bots = (
            ConversationBot.query.filter_by(conversation_id=current.id)
            .join(Bot)
            .all()
        )

    attached_bot_ids = [cb.bot_id for cb in conv_bots]

    return render_template(
        "index.html",
        conversations=conversations,
        current_conversation=current,
        messages=messages,
        bots=bots,
        conv_bots=conv_bots,
        attached_bot_ids=attached_bot_ids,
    )



@bp.route("/messages", methods=["GET"])
def get_messages():
    """
    Simple JSON endpoint to restore messages for a conversation.
    """
    if not g.current_user:
        return jsonify([])
    conv_id = request.args.get("conversation_id", type=int)
    if not conv_id:
        return jsonify([])

    conv = Conversation.query.get_or_404(conv_id)
    if conv.user_id and g.current_user and conv.user_id != g.current_user.id:
        return jsonify([])

    msgs = (
        Message.query.filter_by(conversation_id=conv_id)
        .order_by(Message.created_at)
        .all()
    )
    data = [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "bot_id": m.bot_id,
            "bot_name": m.bot.name if m.bot else None,
            "sender_type": m.sender_type,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]
    return jsonify(data)


@bp.route("/conversations/<int:conv_id>/messages/partial")
def messages_partial(conv_id):
    """
    Partial template with messages, used by HTMX to update the chat box.
    """
    if not g.current_user:
        return render_template("_messages.html", messages=[])
    conv = Conversation.query.get_or_404(conv_id)
    if conv.user_id and g.current_user and conv.user_id != g.current_user.id:
        messages = []
    else:
        messages = (
            Message.query.filter_by(conversation_id=conv_id)
            .order_by(Message.created_at)
            .all()
        )
    return render_template("_messages.html", messages=messages)


@bp.route("/message", methods=["POST"])
def post_message():
    if not g.current_user:
        return render_template("_messages.html", messages=[])
    # Read data from chat form
    conv_id_raw = request.form.get("conversation_id")
    content = request.form.get("content", "").strip()
    
    print("DEBUG /message:")
    print("  conversation_id raw:", conv_id_raw)
    print("  content:", repr(content))
    # Small guard to avoid crashes if conv_id is missing
    try:
        conv_id = int(conv_id_raw)

    except (TypeError, ValueError):
        conv_id = None
        print("  ERROR: no se pudo convertir conversation_id a int")

    if not conv_id:
        print("  conv_id es None o 0, devolviendo lista vacia de mensajes")
        # No conversation id → nothing to do, return empty list
        return render_template("_messages.html", messages=[])

    conversation = Conversation.query.get_or_404(conv_id)
    if conversation.user_id and conversation.user_id != g.current_user.id:
        return render_template("_messages.html", messages=[])

    if not content:
        # Empty message → just re-render existing messages
        messages = (
            Message.query.filter_by(conversation_id=conversation.id)
            .order_by(Message.created_at)
            .all()
        )
        return render_template("_messages.html", messages=messages)

    # 1) Store user message
    user_msg = Message(
        conversation_id=conversation.id,
        sender_type="user",
        content=content,
    )
    db.session.add(user_msg)
    db.session.commit()

    # 2) Get bots attached to this conversation
    conv_bots = (
        ConversationBot.query.filter_by(conversation_id=conversation.id)
        .join(Bot)
        .all()
    )
    # Exclude orchestrator from user-facing replies
    attached_bots = [cb.bot for cb in conv_bots if cb.bot.role != "orchestrator"]

    # 3) Ask RouterBot which bot(s) should answer (can be multiple)
    selected_bots = router_bot.choose_bots(content, attached_bots)

    if not selected_bots:
        db.session.add(
            Message(
                conversation_id=conversation.id,
                sender_type="bot",
                bot_id=None,
                content="[Router] No bot attached to this conversation.",
            )
        )
        db.session.commit()
    else:
        for bot in selected_bots:
            try:
                reply_text = ollama.chat(
                    model=bot.model_name,
                    system_prompt=bot.system_prompt,
                    user_message=content,
                )
            except Exception as e:
                reply_text = f"Ollama error ({bot.name}): {e}"

            db.session.add(
                Message(
                    conversation_id=conversation.id,
                    sender_type="bot",
                    bot_id=bot.id,
                    content=reply_text,
                )
            )

        db.session.commit()

    # 6) Reload all messages for this conversation
    messages = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at)
        .all()
    )
    return render_template("_messages.html", messages=messages)

@bp.route("/conversations", methods=["POST"])
def create_conversation():
    # Create a new chat channel with a simple title
    if not g.current_user:
        return redirect(url_for("main.login"))
    title = request.form.get("title", "").strip() or "New conversation"
    conv = Conversation(title=title, user_id=g.current_user.id if g.current_user else None)
    db.session.add(conv)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/bots", methods=["POST"])
def create_bot():
    # Create a custom bot with name, role, model and system prompt
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip() or "custom"
    system_prompt = request.form.get("system_prompt", "").strip()
    model_name = request.form.get("model_name", "").strip() or "llama3"

    if not name or not system_prompt:
        return redirect(url_for("main.index"))

    bot = Bot(
        name=name,
        role=role,
        system_prompt=system_prompt,
        model_name=model_name,
    )
    db.session.add(bot)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/bots/<int:bot_id>/model", methods=["POST"])
def update_bot_model(bot_id):
    # Update the model used by a bot from the dropdown
    model_name = request.form.get("model_name", "").strip()
    bot = Bot.query.get_or_404(bot_id)
    if model_name:
        bot.model_name = model_name
        db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/conversations/<int:conv_id>/bots/<int:bot_id>/toggle", methods=["POST"])
def toggle_conv_bot(conv_id, bot_id):
    # Attach or detach a bot from a conversation
    conv = Conversation.query.get_or_404(conv_id)
    if conv.user_id and g.current_user and conv.user_id != g.current_user.id:
        return redirect(url_for("main.index"))
    link = ConversationBot.query.filter_by(
        conversation_id=conv_id, bot_id=bot_id
    ).first()
    if link:
        db.session.delete(link)
    else:
        db.session.add(ConversationBot(conversation_id=conv_id, bot_id=bot_id))
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user:
        return redirect(url_for("main.index"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session.permanent = True
            session["user_id"] = user.id
            return redirect(url_for("main.index"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.current_user:
        return redirect(url_for("main.index"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            error = "Email and password are required"
        elif User.query.filter_by(email=email).first():
            error = "User already exists"
        else:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session.permanent = True
            session["user_id"] = user.id
            return redirect(url_for("main.index"))
    return render_template("register.html", error=error)


@bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("main.login"))
