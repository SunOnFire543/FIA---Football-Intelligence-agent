"""Unit tests for Verification, Provenance, and Temporal Backtesting."""

from datetime import datetime, timedelta, timezone
import pytest

from app.evaluation.backtesting import WalkForwardBacktester
from app.evaluation.metrics import EvaluationMetrics
from app.schemas.enums import MarketType, ModelStatus, SelectionOutcome
from app.schemas.models import (
    Fixture,
    MatchPredictionSummary,
    SelectionPrediction,
    ValueOpportunity,
)
from app.verification.result_validator import ResultValidator


def test_result_validator_catches_math_discrepancy():
    now = datetime.now(timezone.utc)

    # Erroneous EV calculation: prob 0.60, odds 2.00, but stated EV is 0.50 (correct is 0.20)
    bogus_opp = ValueOpportunity(
        fixture_id="FIX_1",
        fixture_label="Arsenal vs Chelsea",
        market=MarketType.MATCH_RESULT,
        selection="HOME",
        model_probability=0.60,
        best_odds=2.00,
        bookmaker="Pinnacle",
        expected_value=0.50,  # Deliberately incorrect math
        is_positive_ev=True,
        odds_observed_at=now,
        model_uncertainty=0.1,
        coverage_status="AVAILABLE",
    )

    evidence = ResultValidator.verify_analysis(
        fixture_id="FIX_1",
        competition_id="PL",
        prediction=None,
        value_opps=[bogus_opp],
        parlay_5=None,
        parlay_10=None,
        data_cutoff=now,
    )

    assert evidence.verification_passed is False
    assert any("EV calculation error" in w for w in evidence.verification_warnings)


def test_temporal_walk_forward_backtest():
    backtester = WalkForwardBacktester()

    now = datetime(2026, 10, 20, 15, 0, 0, tzinfo=timezone.utc)
    # Generate 15 chronologically ordered matches
    history = [
        Fixture(
            fixture_id=f"HIST_{i}",
            competition_id="PL",
            season="2026/27",
            kickoff_time=now - timedelta(days=7 * (15 - i)),  # Strictly increasing date
            home_team_id="ARS",
            home_team_name="Arsenal FC",
            away_team_id=f"OPP_{i}",
            away_team_name=f"Opponent {i}",
            status="FINISHED",
            home_score=2 if i % 2 == 0 else 1,
            away_score=0 if i % 3 == 0 else 1,
        )
        for i in range(15)
    ]

    summary = backtester.run_backtest(history, start_index=5)
    assert summary.total_matches_evaluated > 0
    assert summary.temporal_leakage_prevented is True
    assert 0.0 <= summary.brier_score_home_win <= 1.0
    assert summary.log_loss_home_win >= 0.0


def test_metrics_calculations():
    # Perfect predictions: prob = 1.0 when actual = 1, prob = 0.0 when actual = 0
    brier_perfect = EvaluationMetrics.brier_score([1.0, 0.0], [1, 0])
    assert brier_perfect == 0.0

    # Total miss: prob = 0.0 when actual = 1
    brier_worst = EvaluationMetrics.brier_score([0.0, 1.0], [1, 0])
    assert brier_worst == 1.0

    # ROI test: 2 bets, 1 wins at 2.50, 1 loses -> (2.50 - 2) / 2 = +0.25 (+25% ROI)
    bets = [
        (0.6, 2.50, 1),
        (0.6, 2.50, 0),
    ]
    roi = EvaluationMetrics.return_on_investment(bets)
    assert abs(roi - 0.25) < 1e-6
