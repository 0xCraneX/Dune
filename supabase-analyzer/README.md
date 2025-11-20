# Nova Shots Data Analyzer

A Python CLI tool that analyzes exported Nova Shots database data to generate insights, reports, and metrics for stakeholder reporting and sponsorship deliverables.

**Primary Use Cases:**
- Monthly performance reporting
- Sponsorship deliverable validation
- Player growth tracking
- Tournament performance analysis
- Trading volume and engagement metrics

## Features

- ✅ **Player Analytics** - Growth, retention, activity metrics
- ✅ **Tournament Analytics** - Participation, predictions, performance
- ✅ **Trading Analytics** - Volume, frequency, top traders
- ✅ **Sponsorship Reporting** - Deliverables tracking and validation
- ✅ **Monthly Reports** - Comprehensive automated reports
- ✅ **Multiple Output Formats** - Markdown, JSON, CSV

## Requirements

- Python 3.9 or higher
- Exported data from `supabase-exporter`

## Installation

### 1. Navigate to the analyzer directory

```bash
cd supabase-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pandas` - Data analysis
- `numpy` - Numerical computations
- `python-dateutil` - Date handling
- `click` - CLI framework
- `jinja2` - Template rendering
- `tabulate` - Table formatting

### 3. Make the CLI executable (optional)

```bash
chmod +x analyzer.py
```

## Usage

### Quick Start

```bash
# Get overview of your export
python analyzer.py overview --export path/to/export/2025-11-20_11-10-33/

# Generate monthly report
python analyzer.py monthly --export path/to/export/ --month 11 --year 2024

# Analyze specific tournament
python analyzer.py tournament --export path/to/export/ --tournament-id TOURNAMENT_ID
```

---

## Commands

### `overview` - Quick Data Overview

Show summary of exported data:

```bash
python analyzer.py overview --export path/to/export/
```

**Output:**
- Export date and metadata
- List of available tables
- Row counts per table

---

### `monthly` - Generate Monthly Report

Create comprehensive monthly performance report:

```bash
python analyzer.py monthly \
  --export path/to/export/ \
  --month 11 \
  --year 2024 \
  --output november_2024.md
```

**Options:**
- `--export` - Path to export directory (required)
- `--month` - Month number 1-12 (required)
- `--year` - Year (required)
- `--output` - Custom output filename (optional)

**Generated Report Includes:**
- Executive summary with key metrics
- Player growth and activity
- Trading volume and trends
- Tournament highlights
- Top traders table

**Output:** Markdown file in `outputs/` directory

---

### `players` - Player Metrics Analysis

Analyze player growth and engagement:

```bash
python analyzer.py players \
  --export path/to/export/ \
  --start 2024-11-01 \
  --end 2024-11-30
```

**Options:**
- `--export` - Path to export directory (required)
- `--start` - Start date YYYY-MM-DD (required)
- `--end` - End date YYYY-MM-DD (required)

**Output (Console):**
- Total players
- New players in period
- Active players (30-day)
- Growth rate

---

### `trading` - Trading Metrics Analysis

Analyze trading activity:

```bash
python analyzer.py trading \
  --export path/to/export/ \
  --start 2024-11-01 \
  --end 2024-11-30
```

**Options:**
- `--export` - Path to export directory (required)
- `--start` - Start date YYYY-MM-DD (required)
- `--end` - End date YYYY-MM-DD (required)

**Output (Console):**
- Total transactions
- Unique traders
- Average daily metrics

---

### `tournament` - Tournament Performance

Analyze specific tournament:

```bash
python analyzer.py tournament \
  --export path/to/export/ \
  --tournament-id BLAST_SEASON_2
```

**Options:**
- `--export` - Path to export directory (required)
- `--tournament-id` - Tournament identifier (required)

**Output (Console):**
- Tournament name and date
- Total participants
- New users acquired
- Total predictions
- Average predictions per user

---

### `sponsorship` - Sponsorship Deliverables

Generate sponsorship report with contract validation:

```bash
python analyzer.py sponsorship \
  --export path/to/export/ \
  --tournament-id BLAST_SEASON_2 \
  --contract blast_contract.json \
  --output blast_deliverables.md
```

**Options:**
- `--export` - Path to export directory (required)
- `--tournament-id` - Tournament identifier (required)
- `--contract` - Path to contract JSON file (optional)
- `--output` - Output filename (optional, prints to console if not provided)

**Contract JSON Format:**
```json
{
  "sponsor_name": "Blast.tv",
  "min_participants": 1000,
  "min_predictions": 5000,
  "min_new_users": 500,
  "duration_days": 14
}
```

**Output:**
- Contract deliverables comparison table
- Actual vs target metrics with status (✓/✗)
- Performance percentages
- Overall status

---

### `list-tournaments` - List Available Tournaments

Show all tournaments in the export:

```bash
python analyzer.py list-tournaments --export path/to/export/
```

**Output (Console):**
- Tournament IDs
- Tournament names
- Dates

---

## Example Workflows

