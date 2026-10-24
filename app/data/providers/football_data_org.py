"""Football-Data.org API v4 Adapter."""

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


class FootballDataOrgProvider(BaseFootballDataProvider):
    """Adapter for Football-Data.org REST API v4."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.football_data_api_key
        self.base_url = (base_url or settings.football_data_base_url).rstrip("/")
        self._provider_name = "football-data.org"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-Auth-Token": self.api_key}

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def search_competitions(self, query: str) -> List[CompetitionInfo]:
        if not self.is_configured():
            logger.info("Football-Data.org API key not configured. Returning empty.")
            return []

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/competitions", headers=self._headers())
                if resp.status_code != 200:
                    logger.warning(f"Football-Data.org returned HTTP {resp.status_code}")
                    return []
                data = resp.json()
                results = []
                q = query.lower()
                for comp in data.get("competitions", []):
                    name = comp.get("name", "")
                    code = comp.get("code", "")
                    country = comp.get("area", {}).get("name", "")
                    if q in name.lower() or q in code.lower() or q in country.lower():
                        results.append(
                            CompetitionInfo(
                                competition_id=code or str(comp.get("id")),
                                name=name,
                                country=country,
                                provider=self._provider_name,
                            )
                        )
                return results
        except Exception as exc:
            logger.error(f"Error querying Football-Data.org competitions: {exc}")
            return []

    def inspect_competition_coverage(self, competition_id: str) -> Optional[CoverageRecord]:
        return CoverageRecord(
            competition_id=competition_id,
            competition_name=competition_id,
            season="CURRENT",
            provider=self._provider_name,
            status=CoverageStatus.PARTIAL if self.is_configured() else CoverageStatus.NOT_VERIFIED,
            has_match_events=True,
            has_lineups=False,
            has_shots_and_sot=False,
            has_cards_and_fouls=False,
            has_xg=False,
            has_historical_odds=False,
            has_live_odds=False,
            has_player_props=False,
            notes="Football-Data.org Tier 1 covers match results, standings, and basic scorers.",
        )

    def resolve_fixture(
        self,
        query: str,
        competition_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> List[Fixture]:
        if not self.is_configured():
            return []
        try:
            endpoint = f"{self.base_url}/competitions/{competition_id}/matches" if competition_id else f"{self.base_url}/matches"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(endpoint, headers=self._headers())
                if resp.status_code != 200:
                    return []
                matches_data = resp.json().get("matches", [])
                results = []
                q = query.lower()
                for m in matches_data:
                    home = m.get("homeTeam", {}).get("name", "")
                    away = m.get("awayTeam", {}).get("name", "")
                    if q in home.lower() or q in away.lower():
                        kickoff_str = m.get("utcDate")
                        kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00")) if kickoff_str else datetime.utcnow()
                        results.append(
                            Fixture(
                                fixture_id=str(m.get("id")),
                                competition_id=competition_id or m.get("competition", {}).get("code", "UNKNOWN"),
                                season=str(m.get("season", {}).get("startDate", "2026")[:4]),
                                kickoff_time=kickoff,
                                home_team_id=str(m.get("homeTeam", {}).get("id")),
                                home_team_name=home,
                                away_team_id=str(m.get("awayTeam", {}).get("id")),
                                away_team_name=away,
                                status=m.get("status", "SCHEDULED"),
                            )
                        )
                return results
        except Exception as exc:
            logger.error(f"Error resolving fixture on Football-Data.org: {exc}")
            return []

    def get_fixture_statistics(self, fixture_id: str) -> Optional[FixtureStatistics]:
        return None

    def get_team_history(self, team_id: str, limit: int = 15) -> List[Fixture]:
        return []

    def get_player_history(self, player_id: str, limit: int = 15) -> List[PlayerMatchStats]:
        return []

    def get_lineups_and_minutes(self, fixture_id: str) -> Optional[FixtureLineups]:
        return None
