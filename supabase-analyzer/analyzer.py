#!/usr/bin/env python3
"""
Nova Shots Data Analyzer
Main CLI entry point.
"""

import click
from datetime import datetime
from pathlib import Path
import json

from data.loader import DataLoader
from analytics.players import PlayerAnalytics
from analytics.tournaments import TournamentAnalytics
from analytics.trading import TradingAnalytics
from analytics.sponsorship import SponsorshipAnalytics
from reports.generators import ReportGenerator
from utils.formatters import format_number, format_percentage, format_date


@click.group()
@click.version_option(version='1.0.0', prog_name='Nova Shots Analyzer')
def cli():
    """
    Nova Shots Data Analyzer

    Analyze exported Nova Shots database data for insights and reports.
    """
    pass


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
def overview(export):
    """Show quick overview of exported data."""
    try:
        loader = DataLoader(export)
        report_gen = ReportGenerator(loader)

        overview_text = report_gen.generate_overview()
        click.echo(overview_text)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
@click.option('--month', required=True, type=int, help='Month (1-12)')
@click.option('--year', required=True, type=int, help='Year')
@click.option('--output', help='Output filename (optional)')
def monthly(export, month, year, output):
    """Generate monthly report."""
    try:
        loader = DataLoader(export)
        report_gen = ReportGenerator(loader)

        click.echo(f"Generating monthly report for {month}/{year}...")

        output_path = report_gen.generate_monthly_report(month, year, output)

        click.echo(f"✓ Report generated: {output_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
@click.option('--start', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, help='End date (YYYY-MM-DD)')
def players(export, start, end):
    """Analyze player metrics for a period."""
    try:
        loader = DataLoader(export)
        player_analytics = PlayerAnalytics(loader)

        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')

        summary = player_analytics.get_player_summary(start_date, end_date)

        click.echo("\n=== Player Summary ===\n")
        click.echo(f"Period: {start} to {end}")
        click.echo(f"Total Players: {format_number(summary['total_players'])}")
        click.echo(f"New Players: {format_number(summary['new_players'])}")
        click.echo(f"Active Players (30d): {format_number(summary['active_players_30d'])}")
        click.echo(f"Growth Rate: {format_percentage(summary['growth_rate_pct'] / 100)}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
@click.option('--start', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, help='End date (YYYY-MM-DD)')
def trading(export, start, end):
    """Analyze trading metrics for a period."""
    try:
        loader = DataLoader(export)
        trading_analytics = TradingAnalytics(loader)

        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')

        summary = trading_analytics.get_trading_summary(start_date, end_date)

        click.echo("\n=== Trading Summary ===\n")
        click.echo(f"Period: {start} to {end}")
        click.echo(f"Total Transactions: {format_number(summary['total_transactions'])}")
        click.echo(f"Unique Traders: {format_number(summary['unique_traders'])}")
        click.echo(f"Avg Daily Transactions: {format_number(summary['avg_daily_transactions'], 1)}")
        click.echo(f"Avg Daily Traders: {format_number(summary['avg_daily_traders'], 1)}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
@click.option('--tournament-id', required=True, help='Tournament ID')
def tournament(export, tournament_id):
    """Analyze specific tournament performance."""
    try:
        loader = DataLoader(export)
        tournament_analytics = TournamentAnalytics(loader)

        metrics = tournament_analytics.get_tournament_metrics(tournament_id)

        if 'error' in metrics:
            click.echo(f"Error: {metrics['error']}", err=True)
            raise click.Abort()

        click.echo("\n=== Tournament Metrics ===\n")
        click.echo(f"Tournament: {metrics['tournament_name']}")
        click.echo(f"Start Date: {metrics['start_date']}")
        click.echo(f"Total Participants: {format_number(metrics['total_participants'])}")
        click.echo(f"New Users: {format_number(metrics['new_users'])}")
        click.echo(f"Total Predictions: {format_number(metrics['total_predictions'])}")
        click.echo(f"Avg Predictions/User: {metrics['avg_predictions_per_user']:.1f}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
@click.option('--tournament-id', required=True, help='Tournament ID')
@click.option('--contract', help='Path to contract JSON file')
@click.option('--output', help='Output filename for report')
def sponsorship(export, tournament_id, contract, output):
    """Generate sponsorship deliverables report."""
    try:
        loader = DataLoader(export)
        sponsorship_analytics = SponsorshipAnalytics(loader)

        # Load contract terms if provided
        contract_terms = None
        if contract:
            with open(contract, 'r') as f:
                contract_terms = json.load(f)

        # Generate report
        report = sponsorship_analytics.generate_deliverables_summary(
            tournament_id,
            contract_terms or {}
        )

        # Output to file or console
        if output:
            output_path = Path('outputs') / output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            click.echo(f"✓ Report saved to: {output_path}")
        else:
            click.echo(report)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--export', required=True, help='Path to export directory')
def list_tournaments(export):
    """List all available tournaments."""
    try:
        loader = DataLoader(export)
        tournament_analytics = TournamentAnalytics(loader)

        tournaments_df = tournament_analytics.get_all_tournaments()

        if tournaments_df.empty:
            click.echo("No tournaments found.")
            return

        click.echo("\n=== Available Tournaments ===\n")

        for idx, tournament in tournaments_df.iterrows():
            tournament_id = tournament.get('id', 'Unknown')
            tournament_name = tournament.get('name', 'Unknown')
            created_at = format_date(tournament.get('created_at'))

            click.echo(f"ID: {tournament_id}")
            click.echo(f"Name: {tournament_name}")
            click.echo(f"Date: {created_at}")
            click.echo("---")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