### Monthly Stakeholder Report

```bash
# 1. Generate comprehensive monthly report
python analyzer.py monthly \
  --export exports/2025-11-20_11-10-33/ \
  --month 11 \
  --year 2024

# Output: outputs/2024_november_report.md
```

### Tournament Sponsorship Review

```bash
# 1. List available tournaments
python analyzer.py list-tournaments --export exports/2025-11-20_11-10-33/

# 2. Analyze specific tournament
python analyzer.py tournament \
  --export exports/2025-11-20_11-10-33/ \
  --tournament-id YOUR_TOURNAMENT_ID

# 3. Generate deliverables report with contract
python analyzer.py sponsorship \
  --export exports/2025-11-20_11-10-33/ \
  --tournament-id YOUR_TOURNAMENT_ID \
  --contract contracts/blast_contract.json \
  --output blast_deliverables.md
```

### Custom Period Analysis

```bash
# Analyze October 2024
python analyzer.py players \
  --export exports/2025-11-20_11-10-33/ \
  --start 2024-10-01 \
  --end 2024-10-31

python analyzer.py trading \
  --export exports/2025-11-20_11-10-33/ \
  --start 2024-10-01 \
  --end 2024-10-31
```

---

## Output Directory Structure

```
supabase-analyzer/
├── outputs/                      # Generated reports
│   ├── 2024_november_report.md
│   ├── blast_deliverables.md
│   └── custom_analysis.csv
└── ... (source files)
```

---

## Python API Usage

You can also use the analyzer programmatically:

```python
from data.loader import DataLoader
from analytics.players import PlayerAnalytics
from analytics.tournaments import TournamentAnalytics
from reports.generators import ReportGenerator

# Load data
loader = DataLoader('exports/2025-11-20_11-10-33/')

# Get player analytics
player_analytics = PlayerAnalytics(loader)
summary = player_analytics.get_player_summary(start_date, end_date)

# Generate report
report_gen = ReportGenerator(loader)
report_path = report_gen.generate_monthly_report(11, 2024)
```

---

## Data Requirements

The analyzer expects exported data from the `supabase-exporter` tool with:

- `_metadata.json` - Export metadata
- Individual table JSON files (e.g., `players.json`, `transactions.json`)

**Required Tables for Full Functionality:**
- `players` - Player metrics
- `transactions` - Trading analytics
- `tournaments` - Tournament data
- `prediction_tournaments` - Tournament predictions
- `portfolios` - Portfolio analysis

---

## Troubleshooting

### Error: "Export path does not exist"
**Solution:** Ensure you provide the correct path to the export directory containing `_metadata.json`.

```bash
# Correct
python analyzer.py overview --export exports/2025-11-20_11-10-33/

# Incorrect
python analyzer.py overview --export exports/
```

### Error: "Table 'X' not found"
**Cause:** The export doesn't contain the required table.
**Solution:** Re-run the exporter or use commands that don't require that table.

### Empty Output / "No data available"
**Cause:** Date range doesn't match data, or table is empty.
**Solution:** Check the export date range using `overview` command first.

### Tournament ID not found
**Solution:** Use `list-tournaments` to see available tournament IDs.

---

## Report Formats

### Markdown (Default)
- Human-readable
- Easy to share in documentation
- Version control friendly
- Can be converted to HTML/PDF

### JSON (for programmatic access)
```python
report_gen.export_to_json(data, 'output.json')
```

### CSV (for Excel analysis)
```python
report_gen.export_to_csv(dataframe, 'output.csv')
```

---

## Advanced Usage

### Custom Date Ranges

All date-based commands accept custom ranges:

```bash
python analyzer.py players \
  --export path/to/export/ \
  --start 2024-01-01 \
  --end 2024-12-31
```

### Batch Processing

Process multiple months:

```bash
for month in {1..12}; do
  python analyzer.py monthly \
    --export exports/2025-11-20_11-10-33/ \
    --month $month \
    --year 2024
done
```

---

## Development

### Project Structure

```
supabase-analyzer/
├── analyzer.py              # Main CLI
├── config.py                # Configuration
├── data/
│   └── loader.py           # Data loading layer
├── analytics/
│   ├── players.py          # Player analytics
│   ├── tournaments.py      # Tournament analytics
│   ├── trading.py          # Trading analytics
│   └── sponsorship.py      # Sponsorship tracking
├── reports/
│   └── generators.py       # Report generation
└── utils/
    └── formatters.py       # Formatting utilities
```

### Adding Custom Analytics

Extend the analytics modules:

```python
# In analytics/custom.py
class CustomAnalytics:
    def __init__(self, loader):
        self.loader = loader

    def my_custom_metric(self):
        # Your logic here
        pass
```

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review example workflows
3. Examine the `_metadata.json` file in your export

---

## Version History

- **v1.0.0** - Initial release
  - Player, tournament, trading analytics
  - Monthly reporting
  - Sponsorship deliverables tracking
  - CLI interface

---

**Built for Nova Shots** 🎯
