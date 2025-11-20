"""
Tournament analytics module.
Analyzes tournament performance, participation, and predictions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from data.loader import DataLoader


class TournamentAnalytics:
    """Analyze tournament metrics and performance."""

    def __init__(self, loader: DataLoader):
        """
        Initialize tournament analytics.

        Args:
            loader: DataLoader instance with exported data
        """
        self.loader = loader

    def get_all_tournaments(self) -> pd.DataFrame:
        """
        Get list of all tournaments.

        Returns:
            DataFrame with tournament details
        """
        return self.loader.load_table('tournaments')

    def get_tournament_by_id(self, tournament_id: str) -> Optional[Dict]:
        """
        Get tournament details by ID.

        Args:
            tournament_id: Tournament identifier

        Returns:
            Tournament data dict or None
        """
        tournaments_df = self.loader.load_table('tournaments')

        if tournaments_df.empty:
            return None

        # Try to find tournament by id column
        if 'id' in tournaments_df.columns:
            match = tournaments_df[tournaments_df['id'] == tournament_id]
            if not match.empty:
                return match.iloc[0].to_dict()

        return None

    def get_tournament_participants(self, tournament_id: str) -> int:
        """
        Count unique players who participated in tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            Participant count
        """
        try:
            # Load prediction tournaments
            pred_tournaments_df = self.loader.load_table('prediction_tournaments')

            if pred_tournaments_df.empty:
                return 0

            # Filter by tournament_id
            if 'tournament_id' in pred_tournaments_df.columns:
                tournament_preds = pred_tournaments_df[
                    pred_tournaments_df['tournament_id'] == tournament_id
                ]

                if 'player_id' in tournament_preds.columns:
                    return tournament_preds['player_id'].nunique()

            return 0

        except:
            return 0

    def get_tournament_predictions(self, tournament_id: str) -> pd.DataFrame:
        """
        Get all predictions for a tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            DataFrame with prediction data
        """
        try:
            pred_tournaments_df = self.loader.load_table('prediction_tournaments')

            if pred_tournaments_df.empty:
                return pd.DataFrame()

            if 'tournament_id' in pred_tournaments_df.columns:
                return pred_tournaments_df[
                    pred_tournaments_df['tournament_id'] == tournament_id
                ]

            return pd.DataFrame()

        except:
            return pd.DataFrame()

    def get_tournament_metrics(self, tournament_id: str) -> Dict:
        """
        Get comprehensive tournament metrics.

        Args:
            tournament_id: Tournament identifier

        Returns:
            Dictionary with tournament metrics
        """
        tournament = self.get_tournament_by_id(tournament_id)

        if not tournament:
            return {
                'error': f'Tournament {tournament_id} not found',
                'tournament_id': tournament_id
            }

        # Get participants
        participants = self.get_tournament_participants(tournament_id)

        # Get predictions
        predictions_df = self.get_tournament_predictions(tournament_id)
        total_predictions = len(predictions_df)

        # Calculate new users (first-time participants)
        new_users = 0
        if not predictions_df.empty and 'player_id' in predictions_df.columns:
            player_ids = predictions_df['player_id'].unique()

            # Check when players were created
            players_df = self.loader.load_table('players')
            if not players_df.empty and 'id' in players_df.columns and 'created_at' in players_df.columns:
                tournament_players = players_df[players_df['id'].isin(player_ids)]

                # Get tournament dates
                if 'created_at' in tournament:
                    tournament_start = pd.to_datetime(tournament['created_at'])

                    # Count players created near tournament start (within 7 days)
                    lookback = tournament_start - timedelta(days=7)
                    new_user_mask = (tournament_players['created_at'] >= lookback)
                    new_users = new_user_mask.sum()

        # Calculate average predictions per user
        avg_predictions_per_user = 0
        if participants > 0:
            avg_predictions_per_user = total_predictions / participants

        return {
            'tournament_id': tournament_id,
            'tournament_name': tournament.get('name', 'Unknown'),
            'start_date': str(tournament.get('created_at', 'N/A')),
            'total_participants': participants,
            'new_users': new_users,
            'total_predictions': total_predictions,
            'avg_predictions_per_user': round(avg_predictions_per_user, 2)
        }

    def compare_tournaments(self, tournament_ids: List[str]) -> pd.DataFrame:
        """
        Compare metrics across multiple tournaments.

        Args:
            tournament_ids: List of tournament IDs to compare

        Returns:
            DataFrame with comparison metrics
        """
        comparisons = []

        for tournament_id in tournament_ids:
            metrics = self.get_tournament_metrics(tournament_id)
            if 'error' not in metrics:
                comparisons.append(metrics)

        if not comparisons:
            return pd.DataFrame()

        return pd.DataFrame(comparisons)

    def get_tournament_timeline(self, tournament_id: str) -> pd.DataFrame:
        """
        Get daily activity timeline for a tournament.

        Args:
            tournament_id: Tournament identifier

        Returns:
            DataFrame with daily metrics
        """
        predictions_df = self.get_tournament_predictions(tournament_id)

        if predictions_df.empty or 'created_at' not in predictions_df.columns:
            return pd.DataFrame(columns=['date', 'predictions', 'new_participants'])

        # Group by date
        predictions_df['date'] = predictions_df['created_at'].dt.date

        # Daily predictions
        daily_predictions = predictions_df.groupby('date').size().reset_index(name='predictions')

        # Daily new participants (first prediction of the day)
        if 'player_id' in predictions_df.columns:
            first_predictions = predictions_df.sort_values('created_at').groupby('player_id').first()
            first_predictions['date'] = first_predictions['created_at'].dt.date
            daily_new = first_predictions.groupby('date').size().reset_index(name='new_participants')

            # Merge
            timeline = pd.merge(daily_predictions, daily_new, on='date', how='left')
            timeline['new_participants'] = timeline['new_participants'].fillna(0).astype(int)
        else:
            timeline = daily_predictions
            timeline['new_participants'] = 0

        return timeline.sort_values('date')
