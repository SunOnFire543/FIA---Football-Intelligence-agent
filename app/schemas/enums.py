"""Enumerations for Football Intelligence Engine."""

from enum import Enum


class CoverageStatus(str, Enum):
    """Data availability and coverage states."""
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_VERIFIED = "NOT_VERIFIED"
    STALE = "STALE"


class MarketType(str, Enum):
    """Supported betting and analytics markets."""
    MATCH_RESULT = "MATCH_RESULT"              # 1X2 (Home Win, Draw, Away Win)
    DOUBLE_CHANCE = "DOUBLE_CHANCE"            # 1X, 12, X2
    BOTH_TEAMS_TO_SCORE = "BOTH_TEAMS_TO_SCORE"# BTTS (Yes, No)
    OVER_UNDER_GOALS = "OVER_UNDER_GOALS"      # Over/Under total goals (e.g. 1.5, 2.5, 3.5)
    TEAM_TOTAL_GOALS = "TEAM_TOTAL_GOALS"      # Over/Under team goals
    EXACT_SCORE = "EXACT_SCORE"                # e.g. 1-0, 2-1, 0-0
    PLAYER_SHOTS = "PLAYER_SHOTS"              # Over/Under player total shots
    PLAYER_SHOTS_ON_TARGET = "PLAYER_SHOTS_ON_TARGET" # Over/Under player SOT
    ANYTIME_GOALSCORER = "ANYTIME_GOALSCORER"  # Player to score
    TOTAL_CORNERS = "TOTAL_CORNERS"            # Over/Under total corners
    TOTAL_CARDS = "TOTAL_CARDS"                # Over/Under yellow/red cards
    TOTAL_FOULS = "TOTAL_FOULS"                # Over/Under match fouls


class ModelStatus(str, Enum):
    """Statistical model readiness and validity statuses."""
    SUPPORTED = "SUPPORTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    MISSING_INPUTS = "MISSING_INPUTS"
    UNCALIBRATED = "UNCALIBRATED"
    OUT_OF_DISTRIBUTION = "OUT_OF_DISTRIBUTION"
    UNAVAILABLE = "UNAVAILABLE"


class SelectionOutcome(str, Enum):
    """Standard outcome tokens for settlement and normalisation."""
    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"
    HOME_OR_DRAW = "1X"
    HOME_OR_AWAY = "12"
    DRAW_OR_AWAY = "X2"
    YES = "YES"
    NO = "NO"
    OVER = "OVER"
    UNDER = "UNDER"


class ParlayType(str, Enum):
    """Parlay structure classifications."""
    SAME_MATCH = "SAME_MATCH"
    MULTI_MATCH = "MULTI_MATCH"
    HYBRID = "HYBRID"


class SourceCategory(str, Enum):
    """Source quality and authority tier."""
    OFFICIAL_ANNOUNCEMENT = "OFFICIAL_ANNOUNCEMENT"  # Official league, federation, club, or competition
    LICENSED_DATA = "LICENSED_DATA"                  # Licensed / documented statistical providers
    ESTABLISHED_DATABASE = "ESTABLISHED_DATABASE"    # Established databases and reputable sports publications
    SECONDARY_REPORTING = "SECONDARY_REPORTING"      # Secondary sports reporting / general media
    UNVERIFIED_COMMUNITY = "UNVERIFIED_COMMUNITY"    # Social media, fan forums (requires corroboration)


class VerificationStatus(str, Enum):
    """Evidence verification and corroboration state."""
    CONFIRMED = "CONFIRMED"            # Officially confirmed by club/league or verified by multi-source consensus
    REPORTED = "REPORTED"              # Reputable secondary report; not yet official
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"  # Parameter assumption / prior
    UNVERIFIED = "UNVERIFIED"          # Uncorroborated single source
    UNAVAILABLE = "UNAVAILABLE"        # Fact explicitly investigated and found unavailable

