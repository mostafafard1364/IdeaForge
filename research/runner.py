"""
IdeaForge - Experiment Runner

Executes experiments using the MarketDNA engine.
"""

from typing import Optional, Dict, Any
import pandas as pd

from core.market_dna import MarketDNAEngine, MarketDNAConfig
from core.signals import SignalEngine
from backtest.engine import BacktestEngine, BacktestConfig
from research.registry import ExperimentRegistry, Experiment, ExperimentStatus


class ExperimentRunner:
    """
    Runs experiments end-to-end.
    
    Workflow:
    1. Load data
    2. Calculate MarketDNA
    3. Generate signals
    4. Run backtest
    5. Save results
    """
    
    def __init__(
        self,
        registry: Optional[ExperimentRegistry] = None,
        dna_config: Optional[MarketDNAConfig] = None,
        backtest_config: Optional[BacktestConfig] = None
    ):
        self.registry = registry or ExperimentRegistry()
        self.dna_engine = MarketDNAEngine(dna_config)
        self.signal_engine = SignalEngine()
        self.backtest_engine = BacktestEngine(backtest_config)
    
    def run_experiment(
        self,
        experiment: Experiment,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run a complete experiment.
        
        Args:
            experiment: Experiment definition
            data: OHLCV DataFrame
            
        Returns:
            Dictionary with experiment results
        """
        results = {
            'experiment_id': experiment.id,
            'success': False,
            'error': None,
            'metrics': {},
            'data': None
        }
        
        try:
            # Update status
            self.registry.update(experiment.id, status=ExperimentStatus.RUNNING.value)
            
            # Step 1: Calculate MarketDNA
            df = self.dna_engine.calculate_dataframe_states(data)
            
            # Step 2: Generate signals
            params = experiment.parameters
            entry_color = params.get('entry_color', 'blue')
            exit_color = params.get('exit_color', 'red')
            min_strength = params.get('min_strength', 0.5)
            
            df = self.signal_engine.generate_signals(
                df, entry_color=entry_color, exit_color=exit_color, min_strength=min_strength
            )
            
            # Step 3: Run backtest
            bt_config = BacktestConfig(
                initial_capital=params.get('initial_capital', 10000),
                fee_pct=params.get('fee_pct', 0.001),
                slippage_pct=params.get('slippage_pct', 0.0005),
                allow_short=params.get('allow_short', True)
            )
            self.backtest_engine = BacktestEngine(bt_config)
            bt_result = self.backtest_engine.run(df)
            
            # Compile results
            results['metrics'] = {
                'total_trades': bt_result.total_trades,
                'win_rate': round(bt_result.win_rate, 2),
                'profit_factor': round(bt_result.profit_factor, 3),
                'net_profit': round(bt_result.net_profit, 2),
                'total_return_pct': round(bt_result.total_return_pct, 2),
                'max_drawdown_pct': round(bt_result.max_drawdown_pct, 2),
                'avg_trade': round(bt_result.avg_trade, 2),
                'expectancy': round(bt_result.expectancy, 2),
                'long_trades': bt_result.long_trades,
                'short_trades': bt_result.short_trades,
            }
            
            # Determine conclusion
            if bt_result.total_trades < 10:
                conclusion = ExperimentStatus.INCONCLUSIVE.value
                result_summary = "Insufficient trades for conclusion"
            elif bt_result.profit_factor > 1.2 and bt_result.win_rate > 45:
                conclusion = ExperimentStatus.ACCEPTED.value
                result_summary = "Positive expectancy strategy"
            elif bt_result.profit_factor < 0.9:
                conclusion = ExperimentStatus.REJECTED.value
                result_summary = "Negative expectancy strategy"
            else:
                conclusion = ExperimentStatus.INCONCLUSIVE.value
                result_summary = "Marginal results, needs refinement"
            
            results['success'] = True
            results['conclusion'] = conclusion
            results['result_summary'] = result_summary
            results['data'] = df
            
            # Update experiment
            self.registry.update(
                experiment.id,
                status=conclusion,
                metrics=results['metrics'],
                result_summary=result_summary
            )
            
        except Exception as e:
            results['error'] = str(e)
            self.registry.update(
                experiment.id,
                status=ExperimentStatus.FAILED.value,
                result_summary=f"Error: {str(e)}"
            )
        
        return results
