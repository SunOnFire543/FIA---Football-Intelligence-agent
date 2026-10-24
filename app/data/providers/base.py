"""Base interface for Football Data Providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.models import (
    CompetitionInfo,
    CoverageRecord,
    Fixture,
    FixtureLineups,
    FixtureStatistics,
    PlayerMatchStats,
)


class BaseFootballDataProvider(ABC):
    """Abstract interface that all football data adapters must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the data provider."""
        pass

    @abstractmethod
    def search_competitions(self, query: str) -> List[CompetitionInfo]:
        """Search available competitions by keyword or country."""
        pass

    @abstractmethod
    def inspect_competition_coverage(self, competition_id: str) -> Optional[CoverageRecord]:
        """Retrieve telemetry coverage and data depth for a competition."""
        pass

    @abstractmethod
    def resolve_fixture(
        self,
        query: str,
        competition_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> List[Fixture]:
        """Resolve upcoming or historical fixtures matching a query."""
        pass

    @abstractmethod
    def get_fixture_statistics(self, fixture_id: str) -> Optional[FixtureStatistics]:
        """Retrieve match-level event statistics for a fixture."""
        pass

    @abstractmethod
    def get_team_history(self, team_id: str, limit: int = 15) -> List[Fixture]:
        """Retrieve recent historical fixtures for a team."""
        pass

    @abstractmethod
    def get_player_history(self, player_id: str, limit: int = 15) -> List[PlayerMatchStats]:
        """Retrieve player appearances and event stats across recent matches."""
        pass

    @abstractmethod
    def get_lineups_and_minutes(self, fixture_id: str) -> Optional[FixtureLineups]:
        """Retrieve starting and bench lineups with participation flags."""
        pass
