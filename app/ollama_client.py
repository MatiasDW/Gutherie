import os
import requests


class OllamaClient:
    def __init__(self):
        # Use env var so I can switch host easily (local vs docker)
        self.host = os.environ.get("OLLAMA_HOST", "http://ollama:11434")
        # First request can be slow while the model loads; use a generous default
        self.timeout = int(os.environ.get("OLLAMA_TIMEOUT", "500"))

    def chat(self, model: str, system_prompt: str, user_message: str) -> str:
        """
        Simple wrapper to call Ollama chat API.
        First call can be slow because the model needs to load.
        """
        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"].strip()
            return "Sorry, I could not parse the Ollama response."
        except requests.exceptions.Timeout:
            return "Ollama timeout: response took too long."
        except Exception as e:
            # Do not crash the app, just show the error as text
            return f"Ollama error: {e}"
