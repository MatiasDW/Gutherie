from typing import List, Optional
from .models import Bot


class RouterBot:
    # Tiny routing helper. I keep it simple and rule based.
    def choose_bot(self, text: str, available_bots: List[Bot]) -> Optional[Bot]:
        if not available_bots:
            return None

        lower = text.lower()
        role = None

        # Very naive keyword routing by intent
        if any(k in lower for k in ["email", "mail", "subject", "correo"]):
            role = "email"
        elif any(k in lower for k in ["code", "bug", "python", "function", "error"]):
            role = "code"
        elif any(k in lower for k in ["invoice", "account", "tax", "balance", "factura"]):
            role = "accounting"
        elif any(k in lower for k in ["joke", "funny", "chiste", "risa"]):
            role = "joke"

        # Try to match by role first
        if role:
            for bot in available_bots:
                if bot.role == role:
                    return bot

        # Fallback, if no rule matches I just pick the first attached bot
        return available_bots[0]
