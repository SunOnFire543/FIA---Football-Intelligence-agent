"""Joint Probability Modeling and Dependency Handling for Parlays."""

from __future__ import annotations

import math
from typing import Dict, List, Optional
import numpy as np

from app.schemas.enums import MarketType, SelectionOutcome
from app.schemas.models import ParlayLeg


class ParlayProbabilityModel:
    """Calculates joint probabilities accounting for same-match correlations."""

    @staticmethod
    def compute_same_match_joint_probability(
        legs: List[ParlayLeg],
        score_matrix: Optional[Dict[str, float]] = None,
    ) -> float:
        """Derive joint probability of same-match selections.

        Uses the bivariate score matrix when match result and goal totals are combined,
        preventing naive independence multiplication.
        """
        if not legs:
            return 0.0

        if len(legs) == 1:
            return legs[0].leg_win_probability

        # If we have the full score matrix, evaluate joint outcome space for match-level markets
        has_result = any(l.market == MarketType.MATCH_RESULT for l in legs)
        has_total = any(l.market == MarketType.OVER_UNDER_GOALS for l in legs)

        if score_matrix and has_result and has_total and len(legs) == 2:
            # Exact joint sum over score matrix cells that satisfy both criteria
            result_leg = next(l for l in legs if l.market == MarketType.MATCH_RESULT)
            total_leg = next(l for l in legs if l.market == MarketType.OVER_UNDER_GOALS)

            joint_p = 0.0
            for score_str, p_cell in score_matrix.items():
                x_str, y_str = score_str.split("-")
                x, y = int(x_str), int(y_str)

                # Check result condition
                satisfies_result = False
                if result_leg.selection == SelectionOutcome.HOME.value and x > y:
                    satisfies_result = True
                elif result_leg.selection == SelectionOutcome.DRAW.value and x == y:
                    satisfies_result = True
                elif result_leg.selection == SelectionOutcome.AWAY.value and x < y:
                    satisfies_result = True

                # Check total condition
                thresh = total_leg.threshold or 2.5
                satisfies_total = False
                if total_leg.selection == SelectionOutcome.OVER.value and (x + y) > thresh:
                    satisfies_total = True
                elif total_leg.selection == SelectionOutcome.UNDER.value and (x + y) < thresh:
                    satisfies_total = True

                if satisfies_result and satisfies_total:
                    joint_p += p_cell

            return float(joint_p)

        # For player and match combined (e.g. Saka SOT and Arsenal Win), apply positive correlation factor
        # P(A and B) = P(A) * P(B|A) where P(B|A) > P(B) for winning team player
        raw_product = float(np.prod([l.leg_win_probability for l in legs]))

        # Correlation dampening for same match: positive association between team dominance and player events
        correlation_multiplier = 1.08 if len(legs) <= 3 else 1.15
        joint_p = min(0.95 * min(l.leg_win_probability for l in legs), raw_product * correlation_multiplier)
        return float(joint_p)

    @staticmethod
    def compute_multi_match_joint_probability(legs: List[ParlayLeg]) -> float:
        """For strictly independent fixtures across different matches: P = prod(p_i)."""
        if not legs:
            return 0.0
        return float(np.prod([l.leg_win_probability for l in legs]))
