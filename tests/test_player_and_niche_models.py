"""Unit tests for Player Proposition and Niche Count Models."""

import pytest
from app.models.count_models import NicheCountModel
from app.models.player_model import PlayerPropModel
from app.schemas.enums import MarketType
from app.schemas.models import FixtureLineups, LineupPlayer, PlayerMatchStats


def test_player_model_starting_vs_bench():
    model = PlayerPropModel()

    stats = [
        PlayerMatchStats(
            player_id="P1",
            player_name="Test Player",
            fixture_id=f"FIX_{i}",
            team_id="T1",
            minutes_played=90,
            is_starter=True,
            shots=3,
            shots_on_target=2,
            goals=1 if i % 2 == 0 else 0,
        )
        for i in range(10)
    ]

    starter_lineups = FixtureLineups(
        fixture_id="F_UPCOMING",
        is_confirmed=True,
        home_starters=[LineupPlayer(player_id="P1", name="Test Player", position="FWD", is_starter=True)],
    )

    bench_lineups = FixtureLineups(
        fixture_id="F_UPCOMING",
        is_confirmed=True,
        home_bench=[LineupPlayer(player_id="P1", name="Test Player", position="FWD", is_starter=False)],
    )

    preds_starter = model.predict_player_markets("Test Player", stats, starter_lineups)
    preds_bench = model.predict_player_markets("Test Player", stats, bench_lineups)

    # Starter should have significantly higher probability for Over 0.5 SOT than substitute
    sot_starter = next(p.estimated_probability for p in preds_starter if p.market == MarketType.PLAYER_SHOTS_ON_TARGET and p.threshold == 0.5)
    sot_bench = next(p.estimated_probability for p in preds_bench if p.market == MarketType.PLAYER_SHOTS_ON_TARGET and p.threshold == 0.5)
    assert sot_starter > sot_bench
    assert 0.0 < sot_starter < 1.0
    assert 0.0 < sot_bench < 1.0


def test_niche_count_model():
    model = NicheCountModel()
    preds = model.predict_niche_markets(None, avg_corners=10.5, avg_cards=4.2, avg_fouls=22.0)

    # Check corners monotonicity
    c85 = next(p.estimated_probability for p in preds if p.market == MarketType.TOTAL_CORNERS and p.threshold == 8.5)
    c95 = next(p.estimated_probability for p in preds if p.market == MarketType.TOTAL_CORNERS and p.threshold == 9.5)
    c105 = next(p.estimated_probability for p in preds if p.market == MarketType.TOTAL_CORNERS and p.threshold == 10.5)
    assert c85 > c95 > c105
