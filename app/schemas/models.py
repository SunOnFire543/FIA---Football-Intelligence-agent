"""Typed domain models and schemas for Football Intelligence Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.enums import (
    CoverageStatus,
    MarketType,
    ModelStatus,
    ParlayType,
    SelectionOutcome,
    SourceCategory,
    VerificationStatus,
)


# -----------------------------------------------------------------------------
# Core Football Domain Models
# -----------------------------------------------------------------------------

class CompetitionInfo(BaseModel):
    """Football competition / league metadata."""
    competition_id: str
    name: str
    country: str
    division: int = 1
    is_cup: bool = False
    provider: str
    seasons_available: List[str] = Field(default_factory=list)


class TeamInfo(BaseModel):
    """Team details."""
    team_id: str
    name: str
    short_name: Optional[str] = None
    competition_id: str
    stadium: Optional[str] = None


class PlayerInfo(BaseModel):
    """Player details."""
    player_id: str
    name: str
    team_id: str
    position: str  # GK, DEF, MID, FWD
    squad_number: Optional[int] = None
    nationality: Optional[str] = None


class Fixture(BaseModel):
    """Football match fixture."""
    fixture_id: str
    competition_id: str
    season: str
    kickoff_time: datetime
    home_team_id: str
    home_team_name: str
    away_team_id: str
    away_team_name: str
    status: str = "SCHEDULED"  # SCHEDULED, LIVE, FINISHED, POSTPONED
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None


class FixtureStatistics(BaseModel):
    """Aggregated match statistics for finished or in-play matches."""
    fixture_id: str
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    home_possession_pct: Optional[float] = None
    away_possession_pct: Optional[float] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None


class PlayerMatchStats(BaseModel):
    """Player-level match performance statistics."""
    player_id: str
    player_name: str
    fixture_id: str
    team_id: str
    minutes_played: int
    is_starter: bool
    goals: int = 0
    assists: int = 0
    shots: int = 0
    shots_on_target: int = 0
    fouls_committed: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class LineupPlayer(BaseModel):
    """Individual player in a match lineup."""
    player_id: str
    name: str
    position: str
    is_starter: bool
    jersey_number: Optional[int] = None


class FixtureLineups(BaseModel):
    """Lineup confirmation for a fixture."""
    fixture_id: str
    is_confirmed: bool = False
    home_starters: List[LineupPlayer] = Field(default_factory=list)
    home_bench: List[LineupPlayer] = Field(default_factory=list)
    away_starters: List[LineupPlayer] = Field(default_factory=list)
    away_bench: List[LineupPlayer] = Field(default_factory=list)
    source_timestamp: Optional[datetime] = None


# -----------------------------------------------------------------------------
# Coverage Tracking
# -----------------------------------------------------------------------------

class CoverageRecord(BaseModel):
    """Explicit coverage tracking for competitions, seasons, and markets."""
    competition_id: str
    competition_name: str
    season: str
    provider: str
    status: CoverageStatus
    has_match_events: bool = False
    has_lineups: bool = False
    has_shots_and_sot: bool = False
    has_cards_and_fouls: bool = False
    has_xg: bool = False
    has_historical_odds: bool = False
    has_live_odds: bool = False
    has_player_props: bool = False
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Odds & Market Domain Models
# -----------------------------------------------------------------------------

class BookmakerQuote(BaseModel):
    """Individual bookmaker odds quote for a selection."""
    bookmaker: str
    market: MarketType
    selection: str              # e.g., "HOME", "OVER", "Bukayo Saka"
    threshold: Optional[float] = None  # e.g. 2.5 for Over 2.5 Goals, 1.5 for SOT
    decimal_odds: float
    implied_probability: float  # 1 / decimal_odds
    observed_at: datetime
    is_live: bool = False
    is_suspended: bool = False


class MarketOddsComparison(BaseModel):
    """Normalized comparison across multiple bookmakers for equivalent selection."""
    fixture_id: str
    market: MarketType
    selection: str
    threshold: Optional[float] = None
    best_decimal_odds: float
    best_bookmaker: str
    all_quotes: List[BookmakerQuote] = Field(default_factory=list)
    fair_market_probability: Optional[float] = None  # Vig-removed market probability
    observed_at: datetime


# -----------------------------------------------------------------------------
# Statistical Modeling & Predictions
# -----------------------------------------------------------------------------

class SelectionPrediction(BaseModel):
    """Model-derived probability and statistical assessment for an individual selection."""
    market: MarketType
    selection: str
    threshold: Optional[float] = None
    estimated_probability: float
    model_name: str
    model_version: str
    model_status: ModelStatus
    historical_samples_used: int
    uncertainty_score: float = 0.0  # 0.0 (low uncertainty) to 1.0 (high uncertainty)
    notes: Optional[str] = None


class MatchPredictionSummary(BaseModel):
    """Comprehensive match prediction output."""
    fixture_id: str
    home_team: str
    away_team: str
    kickoff_time: datetime
    lambda_home: float            # Expected goals home
    mu_away: float                # Expected goals away
    rho_dixon_coles: float        # Correlation parameter
    predictions: List[SelectionPrediction] = Field(default_factory=list)
    score_matrix: Optional[Dict[str, float]] = None  # key: "x-y", val: prob
    model_status: ModelStatus = ModelStatus.SUPPORTED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValueOpportunity(BaseModel):
    """Assessed statistical edge / expected value on a selection."""
    fixture_id: str
    fixture_label: str
    market: MarketType
    selection: str
    threshold: Optional[float] = None
    model_probability: float
    best_odds: float
    bookmaker: str
    expected_value: float          # p * Odds - 1
    is_positive_ev: bool
    odds_observed_at: datetime
    model_uncertainty: float
    coverage_status: CoverageStatus


# -----------------------------------------------------------------------------
# Parlay Intelligence
# -----------------------------------------------------------------------------

class ParlayLeg(BaseModel):
    """A single selection within a parlay."""
    leg_index: int
    fixture_id: str
    fixture_label: str
    market: MarketType
    selection: str
    threshold: Optional[float] = None
    leg_win_probability: float
    best_individual_odds: Optional[float] = None
    best_bookmaker: Optional[str] = None
    is_same_match_with_prev: bool = False
    evidence_notes: str = ""


class ParlayCandidate(BaseModel):
    """5-leg or 10-leg parlay recommendation."""
    candidate_id: str
    parlay_type: ParlayType
    leg_count: int  # Must be exactly 5 or 10
    legs: List[ParlayLeg]
    combined_odds: float
    is_quote_verified: bool       # True if verified bookmaker combined quote, False if theoretical product
    quote_bookmaker: str
    joint_probability: float      # Accounted for same-match correlation where applicable
    expected_value: Optional[float] = None
    screening_confidence: float   # Minimum leg probability or composite score
    key_uncertainties: List[str] = Field(default_factory=list)
    evidence_summary: str
    is_recommended: bool = True
    abstention_reason: Optional[str] = None


# -----------------------------------------------------------------------------
# Verification & Evidence Record
# -----------------------------------------------------------------------------

class WebSourceEvidence(BaseModel):
    """Traceable, categorized web source with quality score and freshness audit."""
    url: str
    title: Optional[str] = None
    publisher: Optional[str] = None
    domain: str
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    claim_supported: str
    category: SourceCategory = SourceCategory.SECONDARY_REPORTING
    verification_status: VerificationStatus = VerificationStatus.REPORTED
    freshness_warning: Optional[str] = None
    inline_reference_id: Optional[str] = None  # e.g. "[1]"


class WebResearchRecord(BaseModel):
    """Container for a selective web research query and its corroborated findings."""
    query: str
    search_reason: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    sources: List[WebSourceEvidence] = Field(default_factory=list)
    summary: str = ""
    material_conflicts: List[str] = Field(default_factory=list)


class CompactEvidenceRecord(BaseModel):
    """Tamper-evident audit trail linking predictions to factual records."""
    record_id: str
    fixture_id: str
    competition_id: str
    prediction_timestamp: datetime
    data_cutoff_timestamp: datetime
    model_version: str
    selections_evaluated: List[str]
    source_providers: List[str]
    odds_sources: List[str]
    coverage_status: CoverageStatus
    verification_passed: bool
    verification_warnings: List[str] = Field(default_factory=list)
    web_sources: List[WebSourceEvidence] = Field(default_factory=list)
    research_records: List[WebResearchRecord] = Field(default_factory=list)


class AgentExecutionPlan(BaseModel):
    """Structured plan generated by Grok before tool execution."""
    intent: str
    target_competitions: List[str] = Field(default_factory=list)
    target_teams: List[str] = Field(default_factory=list)
    target_fixtures: List[str] = Field(default_factory=list)
    required_markets: List[MarketType] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    parlays_requested: bool = False
    execution_steps: List[str] = Field(default_factory=list)
