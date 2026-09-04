# 🧬 IdeaForge - Quantitative Market Research Laboratory

IdeaForge is a professional quantitative market research environment where researchers can load market data, calculate custom market measurements (Market DNA), visualize them on interactive charts, define and run experiments, backtest strategies using the SAME logic as the chart, and track research history.

## 🎯 Core Principle

**ONE LOGIC → ONE ENGINE → MANY CONSUMERS**

All market calculations originate from shared Python modules - never implemented separately for chart, backtest, or replay.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app/dashboard.py

# Run tests
pytest tests/ -v
```

## 📊 Features

- **Market DNA Engine**: System bar, efficiency, ratio, pressure calculations
- **Interactive Charts**: Candlestick charts with custom colors based on market state
- **Backtest Engine**: Event-driven backtesting with fees and slippage
- **Experiment Framework**: Create, run, and track research experiments
- **No Look-Ahead Bias**: All calculations use only past data

## 🏗️ Project Structure

```
IdeaForge/
├── app/                    # Streamlit dashboard
├── core/                   # Core calculation engine
├── backtest/               # Backtesting engine
├── research/               # Research framework
├── data/                   # Data management
├── tests/                  # Test suite
└── experiments/            # Experiment storage
```

## 🧬 Market Colors

| Color  | Meaning              |
|--------|----------------------|
| YELLOW | Weak movement        |
| PINK   | Medium strength      |
| BLUE   | Strong bullish       |
| RED    | Strong bearish       |
| WHITE  | High pressure        |
| GREEN  | Uniform/consistent   |

## 📝 License

MIT License