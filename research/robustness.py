"""
IdeaForge - Robustness Testing

Tests strategy robustness across parameters, timeframes, and market conditions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from itertools import product

from backtest.engine import BacktestEngine, BacktestConfig


@dataclass
class RobustnessResult:
    """Results from robustness testing."""
    parameter_sets: List[Dict] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)
    best_params: Dict = field(default_factory=dict)
    worst_params: Dict = field(default_factory=dict)
    stability_score: float = 0.0
    
    def get_summary(self) -> Dict:
        """Get summary statistics."""
        if not self.results:
            return {}
        
        pf_values = [r['profit_factor'] for r in self.results if r['profit_factor'] != float('inf')]
        wr_values = [r['win_rate'] for r in self.results]
        ret_values = [r['total_return_pct'] for r in self.results]
        
        return {
            'total_tests': len(self.results),
            'pf_mean': np.mean(pf_values) if pf_values else 0,
            'pf_std': np.std(pf_values) if pf_values else 0,
            'pf_min': min(pf_values) if pf_values else 0,
            'pf_max': max(pf_values) if pf_values else 0,
            'wr_mean': np.mean(wr_values) if wr_values else 0,
            'ret_mean': np.mean(ret_values) if ret_values else 0,
            'ret_std': np.std(ret_values) if ret_values else 0,
        }


class RobustnessTester:
    """Tests strategy robustness across parameter variations."""
    
    def parameter_sweep(
        self,
        df: pd.DataFrame,
        param_grid: Dict[str, List],
        base_config: Optional[BacktestConfig] = None
    ) -> RobustnessResult:
        """Run parameter sweep across grid of parameters."""
        result = RobustnessResult()
        result.parameter_sets = [dict(zip(param_grid.keys(), v)) for v in product(*param_grid.values())]
        
        for params in result.parameter_sets:
            config = base_config or BacktestConfig()
            
            if 'fee_pct' in params:
                config.fee_pct = params['fee_pct']
            if 'slippage_pct' in params:
                config.slippage_pct = params['slippage_pct']
            if 'stop_loss_pct' in params:
                config.stop_loss_pct = params['stop_loss_pct']
            if 'position_size_pct' in params:
                config.position_size_pct = params['position_size_pct']
            
            bt_engine = BacktestEngine(config)
            bt_result = bt_engine.run(df)
            
            result.results.append({
                'params': params,
                'total_trades': bt_result.total_trades,
                'win_rate': bt_result.win_rate,
                'profit_factor': bt_result.profit_factor,
                'total_return_pct': bt_result.total_return_pct,
                'max_drawdown_pct': bt_result.max_drawdown_pct,
                'net_profit': bt_result.net_profit,
            })
        
        if result.results:
            best_idx = max(range(len(result.results)), 
                          key=lambda i: result.results[i]['profit_factor'])
            worst_idx = min(range(len(result.results)), 
                           key=lambda i: result.results[i]['profit_factor'])
            
            result.best_params = result.results[best_idx]['params']
            result.worst_params = result.results[worst_idx]['params']
            
            summary = result.get_summary()
            if summary['pf_std'] > 0:
                result.stability_score = summary['pf_mean'] / summary['pf_std']
            else:
                result.stability_score = summary['pf_mean']
        
        return result
    
    def fee_sensitivity_test(
        self,
        df: pd.DataFrame,
        fee_range: Tuple[float, float, float] = (0.000, 0.005, 0.001)
    ) -> RobustnessResult:
        """Test sensitivity to transaction fees."""
        fees = list(np.arange(fee_range[0], fee_range[1], fee_range[2]))
        param_grid = {'fee_pct': fees}
        return self.parameter_sweep(df, param_grid)
    
    def time_period_test(
        self,
        df: pd.DataFrame,
        periods: int = 3
    ) -> RobustnessResult:
        """Test across different time periods (in-sample vs out-of-sample)."""
        if len(df) < periods * 10:
            return RobustnessResult()
        
        period_size = len(df) // periods
        results_by_period = []
        
        for i in range(periods):
            start = i * period_size
            end = (i + 1) * period_size if i < periods - 1 else len(df)
            period_df = df.iloc[start:end]
            
            config = BacktestConfig()
            bt_engine = BacktestEngine(config)
            bt_result = bt_engine.run(period_df)
            
            results_by_period.append({
                'period': i + 1,
                'start': str(df.iloc[start]['timestamp']),
                'end': str(df.iloc[end-1]['timestamp']),
                'total_trades': bt_result.total_trades,
                'win_rate': bt_result.win_rate,
                'profit_factor': bt_result.profit_factor,
                'total_return_pct': bt_result.total_return_pct,
            })
        
        result = RobustnessResult()
        result.results = results_by_period
        return result
