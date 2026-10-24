"""Unit and integration tests for Grok Web Intelligence, Source Discovery, and Grounding."""

import asyncio
from datetime import datetime, timezone, timedelta
import pytest

from app.agent.grok_client import GrokClient
from app.agent.executor import AgentExecutor
from app.agent.tool_registry import ToolRegistry
from app.agent.web_research import (
    SourceClassifier,
    WebResearchPolicy,
    WebEvidenceBuilder,
    WebResearchEngine,
)
from app.agent.tools import FootballIntelligenceTools
from app.schemas.enums import SourceCategory, VerificationStatus
from app.schemas.models import (
    CompactEvidenceRecord,
    MatchPredictionSummary,
    SelectionPrediction,
    WebSourceEvidence,
    WebResearchRecord,
)
from app.schemas.enums import MarketType, ModelStatus
from app.verification.result_validator import ResultValidator


def test_source_classifier_hierarchy():
    """Verify source categorization respects the evidentiary hierarchy."""
    # Official announcements (Tier 1)
    cat_prem, stat_prem, w_prem = SourceClassifier.classify("https://www.premierleague.com/news/123")
    assert cat_prem == SourceCategory.OFFICIAL_ANNOUNCEMENT
    assert stat_prem == VerificationStatus.CONFIRMED
    assert w_prem == 1.0

    cat_ars, stat_ars, w_ars = SourceClassifier.classify("https://www.arsenal.com/team-news")
    assert cat_ars == SourceCategory.OFFICIAL_ANNOUNCEMENT
    assert stat_ars == VerificationStatus.CONFIRMED

    # Licensed statistical providers (Tier 1 for stats)
    cat_fd, stat_fd, w_fd = SourceClassifier.classify("https://api.football-data.org/v4/matches")
    assert cat_fd == SourceCategory.LICENSED_DATA
    assert stat_fd == VerificationStatus.CONFIRMED
    assert w_fd == 0.95

    # Established reputable publications (Tier 2)
    cat_ath, stat_ath, w_ath = SourceClassifier.classify("https://theathletic.com/football/tactics")
    assert cat_ath == SourceCategory.ESTABLISHED_DATABASE
    assert stat_ath == VerificationStatus.REPORTED
    assert w_ath == 0.85

    cat_bbc, _, _ = SourceClassifier.classify("https://www.bbc.co.uk/sport/football")
    assert cat_bbc == SourceCategory.ESTABLISHED_DATABASE

    # Unverified community / social (Tier 4 / requires corroboration)
    cat_x, stat_x, w_x = SourceClassifier.classify("https://twitter.com/fan_account/status/123")
    assert cat_x == SourceCategory.UNVERIFIED_COMMUNITY
    assert stat_x == VerificationStatus.UNVERIFIED
    assert w_x == 0.30


def test_web_research_policy_selective_decision():
    """Verify selective web search decision suppresses redundant queries and triggers on team news."""
    # 1. Pure odds / EV calculation query where structured data is available
    should_search, reason, _ = WebResearchPolicy.should_research(
        query="Compare bookmaker odds and calculate EV for Arsenal",
        has_structured_odds=True,
    )
    assert should_search is False
    assert "redundant" in reason.lower()

    # 2. Team news / injury query
    should_search, reason, topics = WebResearchPolicy.should_research(
        query="Is Bukayo Saka fit to start against Chelsea? Any injury doubts?",
        has_structured_odds=True,
    )
    assert should_search is True
    assert "injuries_and_fitness" in topics or "lineup_confirmation" in topics

    # 3. Match analysis query
    should_search, reason, topics = WebResearchPolicy.should_research(
        query="Analyse Arsenal vs Chelsea fixture context",
    )
    assert should_search is True
    assert len(topics) >= 1


def test_web_evidence_freshness_audit():
    """Verify that reports older than 48 hours receive a freshness notice."""
    now = datetime.now(timezone.utc)

    # Fresh evidence (5 hours old)
    fresh_ev = WebEvidenceBuilder.create_evidence(
        url="https://www.arsenal.com/news/late-fitness-update",
        claim_supported="Player confirmed in starting XI",
        published_at=now - timedelta(hours=5),
    )
    assert fresh_ev.freshness_warning is None
    assert fresh_ev.domain == "arsenal.com"
    assert fresh_ev.category == SourceCategory.OFFICIAL_ANNOUNCEMENT

    # Stale evidence (72 hours old)
    stale_ev = WebEvidenceBuilder.create_evidence(
        url="https://theathletic.com/football/pre-match-report",
        claim_supported="Player carrying knock from last weekend",
        published_at=now - timedelta(hours=72),
    )
    assert stale_ev.freshness_warning is not None
    assert "72 hours ago" in stale_ev.freshness_warning


