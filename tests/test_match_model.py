"""Unit tests for Dixon-Coles Goal Model and Probability Validation."""

import math
import numpy as np
import pytest

from app.models.match_model import DixonColesMatchModel
from app.models.probability_validation import ProbabilityValidator
from app.schemas.enums import MarketType, SelectionOutcome
from app.schemas.models import Fixture


def test_poisson_pmf_and_tau():
    model = DixonColesMatchModel(rho=-0.08)
    p0 = model._poisson_pmf(0, 1.5)
    expected_p0 = math.exp(-1.5)
    assert abs(p0 - expected_p0) < 1e-6

    # Test tau adjustments
    tau_00 = model._tau(0, 0, 1.5, 1.2)
    assert abs(tau_00 - (1.0 - 1.5 * 1.2 * (-0.08))) < 1e-6

    tau_22 = model._tau(2, 2, 1.5, 1.2)
    assert tau_22 == 1.0


def test_score_matrix_sums_to_one():
    model = DixonColesMatchModel()
    matrix, tail_mass = model.compute_score_matrix(1.65, 1.10)
    total_mass = float(np.sum(matrix))
    assert abs(total_mass - 1.0) < 1e-5
    # Verify upper tail mass truncation is small (< 1%)
    assert tail_mass < 0.01


def test_dixon_coles_predict_probabilities():
    model = DixonColesMatchModel()

    fix = Fixture(
        fixture_id="TEST_FIX",
        competition_id="PL",
        season="2026/27",
        kickoff_time="2026-10-25T15:00:00Z",
        home_team_id="ARS",
        home_team_name="Arsenal",
        away_team_id="CHE",
        away_team_name="Chelsea",
    )

    home_history = [
        Fixture(
            fixture_id=f"H_{i}",
            competition_id="PL",
            season="2026/27",
            kickoff_time="2026-10-01T15:00:00Z",
            home_team_id="ARS",
            home_team_name="Arsenal",
            away_team_id="OPP",
            away_team_name="Opponent",
            status="FINISHED",
            home_score=2,
            away_score=1,
        )
        for i in range(12)
    ]

    away_history = [
        Fixture(
            fixture_id=f"A_{i}",
            competition_id="PL",
            season="2026/27",
            kickoff_time="2026-10-01T15:00:00Z",
            home_team_id="OPP",
            home_team_name="Opponent",
            away_team_id="CHE",
            away_team_name="Chelsea",
            status="FINISHED",
            home_score=1,
            away_score=1,
        )
        for i in range(12)
    ]

    summary = model.predict_fixture(fix, home_history, away_history)

    # 1X2 probabilities must sum to 1.0
    hda = [p.estimated_probability for p in summary.predictions if p.market == MarketType.MATCH_RESULT]
    assert len(hda) == 3
    assert abs(sum(hda) - 1.0) < 1e-4

    # Double Chance consistency: P(1X) == P(1) + P(X)
    p_home = next(p.estimated_probability for p in summary.predictions if p.selection == SelectionOutcome.HOME.value)
    p_draw = next(p.estimated_probability for p in summary.predictions if p.selection == SelectionOutcome.DRAW.value)
    p_1x = next(p.estimated_probability for p in summary.predictions if p.selection == SelectionOutcome.HOME_OR_DRAW.value)
    assert abs(p_1x - (p_home + p_draw)) < 1e-4

    # Over/Under monotonicity: Over 1.5 >= Over 2.5 >= Over 3.5
    p_o15 = next(p.estimated_probability for p in summary.predictions if p.market == MarketType.OVER_UNDER_GOALS and p.threshold == 1.5 and p.selection == "OVER")
    p_o25 = next(p.estimated_probability for p in summary.predictions if p.market == MarketType.OVER_UNDER_GOALS and p.threshold == 2.5 and p.selection == "OVER")
    p_o35 = next(p.estimated_probability for p in summary.predictions if p.market == MarketType.OVER_UNDER_GOALS and p.threshold == 3.5 and p.selection == "OVER")
    assert p_o15 >= p_o25 >= p_o35

    # BTTS sum to 1.0
    btts_yes = next(p.estimated_probability for p in summary.predictions if p.market == MarketType.BOTH_TEAMS_TO_SCORE and p.selection == "YES")
    btts_no = next(p.estimated_probability for p in summary.predictions if p.market == MarketType.BOTH_TEAMS_TO_SCORE and p.selection == "NO")
    assert abs((btts_yes + btts_no) - 1.0) < 1e-4
