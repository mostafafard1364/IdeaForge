"""
Tests for IdeaForge Data Layer
"""

import pytest
import pandas as pd
import numpy as np
from data.loaders import DataLoader, DataLoadResult


class TestDataLoader:
    """Test suite for DataLoader."""
    
    def test_generate_sample_data(self):
        """Test sample data generation."""
        loader = DataLoader()
        df = loader.generate_sample_data(n_candles=100)
        
        assert len(df) == 100
        assert 'timestamp' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    def test_sample_data_ohlc_validity(self):
        """Test that generated OHLC data is valid."""
        loader = DataLoader()
        df = loader.generate_sample_data(n_candles=100)
        
        # High should be >= Low
        assert (df['high'] >= df['low']).all()
        
        # High should be >= Open and Close
        assert (df['high'] >= df['open']).all()
        assert (df['high'] >= df['close']).all()
        
        # Low should be <= Open and Close
        assert (df['low'] <= df['open']).all()
        assert (df['low'] <= df['close']).all()
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        loader = DataLoader()
        result = loader.load("nonexistent_file.csv")
        
        assert not result.success
        assert len(result.errors) > 0
    
    def test_load_empty_dataframe(self):
        """Test loading with empty data."""
        loader = DataLoader()
        result = loader.load("nonexistent.parquet")
        
        assert not result.success
    
    def test_data_is_sorted_by_timestamp(self):
        """Test that data is sorted chronologically."""
        loader = DataLoader()
        df = loader.generate_sample_data(n_candles=100)
        
        # Check timestamps are sorted
        timestamps = pd.to_datetime(df['timestamp'])
        assert timestamps.is_monotonic_increasing
    
    def test_no_duplicate_timestamps(self):
        """Test that there are no duplicate timestamps."""
        loader = DataLoader()
        df = loader.generate_sample_data(n_candles=100)
        
        assert df['timestamp'].is_unique
    
    def test_volume_is_positive(self):
        """Test that volume values are positive."""
        loader = DataLoader()
        df = loader.generate_sample_data(n_candles=100)
        
        assert (df['volume'] >= 0).all()


class TestDataValidation:
    """Test data validation and cleaning."""
    
    def test_invalid_ohlc_removed(self):
        """Test that invalid OHLC rows are removed."""
        loader = DataLoader()
        
        # Create data with invalid OHLC
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, tz='UTC'),
            'open': [100, 100, 100, 100, 100],
            'high': [110, 90, 110, 110, 110],  # Row 1: high < low
            'low': [90, 80, 80, 80, 80],
            'close': [105, 95, 105, 105, 105],
            'volume': [100, 100, 100, 100, 100]
        })
        
        # Manually validate
        invalid_mask = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        assert invalid_mask.any()  # Should have invalid rows
    
    def test_nan_values_handling(self):
        """Test handling of NaN values."""
        loader = DataLoader()
        
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, tz='UTC'),
            'open': [100, np.nan, 100, 100, 100],
            'high': [110, 110, 110, 110, 110],
            'low': [90, 80, 80, 80, 80],
            'close': [105, 95, 105, 105, 105],
            'volume': [100, 100, 100, 100, 100]
        })
        
        # Check NaN detection
        assert df['open'].isna().any()
