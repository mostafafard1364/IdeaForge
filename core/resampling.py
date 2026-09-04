"""
IdeaForge - Resampling Engine

Centralized timeframe resampling for market data.
Ensures correct OHLCV aggregation without look-ahead bias.
"""

import pandas as pd
from typing import Optional, Dict


# Supported timeframes
SUPPORTED_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d']

# Pandas frequency mapping
FREQ_MAP = {
    '1m': '1min',
    '3m': '3min',
    '5m': '5min',
    '15m': '15min',
    '30m': '30min',
    '1h': '1h',
    '2h': '2h',
    '4h': '4h',
    '1d': '1D',
}


class Resampler:
    """
    Centralized resampling engine.
    
    All timeframe conversions go through this single engine
    to ensure consistency and prevent look-ahead bias.
    """
    
    def __init__(self):
        self._freq_map = FREQ_MAP
    
    def resample(
        self,
        df: pd.DataFrame,
        target_tf: str,
        timestamp_col: str = 'timestamp'
    ) -> pd.DataFrame:
        """
        Resample DataFrame to target timeframe.
        
        Args:
            df: DataFrame with OHLCV data
            target_tf: Target timeframe (e.g., '1h', '4h', '1d')
            timestamp_col: Name of timestamp column
            
        Returns:
            Resampled DataFrame
            
        Raises:
            ValueError: If target timeframe is not supported
        """
        if target_tf not in self._freq_map:
            raise ValueError(
                f"Unsupported timeframe: {target_tf}. "
                f"Supported: {list(self._freq_map.keys())}"
            )
        
        if df.empty:
            return df
        
        # Ensure timestamp is index
        if timestamp_col in df.columns:
            df = df.set_index(timestamp_col)
        
        freq = self._freq_map[target_tf]
        
        # Aggregate OHLCV
        resampled = df.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Drop NaN rows (empty periods)
        resampled = resampled.dropna()
        
        # Reset index to get timestamp column back
        resampled = resampled.reset_index()
        
        return resampled
    
    def get_supported_timeframes(self) -> list:
        """Get list of supported timeframes."""
        return SUPPORTED_TIMEFRAMES.copy()
    
    def is_valid_timeframe(self, tf: str) -> bool:
        """Check if timeframe is valid."""
        return tf in self._freq_map
