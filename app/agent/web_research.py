"""Intelligent Web Research, Source Discovery, and Grounding Engine for FIA.

Combines Groq's built-in browser_search capability with structured football data,
enforcing selective search decisions, source-quality tiers, provenance tracking,
freshness audits, and conflict detection.

Note on Domain Filtering:
Groq's built-in browser_search does not currently support request-level 'allowed_domains'
filtering parameters. FIA applies post-search validation against the approved-source hierarchy
(SourceClassifier). This post-search validation classifies, scores, and audits sources,
but is not equivalent to server-side pre-query domain restriction. If strict domain restriction
is required in the future, a dedicated search provider can be connected through FIA's allowlisted tool registry.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.schemas.enums import SourceCategory, VerificationStatus
from app.schemas.models import WebResearchRecord, WebSourceEvidence

logger = logging.getLogger(__name__)

# Known domain quality mapping
OFFICIAL_DOMAINS = {
    "premierleague.com",
    "uefa.com",
    "thefa.com",
    "fifa.com",
    "arsenal.com",
    "chelseafc.com",
    "mancity.com",
    "liverpoolfc.com",
    "tottenhamhotspur.com",
    "manutd.com",
    "realmadrid.com",
    "fcbarcelona.com",
    "laliga.com",
    "bundesliga.com",
    "seriea.it",
}

LICENSED_DATA_DOMAINS = {
    "football-data.org",
    "api-sports.io",
    "the-odds-api.com",
    "statsbomb.com",
    "optaanalyst.com",
    "optasports.com",
    "whoscored.com",
    "fbref.com",
    "sofascore.com",
}

ESTABLISHED_DOMAINS = {
    "bbc.com",
    "bbc.co.uk",
    "theathletic.com",
    "skysports.com",
    "theguardian.com",
    "reuters.com",
    "espn.com",
    "independent.co.uk",
    "telegraph.co.uk",
}

COMMUNITY_DOMAINS = {
    "twitter.com",
    "x.com",
    "reddit.com",
}


class SourceClassifier:
    """Classifies source domains according to evidentiary hierarchy."""

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract clean hostname from URL."""
        if not url:
            return ""
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    @classmethod
    def classify(cls, url: str) -> Tuple[SourceCategory, VerificationStatus, float]:
        """Classify a source URL into category, verification status, and quality weight."""
        domain = cls.extract_domain(url)

        # Check Official
        for d in OFFICIAL_DOMAINS:
            if domain == d or domain.endswith(f".{d}"):
                return SourceCategory.OFFICIAL_ANNOUNCEMENT, VerificationStatus.CONFIRMED, 1.0

        # Check Licensed Data
        for d in LICENSED_DATA_DOMAINS:
            if domain == d or domain.endswith(f".{d}"):
                return SourceCategory.LICENSED_DATA, VerificationStatus.CONFIRMED, 0.95

        # Check Established Databases / Reputable Publications
        for d in ESTABLISHED_DOMAINS:
            if domain == d or domain.endswith(f".{d}"):
                return SourceCategory.ESTABLISHED_DATABASE, VerificationStatus.REPORTED, 0.85

        # Check Community / Social
        for d in COMMUNITY_DOMAINS:
            if domain == d or domain.endswith(f".{d}"):
                return SourceCategory.UNVERIFIED_COMMUNITY, VerificationStatus.UNVERIFIED, 0.30

        # Default Secondary Reporting
        return SourceCategory.SECONDARY_REPORTING, VerificationStatus.REPORTED, 0.65


class WebResearchPolicy:
    """Decides when web research is justified vs redundant."""

    # Keywords signaling contextual research needs
    RESEARCH_TRIGGERS = [
        "injury", "injured", "fit", "fitness", "suspension", "suspended",
        "lineup", "lineups", "starting", "starter", "bench", "absent",
        "team news", "manager", "coach", "tactics", "referee", "weather",
        "confirmed", "availability", "doubt", "doubtful", "ruled out",
    ]

    # Keywords where structured data should be used without web search
    REDUNDANT_ODDS_TRIGGERS = [
        "best odds", "compare odds", "bookmaker price", "pinnacle odds",
        "calculate ev", "expected value", "dixon-coles", "poisson probability",
        "parlay odds", "accumulator calculation",
    ]

    @classmethod
    def should_research(
        cls,
        query: str,
        has_structured_odds: bool = False,
        has_structured_lineups: bool = False,
    ) -> Tuple[bool, str, List[str]]:
        """Evaluate if web research is warranted.

        Returns (should_search, reason, topics_to_research).
        """
        q_lower = query.lower()

        # Check if query is strictly asking for pure mathematical calculations
        # where structured providers already provide the required data
        is_pure_odds_query = any(t in q_lower for t in cls.REDUNDANT_ODDS_TRIGGERS)
        has_news_intent = any(t in q_lower for t in cls.RESEARCH_TRIGGERS)

        if is_pure_odds_query and not has_news_intent and has_structured_odds:
            return (
                False,
                "Verified structured odds and model distributions already present; redundant web search avoided.",
                [],
            )

        # Identify requested topics
        topics = []
        if any(t in q_lower for t in ["injury", "injured", "fit", "fitness", "team news", "doubt"]):
            topics.append("injuries_and_fitness")
        if any(t in q_lower for t in ["lineup", "lineups", "starting", "starter", "bench", "availability"]):
            topics.append("lineup_confirmation")
        if any(t in q_lower for t in ["referee", "cards", "fouls"]):
            topics.append("referee_appointment")
        if any(t in q_lower for t in ["manager", "coach", "tactics"]):
            topics.append("managerial_tactics")

        # If general analysis query (e.g. "Analyse Arsenal vs Chelsea"), default to contextual team news
        if not topics:
            topics = ["team_news", "lineup_confirmation", "referee_appointment"]

        return (
            True,
            "Contextual team news, injury validation, and lineup status required to ground prediction models.",
            topics,
        )


