"""
IdeaForge - Main Dashboard

Streamlit-based research dashboard.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loaders import DataLoader
from core.market_dna import MarketDNAEngine, MarketDNAConfig
from core.resampling import Resampler
from core.signals import SignalEngine
from app.components.chart import ChartRenderer
from backtest.engine import BacktestEngine, BacktestConfig
from research.registry import ExperimentRegistry, ExperimentStatus
from research.runner import ExperimentRunner


# Page configuration
st.set_page_config(
    page_title="IdeaForge - Market Research Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00d4ff;
    }
    .metric-card {
        background: #1e2a3a;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }
    .success-text { color: #00ff88; }
    .danger-text { color: #ff4444; }
    .warning-text { color: #ffaa00; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'dna_engine' not in st.session_state:
        st.session_state.dna_engine = MarketDNAEngine()
    if 'chart_renderer' not in st.session_state:
        st.session_state.chart_renderer = ChartRenderer()
    if 'registry' not in st.session_state:
        st.session_state.registry = ExperimentRegistry()
    if 'runner' not in st.session_state:
    if 'runner' not in st.session_state:
        st.session_state.runner = ExperimentRunner(st.session_state.registry)


def sidebar_controls():
    """Render sidebar controls."""
    with st.sidebar:
        st.markdown('<p class="main-header">🧬 IdeaForge</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.subheader("📊 Data Source")
        data_option = st.radio("Select Data", ["Generate Sample", "Load from File"])
        
        if data_option == "Generate Sample":
            n_candles = st.slider("Number of Candles", 100, 5000, 1000)
            if st.button("Generate Data"):
                loader = DataLoader()
                st.session_state.data = loader.generate_sample_data(n_candles=n_candles)
                st.success(f"Generated {n_candles} candles")
        else:
            file_path = st.text_input("File Path", "data/samples/sample.csv")
            if st.button("Load Data"):
                loader = DataLoader()
                result = loader.load(file_path)
                if result.success:
                    st.session_state.data = result.data
                    st.success(f"Loaded {result.rows_loaded} rows")
                else:
                    st.error(f"Error: {result.errors[0]}")
        
        st.markdown("---")
        st.subheader("⏱️ Timeframe")
        resampler = Resampler()
        timeframe = st.selectbox("Select Timeframe", resampler.get_supported_timeframes(), index=5)
        
        st.markdown("---")
        st.subheader("🧬 Market DNA Config")
        config = MarketDNAConfig()
        config.weak_threshold = st.slider("Weak Threshold", 0.0, 1.0, 0.3)
        config.medium_threshold = st.slider("Medium Threshold", 0.0, 1.0, 0.5)
        config.strong_threshold = st.slider("Strong Threshold", 0.0, 1.0, 0.7)
        config.pressure_threshold = st.slider("Pressure Threshold", 0.0, 1.0, 0.6)
        st.session_state.dna_engine = MarketDNAEngine(config)
        
        return timeframe


def market_page():
    """Main market analysis page."""
    st.markdown('<p class="main-header">📈 Market Analysis</p>', unsafe_allow_html=True)
    
    if st.session_state.data is None:
        st.info("Please load data from the sidebar to begin analysis.")
        return
    
    data = st.session_state.data
    resampler = Resampler()
    if 'timestamp' in data.columns:
        processed = resampler.resample(data, '1h')
    else:
        processed = data
    
    df = st.session_state.dna_engine.calculate_dataframe_states(processed)
    with col2:
        sb_fig = st.session_state.chart_renderer.create_system_bar_chart(display_df)
        st.plotly_chart(sb_fig, use_container_width=True)


def research_page():
    """Research lab page."""
    st.markdown('<p class="main-header">🔬 Research Lab</p>', unsafe_allow_html=True)
    
    if st.session_state.processed_data is None:
        st.info("Please analyze market data first.")
        return
    
    df = st.session_state.processed_data
    
    st.subheader("Signal Generation")
    col1, col2, col3 = st.columns(3)
    with col1:
        entry_color = st.selectbox("Entry Color", ['blue', 'green', 'white'])
    with col2:
        exit_color = st.selectbox("Exit Color", ['red', 'yellow', 'pink'])
    with col3:
        min_strength = st.slider("Min Strength", 0.0, 1.0, 0.5)
    
    signal_engine = SignalEngine()
    df_with_signals = signal_engine.generate_signals(
        df, entry_color=entry_color, exit_color=exit_color, min_strength=min_strength
    )
    
    fig = st.session_state.chart_renderer.create_chart(
        col3.metric("Entry Short", sum(1 for s in signals if s.type.value == 'entry_short'))


def experiments_page():
    """Experiments management page."""
    st.markdown('<p class="main-header">🧪 Experiments</p>', unsafe_allow_html=True)
    registry = st.session_state.registry
    
    with st.expander("Create New Experiment"):
        with st.form("new_experiment"):
            name = st.text_input("Experiment Name")
            hypothesis = st.text_area("Hypothesis")
            description = st.text_area("Description")
            col1, col2 = st.columns(2)
            with col1:
                entry_color = st.selectbox("Entry Color", ['blue', 'green', 'white'])
            with col2:
                exit_color = st.selectbox("Exit Color", ['red', 'yellow', 'pink'])
            min_strength = st.slider("Min Strength", 0.0, 1.0, 0.5)
            
            submitted = st.form_submit_button("Create Experiment")
            if submitted and name:
                exp = registry.create(
                    name=name, hypothesis=hypothesis, description=description,
                    parameters={'entry_color': entry_color, 'exit_color': exit_color, 'min_strength': min_strength}
                )
                st.success(f"Created experiment: {exp.id}")
    
    st.subheader("Experiment Registry")
    experiments = registry.list_all()
    
    if experiments:
        for exp in experiments:
            with st.expander(f"{exp.id}: {exp.name} [{exp.status.upper()}]"):
                st.write(f"**Hypothesis:** {exp.hypothesis}")
                st.write(f"**Status:** {exp.status}")
                st.write(f"**Result:** {exp.result_summary}")
                if exp.metrics:
                    st.write("**Metrics:**")
                    st.json(exp.metrics)
                if st.button(f"Run {exp.id}", key=f"run_{exp.id}"):
                    if st.session_state.data is not None:
                        runner = st.session_state.runner
                        results = runner.run_experiment(exp, st.session_state.data)
                        if results['success']:
                            st.success(f"Completed: {results['conclusion']}")
                        else:
                            st.error(f"Failed: {results['error']}")
                    else:
                        st.warning("Please load data first.")
    else:
        st.info("No experiments yet.")


def backtest_page():
    """Backtest results page."""
    st.markdown('<p class="main-header">📊 Backtest</p>', unsafe_allow_html=True)
    
    if st.session_state.processed_data is None:
        st.info("Please analyze market data first.")
        return
    
    df = st.session_state.processed_data
    
    st.subheader("Backtest Configuration")
    col1, col2, col3 = st.columns(3)
    with col1:
        initial_capital = st.number_input("Initial Capital", 1000, 100000, 10000)
    with col2:
        fee_pct = st.number_input("Fee (%)", 0.0, 1.0, 0.1) / 100
    with col3:
        slippage_pct = st.number_input("Slippage (%)", 0.0, 1.0, 0.05) / 100
    
    signal_engine = SignalEngine()
    df_with_signals = signal_engine.generate_signals(df, entry_color='blue', exit_color='red')
    
    if st.button("Run Backtest"):
        config = BacktestConfig(
            initial_capital=initial_capital, fee_pct=fee_pct, slippage_pct=slippage_pct
        )
        engine = BacktestEngine(config)
        result = engine.run(df_with_signals)
        
        st.subheader("Backtest Results")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", result.total_trades)
        col2.metric("Win Rate", f"{result.win_rate:.1f}%")
        col3.metric("Profit Factor", f"{result.profit_factor:.2f}")
        col4.metric("Net Profit", f"${result.net_profit:.2f}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Return", f"{result.total_return_pct:.2f}%")
        col2.metric("Max Drawdown", f"{result.max_drawdown_pct:.2f}%")
        col3.metric("Avg Trade", f"${result.avg_trade:.2f}")
        col4.metric("Expectancy", f"${result.expectancy:.2f}")


def main():
    """Main application entry point."""
    init_session_state()
    timeframe = sidebar_controls()
    
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📈 Market", "🔬 Research Lab", "🧪 Experiments", "📊 Backtest"],
        horizontal=True, label_visibility="collapsed"
    )
    
    if page == "📈 Market":
        market_page()
    elif page == "🔬 Research Lab":
        research_page()
    elif page == "🧪 Experiments":
        experiments_page()
    elif page == "📊 Backtest":
        backtest_page()


if __name__ == "__main__":
    main()

        df_with_signals.tail(200), title="Signals Chart", show_volume=True, show_signals=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    signals = signal_engine.get_signal_list(df_with_signals)
    if signals:
        st.subheader("Signal Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Signals", len(signals))
        col2.metric("Entry Long", sum(1 for s in signals if s.type.value == 'entry_long'))
        col3.metric("Entry Short", sum(1 for s in signals if s.type.value == 'entry_short'))

    st.session_state.processed_data = df
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_volume = st.checkbox("Show Volume", value=True)
    with col2:
        show_signals = st.checkbox("Show Signals", value=False)
    with col3:
        colored_candles = st.checkbox("Colored Candles", value=True)
    with col4:
        n_display = st.slider("Candles to Display", 50, 500, 200)
    
    display_df = df.tail(n_display)
    fig = st.session_state.chart_renderer.create_chart(
        display_df, title="Market DNA Chart",
        show_volume=show_volume, show_signals=show_signals, colored_candles=colored_candles
    )
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        eff_fig = st.session_state.chart_renderer.create_efficiency_chart(display_df)
        st.plotly_chart(eff_fig, use_container_width=True)
    with col2:
        sb_fig = st.session_state.chart_renderer.create_system_bar_chart(display_df)
        st.plotly_chart(sb_fig, use_container_width=True)

        st.session_state.runner = ExperimentRunner(st.session_state.registry)
