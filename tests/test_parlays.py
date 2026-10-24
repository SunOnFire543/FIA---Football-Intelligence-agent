"""Unit tests for Parlay Intelligence Engine (5-Leg and 10-Leg)."""

import pytest
from app.parlays.generator import ParlayGenerator
from app.parlays.probability import ParlayProbabilityModel
from app.schemas.enums import MarketType, SelectionOutcome
from app.schemas.models import ParlayLeg


def test_same_match_joint_probability_vs_naive_product():
    prob_model = ParlayProbabilityModel()

    # Score matrix where Home Win (x > y) and Over 1.5 (x + y > 1.5) are dependent
    score_matrix = {
        "0-0": 0.08,
        "1-0": 0.12,
        "2-0": 0.15,
        "2-1": 0.14,
        "3-0": 0.10,
        "0-1": 0.09,
        "1-1": 0.12,
        "1-2": 0.08,
        "0-2": 0.07,
        "2-2": 0.05,
    }

    legs = [
        ParlayLeg(
            leg_index=1,
            fixture_id="FIX_1",
            fixture_label="Arsenal vs Chelsea",
            market=MarketType.MATCH_RESULT,
            selection=SelectionOutcome.HOME.value,
            leg_win_probability=0.51,  # 2-0 (0.15) + 2-1 (0.14) + 1-0 (0.12) + 3-0 (0.10) = 0.51
            best_individual_odds=1.85,
        ),
        ParlayLeg(
            leg_index=2,
            fixture_id="FIX_1",
            fixture_label="Arsenal vs Chelsea",
            market=MarketType.OVER_UNDER_GOALS,
            selection=SelectionOutcome.OVER.value,
            threshold=1.5,
            leg_win_probability=0.71,
            best_individual_odds=1.25,
        ),
    ]

    # Exact joint probability evaluated from score matrix
    joint_p = prob_model.compute_same_match_joint_probability(legs, score_matrix)
    naive_product = 0.51 * 0.71  # = 0.3621

    # In our score matrix:
    # Scores where Home Win AND Over 1.5:
    # 2-0 (0.15) + 2-1 (0.14) + 3-0 (0.10) = 0.39
    assert abs(joint_p - 0.39) < 1e-4
    # The joint probability from bivariate distribution correctly differs from naive independent multiplication!
    assert joint_p != naive_product


def test_parlay_candidate_generation_and_abstention():
    generator = ParlayGenerator(target_bookmaker="Bet365")

    # Scenario 1: Insufficient qualifying selections -> Must abstain cleanly
    insufficient_legs = [
        ParlayLeg(
            leg_index=1,
            fixture_id="FIX_1",
            fixture_label="Match 1",
            market=MarketType.MATCH_RESULT,
            selection="HOME",
            leg_win_probability=0.85,
            best_individual_odds=1.20,
        ),
        ParlayLeg(
            leg_index=2,
            fixture_id="FIX_2",
            fixture_label="Match 2",
            market=MarketType.OVER_UNDER_GOALS,
            selection="OVER",
            threshold=1.5,
            leg_win_probability=0.75,
            best_individual_odds=1.25,
        ),
    ]

    p5_abstained = generator.generate_5_leg_candidate(insufficient_legs)
    assert p5_abstained.is_recommended is False
    assert "Only 2 selections met" in p5_abstained.abstention_reason
    assert len(p5_abstained.legs) == 0

    # Scenario 2: Exactly 5 qualifying selections -> Creates valid 5-leg candidate
    qualifying_5 = [
        ParlayLeg(
            leg_index=i,
            fixture_id=f"FIX_{i}",
            fixture_label=f"Match {i}",
            market=MarketType.OVER_UNDER_GOALS,
            selection="OVER",
            threshold=1.5,
            leg_win_probability=0.75,
            best_individual_odds=1.25,
        )
        for i in range(1, 6)
    ]

    p5_valid = generator.generate_5_leg_candidate(qualifying_5)
    assert p5_valid.is_recommended is True
    assert p5_valid.leg_count == 5
    assert len(p5_valid.legs) == 5
    assert p5_valid.combined_odds > 1.0
    assert 0.0 < p5_valid.joint_probability < 1.0

    # Scenario 3: Exactly 10 qualifying selections -> Creates valid 10-leg candidate
    qualifying_10 = [
        ParlayLeg(
            leg_index=i,
            fixture_id=f"FIX_{i}",
            fixture_label=f"Match {i}",
            market=MarketType.OVER_UNDER_GOALS,
            selection="OVER",
            threshold=1.5,
            leg_win_probability=0.72,
            best_individual_odds=1.22,
        )
        for i in range(1, 11)
    ]

    p10_valid = generator.generate_10_leg_candidate(qualifying_10)
    assert p10_valid.is_recommended is True
    assert p10_valid.leg_count == 10
    assert len(p10_valid.legs) == 10
    assert p10_valid.combined_odds > 1.0
    assert 0.0 < p10_valid.joint_probability < 1.0
