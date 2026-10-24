"""Agentverse & ASI:One Discoverability Manifest."""

from __future__ import annotations

import json
from typing import Any, Dict
from pydantic import BaseModel, Field

from app.config.settings import settings


class AgentDiscoverabilityManifest(BaseModel):
    """Manifest describing agent capabilities, protocols, and endpoints for ASI:One."""
    name: str = "FootballIntelligenceAgent"
    version: str = "1.0.0"
    description: str = (
        "Grok-powered Football Analytics and Odds Intelligence Agent. "
        "Provides probabilistic Dixon-Coles goal modeling, multi-bookmaker odds comparison, "
        "statistical expected value (EV), and 5-leg & 10-leg parlay intelligence."
    )
    protocols: list[str] = Field(default_factory=lambda: [
        "agent-chat-protocol/v1",
        "uagents/v1",
    ])
    supported_competitions: list[str] = Field(default_factory=lambda: [
        "Premier League (PL)",
        "La Liga (PD)",
        "UEFA Champions League (CL)",
    ])
    supported_markets: list[str] = Field(default_factory=lambda: [
        "Match Result (1X2)",
        "Double Chance",
        "Over / Under Total Goals (0.5 to 4.5)",
        "Both Teams To Score (BTTS)",
        "Player Shots & Shots On Target (SOT)",
        "Anytime Goalscorer",
        "Total Match Corners",
        "Total Cards & Fouls",
    ])
    endpoints: Dict[str, str] = Field(default_factory=lambda: {
        "acp": "/acp/message",
        "health": "/health",
    })

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def get_agent_manifest() -> AgentDiscoverabilityManifest:
    return AgentDiscoverabilityManifest(name=settings.agent_name)
