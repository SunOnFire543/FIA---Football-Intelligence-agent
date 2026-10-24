"""Player Performance & Proposition Statistical Model.

Calculates per-90 event rates, expected minutes, and Poisson probabilities for
Shots, Shots on Target, Anytime Goalscorer, Fouls, and Cards.
"""

from __future__ import annotations

import math
from typing import List, Optional
import numpy as np

from app.schemas.enums import MarketType, ModelStatus, SelectionOutcome
from app.schemas.models import FixtureLineups, PlayerMatchStats, SelectionPrediction


class PlayerPropModel:
    """Statistical model for individual player betting markets."""

    MODEL_NAME = "Player-Poisson-Rate"
    MODEL_VERSION = "1.5.0"

    @staticmethod
    def _poisson_pmf(k: int, lamb: float) -> float:
        if lamb <= 0.0:
            return 1.0 if k == 0 else 0.0
        return (math.pow(lamb, k) * math.exp(-lamb)) / math.factorial(k)

    @classmethod
    def _poisson_over(cls, threshold: float, lamb: float) -> float:
        """P(Count > threshold)."""
        k_floor = math.floor(threshold)
        cdf = sum(cls._poisson_pmf(k, lamb) for k in range(k_floor + 1))
        return max(0.0, min(1.0, 1.0 - cdf))

    def predict_player_markets(
        self,
        player_name: str,
        player_stats: List[PlayerMatchStats],
        lineup_info: Optional[FixtureLineups] = None,
        opponent_defense_factor: float = 1.0,
    ) -> List[SelectionPrediction]:
        """Derive validated probabilities for player prop selections."""
        predictions: List[SelectionPrediction] = []

        if not player_stats:
            return predictions

        # Check starting status from lineups
        is_starter = True
        is_in_squad = True
        if lineup_info and lineup_info.is_confirmed:
            all_starters = [p.name.lower() for p in (lineup_info.home_starters + lineup_info.away_starters)]
            all_bench = [p.name.lower() for p in (lineup_info.home_bench + lineup_info.away_bench)]
            p_lower = player_name.lower()
            if any(p_lower in s for s in all_starters):
                is_starter = True
            elif any(p_lower in b for b in all_bench):
                is_starter = False
            else:
                is_in_squad = False

        if not is_in_squad:
            # Player is not in matchday squad
            return predictions

        expected_minutes = 85.0 if is_starter else 25.0
        sample_size = len(player_stats)
        status = ModelStatus.SUPPORTED if sample_size >= 5 else ModelStatus.INSUFFICIENT_DATA

        # Calculate historical per-90 rates
        total_mins = sum(s.minutes_played for s in player_stats)
        if total_mins < 90:
            # Insufficient minutes
            return predictions

        factor = (expected_minutes / 90.0) * opponent_defense_factor

        # 1. Shots on Target (SOT)
        total_sot = sum(s.shots_on_target for s in player_stats)
        sot_per_90 = (total_sot / total_mins) * 90.0
        lambda_sot = max(0.1, sot_per_90 * factor)

        for thresh in [0.5, 1.5]:
            p_over = self._poisson_over(thresh, lambda_sot)
            predictions.append(
                SelectionPrediction(
                    market=MarketType.PLAYER_SHOTS_ON_TARGET,
                    selection=f"{player_name} Over {thresh} SOT",
                    threshold=thresh,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=status,
                    historical_samples_used=sample_size,
                    notes=f"Lambda: {lambda_sot:.2f}, Est Mins: {expected_minutes}",
                )
            )

        # 2. Player Total Shots
        total_shots = sum(s.shots for s in player_stats)
        shots_per_90 = (total_shots / total_mins) * 90.0
        lambda_shots = max(0.2, shots_per_90 * factor)

        for thresh in [1.5, 2.5]:
            p_over = self._poisson_over(thresh, lambda_shots)
            predictions.append(
                SelectionPrediction(
                    market=MarketType.PLAYER_SHOTS,
                    selection=f"{player_name} Over {thresh} Shots",
                    threshold=thresh,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=status,
                    historical_samples_used=sample_size,
                )
            )

        # 3. Anytime Goalscorer
        total_goals = sum(s.goals for s in player_stats)
        goals_per_90 = (total_goals / total_mins) * 90.0
        lambda_goals = max(0.05, goals_per_90 * factor)
        p_score = 1.0 - math.exp(-lambda_goals)

        predictions.append(
            SelectionPrediction(
                market=MarketType.ANYTIME_GOALSCORER,
                selection=f"{player_name} Anytime Goalscorer",
                estimated_probability=p_score,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=sample_size,
                notes=f"Est goal rate: {lambda_goals:.2f}",
            )
        )

        return predictions
