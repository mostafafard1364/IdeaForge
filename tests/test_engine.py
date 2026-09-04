"""
Tests for IdeaForge Market DNA Engine
"""

import pytest
import pandas as pd
import numpy as np
from core import (
    Candle, MarketState, MarketColor, MarketRegime,
    SystemBarResult, calculate_system_bar,
    calculate_efficiency, calculate_ratio, calculate_pressure
)
from core.market_dna import MarketDNAEngine, MarketDNAConfig


class TestSystemBarCalculations:
    """Test system bar calculations."""
    
    def test_basic_system_bar(self):
        prices = np.array([100, 105, 103, 108, 110])
        result = calculate_system_bar(prices)
        assert result.up_total > 0
        assert result.down_total > 0
        assert result.system_bar > 0
    
    def test_all_up_movement(self):
        prices = np.array([100, 105, 110, 115, 120])
        result = calculate_system_bar(prices)
        assert result.down_total == 0
        assert result.efficiency == 1.0
    
    def test_all_down_movement(self):
        prices = np.array([120, 115, 110, 105, 100])
        result = calculate_system_bar(prices)
        assert result.up_total == 0
        assert result.efficiency == 1.0
    
    def test_no_movement(self):
        prices = np.array([100, 100, 100, 100])
        result = calculate_system_bar(prices)
        assert result.system_bar == 0
        assert result.efficiency == 0
    
    def test_single_price(self):
        prices = np.array([100])
        result = calculate_system_bar(prices)
        assert result.system_bar == 0


class TestEfficiency:
    def test_perfect_efficiency(self):
        assert calculate_efficiency(10, 10) == 1.0
    
    def test_zero_efficiency(self):
        assert calculate_efficiency(10, 0) == 0.0
    
    def test_safe_division(self):
        assert calculate_efficiency(0, 0) == 0.0
    
    def test_partial_efficiency(self):
        assert calculate_efficiency(10, 5) == 0.5


class TestRatio:
    def test_normal_ratio(self):
        assert calculate_ratio(10, 5) == 2.0
    
    def test_safe_division(self):
        assert calculate_ratio(10, 0) == 0.0


class TestPressure:
    def test_high_pressure(self):
        pressure = calculate_pressure(0.1, 2.0)
        assert pressure > 0.5
    
    def test_low_pressure(self):
        pressure = calculate_pressure(0.9, 1.0)
        assert pressure < 0.1
    
    def test_safe_division(self):
        assert calculate_pressure(0.5, 0) == 0.0

    def test_safe_division(self):
        assert calculate_pressure(0.5, 0) == 0.0


class TestMarketDNAEngine:
    def setup_method(self):
        self.engine = MarketDNAEngine()
    
    def test_calculate_candle_state(self):
        candle = Candle(
            timestamp=pd.Timestamp('2024-01-01', tz='UTC'),
            open=100, high=110, low=90, close=105, volume=1000
        )
        state = self.engine.calculate_candle_state(candle)
        assert state.is_valid
        assert state.chart_range == 20
        assert state.color is not None
    
    def test_calculate_dataframe_states(self):
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h', tz='UTC'),
            'open': np.random.uniform(90, 110, 100),
            'high': np.random.uniform(100, 120, 100),
            'low': np.random.uniform(80, 100, 100),
            'close': np.random.uniform(90, 110, 100),
            'volume': np.random.uniform(100, 1000, 100)
        })
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        result = self.engine.calculate_dataframe_states(df)
        
        assert 'color' in result.columns
        assert 'efficiency' in result.columns
        assert 'pressure' in result.columns
        assert len(result) == len(df)
    
    def test_get_color_map(self):
        color_map = self.engine.get_color_map()
        assert 'blue' in color_map
        assert 'red' in color_map
        assert 'yellow' in color_map


class TestEdgeCases:
    def test_zero_range_candle(self):
        engine = MarketDNAEngine()
        candle = Candle(
            timestamp=pd.Timestamp('2024-01-01', tz='UTC'),
            open=100, high=100, low=100, close=100, volume=1000
        )
        state = engine.calculate_candle_state(candle)
        assert state.is_valid
        assert state.chart_range == 0
    
    def test_very_large_numbers(self):
        engine = MarketDNAEngine()
        candle = Candle(
            timestamp=pd.Timestamp('2024-01-01', tz='UTC'),
            open=1000000, high=2000000, low=500000, close=1500000, volume=1000
        )
        state = engine.calculate_candle_state(candle)
        assert state.is_valid
        assert state.chart_range == 1500000
