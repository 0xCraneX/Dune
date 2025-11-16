"""
Database module for Supabase interactions.
Handles connection management and data fetching.
"""

import time
from typing import Dict, List, Generator, Optional
from supabase import create_client, Client
from tqdm import tqdm
import config


class SupabaseClient:
    """Client for interacting with Supabase database."""

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL
            key: Supabase API key (anon or service role)

        Raises:
            ConnectionError: If connection test fails
        """
        try:
            self.client: Client = create_client(url, key)
            # Test connection with a simple query
            self._test_connection()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")

    def _test_connection(self) -> None:
        """
        Test database connection.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Try to query a table to verify connection
            # This will fail gracefully if no tables exist
            self.client.table('players').select('id').limit(1).execute()
        except Exception as e:
            # Connection might still be valid even if specific table doesn't exist
            # Only raise if it's a connection-related error
            error_msg = str(e).lower()
            if 'connection' in error_msg or 'network' in error_msg or 'unauthorized' in error_msg:
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
            response = self.client.table(table_name).select('*', count='exact').limit(1).execute()
            return response.count if response.count is not None else 0
        except Exception as e:
            print(f"Warning: Could not get count for table '{table_name}': {e}")
            return 0

    def fetch_table_schema(self, table_name: str) -> Dict:
        """
        Get schema information for a table by inspecting data.

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
            # Fetch first row to determine schema
            response = self.client.table(table_name).select('*').limit(1).execute()

            if not response.data:
                return {
                    'table_name': table_name,
                    'columns': [],
                    'sample_types': {},
                }

            first_row = response.data[0]
            columns = list(first_row.keys())

            # Infer types from first row values
            sample_types = {}
            for col, value in first_row.items():
                sample_types[col] = type(value).__name__ if value is not None else 'null'

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

        Uses pagination with .range() method and retries on failure.
        """
        # Get total row count
        total_rows = self.get_table_count(table_name)

        if total_rows == 0:
            return

        # Calculate number of batches
        num_batches = (total_rows + batch_size - 1) // batch_size

        # Create progress bar if requested
        pbar = None
        if show_progress:
            pbar = tqdm(
                total=total_rows,
                desc=f"       {total_rows:,} rows",
                unit=" rows",
                bar_format="{desc} | {bar} {percentage:3.0f}% | {elapsed}",
            )

        # Fetch batches
        for batch_num in range(num_batches):
            start = batch_num * batch_size
            end = start + batch_size - 1

            # Retry logic
            for attempt in range(config.MAX_RETRIES):
                try:
                    response = self.client.table(table_name).select('*').range(start, end).execute()

                    batch_data = response.data
                    if batch_data:
                        yield batch_data

                        if pbar:
                            pbar.update(len(batch_data))

                    # Success, break retry loop
                    break

                except Exception as e:
                    if attempt < config.MAX_RETRIES - 1:
                        # Wait before retrying (exponential backoff)
                        wait_time = config.RETRY_DELAY * (2 ** attempt)
                        print(f"\nWarning: Batch {batch_num + 1}/{num_batches} failed, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        # All retries exhausted
                        print(f"\nError: Failed to fetch batch {batch_num + 1}/{num_batches} after {config.MAX_RETRIES} attempts: {e}")
                        if pbar:
                            pbar.close()
                        raise

        if pbar:
            pbar.close()

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
