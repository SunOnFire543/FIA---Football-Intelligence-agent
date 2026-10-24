"""Unit tests for Odds Normalisation, Comparison, and EV Engine."""

from datetime import datetime, timezone
import pytest

from app.odds.comparison import OddsComparisonEngine
from app.odds.expected_value import ExpectedValueEngine
from app.odds.normalisation import OddsNormaliser
from app.schemas.enums import MarketType, ModelStatus, SelectionOutcome
from app.schemas.models import BookmakerQuote, SelectionPrediction


def test_odds_normalisation_and_vig_removal():
    now = datetime.now(timezone.utc)
    quotes = [
        BookmakerQuote(bookmaker="BookA", market=MarketType.MATCH_RESULT, selection="HOME", decimal_odds=2.00, implied_probability=0.50, observed_at=now),
        BookmakerQuote(bookmaker="BookA", market=MarketType.MATCH_RESULT, selection="DRAW", decimal_odds=3.50, implied_probability=1/3.50, observed_at=now),
        BookmakerQuote(bookmaker="BookA", market=MarketType.MATCH_RESULT, selection="AWAY", decimal_odds=3.80, implied_probability=1/3.80, observed_at=now),
    ]

    vig_free = OddsNormaliser.remove_vig_proportional(quotes)
    # The sum of vig-free probabilities must be exactly 1.0
    total = sum(vig_free.values())
    assert abs(total - 1.0) < 1e-5
    # Overround is removed
    assert vig_free["HOME"] < 0.50


def test_odds_comparison_best_price():
    engine = OddsComparisonEngine()
    now = datetime.now(timezone.utc)

    quotes = [
        BookmakerQuote(bookmaker="Bet365", market=MarketType.MATCH_RESULT, selection="HOME", decimal_odds=1.80, implied_probability=1/1.80, observed_at=now),
        BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection="HOME", decimal_odds=1.86, implied_probability=1/1.86, observed_at=now),
        BookmakerQuote(bookmaker="Unibet", market=MarketType.MATCH_RESULT, selection="HOME", decimal_odds=1.75, implied_probability=1/1.75, observed_at=now),
    ]

    comps = engine.compare_odds("FIX_1", quotes)
    assert len(comps) == 1
    assert comps[0].best_decimal_odds == 1.86
    assert comps[0].best_bookmaker == "Pinnacle"


def test_expected_value_calculation():
    ev_engine = ExpectedValueEngine()

    # Probability = 0.60, Odds = 2.00 -> EV = 0.60 * 2.00 - 1 = +0.20 (+20%)
    ev_pos = ev_engine.calculate_ev(0.60, 2.00)
    assert abs(ev_pos - 0.20) < 1e-6

    # Probability = 0.40, Odds = 2.00 -> EV = 0.40 * 2.00 - 1 = -0.20 (-20%)
    ev_neg = ev_engine.calculate_ev(0.40, 2.00)
    assert abs(ev_neg - (-0.20)) < 1e-6
