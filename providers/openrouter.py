from __future__ import annotations

import base64
import json
from typing import Any

import httpx


class OpenRouterProvider:
    def __init__(self, api_key: str, model: str, base_url: str = "https://openrouter.ai/api/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def _post(self, payload: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "discord-ai-agent",
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            if response.status_code >= 400:
                message = response.text[:500]
                raise RuntimeError(f"OpenRouter error {response.status_code}: {message}")
            return response.json()

    async def generate_text(self, prompt: str, system_prompt: str | None = None, max_tokens: int = 800) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        data = await self._post(payload)
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content)

    async def generate_multimodal(self, prompt: str, image_path: str | None = None, image_bytes: bytes | None = None, system_prompt: str | None = None) -> str:
        if not image_path and not image_bytes:
            return await self.generate_text(prompt, system_prompt=system_prompt)

        if image_bytes is None and image_path:
            with open(image_path, "rb") as handle:
                image_bytes = handle.read()

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})
        payload = {"model": self.model, "messages": messages, "max_tokens": 800}
        data = await self._post(payload)
        return data["choices"][0]["message"]["content"]


__all__ = ["OpenRouterProvider"]
