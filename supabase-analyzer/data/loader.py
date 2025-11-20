"""
Data loading and caching layer for exported Nova Shots data.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd


class DataLoader:
    """
    Loads and caches exported Nova Shots database data.
    Provides efficient access to tables as pandas DataFrames.
    """

    def __init__(self, export_path: str):
        """
        Initialize data loader with export directory.

        Args:
            export_path: Path to export folder (e.g., exports/2025-11-20_11-10-33/)
        """
        self.export_path = Path(export_path)

        if not self.export_path.exists():
            raise ValueError(f"Export path does not exist: {export_path}")

        # Load metadata first
        self.metadata = self.load_metadata()

        # Cache for loaded tables
        self._table_cache: Dict[str, pd.DataFrame] = {}

        # Get available tables from metadata
        self.available_tables = list(self.metadata.get('tables', {}).keys())

    def load_metadata(self) -> Dict:
        """
        Load and parse _metadata.json.

        Returns:
            Dictionary containing export metadata
        """
        metadata_path = self.export_path / '_metadata.json'

        if not metadata_path.exists():
            raise ValueError(f"Metadata file not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Validate required fields
        if 'export_info' not in metadata:
            raise ValueError("Invalid metadata: missing 'export_info'")
        if 'tables' not in metadata:
            raise ValueError("Invalid metadata: missing 'tables'")

        return metadata

    def load_table(self, table_name: str) -> pd.DataFrame:
        """
        Load a table as pandas DataFrame with caching.

        Args:
            table_name: Name of the table to load

        Returns:
            DataFrame containing table data
        """
        # Check cache first
        if table_name in self._table_cache:
            return self._table_cache[table_name]

        # Verify table exists
        if table_name not in self.available_tables:
            raise ValueError(
                f"Table '{table_name}' not found. Available tables: {', '.join(self.available_tables)}"
            )

        # Load from JSON file
        table_path = self.export_path / f"{table_name}.json"

        if not table_path.exists():
            raise ValueError(f"Table file not found: {table_path}")

        # Read JSON and convert to DataFrame
        with open(table_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            # Empty table
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)

            # Parse datetime columns
            datetime_columns = ['created_at', 'updated_at', 'timestamp', 'date']
            for col in datetime_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

        # Cache the DataFrame
        self._table_cache[table_name] = df

        return df

    def get_table_names(self) -> List[str]:
        """
        Get list of all available tables.

        Returns:
            Sorted list of table names
        """
        return sorted(self.available_tables)

    def get_date_range(self, table_name: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Get min/max dates from created_at column.

        Args:
            table_name: Name of the table

        Returns:
            Tuple of (min_date, max_date) or None if no created_at column
        """
        df = self.load_table(table_name)

        if df.empty or 'created_at' not in df.columns:
            return None

        return (df['created_at'].min(), df['created_at'].max())

    def filter_by_date(
        self,
        df: pd.DataFrame,
        start: datetime,
        end: datetime,
        date_column: str = 'created_at'
    ) -> pd.DataFrame:
        """
        Filter DataFrame by date range.

        Args:
            df: DataFrame to filter
            start: Start date (inclusive)
            end: End date (inclusive)
            date_column: Column name to filter on

        Returns:
            Filtered DataFrame
        """
        if date_column not in df.columns:
            raise ValueError(f"Column '{date_column}' not found in DataFrame")

        mask = (df[date_column] >= start) & (df[date_column] <= end)
        return df[mask].copy()

    def join_tables(
        self,
        left_table: str,
        right_table: str,
        left_on: str,
        right_on: str,
        how: str = 'inner'
    ) -> pd.DataFrame:
        """
        Join two tables based on foreign key relationship.

        Args:
            left_table: Name of left table
            right_table: Name of right table
            left_on: Column in left table
            right_on: Column in right table
            how: Join type ('inner', 'left', 'right', 'outer')

        Returns:
            Joined DataFrame
        """
        left_df = self.load_table(left_table)
        right_df = self.load_table(right_table)

        return pd.merge(
            left_df,
            right_df,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffixes=('', f'_{right_table}')
        )

    def clear_cache(self) -> None:
        """Clear all cached tables to free memory."""
        self._table_cache.clear()

    def get_export_info(self) -> Dict:
        """Get export information from metadata."""
        return self.metadata.get('export_info', {})

    def get_table_info(self, table_name: str) -> Dict:
        """
        Get metadata information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table metadata
        """
        tables_meta = self.metadata.get('tables', {})
        if table_name not in tables_meta:
            raise ValueError(f"Table '{table_name}' not found in metadata")

        return tables_meta[table_name]

    def get_relationships(self) -> List[Dict]:
        """Get detected relationships from metadata."""
        return self.metadata.get('relationships', [])
