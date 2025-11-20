"""
Player analytics module.
Analyzes player growth, retention, and engagement.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from data.loader import DataLoader


class PlayerAnalytics:
    """Analyze player metrics and behavior."""

    def __init__(self, loader: DataLoader):
        """
        Initialize player analytics.

        Args:
            loader: DataLoader instance with exported data
        """
        self.loader = loader

    def get_total_players(self) -> int:
        """
        Get total number of unique players.

        Returns:
            Total player count
        """
        players_df = self.loader.load_table('players')
        return len(players_df)

    def get_new_players(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get players who joined in date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with new player details
        """
        players_df = self.loader.load_table('players')

        if players_df.empty or 'created_at' not in players_df.columns:
            return pd.DataFrame()

        return self.loader.filter_by_date(players_df, start_date, end_date)

    def get_player_growth_by_day(self) -> pd.DataFrame:
        """
        Calculate daily player registration counts.

        Returns:
            DataFrame with columns [date, new_players, cumulative_players]
        """
        players_df = self.loader.load_table('players')

        if players_df.empty or 'created_at' not in players_df.columns:
            return pd.DataFrame(columns=['date', 'new_players', 'cumulative_players'])

        # Group by date
        players_df['date'] = players_df['created_at'].dt.date
        daily_counts = players_df.groupby('date').size().reset_index(name='new_players')

        # Calculate cumulative
        daily_counts['cumulative_players'] = daily_counts['new_players'].cumsum()

        return daily_counts

    def get_player_retention(
        self,
        cohort_start: datetime,
        cohort_end: datetime,
        retention_days: List[int] = [1, 7, 30]
    ) -> Dict:
        """
        Calculate retention rates for a cohort.

        Args:
            cohort_start: Cohort start date
            cohort_end: Cohort end date
            retention_days: Days to check retention for

        Returns:
            Dictionary with retention metrics
        """
        # Get cohort players
        cohort_players = self.get_new_players(cohort_start, cohort_end)

        if cohort_players.empty:
            return {'cohort_size': 0, 'retention': {}}

        cohort_size = len(cohort_players)
        player_ids = set(cohort_players['id'].tolist())

        # Load activity data (transactions as proxy for activity)
        try:
            transactions_df = self.loader.load_table('transactions')
        except:
            return {'cohort_size': cohort_size, 'retention': {}, 'error': 'No transaction data'}

        retention_rates = {}

        for days in retention_days:
            # Calculate retention window
            retention_start = cohort_end + timedelta(days=days)
            retention_end = retention_start + timedelta(days=1)

            # Find players active during retention window
            if not transactions_df.empty and 'created_at' in transactions_df.columns:
                active_transactions = self.loader.filter_by_date(
                    transactions_df,
                    retention_start,
                    retention_end
                )

                if not active_transactions.empty and 'player_id' in active_transactions.columns:
                    active_players = set(active_transactions['player_id'].unique())
                    retained = active_players.intersection(player_ids)
                    retention_rate = len(retained) / cohort_size if cohort_size > 0 else 0
                else:
                    retention_rate = 0
            else:
                retention_rate = 0

            retention_rates[f'day_{days}'] = retention_rate

        return {
            'cohort_size': cohort_size,
            'cohort_start': cohort_start.strftime('%Y-%m-%d'),
            'cohort_end': cohort_end.strftime('%Y-%m-%d'),
            'retention': retention_rates
        }

    def get_active_players(
        self,
        reference_date: datetime,
        lookback_days: int = 7
    ) -> int:
        """
        Count active players in last N days from reference date.

        Args:
            reference_date: Reference date
            lookback_days: Days to look back

        Returns:
            Count of active players
        """
        start_date = reference_date - timedelta(days=lookback_days)

        try:
            transactions_df = self.loader.load_table('transactions')
            if transactions_df.empty or 'created_at' not in transactions_df.columns:
                return 0

            active_txns = self.loader.filter_by_date(
                transactions_df,
                start_date,
                reference_date
            )

            if 'player_id' in active_txns.columns:
                return active_txns['player_id'].nunique()
            return 0

        except:
            return 0

    def get_top_traders(self, limit: int = 100) -> pd.DataFrame:
        """
        Get top players by transaction count.

        Args:
            limit: Number of top traders to return

        Returns:
            DataFrame with player_id, transaction_count
        """
        try:
            transactions_df = self.loader.load_table('transactions')
            if transactions_df.empty or 'player_id' not in transactions_df.columns:
                return pd.DataFrame(columns=['player_id', 'transaction_count'])

            top_traders = transactions_df.groupby('player_id').size().reset_index(name='transaction_count')
            top_traders = top_traders.sort_values('transaction_count', ascending=False).head(limit)

            return top_traders

        except:
            return pd.DataFrame(columns=['player_id', 'transaction_count'])

    def get_player_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get comprehensive player summary for a period.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dictionary with player metrics
        """
        total_players = self.get_total_players()
        new_players_df = self.get_new_players(start_date, end_date)
        new_players_count = len(new_players_df)

        # Calculate active players at end of period
        active_players = self.get_active_players(end_date, lookback_days=30)

        # Get growth rate
        previous_period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=previous_period_days)
        previous_new = len(self.get_new_players(previous_start, start_date))

        growth_rate = 0
        if previous_new > 0:
            growth_rate = ((new_players_count - previous_new) / previous_new) * 100

        return {
            'total_players': total_players,
            'new_players': new_players_count,
            'active_players_30d': active_players,
            'growth_rate_pct': growth_rate,
            'period_start': start_date.strftime('%Y-%m-%d'),
            'period_end': end_date.strftime('%Y-%m-%d')
        }
