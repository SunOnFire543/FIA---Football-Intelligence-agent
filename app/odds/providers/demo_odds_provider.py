"""Deterministic Demo Odds Provider with Multi-Bookmaker Quotes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from app.odds.providers.base import BaseOddsProvider
from app.schemas.enums import MarketType, SelectionOutcome
from app.schemas.models import BookmakerQuote


class DemoOddsProvider(BaseOddsProvider):
    """Provides verified simulated bookmaker quotes across traditional and niche markets."""

    def __init__(self) -> None:
        self._provider_name = "demo"
        self._obs_time = datetime(2026, 10, 24, 11, 30, 0, tzinfo=timezone.utc)
        self._quotes_by_fixture: Dict[str, List[BookmakerQuote]] = {}
        self._init_quotes()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def is_configured(self) -> bool:
        """Demo odds provider is simulated, not an external live provider."""
        return False

    def _init_quotes(self) -> None:
        t = self._obs_time

        # Arsenal vs Chelsea
        self._quotes_by_fixture["FIX_ARS_CHE_2026"] = [
            # 1X2 Match Result
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.HOME.value, decimal_odds=1.86, implied_probability=1/1.86, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.HOME.value, decimal_odds=1.82, implied_probability=1/1.82, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Unibet", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.HOME.value, decimal_odds=1.80, implied_probability=1/1.80, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.DRAW.value, decimal_odds=3.92, implied_probability=1/3.92, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.DRAW.value, decimal_odds=3.80, implied_probability=1/3.80, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.AWAY.value, decimal_odds=4.50, implied_probability=1/4.50, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.AWAY.value, decimal_odds=4.30, implied_probability=1/4.30, observed_at=t, is_live=True),

            # Double Chance
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.DOUBLE_CHANCE, selection=SelectionOutcome.HOME_OR_DRAW.value, decimal_odds=1.28, implied_probability=1/1.28, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.DOUBLE_CHANCE, selection=SelectionOutcome.HOME_OR_DRAW.value, decimal_odds=1.25, implied_probability=1/1.25, observed_at=t, is_live=True),

            # Over/Under Total Goals
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=1.5, decimal_odds=1.24, implied_probability=1/1.24, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=1.5, decimal_odds=1.22, implied_probability=1/1.22, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=2.5, decimal_odds=1.80, implied_probability=1/1.80, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=2.5, decimal_odds=1.75, implied_probability=1/1.75, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.UNDER.value, threshold=2.5, decimal_odds=2.15, implied_probability=1/2.15, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.UNDER.value, threshold=2.5, decimal_odds=2.10, implied_probability=1/2.10, observed_at=t, is_live=True),

            # Both Teams To Score
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.BOTH_TEAMS_TO_SCORE, selection=SelectionOutcome.YES.value, decimal_odds=1.74, implied_probability=1/1.74, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.BOTH_TEAMS_TO_SCORE, selection=SelectionOutcome.YES.value, decimal_odds=1.70, implied_probability=1/1.70, observed_at=t, is_live=True),

            # Player Props - Bukayo Saka
            BookmakerQuote(bookmaker="Unibet", market=MarketType.PLAYER_SHOTS_ON_TARGET, selection="Bukayo Saka Over 0.5 SOT", threshold=0.5, decimal_odds=1.40, implied_probability=1/1.40, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.PLAYER_SHOTS_ON_TARGET, selection="Bukayo Saka Over 0.5 SOT", threshold=0.5, decimal_odds=1.36, implied_probability=1/1.36, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Unibet", market=MarketType.PLAYER_SHOTS, selection="Bukayo Saka Over 1.5 Shots", threshold=1.5, decimal_odds=1.32, implied_probability=1/1.32, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.PLAYER_SHOTS, selection="Bukayo Saka Over 1.5 Shots", threshold=1.5, decimal_odds=1.30, implied_probability=1/1.30, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Bet365", market=MarketType.ANYTIME_GOALSCORER, selection="Bukayo Saka Anytime Goalscorer", decimal_odds=2.85, implied_probability=1/2.85, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Unibet", market=MarketType.ANYTIME_GOALSCORER, selection="Bukayo Saka Anytime Goalscorer", decimal_odds=3.00, implied_probability=1/3.00, observed_at=t, is_live=True),

            # Player Props - Kai Havertz
            BookmakerQuote(bookmaker="Bet365", market=MarketType.PLAYER_SHOTS_ON_TARGET, selection="Kai Havertz Over 0.5 SOT", threshold=0.5, decimal_odds=1.45, implied_probability=1/1.45, observed_at=t, is_live=True),

            # Niche Counts
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.TOTAL_CORNERS, selection="Over 8.5 Total Corners", threshold=8.5, decimal_odds=1.44, implied_probability=1/1.44, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.TOTAL_CORNERS, selection="Over 8.5 Total Corners", threshold=8.5, decimal_odds=1.40, implied_probability=1/1.40, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Unibet", market=MarketType.TOTAL_CARDS, selection="Over 3.5 Total Cards", threshold=3.5, decimal_odds=1.58, implied_probability=1/1.58, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.TOTAL_CARDS, selection="Over 3.5 Total Cards", threshold=3.5, decimal_odds=1.55, implied_probability=1/1.55, observed_at=t, is_live=True),

            BookmakerQuote(bookmaker="Bet365", market=MarketType.TOTAL_FOULS, selection="Over 21.5 Total Fouls", threshold=21.5, decimal_odds=1.72, implied_probability=1/1.72, observed_at=t, is_live=True),
        ]

        # Man City vs Liverpool
        self._quotes_by_fixture["FIX_MCI_LIV_2026"] = [
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.HOME.value, decimal_odds=2.05, implied_probability=1/2.05, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.DOUBLE_CHANCE, selection=SelectionOutcome.HOME_OR_DRAW.value, decimal_odds=1.35, implied_probability=1/1.35, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=1.5, decimal_odds=1.18, implied_probability=1/1.18, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.BOTH_TEAMS_TO_SCORE, selection=SelectionOutcome.YES.value, decimal_odds=1.60, implied_probability=1/1.60, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.TOTAL_CORNERS, selection="Over 8.5 Total Corners", threshold=8.5, decimal_odds=1.38, implied_probability=1/1.38, observed_at=t, is_live=True),
        ]

        # Real Madrid vs Barcelona
        self._quotes_by_fixture["FIX_RMA_BAR_2026"] = [
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.MATCH_RESULT, selection=SelectionOutcome.HOME.value, decimal_odds=2.15, implied_probability=1/2.15, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.DOUBLE_CHANCE, selection=SelectionOutcome.HOME_OR_DRAW.value, decimal_odds=1.38, implied_probability=1/1.38, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Pinnacle", market=MarketType.OVER_UNDER_GOALS, selection=SelectionOutcome.OVER.value, threshold=1.5, decimal_odds=1.20, implied_probability=1/1.20, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.BOTH_TEAMS_TO_SCORE, selection=SelectionOutcome.YES.value, decimal_odds=1.55, implied_probability=1/1.55, observed_at=t, is_live=True),
            BookmakerQuote(bookmaker="Bet365", market=MarketType.TOTAL_CARDS, selection="Over 3.5 Total Cards", threshold=3.5, decimal_odds=1.45, implied_probability=1/1.45, observed_at=t, is_live=True),
        ]

    def get_current_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        return self._quotes_by_fixture.get(fixture_id, [])

    def get_historical_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        return self._quotes_by_fixture.get(fixture_id, [])
