"""
Tests for Replay Engine and Robustness Testing
"""

import pytest
import pandas as pd
import numpy as np
from core.replay import ReplayEngine, ReplayState
from research.robustness import RobustnessTester, RobustnessResult
from backtest.engine import BacktestConfig


class TestReplayEngine:
    """Test replay engine."""

    def setup_method(self):
        self.df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h', tz='UTC'),
            'open': [100] * 100,
            'high': [110] * 100,
            'low': [90] * 100,
            'close': [100, 101] * 50,
            'volume': [100] * 100,
        })
        self.replay = ReplayEngine(self.df, initial_capital=10000)

    def test_initial_state(self):
        assert self.replay.state.current_index == 0
        assert len(self.replay.state.revealed_data) == 1

    def test_step_forward(self):
        assert self.replay.step() == True
        assert self.replay.state.current_index == 1
        assert len(self.replay.state.revealed_data) == 2

    def test_step_back(self):
        self.replay.step()
        assert self.replay.can_step_back()
        assert self.replay.step_back() == True
        assert self.replay.state.current_index == 0

    def test_jump_to(self):
        target = pd.Timestamp('2024-01-01 05:00', tz='UTC')
        assert self.replay.jump_to(target) == True
        assert self.replay.state.current_index == 5

    def test_reset(self):
        self.replay.step()
        self.replay.step()
        self.replay.reset()
        assert self.replay.state.current_index == 0
        assert self.replay.state.step_count == 0

    def test_no_lookahead(self):
        self.replay.step()
        self.replay.step()
        revealed = self.replay.get_revealed_data()
        assert len(revealed) == 3

    def test_end_of_data(self):
        for _ in range(100):
            self.replay.step()
        assert self.replay.step() == False


class TestRobustnessTester:
    """Test robustness testing."""

    def setup_method(self):
        self.df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h', tz='UTC'),
            'open': [100] * 100,
            'high': [110] * 100,
            'low': [90] * 100,
            'close': np.concatenate([np.linspace(100, 110, 50), np.linspace(110, 100, 50)]),
            'volume': [100] * 100,
            'signal': ['entry_long', 'exit_long'] * 50,
        })
        self.tester = RobustnessTester()

    def test_parameter_sweep(self):
        param_grid = {'fee_pct': [0.001, 0.002], 'slippage_pct': [0.0005, 0.001]}
        result = self.tester.parameter_sweep(self.df, param_grid)
        assert len(result.results) == 4
        assert len(result.parameter_sets) == 4

    def test_fee_sensitivity(self):
        result = self.tester.fee_sensitivity_test(self.df)
        assert len(result.results) > 0
        assert result.best_params is not None

    def test_time_period_test(self):
        result = self.tester.time_period_test(self.df, periods=3)
        assert len(result.results) == 3
        assert 'profit_factor' in result.results[0]

    def test_stability_score(self):
        result = self.tester.fee_sensitivity_test(self.df)
        assert result.stability_score is not None
        assert isinstance(result.stability_score, float)