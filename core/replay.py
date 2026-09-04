
"""
IdeaForge - Replay Mode

Replays historical market data progressively.
Prevents look-ahead bias by only revealing data that would be available at each moment.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import pandas as pd
import copy
import sys

@dataclass
class ReplayState:
    """State during replay."""
    current_index: int = 0
    current_timestamp: pd.Timestamp = None
    revealed_data: pd.DataFrame = None
    position: Optional[dict] = None
    capital: float = 0.0
    trades: List = field(default_factory=list)
    step_count: int = 0


class ReplayEngine:
    """Historical replay engine."""

    def __init__(self, df, initial_capital=10000.0):
        self._original_df = df.copy()
        self._initial_capital = initial_capital
        self._state = ReplayState(
            current_index=0,
            current_timestamp=df.iloc[0]['timestamp'] if len(df) > 0 else pd.NaT,
            revealed_data=df.iloc[:1].copy() if len(df) > 0 else pd.DataFrame(),
            capital=initial_capital
        )
        self._history = []

    @property
    def state(self):
        return self._state

    def step(self):
        """Advance replay by one step."""
        if self._state.current_index >= len(self._original_df) - 1:
            return False
        self._history.append(copy.deepcopy(self._state))
        self._state.current_index += 1
        self._state.current_timestamp = self._original_df.iloc[self._state.current_index]['timestamp']
        self._state.revealed_data = self._original_df.iloc[:self._state.current_index + 1].copy()
        self._state.step_count += 1
        return True

    def step_n(self, n):
        """Advance replay by n steps."""
        steps = 0
        for _ in range(n):
            if not self.step():
                break
            steps += 1
        return steps

    def jump_to(self, timestamp):
        """Jump to specific timestamp."""
        for i in range(len(self._original_df)):
            ts = pd.Timestamp(self._original_df.iloc[i]['timestamp'])
            if ts >= timestamp:
                self._state.current_index = i
                self._state.current_timestamp = ts
                self._state.revealed_data = self._original_df.iloc[:i + 1].copy()
                return True
        return False

    def reset(self):
        """Reset replay to beginning."""
        self._state = ReplayState(
            current_index=0,
            current_timestamp=self._original_df.iloc[0]['timestamp'] if len(self._original_df) > 0 else pd.NaT,
            revealed_data=self._original_df.iloc[:1].copy() if len(self._original_df) > 0 else pd.DataFrame(),
            capital=self._initial_capital
        )
        self._history = []

    def get_revealed_data(self):
        """Get only the data revealed so far."""
        return self._state.revealed_data.copy()

    def get_progress(self):
        """Get replay progress information."""
        total = len(self._original_df)
        current = self._state.current_index + 1
        return {
            'current': current,
            'total': total,
            'progress_pct': (current / total * 100) if total > 0 else 0,
            'timestamp': self._state.current_timestamp,
            'steps': self._state.step_count
        }

    def can_step_back(self):
        """Check if we can step backward."""
        return len(self._history) > 0

    def step_back(self):
        """Go back one step."""
        if not self._history:
            return False
        self._state = self._history.pop()
        return True
