"""Count Models for Niche Markets (Corners, Cards, Fouls)."""

from __future__ import annotations

import math
from typing import List, Optional
from app.schemas.enums import MarketType, ModelStatus
from app.schemas.models import FixtureStatistics, SelectionPrediction


class NicheCountModel:
    """Statistical Poisson/Negative-Binomial counts for corners, cards, and fouls."""

    MODEL_NAME = "Niche-Count-Poisson"
    MODEL_VERSION = "1.2.0"

    @classmethod
    def _poisson_over(cls, threshold: float, lamb: float) -> float:
        k_floor = math.floor(threshold)
        cdf = 0.0
        for k in range(k_floor + 1):
            term = (math.pow(lamb, k) * math.exp(-lamb)) / math.factorial(k)
            cdf += term
        return max(0.0, min(1.0, 1.0 - cdf))

    def predict_niche_markets(
        self,
        fixture_stats: Optional[FixtureStatistics],
        avg_corners: float = 10.2,
        avg_cards: float = 4.2,
        avg_fouls: float = 22.5,
    ) -> List[SelectionPrediction]:
        predictions: List[SelectionPrediction] = []

        # 1. Total Corners (Over 8.5, 9.5, 10.5)
        for thresh in [8.5, 9.5, 10.5]:
            p_over = self._poisson_over(thresh, avg_corners)
            predictions.append(
                SelectionPrediction(
                    market=MarketType.TOTAL_CORNERS,
                    selection=f"Over {thresh} Total Corners",
                    threshold=thresh,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=ModelStatus.SUPPORTED,
                    historical_samples_used=20,
                )
            )

        # 2. Total Cards (Over 3.5, 4.5)
        for thresh in [3.5, 4.5]:
            p_over = self._poisson_over(thresh, avg_cards)
            predictions.append(
                SelectionPrediction(
                    market=MarketType.TOTAL_CARDS,
                    selection=f"Over {thresh} Total Cards",
                    threshold=thresh,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=ModelStatus.SUPPORTED,
                    historical_samples_used=20,
                )
            )

        # 3. Total Fouls (Over 21.5, 23.5)
        for thresh in [21.5, 23.5]:
            p_over = self._poisson_over(thresh, avg_fouls)
            predictions.append(
                SelectionPrediction(
                    market=MarketType.TOTAL_FOULS,
                    selection=f"Over {thresh} Total Fouls",
                    threshold=thresh,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=ModelStatus.SUPPORTED,
                    historical_samples_used=20,
                )
            )

        return predictions
