"""Expected Value (EV) and Statistical Edge Engine."""

from __future__ import annotations

from typing import List, Optional
from app.schemas.enums import CoverageStatus, ModelStatus
from app.schemas.models import (
    MarketOddsComparison,
    SelectionPrediction,
    ValueOpportunity,
)


class ExpectedValueEngine:
    """Computes expected net return per unit stake and identifies statistical value."""

    @staticmethod
    def calculate_ev(prob: float, decimal_odds: float) -> float:
        """Expected net return per unit stake: p * Odds - 1."""
        if prob <= 0.0 or decimal_odds <= 1.0:
            return -1.0
        return (prob * decimal_odds) - 1.0

    def evaluate_value(
        self,
        fixture_id: str,
        fixture_label: str,
        predictions: List[SelectionPrediction],
        odds_comparisons: List[MarketOddsComparison],
        coverage_status: CoverageStatus = CoverageStatus.AVAILABLE,
    ) -> List[ValueOpportunity]:
        """Match predictions against best verified odds to compute EV."""
        opportunities: List[ValueOpportunity] = []

        # Index odds by (market, selection_upper, threshold)
        odds_map = {}
        for oc in odds_comparisons:
            thresh_key = f"{oc.threshold:.2f}" if oc.threshold is not None else "NONE"
            key = (oc.market, oc.selection.strip().upper(), thresh_key)
            odds_map[key] = oc

        for p in predictions:
            thresh_key = f"{p.threshold:.2f}" if p.threshold is not None else "NONE"
            key = (p.market, p.selection.strip().upper(), thresh_key)

            oc = odds_map.get(key)
            if not oc:
                continue

            ev = self.calculate_ev(p.estimated_probability, oc.best_decimal_odds)
            is_pos = ev > 0.0 and p.model_status == ModelStatus.SUPPORTED

            opportunities.append(
                ValueOpportunity(
                    fixture_id=fixture_id,
                    fixture_label=fixture_label,
                    market=p.market,
                    selection=p.selection,
                    threshold=p.threshold,
                    model_probability=p.estimated_probability,
                    best_odds=oc.best_decimal_odds,
                    bookmaker=oc.best_bookmaker,
                    expected_value=ev,
                    is_positive_ev=is_pos,
                    odds_observed_at=oc.observed_at,
                    model_uncertainty=p.uncertainty_score,
                    coverage_status=coverage_status,
                )
            )

        return opportunities
