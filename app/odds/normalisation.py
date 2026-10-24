"""Odds Normalisation and Margin / Vig Removal."""

from __future__ import annotations

from typing import Dict, List, Tuple
from app.schemas.enums import MarketType
from app.schemas.models import BookmakerQuote


class OddsNormaliser:
    """Normalises market identifiers, selections, and removes bookmaker margin."""

    @staticmethod
    def match_key(quote: BookmakerQuote) -> Tuple[str, str, str]:
        """Unique key for matching identical selections and thresholds."""
        thresh_str = f"{quote.threshold:.2f}" if quote.threshold is not None else "NONE"
        sel_clean = quote.selection.strip().upper()
        return (quote.market.value, sel_clean, thresh_str)

    @staticmethod
    def remove_vig_proportional(quotes: List[BookmakerQuote]) -> Dict[str, float]:
        """Derive vig-free market implied probabilities using proportional normalisation.

        Sum(1 / O_i) = S (Overround).
        p_fair_i = (1 / O_i) / S.
        """
        if not quotes:
            return {}

        implied_sum = sum(q.implied_probability for q in quotes)
        if implied_sum <= 0:
            return {}

        vig_free: Dict[str, float] = {}
        for q in quotes:
            vig_free[q.selection] = q.implied_probability / implied_sum
        return vig_free
