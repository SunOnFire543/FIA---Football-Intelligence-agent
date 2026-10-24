"""High-Fidelity Deterministic Demo Football Data Provider.

Provides multi-season historical match logs, player events, lineups, and coverage
telemetry for offline testing, demos, and verification.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.data.providers.base import BaseFootballDataProvider
from app.schemas.enums import CoverageStatus
from app.schemas.models import (
    CompetitionInfo,
    CoverageRecord,
    Fixture,
    FixtureLineups,
    FixtureStatistics,
    LineupPlayer,
    PlayerMatchStats,
)


class DemoFootballDataProvider(BaseFootballDataProvider):
    """Deterministic provider with rich multi-season football data."""

    def __init__(self) -> None:
        self._provider_name = "demo"
        self._now = datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
        self._init_data()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def _init_data(self) -> None:
        # Competitions
        self.competitions = [
            CompetitionInfo(
                competition_id="PL",
                name="Premier League",
                country="England",
                division=1,
                provider=self._provider_name,
                seasons_available=["2022/23", "2023/24", "2024/25", "2025/26", "2026/27"],
            ),
            CompetitionInfo(
                competition_id="PD",
                name="La Liga",
                country="Spain",
                division=1,
                provider=self._provider_name,
                seasons_available=["2022/23", "2023/24", "2024/25", "2025/26", "2026/27"],
            ),
            CompetitionInfo(
                competition_id="CL",
                name="UEFA Champions League",
                country="Europe",
                is_cup=True,
                provider=self._provider_name,
                seasons_available=["2022/23", "2023/24", "2024/25", "2025/26", "2026/27"],
            ),
        ]

        # Coverage Records (5-Year Target)
        self.coverage_records: Dict[str, CoverageRecord] = {
            "PL": CoverageRecord(
                competition_id="PL",
                competition_name="Premier League",
                season="2026/27",
                provider=self._provider_name,
                status=CoverageStatus.AVAILABLE,
                has_match_events=True,
                has_lineups=True,
                has_shots_and_sot=True,
                has_cards_and_fouls=True,
                has_xg=True,
                has_historical_odds=True,
                has_live_odds=True,
                has_player_props=True,
                notes="Complete 5-year historical and current data verified for English Premier League.",
            ),
            "PD": CoverageRecord(
                competition_id="PD",
                competition_name="La Liga",
                season="2026/27",
                provider=self._provider_name,
                status=CoverageStatus.AVAILABLE,
                has_match_events=True,
                has_lineups=True,
                has_shots_and_sot=True,
                has_cards_and_fouls=True,
                has_xg=True,
                has_historical_odds=True,
                has_live_odds=True,
                has_player_props=True,
                notes="Complete 5-year coverage verified for Primera Division.",
            ),
            "CL": CoverageRecord(
                competition_id="CL",
                competition_name="UEFA Champions League",
                season="2026/27",
                provider=self._provider_name,
                status=CoverageStatus.PARTIAL,
                has_match_events=True,
                has_lineups=True,
                has_shots_and_sot=True,
                has_cards_and_fouls=True,
                has_xg=False,
                has_historical_odds=True,
                has_live_odds=True,
                has_player_props=False,
                notes="Cup format: Group & knockout stages covered. Player props uncalibrated.",
            ),
        }

        # Upcoming Fixtures
        self.upcoming_fixtures = [
            Fixture(
                fixture_id="FIX_ARS_CHE_2026",
                competition_id="PL",
                season="2026/27",
                kickoff_time=self._now + timedelta(days=1, hours=5),
                home_team_id="ARS",
                home_team_name="Arsenal FC",
                away_team_id="CHE",
                away_team_name="Chelsea FC",
                status="SCHEDULED",
                venue="Emirates Stadium, London",
            ),
            Fixture(
                fixture_id="FIX_MCI_LIV_2026",
                competition_id="PL",
                season="2026/27",
                kickoff_time=self._now + timedelta(days=2),
                home_team_id="MCI",
                home_team_name="Manchester City",
                away_team_id="LIV",
                away_team_name="Liverpool FC",
                status="SCHEDULED",
                venue="Etihad Stadium, Manchester",
            ),
            Fixture(
                fixture_id="FIX_RMA_BAR_2026",
                competition_id="PD",
                season="2026/27",
                kickoff_time=self._now + timedelta(days=2, hours=3),
                home_team_id="RMA",
                home_team_name="Real Madrid",
                away_team_id="BAR",
                away_team_name="FC Barcelona",
                status="SCHEDULED",
                venue="Santiago Bernabéu, Madrid",
            ),
        ]

        # Rich Historical Fixture Results (Last 15 matches for Arsenal and Chelsea)
        self.historical_fixtures: Dict[str, List[Fixture]] = {
            "ARS": [
                Fixture(
                    fixture_id=f"HIST_ARS_{i}",
                    competition_id="PL",
                    season="2026/27" if i < 8 else "2025/26",
                    kickoff_time=self._now - timedelta(days=7 * (i + 1)),
                    home_team_id="ARS" if i % 2 == 0 else f"OPP_{i}",
                    home_team_name="Arsenal FC" if i % 2 == 0 else f"Opponent {i}",
                    away_team_id=f"OPP_{i}" if i % 2 == 0 else "ARS",
                    away_team_name=f"Opponent {i}" if i % 2 == 0 else "Arsenal FC",
                    status="FINISHED",
                    home_score=2 if i % 3 != 0 else 3,
                    away_score=1 if i % 4 != 0 else 0,
                )
                for i in range(16)
            ],
            "CHE": [
                Fixture(
                    fixture_id=f"HIST_CHE_{i}",
                    competition_id="PL",
                    season="2026/27" if i < 8 else "2025/26",
                    kickoff_time=self._now - timedelta(days=7 * (i + 1)),
                    home_team_id="CHE" if i % 2 == 0 else f"OPP_C_{i}",
                    home_team_name="Chelsea FC" if i % 2 == 0 else f"Opponent C{i}",
                    away_team_id=f"OPP_C_{i}" if i % 2 == 0 else "CHE",
                    away_team_name=f"Opponent C{i}" if i % 2 == 0 else "Chelsea FC",
                    status="FINISHED",
                    home_score=1 if i % 2 == 0 else 2,
                    away_score=1 if i % 3 == 0 else 0,
                )
                for i in range(16)
            ],
        }

        # Lineups for upcoming Arsenal vs Chelsea
        self.lineups: Dict[str, FixtureLineups] = {
            "FIX_ARS_CHE_2026": FixtureLineups(
                fixture_id="FIX_ARS_CHE_2026",
                is_confirmed=True,
                home_starters=[
                    LineupPlayer(player_id="PL_ARS_1", name="David Raya", position="GK", is_starter=True, jersey_number=22),
                    LineupPlayer(player_id="PL_ARS_2", name="William Saliba", position="DEF", is_starter=True, jersey_number=2),
                    LineupPlayer(player_id="PL_ARS_3", name="Gabriel Magalhaes", position="DEF", is_starter=True, jersey_number=6),
                    LineupPlayer(player_id="PL_ARS_4", name="Declan Rice", position="MID", is_starter=True, jersey_number=41),
                    LineupPlayer(player_id="PL_ARS_5", name="Martin Ødegaard", position="MID", is_starter=True, jersey_number=8),
                    LineupPlayer(player_id="PL_ARS_6", name="Bukayo Saka", position="FWD", is_starter=True, jersey_number=7),
                    LineupPlayer(player_id="PL_ARS_7", name="Kai Havertz", position="FWD", is_starter=True, jersey_number=29),
                    LineupPlayer(player_id="PL_ARS_8", name="Gabriel Martinelli", position="FWD", is_starter=True, jersey_number=11),
                ],
                away_starters=[
                    LineupPlayer(player_id="PL_CHE_1", name="Robert Sanchez", position="GK", is_starter=True, jersey_number=1),
                    LineupPlayer(player_id="PL_CHE_2", name="Levi Colwill", position="DEF", is_starter=True, jersey_number=6),
                    LineupPlayer(player_id="PL_CHE_3", name="Moises Caicedo", position="MID", is_starter=True, jersey_number=25),
                    LineupPlayer(player_id="PL_CHE_4", name="Enzo Fernandez", position="MID", is_starter=True, jersey_number=8),
                    LineupPlayer(player_id="PL_CHE_5", name="Cole Palmer", position="MID", is_starter=True, jersey_number=20),
                    LineupPlayer(player_id="PL_CHE_6", name="Nicolas Jackson", position="FWD", is_starter=True, jersey_number=15),
                ],
                source_timestamp=self._now - timedelta(hours=2),
            )
        }

        # Player Historical Event Statistics (e.g. Bukayo Saka)
        self.player_stats: Dict[str, List[PlayerMatchStats]] = {
            "PL_ARS_6": [  # Bukayo Saka
                PlayerMatchStats(
                    player_id="PL_ARS_6",
                    player_name="Bukayo Saka",
                    fixture_id=f"HIST_ARS_{i}",
                    team_id="ARS",
                    minutes_played=88 if i % 6 != 0 else 72,
                    is_starter=True,
                    goals=1 if i in (1, 4, 7, 9) else 0,
                    assists=1 if i in (0, 3, 8) else 0,
                    shots=3 if i % 2 == 0 else 2,
                    shots_on_target=2 if i % 3 != 0 else 1,
                    fouls_committed=1 if i % 2 == 0 else 0,
                    yellow_cards=1 if i == 5 else 0,
                )
                for i in range(15)
            ],
            "PL_ARS_7": [  # Kai Havertz
                PlayerMatchStats(
                    player_id="PL_ARS_7",
                    player_name="Kai Havertz",
                    fixture_id=f"HIST_ARS_{i}",
                    team_id="ARS",
                    minutes_played=85,
                    is_starter=True,
                    goals=1 if i in (2, 5, 8) else 0,
                    assists=0,
                    shots=2,
                    shots_on_target=1,
                    fouls_committed=2,
                    yellow_cards=1 if i in (3, 10) else 0,
                )
                for i in range(15)
            ],
            "PL_CHE_5": [  # Cole Palmer
                PlayerMatchStats(
                    player_id="PL_CHE_5",
                    player_name="Cole Palmer",
                    fixture_id=f"HIST_CHE_{i}",
                    team_id="CHE",
                    minutes_played=90,
                    is_starter=True,
                    goals=1 if i in (0, 2, 6, 11) else 0,
                    assists=1 if i in (1, 4) else 0,
                    shots=3,
                    shots_on_target=2 if i % 2 == 0 else 1,
                    fouls_committed=1,
                    yellow_cards=0,
                )
                for i in range(15)
            ],
        }

        # Match Event Statistics
        self.fixture_statistics: Dict[str, FixtureStatistics] = {
            "FIX_ARS_CHE_2026": FixtureStatistics(
                fixture_id="FIX_ARS_CHE_2026",
                home_shots=14,
                away_shots=9,
                home_shots_on_target=6,
                away_shots_on_target=3,
                home_corners=7,
                away_corners=4,
                home_fouls=10,
                away_fouls=12,
                home_yellow_cards=1,
                away_yellow_cards=3,
                home_possession_pct=58.2,
                away_possession_pct=41.8,
                home_xg=1.85,
                away_xg=0.92,
            )
        }

    def search_competitions(self, query: str) -> List[CompetitionInfo]:
        q = query.lower().strip()
        return [c for c in self.competitions if q in c.name.lower() or q in c.country.lower() or q in c.competition_id.lower()]

    def inspect_competition_coverage(self, competition_id: str) -> Optional[CoverageRecord]:
        return self.coverage_records.get(competition_id.upper())

    def resolve_fixture(
        self,
        query: str,
        competition_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> List[Fixture]:
        q = query.lower().strip()
        matches = []
        for fix in self.upcoming_fixtures:
            if competition_id and fix.competition_id != competition_id.upper():
                continue
            if (
                q in fix.home_team_name.lower()
                or q in fix.away_team_name.lower()
                or q in fix.fixture_id.lower()
                or (q in "arsenal" and "arsenal" in fix.home_team_name.lower())
                or (q in "chelsea" and "chelsea" in fix.away_team_name.lower())
            ):
                matches.append(fix)
        return matches

    def get_fixture_statistics(self, fixture_id: str) -> Optional[FixtureStatistics]:
        return self.fixture_statistics.get(fixture_id)

    def get_team_history(self, team_id: str, limit: int = 15) -> List[Fixture]:
        return self.historical_fixtures.get(team_id.upper(), [])[:limit]

    def get_player_history(self, player_id: str, limit: int = 15) -> List[PlayerMatchStats]:
        return self.player_stats.get(player_id, [])[:limit]

    def get_lineups_and_minutes(self, fixture_id: str) -> Optional[FixtureLineups]:
        return self.lineups.get(fixture_id)
