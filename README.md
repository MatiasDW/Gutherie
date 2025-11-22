# AI Chatroom

Small multi-bot chatroom built with Flask, HTMX, and SQLite, using local LLMs served by Ollama. Multiple bots (Email, Code, Accounting, Joke, plus any custom bots you add) share a chatroom; a RouterBot picks who answers each message.

## Features
- Multiple bots per conversation; attach/detach per conversation
- Create custom bots with name, role, system prompt, and model
- Change bot model via dropdown
- RouterBot picks a bot by intent; fallback matches custom bot role/name if mentioned, then first attached
- HTMX: send without full reload, auto-refresh messages
- SQLite persistence for conversations, messages, bots, and conversation/bot links
- Docker Compose for the web app and Ollama

## Project Structure
```
app/
  __init__.py        # Flask factory, DB init, seed bots
  models.py          # SQLAlchemy models
  routes.py          # Routes and message handling
  router.py          # RouterBot keyword/role/name routing
  templates/
    index.html       # Main chat UI
    _messages.html   # Messages partial
    _bots_sidebar.html
  static/
    htmx.min.js
    styles.css
Dockerfile
docker-compose.yml
README.md
```

## Requirements
- Docker and Docker Compose
- Internet to pull Ollama image/model (one time)
- Host Python not required; runs in containers

## Environment Variables
`.env` example (project root):
```
FLASK_APP=app:create_app
FLASK_ENV=development
DATABASE_URL=sqlite:////app/instance/chatroom.db
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3
```

## First-Time Setup
1) Clone the repo
```
git clone https://github.com/MatiasDW/Gutherie.git fot https
git clone git@github.com:MatiasDW/Gutherie.git fot ssh

cd ai-chatroom
```
2) Create `.env` (see above)
3) Ensure HTMX is local (already in `app/static/htmx.min.js`; if missing):
```
curl -L https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o app/static/htmx.min.js
```

## Run with Docker
1) Build and start
```
docker compose up --build
```
Flask: `http://127.0.0.1:5000`  
Ollama: `http://127.0.0.1:11434` (internal: `http://ollama:11434`)

2) Pull the model in Ollama
```
docker compose exec ollama ollama pull llama3
```

3) Verify DB path
```
docker compose exec web python - <<'PY'
from app import create_app, db
app = create_app()
with app.app_context():
    print("DB URL:", db.engine.url)
PY
```

## Using the App
- Open `http://127.0.0.1:5000`
- Create/select conversations
- Attach/detach bots per conversation
- Create custom bots (name, role, prompt, model) in the sidebar
- Send messages; HTMX posts to `/message`, router picks a bot
- Messages auto-refresh via HTMX polling

## Router Logic
- Keywords → roles:
  - email/mail/subject/correo → `email`
  - code/python/bug/function/error → `code`
  - invoice/factura/tax/balance → `accounting`
  - joke/chiste/funny/risa → `joke`
- If no keyword rule matches, it tries any attached bot whose role or name appears in the message (works for custom bots).
- Final fallback: first attached bot.

## Database Schema (high level)
- `conversations`: id, title, created_at
- `messages`: id, conversation_id, sender_type, bot_id (nullable), content, created_at
- `bots`: id, name, role, model_name, system_prompt
- `conversation_bots`: id, conversation_id, bot_id

## Troubleshooting
- HTMX not working: ensure `app/static/htmx.min.js` exists and `base.html` includes it.
- Ollama errors: `docker compose ps`; `docker compose exec ollama ollama pull llama3`; ensure bot model names exist.
- DB path: default `/app/instance/chatroom.db` (`sqlite:////app/instance/chatroom.db`). Use an absolute path to avoid accidental new DB files.

## License
You can adapt this project as needed for your own experiments or interview exercises.
