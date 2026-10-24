"""Response Builder for Formatting Evidence-Backed Football Reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.schemas.models import (
    MatchPredictionSummary,
    ValueOpportunity,
    ParlayCandidate,
    CoverageRecord,
    CompactEvidenceRecord,
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
    ) -> str:
        lines: List[str] = []
        lines.append(f"# Match Intelligence Report: {fixture_label}\n")

        # 1. Coverage & Data Freshness
        lines.append("## 1. Data Coverage & Provenance")
        if coverage:
            lines.append(f"- **Competition**: {coverage.competition_name} ({coverage.season})")
            lines.append(f"- **Coverage Status**: `{coverage.status.value}`")
            lines.append(f"- **Provider**: {coverage.provider}")
            lines.append(f"- **Telemetry**: Lineups: {'Yes' if coverage.has_lineups else 'No'} | Shots/SOT: {'Yes' if coverage.has_shots_and_sot else 'No'} | Cards/Fouls: {'Yes' if coverage.has_cards_and_fouls else 'No'} | xG: {'Yes' if coverage.has_xg else 'No'}")
        else:
            lines.append("- Coverage data: Not available.")
        lines.append("")

        # 2. Statistical Probabilities
        lines.append("## 2. Statistical Model Predictions (Poisson + Dixon-Coles)")
        if prediction:
            lines.append(f"- **Expected Goals**: {prediction.home_team} **{prediction.lambda_home:.2f}** - **{prediction.mu_away:.2f}** {prediction.away_team}")
            lines.append(f"- **Dixon-Coles Parameter ($\\rho$)**: `{prediction.rho_dixon_coles:.3f}`")
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
        lines.append("## 3. Bookmaker Odds Comparison & Value Opportunities")
        if value_opps:
            lines.append("| Selection | Best Odds | Bookmaker | Model Prob | Expected Value (EV) | Value Status |")
            lines.append("| :--- | :---: | :--- | :---: | :---: | :--- |")
            for vo in value_opps:
                ev_pct = f"{vo.expected_value * 100:+.1f}%"
                val_status = "**Positive EV**" if vo.is_positive_ev else "Negative EV"
                lines.append(
                    f"| {vo.selection} {f'({vo.threshold})' if vo.threshold else ''} | **{vo.best_odds:.2f}** | {vo.bookmaker} | {vo.model_probability*100:.1f}% | {ev_pct} | {val_status} |"
                )
        else:
            lines.append("- No verified bookmaker odds found or no qualifying value selections.")
        lines.append("")

        # 4. Parlay Candidates
        lines.append("## 4. Parlay Intelligence Engine")

        # 5-leg parlay
        lines.append("### Parlay A: Five Legs (Screening Threshold: High Probability & Positive Edge)")
        if parlay_5 and parlay_5.is_recommended:
            lines.append(f"- **Structure**: {parlay_5.parlay_type.value} ({parlay_5.leg_count} Legs)")
            lines.append(f"- **Combined Odds**: **{parlay_5.combined_odds:.2f}** ({'Verified Bookmaker Quote' if parlay_5.is_quote_verified else 'Theoretical Joint Estimate'})")
            lines.append(f"- **Joint Win Probability**: **{parlay_5.joint_probability * 100:.2f}%**")
            if parlay_5.expected_value is not None:
                lines.append(f"- **Combined Expected Value**: **{parlay_5.expected_value * 100:+.1f}%**")
            lines.append(f"- **Bookmaker**: {parlay_5.quote_bookmaker}")
            lines.append("\n**Leg Details:**")
            for leg in parlay_5.legs:
                price_str = f"@{leg.best_individual_odds:.2f}" if leg.best_individual_odds else ""
                lines.append(f"  {leg.leg_index}. {leg.fixture_label}: **{leg.selection}** {f'({leg.threshold})' if leg.threshold else ''} (Prob: {leg.leg_win_probability*100:.1f}%) {price_str} - {leg.evidence_notes}")
        else:
            reason = parlay_5.abstention_reason if parlay_5 else "Insufficient qualifying selections."
            lines.append(f"> [!NOTE]\n> **Abstained from 5-leg parlay**: {reason}\n")

        lines.append("")

        # 10-leg parlay
        lines.append("### Parlay B: Ten Legs (Multi-Match Comprehensive Candidate)")
        if parlay_10 and parlay_10.is_recommended:
            lines.append(f"- **Structure**: {parlay_10.parlay_type.value} ({parlay_10.leg_count} Legs)")
            lines.append(f"- **Combined Odds**: **{parlay_10.combined_odds:.2f}** ({'Verified Bookmaker Quote' if parlay_10.is_quote_verified else 'Theoretical Joint Estimate'})")
            lines.append(f"- **Joint Win Probability**: **{parlay_10.joint_probability * 100:.2f}%**")
            if parlay_10.expected_value is not None:
                lines.append(f"- **Combined Expected Value**: **{parlay_10.expected_value * 100:+.1f}%**")
            lines.append(f"- **Bookmaker**: {parlay_10.quote_bookmaker}")
            lines.append("\n**Leg Details:**")
            for leg in parlay_10.legs:
                price_str = f"@{leg.best_individual_odds:.2f}" if leg.best_individual_odds else ""
                lines.append(f"  {leg.leg_index}. {leg.fixture_label}: **{leg.selection}** {f'({leg.threshold})' if leg.threshold else ''} (Prob: {leg.leg_win_probability*100:.1f}%) {price_str} - {leg.evidence_notes}")
        else:
            reason = parlay_10.abstention_reason if parlay_10 else "Insufficient qualifying selections."
            lines.append(f"> [!NOTE]\n> **Abstained from 10-leg parlay**: {reason}\n")

        # 5. Verification & Audit Trail
        lines.append("\n## 5. Result Verification & Integrity Checks")
        if evidence:
            lines.append(f"- **Audit Record ID**: `{evidence.record_id}`")
            lines.append(f"- **Data Cutoff**: {evidence.data_cutoff_timestamp.isoformat()} (strictly protects against future-data leakage)")
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
