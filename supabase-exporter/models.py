"""
Data models and validation for exports.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class TableMetadata:
    """Metadata for a single table."""

    table_name: str
    row_count: int
    columns: List[str]
    has_created_at: bool = False
    has_updated_at: bool = False
    date_range: Optional[Dict[str, Any]] = None
    file_path: str = ""
    file_size_bytes: int = 0
    sample_row: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ExportMetadata:
    """Metadata for an export run."""

    export_timestamp: str
    export_version: str
    database_url: str  # Sanitized
    total_tables: int
    exported_tables: int
    skipped_tables: List[str]
    total_rows: int
    export_duration_seconds: float
    config: Dict[str, Any] = field(default_factory=dict)
    tables: Dict[str, TableMetadata] = field(default_factory=dict)
    relationships: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'export_info': {
                'timestamp': self.export_timestamp,
                'version': self.export_version,
                'database_url': self.database_url,
                'total_tables': self.total_tables,
                'exported_tables': self.exported_tables,
                'total_rows': self.total_rows,
                'export_duration_seconds': self.export_duration_seconds,
                'config': self.config,
            },
            'tables': {
                name: metadata.to_dict()
                for name, metadata in self.tables.items()
            },
            'relationships': self.relationships,
        }
        return result


def extract_date_range(data: List[Dict]) -> Optional[Dict]:
    """
    Extract min/max dates from created_at field.

    Args:
        data: List of records with potential created_at field

    Returns:
        Dictionary with min/max dates and span, or None if no dates found

    Returns:
        {
            'min_created_at': str,
            'max_created_at': str,
            'span_days': int
        }
    """
    if not data:
        return None

    # Collect all created_at values
    dates = []
    for record in data:
        if 'created_at' in record and record['created_at']:
            try:
                # Parse ISO format datetime
                date_str = record['created_at']
                # Handle both with and without timezone
                if 'T' in date_str:
                    dates.append(date_str)
            except (ValueError, TypeError):
                continue

    if not dates:
        return None

    # Sort dates to find min and max
    dates.sort()
    min_date = dates[0]
    max_date = dates[-1]

    # Calculate span in days
    try:
        # Parse dates to calculate difference
        min_dt = datetime.fromisoformat(min_date.replace('Z', '+00:00'))
        max_dt = datetime.fromisoformat(max_date.replace('Z', '+00:00'))
        span_days = (max_dt - min_dt).days
    except (ValueError, TypeError):
        span_days = 0

    return {
        'min_created_at': min_date,
        'max_created_at': max_date,
        'span_days': span_days,
    }


def detect_has_timestamp_fields(data: List[Dict]) -> tuple:
    """
    Detect if data has created_at and updated_at fields.

    Args:
        data: List of records

    Returns:
        Tuple of (has_created_at, has_updated_at)
    """
    if not data:
        return False, False

    # Check first record (assume consistent schema)
    first_record = data[0]
    has_created_at = 'created_at' in first_record
    has_updated_at = 'updated_at' in first_record

    return has_created_at, has_updated_at
