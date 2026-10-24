"""Compatibility Bridge: GrokClient -> GroqClient.

Migrated to official Groq API client with browser_search support.
This module retains backwards compatibility aliases for existing components.
"""

from __future__ import annotations

from app.agent.groq_client import (
    BaseLLMClient,
    GroqAPIError,
    GroqClient,
)

# Compatibility aliases
GrokAPIError = GroqAPIError
GrokClient = GroqClient

__all__ = ["BaseLLMClient", "GroqClient", "GroqAPIError", "GrokClient", "GrokAPIError"]
