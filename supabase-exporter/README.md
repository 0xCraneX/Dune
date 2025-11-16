# Nova Shots Database Exporter

A Python CLI tool that exports all data from the Nova Shots Supabase database to JSON files for monthly analysis. Preserves data integrity, relationships, and timestamps while handling 30 tables with up to 50k rows each.

**Primary Use Case:** Monthly export for Claude analysis of player metrics, trades, bans, and sponsorship deliverables.

## Features

- ✅ Exports 27 tables (excludes 3 system tables)
- ✅ Preserves data types, timestamps, and relationships
- ✅ Handles large tables (up to 50k+ rows)
- ✅ Generates comprehensive metadata for Claude analysis
- ✅ Progress bars and user-friendly output
- ✅ Automatic retry with exponential backoff
- ✅ Timestamped export directories
- ✅ Relationship detection between tables

## Requirements

- Python 3.8 or higher
- Supabase project with Nova Shots database
- Supabase API key (anon key or service role key)

## Installation

### 1. Clone or download the project

```bash
cd supabase-exporter
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install supabase python-dotenv tqdm
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
```

**Where to find your credentials:**

1. Log into [Supabase dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy the **URL** and **anon key** (or **service_role key** for full access)

**Important:** Use the **service role key** if you need to bypass Row Level Security (RLS) policies and export all data.

## Usage

### Basic Usage

Export all tables to a timestamped directory:

```bash
python exporter.py
```

This will create a new export in `exports/YYYY-MM-DD_HH-MM-SS/` with all table JSON files and metadata.

### Command-Line Options

```bash
python exporter.py --help
```

**Available options:**

- `--output DIR` - Output directory (default: `exports/`)
- `--table TABLE` - Export only a specific table
- `--batch-size SIZE` - Rows per batch (default: 1000)
- `--quiet` - Minimal output
- `--version` - Show version information

### Examples

```bash
# Export everything (default)
python exporter.py

# Export to a specific directory
python exporter.py --output ./backups

# Export only the players table
python exporter.py --table players

# Use larger batches for faster export (uses more memory)
python exporter.py --batch-size 5000

# Quiet mode (minimal output)
python exporter.py --quiet
```

## Output Structure

Each export creates a timestamped directory:

```
exports/
└── 2024-11-15_14-30-00/
    ├── _metadata.json           # Export metadata and schema info
    ├── players.json             # Player records
    ├── transactions.json        # Transaction records
    ├── tournaments.json         # Tournament records
    ├── leaderboards.json        # Leaderboard data
    └── ... (24 more table files)
```

### Metadata File

The `_metadata.json` file contains:

- Export timestamp and version
- Per-table row counts and schemas
- Date ranges (min/max created_at)
- Detected relationships between tables
- File sizes and column information
- Sample rows for schema understanding

**This file should be uploaded to Claude FIRST** to provide context about the export.

### Table Files

Each table is exported as a pretty-printed JSON array:

```json
[
  {
    "id": "uuid-or-int",
    "created_at": "2024-01-15T10:30:00+00:00",
    "updated_at": "2024-01-15T10:30:00+00:00",
    "field1": "value1",
    "field2": 123,
    "field3": true
  },
  ...
]
```

**Features:**
- Preserves data types (numbers, booleans, null, arrays, objects)
- ISO 8601 timestamps with timezone
- Pretty-printed with 2-space indentation
- Sorted keys for consistency

## Exported Tables

The tool exports **27 tables** from the Nova Shots database:

**Player & User Data:**
- `players` - Player profiles and wallet addresses
- `users` - User accounts
- `banned_ips` - IP ban records

**Tournaments & Matches:**
- `tournaments` - Tournament definitions
- `prediction_tournaments` - Prediction-based tournaments
- `prediction_matches` - Prediction match data
- `blast_matches` - Blast tournament matches
- `teams` - Team information

**Trading & Economy:**
- `transactions` - All player transactions
- `portfolios` - Player portfolio snapshots
- `portfolio_history` - Historical portfolio data
- `prices` - Token price history
- `token_configurations` - Token settings
- `token_data` - Token metadata

**Leaderboards & Quests:**
- `leaderboards` - Leaderboard definitions
- `leaderboard_entries` - Leaderboard rankings
- `quests` - Quest definitions
- `daily_predictions` - Daily prediction data

**Rewards & Airdrops:**
- `airdrop_distributions` - Airdrop distribution records
- `airdrop_requests` - Airdrop request records
- `distributions` - General distribution records

**Other:**
- `referral_codes` - Referral code data
- `referrals` - Referral relationships
- `store` - Store items
- `jobs` - Background job data
- `notices` - System notices
- `faq` - FAQ content

**Skipped Tables (System/Internal):**
- `typeorm_migrations` - Database migrations
- `indexing` - Internal indexing
- `integrity` - Internal integrity checks

## Data Analysis Workflow with Claude

### Step 1: Upload Metadata First

Upload `_metadata.json` to Claude so it understands:
- What tables exist and their sizes
- Date ranges for temporal analysis
- Relationships between tables
- Schema information

### Step 2: Ask Your Analysis Question

Example questions:
- "How many new players joined during October?"
- "What were the top 10 most traded tokens this month?"
- "Show me the leaderboard winners and their rewards"
- "Analyze referral program effectiveness"

### Step 3: Claude Requests Specific Tables

Based on your question, Claude will ask for specific table files (e.g., `players.json`, `transactions.json`)

### Step 4: Upload Requested Tables

Upload only the files Claude needs - this saves time and reduces context size.

### Step 5: Claude Analyzes

Claude can:
- Filter by date ranges using `created_at`
- Count records matching criteria
- Cross-reference tables using foreign keys
- Aggregate data (sum trades, count bans, etc.)
- Generate reports or visualizations

## Troubleshooting

### Error: "SUPABASE_URL is not set"

**Solution:** Create a `.env` file with your Supabase credentials. Copy `.env.example` to `.env` and fill in your values.

### Error: "Connection test failed"

**Possible causes:**
- Invalid Supabase URL or API key
- Network connectivity issues
- Project doesn't exist or is paused

**Solution:**
1. Verify your credentials in the Supabase dashboard
2. Check your internet connection
3. Ensure your Supabase project is active

### Error: "Could not get count for table"

**Possible causes:**
- Row Level Security (RLS) policies restricting access
- Table doesn't exist
- Insufficient permissions

**Solution:**
- Use the **service role key** instead of the anon key for full access
- Verify the table exists in your database

### Fewer rows exported than expected

**Cause:** RLS policies limiting access with user-level (anon) key

**Solution:** Use the **service role key** from Supabase dashboard (Settings → API) which bypasses RLS.

### Export is slow

**Solutions:**
1. Increase batch size: `python exporter.py --batch-size 5000`
2. Run overnight for very large databases
3. Export specific tables only: `python exporter.py --table players`

### Network interruptions during export

The tool automatically retries failed requests up to 3 times with exponential backoff. Each table is saved independently, so partial exports are still useful.

## Performance

**Typical performance:**
- **Small tables** (< 1,000 rows): 1-5 seconds
- **Medium tables** (1,000 - 10,000 rows): 5-30 seconds
- **Large tables** (10,000 - 50,000 rows): 30-120 seconds

**Full database export:** 2-5 minutes for ~500k total rows

**Memory usage:** < 500 MB RAM during export

## Security Notes

- **Never commit `.env` file to git** - it contains sensitive credentials
- **Don't share export files publicly** - they may contain sensitive user data
- **Store exports securely** - use encrypted storage if needed
- **Use service role key carefully** - it has full database access

The `.gitignore` file is configured to exclude `.env` and `exports/` from git.

## Development

### Project Structure

```
supabase-exporter/
├── config.py          # Configuration and constants
├── database.py        # Supabase client and data fetching
├── models.py          # Data models and validation
├── utils.py           # Helper functions
├── exporter.py        # Main export orchestration (entry point)
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── exports/           # Output directory (gitignored)
```

### Running Tests

Test the connection and export a small table:

```bash
python exporter.py --table faq
```

Verify the output:

1. Check `exports/YYYY-MM-DD_HH-MM-SS/` exists
2. Open `_metadata.json` - should show table info
3. Open `faq.json` - should be valid JSON

### Contributing

This is a standalone utility for Nova Shots internal use. Modify as needed for your requirements.

## Version History

- **v1.0.0** (2024-11-15) - Initial release
  - Export 27 tables from Nova Shots database
  - Metadata generation with relationship detection
  - Progress bars and retry logic
  - Comprehensive documentation

## License

Proprietary - Nova Shots internal tool

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Supabase documentation](https://supabase.com/docs)
3. Contact the Nova Shots development team

---

**Happy exporting!** 🚀
