from __future__ import annotations

from typing import Any

import httpx


class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate_text(self, prompt: str, system_prompt: str | None = None, max_tokens: int = 800) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"Groq error {response.status_code}: {response.text[:500]}")
            data = response.json()
            return data["choices"][0]["message"]["content"]


__all__ = ["GroqProvider"]
