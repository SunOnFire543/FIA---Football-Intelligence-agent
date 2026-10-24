"""Odds Aggregation and Cross-Bookmaker Comparison Engine."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple
from app.odds.normalisation import OddsNormaliser
from app.schemas.models import BookmakerQuote, MarketOddsComparison


class OddsComparisonEngine:
    """Compares equivalent market selections across all connected bookmakers."""

    def compare_odds(self, fixture_id: str, quotes: List[BookmakerQuote]) -> List[MarketOddsComparison]:
        """Aggregate quotes and determine the best available price for each selection."""
        # Group by (market, selection, threshold)
        grouped: Dict[Tuple[str, str, str], List[BookmakerQuote]] = defaultdict(list)
        for q in quotes:
            if q.is_suspended:
                continue
            key = OddsNormaliser.match_key(q)
            grouped[key].append(q)

        comparisons: List[MarketOddsComparison] = []
        for (mkt_val, sel, thresh_str), group in grouped.items():
            # Find best quote
            best_quote = max(group, key=lambda x: x.decimal_odds)
            comparisons.append(
                MarketOddsComparison(
                    fixture_id=fixture_id,
                    market=best_quote.market,
                    selection=best_quote.selection,
                    threshold=best_quote.threshold,
                    best_decimal_odds=best_quote.decimal_odds,
                    best_bookmaker=best_quote.bookmaker,
                    all_quotes=group,
                    observed_at=best_quote.observed_at,
                )
            )

        return comparisons
