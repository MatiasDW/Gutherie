from typing import List, Optional
from .models import Bot


class RouterBot:
    """
    Simple, rule-based orchestrator that can involve multiple specialists.
    """

    ROLE_KEYWORDS = {
        "project_owner": ["scope", "goal", "requirement", "story", "product", "stakeholder", "business"],
        "project_manager": ["timeline", "deadline", "plan", "estimate", "risk", "milestone", "priority", "deliverable"],
        "solution_architect": ["architecture", "design", "pattern", "scalable", "scalability", "security", "compliance", "integration"],
        "devops": ["deploy", "deployment", "docker", "kubernetes", "infra", "infrastructure", "ci", "cd", "pipeline", "monitoring", "logging", "reliability"],
        "data_engineer": ["pipeline", "ingest", "ingestion", "etl", "elt", "warehouse", "lake", "schema", "dbt"],
        "data_scientist": ["model", "ml", "machine learning", "experiment", "analysis", "dataset", "feature", "prediction", "forecast"],
        "backend_engineer": ["api", "endpoint", "backend", "service", "microservice", "database", "auth", "authorization", "logic"],
        "database_engineer": ["sql", "database", "mysql", "postgres", "postgresql", "index", "query", "transaction", "migration", "schema"],
        "frontend_engineer": ["ui", "ux", "frontend", "react", "component", "layout", "css", "design system", "accessibility"],
    }

    PRIORITY_ORDER = [
        "orchestrator",
        "project_manager",
        "project_owner",
        "solution_architect",
        "backend_engineer",
        "database_engineer",
        "devops",
        "data_engineer",
        "data_scientist",
        "frontend_engineer",
    ]

    def choose_bots(self, text: str, available_bots: List[Bot]) -> List[Bot]:
        if not available_bots:
            return []

        lower = text.lower()
        selected_roles = set()

        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(keyword in lower for keyword in keywords):
                selected_roles.add(role)

        bots_by_role = {bot.role: bot for bot in available_bots}

        # Pick best-matching specialist (exclude orchestrator from responses)
        if selected_roles:
            for role in self.PRIORITY_ORDER:
                if role == "orchestrator":
                    continue
                if role in selected_roles:
                    bot = bots_by_role.get(role)
                    if bot:
                        return [bot]

        # Fallback preference: architect or backend as generalists
        for fallback_role in ["solution_architect", "backend_engineer"]:
            bot = bots_by_role.get(fallback_role)
            if bot:
                return [bot]

        # Final fallback: first non-orchestrator, else first bot
        for bot in available_bots:
            if bot.role != "orchestrator":
                return [bot]
        return available_bots[:1]
