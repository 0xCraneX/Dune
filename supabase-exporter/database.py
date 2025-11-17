"""
Database module for PostgreSQL interactions.
Handles connection management and data fetching.
"""

import time
import json
from typing import Dict, List, Generator, Optional, Any
from datetime import datetime, date
import psycopg2
import psycopg2.extras
from tqdm import tqdm
import config


class PostgreSQLClient:
    """Client for interacting with PostgreSQL database."""

    def __init__(self, database_url: str):
        """
        Initialize PostgreSQL client.

        Args:
            database_url: PostgreSQL connection string

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            self.conn = psycopg2.connect(database_url)
            self.conn.set_session(readonly=True, autocommit=True)
            # Test connection
            self._test_connection()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def _test_connection(self) -> None:
        """
        Test database connection.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {e}")

    def get_table_count(self, table_name: str) -> int:
        """
        Get total row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Total number of rows in the table
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                return count
        except Exception as e:
            print(f"Warning: Could not get count for table '{table_name}': {e}")
            return 0

    def fetch_table_schema(self, table_name: str) -> Dict:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with schema information:
            {
                'table_name': str,
                'columns': List[str],
                'sample_types': Dict[str, str]
            }
        """
        try:
            with self.conn.cursor() as cur:
                # Get column names
                cur.execute(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))

                rows = cur.fetchall()
                columns = [row[0] for row in rows]
                sample_types = {row[0]: row[1] for row in rows}

                return {
                    'table_name': table_name,
                    'columns': columns,
                    'sample_types': sample_types,
                }

        except Exception as e:
            print(f"Warning: Could not fetch schema for table '{table_name}': {e}")
            return {
                'table_name': table_name,
                'columns': [],
                'sample_types': {},
            }

    def fetch_table_data(
        self,
        table_name: str,
        batch_size: int = config.BATCH_SIZE,
        show_progress: bool = True,
    ) -> Generator[List[Dict], None, None]:
        """
        Fetch all data from a table in batches.

        Args:
            table_name: Name of the table
            batch_size: Number of rows per batch
            show_progress: Show progress bar

        Yields:
            Batches of rows as list of dictionaries
        """
        # Get total row count
        total_rows = self.get_table_count(table_name)

        if total_rows == 0:
            return

        # Create progress bar if requested
        pbar = None
        if show_progress:
            pbar = tqdm(
                total=total_rows,
                desc=f"       {total_rows:,} rows",
                unit=" rows",
                bar_format="{desc} | {bar} {percentage:3.0f}% | {elapsed}",
            )

        # Fetch batches using server-side cursor
        try:
            # Use a named cursor for server-side cursor (doesn't load all data into memory)
            with self.conn.cursor(name='fetch_cursor', cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.itersize = batch_size
                cur.execute(f"SELECT * FROM {table_name}")

                while True:
                    # Retry logic for each batch
                    for attempt in range(config.MAX_RETRIES):
                        try:
                            batch = cur.fetchmany(batch_size)
                            if not batch:
                                if pbar:
                                    pbar.close()
                                return

                            # Convert RealDictRow to regular dict and handle special types
                            batch_data = [self._serialize_row(dict(row)) for row in batch]

                            yield batch_data

                            if pbar:
                                pbar.update(len(batch_data))

                            # Success, break retry loop
                            break

                        except Exception as e:
                            if attempt < config.MAX_RETRIES - 1:
                                # Wait before retrying (exponential backoff)
                                wait_time = config.RETRY_DELAY * (2 ** attempt)
                                print(f"\nWarning: Batch fetch failed, retrying in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                # All retries exhausted
                                print(f"\nError: Failed to fetch batch after {config.MAX_RETRIES} attempts: {e}")
                                if pbar:
                                    pbar.close()
                                raise

        except Exception as e:
            if pbar:
                pbar.close()
            raise

        if pbar:
            pbar.close()

    def _serialize_row(self, row: Dict) -> Dict:
        """
        Serialize a row to JSON-compatible types.
        Converts datetime, date, and other special types to strings.

        Args:
            row: Dictionary representing a database row

        Returns:
            JSON-serializable dictionary
        """
        serialized = {}
        for key, value in row.items():
            if value is None:
                serialized[key] = None
            elif isinstance(value, (datetime, date)):
                # Convert to ISO format string
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                # Already JSON-compatible
                serialized[key] = value
            elif isinstance(value, bytes):
                # Convert bytes to string (e.g., UUID bytes)
                try:
                    serialized[key] = value.decode('utf-8')
                except:
                    serialized[key] = str(value)
            else:
                serialized[key] = value

        return serialized

    def export_table(self, table_name: str) -> Dict:
        """
        Export complete table with metadata.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with:
            {
                'table_name': str,
                'row_count': int,
                'columns': List[str],
                'data': List[Dict],
                'fetch_time_seconds': float,
                'success': bool,
                'error': Optional[str]
            }
        """
        start_time = time.time()

        try:
            # Get row count
            row_count = self.get_table_count(table_name)

            # Get schema
            schema = self.fetch_table_schema(table_name)

            # Fetch all data
            all_data = []
            for batch in self.fetch_table_data(table_name, show_progress=False):
                all_data.extend(batch)

            fetch_time = time.time() - start_time

            return {
                'table_name': table_name,
                'row_count': row_count,
                'columns': schema['columns'],
                'data': all_data,
                'fetch_time_seconds': fetch_time,
                'success': True,
                'error': None,
            }

        except Exception as e:
            fetch_time = time.time() - start_time

            return {
                'table_name': table_name,
                'row_count': 0,
                'columns': [],
                'data': [],
                'fetch_time_seconds': fetch_time,
                'success': False,
                'error': str(e),
            }

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
