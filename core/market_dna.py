"""
IdeaForge - Market DNA Engine

This is the core engine that calculates all market measurements.
It is the SINGLE SOURCE OF TRUTH for all market calculations.

The same engine is used by:
- Chart visualization
- Backtesting
- Replay mode
- Experiment runner
"""

from dataclasses import dataclass
from typing import Optional, Dict
import pandas as pd
import numpy as np

from . import (
    Candle, MarketState, MarketColor, MarketRegime,
    calculate_system_bar, calculate_efficiency, calculate_ratio, calculate_pressure
)


@dataclass
class MarketDNAConfig:
    """Configuration for Market DNA calculations."""
    weak_threshold: float = 0.3
    medium_threshold: float = 0.5
    strong_threshold: float = 0.7
    pressure_threshold: float = 0.6
    uniform_threshold: float = 0.8
    direction_threshold: float = 0.3


class MarketDNAEngine:
    """
    Core Market DNA calculation engine.
    
    This engine calculates all market state measurements.
    It MUST be the single source of truth for all market calculations.
    """
    
    def __init__(self, config: Optional[MarketDNAConfig] = None):
        self.config = config or MarketDNAConfig()
    
    def calculate_candle_state(
        self,
        candle: Candle,
        intra_prices: Optional[np.ndarray] = None
    ) -> MarketState:
        """
        Calculate complete market state for a single candle.
        
        Args:
            candle: OHLCV candle data
            intra_prices: Optional intra-candle prices for system bar calculation
            
        Returns:
            MarketState with all measurements
        """
        state = MarketState()
        
        try:
            state.chart_range = candle.chart_range
            
            # Calculate system bar
            if intra_prices is not None and len(intra_prices) >= 2:
                sb_result = calculate_system_bar(intra_prices)
            else:
                typical_prices = np.array([
                    candle.open,
                    (candle.high + candle.low) / 2,
                    candle.close
                ])
                sb_result = calculate_system_bar(typical_prices)
            
            state.system_bar = sb_result.system_bar
            state.net_movement = sb_result.net_movement
            state.up_total = sb_result.up_total
            state.down_total = sb_result.down_total
            
            # Derived metrics
            state.efficiency = calculate_efficiency(state.system_bar, state.net_movement)
            state.ratio = calculate_ratio(state.system_bar, state.chart_range)
            state.pressure = calculate_pressure(state.efficiency, state.ratio)
            state.direction = sb_result.direction if sb_result.system_bar > 0 else 0.0
            state.strength = abs(state.direction)
            
            # Classify
            state.color = self._classify_color(state)
            state.regime = self._classify_regime(state)
            state.is_valid = True
            
        except Exception as e:
            state.is_valid = False
            state.error_message = str(e)
        
        return state

    def calculate_dataframe_states(
        self,
        df: pd.DataFrame,
        price_col: str = 'close'
    ) -> pd.DataFrame:
        """
        Calculate market states for entire DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            price_col: Column to use for system bar estimation
            
        Returns:
            DataFrame with added market state columns
        """
        result = df.copy()
        
        # Calculate movements
        if len(result) >= 2:
            deltas = result[price_col].diff()
            result['net_movement'] = deltas
            result['up_total'] = deltas.clip(lower=0).rolling(2).sum()
            result['down_total'] = (-deltas.clip(upper=0)).rolling(2).sum()
            result['system_bar'] = result['up_total'] + result['down_total']
        else:
            result['net_movement'] = 0.0
            result['up_total'] = 0.0
            result['down_total'] = 0.0
            result['system_bar'] = 0.0
        
        # Chart range
        result['chart_range'] = result['high'] - result['low']
        
        # Efficiency
        result['efficiency'] = np.where(
            result['system_bar'] > 0,
            result['net_movement'].abs() / result['system_bar'],
            0.0
        )
        
        # Ratio
        result['ratio'] = np.where(
            result['chart_range'] > 0,
            result['system_bar'] / result['chart_range'],
            0.0
        )
        
        # Pressure
        result['pressure'] = (1 - result['efficiency']) * (result['ratio'] / 2.0).clip(upper=1.0)
        
        # Direction
        result['direction'] = np.where(
            result['system_bar'] > 0,
            result['net_movement'] / result['system_bar'],
            0.0
        )
        
        # Strength
        result['strength'] = result['direction'].abs()
        
        # Color and regime classification
        classifications = result.apply(self._classify_row, axis=1)
        result['color'] = classifications.apply(lambda x: x['color'])
        result['regime'] = classifications.apply(lambda x: x['regime'])
        
        return result

    def _classify_color(self, state: MarketState) -> MarketColor:
        """Classify market color based on state measurements."""
        cfg = self.config
        
        if state.pressure > cfg.pressure_threshold and state.ratio > 1.0:
            return MarketColor.WHITE
        
        if state.efficiency > cfg.uniform_threshold and state.ratio < 1.2:
            return MarketColor.GREEN
        
        if state.strength > cfg.strong_threshold:
            if state.direction > cfg.direction_threshold:
                return MarketColor.BLUE
            elif state.direction < -cfg.direction_threshold:
                return MarketColor.RED
        
        if state.strength > cfg.medium_threshold:
            return MarketColor.PINK
        
        return MarketColor.YELLOW

    def _classify_regime(self, state: MarketState) -> MarketRegime:
        """Classify market regime."""
        if state.ratio < 0.8:
            return MarketRegime.COMPRESSED
        elif state.ratio > 1.5:
            return MarketRegime.EXPANDING
        elif state.strength > 0.6:
            if state.direction > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN
        else:
            return MarketRegime.RANGING

    def _classify_row(self, row: pd.Series) -> Dict[str, str]:
        """Classify color and regime from DataFrame row."""
        efficiency = row.get('efficiency', 0)
        ratio = row.get('ratio', 0)
        pressure = row.get('pressure', 0)
        direction = row.get('direction', 0)
        strength = row.get('strength', 0)
        
        cfg = self.config
        
        if pressure > cfg.pressure_threshold and ratio > 1.0:
            return {'color': MarketColor.WHITE.value, 'regime': MarketRegime.COMPRESSED.value}
        
        if efficiency > cfg.uniform_threshold and ratio < 1.2:
            return {'color': MarketColor.GREEN.value, 'regime': MarketRegime.RANGING.value}
        
        if strength > cfg.strong_threshold:
            if direction > cfg.direction_threshold:
                return {'color': MarketColor.BLUE.value, 'regime': MarketRegime.TRENDING_UP.value}
            elif direction < -cfg.direction_threshold:
                return {'color': MarketColor.RED.value, 'regime': MarketRegime.TRENDING_DOWN.value}
        
        if strength > cfg.medium_threshold:
            return {'color': MarketColor.PINK.value, 'regime': MarketRegime.RANGING.value}
        
        return {'color': MarketColor.YELLOW.value, 'regime': MarketRegime.RANGING.value}

    def get_color_map(self) -> Dict[str, str]:
        """Get mapping of color names to hex values."""
        return {
            MarketColor.YELLOW.value: '#FFD700',
            MarketColor.PINK.value: '#FF69B4',
            MarketColor.BLUE.value: '#1E90FF',
            MarketColor.RED.value: '#DC143C',
            MarketColor.WHITE.value: '#F5F5F5',
            MarketColor.GREEN.value: '#32CD32',
            MarketColor.GRAY.value: '#808080',
        }


