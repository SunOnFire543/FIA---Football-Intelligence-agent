"""Unit tests for Groq API client (`POST /chat/completions`)."""

import asyncio
import pytest
from app.agent.groq_client import GroqClient, GroqAPIError


def test_groq_api_endpoint_and_model():
    client = GroqClient(api_key="gsk_test_key", base_url="https://api.groq.com/openai/v1")
    # Base URL must be configured for the official Groq API
    assert client.base_url == "https://api.groq.com/openai/v1"
    assert client.model == "openai/gpt-oss-120b"


def test_groq_client_missing_key_explicit_error():
    client = GroqClient(api_key="", mock_mode=False)
    with pytest.raises(GroqAPIError) as exc_info:
        asyncio.run(client.generate_response(messages=[{"role": "user", "content": "Hello"}]))
    assert "GROQ_API_KEY is not configured" in str(exc_info.value)
    assert "strictly refuses to silently substitute an unconfigured secondary LLM" in str(exc_info.value)


def test_groq_api_mock_tool_parsing():
    client = GroqClient(api_key="gsk_mock_key", mock_mode=True)

    # Groq returns tool_calls in message
    def mock_groq_api(messages, tools):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_resp_123",
                    "type": "function",
                    "function": {
                        "name": "predict_match_markets",
                        "arguments": '{"fixture_id": "FIX_ARS_CHE_2026"}',
                    },
                }
            ],
            "finish_reason": "tool_calls",
            "response_id": "resp_001",
        }

    client.set_mock_handler(mock_groq_api)

    resp = asyncio.run(
        client.generate_response(
            messages=[{"role": "user", "content": "Analyze match"}],
            tools=[{"type": "function", "function": {"name": "predict_match_markets", "parameters": {}}}],
        )
    )

    assert resp["role"] == "assistant"
    assert resp["tool_calls"] is not None
    assert len(resp["tool_calls"]) == 1
    call = resp["tool_calls"][0]
    assert call["id"] == "call_resp_123"
    assert call["function"]["name"] == "predict_match_markets"
    assert "FIX_ARS_CHE_2026" in call["function"]["arguments"]
