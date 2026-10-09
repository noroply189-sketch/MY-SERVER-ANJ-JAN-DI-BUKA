from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from config.settings import get_settings
from providers.gemini import GeminiProvider
from providers.groq import GroqProvider
from providers.openrouter import OpenRouterProvider

settings = get_settings()


@dataclass
class AIRequest:
    prompt: str
    system_prompt: str | None = None
    image_path: str | None = None
    image_bytes: bytes | None = None
    max_tokens: int = 800
    task_type: str = "general"


class AIRouter:
    def __init__(self) -> None:
        self.providers = {
            "openrouter": OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_model),
            "groq": GroqProvider(settings.groq_api_key, settings.groq_model),
            "gemini": GeminiProvider(settings.gemini_api_key, settings.gemini_model),
        }
        self.primary = settings.ai_primary_provider.lower()
        self.fallback_order = [p.strip().lower() for p in settings.ai_fallback_order if p.strip()]

    def _ordered_providers(self) -> list[str]:
        order = [self.primary] + [p for p in self.fallback_order if p != self.primary]
        return [p for p in order if p in self.providers]

    async def _call_provider(self, provider_name: str, request: AIRequest) -> str:
        provider = self.providers[provider_name]
        if request.image_path or request.image_bytes:
            if hasattr(provider, "generate_multimodal"):
                return await provider.generate_multimodal(
                    request.prompt,
                    image_path=request.image_path,
                    image_bytes=request.image_bytes,
                    system_prompt=request.system_prompt,
                )
        return await provider.generate_text(
            request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
        )

    async def route(self, request: AIRequest) -> str:
        errors: list[str] = []
        for provider_name in self._ordered_providers():
            try:
                return await asyncio.wait_for(self._call_provider(provider_name, request), timeout=60)
            except Exception as exc:  # pragma: no cover - real provider failure path
                errors.append(f"{provider_name}: {exc}")
                continue
        raise RuntimeError(f"All AI providers failed: {'; '.join(errors) or 'No backend available'}")


router = AIRouter()

__all__ = ["AIRouter", "AIRequest", "router"]
