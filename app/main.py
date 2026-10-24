"""Main Application Entry Point and CLI for Football Intelligence Engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Optional

from app.agent.groq_client import GroqClient
from app.agent.planner import FOOTBALL_INTELLIGENCE_SYSTEM_PROMPT
from app.agent.response_builder import ResponseBuilder
from app.agent.tools import FootballIntelligenceTools
from app.config.settings import settings
from app.db.session import init_db
from app.fetch.acp_server import ACPMessageRequest, FootballACPAgent
from app.fetch.agent_manifest import get_agent_manifest
from app.fetch.uagent_service import create_football_uagent
from app.schemas.models import (
    CompactEvidenceRecord,
    CoverageRecord,
    MatchPredictionSummary,
    ParlayCandidate,
    ValueOpportunity,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("football_intelligence")


def run_analysis_workflow(query: str, data_mode: Optional[str] = None) -> None:
    """Execute complete end-to-end analytical workflow for a match query."""
    mode = (data_mode or settings.data_mode).upper()
    is_live = (mode == "LIVE")

    print(f"\n[+] Initializing Football Intelligence Engine...")
    print(f"[+] Application Operating Mode: {mode} ({'LIVE Production' if is_live else 'DEMO Simulated Test Data'})")
    print(f"[+] LLM Provider: Groq ({settings.groq_model}) | API Key: {settings.get_masked_api_key('groq_api_key')}")
    print(f"[+] Football Data Provider: {settings.football_data_provider}")
    print(f"[+] Odds Provider: {settings.odds_provider}")
    print(f"[+] User Query: \"{query}\"\n")

    init_db()
    tools = FootballIntelligenceTools()

    # In LIVE mode, strictly verify provider configuration
    if is_live:
        if not tools.data_provider.is_configured():
            print("[-] LIVE MODE ERROR: Football data provider credentials are not configured.")
            print("    Please set FOOTBALL_DATA_API_KEY or API_FOOTBALL_KEY in your .env file.")
            print("    The Football Intelligence Engine strictly refuses to fabricate fallback data.")
            return

    # 1. Resolve fixture
    print("[1/6] Resolving fixture...")
    fixtures = tools.resolve_fixture(query)
    if not fixtures:
        print("[-] Could not resolve fixture for query.")
        return
    target_fixture = fixtures[0]
    fixture_id = target_fixture["fixture_id"]
    fixture_label = f"{target_fixture['home_team_name']} vs {target_fixture['away_team_name']}"
    print(f"      Resolved: {fixture_label} (ID: {fixture_id})")

    # 2. Check coverage
    print("[2/6] Inspecting data coverage & depth...")
    coverage_data = tools.inspect_competition_coverage(target_fixture["competition_id"])
    coverage = CoverageRecord(**coverage_data) if "competition_id" in coverage_data else None
    status_label = coverage.status.value if coverage else 'UNKNOWN'
    print(f"      Status: {status_label} | Telemetry: Lineups, SOT, Cards, Fouls")

    # 3. Statistical modeling (Poisson & Dixon-Coles)
    print("[3/6] Fitting Dixon-Coles bivariate goal model & player props...")
    pred_data = tools.predict_match_markets(fixture_id)
    pred_summary = MatchPredictionSummary(**pred_data)
    print(f"      Expected Goals: {pred_summary.home_team} {pred_summary.lambda_home:.2f} - {pred_summary.mu_away:.2f} {pred_summary.away_team}")

    # 4. Bookmaker odds & Expected Value
    print(f"[4/6] Comparing multi-bookmaker odds & calculating Expected Value (EV)...")
    opps_data = tools.calculate_expected_value(fixture_id)
    opps = [ValueOpportunity(**o) for o in opps_data]
    pos_ev_count = sum(1 for o in opps if o.is_positive_ev)
    print(f"      Found {len(opps)} comparable selections ({pos_ev_count} positive EV opportunities)")

    # 5. Parlay intelligence (5-leg and 10-leg)
    print("[5/6] Generating 5-leg and 10-leg parlay candidates with joint probability modeling...")
    parlay_data = tools.generate_parlay_candidates(fixture_id)
    p5 = ParlayCandidate(**parlay_data["parlay_5_leg"])
    p10 = ParlayCandidate(**parlay_data["parlay_10_leg"])
    print(f"      5-Leg Candidate: {'Recommended (Joint Prob: ' + str(round(p5.joint_probability*100, 1)) + '%)' if p5.is_recommended else 'Abstained'}")
    print(f"      10-Leg Candidate: {'Recommended (Joint Prob: ' + str(round(p10.joint_probability*100, 2)) + '%)' if p10.is_recommended else 'Abstained'}")

    # 6. Verification & synthesis
    print("[6/6] Verifying calculations, web intelligence & auditing provenance record...")
    ev_data = tools.verify_analysis(fixture_id)
    evidence = CompactEvidenceRecord(**ev_data)
    print(f"      Audit Passed: {evidence.verification_passed} (Record: {evidence.record_id})")
    if evidence.web_sources:
        print(f"      Web Intelligence: {len(evidence.web_sources)} grounded sources verified ({len(evidence.research_records)} research record(s))")

    # Format output with explicit data_mode
    report = ResponseBuilder.format_match_analysis(
        fixture_label=fixture_label,
        coverage=coverage,
        prediction=pred_summary,
        value_opps=opps,
        parlay_5=p5,
        parlay_10=p10,
        evidence=evidence,
        data_mode=mode,
    )

    print("\n" + "=" * 80)
    print(report)
    print("=" * 80 + "\n")


def run_evaluation(competition_id: str = "PL") -> None:
    """Execute chronological backtesting."""
    print(f"\n[+] Running chronological walk-forward backtest for {competition_id}...")
    tools = FootballIntelligenceTools()
    summary = tools.get_model_evaluation(competition_id)
    print("\n" + "=" * 50)
    print(f"Walk-Forward Evaluation Summary ({competition_id})")
    print("=" * 50)
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("=" * 50 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Football Intelligence Engine CLI")
    parser.add_argument("--mode", type=str, choices=["DEMO", "LIVE"], default=None, help="Application data mode")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze match fixture")
    analyze_parser.add_argument("query", type=str, default="Arsenal", nargs="?", help="Fixture or team query")

    # Evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Run chronological model evaluation")
    eval_parser.add_argument("--competition", type=str, default="PL", help="Competition code")

    # Manifest
    subparsers.add_parser("manifest", help="Print ASI:One discoverability manifest")

    # ACP message simulation
    acp_parser = subparsers.add_parser("acp-query", help="Simulate incoming ACP message from ASI:One")
    acp_parser.add_argument("message", type=str, help="Message text")

    # Run uAgent
    subparsers.add_parser("run-uagent", help="Instantiate and run the official Fetch.ai uAgent")

    args = parser.parse_args()
    data_mode = args.mode or settings.data_mode

    if args.command == "analyze" or args.command is None:
        query = getattr(args, "query", "Arsenal") or "Arsenal"
        run_analysis_workflow(query, data_mode=data_mode)
    elif args.command == "evaluate":
        run_evaluation(args.competition)
    elif args.command == "manifest":
        manifest = get_agent_manifest()
        print(json.dumps(manifest.to_dict(), indent=2))
    elif args.command == "acp-query":
        agent = FootballACPAgent()
        req = ACPMessageRequest(sender="local_simulation_user", message=args.message, session_id="session_001")
        resp = agent.handle_message_sync(req)
        print(f"\nACP Status: {resp.status}")
        print(f"Sender: {resp.sender}")
        print(resp.response)
    elif args.command == "run-uagent":
        print(f"[+] Starting uAgents runtime for {settings.agent_name}...")
        try:
            uagent = create_football_uagent()
        except ValueError as exc:
            print(f"[-] ERROR: {exc}")
            return
        print(f"[+] uAgent instantiated with address: {uagent.address}")
        print(f"[+] Registered protocols: {[p.name for p in uagent.protocols.values()]}")
        print("[+] Starting agent event loop (press Ctrl+C to stop)...")
        uagent.run()


if __name__ == "__main__":
    main()
