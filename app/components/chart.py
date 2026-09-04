"""
IdeaForge - Chart Components

Plotly-based chart rendering for market data visualization.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any


class ChartRenderer:
    """
    Renders interactive charts using Plotly.
    
    Supports:
    - Candlestick charts
    - Custom colored candles
    - Volume bars
    - Sub-panels for indicators
    - Signal markers
    - Range highlights
    """
    
    def __init__(self):
        self._color_map = {
            'yellow': '#FFD700',
            'pink': '#FF69B4',
            'blue': '#1E90FF',
            'red': '#DC143C',
            'white': '#F5F5F5',
            'green': '#32CD32',
            'gray': '#808080',
        }
    
    def create_chart(
        self,
        df: pd.DataFrame,
        title: str = "Market Chart",
        show_volume: bool = True,
        show_signals: bool = False,
        colored_candles: bool = True,
        height: int = 800
    ) -> go.Figure:
        """
        Create a complete market chart.
        
        Args:
            df: DataFrame with OHLCV and market state data
            title: Chart title
            show_volume: Whether to show volume sub-panel
            show_signals: Whether to show signal markers
            colored_candles: Whether to use market DNA colors
            height: Chart height in pixels
            
        Returns:
            Plotly Figure object
        """
        rows = 2 if show_volume else 1
        row_heights = [0.7, 0.3] if show_volume else [1.0]
        
        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
            subplot_titles=(title, "Volume") if show_volume else (title,)
        )
        
        # Add candlestick trace
        if colored_candles and 'color' in df.columns:
            self._add_colored_candles(fig, df)
        else:
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'] if 'timestamp' in df.columns else df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='Price'
                ),
                row=1, col=1
            )
        
        # Add volume
        if show_volume and 'volume' in df.columns:
            colors = [
                self._color_map.get(color, '#808080')
                for color in df.get('color', ['gray'] * len(df))
            ]
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'] if 'timestamp' in df.columns else df.index,
                    y=df['volume'],
                    name='Volume',
        fig.update_layout(
            height=height,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template='plotly_dark',
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#16213e',
            font=dict(color='#e0e0e0')
        )
        
        return fig
    
    def _add_colored_candles(self, fig: go.Figure, df: pd.DataFrame):
        """Add candles colored by market state."""
        x = df['timestamp'] if 'timestamp' in df.columns else df.index
        
        fig.add_trace(
            go.Candlestick(
                x=x,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price',
                increasing_line_color='#32CD32',
                decreasing_line_color='#DC143C'
            ),
            row=1, col=1
        )
        
        # Add color markers
        for color_name, hex_color in self._color_map.items():
            mask = df['color'] == color_name
            if mask.any():
                fig.add_trace(
                    go.Scatter(
                        x=x[mask],
                        y=df.loc[mask, 'low'] * 0.999,
                        mode='markers',
                        name=color_name.capitalize(),
                        marker=dict(color=hex_color, size=8, symbol='diamond'),
                        showlegend=True
                    ),
                    row=1, col=1
                )
    
    def _add_signals(self, fig: go.Figure, df: pd.DataFrame):
        """Add buy/sell signal markers."""
        x = df['timestamp'] if 'timestamp' in df.columns else df.index
        
        buy_mask = df['signal'] == 'entry_long'
        if buy_mask.any():
            fig.add_trace(
                go.Scatter(
                    x=x[buy_mask],
                    y=df.loc[buy_mask, 'low'] * 0.995,
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(color='#00FF00', size=12, symbol='triangle-up')
                ),
                row=1, col=1
            )
        
        sell_mask = df['signal'] == 'entry_short'
        if sell_mask.any():
            fig.add_trace(
                go.Scatter(
                    x=x[sell_mask],
                    y=df.loc[sell_mask, 'high'] * 1.005,
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(color='#FF0000', size=12, symbol='triangle-down')
                ),
                row=1, col=1
            )
    
    def create_efficiency_chart(self, df: pd.DataFrame, height: int = 300) -> go.Figure:
        """Create efficiency indicator chart."""
        fig = go.Figure()
        x = df['timestamp'] if 'timestamp' in df.columns else df.index
        
        if 'efficiency' in df.columns:
            fig.add_trace(go.Scatter(
                x=x, y=df['efficiency'],
                mode='lines', name='Efficiency',
                line=dict(color='#1E90FF', width=2)
            ))
        
        if 'pressure' in df.columns:
            fig.add_trace(go.Scatter(
                x=x, y=df['pressure'],
                mode='lines', name='Pressure',
                line=dict(color='#DC143C', width=2)
            ))
        
        fig.update_layout(
            height=height, title='Efficiency & Pressure',
            template='plotly_dark', paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e'
        )
        
        return fig
    
    def create_system_bar_chart(self, df: pd.DataFrame, height: int = 200) -> go.Figure:
        """Create system bar chart."""
        fig = go.Figure()
        x = df['timestamp'] if 'timestamp' in df.columns else df.index
        
        if 'system_bar' in df.columns:
            fig.add_trace(go.Bar(
                x=x, y=df['system_bar'],
                name='System Bar', marker_color='#32CD32', opacity=0.7
            ))
        
        if 'ratio' in df.columns:
            fig.add_trace(go.Scatter(
                x=x, y=df['ratio'],
                mode='lines', name='Ratio', yaxis='y2',
                line=dict(color='#FFD700', width=2)
            ))
        
        fig.update_layout(
            height=height, title='System Bar & Ratio',
            template='plotly_dark', paper_bgcolor='#1a1a2e', plot_bgcolor='#16213e',
            yaxis2=dict(overlaying='y', side='right', showgrid=False)
        )
        
        return fig

                    marker_color=colors,
                    opacity=0.6
                ),
                row=2, col=1
            )
        
        # Add signals
        if show_signals and 'signal' in df.columns:
            self._add_signals(fig, df)
        
        fig.update_layout(
            height=height,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            template='plotly_dark',
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#16213e',
            font=dict(color='#e0e0e0')
        )
        
        return fig
