"""Groq LLM Client and Provider Interface for Football Intelligence Agent.

Integrates with the official Groq API endpoint:
POST https://api.groq.com/openai/v1/chat/completions
Documentation: https://console.groq.com/docs
Browser-search documentation: https://console.groq.com/docs/tool-use/built-in-tools/browser-search

Handles structured reasoning, function calling, server-side browser search,
bounded retries, and provides deterministic mock modes for test isolation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
import httpx

try:
    from groq import AsyncGroq, Groq, APIError, AuthenticationError, RateLimitError, BadRequestError
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False

from app.config.settings import settings

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Raised when Groq API returns an error or fails."""
    pass


# Base LLM Client Interface
class BaseLLMClient(ABC):
    """Provider-neutral LLM client interface."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if real LLM API credentials are configured."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        enable_web_search: bool = False,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate a response with optional function tools and browser search."""
        pass


class GroqClient(BaseLLMClient):
    """Client for official Groq API supporting OpenAI open-weight models, tool calling, and browser search."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        mock_mode: bool = False,
    ):
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        self.model = model or settings.groq_model
        self.base_url = (base_url or settings.groq_base_url).rstrip("/")
        self.timeout = timeout or settings.groq_timeout_seconds
        self.mock_mode = mock_mode
        self._mock_handler: Optional[Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]] = None

        # Initialize official Groq async client if key is configured
        self._sdk_client: Optional[Any] = None
        if HAS_GROQ_SDK and self.is_configured():
            try:
                self._sdk_client = AsyncGroq(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout,
                )
            except Exception as exc:
                logger.warning(f"Failed to initialize AsyncGroq SDK client: {exc}")

    def set_mock_handler(
        self,
        handler: Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]
    ) -> None:
        """Set a deterministic handler for test suites without making live network requests."""
        self._mock_handler = handler
        self.mock_mode = True

    def is_configured(self) -> bool:
        """Check if an authentic Groq API key is configured."""
        if not self.api_key:
            return False
        key = self.api_key.strip()
        return bool(key and not key.startswith("your_") and not key.startswith("xai-"))

    def _extract_citations(
        self,
        content: Optional[str],
        executed_tools: Optional[List[Dict[str, Any]]],
    ) -> List[str]:
        """Extract source URLs from executed browser tools and content."""
        citations: List[str] = []

        # 1. Extract from executed_tools (Groq browser_search search results)
        if executed_tools and isinstance(executed_tools, list):
            for tool_item in executed_tools:
                if not isinstance(tool_item, dict):
                    continue
                search_results = tool_item.get("search_results") or {}
                results_list = search_results.get("results") or []
                for r in results_list:
                    if isinstance(r, dict) and "url" in r:
                        u = r["url"]
                        if u and u not in citations:
                            citations.append(u)

        # 2. Extract markdown or plaintext URLs from final text content
        if content:
            # Markdown links: [text](url)
            md_urls = re.findall(r'\[(?:[^\]]+)\]\((https?://[^\s\)]+)\)', content)
            for u in md_urls:
                if u not in citations:
                    citations.append(u)
            # Plaintext URLs
            raw_urls = re.findall(r'(https?://[^\s\<\>"\']+[a-zA-Z0-9/])', content)
            for u in raw_urls:
                clean_u = u.rstrip(".,;)]}")
                if clean_u not in citations:
                    citations.append(clean_u)

        return citations

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        enable_web_search: bool = False,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Send a request to the official Groq chat completions API (`POST /chat/completions`).

        Supports built-in server-side `browser_search` and custom client-side function calling.

        Returns a normalized dictionary formatted with:
        {
            "role": "assistant",
            "content": str or None,
            "tool_calls": List[Dict] or None,       # Custom local function calls only
            "executed_tools": List[Dict] or None,   # Server-side browser_search activities
            "citations": List[str],                 # Grounding source URLs
            "reasoning": str or None,               # CoT reasoning trace
            "finish_reason": str,
            "response_id": str or None
        }
        """
        # If in mock mode or API key is not configured for tests
        if self.mock_mode or not self.is_configured():
            if self._mock_handler:
                res = self._mock_handler(messages, tools or [])
                if "citations" not in res:
                    res["citations"] = []
                if "executed_tools" not in res:
                    res["executed_tools"] = None
                if "web_search_calls" in res and "executed_tools" not in res:
                    res["executed_tools"] = res["web_search_calls"]
                return res

            if not self.is_configured():
                raise GroqAPIError(
                    "GROQ_API_KEY is not configured. Please set GROQ_API_KEY in your environment or .env file. "
                    "The Football Intelligence Engine strictly refuses to silently substitute an unconfigured secondary LLM."
                )

        # Assemble tools payload
        active_tools: List[Dict[str, Any]] = []
        if enable_web_search:
            # Groq documented built-in browser search tool
            active_tools.append({"type": "browser_search"})

        if tools:
            # Custom application functions
            active_tools.extend(tools)

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build request payload
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if active_tools:
            payload["tools"] = active_tools

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(endpoint, headers=headers, json=payload)

                    if response.status_code == 401:
                        raise GroqAPIError("Groq API Authentication failed: Invalid or expired GROQ_API_KEY.")

                    if response.status_code == 429:
                        wait_sec = attempt * 2.0
                        logger.warning(f"Groq API rate limit hit (429). Retrying in {wait_sec}s (attempt {attempt}/{max_retries})...")
                        if attempt < max_retries:
                            await asyncio.sleep(wait_sec)
                            continue
                        raise GroqAPIError("Groq API rate limit exceeded after maximum retries. Please back off.")

                    if response.status_code >= 500:
                        wait_sec = attempt * 1.5
                        logger.warning(f"Groq server error ({response.status_code}). Retrying in {wait_sec}s...")
                        if attempt < max_retries:
                            await asyncio.sleep(wait_sec)
                            continue
                        raise GroqAPIError(f"Groq upstream server error ({response.status_code}): {response.text}")

                    if response.status_code >= 400:
                        err_text = response.text
                        try:
                            err_json = response.json()
                            err_msg = err_json.get("error", {}).get("message", err_text)
                        except Exception:
                            err_msg = err_text
                        raise GroqAPIError(f"Groq API error (HTTP {response.status_code}): {err_msg}")

                    data = response.json()
                    response_id = data.get("id")

                    choices = data.get("choices", [])
                    if not choices:
                        return {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": None,
                            "executed_tools": None,
                            "citations": [],
                            "reasoning": None,
                            "finish_reason": "stop",
                            "response_id": response_id,
                        }

                    choice = choices[0]
                    msg = choice.get("message", {})
                    content = msg.get("content")
                    raw_tool_calls = msg.get("tool_calls")
                    executed_tools = msg.get("executed_tools")
                    reasoning = msg.get("reasoning")
                    finish_reason = choice.get("finish_reason", "stop")

                    # Parse custom function calls
                    parsed_tool_calls = []
                    if raw_tool_calls and isinstance(raw_tool_calls, list):
                        for tc in raw_tool_calls:
                            if isinstance(tc, dict):
                                parsed_tool_calls.append({
                                    "id": tc.get("id", f"call_{len(parsed_tool_calls)}"),
                                    "type": "function",
                                    "function": {
                                        "name": tc.get("function", {}).get("name", ""),
                                        "arguments": tc.get("function", {}).get("arguments", "{}"),
                                    },
                                })

                    # Extract grounding citations
                    citations = self._extract_citations(content, executed_tools)

                    return {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": parsed_tool_calls if parsed_tool_calls else None,
                        "executed_tools": executed_tools if executed_tools else None,
                        "web_search_calls": executed_tools if executed_tools else None,  # Compatibility alias
                        "citations": citations,
                        "reasoning": reasoning,
                        "finish_reason": finish_reason,
                        "response_id": response_id,
                    }

            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(f"Groq API timeout on attempt {attempt}/{max_retries}: {exc}")
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 1.0)
                    continue
                raise GroqAPIError(f"Groq API request timed out after {self.timeout}s: {exc}") from exc
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(f"Network error on attempt {attempt}/{max_retries}: {exc}")
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 1.0)
                    continue
                raise GroqAPIError(f"Network error connecting to Groq API: {exc}") from exc

        raise GroqAPIError(f"Groq API call failed after {max_retries} attempts: {last_error}")


# Backwards compatibility aliases
GrokClient = GroqClient
GrokAPIError = GroqAPIError
