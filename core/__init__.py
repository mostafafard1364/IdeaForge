"""
IdeaForge - Core Market Data Structures
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import pandas as pd
import numpy as np


class MarketColor(Enum):
    """Market DNA color states."""
    YELLOW = "yellow"      # Weak
    PINK = "pink"          # Medium
    BLUE = "blue"          # Strong bullish
    RED = "red"            # Strong bearish
    WHITE = "white"        # High pressure / compressed
    GREEN = "green"        # Uniform / consistent
    GRAY = "gray"          # Undefined / neutral


class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    COMPRESSED = "compressed"
    EXPANDING = "expanding"
    UNKNOWN = "unknown"


@dataclass
class Candle:
    """Single OHLCV candle."""
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def chart_range(self) -> float:
        """High - Low"""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Close - Open"""
        return self.close - self.open
    
    @property
    def body_abs(self) -> float:
        """Absolute body size"""
        return abs(self.body)
    
    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        return abs(self.body) <= self.chart_range * 0.1 if self.chart_range > 0 else True


@dataclass
class MarketState:
    """Complete market state for a single candle."""
    # Core measurements
    chart_range: float = 0.0
    system_bar: float = 0.0
    net_movement: float = 0.0
    up_total: float = 0.0
    down_total: float = 0.0
    
    # Derived metrics
    efficiency: float = 0.0
    ratio: float = 0.0
    pressure: float = 0.0
    
    # Classifications
    color: MarketColor = MarketColor.GRAY
    regime: MarketRegime = MarketRegime.UNKNOWN
    strength: float = 0.0
    direction: float = 0.0  # -1 to 1
    
    # Metadata
    is_valid: bool = True
    error_message: Optional[str] = None


@dataclass
class SystemBarResult:
    """Result of system bar calculation."""
    up_total: float = 0.0
    down_total: float = 0.0
    net_movement: float = 0.0
    system_bar: float = 0.0
    
    @property
    def efficiency(self) -> float:
        """Calculate efficiency with safe division."""
        if self.system_bar == 0:
            return 0.0
        return abs(self.net_movement) / self.system_bar
    
    @property
    def direction(self) -> float:
        """Direction from -1 (all down) to 1 (all up)."""
        if self.system_bar == 0:
            return 0.0
        return self.net_movement / self.system_bar


def calculate_system_bar(prices: np.ndarray) -> SystemBarResult:
    """
    Calculate system bar from a sequence of prices.
    
    The system bar represents the total absolute internal movement
    inside the aggregation period.
    
    Args:
        prices: Array of price values
        
    Returns:
        SystemBarResult with all components
    """
    if len(prices) < 2:
        return SystemBarResult()
    
    # Calculate price differences
    deltas = np.diff(prices)
    
    # Sum of upward movements
    up_total = np.sum(deltas[deltas > 0]) if np.any(deltas > 0) else 0.0
    
    # Sum of absolute downward movements
    down_total = np.sum(np.abs(deltas[deltas < 0])) if np.any(deltas < 0) else 0.0
    
    # Net movement
    net_movement = up_total - down_total
    
    # System bar (total absolute movement)
    system_bar = up_total + down_total
    
    return SystemBarResult(
        up_total=float(up_total),
        down_total=float(down_total),
        net_movement=float(net_movement),
        system_bar=float(system_bar)
    )


def calculate_efficiency(system_bar: float, net_movement: float) -> float:
    """
    Calculate efficiency with safe division.
    
    efficiency = abs(net_movement) / system_bar
    
    Args:
        system_bar: Total absolute movement
        net_movement: Net directional movement
        
    Returns:
        Efficiency value between 0 and 1
    """
    if system_bar == 0:
        return 0.0
    return abs(net_movement) / system_bar


def calculate_ratio(system_bar: float, chart_range: float) -> float:
    """
    Calculate ratio with safe division.
    
    ratio = system_bar / chart_range
    
    Args:
        system_bar: Total absolute movement
        chart_range: High - Low of the period
        
    Returns:
        Ratio value (>= 1.0 means more internal movement than visible range)
    """
    if chart_range == 0:
        return 0.0
    return system_bar / chart_range


def calculate_pressure(efficiency: float, ratio: float) -> float:
    """
    Calculate market pressure.
    
    High pressure = low efficiency + high ratio
    (market is compressed, building energy)
    
    Args:
        efficiency: Movement efficiency (0-1)
        ratio: System bar to chart range ratio
        
    Returns:
        Pressure value (0-1, higher = more pressure)
    """
    # Pressure is inverse of efficiency, scaled by ratio
    if ratio == 0:
        return 0.0
    return (1 - efficiency) * min(ratio / 2.0, 1.0)
