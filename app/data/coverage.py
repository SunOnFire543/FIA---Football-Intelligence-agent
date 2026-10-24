"""Coverage Registry and Data Depth Tracker.

Tracks explicit data availability states across competitions, seasons,
and statistical markets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.enums import CoverageStatus, MarketType
from app.schemas.models import CoverageRecord


class CoverageRegistry:
    """Manages and audits data coverage across the football pyramid."""

    def __init__(self) -> None:
        self._registry: Dict[str, CoverageRecord] = {}

    def register(self, record: CoverageRecord) -> None:
        """Register or update a coverage record."""
        key = f"{record.competition_id}:{record.season}:{record.provider}".upper()
        self._registry[key] = record

    def get_coverage(
        self,
        competition_id: str,
        season: str = "2026/27",
        provider: str = "demo",
    ) -> Optional[CoverageRecord]:
        """Look up coverage by competition, season, and provider."""
        key = f"{competition_id}:{season}:{provider}".upper()
        if key in self._registry:
            return self._registry[key]

        # Fallback to competition_id lookup
        for k, v in self._registry.items():
            if k.startswith(competition_id.upper()):
                return v
        return None

    def is_market_supported(
        self,
        competition_id: str,
        market: MarketType,
        season: str = "2026/27",
        provider: str = "demo",
    ) -> bool:
        """Check if a specific market is supported under verified coverage."""
        cov = self.get_coverage(competition_id, season, provider)
        if not cov or cov.status == CoverageStatus.UNAVAILABLE:
            return False

        if market in (MarketType.MATCH_RESULT, MarketType.DOUBLE_CHANCE, MarketType.OVER_UNDER_GOALS, MarketType.BOTH_TEAMS_TO_SCORE):
            return cov.has_match_events

        if market in (MarketType.PLAYER_SHOTS, MarketType.PLAYER_SHOTS_ON_TARGET, MarketType.ANYTIME_GOALSCORER):
            return cov.has_player_props and cov.has_lineups

        if market in (MarketType.TOTAL_CARDS, MarketType.TOTAL_FOULS):
            return cov.has_cards_and_fouls

        return cov.has_match_events


# Default global coverage registry
default_coverage_registry = CoverageRegistry()

# Initialize standard 5-year coverage baselines
default_coverage_registry.register(
    CoverageRecord(
        competition_id="PL",
        competition_name="Premier League",
        season="2026/27",
        provider="demo",
        status=CoverageStatus.AVAILABLE,
        has_match_events=True,
        has_lineups=True,
        has_shots_and_sot=True,
        has_cards_and_fouls=True,
        has_xg=True,
        has_historical_odds=True,
        has_live_odds=True,
        has_player_props=True,
        notes="Verified 5-year coverage for English Premier League (2022-2027).",
    )
)

default_coverage_registry.register(
    CoverageRecord(
        competition_id="PD",
        competition_name="La Liga",
        season="2026/27",
        provider="demo",
        status=CoverageStatus.AVAILABLE,
        has_match_events=True,
        has_lineups=True,
        has_shots_and_sot=True,
        has_cards_and_fouls=True,
        has_xg=True,
        has_historical_odds=True,
        has_live_odds=True,
        has_player_props=True,
        notes="Verified 5-year coverage for Spanish La Liga.",
    )
)

default_coverage_registry.register(
    CoverageRecord(
        competition_id="CL",
        competition_name="UEFA Champions League",
        season="2026/27",
        provider="demo",
        status=CoverageStatus.PARTIAL,
        has_match_events=True,
        has_lineups=True,
        has_shots_and_sot=True,
        has_cards_and_fouls=True,
        has_xg=False,
        has_historical_odds=True,
        has_live_odds=True,
        has_player_props=False,
        notes="Tournament structure. Match markets supported; player props uncalibrated.",
    )
)
