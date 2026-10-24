"""The Odds API Adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
import httpx

from app.config.settings import settings
from app.odds.providers.base import BaseOddsProvider
from app.schemas.enums import MarketType, SelectionOutcome
from app.schemas.models import BookmakerQuote

logger = logging.getLogger(__name__)


class TheOddsAPIProvider(BaseOddsProvider):
    """Adapter for The Odds API REST service."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.the_odds_api_key
        self.base_url = (base_url or settings.the_odds_api_base_url).rstrip("/")
        self._provider_name = "the-odds-api"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def get_current_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        if not self.is_configured():
            logger.info("The Odds API key not configured. Returning empty.")
            return []
        try:
            # Query EPL odds as default sport
            url = f"{self.base_url}/sports/soccer_epl/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,uk",
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"The Odds API returned HTTP {resp.status_code}")
                    return []
                data = resp.json()
                quotes: List[BookmakerQuote] = []
                for event in data:
                    for bm in event.get("bookmakers", []):
                        bm_name = bm.get("title", "Unknown")
                        for mkt in bm.get("markets", []):
                            mkt_key = mkt.get("key")
                            obs_time = datetime.utcnow()
                            if mkt_key == "h2h":
                                for outcome in mkt.get("outcomes", []):
                                    name = outcome.get("name", "")
                                    price = float(outcome.get("price", 1.0))
                                    sel = SelectionOutcome.HOME.value if name == event.get("home_team") else (
                                        SelectionOutcome.AWAY.value if name == event.get("away_team") else SelectionOutcome.DRAW.value
                                    )
                                    quotes.append(
                                        BookmakerQuote(
                                            bookmaker=bm_name,
                                            market=MarketType.MATCH_RESULT,
                                            selection=sel,
                                            decimal_odds=price,
                                            implied_probability=1.0 / price,
                                            observed_at=obs_time,
                                            is_live=True,
                                        )
                                    )
                return quotes
        except Exception as exc:
            logger.error(f"Error querying The Odds API: {exc}")
            return []

    def get_historical_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        return []
