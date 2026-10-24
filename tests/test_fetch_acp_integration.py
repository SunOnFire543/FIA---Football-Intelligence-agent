"""Integration tests for Fetch.ai Agent Chat Protocol (ACP) and ASI:One."""

import asyncio
import pytest

from app.agent.grok_client import GrokClient
from app.fetch.acp_server import ACPMessageRequest, FootballACPAgent
from app.fetch.agent_manifest import get_agent_manifest


def test_agent_manifest_discoverability():
    manifest = get_agent_manifest()
    data = manifest.to_dict()

    assert data["name"] == "FootballIntelligenceAgent"
    assert "agent-chat-protocol/v1" in data["protocols"]
    assert "Premier League (PL)" in data["supported_competitions"]
    assert "Match Result (1X2)" in data["supported_markets"]
    assert "/acp/message" in data["endpoints"].values()


def test_acp_agent_e2e_conversation():
    # Test deterministic ACP handling of user request
    mock_grok = GrokClient(api_key="mock", mock_mode=True)
    agent = FootballACPAgent(grok_client=mock_grok)

    req = ACPMessageRequest(
        sender="asi_one_user_123",
        message="Analyse the next Arsenal match using historical statistics, compare current bookmaker odds, and generate a 5-leg and 10-leg parlay.",
        session_id="asi_session_abc",
    )

    resp = asyncio.run(agent.handle_message(req))

    assert resp.status == "SUCCESS"
    assert resp.session_id == "asi_session_abc"
    assert resp.evidence_record_id is not None
    assert "EVID_" in resp.evidence_record_id

    # Verify report sections
    text = resp.response
    assert "Match Intelligence Report: Arsenal FC vs Chelsea FC" in text
    assert "Data Coverage & Provenance" in text
    assert "Dixon-Coles Parameter" in text
    assert "Bookmaker Odds Comparison & Value Opportunities" in text
    assert "Parlay Intelligence Engine" in text
    assert "Parlay A: Five Legs" in text
    assert "Result Verification & Integrity Checks" in text
    assert "Responsible Gambling Advisory" in text
