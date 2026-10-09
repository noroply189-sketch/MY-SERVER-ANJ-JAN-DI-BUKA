from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from database.db import get_connection


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[int, dict[str, Any]] = defaultdict(dict)

    async def get_session(self, user_id: int) -> dict[str, Any]:
        if user_id not in self._sessions:
            self._sessions[user_id] = {
                "history": [],
                "preferences": {},
            }
        return self._sessions[user_id]

    async def append_message(self, user_id: int, role: str, content: str) -> None:
        session = await self.get_session(user_id)
        session["history"].append({"role": role, "content": content})

    async def get_history(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        session = await self.get_session(user_id)
        return session["history"][-limit:]

    async def save_to_db(self, user_id: int) -> None:
        session = await self.get_session(user_id)
        conn = await get_connection()
        try:
            await conn.execute(
                "INSERT OR REPLACE INTO users (user_id, preferences) VALUES (?, ?)",
                (user_id, json.dumps(session.get("preferences", {}))),
            )
            for item in session.get("history", []):
                await conn.execute(
                    "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                    (user_id, item["role"], item["content"]),
                )
            await conn.commit()
        finally:
            await conn.close()


session_manager = SessionManager()

__all__ = ["SessionManager", "session_manager"]
