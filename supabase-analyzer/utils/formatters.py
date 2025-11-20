"""
Data formatting utilities for reports and console output.
"""

from datetime import datetime
from typing import Any
import pandas as pd


def format_number(n: float, decimals: int = 0) -> str:
    """
    Format number with thousands separators.

    Args:
        n: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "1,523" or "1,523.45")
    """
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format as percentage.

    Args:
        value: Value between 0 and 1 (or percentage if > 1)
        decimals: Number of decimal places

    Returns:
        Formatted percentage (e.g., "54.7%")
    """
    # Handle both decimal (0.547) and percentage (54.7) inputs
    if value <= 1.0:
        value = value * 100
    return f"{value:.{decimals}f}%"


def format_currency(value: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    Format as currency.

    Args:
        value: Amount
        currency: Currency code
        decimals: Number of decimal places

    Returns:
        Formatted currency (e.g., "$1,523.45")
    """
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£'}
    symbol = symbols.get(currency, currency + ' ')
    return f"{symbol}{value:,.{decimals}f}"


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 5m", "45s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{hours}h"


def format_date(dt: datetime, format_str: str = '%b %d, %Y') -> str:
    """
    Format datetime as string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted date string
    """
    if pd.isna(dt):
        return "N/A"
    return dt.strftime(format_str)


def format_date_range(start: datetime, end: datetime) -> str:
    """
    Format date range nicely.

    Args:
        start: Start date
        end: End date

    Returns:
        Formatted range (e.g., "Oct 1, 2024 - Oct 31, 2024")
    """
    return f"{format_date(start)} - {format_date(end)}"


def create_markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    """
    Convert DataFrame to markdown table.

    Args:
        df: DataFrame to convert
        max_rows: Maximum rows to include

    Returns:
        Markdown formatted table string
    """
    if df.empty:
        return "*No data available*"

    # Limit rows if needed
    if len(df) > max_rows:
        display_df = df.head(max_rows)
        truncated = True
    else:
        display_df = df
        truncated = False

    # Use tabulate for markdown formatting
    from tabulate import tabulate
    table = tabulate(display_df, headers='keys', tablefmt='pipe', showindex=False)

    if truncated:
        table += f"\n\n*Showing {max_rows} of {len(df)} rows*"

    return table


def status_indicator(actual: float, target: float, better_when_higher: bool = True) -> str:
    """
    Return status symbol based on performance vs target.

    Args:
        actual: Actual value
        target: Target value
        better_when_higher: If True, higher is better

    Returns:
        Status symbol (✓, ✗, ⚠)
    """
    if target == 0:
        return "N/A"

    ratio = actual / target

    if better_when_higher:
        if ratio >= 1.0:
            return "✓"
        elif ratio >= 0.8:
            return "⚠"
        else:
            return "✗"
    else:
        if ratio <= 1.0:
            return "✓"
        elif ratio <= 1.2:
            return "⚠"
        else:
            return "✗"


def format_growth(current: float, previous: float, as_percentage: bool = True) -> str:
    """
    Format growth/change between two values.

    Args:
        current: Current value
        previous: Previous value
        as_percentage: If True, format as percentage

    Returns:
        Formatted growth string (e.g., "+25.3%" or "+1,234")
    """
    if previous == 0:
        if current == 0:
            return "0%"
        return "N/A"

    change = current - previous
    pct_change = (change / previous) * 100

    if as_percentage:
        sign = "+" if pct_change > 0 else ""
        return f"{sign}{pct_change:.1f}%"
    else:
        sign = "+" if change > 0 else ""
        return f"{sign}{format_number(change)}"


def create_bullet_list(items: list) -> str:
    """
    Create markdown bullet list.

    Args:
        items: List of items

    Returns:
        Markdown formatted bullet list
    """
    return "\n".join(f"- {item}" for item in items)


def create_numbered_list(items: list) -> str:
    """
    Create markdown numbered list.

    Args:
        items: List of items

    Returns:
        Markdown formatted numbered list
    """
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
