"""
Trading analytics module.
Analyzes trading volume, patterns, and portfolio metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from data.loader import DataLoader


class TradingAnalytics:
    """Analyze trading and economic metrics."""

    def __init__(self, loader: DataLoader):
        """
        Initialize trading analytics.

        Args:
            loader: DataLoader instance with exported data
        """
        self.loader = loader

    def get_total_transactions(self) -> int:
        """
        Get total transaction count.

        Returns:
            Total number of transactions
        """
        transactions_df = self.loader.load_table('transactions')
        return len(transactions_df)

    def get_transactions_by_date(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Get transactions in date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with filtered transactions
        """
        transactions_df = self.loader.load_table('transactions')

        if transactions_df.empty or 'created_at' not in transactions_df.columns:
            return pd.DataFrame()

        return self.loader.filter_by_date(transactions_df, start_date, end_date)

    def get_daily_volume(self) -> pd.DataFrame:
        """
        Calculate daily trading metrics.

        Returns:
            DataFrame with columns [date, transaction_count, unique_traders]
        """
        transactions_df = self.loader.load_table('transactions')

        if transactions_df.empty or 'created_at' not in transactions_df.columns:
            return pd.DataFrame(columns=['date', 'transaction_count', 'unique_traders'])

        # Group by date
        transactions_df['date'] = transactions_df['created_at'].dt.date

        # Daily transaction count
        daily_counts = transactions_df.groupby('date').size().reset_index(name='transaction_count')

        # Daily unique traders
        if 'player_id' in transactions_df.columns:
            daily_traders = transactions_df.groupby('date')['player_id'].nunique().reset_index(name='unique_traders')
            daily_volume = pd.merge(daily_counts, daily_traders, on='date')
        else:
            daily_volume = daily_counts
            daily_volume['unique_traders'] = 0

        return daily_volume.sort_values('date')

    def get_trading_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get comprehensive trading summary for a period.

        Args:
            start_date: Period start
            end_date: Period end

        Returns:
            Dictionary with trading metrics
        """
        period_txns = self.get_transactions_by_date(start_date, end_date)

        total_transactions = len(period_txns)

        unique_traders = 0
        if not period_txns.empty and 'player_id' in period_txns.columns:
            unique_traders = period_txns['player_id'].nunique()

        # Calculate daily averages
        days = (end_date - start_date).days + 1
        avg_daily_transactions = total_transactions / days if days > 0 else 0
        avg_daily_traders = unique_traders / days if days > 0 else 0

        return {
            'total_transactions': total_transactions,
            'unique_traders': unique_traders,
            'avg_daily_transactions': round(avg_daily_transactions, 1),
            'avg_daily_traders': round(avg_daily_traders, 1),
            'period_start': start_date.strftime('%Y-%m-%d'),
            'period_end': end_date.strftime('%Y-%m-%d'),
            'period_days': days
        }

    def get_top_traders(self, limit: int = 100) -> pd.DataFrame:
        """
        Get top traders by transaction count.

        Args:
            limit: Number of top traders to return

        Returns:
            DataFrame with player_id, transaction_count
        """
        transactions_df = self.loader.load_table('transactions')

        if transactions_df.empty or 'player_id' not in transactions_df.columns:
            return pd.DataFrame(columns=['player_id', 'transaction_count'])

        top_traders = transactions_df.groupby('player_id').size().reset_index(name='transaction_count')
        top_traders = top_traders.sort_values('transaction_count', ascending=False).head(limit)

        return top_traders

    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio metrics summary.

        Returns:
            Dictionary with portfolio statistics
        """
        try:
            portfolios_df = self.loader.load_table('portfolios')

            if portfolios_df.empty:
                return {
                    'total_portfolios': 0,
                    'error': 'No portfolio data available'
                }

            total_portfolios = len(portfolios_df)

            # Get unique portfolio owners
            unique_owners = 0
            if 'player_id' in portfolios_df.columns:
                unique_owners = portfolios_df['player_id'].nunique()

            return {
                'total_portfolios': total_portfolios,
                'unique_portfolio_owners': unique_owners,
            }

        except:
            return {
                'total_portfolios': 0,
                'error': 'Portfolio table not available'
            }
