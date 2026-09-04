"""
IdeaForge - Data Loaders

Unified interface for loading market data from various sources.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class DataLoadResult:
    """Result of data loading operation."""
    data: pd.DataFrame
    source: str
    rows_loaded: int
    rows_dropped: int
    warnings: List[str]
    errors: List[str]

    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.rows_loaded > 0


class DataLoader:
    """Unified data loader for market data."""

    REQUIRED_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

    def __init__(self, timezone: str = 'UTC'):
        self.timezone = timezone
        self._warnings: List[str] = []
        self._errors: List[str] = []

    def load(self, path):
        """Load data from file path."""
        path = Path(path)
        self._warnings = []
        self._errors = []

        if not path.exists():
            return DataLoadResult(
                data=pd.DataFrame(), source=str(path), rows_loaded=0,
                rows_dropped=0, warnings=[], errors=[f"File not found: {path}"]
            )

        try:
            if path.suffix.lower() == '.csv':
                df = self._load_csv(path)
            elif path.suffix.lower() in ['.parquet', '.pq']:
                df = self._load_parquet(path)
            else:
                return DataLoadResult(
                    data=pd.DataFrame(), source=str(path), rows_loaded=0,
                    rows_dropped=0, warnings=[], errors=[f"Unsupported format: {path.suffix}"]
                )

            if df.empty:
                return DataLoadResult(
                    data=df, source=str(path), rows_loaded=0, rows_dropped=0,
                    warnings=self._warnings, errors=["No data loaded"]
                )

            original_rows = len(df)
            df = self._normalize_columns(df)
            df = self._validate_and_clean(df)
            rows_dropped = original_rows - len(df)

            return DataLoadResult(
                data=df, source=str(path), rows_loaded=len(df),
                rows_dropped=rows_dropped, warnings=self._warnings, errors=self._errors
            )

        except Exception as e:
            return DataLoadResult(
                data=pd.DataFrame(), source=str(path), rows_loaded=0,
                rows_dropped=0, warnings=self._warnings, errors=[f"Error: {str(e)}"]
            )

    def _load_csv(self, path):
        """Load data from CSV file."""
        df = pd.read_csv(path)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'], utc=True)
            df = df.drop(columns=['date'])
        elif 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'], utc=True)
            df = df.drop(columns=['time'])
        return df

    def _load_parquet(self, path):
        """Load data from Parquet file."""
        df = pd.read_parquet(path)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        return df

    def _normalize_columns(self, df):
        """Normalize column names."""
        df.columns = df.columns.str.lower().str.strip()
        column_map = {'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume',
                      'vol': 'volume', 'qty': 'volume'}
        return df.rename(columns=column_map)

    def _validate_and_clean(self, df):
        """Validate and clean the data."""
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self._errors.append(f"Missing required columns: {missing_cols}")
            return pd.DataFrame()

        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)

        duplicates = df.duplicated(subset=['timestamp'], keep='first')
        if duplicates.any():
            self._warnings.append(f"Removed {duplicates.sum()} duplicate timestamps")
            df = df[~duplicates].reset_index(drop=True)

        invalid_mask = (
            (df['high'] < df['low']) | (df['high'] < df['open']) |
            (df['high'] < df['close']) | (df['low'] > df['open']) | (df['low'] > df['close'])
        )
        if invalid_mask.any():
            self._warnings.append(f"Removed {invalid_mask.sum()} rows with invalid OHLC")
            df = df[~invalid_mask].reset_index(drop=True)

        nan_mask = df[self.REQUIRED_COLUMNS].isna().any(axis=1)
        if nan_mask.any():
            self._warnings.append(f"Removed {nan_mask.sum()} rows with NaN")
            df = df[~nan_mask].reset_index(drop=True)

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df.dropna(subset=self.REQUIRED_COLUMNS).reset_index(drop=True)

    def generate_sample_data(self, n_candles=1000, start_price=50000.0,
                            volatility=0.02, trend=0.0001):
        """Generate sample OHLCV data for testing."""
        np.random.seed(42)
        timestamps = pd.date_range(start='2024-01-01', periods=n_candles, freq='1h', tz='UTC')
        returns = np.random.normal(trend, volatility, n_candles)
        close_prices = start_price * np.cumprod(1 + returns)
        high_prices = close_prices * (1 + np.abs(np.random.normal(0, volatility * 0.5, n_candles)))
        low_prices = close_prices * (1 - np.abs(np.random.normal(0, volatility * 0.5, n_candles)))
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = start_price
        high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
        low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
        volume = np.random.exponential(100, n_candles) * (1 + np.abs(returns) * 10)
        return pd.DataFrame({
            'timestamp': timestamps, 'open': open_prices, 'high': high_prices,
            'low': low_prices, 'close': close_prices, 'volume': volume
        })
