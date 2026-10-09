from __future__ import annotations

from typing import Any

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


class GeminiProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate_text(self, prompt: str, system_prompt: str | None = None, max_tokens: int = 800) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        if genai is None:
            raise RuntimeError("google-genai is not installed. Install it with pip install google-genai.")

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=f"{system_prompt or ''}\n\n{prompt}".strip(),
            config={"max_output_tokens": max_tokens, "temperature": 0.7},
        )
        if hasattr(response, "text"):
            return response.text
        return str(response)


__all__ = ["GeminiProvider"]
