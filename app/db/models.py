"""SQLAlchemy database models for persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DBCompetition(Base):
    """Competition entity."""
    __tablename__ = "competitions"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, index=True)
    country = Column(String(64), nullable=False)
    division = Column(Integer, default=1)
    is_cup = Column(Boolean, default=False)
    provider = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teams = relationship("DBTeam", back_populates="competition")
    fixtures = relationship("DBFixture", back_populates="competition")


class DBTeam(Base):
    """Team entity."""
    __tablename__ = "teams"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, index=True)
    short_name = Column(String(32), nullable=True)
    competition_id = Column(String(64), ForeignKey("competitions.id"), nullable=False)
    stadium = Column(String(128), nullable=True)

    competition = relationship("DBCompetition", back_populates="teams")
    players = relationship("DBPlayer", back_populates="team")


class DBPlayer(Base):
    """Player entity."""
    __tablename__ = "players"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False, index=True)
    team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    position = Column(String(16), nullable=False)  # GK, DEF, MID, FWD
    squad_number = Column(Integer, nullable=True)
    nationality = Column(String(64), nullable=True)

    team = relationship("DBTeam", back_populates="players")


class DBFixture(Base):
    """Fixture entity."""
    __tablename__ = "fixtures"

    id = Column(String(64), primary_key=True)
    competition_id = Column(String(64), ForeignKey("competitions.id"), nullable=False, index=True)
    season = Column(String(16), nullable=False, index=True)
    kickoff_time = Column(DateTime, nullable=False, index=True)
    home_team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    home_team_name = Column(String(128), nullable=False)
    away_team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    away_team_name = Column(String(128), nullable=False)
    status = Column(String(32), default="SCHEDULED")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    venue = Column(String(128), nullable=True)

    competition = relationship("DBCompetition", back_populates="fixtures")
    statistics = relationship("DBFixtureStatistics", back_populates="fixture", uselist=False)
    odds = relationship("DBBookmakerOdds", back_populates="fixture")


class DBFixtureStatistics(Base):
    """Match statistics entity."""
    __tablename__ = "fixture_statistics"

    fixture_id = Column(String(64), ForeignKey("fixtures.id"), primary_key=True)
    home_shots = Column(Integer, default=0)
    away_shots = Column(Integer, default=0)
    home_shots_on_target = Column(Integer, default=0)
    away_shots_on_target = Column(Integer, default=0)
    home_corners = Column(Integer, default=0)
    away_corners = Column(Integer, default=0)
    home_fouls = Column(Integer, default=0)
    away_fouls = Column(Integer, default=0)
    home_yellow_cards = Column(Integer, default=0)
    away_yellow_cards = Column(Integer, default=0)
    home_red_cards = Column(Integer, default=0)
    away_red_cards = Column(Integer, default=0)
    home_possession_pct = Column(Float, nullable=True)
    away_possession_pct = Column(Float, nullable=True)
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)

    fixture = relationship("DBFixture", back_populates="statistics")


class DBPlayerMatchStats(Base):
    """Player performance stats in a fixture."""
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String(64), ForeignKey("players.id"), nullable=False, index=True)
    fixture_id = Column(String(64), ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(String(64), nullable=False)
    minutes_played = Column(Integer, default=0)
    is_starter = Column(Boolean, default=False)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)


class DBBookmakerOdds(Base):
    """Bookmaker odds quote entity."""
    __tablename__ = "bookmaker_odds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id = Column(String(64), ForeignKey("fixtures.id"), nullable=False, index=True)
    bookmaker = Column(String(64), nullable=False, index=True)
    market = Column(String(64), nullable=False, index=True)
    selection = Column(String(64), nullable=False, index=True)
    threshold = Column(Float, nullable=True)
    decimal_odds = Column(Float, nullable=False)
    observed_at = Column(DateTime, nullable=False, index=True)
    is_live = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)

    fixture = relationship("DBFixture", back_populates="odds")


class DBCoverageRecord(Base):
    """Competition coverage metadata entity."""
    __tablename__ = "coverage_records"

    id = Column(String(128), primary_key=True)  # competition_id:season:provider
    competition_id = Column(String(64), nullable=False, index=True)
    competition_name = Column(String(128), nullable=False)
    season = Column(String(16), nullable=False)
    provider = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    has_match_events = Column(Boolean, default=False)
    has_lineups = Column(Boolean, default=False)
    has_shots_and_sot = Column(Boolean, default=False)
    has_cards_and_fouls = Column(Boolean, default=False)
    has_xg = Column(Boolean, default=False)
    has_historical_odds = Column(Boolean, default=False)
    has_live_odds = Column(Boolean, default=False)
    has_player_props = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)


class DBEvidenceRecord(Base):
    """Audit and provenance record entity."""
    __tablename__ = "evidence_records"

    record_id = Column(String(64), primary_key=True)
    fixture_id = Column(String(64), nullable=False, index=True)
    competition_id = Column(String(64), nullable=False)
    prediction_timestamp = Column(DateTime, nullable=False)
    data_cutoff_timestamp = Column(DateTime, nullable=False)
    model_version = Column(String(32), nullable=False)
    payload_json = Column(Text, nullable=False)
    verification_passed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
