"""Statistical Metrics: Brier Score, Log Loss, Calibration, and ROI."""

from __future__ import annotations

import math
from typing import List, Tuple
import numpy as np


class EvaluationMetrics:
    """Calculates chronological model accuracy and betting performance metrics."""

    @staticmethod
    def brier_score(predictions: List[float], actuals: List[int]) -> float:
        """Brier score: Mean squared error of probability predictions."""
        if not predictions or len(predictions) != len(actuals):
            return 0.0
        return float(np.mean([(p - y) ** 2 for p, y in zip(predictions, actuals)]))

    @staticmethod
    def log_loss(predictions: List[float], actuals: List[int], eps: float = 1e-15) -> float:
        """Binary cross-entropy / log loss."""
        if not predictions or len(predictions) != len(actuals):
            return 0.0
        clipped = [max(eps, min(1.0 - eps, p)) for p in predictions]
        losses = [
            -(y * math.log(p) + (1 - y) * math.log(1.0 - p))
            for p, y in zip(clipped, actuals)
        ]
        return float(np.mean(losses))

    @staticmethod
    def return_on_investment(
        bets: List[Tuple[float, float, int]]  # (prob, decimal_odds, won: 1 or 0)
    ) -> float:
        """Calculate realized ROI per unit stake."""
        if not bets:
            return 0.0
        total_stakes = len(bets)
        total_payout = sum(odds if won == 1 else 0.0 for _, odds, won in bets)
        return float((total_payout - total_stakes) / total_stakes)
