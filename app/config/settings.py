"""Application Settings and Environment Configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Automatically load .env if present
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings(BaseModel):
    """Central configuration for Football Intelligence Engine."""

    # xAI / Grok Configuration
    xai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("XAI_API_KEY"))
    xai_model: str = Field(default_factory=lambda: os.getenv("XAI_MODEL", "grok-4.7"))
    xai_base_url: str = Field(default_factory=lambda: os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"))
    xai_timeout_seconds: float = Field(default_factory=lambda: float(os.getenv("XAI_TIMEOUT_SECONDS", "60.0")))
    xai_max_tool_rounds: int = Field(default_factory=lambda: int(os.getenv("XAI_MAX_TOOL_ROUNDS", "8")))

    # Football Data Provider Configuration
    football_data_provider: str = Field(default_factory=lambda: os.getenv("FOOTBALL_DATA_PROVIDER", "demo"))
    football_data_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("FOOTBALL_DATA_API_KEY"))
    football_data_base_url: str = Field(default_factory=lambda: os.getenv("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4"))
    api_football_key: Optional[str] = Field(default_factory=lambda: os.getenv("API_FOOTBALL_KEY"))
    api_football_host: str = Field(default_factory=lambda: os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io"))

    # Odds Provider Configuration
    odds_provider: str = Field(default_factory=lambda: os.getenv("ODDS_PROVIDER", "demo"))
    the_odds_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("THE_ODDS_API_KEY"))
    the_odds_api_base_url: str = Field(default_factory=lambda: os.getenv("THE_ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4"))

    # Fetch.ai / Agentverse / ASI:One Configuration
    agentverse_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("AGENTVERSE_API_KEY"))
    agent_name: str = Field(default_factory=lambda: os.getenv("AGENT_NAME", "FootballIntelligenceAgent"))
    agent_seed: Optional[str] = Field(default_factory=lambda: os.getenv("AGENT_SEED", "football_intelligence_seed_phrase"))
    agent_port: int = Field(default_factory=lambda: int(os.getenv("AGENT_PORT", "8000")))
    agent_endpoint: str = Field(default_factory=lambda: os.getenv("AGENT_ENDPOINT", "http://127.0.0.1:8000/submit"))

    # Storage & Persistence
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/football_intel.db"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Statistical & Parlay Modeling Hyperparameters
    min_historical_matches: int = Field(default_factory=lambda: int(os.getenv("MIN_HISTORICAL_MATCHES", "10")))
    default_dixon_coles_rho: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_DIXON_COLES_RHO", "-0.08")))
    parlay_5_leg_min_prob: float = Field(default_factory=lambda: float(os.getenv("PARLAY_5_LEG_MIN_PROB", "0.70")))
    parlay_10_leg_min_prob: float = Field(default_factory=lambda: float(os.getenv("PARLAY_10_LEG_MIN_PROB", "0.60")))
    max_parlay_legs: int = Field(default_factory=lambda: int(os.getenv("MAX_PARLAY_LEGS", "10")))

    # Security: Ensure sensitive fields are never printed or leaked in str() or repr()
    def get_masked_api_key(self, key_name: str) -> str:
        val = getattr(self, key_name, None)
        if not val:
            return "<UNSET>"
        if len(val) <= 8:
            return "***"
        return f"{val[:3]}...{val[-4:]}"


# Global singleton instance
settings = Settings()