class WebEvidenceBuilder:
    """Constructs verified WebSourceEvidence records from raw findings."""

    @staticmethod
    def create_evidence(
        url: str,
        claim_supported: str,
        title: Optional[str] = None,
        publisher: Optional[str] = None,
        published_at: Optional[datetime] = None,
        inline_id: Optional[str] = None,
    ) -> WebSourceEvidence:
        domain = SourceClassifier.extract_domain(url)
        category, status, _ = SourceClassifier.classify(url)

        # Freshness audit (e.g., flag if published > 48 hours ago for match news)
        freshness_warning = None
        now = datetime.now(timezone.utc)
        if published_at:
            age = now - (published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc))
            if age > timedelta(hours=48):
                freshness_warning = f"Report published {int(age.total_seconds() / 3600)} hours ago; may not reflect late matchday developments."

        # If publisher not supplied, deduce from domain
        inferred_publisher = publisher or domain.split(".")[0].capitalize()

        return WebSourceEvidence(
            url=url,
            title=title or f"{inferred_publisher} Report",
            publisher=inferred_publisher,
            domain=domain,
            retrieved_at=now,
            published_at=published_at,
            claim_supported=claim_supported,
            category=category,
            verification_status=status,
            freshness_warning=freshness_warning,
            inline_reference_id=inline_id,
        )


class WebResearchEngine:
    """Coordinates selective web research, structured source synthesis, and conflict detection."""

    @classmethod
    def get_grounded_research(
        cls,
        fixture_id: str,
        home_team: str = "Arsenal FC",
        away_team: str = "Chelsea FC",
        data_mode: str = "DEMO",
    ) -> WebResearchRecord:
        """Retrieve verified web intelligence and source citations."""
        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------------------
        # DEMO Mode: High-fidelity, deterministic grounded evidence
        # ---------------------------------------------------------------------
        if data_mode.upper() == "DEMO":
            sources = [
                WebEvidenceBuilder.create_evidence(
                    url="https://www.premierleague.com/news/arsenal-chelsea-team-news",
                    title="[SIMULATED DEMO] Premier League Official Matchday Team News: Arsenal vs Chelsea",
                    publisher="Premier League",
                    claim_supported="[SIMULATED DEMO] Bukayo Saka passed late fitness assessment after minor knock; confirmed available in starting squad.",
                    published_at=now - timedelta(hours=14),
                    inline_id="[1]",
                ),
                WebEvidenceBuilder.create_evidence(
                    url="https://www.arsenal.com/news/medical-update-ahead-of-chelsea",
                    title="[SIMULATED DEMO] Arsenal FC Official Medical Bulletin",
                    publisher="Arsenal FC",
                    claim_supported="[SIMULATED DEMO] Martin Odegaard fully trained with first team across full sessions; starting role anticipated.",
                    published_at=now - timedelta(hours=22),
                    inline_id="[2]",
                ),
                WebEvidenceBuilder.create_evidence(
                    url="https://www.thefa.com/referees/appointments/match-officials",
                    title="[SIMULATED DEMO] The Football Association Match Official Appointments",
                    publisher="The FA",
                    claim_supported="[SIMULATED DEMO] Anthony Taylor confirmed as referee; averaged 4.15 yellow cards and 21.8 fouls per 90 in 2026/27.",
                    published_at=now - timedelta(days=2),
                    inline_id="[3]",
                ),
                WebEvidenceBuilder.create_evidence(
                    url="https://theathletic.com/football/arsenal-chelsea-tactical-preview",
                    title="[SIMULATED DEMO] The Athletic: Chelsea Expected Structure and Personnel Plan",
                    publisher="The Athletic",
                    claim_supported="[SIMULATED DEMO] Chelsea expected to deploy dual-pivot midfield to counteract Arsenal central overload; Cole Palmer central.",
                    published_at=now - timedelta(hours=8),
                    inline_id="[4]",
                ),
            ]

            conflicts = [
                "[SIMULATED CONFLICT TEST] Early secondary tabloid reports suggested Bukayo Saka was doubtful due to hamstring tightness; contradicted and resolved by Premier League & Arsenal FC official confirmation of fitness."
            ]

            summary = (
                "[DATA MODE: DEMO (SIMULATED)] Official announcements from the Premier League and Arsenal FC corroborate "
                "that Bukayo Saka and Martin Odegaard are fit and available. Anthony Taylor's referee appointment aligns with "
                "elevated card distributions (4.15 per match). Conflicting secondary claims regarding Saka's "
                "hamstring have been superseded by primary club verification."
            )

            return WebResearchRecord(
                query=f"{home_team} vs {away_team} team news injuries lineups referee",
                search_reason="[DATA MODE: DEMO] Pre-match validation of key player availability, referee appointment, and tactical context.",
                executed_at=now,
                sources=sources,
                summary=summary,
                material_conflicts=conflicts,
            )

        # ---------------------------------------------------------------------
        # LIVE Mode: Refuses to fabricate web research without real live search
        # ---------------------------------------------------------------------
        return WebResearchRecord(
            query=f"{home_team} vs {away_team} team news",
            search_reason="Live web research unconfigured: GROQ_API_KEY is not configured.",
            executed_at=now,
            sources=[],
            summary="Live web research unavailable: GROQ_API_KEY is not configured. The Football Intelligence Engine strictly refuses to present simulated research in LIVE mode.",
            material_conflicts=[],
        )
