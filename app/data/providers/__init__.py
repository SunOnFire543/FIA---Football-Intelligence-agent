from app.data.providers.base import BaseFootballDataProvider
from app.data.providers.demo_provider import DemoFootballDataProvider
from app.data.providers.football_data_org import FootballDataOrgProvider
from app.data.providers.api_football import APIFootballProvider
from app.config.settings import settings


def get_football_provider(provider_name: str | None = None) -> BaseFootballDataProvider:
    """Factory to retrieve configured or requested football data provider."""
    name = (provider_name or settings.football_data_provider).lower()
    if name == "football-data.org":
        provider = FootballDataOrgProvider()
        if provider.is_configured():
            return provider
    elif name == "api-football":
        provider = APIFootballProvider()
        if provider.is_configured():
            return provider

    # Default to high-fidelity demo provider
    return DemoFootballDataProvider()


__all__ = [
    "BaseFootballDataProvider",
    "DemoFootballDataProvider",
    "FootballDataOrgProvider",
    "APIFootballProvider",
    "get_football_provider",
]
