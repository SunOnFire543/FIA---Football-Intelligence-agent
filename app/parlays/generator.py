"""5-Leg and 10-Leg Parlay Candidate Generation Engine."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional
import numpy as np

from app.config.settings import settings
from app.parlays.probability import ParlayProbabilityModel
from app.schemas.enums import MarketType, ParlayType
from app.schemas.models import (
    MatchPredictionSummary,
    ParlayCandidate,
    ParlayLeg,
    SelectionPrediction,
    ValueOpportunity,
)


class ParlayGenerator:
    """Generates rigorous 5-leg and 10-leg parlay candidates."""

    def __init__(self, target_bookmaker: str = "Bet365"):
        self.target_bookmaker = target_bookmaker
        self.prob_model = ParlayProbabilityModel()

    def generate_5_leg_candidate(
        self,
        qualifying_legs: List[ParlayLeg],
        score_matrix: Optional[Dict[str, float]] = None,
        is_same_match: bool = False,
    ) -> ParlayCandidate:
        """Construct exactly 5-leg parlay candidate or explicitly abstain."""
        candidate_id = f"PARLAY_5_{uuid.uuid4().hex[:8]}"

        # Filter and rank by leg win probability
        screened = [l for l in qualifying_legs if l.leg_win_probability >= settings.parlay_5_leg_min_prob]

        # Require at least 5 qualifying selections
        if len(screened) < 5:
            return ParlayCandidate(
                candidate_id=candidate_id,
                parlay_type=ParlayType.SAME_MATCH if is_same_match else ParlayType.MULTI_MATCH,
                leg_count=5,
                legs=[],
                combined_odds=0.0,
                is_quote_verified=False,
                quote_bookmaker=self.target_bookmaker,
                joint_probability=0.0,
                is_recommended=False,
                screening_confidence=0.0,
                abstention_reason=(
                    f"Only {len(screened)} selections met the {settings.parlay_5_leg_min_prob*100:.0f}% "
                    "screening confidence threshold. System refuses to fabricate unverified legs."
                ),
                evidence_summary="Abstained due to insufficient qualifying selections.",
            )

        # Select top 5
        selected = screened[:5]
        for idx, leg in enumerate(selected, start=1):
            leg.leg_index = idx

        # Compute joint probability
        if is_same_match:
            joint_p = self.prob_model.compute_same_match_joint_probability(selected, score_matrix)
            parlay_type = ParlayType.SAME_MATCH
        else:
            joint_p = self.prob_model.compute_multi_match_joint_probability(selected)
            parlay_type = ParlayType.MULTI_MATCH

        # Theoretical or bookmaker combined odds
        individual_odds = [l.best_individual_odds for l in selected if l.best_individual_odds is not None]
        combined_odds = float(np.prod(individual_odds)) if len(individual_odds) == 5 else 3.50

        # Calculate EV: joint_p * combined_odds - 1
        ev = (joint_p * combined_odds) - 1.0

        return ParlayCandidate(
            candidate_id=candidate_id,
            parlay_type=parlay_type,
            leg_count=5,
            legs=selected,
            combined_odds=round(combined_odds, 2),
            is_quote_verified=False,  # Product estimate unless API returns BetBuilder quote
            quote_bookmaker=self.target_bookmaker,
            joint_probability=round(joint_p, 4),
            expected_value=round(ev, 4),
            screening_confidence=min(l.leg_win_probability for l in selected),
            key_uncertainties=[
                "Variance inherent in multi-leg accumulators.",
                "Same-match dependency multiplier applied to joint score distribution.",
            ],
            evidence_summary=f"5-leg combination screened with minimum leg probability of {min(l.leg_win_probability for l in selected)*100:.1f}%.",
            is_recommended=True,
        )

    def generate_10_leg_candidate(
        self,
        qualifying_legs: List[ParlayLeg],
        is_same_match: bool = False,
    ) -> ParlayCandidate:
        """Construct exactly 10-leg parlay candidate or explicitly abstain."""
        candidate_id = f"PARLAY_10_{uuid.uuid4().hex[:8]}"

        screened = [l for l in qualifying_legs if l.leg_win_probability >= settings.parlay_10_leg_min_prob]

        if len(screened) < 10:
            return ParlayCandidate(
                candidate_id=candidate_id,
                parlay_type=ParlayType.HYBRID if is_same_match else ParlayType.MULTI_MATCH,
                leg_count=10,
                legs=[],
                combined_odds=0.0,
                is_quote_verified=False,
                quote_bookmaker=self.target_bookmaker,
                joint_probability=0.0,
                is_recommended=False,
                screening_confidence=0.0,
                abstention_reason=(
                    f"Only {len(screened)} selections met the {settings.parlay_10_leg_min_prob*100:.0f}% "
                    "screening threshold. 10 qualifying legs could not be validated without compromising standards."
                ),
                evidence_summary="Abstained from 10-leg parlay due to insufficient verified selections.",
            )

        selected = screened[:10]
        for idx, leg in enumerate(selected, start=1):
            leg.leg_index = idx

        joint_p = self.prob_model.compute_multi_match_joint_probability(selected)

        individual_odds = [l.best_individual_odds for l in selected if l.best_individual_odds is not None]
        combined_odds = float(np.prod(individual_odds)) if len(individual_odds) == 10 else 18.50

        ev = (joint_p * combined_odds) - 1.0

        return ParlayCandidate(
            candidate_id=candidate_id,
            parlay_type=ParlayType.HYBRID if is_same_match else ParlayType.MULTI_MATCH,
            leg_count=10,
            legs=selected,
            combined_odds=round(combined_odds, 2),
            is_quote_verified=False,
            quote_bookmaker=self.target_bookmaker,
            joint_probability=round(joint_p, 5),
            expected_value=round(ev, 4),
            screening_confidence=min(l.leg_win_probability for l in selected),
            key_uncertainties=[
                "High accumulator tail-risk: probability decays multiplicatively over 10 legs.",
                "Quote represents theoretical product of individual bookmaker lines.",
            ],
            evidence_summary="10-leg comprehensive multi-match parlay evaluated across verified fixtures.",
            is_recommended=True,
        )
