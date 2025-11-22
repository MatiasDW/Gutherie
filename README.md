# AI Chatroom

This project provides a lightweight Flask-based chatroom interface connected to multiple local LLM bots powered by Ollama. Users can create conversations, attach bots, and receive AI-generated responses in real-time via HTMX.

## Features

- Multiple bots per conversation (Accounting, Email, Coding, Jokes)
- Local LLM inference through Ollama
- Router system that automatically selects the correct bot based on intent
- Option for manual bot selection
- Auto-refresh messages using HTMX polling
- Dockerized environment (Flask + Ollama)
- SQLite local database for conversations, messages and bots

## Project Structure

```
app/
  __init__.py
  models.py
  routes.py
  router.py
  templates/
    index.html
    _messages.html
  static/
    htmx.min.js
    styles.css
Dockerfile
docker-compose.yml
README.md
```

## Requirements

- Docker and Docker Compose  
- Ollama container running model llama3 (or others)  
- Python 3.12 container side  
- Flask, SQLAlchemy, HTMX

## Running the Project

### 1) Build

```
docker-compose build
```

### 2) Run Containers

```
docker-compose up
```

Flask app URL:

```
http://127.0.0.1:5000
```

Ollama service runs at port 11434.

## Usage

### Create conversations

Use the left sidebar to create or switch between conversations.

### Attach bots

You can add multiple bots with roles:

- accounting  
- email  
- code  
- joke

Each bot may run a different model (llama3 etc).

### Send messages

Write your message at the bottom.  
HTMX posts to `/message` and reloads the message list.

If manual bot selection is enabled, you can choose which bot replies.

## Router Behavior

The router inspects the user message and matches:

- "email", "correo", "subject" → email bot  
- "code", "python", "bug" → code bot  
- "invoice", "factura", "tax" → accounting bot  
- "joke", "chiste", "funny" → joke bot  

If nothing matches, it falls back to the first bot.

## Database Schema

**Conversations**  
Store chat sessions.

**Messages**  
Fields:
- conversation_id  
- sender_type  
- bot_id  
- content  
- created_at  

**Bots**  
Fields:  
- name  
- role  
- model  
- system_prompt  

## Troubleshooting

### Messages only show after refresh

This happens when HTMX is not loaded.  
Ensure you are loading it locally:

```
<script src="/static/htmx.min.js"></script>
```

Also confirm the form has:

```
hx-post="/message"
hx-target="#messages"
hx-swap="innerHTML"
```

### Slow model loading

CPU-only systems may take over a minute to load large models like LLaMA‑3‑8B.  
Inference becomes faster after first load.

## License
