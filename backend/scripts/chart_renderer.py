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
    top_k_order = None  # Store the order for later sorting
    if top_k and top_k.get("col"):
        top_k_col = top_k.get("col")
        k = top_k.get("k", 10)
        by_col = top_k.get("by", y_col)
        order = top_k.get("order", "desc")
        top_k_order = order  # Store for later
        
        if top_k_col in df.columns:
            # Group by top_k_col and aggregate by_col to find top k
            grouped = df.groupby(top_k_col)[by_col].sum().reset_index()
            sorted_grouped = grouped.sort_values(by_col, ascending=(order == "asc"))
            top_values = sorted_grouped.head(k)[top_k_col].tolist()
            # Filter to only top k values
            df = df[df[top_k_col].isin(top_values)]
            
            # Create a sort order mapping to preserve the top_k order
            sort_order_map = {val: idx for idx, val in enumerate(top_values)}
            
            # If we have a series column, maintain sort order by adding a sort key
            if series_col:
                # For grouped charts, maintain sort order by adding a sort key
                df['_top_k_sort'] = df[top_k_col].map(sort_order_map)
                df = df.sort_values('_top_k_sort')
                df = df.drop(columns=['_top_k_sort'])
            else:
                # For simple bar charts without series, aggregate by top_k_col to ensure one row per value
                # This handles cases where SQL might return multiple rows per top_k value
                if len(df.groupby(top_k_col)) > len(top_values):
                    # Need to aggregate - group by top_k_col and sum y_col
                    df = df.groupby(top_k_col)[y_col].sum().reset_index()
                    # Sort by y_col in the specified order
                    df = df.sort_values(y_col, ascending=(order == "asc"))
                    # Ensure we only have the top k (should already be filtered, but double-check)
                    df = df.head(k)
                else:
                    # Data is already one row per top_k value, just ensure it's sorted
                    df['_top_k_sort'] = df[top_k_col].map(sort_order_map)
                    df = df.sort_values('_top_k_sort')
                    df = df.drop(columns=['_top_k_sort'])
    
    # Apply limits
    limits = chart.get("limits", {})
    max_points = limits.get("max_points", 2000)
    if len(df) > max_points:
        df = df.head(max_points)
    
    # Prepare data
    df_plot = df.copy()
    
    # Handle x-axis data type and sorting
    x_dtype = x_config.get("dtype", "number")
    
    # Special handling: if we have separate year and month columns, combine them
    if x_dtype == "datetime" and x_col in df_plot.columns:
        # Check if we have separate year and month columns that should be combined
        if "year" in df_plot.columns and "month" in df_plot.columns and x_col in ["year", "month"]:
            # Create a proper date column from year and month
            df_plot["_date"] = pd.to_datetime(
                df_plot["year"].astype(str) + "-" + df_plot["month"].astype(str).str.zfill(2) + "-01"
            )
            x_col = "_date"
        else:
            # Check the actual data type and format
            original_dtype = df_plot[x_col].dtype
            sample_value = df_plot[x_col].iloc[0] if len(df_plot) > 0 else None
            
            # If it's already a datetime type, verify it's not 1970 dates
            if pd.api.types.is_datetime64_any_dtype(df_plot[x_col]):
                # Check if dates are suspiciously old (before 2000)
                if len(df_plot) > 0 and df_plot[x_col].min() < pd.Timestamp('2000-01-01'):
                    # These are likely misinterpreted dates, try to fix
                    pass  # Will fall through to fix below
                else:
                    pass  # Already datetime and looks correct
            # If it's a string that looks like a date, parse it
            elif original_dtype == 'object' or isinstance(sample_value, str):
                # Try parsing as date string first - DuckDB often returns dates as strings
                df_plot[x_col] = pd.to_datetime(df_plot[x_col], errors='coerce', format='mixed')
                # If that produced 1970 dates, the strings might be numeric representations
                if len(df_plot) > 0 and df_plot[x_col].min() < pd.Timestamp('2000-01-01'):
                    # Try converting string to int first, then parsing
                    try:
                        numeric_vals = pd.to_numeric(df_plot[x_col].astype(str), errors='coerce')
                        # If they're reasonable date numbers (like 20230101 for 2023-01-01)
                        if numeric_vals.min() > 20000000 and numeric_vals.max() < 21000000:
                            df_plot[x_col] = pd.to_datetime(numeric_vals.astype(str), format='%Y%m%d', errors='coerce')
                    except:
                        pass
            # If it's numeric, check if it's a reasonable date range
            elif original_dtype in ['int64', 'float64', 'int32', 'float32']:
                # Check if values are in a reasonable date range (not Unix timestamps)
                min_val = df_plot[x_col].min()
                max_val = df_plot[x_col].max()
                
                # If values are very large (likely Unix timestamp in seconds or milliseconds)
                if min_val > 1000000000:  # After 2001-09-09 (Unix timestamp)
                    # Could be Unix timestamp - but DuckDB DATE_TRUNC shouldn't return this
                    # Try parsing as date string first, then as timestamp
                    df_plot[x_col] = pd.to_datetime(df_plot[x_col], unit='s', errors='coerce')
                    # If that fails or produces 1970 dates, try as days since epoch
                    if df_plot[x_col].min() < pd.Timestamp('2000-01-01'):
                        df_plot[x_col] = pd.to_datetime(df_plot[x_col], unit='D', origin='unix', errors='coerce')
                # If values are small numbers (like days since some date), might be days since epoch
                elif min_val > 0 and max_val < 100000:
                    # Could be days since epoch - try that
                    df_plot[x_col] = pd.to_datetime(df_plot[x_col], unit='D', origin='unix', errors='coerce')
                # Otherwise, try standard parsing
                else:
                    df_plot[x_col] = pd.to_datetime(df_plot[x_col], errors='coerce')
                
                # If conversion failed or produced 1970 dates, try string conversion
                if df_plot[x_col].isna().any() or df_plot[x_col].min() < pd.Timestamp('2000-01-01'):
                    # Try converting to string first, then parsing
                    df_plot[x_col] = pd.to_datetime(df_plot[x_col].astype(str), errors='coerce', format='mixed')
            else:
                # Default: try to parse as datetime
                df_plot[x_col] = pd.to_datetime(df_plot[x_col], errors='coerce', format='mixed')
            
            # Final check: if we still have 1970 dates or failed conversions, check for year/month columns
            if df_plot[x_col].isna().any() or (df_plot[x_col].min() < pd.Timestamp('2000-01-01') and "year" in df_plot.columns):
                if "year" in df_plot.columns and "month" in df_plot.columns:
                    # Fallback: combine year and month
                    df_plot["_date"] = pd.to_datetime(
                        df_plot["year"].astype(str) + "-" + df_plot["month"].astype(str).str.zfill(2) + "-01"
                    )
                    x_col = "_date"
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
            # Simple bar chart - ensure data is sorted by y_col descending for "top N" queries
            # If top_k was used, data should already be sorted, but ensure it anyway
            if top_k_order == "desc":
                df_plot = df_plot.sort_values(y_col, ascending=False)
            elif top_k_order == "asc":
                df_plot = df_plot.sort_values(y_col, ascending=True)
            elif not x_config.get("sort", False):  # Only auto-sort if not explicitly sorted by x
                # Default: sort by y_col descending for bar charts (highest first)
                df_plot = df_plot.sort_values(y_col, ascending=False)
            
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
        # Use appropriate date format based on data range
        if pd.api.types.is_datetime64_any_dtype(df_plot[x_col]):
            date_min = df_plot[x_col].min()
            date_max = df_plot[x_col].max()
            date_range = (date_max - date_min).days if pd.notna(date_max) and pd.notna(date_min) else 0
            
            # Choose format based on time span
            if date_range > 365:
                # Years/months - show year-month
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
            elif date_range > 30:
                # Months/days - show month-day
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            else:
                # Days/hours - show full datetime
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d %H:%M'))
        else:
            # Fallback format
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
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

