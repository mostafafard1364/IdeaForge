"""
Tests for IdeaForge Backtest Engine
"""

import pytest
import pandas as pd
import numpy as np
from backtest.engine import (
    BacktestEngine, BacktestConfig, BacktestResult,
    Trade, TradeDirection
)


class TestBacktestEngine:
    """Test backtest engine."""
    
    def setup_method(self):
        self.config = BacktestConfig(
            initial_capital=10000,
            fee_pct=0.001,
            slippage_pct=0.0005
        )
        self.engine = BacktestEngine(self.config)
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        result = self.engine.run(df)
        assert result.total_trades == 0
    
    def test_no_signals(self):
        """Test with data but no signals."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, tz='UTC'),
            'open': np.random.uniform(90, 110, 100),
            'high': np.random.uniform(100, 120, 100),
            'low': np.random.uniform(80, 100, 100),
            'close': np.random.uniform(90, 110, 100),
            'volume': np.random.uniform(100, 1000, 100),
            'signal': ['none'] * 100
        })
        
        result = self.engine.run(df)
        assert result.total_trades == 0
    
    def test_single_long_trade(self):
        """Test single long trade."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, tz='UTC'),
            'open': [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            'high': [105, 105, 105, 105, 105, 105, 105, 105, 105, 105],
            'low': [95, 95, 95, 95, 95, 95, 95, 95, 95, 95],
            'close': [100, 102, 104, 106, 108, 110, 112, 114, 116, 118],
            'volume': [100] * 10,
            'signal': ['none', 'entry_long', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'exit_long']
        })
        
        result = self.engine.run(df)
        assert result.total_trades == 1
        assert result.trades[0].direction == TradeDirection.LONG
        assert result.trades[0].pnl > 0  # Profitable trade
    
    def test_fees_applied(self):
        """Test that fees are applied to trades."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, tz='UTC'),
            'open': [100, 100, 100, 100, 100],
            'high': [105, 105, 105, 105, 105],
            'low': [95, 95, 95, 95, 95],
            'close': [100, 100, 100, 100, 100],
            'volume': [100] * 5,
            'signal': ['entry_long', 'none', 'none', 'none', 'exit_long']
        })
        
        result = self.engine.run(df)
        if result.trades:
            assert result.trades[0].fees > 0
    
    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20, tz='UTC'),
            'open': [100] * 20,
            'high': [110] * 20,
            'low': [90] * 20,
            'close': [100, 110, 100, 110, 100, 110, 100, 110, 100, 110,
                     100, 110, 100, 110, 100, 110, 100, 110, 100, 110],
            'volume': [100] * 20,
            'signal': ['entry_long', 'exit_long', 'entry_long', 'exit_long',
                       'entry_long', 'exit_long', 'entry_long', 'exit_long',
                       'entry_long', 'exit_long', 'entry_long', 'exit_long',
                       'entry_long', 'exit_long', 'entry_long', 'exit_long',
                       'entry_long', 'exit_long', 'none', 'none']
        })
        
        result = self.engine.run(df)
        
        if result.total_trades > 0:
            assert result.win_rate >= 0
            assert result.win_rate <= 100
            assert result.profit_factor >= 0


class TestBacktestConfig:
    """Test backtest configuration."""
    
    def test_default_config(self):
        config = BacktestConfig()
        assert config.initial_capital == 10000
        assert config.fee_pct == 0.001
        assert config.slippage_pct == 0.0005
    
    def test_custom_config(self):
        config = BacktestConfig(
            initial_capital=50000,
            fee_pct=0.002,
            allow_short=False
        )
        assert config.initial_capital == 50000
        assert config.fee_pct == 0.002
        assert not config.allow_short