def test_groq_server_vs_client_tools_discrimination():
    """Verify discrimination between server-side browser_search and client-side custom function calls."""
    client = GrokClient(api_key="gsk_mock_key", mock_mode=True)

    # Mock a Groq API response returning BOTH server-side browser search activity AND a custom function call
    def mock_responses_with_search(messages, tools):
        return {
            "role": "assistant",
            "content": "Based on official club reporting [[1]](https://www.arsenal.com/news/team-news), Bukayo Saka is available.",
            "tool_calls": [
                {
                    "id": "call_local_001",
                    "type": "function",
                    "function": {
                        "name": "predict_match_markets",
                        "arguments": '{"fixture_id": "FIX_ARS_CHE_2026"}',
                    },
                }
            ],
            "executed_tools": [
                {
                    "name": "browser.search",
                    "type": "browser_search",
                    "id": "ws_call_server_999",
                    "arguments": '{"query": "Arsenal vs Chelsea injury news Bukayo Saka"}',
                    "search_results": {
                        "results": [
                            {"title": "Arsenal FC Team News", "url": "https://www.arsenal.com/news/team-news"},
                            {"title": "Premier League Bulletin", "url": "https://www.premierleague.com/news/official-bulletin"},
                        ]
                    },
                }
            ],
            "citations": [
                "https://www.arsenal.com/news/team-news",
                "https://www.premierleague.com/news/official-bulletin",
            ],
            "finish_reason": "tool_calls",
            "response_id": "resp_search_001",
        }

    client.set_mock_handler(mock_responses_with_search)

    # 1. Verify GroqClient returns segregated tool_calls and citations
    resp = asyncio.run(
        client.generate_response(
            messages=[{"role": "user", "content": "Check Saka fitness and predict match"}],
            enable_web_search=True,
        )
    )

    assert resp["tool_calls"] is not None
    assert len(resp["tool_calls"]) == 1
    assert resp["tool_calls"][0]["function"]["name"] == "predict_match_markets"

    # Server-side browser search events must NOT be in tool_calls
    call_names = [c["function"]["name"] for c in resp["tool_calls"]]
    assert "browser_search" not in call_names
    assert "browser.search" not in call_names
    assert resp["executed_tools"] is not None
    assert len(resp["citations"]) == 2
    assert "https://www.arsenal.com/news/team-news" in resp["citations"]

    # 2. Verify AgentExecutor dispatches ONLY local functions and records citations
    registry = ToolRegistry()
    tools = FootballIntelligenceTools()
    registry.register(
        name="predict_match_markets",
        description="Predict match",
        parameters={"type": "object", "properties": {"fixture_id": {"type": "string"}}},
        handler=tools.predict_match_markets,
    )

    # In round 2, Groq will finish
    round_count = 0

    def mock_multi_round(messages, tool_schemas):
        nonlocal round_count
        round_count += 1
        if round_count == 1:
            return mock_responses_with_search(messages, tool_schemas)
        return {
            "role": "assistant",
            "content": "Analysis complete with verified web sources.",
            "tool_calls": None,
            "citations": ["https://www.arsenal.com/news/team-news"],
            "finish_reason": "stop",
            "response_id": "resp_search_002",
        }

    client.set_mock_handler(mock_multi_round)
    executor = AgentExecutor(llm_client=client, tool_registry=registry, max_rounds=3)

    exec_res = asyncio.run(executor.run(
        system_prompt="System prompt",
        user_message="Check Saka fitness and predict Arsenal match",
    ))

    # Assertions on execution result
    assert "Analysis complete with verified web sources." in exec_res.final_response
    assert len(exec_res.tool_records) == 1
    assert exec_res.tool_records[0].tool_name == "predict_match_markets"
    assert len(exec_res.citations) >= 2
    assert len(exec_res.web_sources) >= 2
    assert exec_res.web_sources[0].domain == "arsenal.com"
    assert exec_res.web_sources[0].category == SourceCategory.OFFICIAL_ANNOUNCEMENT


def test_conflict_detection_and_reporting():
    """Verify that contradictory reports are flagged in WebResearchRecord."""
    rec = WebResearchEngine.get_grounded_research(
        fixture_id="FIX_ARS_CHE_2026",
        home_team="Arsenal FC",
        away_team="Chelsea FC",
        data_mode="DEMO",
    )
    assert len(rec.sources) >= 4
    assert len(rec.material_conflicts) >= 1
    assert "hamstring" in rec.material_conflicts[0].lower()
    assert "Bukayo Saka" in rec.summary


def test_compact_evidence_record_with_web_sources_validation():
    """Verify ResultValidator audits web sources and enforces URL validity."""
    now = datetime.now(timezone.utc)
    valid_source = WebEvidenceBuilder.create_evidence(
        url="https://www.premierleague.com/news/101",
        claim_supported="Lineups confirmed 60 minutes prior to kickoff",
    )

    # Valid evidence record
    rec_valid = ResultValidator.verify_analysis(
        fixture_id="FIX_ARS_CHE_2026",
        competition_id="PL",
        prediction=None,
        value_opps=[],
        parlay_5=None,
        parlay_10=None,
        data_cutoff=now,
        web_sources=[valid_source],
    )
    assert rec_valid.verification_passed is True
    assert len(rec_valid.web_sources) == 1
    assert rec_valid.web_sources[0].domain == "premierleague.com"

    # Invalid URL rejected by validator
    invalid_source = WebSourceEvidence(
        url="ftp://invalid-protocol.com/data",
        domain="invalid-protocol.com",
        claim_supported="Some claim",
        category=SourceCategory.SECONDARY_REPORTING,
        verification_status=VerificationStatus.REPORTED,
    )
    rec_invalid = ResultValidator.verify_analysis(
        fixture_id="FIX_ARS_CHE_2026",
        competition_id="PL",
        prediction=None,
        value_opps=[],
        parlay_5=None,
        parlay_10=None,
        data_cutoff=now,
        web_sources=[invalid_source],
    )
    assert rec_invalid.verification_passed is False
    assert any("Invalid web source URL" in w for w in rec_invalid.verification_warnings)


def test_allowlisted_tool_research_match_context():
    """Verify tool 18 (research_match_context) executes and returns typed research."""
    tools = FootballIntelligenceTools()
    res = tools.research_match_context("FIX_ARS_CHE_2026")

    assert "query" in res
    assert "sources" in res
    assert len(res["sources"]) >= 4
    assert any("premierleague.com" in s["url"] for s in res["sources"])
    assert any(s["category"] == SourceCategory.OFFICIAL_ANNOUNCEMENT.value for s in res["sources"])
    assert "summary" in res
    assert len(res["summary"]) > 20
