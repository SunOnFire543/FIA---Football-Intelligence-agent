"""Unit tests for Phase 1 Core Foundation components."""

import asyncio
import pytest
from app.config.settings import Settings
from app.agent.grok_client import GrokClient, GrokAPIError
from app.agent.tool_registry import ToolRegistry
from app.agent.executor import AgentExecutor
from app.db.session import init_db, drop_db, SessionLocal
from app.db.models import DBCompetition, DBTeam


def run_async(coro):
    return asyncio.run(coro)


def test_settings_masked_keys():
    s = Settings(xai_api_key="xai-1234567890abcdef")
    masked = s.get_masked_api_key("xai_api_key")
    assert masked == "xai...cdef"
    assert "1234567890" not in masked


def test_db_init_and_entities():
    init_db()
    db = SessionLocal()
    try:
        comp = DBCompetition(
            id="PL",
            name="Premier League",
            country="England",
            division=1,
            provider="demo",
        )
        db.merge(comp)
        team = DBTeam(
            id="ARS",
            name="Arsenal FC",
            short_name="Arsenal",
            competition_id="PL",
            stadium="Emirates Stadium",
        )
        db.merge(team)
        db.commit()

        queried_team = db.query(DBTeam).filter_by(id="ARS").first()
        assert queried_team is not None
        assert queried_team.name == "Arsenal FC"
        assert queried_team.competition.name == "Premier League"
    finally:
        db.close()


def test_tool_registry_execution():
    async def _test():
        registry = ToolRegistry()

        def add_numbers(a: int, b: int) -> int:
            return a + b

        registry.register(
            name="add_numbers",
            description="Add two numbers together",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
            handler=add_numbers,
        )

        # Valid execution
        res = await registry.execute_tool("add_numbers", {"a": 10, "b": 25})
        assert res["success"] is True
        assert res["data"] == 35

        # Unregistered tool
        res_err = await registry.execute_tool("unregistered_tool", {})
        assert res_err["success"] is False
        assert res_err["status"] == "UNAUTHORIZED_TOOL"

    run_async(_test())


def test_grok_client_missing_key_fails_cleanly():
    async def _test():
        client = GrokClient(api_key="", mock_mode=False)
        with pytest.raises(GrokAPIError) as exc_info:
            await client.generate_response(messages=[{"role": "user", "content": "Hello"}])
        assert "XAI_API_KEY is not configured" in str(exc_info.value)

    run_async(_test())


def test_agent_executor_mock_and_tool_loop():
    async def _test():
        registry = ToolRegistry()

        def get_weather(city: str) -> str:
            return f"Sunny in {city}"

        registry.register(
            name="get_weather",
            description="Get weather for city",
            parameters={"type": "object", "properties": {"city": {"type": "string"}}},
            handler=get_weather,
        )

        client = GrokClient(api_key="mock-key", mock_mode=True)

        calls_count = 0

        def mock_grok(messages, tools):
            nonlocal calls_count
            calls_count += 1
            if calls_count == 1:
                return {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"city": "London"}',
                            },
                        }
                    ],
                    "finish_reason": "tool_calls",
                }
            else:
                return {
                    "role": "assistant",
                    "content": "In London, the weather is sunny.",
                    "tool_calls": None,
                    "finish_reason": "stop",
                }

        client.set_mock_handler(mock_grok)

        executor = AgentExecutor(grok_client=client, tool_registry=registry, max_rounds=5)
        res = await executor.run(system_prompt="Test system", user_message="What is the weather in London?")

        assert res.rounds_executed == 2
        assert "London, the weather is sunny" in res.final_response
        assert len(res.tool_records) == 1
        assert res.tool_records[0].tool_name == "get_weather"
        assert res.tool_records[0].result["data"] == "Sunny in London"

    run_async(_test())
