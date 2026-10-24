from app.odds.providers.base import BaseOddsProvider
from app.odds.providers.demo_odds_provider import DemoOddsProvider
from app.odds.providers.the_odds_api import TheOddsAPIProvider
from app.config.settings import settings


def get_odds_provider(provider_name: str | None = None) -> BaseOddsProvider:
    name = (provider_name or settings.odds_provider).lower()
    if name == "the-odds-api":
        provider = TheOddsAPIProvider()
        if provider.is_configured():
            return provider
    return DemoOddsProvider()


__all__ = [
    "BaseOddsProvider",
    "DemoOddsProvider",
    "TheOddsAPIProvider",
    "get_odds_provider",
]
