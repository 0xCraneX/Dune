"""
Utility functions for file operations, formatting, and helpers.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


def create_export_directory(base_dir: str) -> Path:
    """
    Create timestamped export directory.

    Args:
        base_dir: Base directory for exports

    Returns:
        Path object pointing to the created directory

    Format: YYYY-MM-DD_HH-MM-SS
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    export_path = Path(base_dir) / timestamp
    export_path.mkdir(parents=True, exist_ok=True)
    return export_path


def save_json(data: Any, filepath: Path, pretty: bool = True) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save (must be JSON serializable)
        filepath: Path where to save the file
        pretty: If True, pretty print with indentation

    Creates parent directories if needed.
    Uses UTF-8 encoding.
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        else:
            json.dump(data, f, ensure_ascii=False)


def load_json(filepath: Path) -> Optional[Any]:
    """
    Load JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Loaded data or None if file doesn't exist or is invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 MB")

    Examples:
        1024 -> "1.0 KB"
        1048576 -> "1.0 MB"
        1073741824 -> "1.0 GB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1m 5s", "1h 30m")

    Examples:
        65 -> "1m 5s"
        3665 -> "1h 1m 5s"
        45 -> "45s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes > 0:
        if remaining_seconds > 0:
            return f"{hours}h {remaining_minutes}m {remaining_seconds}s"
        return f"{hours}h {remaining_minutes}m"

    return f"{hours}h"


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


def get_file_size(filepath: Path) -> int:
    """
    Get file size in bytes.

    Args:
        filepath: Path to file

    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return filepath.stat().st_size
    except FileNotFoundError:
        return 0
