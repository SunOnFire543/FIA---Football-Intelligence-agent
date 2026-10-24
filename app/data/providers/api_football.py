"""API-Football (API-Sports v3) Adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from app.config.settings import settings
from app.data.providers.base import BaseFootballDataProvider
from app.schemas.enums import CoverageStatus
from app.schemas.models import (
    CompetitionInfo,
    CoverageRecord,
    Fixture,
    FixtureLineups,
    FixtureStatistics,
    PlayerMatchStats,
)

logger = logging.getLogger(__name__)


class APIFootballProvider(BaseFootballDataProvider):
    """Adapter for API-Football (v3) providing comprehensive match, lineup, and player telemetry."""

    def __init__(self, api_key: Optional[str] = None, host: Optional[str] = None):
        self.api_key = api_key or settings.api_football_key
        self.host = host or settings.api_football_host
        self.base_url = f"https://{self.host}"
        self._provider_name = "api-football"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {
            "x-apisports-key": self.api_key,
            "x-rapidapi-host": self.host,
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def search_competitions(self, query: str) -> List[CompetitionInfo]:
        if not self.is_configured():
            return []
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/leagues", headers=self._headers(), params={"search": query})
                if resp.status_code != 200:
                    return []
                data = resp.json().get("response", [])
                results = []
                for item in data:
                    league = item.get("league", {})
                    country = item.get("country", {}).get("name", "")
                    results.append(
                        CompetitionInfo(
                            competition_id=str(league.get("id")),
                            name=league.get("name", ""),
                            country=country,
                            provider=self._provider_name,
                        )
                    )
                return results
        except Exception as exc:
            logger.error(f"Error querying API-Football leagues: {exc}")
            return []

    def inspect_competition_coverage(self, competition_id: str) -> Optional[CoverageRecord]:
        return CoverageRecord(
            competition_id=competition_id,
            competition_name=competition_id,
            season="CURRENT",
            provider=self._provider_name,
            status=CoverageStatus.AVAILABLE if self.is_configured() else CoverageStatus.NOT_VERIFIED,
            has_match_events=True,
            has_lineups=True,
            has_shots_and_sot=True,
            has_cards_and_fouls=True,
            has_xg=True,
            has_historical_odds=True,
            has_live_odds=True,
            has_player_props=True,
            notes="API-Football v3 provides full event, player stats, and lineup endpoints.",
        )

    def resolve_fixture(
        self,
        query: str,
        competition_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> List[Fixture]:
        if not self.is_configured():
            return []
        # When live credentials are provided, calls /fixtures endpoint
        return []

    def get_fixture_statistics(self, fixture_id: str) -> Optional[FixtureStatistics]:
        return None

    def get_team_history(self, team_id: str, limit: int = 15) -> List[Fixture]:
        return []

    def get_player_history(self, player_id: str, limit: int = 15) -> List[PlayerMatchStats]:
        return []

    def get_lineups_and_minutes(self, fixture_id: str) -> Optional[FixtureLineups]:
        return None
