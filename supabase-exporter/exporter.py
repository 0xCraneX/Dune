#!/usr/bin/env python3
"""
Nova Shots Database Exporter
Main export orchestration module.
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import config
from database import SupabaseClient
from models import ExportMetadata, TableMetadata, extract_date_range, detect_has_timestamp_fields
from utils import (
    create_export_directory,
    save_json,
    format_bytes,
    format_duration,
    sanitize_url,
    get_file_size,
)


class DatabaseExporter:
    """Main class for orchestrating database exports."""

    def __init__(self, output_base_dir: str = config.OUTPUT_DIR):
        """
        Initialize the exporter.

        Args:
            output_base_dir: Base directory for exports
        """
        self.output_base_dir = output_base_dir
        self.export_dir: Optional[Path] = None
        self.client: Optional[SupabaseClient] = None
        self.metadata: Optional[ExportMetadata] = None
        self.errors: List[Dict] = []

    def export_all(self) -> str:
        """
        Main export orchestration function.
        Exports all tables and generates metadata.

        Returns:
            Path to export directory
        """
        start_time = time.time()

        # Create export directory
        self.export_dir = create_export_directory(self.output_base_dir)
        print(f"Starting export to: {self.export_dir}/\n")

        # Initialize Supabase client
        print("Connecting to database...")
        try:
            self.client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
            print("✓ Connected successfully\n")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)

        # Initialize metadata
        self.metadata = ExportMetadata(
            export_timestamp=datetime.now().isoformat(),
            export_version=config.EXPORT_VERSION,
            database_url=sanitize_url(config.SUPABASE_URL),
            total_tables=len(config.ALL_TABLES),
            exported_tables=0,
            skipped_tables=config.SKIP_TABLES,
            total_rows=0,
            export_duration_seconds=0,
            config={
                'batch_size': config.BATCH_SIZE,
                'skipped_tables': config.SKIP_TABLES,
            },
        )

        # Export all tables
        print(f"Exporting {len(config.EXPORT_TABLES)} tables...\n")

        successful_exports = 0
        total_rows = 0

        for idx, table_name in enumerate(config.EXPORT_TABLES, 1):
            print(f"[{idx}/{len(config.EXPORT_TABLES)}] Exporting {table_name}...")

            success, rows = self.export_single_table(table_name)

            if success:
                successful_exports += 1
                total_rows += rows
                print(f"       ✓ Saved to {table_name}.json ({format_bytes(get_file_size(self.export_dir / f'{table_name}.json'))})\n")
            else:
                print(f"       ✗ Failed to export {table_name}\n")

        # Update metadata totals
        self.metadata.exported_tables = successful_exports
        self.metadata.total_rows = total_rows
        self.metadata.export_duration_seconds = time.time() - start_time

        # Detect relationships
        print("Detecting table relationships...")
        self.metadata.relationships = self.detect_relationships()
        print(f"✓ Found {len(self.metadata.relationships)} probable relationships\n")

        # Save metadata
        print("Generating metadata...")
        self.save_metadata()
        print("✓ Saved to _metadata.json\n")

        # Save errors if any
        if self.errors:
            error_file = self.export_dir / '_errors.json'
            save_json(self.errors, error_file)
            print(f"⚠ Errors logged to _errors.json\n")

        # Print summary
        self.print_summary()

        return str(self.export_dir)

    def export_single_table(self, table_name: str) -> tuple:
        """
        Export a single table to JSON.

        Args:
            table_name: Name of the table to export

        Returns:
            Tuple of (success: bool, row_count: int)
        """
        try:
            # Get table count
            row_count = self.client.get_table_count(table_name)

            if row_count == 0:
                print(f"       (empty table, skipping)")
                # Still create metadata for empty table
                table_metadata = TableMetadata(
                    table_name=table_name,
                    row_count=0,
                    columns=[],
                    file_path=f"{table_name}.json",
                )
                self.metadata.tables[table_name] = table_metadata
                return True, 0

            # Fetch all data in batches
            all_data = []
            for batch in self.client.fetch_table_data(table_name, show_progress=True):
                all_data.extend(batch)

            # Save to JSON file
            json_file = self.export_dir / f"{table_name}.json"
            save_json(all_data, json_file, pretty=True)

            # Generate table metadata
            table_metadata = self._create_table_metadata(table_name, all_data, json_file)
            self.metadata.tables[table_name] = table_metadata

            return True, row_count

        except Exception as e:
            error_info = {
                'table': table_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
            self.errors.append(error_info)
            return False, 0

    def _create_table_metadata(
        self,
        table_name: str,
        data: List[Dict],
        json_file: Path,
    ) -> TableMetadata:
        """
        Create metadata for a table.

        Args:
            table_name: Name of the table
            data: Table data
            json_file: Path to JSON file

        Returns:
            TableMetadata object
        """
        # Get columns from first row
        columns = list(data[0].keys()) if data else []

        # Detect timestamp fields
        has_created_at, has_updated_at = detect_has_timestamp_fields(data)

        # Extract date range if created_at exists
        date_range = None
        if has_created_at:
            date_range = extract_date_range(data)

        # Get sample row (first row)
        sample_row = data[0] if data else None

        # Create metadata
        metadata = TableMetadata(
            table_name=table_name,
            row_count=len(data),
            columns=columns,
            has_created_at=has_created_at,
            has_updated_at=has_updated_at,
            date_range=date_range,
            file_path=f"{table_name}.json",
            file_size_bytes=get_file_size(json_file),
            sample_row=sample_row,
        )

        return metadata

    def detect_relationships(self) -> List[Dict]:
        """
        Detect potential foreign key relationships using heuristics.

        Returns:
            List of probable relationships:
            [
                {
                    'from_table': 'transactions',
                    'from_column': 'player_id',
                    'to_table': 'players',
                    'to_column': 'id',
                    'confidence': 'high' | 'medium' | 'low'
                }
            ]
        """
        relationships = []
        exported_tables = set(config.EXPORT_TABLES)

        for table_name, table_metadata in self.metadata.tables.items():
            # Look for columns ending in _id
            for column in table_metadata.columns:
                if column.endswith('_id') and column != 'id':
                    # Extract potential target table name
                    # e.g., player_id -> players, tournament_id -> tournaments
                    base_name = column[:-3]  # Remove '_id'

                    # Try both singular and plural forms
                    potential_targets = [
                        base_name,  # Exact match
                        base_name + 's',  # Plural
                        base_name + 'es',  # Plural (match -> matches)
                    ]

                    # Check if any potential target exists
                    for target in potential_targets:
                        if target in exported_tables:
                            relationships.append({
                                'from_table': table_name,
                                'from_column': column,
                                'to_table': target,
                                'to_column': 'id',
                                'confidence': 'high',
                            })
                            break

        return relationships

    def save_metadata(self) -> None:
        """Generate and save _metadata.json."""
        metadata_file = self.export_dir / '_metadata.json'
        save_json(self.metadata.to_dict(), metadata_file, pretty=True)

    def print_summary(self) -> None:
        """Print export summary."""
        duration = self.metadata.export_duration_seconds
        total_size = sum(
            metadata.file_size_bytes
            for metadata in self.metadata.tables.values()
        )

        print("=" * 50)
        print("Export Complete! ✓")
        print("=" * 50)
        print(f"Exported: {self.metadata.exported_tables} tables, {self.metadata.total_rows:,} rows")
        print(f"Duration: {format_duration(duration)}")
        print(f"Location: {self.export_dir}/")
        print(f"Size: {format_bytes(total_size)}")
        print()
        print(f"Failed tables: {len(self.errors)}")
        print(f"Warnings: 0")
        print()
        print("Next steps:")
        print("1. Upload _metadata.json to Claude first")
        print("2. Upload specific table files as needed for analysis")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Export Nova Shots Supabase database to JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export everything (default)
  python exporter.py

  # Export to specific directory
  python exporter.py --output ./backups

  # Export only a specific table
  python exporter.py --table players

  # Use larger batch size (faster, more memory)
  python exporter.py --batch-size 5000
        """
    )

    parser.add_argument(
        '--output',
        default=config.OUTPUT_DIR,
        help='Output directory (default: exports/)',
    )

    parser.add_argument(
        '--table',
        help='Export only specific table',
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=config.BATCH_SIZE,
        help=f'Rows per batch (default: {config.BATCH_SIZE})',
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output',
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'Nova Shots Database Exporter v{config.EXPORT_VERSION}',
    )

    args = parser.parse_args()

    # Update config with CLI args
    if args.batch_size != config.BATCH_SIZE:
        config.BATCH_SIZE = args.batch_size

    # Print header
    if not args.quiet:
        print()
        print(f"Nova Shots Database Exporter v{config.EXPORT_VERSION}")
        print("=" * 50)
        config.print_config_summary()

    # Validate configuration
    try:
        config.validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    # Export single table or all tables
    exporter = DatabaseExporter(output_base_dir=args.output)

    if args.table:
        # Single table export
        print(f"Exporting table: {args.table}\n")
        exporter.export_dir = create_export_directory(args.output)
        exporter.client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        success, rows = exporter.export_single_table(args.table)

        if success:
            print(f"\n✓ Exported {rows:,} rows to {exporter.export_dir}/{args.table}.json")
        else:
            print(f"\n✗ Failed to export {args.table}")
            sys.exit(1)
    else:
        # Full export
        export_path = exporter.export_all()

        if not args.quiet:
            print(f"\nExport saved to: {export_path}")


if __name__ == '__main__':
    main()
