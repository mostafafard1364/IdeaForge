"""
IdeaForge - Backtest Engine

Standardized backtesting interface.
Uses the same MarketDNA calculations as the chart.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import pandas as pd
import numpy as np


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Trade:
    """Single completed trade."""
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: TradeDirection
    entry_price: float
    exit_price: float
    size: float = 1.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fees: float = 0.0
    holding_periods: int = 0
    exit_reason: str = ""


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    initial_capital: float = 10000.0
    fee_pct: float = 0.001
    slippage_pct: float = 0.0005
    position_size_pct: float = 0.95
    allow_short: bool = True
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


@dataclass
class BacktestResult:
    """Complete backtest results."""
    trades: List[Trade] = field(default_factory=list)
    total_return_pct: float = 0.0
    total_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown: float = 0.0
    avg_trade: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    long_trades: int = 0
    short_trades: int = 0
    long_win_rate: float = 0.0
    short_win_rate: float = 0.0
    equity_curve: Optional[pd.Series] = None
    
    @property
    @property
    def sharpe_ratio(self) -> float:
        if self.equity_curve is None or len(self.equity_curve) < 2:
            return 0.0
        returns = self.equity_curve.pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        return np.sqrt(252) * returns.mean() / returns.std()


class BacktestEngine:
    """Backtesting engine using same MarketDNA calculations as chart."""
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
    
    def run(self, df: pd.DataFrame, signals: Optional[pd.Series] = None) -> BacktestResult:
        """Run backtest on DataFrame with signals."""
        result = BacktestResult()
        
        if df.empty:
            return result
        
        if signals is None:
            if 'signal' not in df.columns:
                return result
            signals = df['signal']
        
        trades = []
        position = None
        capital = self.config.initial_capital
        
        for i in range(len(df)):
            row = df.iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 'none'
            price = row['close']
            timestamp = row['timestamp'] if 'timestamp' in df.columns else pd.NaT
            
            if position is not None:
                exit_reason = self._check_exit(position, row, signal)
                if exit_reason:
                    trade = self._close_position(position, price, timestamp, i, exit_reason)
                    trades.append(trade)
                    capital += trade.pnl
                    position = None

            if position is None:
                if signal == 'entry_long':
                    position = self._open_position(TradeDirection.LONG, price, timestamp, i, capital)
                elif signal == 'entry_short' and self.config.allow_short:
                    position = self._open_position(TradeDirection.SHORT, price, timestamp, i, capital)

        if position is not None:
            price = df.iloc[-1]['close']
            timestamp = df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else pd.NaT
            trade = self._close_position(position, price, timestamp, len(df) - 1, 'end_of_data')
            trades.append(trade)

        result.trades = trades
        result = self._calculate_statistics(result, capital)
        return result
    
    def _check_exit(self, position: Dict, row: pd.Series, signal: str) -> Optional[str]:
        """Check if position should be exited."""
        if self.config.stop_loss_pct:
            if position['direction'] == TradeDirection.LONG:
                stop_price = position['entry_price'] * (1 - self.config.stop_loss_pct)
                if row['low'] <= stop_price:
                    return 'stop_loss'
            else:
                stop_price = position['entry_price'] * (1 + self.config.stop_loss_pct)
                if row['high'] >= stop_price:
                    return 'stop_loss'
        
        if self.config.take_profit_pct:
            if position['direction'] == TradeDirection.LONG:
                tp_price = position['entry_price'] * (1 + self.config.take_profit_pct)
                if row['high'] >= tp_price:
                    return 'take_profit'
            else:
                tp_price = position['entry_price'] * (1 - self.config.take_profit_pct)
                if row['low'] <= tp_price:
                    return 'take_profit'
        
        if position['direction'] == TradeDirection.LONG and signal in ['entry_short', 'exit_long']:
            return 'signal'
        elif position['direction'] == TradeDirection.SHORT and signal in ['entry_long', 'exit_short']:
            return 'signal'
        
        return None
    
    def _open_position(
        self, direction: TradeDirection, price: float,
        timestamp: pd.Timestamp, idx: int, capital: float
    ) -> Dict:
        """Open a new position."""
        if direction == TradeDirection.LONG:
            fill_price = price * (1 + self.config.slippage_pct)
        else:
            fill_price = price * (1 - self.config.slippage_pct)
        
        position_size = capital * self.config.position_size_pct / fill_price
        
        return {
            'direction': direction,
            'entry_price': fill_price,
            'entry_time': timestamp,
            'entry_idx': idx,
            'size': position_size,
            'fees': capital * self.config.position_size_pct * self.config.fee_pct
        }
    
    def _close_position(
        self, position: Dict, price: float,
        timestamp: pd.Timestamp, idx: int, reason: str
    ) -> Trade:
        """Close an existing position."""
        if position['direction'] == TradeDirection.LONG:
            fill_price = price * (1 - self.config.slippage_pct)
            pnl = (fill_price - position['entry_price']) * position['size']
            pnl_pct = (fill_price / position['entry_price'] - 1) * 100
        else:
            fill_price = price * (1 + self.config.slippage_pct)
            pnl = (position['entry_price'] - fill_price) * position['size']
            pnl_pct = (position['entry_price'] / fill_price - 1) * 100
        
        exit_fee = fill_price * position['size'] * self.config.fee_pct
        total_fees = position['fees'] + exit_fee
        pnl -= total_fees
        
        return Trade(
            entry_time=position['entry_time'],
            exit_time=timestamp,
            direction=position['direction'],
            entry_price=position['entry_price'],
            exit_price=fill_price,
            size=position['size'],
            pnl=pnl,
            pnl_pct=pnl_pct - (total_fees / (position['entry_price'] * position['size'])) * 100,
            fees=total_fees,
            holding_periods=idx - position['entry_idx'],
            exit_reason=reason
        )
    
    def _calculate_statistics(self, result: BacktestResult, final_capital: float) -> BacktestResult:
        """Calculate all backtest statistics."""
        trades = result.trades
        result.total_trades = len(trades)
        
        if not trades:
            return result
        
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = len(wins) / len(trades) * 100 if trades else 0
        
        result.gross_profit = sum(t.pnl for t in wins) if wins else 0
        result.gross_loss = sum(t.pnl for t in losses) if losses else 0
        result.net_profit = result.gross_profit + result.gross_loss
        result.profit_factor = abs(result.gross_profit / result.gross_loss) if result.gross_loss != 0 else float('inf')
        
        result.total_return = final_capital - self.config.initial_capital
        result.total_return_pct = (final_capital / self.config.initial_capital - 1) * 100
        
        result.avg_trade = result.net_profit / len(trades)
        result.avg_win = result.gross_profit / len(wins) if wins else 0
        result.avg_loss = result.gross_loss / len(losses) if losses else 0
        result.expectancy = (result.win_rate / 100 * result.avg_win) + ((1 - result.win_rate / 100) * result.avg_loss)
        
        long_trades = [t for t in trades if t.direction == TradeDirection.LONG]
        short_trades = [t for t in trades if t.direction == TradeDirection.SHORT]
        result.long_trades = len(long_trades)
        result.short_trades = len(short_trades)
        
        if long_trades:
            result.long_win_rate = sum(1 for t in long_trades if t.pnl > 0) / len(long_trades) * 100
        if short_trades:
            result.short_win_rate = sum(1 for t in short_trades if t.pnl > 0) / len(short_trades) * 100
        
        return result

    def sharpe_ratio(self) -> float:
        if self.equity_curve is None or len(self.equity_curve) < 2:
            return 0.0
        returns = self.equity_curve.pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        return np.sqrt(252) * returns.mean() / returns.std()
