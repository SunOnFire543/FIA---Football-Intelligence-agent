"""Dixon-Coles Bivariate Goal Prediction Model.

Implements Poisson goals baseline with low-score correlation adjustment for
Home/Draw/Away, Over/Under, Double Chance, BTTS, and score matrices.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

from app.config.settings import settings
from app.models.probability_validation import ProbabilityValidator
from app.schemas.enums import MarketType, ModelStatus, SelectionOutcome
from app.schemas.models import Fixture, MatchPredictionSummary, SelectionPrediction


class DixonColesMatchModel:
    """Goals-based bivariate match prediction model."""

    MODEL_NAME = "Dixon-Coles-Poisson"
    MODEL_VERSION = "2.1.0"
    MAX_GOALS = 8  # 0 to 7 goals evaluated in matrix

    def __init__(self, rho: Optional[float] = None, home_advantage: float = 1.22):
        self.rho = rho if rho is not None else settings.default_dixon_coles_rho
        self.home_advantage = home_advantage

    @staticmethod
    def _poisson_pmf(k: int, lamb: float) -> float:
        """Standard Poisson probability mass."""
        if lamb <= 0.0:
            return 1.0 if k == 0 else 0.0
        return (math.pow(lamb, k) * math.exp(-lamb)) / math.factorial(k)

    def _tau(self, x: int, y: int, lamb: float, mu: float) -> float:
        """Dixon-Coles adjustment parameter for low scoring events."""
        if x == 0 and y == 0:
            return 1.0 - (lamb * mu * self.rho)
        elif x == 0 and y == 1:
            return 1.0 + (lamb * self.rho)
        elif x == 1 and y == 0:
            return 1.0 + (mu * self.rho)
        elif x == 1 and y == 1:
            return 1.0 - self.rho
        return 1.0

    def compute_score_matrix(self, lambda_home: float, mu_away: float) -> np.ndarray:
        """Compute the joint probability distribution of match scores."""
        matrix = np.zeros((self.MAX_GOALS, self.MAX_GOALS), dtype=np.float64)

        for x in range(self.MAX_GOALS):
            px = self._poisson_pmf(x, lambda_home)
            for y in range(self.MAX_GOALS):
                py = self._poisson_pmf(y, mu_away)
                adj = self._tau(x, y, lambda_home, mu_away)
                # Enforce non-negativity
                prob = max(0.0, adj * px * py)
                matrix[x, y] = prob

        # Normalize over truncated matrix to strictly enforce sum = 1.0
        total_mass = np.sum(matrix)
        if total_mass > 0:
            matrix = matrix / total_mass
        return matrix

    def estimate_lambdas(
        self,
        home_fixtures: List[Fixture],
        away_fixtures: List[Fixture],
        home_team_id: str,
        away_team_id: str,
    ) -> Tuple[float, float, int]:
        """Estimate expected goals lambda and mu using historical match records."""
        total_samples = len(home_fixtures) + len(away_fixtures)
        if total_samples < settings.min_historical_matches:
            # Fallback to balanced prior if historical matches are insufficient
            return 1.45, 1.15, total_samples

        # Calculate goals scored and conceded by home team
        home_scored = []
        home_conceded = []
        for f in home_fixtures:
            if f.status != "FINISHED" or f.home_score is None or f.away_score is None:
                continue
            if f.home_team_id == home_team_id:
                home_scored.append(f.home_score)
                home_conceded.append(f.away_score)
            else:
                home_scored.append(f.away_score)
                home_conceded.append(f.home_score)

        # Calculate goals scored and conceded by away team
        away_scored = []
        away_conceded = []
        for f in away_fixtures:
            if f.status != "FINISHED" or f.home_score is None or f.away_score is None:
                continue
            if f.home_team_id == away_team_id:
                away_scored.append(f.home_score)
                away_conceded.append(f.away_score)
            else:
                away_scored.append(f.away_score)
                away_conceded.append(f.home_score)

        avg_league_goals = 1.35
        home_att = np.mean(home_scored) / avg_league_goals if home_scored else 1.0
        home_def = np.mean(home_conceded) / avg_league_goals if home_conceded else 1.0

        away_att = np.mean(away_scored) / avg_league_goals if away_scored else 1.0
        away_def = np.mean(away_conceded) / avg_league_goals if away_conceded else 1.0

        lambda_h = max(0.3, home_att * away_def * self.home_advantage * avg_league_goals)
        mu_a = max(0.3, away_att * home_def * avg_league_goals)

        return float(lambda_h), float(mu_a), total_samples

    def predict_fixture(
        self,
        fixture: Fixture,
        home_history: List[Fixture],
        away_history: List[Fixture],
    ) -> MatchPredictionSummary:
        """Generate comprehensive match market predictions."""
        lambda_h, mu_a, samples = self.estimate_lambdas(
            home_history, away_history, fixture.home_team_id, fixture.away_team_id
        )

        matrix = self.compute_score_matrix(lambda_h, mu_a)
        score_dict: Dict[str, float] = {}
        for x in range(self.MAX_GOALS):
            for y in range(self.MAX_GOALS):
                score_dict[f"{x}-{y}"] = float(matrix[x, y])

        predictions: List[SelectionPrediction] = []

        # 1. Match Result (1X2)
        p_home = float(np.sum(np.tril(matrix, -1)))  # x > y
        p_draw = float(np.trace(matrix))             # x == y
        p_away = float(np.sum(np.triu(matrix, 1)))   # x < y

        # Enforce exact partition sum
        hda_norm = np.array([p_home, p_draw, p_away])
        hda_norm = hda_norm / np.sum(hda_norm)
        p_home, p_draw, p_away = float(hda_norm[0]), float(hda_norm[1]), float(hda_norm[2])

        status = ModelStatus.SUPPORTED if samples >= settings.min_historical_matches else ModelStatus.INSUFFICIENT_DATA

        predictions.append(
            SelectionPrediction(
                market=MarketType.MATCH_RESULT,
                selection=SelectionOutcome.HOME.value,
                estimated_probability=p_home,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )
        predictions.append(
            SelectionPrediction(
                market=MarketType.MATCH_RESULT,
                selection=SelectionOutcome.DRAW.value,
                estimated_probability=p_draw,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )
        predictions.append(
            SelectionPrediction(
                market=MarketType.MATCH_RESULT,
                selection=SelectionOutcome.AWAY.value,
                estimated_probability=p_away,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )

        # 2. Double Chance
        predictions.append(
            SelectionPrediction(
                market=MarketType.DOUBLE_CHANCE,
                selection=SelectionOutcome.HOME_OR_DRAW.value,
                estimated_probability=p_home + p_draw,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )
        predictions.append(
            SelectionPrediction(
                market=MarketType.DOUBLE_CHANCE,
                selection=SelectionOutcome.HOME_OR_AWAY.value,
                estimated_probability=p_home + p_away,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )
        predictions.append(
            SelectionPrediction(
                market=MarketType.DOUBLE_CHANCE,
                selection=SelectionOutcome.DRAW_OR_AWAY.value,
                estimated_probability=p_draw + p_away,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )

        # 3. Over / Under Total Goals
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            p_over = 0.0
            for x in range(self.MAX_GOALS):
                for y in range(self.MAX_GOALS):
                    if (x + y) > threshold:
                        p_over += matrix[x, y]
            p_over = float(p_over)
            p_under = float(1.0 - p_over)

            predictions.append(
                SelectionPrediction(
                    market=MarketType.OVER_UNDER_GOALS,
                    selection=SelectionOutcome.OVER.value,
                    threshold=threshold,
                    estimated_probability=p_over,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=status,
                    historical_samples_used=samples,
                )
            )
            predictions.append(
                SelectionPrediction(
                    market=MarketType.OVER_UNDER_GOALS,
                    selection=SelectionOutcome.UNDER.value,
                    threshold=threshold,
                    estimated_probability=p_under,
                    model_name=self.MODEL_NAME,
                    model_version=self.MODEL_VERSION,
                    model_status=status,
                    historical_samples_used=samples,
                )
            )

        # 4. Both Teams To Score (BTTS)
        p_btts_yes = float(np.sum(matrix[1:, 1:]))
        p_btts_no = float(1.0 - p_btts_yes)

        predictions.append(
            SelectionPrediction(
                market=MarketType.BOTH_TEAMS_TO_SCORE,
                selection=SelectionOutcome.YES.value,
                estimated_probability=p_btts_yes,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )
        predictions.append(
            SelectionPrediction(
                market=MarketType.BOTH_TEAMS_TO_SCORE,
                selection=SelectionOutcome.NO.value,
                estimated_probability=p_btts_no,
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                model_status=status,
                historical_samples_used=samples,
            )
        )

        # Audit prediction set
        val_errors = ProbabilityValidator.audit_prediction_set(predictions)
        if val_errors:
            raise ValueError(f"Internal probability validation error: {val_errors[0].message}")

        return MatchPredictionSummary(
            fixture_id=fixture.fixture_id,
            home_team=fixture.home_team_name,
            away_team=fixture.away_team_name,
            kickoff_time=fixture.kickoff_time,
            lambda_home=lambda_h,
            mu_away=mu_a,
            rho_dixon_coles=self.rho,
            predictions=predictions,
            score_matrix=score_dict,
            model_status=status,
        )
