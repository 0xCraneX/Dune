"""
Configuration constants for Nova Shots Analyzer.
"""

# Date formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DISPLAY_DATE_FORMAT = '%b %d, %Y'

# Analysis thresholds
WHALE_THRESHOLD = 100000  # Tokens to be considered whale
HIGH_FREQUENCY_TRADES = 50  # Trades per day threshold
SUSPICIOUS_PATTERN_SCORE = 0.8  # Bot detection threshold

# Report defaults
DEFAULT_TOP_N = 100  # Default for top-X queries
DEFAULT_LOOKBACK_DAYS = 30  # For retention calculations
RETENTION_DAYS = [1, 7, 30]  # Standard retention periods

# Output configuration
OUTPUT_DIR = 'outputs'
SUPPORTED_FORMATS = ['markdown', 'json', 'csv']

# Template paths
TEMPLATE_DIR = 'reports/templates'

# Table names (from exporter)
TABLE_NAMES = {
    'players': 'players',
    'users': 'users',
    'transactions': 'transactions',
    'portfolios': 'portfolios',
    'portfolio_history': 'portfolio_history',
    'tournaments': 'tournaments',
    'prediction_tournaments': 'prediction_tournaments',
    'prediction_matches': 'prediction_matches',
    'blast_matches': 'blast_matches',
    'teams': 'teams',
    'leaderboards': 'leaderboards',
    'leaderboard_entries': 'leaderboard_entries',
    'quests': 'quests',
    'daily_predictions': 'daily_predictions',
    'prices': 'prices',
    'token_data': 'token_data',
    'token_configurations': 'token_configurations',
    'airdrop_distributions': 'airdrop_distributions',
    'airdrop_requests': 'airdrop_requests',
    'distributions': 'distributions',
    'referral_codes': 'referral_codes',
    'referrals': 'referrals',
    'banned_ips': 'banned_ips',
    'notices': 'notices',
    'faq': 'faq',
    'store': 'store',
    'jobs': 'jobs',
}
