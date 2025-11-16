"""
Configuration module for Supabase Exporter.
Centralizes all configuration, constants, and environment variables.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Environment Variables
# ============================================================================

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# ============================================================================
# Export Constants
# ============================================================================

BATCH_SIZE = 1000  # Rows to fetch per request
MAX_RETRIES = 3  # Retry attempts for failed requests
RETRY_DELAY = 2  # Seconds between retries
REQUEST_TIMEOUT = 30  # Timeout for API requests (seconds)
OUTPUT_DIR = 'exports'  # Base export directory
EXPORT_VERSION = '1.0.0'  # Version of the export format

# ============================================================================
# Table Configuration
# ============================================================================

# All 30 tables from the Nova Shots database
ALL_TABLES = [
    'airdrop_distributions',
    'airdrop_requests',
    'banned_ips',
    'blast_matches',
    'daily_predictions',
    'distributions',
    'faq',
    'indexing',
    'integrity',
    'jobs',
    'leaderboard_entries',
    'leaderboards',
    'notices',
    'players',
    'portfolio_history',
    'portfolios',
    'prediction_matches',
    'prediction_tournaments',
    'prices',
    'quests',
    'referral_codes',
    'referrals',
    'store',
    'teams',
    'token_configurations',
    'token_data',
    'tournaments',
    'transactions',
    'typeorm_migrations',
    'users',
]

# System tables to skip (internal/migration tables)
SKIP_TABLES = [
    'typeorm_migrations',
    'indexing',
    'integrity',
]

# Tables to export (27 tables)
EXPORT_TABLES = [t for t in ALL_TABLES if t not in SKIP_TABLES]

# ============================================================================
# Validation
# ============================================================================

def validate_config() -> bool:
    """
    Validates that required environment variables are set.
    Prints configuration summary.
    Raises ValueError if config is invalid.

    Returns:
        bool: True if configuration is valid
    """
    errors = []

    # Check required environment variables
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is not set")
    elif not SUPABASE_URL.startswith('https://'):
        errors.append("SUPABASE_URL must start with https://")

    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY is not set")

    # If there are errors, raise exception
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        error_msg += "\n\nPlease check your .env file and ensure all required variables are set."
        raise ValueError(error_msg)

    return True


def print_config_summary() -> None:
    """Print a summary of the current configuration."""
    print("Configuration:")
    print(f"  Database URL: {sanitize_url(SUPABASE_URL)}")
    print(f"  API Key: {'*' * 20}{SUPABASE_KEY[-8:] if len(SUPABASE_KEY) > 8 else '***'}")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Max Retries: {MAX_RETRIES}")
    print(f"  Tables to Export: {len(EXPORT_TABLES)}")
    print(f"  Skipped Tables: {', '.join(SKIP_TABLES)}")
    print()


def sanitize_url(url: str) -> str:
    """
    Remove sensitive parts from URL for logging.
    Keeps only protocol and domain.

    Args:
        url: The URL to sanitize

    Returns:
        Sanitized URL string
    """
    if not url:
        return ""

    # Extract just the protocol and domain
    if '://' in url:
        parts = url.split('/')
        return f"{parts[0]}//{parts[2]}"

    return url
