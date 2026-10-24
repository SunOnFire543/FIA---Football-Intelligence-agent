"""Incremental Ingestion Service for Football Intelligence Engine."""

from __future__ import annotations

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.data.providers.base import BaseFootballDataProvider
from app.db.models import DBCompetition, DBFixture, DBFixtureStatistics
from app.db.session import SessionLocal
from app.schemas.models import Fixture

logger = logging.getLogger(__name__)


class IngestionService:
    """Manages incremental ingestion and persistence of football data."""

    def __init__(self, provider: BaseFootballDataProvider, db_session: Optional[Session] = None):
        self.provider = provider
        self.db = db_session or SessionLocal()

    def ingest_fixtures(self, query: str, competition_id: Optional[str] = None) -> List[Fixture]:
        """Fetch fixtures from provider and upsert into database."""
        fixtures = self.provider.resolve_fixture(query, competition_id)
        for fix in fixtures:
            # Upsert into database
            existing = self.db.query(DBFixture).filter_by(id=fix.fixture_id).first()
            if existing:
                existing.status = fix.status
                existing.home_score = fix.home_score
                existing.away_score = fix.away_score
            else:
                db_fix = DBFixture(
                    id=fix.fixture_id,
                    competition_id=fix.competition_id,
                    season=fix.season,
                    kickoff_time=fix.kickoff_time,
                    home_team_id=fix.home_team_id,
                    home_team_name=fix.home_team_name,
                    away_team_id=fix.away_team_id,
                    away_team_name=fix.away_team_name,
                    status=fix.status,
                    venue=fix.venue,
                )
                self.db.add(db_fix)
        self.db.commit()
        return fixtures
