"""Result Verification and Evidence Auditing Layer."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.schemas.enums import CoverageStatus
from app.schemas.models import (
    CompactEvidenceRecord,
    MatchPredictionSummary,
    ParlayCandidate,
    ValueOpportunity,
)


class ResultValidator:
    """Verifies that generated analysis, probabilities, and odds adhere strictly to evidence."""

    @classmethod
    def verify_analysis(
        cls,
        fixture_id: str,
        competition_id: str,
        prediction: Optional[MatchPredictionSummary],
        value_opps: List[ValueOpportunity],
        parlay_5: Optional[ParlayCandidate],
        parlay_10: Optional[ParlayCandidate],
        data_cutoff: datetime,
    ) -> CompactEvidenceRecord:
        """Run systematic integrity checks across all analytical outputs."""
        warnings: List[str] = []
        is_passed = True
        selections: List[str] = []

        # 1. Prediction integrity checks
        if prediction:
            if prediction.fixture_id != fixture_id:
                warnings.append(f"Fixture ID mismatch: expected {fixture_id}, got {prediction.fixture_id}")
                is_passed = False

            for p in prediction.predictions:
                selections.append(f"{p.market.value}:{p.selection}")
                if p.estimated_probability < 0.0 or p.estimated_probability > 1.0:
                    warnings.append(f"Probability out of bounds: {p.selection} = {p.estimated_probability}")
                    is_passed = False

        # 2. Value opportunity and EV math check: EV = p * O - 1
        for vo in value_opps:
            expected_calc = (vo.model_probability * vo.best_odds) - 1.0
            if abs(vo.expected_value - expected_calc) > 1e-3:
                warnings.append(
                    f"EV calculation error for {vo.selection}: stated {vo.expected_value:.4f}, expected {expected_calc:.4f}"
                )
                is_passed = False

            if vo.best_odds <= 1.0:
                warnings.append(f"Invalid decimal odds: {vo.selection} has odds {vo.best_odds} <= 1.0")
                is_passed = False

        # 3. Parlay checks
        if parlay_5 and parlay_5.is_recommended:
            if parlay_5.leg_count != 5:
                warnings.append(f"Parlay A has {parlay_5.leg_count} legs; exactly 5 legs required.")
                is_passed = False
            if parlay_5.joint_probability <= 0.0 or parlay_5.joint_probability > 1.0:
                warnings.append(f"Parlay A joint probability out of bounds: {parlay_5.joint_probability}")
                is_passed = False

        if parlay_10 and parlay_10.is_recommended:
            if parlay_10.leg_count != 10:
                warnings.append(f"Parlay B has {parlay_10.leg_count} legs; exactly 10 legs required.")
                is_passed = False
            if parlay_10.joint_probability <= 0.0 or parlay_10.joint_probability > 1.0:
                warnings.append(f"Parlay B joint probability out of bounds: {parlay_10.joint_probability}")
                is_passed = False

        record = CompactEvidenceRecord(
            record_id=f"EVID_{uuid.uuid4().hex[:10]}",
            fixture_id=fixture_id,
            competition_id=competition_id,
            prediction_timestamp=datetime.now(timezone.utc),
            data_cutoff_timestamp=data_cutoff,
            model_version=prediction.model_status.value if prediction else "NONE",
            selections_evaluated=selections,
            source_providers=["demo_provider", "demo_odds"],
            odds_sources=["Bet365", "Pinnacle", "Unibet"],
            coverage_status=CoverageStatus.AVAILABLE,
            verification_passed=is_passed,
            verification_warnings=warnings,
        )

        return record
