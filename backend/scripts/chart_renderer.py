"""
Chart renderer that generates matplotlib visualizations from structured chart specs
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Force non-GUI backend
matplotlib.use("Agg")


def render_chart_from_spec(df: pd.DataFrame, spec: Dict[str, Any], output_path: Path) -> None:
    """
    Render a chart from a structured spec.
    
    Args:
        df: DataFrame with the data
        spec: Chart specification dict with structure:
            {
                "chart": {
                    "type": "line|bar|scatter|hist|box|heatmap|none",
                    "title": "string",
                    "x": {"col": "string", "dtype": "datetime|category|number", "sort": true},
                    "y": {"col": "string", "dtype": "number", "sort": false},
                    "series": {"col": "string|null"},
                    "top_k": {"col": "string|null", "k": 10, "by": "y", "order": "desc"},
                    "orientation": "vertical|horizontal",
                    "stacked": false,
                    "limits": {"max_points": 2000}
                }
            }
        output_path: Path to save the chart
    """
    chart = spec.get("chart", {})
    chart_type = chart.get("type", "bar")
    
    if chart_type == "none":
        return
    
    # Get axis configs
    x_config = chart.get("x", {})
    y_config = chart.get("y", {})
    x_col = x_config.get("col") if isinstance(x_config, dict) else x_config
    y_col = y_config.get("col") if isinstance(y_config, dict) else y_config
    series_config = chart.get("series")
    series_col = series_config.get("col") if isinstance(series_config, dict) else (series_config if series_config else None)
    
    if not x_col or not y_col:
        raise ValueError(f"Missing required columns: x={x_col}, y={y_col}")
    
    # Check if columns exist
    if x_col not in df.columns:
        raise ValueError(f"Column '{x_col}' not found in DataFrame. Available: {list(df.columns)}")
    if y_col not in df.columns:
        raise ValueError(f"Column '{y_col}' not found in DataFrame. Available: {list(df.columns)}")
    
    # Apply top_k filter if specified
    top_k = chart.get("top_k")
    if top_k and top_k.get("col"):
        top_k_col = top_k.get("col")
        k = top_k.get("k", 10)
        by_col = top_k.get("by", y_col)
        order = top_k.get("order", "desc")
        
        if top_k_col in df.columns:
            # Group by top_k_col and aggregate by_col
            grouped = df.groupby(top_k_col)[by_col].sum().reset_index()
            sorted_grouped = grouped.sort_values(by_col, ascending=(order == "asc"))
            top_values = sorted_grouped.head(k)[top_k_col].tolist()
            df = df[df[top_k_col].isin(top_values)]
    
    # Apply limits
    limits = chart.get("limits", {})
    max_points = limits.get("max_points", 2000)
    if len(df) > max_points:
        df = df.head(max_points)
    
    # Prepare data
    df_plot = df.copy()
    
    # Handle x-axis data type and sorting
    x_dtype = x_config.get("dtype", "number")
    if x_dtype == "datetime" and x_col in df_plot.columns:
        df_plot[x_col] = pd.to_datetime(df_plot[x_col])
    elif x_dtype == "number" and x_col in df_plot.columns:
        df_plot[x_col] = pd.to_numeric(df_plot[x_col], errors='coerce')
    
    if x_config.get("sort", False):
        df_plot = df_plot.sort_values(x_col)
    
    # Handle y-axis sorting
    if y_config.get("sort", False):
        df_plot = df_plot.sort_values(y_col)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    orientation = chart.get("orientation", "vertical")
    stacked = chart.get("stacked", False)
    
    # Render based on chart type
    if chart_type == "bar":
        if series_col and series_col in df_plot.columns:
            # Grouped or stacked bar chart
            pivot_df = df_plot.pivot_table(
                index=x_col,
                columns=series_col,
                values=y_col,
                aggfunc='sum'
            ).fillna(0)
            
            if orientation == "horizontal":
                pivot_df.plot(kind='barh', ax=ax, stacked=stacked)
            else:
                pivot_df.plot(kind='bar', ax=ax, stacked=stacked)
            ax.legend(title=series_col)
        else:
            # Simple bar chart
            if orientation == "horizontal":
                ax.barh(df_plot[x_col], df_plot[y_col])
            else:
                ax.bar(df_plot[x_col], df_plot[y_col])
    
    elif chart_type == "line":
        if series_col and series_col in df_plot.columns:
            # Multiple lines
            for series_val in df_plot[series_col].unique():
                series_data = df_plot[df_plot[series_col] == series_val]
                series_data = series_data.sort_values(x_col)
                ax.plot(series_data[x_col], series_data[y_col], marker='o', label=str(series_val))
            ax.legend(title=series_col)
        else:
            # Single line
            plot_df = df_plot.sort_values(x_col)
            ax.plot(plot_df[x_col], plot_df[y_col], marker='o')
    
    elif chart_type == "scatter":
        if series_col and series_col in df_plot.columns:
            for series_val in df_plot[series_col].unique():
                series_data = df_plot[df_plot[series_col] == series_val]
                ax.scatter(series_data[x_col], series_data[y_col], label=str(series_val), alpha=0.6)
            ax.legend(title=series_col)
        else:
            ax.scatter(df_plot[x_col], df_plot[y_col], alpha=0.6)
    
    elif chart_type == "hist":
        ax.hist(df_plot[y_col], bins=min(50, len(df_plot)), edgecolor='black')
        ax.set_xlabel(y_col)
        ax.set_ylabel("Frequency")
    
    elif chart_type == "box":
        if series_col and series_col in df_plot.columns:
            data_to_plot = [df_plot[df_plot[series_col] == val][y_col].values 
                          for val in df_plot[series_col].unique()]
            labels = [str(val) for val in df_plot[series_col].unique()]
            ax.boxplot(data_to_plot, labels=labels)
            ax.set_xlabel(series_col)
        else:
            ax.boxplot([df_plot[y_col].values])
        ax.set_ylabel(y_col)
    
    elif chart_type == "heatmap":
        if series_col and series_col in df_plot.columns:
            pivot_df = df_plot.pivot_table(
                index=x_col,
                columns=series_col,
                values=y_col,
                aggfunc='sum'
            ).fillna(0)
            im = ax.imshow(pivot_df.values, aspect='auto', cmap='YlOrRd')
            ax.set_xticks(range(len(pivot_df.columns)))
            ax.set_xticklabels(pivot_df.columns, rotation=45, ha='right')
            ax.set_yticks(range(len(pivot_df.index)))
            ax.set_yticklabels(pivot_df.index)
            plt.colorbar(im, ax=ax)
        else:
            raise ValueError("Heatmap requires a series column")
    
    # Set labels and title
    title = chart.get("title", "")
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Format x-axis
    if x_dtype == "datetime":
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    elif x_config.get("dtype") == "category":
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True, alpha=0.3)
    
    # Save
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

