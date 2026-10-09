from __future__ import annotations

import json
from typing import Any

import httpx

from config.settings import get_settings

settings = get_settings()


class WebSearchClient:
    def __init__(self, provider: str = "tavily", api_key: str | None = None) -> None:
        self.provider = provider.lower()
        self.api_key = api_key or settings.search_api_key

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, str]]:
        if self.provider == "tavily":
            return await self._search_tavily(query, max_results)
        if self.provider == "brave":
            return await self._search_brave(query, max_results)
        raise RuntimeError(f"Unsupported search provider: {self.provider}")

    async def _search_tavily(self, query: str, max_results: int) -> list[dict[str, str]]:
        if not self.api_key:
            raise RuntimeError("SEARCH_API_KEY is not configured.")
        payload = {"api_key": self.api_key, "query": query, "max_results": max_results}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            if response.status_code >= 400:
                raise RuntimeError(f"Tavily search failed: {response.text[:500]}")
            data = response.json()
        results = data.get("results", [])
        return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", r.get("snippet", ""))} for r in results]

    async def _search_brave(self, query: str, max_results: int) -> list[dict[str, str]]:
        if not self.api_key:
            raise RuntimeError("BRAVE_API_KEY is not configured.")
        params = {"q": query, "count": max_results, "text": "plain"}
        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
            if response.status_code >= 400:
                raise RuntimeError(f"Brave search failed: {response.text[:500]}")
            data = response.json()
        results = data.get("web", {}).get("results", [])
        return [{"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("description", "")} for item in results]


async def quick_search(query: str) -> list[dict[str, str]]:
    client = WebSearchClient(settings.search_provider, settings.search_api_key)
    return await client.search(query)


__all__ = ["WebSearchClient", "quick_search"]
