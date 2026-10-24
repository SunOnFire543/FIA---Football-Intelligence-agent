"""Walk-Forward Chronological Backtesting Engine.

Guarantees temporal data integrity by ensuring predictions at timestamp t only
access historical observations from timestamps < t.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple
from pydantic import BaseModel

from app.evaluation.metrics import EvaluationMetrics
from app.models.match_model import DixonColesMatchModel
from app.schemas.enums import SelectionOutcome
from app.schemas.models import Fixture


class BacktestSummary(BaseModel):
    """Results of a walk-forward historical simulation."""
    total_matches_evaluated: int
    brier_score_home_win: float
    brier_score_over_2_5: float
    log_loss_home_win: float
    simulated_roi_positive_ev: float
    qualifying_bets_count: int
    temporal_leakage_prevented: bool = True


class WalkForwardBacktester:
    """Performs walk-forward chronological backtesting."""

    def __init__(self, model: Optional[DixonColesMatchModel] = None):
        self.model = model or DixonColesMatchModel()

    def run_backtest(
        self,
        historical_fixtures: List[Fixture],
        start_index: int = 5,
    ) -> BacktestSummary:
        """Evaluate match predictions sequentially in chronological order."""
        # Sort strictly chronologically
        sorted_fixtures = sorted(historical_fixtures, key=lambda f: f.kickoff_time)

        home_win_probs: List[float] = []
        home_win_actuals: List[int] = []
        over25_probs: List[float] = []
        over25_actuals: List[int] = []
        simulated_bets: List[Tuple[float, float, int]] = []

        for i in range(start_index, len(sorted_fixtures)):
            target_fixture = sorted_fixtures[i]
            if target_fixture.home_score is None or target_fixture.away_score is None:
                continue

            # Strict temporal boundary: only use fixtures strictly BEFORE this fixture's kickoff
            past_fixtures = [
                f for f in sorted_fixtures[:i]
                if f.kickoff_time < target_fixture.kickoff_time and f.status == "FINISHED"
            ]

            home_history = [f for f in past_fixtures if target_fixture.home_team_id in (f.home_team_id, f.away_team_id)]
            away_history = [f for f in past_fixtures if target_fixture.away_team_id in (f.home_team_id, f.away_team_id)]

            # Generate prediction at cutoff
            summary = self.model.predict_fixture(target_fixture, home_history, away_history)

            # Extract Home Win prediction
            hw_pred = next((p for p in summary.predictions if p.selection == SelectionOutcome.HOME.value), None)
            if hw_pred:
                p_hw = hw_pred.estimated_probability
                actual_hw = 1 if target_fixture.home_score > target_fixture.away_score else 0
                home_win_probs.append(p_hw)
                home_win_actuals.append(actual_hw)

                # Simulated EV bet at simulated closing odds of 1.90 if model prob > 0.55
                if p_hw > 0.55:
                    simulated_bets.append((p_hw, 1.90, actual_hw))

            # Extract Over 2.5 prediction
            o25_pred = next(
                (p for p in summary.predictions if p.market.value == "OVER_UNDER_GOALS" and p.threshold == 2.5 and p.selection == "OVER"),
                None,
            )
            if o25_pred:
                p_o25 = o25_pred.estimated_probability
                actual_o25 = 1 if (target_fixture.home_score + target_fixture.away_score) > 2.5 else 0
                over25_probs.append(p_o25)
                over25_actuals.append(actual_o25)

        brier_hw = EvaluationMetrics.brier_score(home_win_probs, home_win_actuals)
        brier_o25 = EvaluationMetrics.brier_score(over25_probs, over25_actuals)
        log_loss_hw = EvaluationMetrics.log_loss(home_win_probs, home_win_actuals)
        roi = EvaluationMetrics.return_on_investment(simulated_bets)

        return BacktestSummary(
            total_matches_evaluated=len(home_win_probs),
            brier_score_home_win=round(brier_hw, 4),
            brier_score_over_2_5=round(brier_o25, 4),
            log_loss_home_win=round(log_loss_hw, 4),
            simulated_roi_positive_ev=round(roi, 4),
            qualifying_bets_count=len(simulated_bets),
            temporal_leakage_prevented=True,
        )
