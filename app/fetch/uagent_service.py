"""uAgents Framework Native Integration for Football Intelligence Agent.

Implements official Fetch.ai uAgents runtime with the official Agent Chat Protocol
(AgentChatProtocol:0.3.0 from uagents_core.contrib.protocols.chat) for ASI:One compatibility.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from app.agent.response_builder import ResponseBuilder
from app.agent.tools import FootballIntelligenceTools
from app.config.settings import settings
from app.schemas.models import (
    CompactEvidenceRecord,
    CoverageRecord,
    MatchPredictionSummary,
    ParlayCandidate,
    ValueOpportunity,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Internal Pipeline Result Schema
# -----------------------------------------------------------------------------

class FootballAnalysisResult(Model):
    """Result container for pipeline execution."""
    report: str
    status: str = "SUCCESS"
    session_id: str = ""
    evidence_record_id: Optional[str] = None
    data_mode: str = "DEMO"


# -----------------------------------------------------------------------------
# Deterministic Analysis Pipeline Execution
# -----------------------------------------------------------------------------

def execute_pipeline_for_query(query: str, data_mode: Optional[str] = None) -> FootballAnalysisResult:
    """Execute the core deterministic analysis pipeline for a query."""
    mode = (data_mode or settings.data_mode).upper()
    tools = FootballIntelligenceTools()

    # In LIVE mode, verify provider configuration
    if mode == "LIVE":
        if not tools.data_provider.is_configured():
            return FootballAnalysisResult(
                report=(
                    "# Football Intelligence Engine [DATA MODE: LIVE]\n\n"
                    "> [!WARNING]\n"
                    "> **Live Data Provider Unconfigured**: LIVE mode requires active provider credentials "
                    "(`FOOTBALL_DATA_API_KEY` or `API_FOOTBALL_KEY`). "
                    "The system strictly refuses to disguise simulated data as live data."
                ),
                status="UNCONFIGURED_PROVIDER",
                data_mode="LIVE",
            )

    # Resolve fixture
    fixture_id = "FIX_ARS_CHE_2026"
    q_lower = query.lower()
    if "city" in q_lower or "liverpool" in q_lower:
        fixture_id = "FIX_MCI_LIV_2026"
    elif "madrid" in q_lower or "barcelona" in q_lower:
        fixture_id = "FIX_RMA_BAR_2026"

    coverage_data = tools.inspect_competition_coverage("PL")
    cov_record = CoverageRecord(**coverage_data) if "competition_id" in coverage_data else None

    pred_data = tools.predict_match_markets(fixture_id)
    pred_summary = MatchPredictionSummary(**pred_data) if "predictions" in pred_data else None

    val_opps_data = tools.calculate_expected_value(fixture_id)
    val_opps = [ValueOpportunity(**v) for v in val_opps_data]

    parlay_data = tools.generate_parlay_candidates(fixture_id)
    p5 = ParlayCandidate(**parlay_data["parlay_5_leg"])
    p10 = ParlayCandidate(**parlay_data["parlay_10_leg"])

    ev_data = tools.verify_analysis(fixture_id)
    evidence = CompactEvidenceRecord(**ev_data)

    formatted_report = ResponseBuilder.format_match_analysis(
        fixture_label=f"{pred_summary.home_team} vs {pred_summary.away_team}" if pred_summary else fixture_id,
        coverage=cov_record,
        prediction=pred_summary,
        value_opps=val_opps,
        parlay_5=p5,
        parlay_10=p10,
        evidence=evidence,
        data_mode=mode,
    )

    return FootballAnalysisResult(
        report=formatted_report,
        status="SUCCESS",
        evidence_record_id=evidence.record_id if evidence else None,
        data_mode=mode,
    )


# -----------------------------------------------------------------------------
# Official AgentChatProtocol Definition (Spec: AgentChatProtocol:0.3.0)
# -----------------------------------------------------------------------------

official_chat_protocol = Protocol(spec=chat_protocol_spec)


@official_chat_protocol.on_message(ChatMessage)
async def handle_official_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming official ChatMessage from ASI:One or Agentverse peer."""
    text_query = msg.text() if callable(getattr(msg, "text", None)) else str(msg.content)
    ctx.logger.info(f"AgentChatProtocol received query from {sender}: '{text_query}'")

    # 1. Send immediate official acknowledgment
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    # 2. Execute analysis pipeline
    analysis = execute_pipeline_for_query(text_query, settings.data_mode)

    # 3. Send official ChatMessage response
    response_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid.uuid4(),
        content=[TextContent(type="text", text=analysis.report)],
    )
    await ctx.send(sender, response_msg)


@official_chat_protocol.on_message(ChatAcknowledgement)
async def handle_official_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle receipt of chat acknowledgment."""
    ctx.logger.info(f"Chat message acknowledged by {sender}: {msg.acknowledged_msg_id}")


# -----------------------------------------------------------------------------
# Agent Factory
# -----------------------------------------------------------------------------

INSECURE_SEEDS = {
    "football_intelligence_seed_phrase",
    "football_intelligence_engine_seed_phrase_here",
    "your_seed_phrase_here",
    "your_agent_seed_here",
}


def create_football_uagent(
    name: Optional[str] = None,
    seed: Optional[str] = None,
    port: Optional[int] = None,
    endpoint: Optional[str] = None,
    mailbox: Optional[str] = None,
) -> Agent:
    """Instantiate and configure the official uAgents Agent with AgentChatProtocol."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    agent_name = name or settings.agent_name
    agent_seed = seed if seed is not None else settings.agent_seed

    if not agent_seed or not str(agent_seed).strip() or str(agent_seed).strip() in INSECURE_SEEDS:
        raise ValueError(
            "Agent launch refused: AGENT_SEED is missing, unset, or set to an insecure default. "
            "Please securely configure AGENT_SEED in your .env file before launching the uAgent."
        )

    agent_port = port or settings.agent_port

    use_mailbox = bool(mailbox or settings.agentverse_api_key)
    # When mailbox is active and no explicit endpoint is provided, do not pass endpoint
    # so uagents correctly configures the Agentverse mailbox submit endpoint.
    configured_endpoint = None
    if endpoint:
        configured_endpoint = [endpoint]
    elif not use_mailbox and settings.agent_endpoint:
        configured_endpoint = [settings.agent_endpoint]

    agent = Agent(
        name=agent_name,
        seed=agent_seed,
        port=agent_port,
        endpoint=configured_endpoint,
        mailbox=use_mailbox,
        loop=loop,
    )

    # Include the official AgentChatProtocol
    agent.include(official_chat_protocol, publish_manifest=True)
    return agent
