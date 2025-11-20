"""
Report generation module.
Creates markdown reports from analytics data.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import json

from data.loader import DataLoader
from analytics.players import PlayerAnalytics
from analytics.tournaments import TournamentAnalytics
from analytics.trading import TradingAnalytics
from analytics.sponsorship import SponsorshipAnalytics
from utils.formatters import (
    format_number,
    format_percentage,
    format_date,
    format_date_range,
    format_growth,
    create_markdown_table
)
import config


class ReportGenerator:
    """Generate various reports from exported data."""

    def __init__(self, loader: DataLoader, output_dir: str = config.OUTPUT_DIR):
        """
        Initialize report generator.

        Args:
            loader: DataLoader with exported data
            output_dir: Directory for output files
        """
        self.loader = loader
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize analytics modules
        self.player_analytics = PlayerAnalytics(loader)
        self.tournament_analytics = TournamentAnalytics(loader)
        self.trading_analytics = TradingAnalytics(loader)
        self.sponsorship_analytics = SponsorshipAnalytics(loader)

    def generate_monthly_report(
        self,
        month: int,
        year: int,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive monthly report.

        Args:
            month: Month number (1-12)
            year: Year
            output_filename: Optional custom filename

        Returns:
            Path to generated report
        """
        # Calculate date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Generate report filename
        if not output_filename:
            month_name = start_date.strftime('%B').lower()
            output_filename = f"{year}_{month_name}_report.md"

        output_path = self.output_dir / output_filename

        # Get analytics data
        player_summary = self.player_analytics.get_player_summary(start_date, end_date)
        trading_summary = self.trading_analytics.get_trading_summary(start_date, end_date)

        # Build report
        report = self._build_monthly_report_content(
            start_date,
            end_date,
            player_summary,
            trading_summary
        )

        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        return str(output_path)

    def _build_monthly_report_content(
        self,
        start_date: datetime,
        end_date: datetime,
        player_summary: Dict,
        trading_summary: Dict
    ) -> str:
        """
        Build monthly report markdown content.

        Args:
            start_date: Period start
            end_date: Period end
            player_summary: Player metrics
            trading_summary: Trading metrics

        Returns:
            Markdown formatted report
        """
        month_name = start_date.strftime('%B %Y')

        report = f"""# Nova Shots Monthly Report
**Period:** {month_name}
**Generated:** {format_date(datetime.now())}

---

## Executive Summary

### Key Metrics

- **Total Players:** {format_number(player_summary['total_players'])}
- **New Players:** {format_number(player_summary['new_players'])} ({format_growth(player_summary['new_players'], player_summary['total_players'] - player_summary['new_players'])})
- **Active Players (30d):** {format_number(player_summary['active_players_30d'])}
- **Total Transactions:** {format_number(trading_summary['total_transactions'])}
- **Unique Traders:** {format_number(trading_summary['unique_traders'])}

### Growth Rate
- **Player Growth:** {format_percentage(player_summary['growth_rate_pct'] / 100)} vs previous period

---

## Player Metrics

### New Players
- **Total New Players:** {format_number(player_summary['new_players'])}
- **Average Daily New Players:** {format_number(player_summary['new_players'] / trading_summary['period_days'])}

### Activity
- **Active Players (30-day):** {format_number(player_summary['active_players_30d'])}

---

## Trading Activity

### Transaction Volume
- **Total Transactions:** {format_number(trading_summary['total_transactions'])}
- **Unique Traders:** {format_number(trading_summary['unique_traders'])}
- **Average Daily Transactions:** {format_number(trading_summary['avg_daily_transactions'], 1)}
- **Average Daily Traders:** {format_number(trading_summary['avg_daily_traders'], 1)}

### Top Traders
"""

        # Get top traders
        top_traders_df = self.trading_analytics.get_top_traders(limit=10)
        if not top_traders_df.empty:
            report += "\n" + create_markdown_table(top_traders_df) + "\n"
        else:
            report += "\n*No trading data available*\n"

        report += f"""
---

## Tournaments

"""

        # Get tournaments in the period
        tournaments_df = self.tournament_analytics.get_all_tournaments()
        if not tournaments_df.empty and 'created_at' in tournaments_df.columns:
            period_tournaments = self.loader.filter_by_date(tournaments_df, start_date, end_date)

            if not period_tournaments.empty:
                report += f"**Total Tournaments:** {len(period_tournaments)}\n\n"

                # List tournaments
                if 'name' in period_tournaments.columns:
                    for _, tournament in period_tournaments.head(5).iterrows():
                        tournament_name = tournament.get('name', 'Unknown')
                        tournament_date = format_date(tournament.get('created_at'))
                        report += f"- **{tournament_name}** ({tournament_date})\n"
            else:
                report += "*No tournaments in this period*\n"
        else:
            report += "*Tournament data not available*\n"

        report += f"""
---

## Data Summary

- **Period:** {format_date_range(start_date, end_date)}
- **Report Generated:** {format_date(datetime.now())}
- **Export Source:** {self.loader.export_path.name}

---

*Generated by Nova Shots Analytics Engine*
"""

        return report

    def generate_overview(self) -> str:
        """
        Generate quick overview of the export data.

        Returns:
            Markdown formatted overview
        """
        export_info = self.loader.get_export_info()
        table_names = self.loader.get_table_names()

        overview = f"""# Data Export Overview

## Export Information

- **Export Date:** {export_info.get('timestamp', 'Unknown')}
- **Total Tables:** {len(table_names)}
- **Total Rows:** {format_number(export_info.get('total_rows', 0))}

## Available Tables

"""

        for table_name in table_names:
            try:
                table_info = self.loader.get_table_info(table_name)
                row_count = table_info.get('row_count', 0)
                overview += f"- **{table_name}:** {format_number(row_count)} rows\n"
            except:
                overview += f"- **{table_name}:** (metadata unavailable)\n"

        overview += "\n---\n\n*Use the analyzer CLI to generate detailed reports*\n"

        return overview

    def export_to_json(self, data: Dict, filename: str) -> str:
        """
        Export data to JSON file.

        Args:
            data: Dictionary to export
            filename: Output filename

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return str(output_path)

    def export_to_csv(self, df, filename: str) -> str:
        """
        Export DataFrame to CSV.

        Args:
            df: pandas DataFrame
            filename: Output filename

        Returns:
            Path to generated file
        """
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        return str(output_path)
