# partition_manager/partition_manager.py
# Manages ClickHouse table partitions - create, migrate, drop, and optimize.
# Used by the CLI for partition operations.

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from tabulate import tabulate


class PartitionManager:
    """
    Handles all partition operations for the network_events table.

    Partitions in ClickHouse are like monthly folders for your data.
    This class helps you create, manage, and clean up these partitions.
    """

    def __init__(self, client):
        self.client = client
        self.database = "telecom_analytics"
        self.table_name = "network_events"
        self.partitioned_table_name = "network_events_partitioned"

    # ------------------------------------------------------------------
    # Create a new table with partitioning
    # ------------------------------------------------------------------

    def create_partitioned_table(self, partition_by: str = "toYYYYMM(event_time)") -> bool:
        """
        Creates a new table with monthly partitioning.

        The new table has the same structure as the original but with
        partitions based on the event_time column.

        Args:
            partition_by: How to partition (default: by month)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = f"""
                CREATE TABLE IF NOT EXISTS {self.partitioned_table_name} (
                    event_time DateTime,
                    user_id UInt64,
                    event_type String,
                    country String,
                    city String,
                    device String,
                    network_type String,
                    app_name String,
                    latency_ms UInt16,
                    download_speed Float32,
                    packet_loss Float32
                )
                ENGINE = MergeTree()
                PARTITION BY {partition_by}
                ORDER BY (event_time, user_id)
                SETTINGS index_granularity = 8192
            """

            self.client.query(query)
            print(f"✅ Partitioned table '{self.partitioned_table_name}' created successfully!")
            return True

        except Exception as err:
            print(f"❌ Failed to create partitioned table: {err}")
            return False

    # ------------------------------------------------------------------
    # Move data to the partitioned table
    # ------------------------------------------------------------------

    def migrate_to_partitioned(self) -> int:
        """
        Copies all data from the original table to the partitioned one.

        First checks if the partitioned table exists, creates it if needed.
        Returns the number of rows migrated.

        Returns:
            Number of rows migrated, 0 if failed
        """
        try:
            print("🔄 Migrating data to partitioned table...")

            # Make sure the destination table exists
            if not self._table_exists(self.partitioned_table_name):
                print("⚠️  Partitioned table does not exist. Creating...")
                self.create_partitioned_table()

            # Copy all data from original to partitioned
            query = f"""
                INSERT INTO {self.partitioned_table_name}
                SELECT * FROM {self.table_name}
            """

            self.client.query(query)

            # Verify the migration worked
            result = self.client.query(f"""
                SELECT count() FROM {self.partitioned_table_name}
            """)
            count = result.result_rows[0][0]

            print(f"✅ Migrated {count:,} rows to '{self.partitioned_table_name}'")
            return count

        except Exception as err:
            print(f"❌ Migration failed: {err}")
            return 0

    # ------------------------------------------------------------------
    # Replace the original table with the partitioned one
    # ------------------------------------------------------------------

    def replace_with_partitioned(self, backup: bool = True) -> bool:
        """
        Swaps the partitioned table with the original one.

        Optionally keeps the original as backup with a timestamp name.

        Args:
            backup: If True, keep original as backup

        Returns:
            True if successful, False otherwise
        """
        try:
            if backup:
                # Rename original to something like network_events_backup_20260101_120000
                backup_name = f"{self.table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.client.query(f"""
                    RENAME TABLE {self.table_name} TO {backup_name}
                """)
                print(f"✅ Original table backed up as '{backup_name}'")

            # Rename partitioned table to the original name
            self.client.query(f"""
                RENAME TABLE {self.partitioned_table_name} TO {self.table_name}
            """)

            print(f"✅ Table '{self.table_name}' is now partitioned!")
            return True

        except Exception as err:
            print(f"❌ Replace failed: {err}")
            return False

    # ------------------------------------------------------------------
    # Show partition information
    # ------------------------------------------------------------------

    def show_partitions(self, table: Optional[str] = None) -> None:
        """
        Displays all active partitions for a table with size and row count.

        Shows a nice table with:
        - Partition name (like 202401)
        - Part name (internal name)
        - Number of rows
        - Size on disk
        - Last modified time

        Args:
            table: Table name (uses default if not provided)
        """
        table_name = table or self.table_name

        try:
            query = f"""
                SELECT
                    partition,
                    name as part_name,
                    rows,
                    formatReadableSize(bytes_on_disk) as size,
                    modification_time
                FROM system.parts
                WHERE database = '{self.database}'
                AND table = '{table_name}'
                AND active = 1
                ORDER BY partition
            """

            result = self.client.query(query)
            rows = result.result_rows

            if not rows:
                print(f"⚠️  No partitions found for table '{table_name}'")
                return

            headers = ["Partition", "Part Name", "Rows", "Size", "Modified"]
            print(f"\n📊 Partitions for '{table_name}':")
            print(tabulate(rows, headers=headers, tablefmt="grid"))

            # Show summary stats
            total_rows = sum(row[2] for row in rows)
            print(f"\n📌 Total partitions: {len(rows)}")
            print(f"📌 Total rows: {total_rows:,}")

        except Exception as err:
            print(f"❌ Failed to get partitions: {err}")

    # ------------------------------------------------------------------
    # Delete a specific partition
    # ------------------------------------------------------------------

    def drop_partition(self, partition_value: str, table: Optional[str] = None) -> bool:
        """
        Permanently deletes a specific partition.

        WARNING: This cannot be undone!

        Args:
            partition_value: Partition to delete (e.g., '202401')
            table: Table name (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        table_name = table or self.table_name

        try:
            # Safety check - ask for confirmation
            confirm = input(f"⚠️  Are you sure you want to drop partition '{partition_value}'? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Operation cancelled")
                return False

            self.client.query(f"""
                ALTER TABLE {table_name}
                DROP PARTITION '{partition_value}'
            """)

            print(f"✅ Partition '{partition_value}' dropped successfully!")
            return True

        except Exception as err:
            print(f"❌ Failed to drop partition: {err}")
            return False

    # ------------------------------------------------------------------
    # Delete partitions older than N months
    # ------------------------------------------------------------------

    def drop_partitions_older_than(self, months: int, table: Optional[str] = None) -> int:
        """
        Automatically finds and deletes partitions older than N months.

        Useful for data retention policies - keep only recent data.

        Args:
            months: How many months of data to keep
            table: Table name (uses default if not provided)

        Returns:
            Number of partitions dropped
        """
        table_name = table or self.table_name

        try:
            # Calculate cutoff (e.g., 6 months ago from today)
            current_date = datetime.now()
            cutoff_date = current_date - timedelta(days=months * 30)
            cutoff_partition = cutoff_date.strftime("%Y%m")

            # Find all partitions older than cutoff
            result = self.client.query(f"""
                SELECT DISTINCT partition
                FROM system.parts
                WHERE database = '{self.database}'
                AND table = '{table_name}'
                AND active = 1
                AND partition < '{cutoff_partition}'
                ORDER BY partition
            """)

            partitions = [row[0] for row in result.result_rows]

            if not partitions:
                print(f"✅ No partitions older than {months} months")
                return 0

            # Show what we found and ask for confirmation
            print(f"⚠️  Found {len(partitions)} partitions older than {months} months:")
            print(f"   {', '.join(partitions)}")

            confirm = input(f"⚠️  Drop all these partitions? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Operation cancelled")
                return 0

            # Drop each partition one by one
            dropped = 0
            for partition in partitions:
                try:
                    self.client.query(f"""
                        ALTER TABLE {table_name}
                        DROP PARTITION '{partition}'
                    """)
                    dropped += 1
                    print(f"   ✅ Dropped partition: {partition}")
                except Exception as err:
                    print(f"   ❌ Failed to drop {partition}: {err}")

            print(f"✅ Dropped {dropped} partitions")
            return dropped

        except Exception as err:
            print(f"❌ Failed to drop old partitions: {err}")
            return 0

    # ------------------------------------------------------------------
    # Optimize table by merging partitions
    # ------------------------------------------------------------------

    def merge_partitions(self, partition_range: Optional[str] = None, table: Optional[str] = None) -> bool:
        """
        Optimizes the table by merging small parts into larger ones.

        Can optimize the whole table or a specific partition range.
        This improves query performance.

        Args:
            partition_range: Optional range (e.g., '202401', '202402')
            table: Table name (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        table_name = table or self.table_name

        try:
            if partition_range:
                query = f"""
                    OPTIMIZE TABLE {table_name}
                    PARTITION {partition_range}
                """
            else:
                query = f"""
                    OPTIMIZE TABLE {table_name}
                """

            self.client.query(query)
            print(f"✅ Table '{table_name}' optimized successfully!")
            return True

        except Exception as err:
            print(f"❌ Optimization failed: {err}")
            return False

    # ------------------------------------------------------------------
    # Get status of both original and partitioned tables
    # ------------------------------------------------------------------

    def get_table_status(self) -> Dict[str, Any]:
        """
        Checks both the original and partitioned tables and returns their status.

        Useful for seeing if migration was successful and what the current state is.

        Returns:
            Dict with information about both tables
        """
        status = {
            "original": {},
            "partitioned": {},
            "partitioned_exists": False
        }

        # Check original table
        try:
            result = self.client.query(f"""
                SELECT 
                    name,
                    engine,
                    total_rows,
                    formatReadableSize(total_bytes) as size
                FROM system.tables
                WHERE database = '{self.database}'
                AND name = '{self.table_name}'
            """)

            if result.result_rows:
                row = result.result_rows[0]
                status["original"] = {
                    "name": row[0],
                    "engine": row[1],
                    "rows": row[2],
                    "size": row[3]
                }
        except:
            pass

        # Check partitioned table
        try:
            result = self.client.query(f"""
                SELECT 
                    name,
                    engine,
                    total_rows,
                    formatReadableSize(total_bytes) as size
                FROM system.tables
                WHERE database = '{self.database}'
                AND name = '{self.partitioned_table_name}'
            """)

            if result.result_rows:
                row = result.result_rows[0]
                status["partitioned"] = {
                    "name": row[0],
                    "engine": row[1],
                    "rows": row[2],
                    "size": row[3]
                }
                status["partitioned_exists"] = True
        except:
            pass

        return status

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            result = self.client.query(f"""
                SELECT count()
                FROM system.tables
                WHERE database = '{self.database}'
                AND name = '{table_name}'
            """)
            return result.result_rows[0][0] > 0
        except:
            return False
