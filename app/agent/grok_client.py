"""Grok LLM Client using official xAI API.

Handles structured reasoning, function calling, multi-turn tool loops,
and provides deterministic mock modes for offline testing.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional
import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


class GrokAPIError(Exception):
    """Raised when xAI API returns an error or fails."""
    pass


class GrokClient:
    """Client for xAI API supporting Grok models and tool calling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        mock_mode: bool = False,
    ):
        self.api_key = api_key or settings.xai_api_key
        self.model = model or settings.xai_model
        self.base_url = (base_url or settings.xai_base_url).rstrip("/")
        self.timeout = timeout or settings.xai_timeout_seconds
        self.mock_mode = mock_mode
        self._mock_handler: Optional[Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]] = None

    def set_mock_handler(
        self,
        handler: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]
    ) -> None:
        """Set a deterministic handler for test suites."""
        self._mock_handler = handler
        self.mock_mode = True

    def is_configured(self) -> bool:
        """Check if a real xAI API key is configured."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Send a request to xAI API or deterministic mock handler.

        Returns a dictionary formatted with:
        {
            "role": "assistant",
            "content": str or None,
            "tool_calls": List[Dict] or None,
            "finish_reason": str
        }
        """
        # If in mock mode or API key is not configured for tests
        if self.mock_mode or not self.is_configured():
            if self._mock_handler:
                return self._mock_handler(messages, tools or [])
            if not self.is_configured():
                raise GrokAPIError(
                    "XAI_API_KEY is not configured. Please set XAI_API_KEY in your environment or .env file. "
                    "The system does not silently substitute another LLM."
                )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Check for responses endpoint or chat/completions
        endpoint = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                if response.status_code == 401:
                    raise GrokAPIError("xAI API Authentication failed: Invalid or expired XAI_API_KEY.")
                if response.status_code == 429:
                    raise GrokAPIError("xAI API rate limit exceeded. Please back off and retry.")
                if response.status_code >= 400:
                    raise GrokAPIError(f"xAI API error (HTTP {response.status_code}): {response.text}")

                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]
                return {
                    "role": message.get("role", "assistant"),
                    "content": message.get("content"),
                    "tool_calls": message.get("tool_calls"),
                    "finish_reason": choice.get("finish_reason", "stop"),
                }
        except httpx.TimeoutException as exc:
            raise GrokAPIError(f"xAI API request timed out after {self.timeout}s: {exc}") from exc
        except httpx.RequestError as exc:
            raise GrokAPIError(f"Network error connecting to xAI API: {exc}") from exc
