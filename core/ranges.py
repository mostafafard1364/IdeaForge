"""
IdeaForge - Range Detection

Detects consolidation ranges and breakout patterns.
"""

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import numpy as np


@dataclass
class PriceRange:
    """Detected price range."""
    start_idx: int
    end_idx: int
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    high: float
    low: float
    mid: float
    width: float
    candle_count: int
    is_valid: bool = True


@dataclass
class Breakout:
    """Detected breakout from range."""
    range_idx: int
    timestamp: pd.Timestamp
    direction: str  # 'up' or 'down'
    price: float
    range_high: float
    range_low: float
    strength: float


class RangeDetector:
    """
    Detects consolidation ranges and breakouts.
    
    A range is defined as price moving within a bounded area
    for a minimum number of candles.
    """
    
    def __init__(
        self,
        min_candles: int = 10,
        max_candle_width_pct: float = 0.02,
        breakout_threshold_pct: float = 0.005
    ):
        self.min_candles = min_candles
        self.max_candle_width_pct = max_candle_width_pct
        self.breakout_threshold_pct = breakout_threshold_pct
    
    def detect_ranges(self, df: pd.DataFrame) -> List[PriceRange]:
        """
        Detect all consolidation ranges in the data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected PriceRange objects
        """
        ranges = []
        
        if len(df) < self.min_candles:
            return ranges
        
        # Rolling window approach
        i = 0
        while i < len(df) - self.min_candles:
            window = df.iloc[i:i + self.min_candles]
            
            high = window['high'].max()
            low = window['low'].min()
            mid = (high + low) / 2
            width = high - low
            
            # Check if range is tight enough
            avg_price = window['close'].mean()
            width_pct = width / avg_price if avg_price > 0 else 1.0
            
            if width_pct <= self.max_candle_width_pct:
                # Extend range as far as possible
                end_idx = i + self.min_candles
                while end_idx < len(df):
                    next_high = max(high, df.iloc[end_idx]['high'])
                    next_low = min(low, df.iloc[end_idx]['low'])
                    next_width = next_high - next_low
                    next_pct = next_width / avg_price if avg_price > 0 else 1.0
                    
                    if next_pct <= self.max_candle_width_pct:
                        high = next_high
                        low = next_low
                        end_idx += 1
                    else:
                        break
                
                mid = (high + low) / 2
                
                price_range = PriceRange(
                    start_idx=i,
                    end_idx=end_idx - 1,
                    start_time=window['timestamp'].iloc[0] if 'timestamp' in df.columns else pd.NaT,
                    end_time=df.iloc[end_idx - 1]['timestamp'] if 'timestamp' in df.columns else pd.NaT,
                    high=high,
                    low=low,
                    mid=mid,
                    width=width,
                    candle_count=end_idx - i
                )
                ranges.append(price_range)
                i = end_idx
            else:
                i += 1
        
        return ranges
    
    def detect_breakouts(self, df: pd.DataFrame, ranges: List[PriceRange]) -> List[Breakout]:
        """
        Detect breakouts from detected ranges.
        
        Args:
            df: DataFrame with OHLCV data
            ranges: List of PriceRange objects
            
        Returns:
            List of detected Breakout objects
        """
        breakouts = []
        
        for i, price_range in enumerate(ranges):
            # Check candle after range
            breakout_idx = price_range.end_idx + 1
            if breakout_idx >= len(df):
                continue
            
            candle = df.iloc[breakout_idx]
            threshold = price_range.width * self.breakout_threshold_pct
            
            # Upward breakout
            if candle['close'] > price_range.high + threshold:
                strength = (candle['close'] - price_range.high) / price_range.width if price_range.width > 0 else 0
                breakout = Breakout(
                    range_idx=i,
                    timestamp=candle['timestamp'] if 'timestamp' in df.columns else pd.NaT,
                    direction='up',
                    price=candle['close'],
                    range_high=price_range.high,
                    range_low=price_range.low,
                    strength=strength
                )
                breakouts.append(breakout)
            
            # Downward breakout
            elif candle['close'] < price_range.low - threshold:
                strength = (price_range.low - candle['close']) / price_range.width if price_range.width > 0 else 0
                breakout = Breakout(
                    range_idx=i,
                    timestamp=candle['timestamp'] if 'timestamp' in df.columns else pd.NaT,
                    direction='down',
                    price=candle['close'],
                    range_high=price_range.high,
                    range_low=price_range.low,
                    strength=strength
                )
                breakouts.append(breakout)
        
        return breakouts
