"""Agent Chat Protocol (ACP) & ASI:One Integration Handler."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.agent.executor import AgentExecutor
from app.agent.groq_client import BaseLLMClient, GrokClient
from app.agent.planner import FOOTBALL_INTELLIGENCE_SYSTEM_PROMPT
from app.agent.response_builder import ResponseBuilder
from app.agent.tool_registry import ToolRegistry
from app.agent.tools import FootballIntelligenceTools, register_all_tools
from app.config.settings import settings
from app.fetch.agent_manifest import get_agent_manifest
from app.schemas.models import ParlayCandidate

logger = logging.getLogger(__name__)


class ACPMessageRequest(BaseModel):
    """Incoming ACP message payload."""
    sender: str
    message: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ACPMessageResponse(BaseModel):
    """Outgoing ACP response payload."""
    sender: str
    response: str
    session_id: Optional[str] = None
    status: str = "SUCCESS"
    evidence_record_id: Optional[str] = None


class FootballACPAgent:
    """Agent implementing Agent Chat Protocol for ASI:One and Agentverse."""

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        # Backwards compatibility alias
        grok_client: Optional[BaseLLMClient] = None,
    ):
        self.llm_client = llm_client or grok_client or GrokClient()
        self.grok_client = self.llm_client
        self.tool_registry = ToolRegistry()
        self.tools = FootballIntelligenceTools()
        register_all_tools(self.tool_registry, self.tools)
        self.executor = AgentExecutor(
            llm_client=self.llm_client,
            tool_registry=self.tool_registry,
            max_rounds=getattr(settings, "groq_max_tool_rounds", 8),
        )
        self.manifest = get_agent_manifest()

    def handle_message_sync(self, request: ACPMessageRequest) -> ACPMessageResponse:
        """Synchronous wrapper for handle_message."""
        user_query = request.message.strip()
        logger.info(f"Received ACP query (sync) from {request.sender}: '{user_query}'")

        # Deterministic analysis slice
        fixture_id = "FIX_ARS_CHE_2026"
        if "city" in user_query.lower() or "liverpool" in user_query.lower():
            fixture_id = "FIX_MCI_LIV_2026"
        elif "madrid" in user_query.lower() or "barcelona" in user_query.lower():
            fixture_id = "FIX_RMA_BAR_2026"

        coverage_data = self.tools.inspect_competition_coverage("PL")
        cov_record = None
        if "competition_id" in coverage_data:
            from app.schemas.models import CoverageRecord
            cov_record = CoverageRecord(**coverage_data)

        pred_data = self.tools.predict_match_markets(fixture_id)
        from app.schemas.models import MatchPredictionSummary
        pred_summary = MatchPredictionSummary(**pred_data) if "predictions" in pred_data else None

        val_opps_data = self.tools.calculate_expected_value(fixture_id)
        from app.schemas.models import ValueOpportunity
        val_opps = [ValueOpportunity(**v) for v in val_opps_data]

        parlay_data = self.tools.generate_parlay_candidates(fixture_id)
        p5 = ParlayCandidate(**parlay_data["parlay_5_leg"])
        p10 = ParlayCandidate(**parlay_data["parlay_10_leg"])

        ev_data = self.tools.verify_analysis(fixture_id)
        from app.schemas.models import CompactEvidenceRecord
        evidence = CompactEvidenceRecord(**ev_data)

        formatted_report = ResponseBuilder.format_match_analysis(
            fixture_label=f"{pred_summary.home_team} vs {pred_summary.away_team}" if pred_summary else fixture_id,
            coverage=cov_record,
            prediction=pred_summary,
            value_opps=val_opps,
            parlay_5=p5,
            parlay_10=p10,
            evidence=evidence,
        )

        return ACPMessageResponse(
            sender=self.manifest.name,
            response=formatted_report,
            session_id=request.session_id,
            status="SUCCESS",
            evidence_record_id=evidence.record_id if evidence else None,
        )

    async def handle_message(self, request: ACPMessageRequest) -> ACPMessageResponse:
        """Process an incoming ACP user query through Grok and analytical tools."""
        user_query = request.message.strip()
        logger.info(f"Received ACP query from {request.sender}: '{user_query}'")

        # If Grok is not configured with a live key, or in deterministic mode, execute the deterministic analysis slice
        if not self.grok_client.is_configured() or self.grok_client.mock_mode:
            # Deterministic vertical execution:
            fixture_id = "FIX_ARS_CHE_2026"
            if "city" in user_query.lower() or "liverpool" in user_query.lower():
                fixture_id = "FIX_MCI_LIV_2026"
            elif "madrid" in user_query.lower() or "barcelona" in user_query.lower():
                fixture_id = "FIX_RMA_BAR_2026"

            coverage_data = self.tools.inspect_competition_coverage("PL")
            cov_record = None
            if "competition_id" in coverage_data:
                from app.schemas.models import CoverageRecord
                cov_record = CoverageRecord(**coverage_data)

            pred_data = self.tools.predict_match_markets(fixture_id)
            from app.schemas.models import MatchPredictionSummary
            pred_summary = MatchPredictionSummary(**pred_data) if "predictions" in pred_data else None

            val_opps_data = self.tools.calculate_expected_value(fixture_id)
            from app.schemas.models import ValueOpportunity
            val_opps = [ValueOpportunity(**v) for v in val_opps_data]

            parlay_data = self.tools.generate_parlay_candidates(fixture_id)
            p5 = ParlayCandidate(**parlay_data["parlay_5_leg"])
            p10 = ParlayCandidate(**parlay_data["parlay_10_leg"])

            ev_data = self.tools.verify_analysis(fixture_id)
            from app.schemas.models import CompactEvidenceRecord
            evidence = CompactEvidenceRecord(**ev_data)

            formatted_report = ResponseBuilder.format_match_analysis(
                fixture_label=f"{pred_summary.home_team} vs {pred_summary.away_team}" if pred_summary else fixture_id,
                coverage=cov_record,
                prediction=pred_summary,
                value_opps=val_opps,
                parlay_5=p5,
                parlay_10=p10,
                evidence=evidence,
            )

            return ACPMessageResponse(
                sender=self.manifest.name,
                response=formatted_report,
                session_id=request.session_id,
                status="SUCCESS",
                evidence_record_id=evidence.record_id if evidence else None,
            )

        # Live Grok execution
        exec_res = await self.executor.run(
            system_prompt=FOOTBALL_INTELLIGENCE_SYSTEM_PROMPT,
            user_message=user_query,
        )

        return ACPMessageResponse(
            sender=self.manifest.name,
            response=exec_res.final_response,
            session_id=request.session_id,
            status="SUCCESS",
        )
