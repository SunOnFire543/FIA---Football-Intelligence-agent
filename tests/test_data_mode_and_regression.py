"""Regression tests for data modes, stale odds, and modeling edge cases."""

from datetime import datetime, timezone
import pytest

from app.agent.response_builder import ResponseBuilder
from app.models.match_model import DixonColesMatchModel
from app.odds.comparison import OddsComparisonEngine
from app.schemas.enums import MarketType
from app.schemas.models import (
    BookmakerQuote,
    CompactEvidenceRecord,
    CoverageRecord,
    CoverageStatus,
    MatchPredictionSummary,
    ValueOpportunity,
)


def test_stale_or_suspended_odds_filtered():
    engine = OddsComparisonEngine()
    now = datetime.now(timezone.utc)

    quotes = [
        BookmakerQuote(
            bookmaker="SuspendedBookie",
            market=MarketType.MATCH_RESULT,
            selection="HOME",
            decimal_odds=2.50,
            implied_probability=1/2.50,
            observed_at=now,
            is_suspended=True,  # Suspended quote must be filtered out
        ),
        BookmakerQuote(
            bookmaker="ActiveBookie",
            market=MarketType.MATCH_RESULT,
            selection="HOME",
            decimal_odds=1.85,
            implied_probability=1/1.85,
            observed_at=now,
            is_suspended=False,
        ),
    ]

    comparisons = engine.compare_odds("FIX_TEST", quotes)
    assert len(comparisons) == 1
    assert comparisons[0].best_bookmaker == "ActiveBookie"
    assert comparisons[0].best_decimal_odds == 1.85


def test_score_matrix_tail_mass_for_high_scoring_match():
    # Even for high-scoring expectations, check that upper tail (>= 8 goals) is tracked
    model = DixonColesMatchModel(rho=-0.08)
    matrix, tail_mass = model.compute_score_matrix(2.5, 2.0)
    # Total mass must be normalized to 1.0
    import numpy as np
    assert abs(float(np.sum(matrix)) - 1.0) < 1e-5
    # The tail mass was bounded and tracked
    assert 0.0 <= tail_mass <= 0.10


def test_response_builder_demo_vs_live_mode_labeling():
    now = datetime.now(timezone.utc)
    ev = CompactEvidenceRecord(
        record_id="EVID_TEST",
        fixture_id="FIX_1",
        competition_id="PL",
        prediction_timestamp=now,
        data_cutoff_timestamp=now,
        model_version="2.1.0",
        selections_evaluated=[],
        source_providers=["test"],
        odds_sources=["test"],
        coverage_status=CoverageStatus.AVAILABLE,
        verification_passed=True,
    )

    demo_text = ResponseBuilder.format_match_analysis(
        fixture_label="Arsenal vs Chelsea",
        coverage=None,
        prediction=None,
        value_opps=[],
        parlay_5=None,
        parlay_10=None,
        evidence=ev,
        data_mode="DEMO",
    )
    assert "[DATA MODE: DEMO (SIMULATED)]" in demo_text
    assert "DEMO / SIMULATION MODE NOTICE" in demo_text

    live_text = ResponseBuilder.format_match_analysis(
        fixture_label="Arsenal vs Chelsea",
        coverage=None,
        prediction=None,
        value_opps=[],
        parlay_5=None,
        parlay_10=None,
        evidence=ev,
        data_mode="LIVE",
    )
    assert "[DATA MODE: LIVE]" in live_text
    assert "DEMO / SIMULATION MODE NOTICE" not in live_text
