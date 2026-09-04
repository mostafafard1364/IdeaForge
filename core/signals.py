"""
IdeaForge - Signal Engine

Generates trading signals based on market state.
All signals are derived from MarketDNA calculations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import pandas as pd
import numpy as np


class SignalType(Enum):
    """Types of trading signals."""
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    NONE = "none"


@dataclass
class Signal:
    """A trading signal."""
    timestamp: pd.Timestamp
    type: SignalType
    price: float
    strength: float = 0.0
    reason: str = ""
    
    def is_entry(self) -> bool:
        return self.type in [SignalType.ENTRY_LONG, SignalType.ENTRY_SHORT]
    
    def is_exit(self) -> bool:
        return self.type in [SignalType.EXIT_LONG, SignalType.EXIT_SHORT]
    
    def is_long(self) -> bool:
        return self.type in [SignalType.ENTRY_LONG, SignalType.EXIT_LONG]


class SignalEngine:
    """
    Signal generation engine.
    
    All signals are derived from MarketDNA state.
    No external logic is used.
    """
    
    def __init__(self):
        self._signal_history: List[Signal] = []
    
    def generate_signals(
        self,
        df: pd.DataFrame,
        entry_color: str = "blue",
        exit_color: str = "red",
        min_strength: float = 0.5
    ) -> pd.DataFrame:
        """
        Generate signals based on market color and strength.
        
        Args:
            df: DataFrame with market state columns
            entry_color: Color that triggers entry
            exit_color: Color that triggers exit
            min_strength: Minimum strength for signal
            
        Returns:
            DataFrame with added signal column
        """
        result = df.copy()
        
        if 'color' not in result.columns or 'strength' not in result.columns:
            result['signal'] = SignalType.NONE.value
            result['signal_strength'] = 0.0
            return result
        
        # Generate signals
        signals = []
        strengths = []
        
        for _, row in result.iterrows():
            signal = SignalType.NONE
            strength = 0.0
            
            color = row.get('color', '')
            str_val = row.get('strength', 0)
            
            if str_val >= min_strength:
                if color == entry_color:
                    signal = SignalType.ENTRY_LONG
                    strength = str_val
                elif color == exit_color:
                    signal = SignalType.ENTRY_SHORT
                    strength = str_val
            
            signals.append(signal.value)
            strengths.append(strength)
        
        result['signal'] = signals
        result['signal_strength'] = strengths
        
        return result
    
    def get_signal_list(self, df: pd.DataFrame) -> List[Signal]:
        """Extract list of non-zero signals from DataFrame."""
        signals = []
        
        if 'signal' not in df.columns:
            return signals
        
        for _, row in df.iterrows():
            sig_type = row.get('signal', SignalType.NONE.value)
            if sig_type != SignalType.NONE.value:
                signal = Signal(
                    timestamp=row.get('timestamp', pd.NaT),
                    type=SignalType(sig_type),
                    price=row.get('close', 0),
                    strength=row.get('signal_strength', 0),
                    reason=f"Color: {row.get('color', 'unknown')}"
                )
                signals.append(signal)
        
        return signals
