"""Base interface for Odds Providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from app.schemas.models import BookmakerQuote


class BaseOddsProvider(ABC):
    """Abstract interface for bookmaker odds adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials are configured for live data."""
        pass

    @abstractmethod
    def get_current_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        """Retrieve current active bookmaker odds for a fixture."""
        pass

    @abstractmethod
    def get_historical_odds(self, fixture_id: str) -> List[BookmakerQuote]:
        """Retrieve historical odds observation timestamps and prices."""
        pass
