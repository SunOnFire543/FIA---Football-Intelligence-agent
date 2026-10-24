"""Strict Mathematical Validation for Probabilities and Distributions."""

from __future__ import annotations

import math
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.schemas.enums import MarketType, ModelStatus
from app.schemas.models import SelectionPrediction


class ValidationErrorRecord(BaseModel):
    """Details of a mathematical or structural probability violation."""
    error_type: str
    message: str
    market: MarketType
    observed_sum: Optional[float] = None


class ProbabilityValidator:
    """Enforces axiomatic probability constraints and distribution consistency."""

    TOLERANCE: float = 1e-4

    @classmethod
    def validate_bounds(cls, prob: float, name: str = "probability") -> None:
        """Check that probability lies strictly in [0.0, 1.0]."""
        if math.isnan(prob) or math.isinf(prob):
            raise ValueError(f"Probability '{name}' is NaN or Infinite: {prob}")
        if prob < -cls.TOLERANCE or prob > 1.0 + cls.TOLERANCE:
            raise ValueError(f"Probability '{name}' out of bounds [0, 1]: {prob:.6f}")

    @classmethod
    def validate_partition(cls, probs: List[float], partition_name: str) -> None:
        """Verify that mutually exclusive and collectively exhaustive outcomes sum to 1.0."""
        total = sum(probs)
        if abs(total - 1.0) > cls.TOLERANCE:
            raise ValueError(
                f"Partition '{partition_name}' does not sum to 1.0 (Sum: {total:.6f}, Diff: {abs(total - 1.0):.6f})"
            )

    @classmethod
    def audit_prediction_set(
        cls, predictions: List[SelectionPrediction]
    ) -> List[ValidationErrorRecord]:
        """Perform comprehensive consistency checks across a set of market predictions."""
        errors: List[ValidationErrorRecord] = []

        # 1. Bounds check
        for p in predictions:
            if p.estimated_probability < 0.0 or p.estimated_probability > 1.0:
                errors.append(
                    ValidationErrorRecord(
                        error_type="OUT_OF_BOUNDS",
                        message=f"Probability {p.estimated_probability} out of [0, 1]",
                        market=p.market,
                    )
                )

        # 2. Match Result (1X2) sum
        hda = [p.estimated_probability for p in predictions if p.market == MarketType.MATCH_RESULT]
        if len(hda) == 3:
            s = sum(hda)
            if abs(s - 1.0) > cls.TOLERANCE:
                errors.append(
                    ValidationErrorRecord(
                        error_type="PARTITION_SUM_MISMATCH",
                        message=f"1X2 outcomes sum to {s:.5f} instead of 1.0",
                        market=MarketType.MATCH_RESULT,
                        observed_sum=s,
                    )
                )

        # 3. BTTS sum
        btts = [p.estimated_probability for p in predictions if p.market == MarketType.BOTH_TEAMS_TO_SCORE]
        if len(btts) == 2:
            s = sum(btts)
            if abs(s - 1.0) > cls.TOLERANCE:
                errors.append(
                    ValidationErrorRecord(
                        error_type="PARTITION_SUM_MISMATCH",
                        message=f"BTTS Yes/No outcomes sum to {s:.5f} instead of 1.0",
                        market=MarketType.BOTH_TEAMS_TO_SCORE,
                        observed_sum=s,
                    )
                )

        # 4. Over/Under monotonic decrease
        overs = sorted(
            [p for p in predictions if p.market == MarketType.OVER_UNDER_GOALS and p.selection.upper() == "OVER"],
            key=lambda x: x.threshold if x.threshold is not None else 0.0,
        )
        for i in range(len(overs) - 1):
            if overs[i].estimated_probability < overs[i + 1].estimated_probability - cls.TOLERANCE:
                errors.append(
                    ValidationErrorRecord(
                        error_type="MONOTONICITY_VIOLATION",
                        message=(
                            f"Over {overs[i].threshold} ({overs[i].estimated_probability:.3f}) has lower probability "
                            f"than Over {overs[i+1].threshold} ({overs[i+1].estimated_probability:.3f})"
                        ),
                        market=MarketType.OVER_UNDER_GOALS,
                    )
                )

        return errors
