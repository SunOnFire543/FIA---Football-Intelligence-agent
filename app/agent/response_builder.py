"""Response Builder for Formatting Evidence-Backed Football Reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.config.settings import settings
from app.schemas.models import (
    MatchPredictionSummary,
    ValueOpportunity,
    ParlayCandidate,
    CoverageRecord,
    CompactEvidenceRecord,
    WebResearchRecord,
    WebSourceEvidence,
)


class ResponseBuilder:
    """Formats verified analytics, odds, EV, and parlays into clear markdown summaries."""

    @staticmethod
    def format_match_analysis(
        fixture_label: str,
        coverage: Optional[CoverageRecord],
        prediction: Optional[MatchPredictionSummary],
        value_opps: List[ValueOpportunity],
        parlay_5: Optional[ParlayCandidate],
        parlay_10: Optional[ParlayCandidate],
        evidence: Optional[CompactEvidenceRecord],
        data_mode: Optional[str] = None,
        web_sources: Optional[List[WebSourceEvidence]] = None,
        web_research: Optional[WebResearchRecord] = None,
    ) -> str:
        mode = (data_mode or settings.data_mode).upper()
        is_demo = (mode == "DEMO")

        lines: List[str] = []
        mode_badge = "[DATA MODE: DEMO (SIMULATED)]" if is_demo else "[DATA MODE: LIVE]"
        lines.append(f"# Match Intelligence Report: {fixture_label} {mode_badge}\n")

        # Conspicuous Notice for DEMO Mode
        if is_demo:
            lines.append(
                "> [!WARNING]\n"
                "> **DEMO / SIMULATION MODE NOTICE**:\n"
                "> - Fixtures, event histories, and bookmaker odds in this report are **simulated test data**.\n"
                "> - Simulated prices do NOT represent confirmed executable bookmaker odds.\n"
                "> - This test run does NOT prove 5 years of verified live historical coverage.\n"
                "> - Expected values (EV) and accumulator returns represent synthetic scenarios and must **NEVER** "
                "> be interpreted as evidence of real-world profitability or financial advice.\n"
            )

        # 1. Coverage & Data Freshness
        lines.append("## 1. Data Coverage & Provenance")
        if coverage:
            provenance_tag = "Simulated Local Test Dataset" if is_demo else f"Verified Live Feed ({coverage.provider})"
            lines.append(f"- **Data Mode**: `{mode}` ({provenance_tag})")
            lines.append(f"- **Competition**: {coverage.competition_name} ({coverage.season})")
            lines.append(f"- **Coverage Status**: `{coverage.status.value}`")
            lines.append(f"- **Provider**: {coverage.provider}")
            lines.append(f"- **Telemetry**: Lineups: {'Yes' if coverage.has_lineups else 'No'} | Shots/SOT: {'Yes' if coverage.has_shots_and_sot else 'No'} | Cards/Fouls: {'Yes' if coverage.has_cards_and_fouls else 'No'} | xG: {'Yes' if coverage.has_xg else 'No'}")
            if is_demo:
                lines.append("- **Coverage Note**: Simulated multi-season fixture depth for test verification.")
        else:
            lines.append("- Coverage data: Not available.")
        lines.append("")

        # 2. Statistical Probabilities
        lines.append("## 2. Statistical Model Predictions (Poisson + Dixon-Coles)")
        if prediction:
            lines.append(f"- **Expected Goals**: {prediction.home_team} **{prediction.lambda_home:.2f}** - **{prediction.mu_away:.2f}** {prediction.away_team}")
            lines.append(f"- **Dixon-Coles Parameter ($\\rho$)**: `{prediction.rho_dixon_coles:.3f}` *(Provisional literature baseline; empirical estimation requires >=30 matched season games)*")
            lines.append(f"- **Model Status**: `{prediction.model_status.value}`")
            lines.append("\n### Key Market Probabilities:")
            lines.append("| Market | Selection | Threshold | Model Probability | Implied Fair Odds | Status |")
            lines.append("| :--- | :--- | :--- | :---: | :---: | :--- |")
            for p in prediction.predictions:
                fair_odds = f"{1.0 / p.estimated_probability:.2f}" if p.estimated_probability > 0 else "N/A"
                thresh_str = f"{p.threshold:.1f}" if p.threshold is not None else "-"
                lines.append(
                    f"| {p.market.value} | {p.selection} | {thresh_str} | **{p.estimated_probability * 100:.1f}%** | {fair_odds} | `{p.model_status.value}` |"
                )
        else:
            lines.append("- Prediction models: Insufficient historical data.")
        lines.append("")

        # 3. Odds Comparison & Expected Value
        price_header = "Best Simulated Odds" if is_demo else "Best Verified Odds"
        lines.append(f"## 3. Bookmaker Odds Comparison & Value Opportunities ({'Simulated Lines' if is_demo else 'Live Lines'})")
        if value_opps:
            lines.append(f"| Selection | {price_header} | Bookmaker | Model Prob | Expected Value (EV) | Value Status |")
            lines.append("| :--- | :---: | :--- | :---: | :---: | :--- |")
            for vo in value_opps:
                ev_pct = f"{vo.expected_value * 100:+.1f}%"
                val_status = "**Positive EV**" if vo.is_positive_ev else "Negative EV"
                sim_tag = " (Simulated)" if is_demo else ""
                lines.append(
                    f"| {vo.selection} {f'({vo.threshold})' if vo.threshold else ''} | **{vo.best_odds:.2f}**{sim_tag} | {vo.bookmaker} | {vo.model_probability*100:.1f}% | {ev_pct} | {val_status} |"
                )
        else:
            lines.append("- No verified bookmaker odds found or no qualifying value selections.")
        lines.append("")

        # 4. Parlay Candidates
        lines.append("## 4. Parlay Intelligence Engine")

        # 5-leg parlay
        lines.append(f"### Parlay A: Five Legs ({'Simulated Candidate' if is_demo else 'Live Candidate'})")
        if parlay_5 and parlay_5.is_recommended:
            quote_desc = "Simulated Theoretical Product" if is_demo else ("Verified Single-Bookmaker Slip" if parlay_5.is_quote_verified else "Theoretical Product Estimate")
            lines.append(f"- **Structure**: {parlay_5.parlay_type.value} ({parlay_5.leg_count} Legs)")
            lines.append(f"- **Combined Odds**: **{parlay_5.combined_odds:.2f}** ({quote_desc})")
            lines.append(f"- **Joint Win Probability**: **{parlay_5.joint_probability * 100:.2f}%** *(Joint score matrix summation)*")
            if parlay_5.expected_value is not None:
                lines.append(f"- **Combined Expected Value**: **{parlay_5.expected_value * 100:+.1f}%**")
            lines.append(f"- **Reference Bookmaker**: {parlay_5.quote_bookmaker}")
            lines.append("\n**Leg Details:**")
            for leg in parlay_5.legs:
                price_str = f"@{leg.best_individual_odds:.2f}" if leg.best_individual_odds else ""
                lines.append(f"  {leg.leg_index}. {leg.fixture_label}: **{leg.selection}** {f'({leg.threshold})' if leg.threshold else ''} (Prob: {leg.leg_win_probability*100:.1f}%) {price_str} - {leg.evidence_notes}")
        else:
            reason = parlay_5.abstention_reason if parlay_5 else "Insufficient qualifying selections."
            lines.append(f"> [!NOTE]\n> **Abstained from 5-leg parlay**: {reason}\n")

        lines.append("")

        # 10-leg parlay
        lines.append(f"### Parlay B: Ten Legs ({'Simulated Multi-Match Accumulator' if is_demo else 'Live Multi-Match Candidate'})")
        if parlay_10 and parlay_10.is_recommended:
            quote_desc = "Simulated Theoretical Product" if is_demo else ("Verified Single-Bookmaker Slip" if parlay_10.is_quote_verified else "Theoretical Product Estimate")
            lines.append(f"- **Structure**: {parlay_10.parlay_type.value} ({parlay_10.leg_count} Legs)")
            lines.append(f"- **Combined Odds**: **{parlay_10.combined_odds:.2f}** ({quote_desc})")
            lines.append(f"- **Joint Win Probability**: **{parlay_10.joint_probability * 100:.2f}%**")
            if parlay_10.expected_value is not None:
                lines.append(f"- **Combined Expected Value**: **{parlay_10.expected_value * 100:+.1f}%**")
            lines.append(f"- **Reference Bookmaker**: {parlay_10.quote_bookmaker}")
            lines.append("\n**Leg Details:**")
            for leg in parlay_10.legs:
                price_str = f"@{leg.best_individual_odds:.2f}" if leg.best_individual_odds else ""
                lines.append(f"  {leg.leg_index}. {leg.fixture_label}: **{leg.selection}** {f'({leg.threshold})' if leg.threshold else ''} (Prob: {leg.leg_win_probability*100:.1f}%) {price_str} - {leg.evidence_notes}")
        else:
            reason = parlay_10.abstention_reason if parlay_10 else "Insufficient qualifying selections."
            lines.append(f"> [!NOTE]\n> **Abstained from 10-leg parlay**: {reason}\n")

        # 5. Web Intelligence, Team News & Grounded Sources
        sources_to_show = web_sources or (evidence.web_sources if evidence else [])
        research_rec = web_research or (evidence.research_records[0] if evidence and evidence.research_records else None)

        if sources_to_show or research_rec:
            grounding_tag = "Simulated Grounding" if is_demo else "Verified Live Citations"
            lines.append(f"## 5. Web Intelligence, Team News & Grounded Sources ({grounding_tag})")
            if is_demo:
                lines.append(
                    "> [!NOTE]\n"
                    "> **DEMO GROUNDING NOTICE**: Web research references below represent synthetic test fixtures "
                    "for deterministic offline evaluation. In LIVE mode, citations and URLs are extracted in real-time "
                    "from Groq API browser_search results.\n"
                )
            if research_rec and research_rec.summary:
                lines.append(f"**Grounded Context Summary**: {research_rec.summary}\n")
            if research_rec and research_rec.material_conflicts:
                for conf in research_rec.material_conflicts:
                    lines.append(f"> [!NOTE]\n> **Disputed / Conflicting Reports Detected**: {conf}\n")

            if sources_to_show:
                lines.append("| Ref | Source / Domain | Category | Verification | Supported Claim | Freshness |")
                lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
                for s in sources_to_show:
                    ref_tag = s.inline_reference_id or "-"
                    link_text = f"[{s.publisher or s.domain}]({s.url})"
                    fresh_text = s.freshness_warning or "Current"
                    lines.append(
                        f"| {ref_tag} | {link_text} | `{s.category.value}` | `{s.verification_status.value}` | {s.claim_supported} | {fresh_text} |"
                    )
            lines.append("")

        # 6. Verification & Audit Trail
        section_num = "6" if (sources_to_show or research_rec) else "5"
        lines.append(f"\n## {section_num}. Result Verification & Integrity Checks")
        if evidence:
            lines.append(f"- **Audit Record ID**: `{evidence.record_id}`")
            lines.append(f"- **Data Mode**: `{mode}`")
            lines.append(f"- **Data Cutoff**: {evidence.data_cutoff_timestamp.isoformat()} (strictly prevents future-data leakage)")
            lines.append(f"- **Verification Status**: `{'PASSED' if evidence.verification_passed else 'FAILED'}`")
            if evidence.verification_warnings:
                for w in evidence.verification_warnings:
                    lines.append(f"  - Warning: {w}")
        lines.append("")

        # 6. Responsible Gambling
        lines.append("---")
        lines.append(
            "> [!IMPORTANT]\n"
            "> **Responsible Gambling Advisory**: Probabilities and expected values are generated using statistical models "
            "> based on historical data. Sports outcomes inherently contain stochastic variance. Never risk money you cannot "
            "> afford to lose. No prediction is guaranteed."
        )

        return "\n".join(lines)
