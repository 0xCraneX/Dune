"""
Sponsorship analytics module.
Tracks sponsorship deliverables and ROI metrics.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from data.loader import DataLoader
from .tournaments import TournamentAnalytics
from .players import PlayerAnalytics


class SponsorshipAnalytics:
    """Analyze sponsorship deliverables and performance."""

    def __init__(self, loader: DataLoader):
        """
        Initialize sponsorship analytics.

        Args:
            loader: DataLoader instance with exported data
        """
        self.loader = loader
        self.tournament_analytics = TournamentAnalytics(loader)
        self.player_analytics = PlayerAnalytics(loader)

    def get_tournament_deliverables(
        self,
        tournament_id: str,
        contract_terms: Optional[Dict] = None
    ) -> Dict:
        """
        Get all key metrics for a sponsored tournament.

        Args:
            tournament_id: Tournament identifier
            contract_terms: Optional dict with contracted minimums
                {
                    'min_participants': 1000,
                    'min_predictions': 5000,
                    'min_new_users': 500,
                    'duration_days': 14,
                    'sponsor_name': 'Sponsor Name'
                }

        Returns:
            Comprehensive deliverables report
        """
        # Get base tournament metrics
        tournament_metrics = self.tournament_analytics.get_tournament_metrics(tournament_id)

        if 'error' in tournament_metrics:
            return tournament_metrics

        # Extract actual metrics
        actual_participants = tournament_metrics['total_participants']
        actual_predictions = tournament_metrics['total_predictions']
        actual_new_users = tournament_metrics['new_users']

        # Build deliverables report
        deliverables = {
            'tournament_id': tournament_id,
            'tournament_name': tournament_metrics['tournament_name'],
            'start_date': tournament_metrics['start_date'],
            'actual_metrics': {
                'participants': actual_participants,
                'predictions': actual_predictions,
                'new_users': actual_new_users,
                'avg_predictions_per_user': tournament_metrics['avg_predictions_per_user']
            }
        }

        # If contract terms provided, compare actuals vs targets
        if contract_terms:
            deliverables['sponsor_name'] = contract_terms.get('sponsor_name', 'Unknown')

            # Participants comparison
            min_participants = contract_terms.get('min_participants', 0)
            participants_met = actual_participants >= min_participants if min_participants > 0 else True
            participants_performance = (actual_participants / min_participants) if min_participants > 0 else 0

            # Predictions comparison
            min_predictions = contract_terms.get('min_predictions', 0)
            predictions_met = actual_predictions >= min_predictions if min_predictions > 0 else True
            predictions_performance = (actual_predictions / min_predictions) if min_predictions > 0 else 0

            # New users comparison
            min_new_users = contract_terms.get('min_new_users', 0)
            new_users_met = actual_new_users >= min_new_users if min_new_users > 0 else True
            new_users_performance = (actual_new_users / min_new_users) if min_new_users > 0 else 0

            deliverables['contract_comparison'] = {
                'participants': {
                    'target': min_participants,
                    'actual': actual_participants,
                    'met': participants_met,
                    'performance_ratio': round(participants_performance, 2)
                },
                'predictions': {
                    'target': min_predictions,
                    'actual': actual_predictions,
                    'met': predictions_met,
                    'performance_ratio': round(predictions_performance, 2)
                },
                'new_users': {
                    'target': min_new_users,
                    'actual': actual_new_users,
                    'met': new_users_met,
                    'performance_ratio': round(new_users_performance, 2)
                }
            }

            # Overall status
            all_met = participants_met and predictions_met and new_users_met
            deliverables['overall_status'] = 'All Targets Met ✓' if all_met else 'Targets Partially Met ⚠'

        return deliverables

    def compare_sponsorship_periods(self, tournament_ids: List[str]) -> pd.DataFrame:
        """
        Compare multiple sponsored tournaments.

        Args:
            tournament_ids: List of tournament IDs

        Returns:
            DataFrame with comparison data
        """
        comparisons = []

        for tournament_id in tournament_ids:
            deliverables = self.get_tournament_deliverables(tournament_id)

            if 'error' not in deliverables:
                comparison = {
                    'tournament_id': tournament_id,
                    'tournament_name': deliverables['tournament_name'],
                    'participants': deliverables['actual_metrics']['participants'],
                    'predictions': deliverables['actual_metrics']['predictions'],
                    'new_users': deliverables['actual_metrics']['new_users'],
                    'avg_predictions_per_user': deliverables['actual_metrics']['avg_predictions_per_user']
                }
                comparisons.append(comparison)

        if not comparisons:
            return pd.DataFrame()

        return pd.DataFrame(comparisons)

    def generate_deliverables_summary(
        self,
        tournament_id: str,
        contract_terms: Dict
    ) -> str:
        """
        Generate markdown formatted deliverables summary.

        Args:
            tournament_id: Tournament identifier
            contract_terms: Contract terms dictionary

        Returns:
            Markdown formatted report
        """
        deliverables = self.get_tournament_deliverables(tournament_id, contract_terms)

        if 'error' in deliverables:
            return f"## Error\n\n{deliverables['error']}"

        # Build markdown report
        report = f"""# Sponsorship Deliverables Report

**Tournament:** {deliverables['tournament_name']}
**Sponsor:** {deliverables.get('sponsor_name', 'N/A')}
**Date:** {deliverables['start_date']}

---

## Contract Deliverables

"""

        if 'contract_comparison' in deliverables:
            comp = deliverables['contract_comparison']

            report += "| Metric | Target | Actual | Status | Performance |\n"
            report += "|--------|--------|--------|--------|-------------|\n"

            # Participants
            p = comp['participants']
            p_status = "✓" if p['met'] else "✗"
            report += f"| Participants | {p['target']:,} | {p['actual']:,} | {p_status} | {p['performance_ratio']:.0%} |\n"

            # Predictions
            pr = comp['predictions']
            pr_status = "✓" if pr['met'] else "✗"
            report += f"| Predictions | {pr['target']:,} | {pr['actual']:,} | {pr_status} | {pr['performance_ratio']:.0%} |\n"

            # New Users
            n = comp['new_users']
            n_status = "✓" if n['met'] else "✗"
            report += f"| New Users | {n['target']:,} | {n['actual']:,} | {n_status} | {n['performance_ratio']:.0%} |\n"

            report += f"\n**Overall Status:** {deliverables['overall_status']}\n\n"

        report += f"""---

## Performance Metrics

- **Total Participants:** {deliverables['actual_metrics']['participants']:,}
- **Total Predictions:** {deliverables['actual_metrics']['predictions']:,}
- **New Users Acquired:** {deliverables['actual_metrics']['new_users']:,}
- **Avg Predictions per User:** {deliverables['actual_metrics']['avg_predictions_per_user']:.1f}

"""

        return report
