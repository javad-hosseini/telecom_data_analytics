"""
Partition Manager for ClickHouse Tables

This module handles partition operations like:
- Creating partitioned tables
- Moving data to partitioned tables
- Dropping old partitions
- Showing partition information
- Merging partitions
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tabulate import tabulate


class PartitionManager:
    """
    Manages ClickHouse table partitions operations
    """

    def __init__(self, client):
        self.client = client
        self.database = "telecom_analytics"
        self.table_name = "network_events"
        self.partitioned_table_name = "network_events_partitioned"

    # ============================================
    # CREATE PARTITIONED TABLE
    # ============================================

    def create_partitioned_table(self, partition_by: str = "toYYYYMM(event_time)") -> bool:
        """
        Create a new table with partitioning

        Args:
            partition_by: Partition expression (default: toYYYYMM(event_time))

        Returns:
            bool: True if successful
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

    # ============================================
    # MIGRATE DATA
    # ============================================

    def migrate_to_partitioned(self) -> int:
        """
        Migrate data from original table to partitioned table

        Returns:
            int: Number of rows migrated
        """
        try:
            print("🔄 Migrating data to partitioned table...")

            # Check if partitioned table exists
            if not self._table_exists(self.partitioned_table_name):
                print("⚠️  Partitioned table does not exist. Creating...")
                self.create_partitioned_table()

            # Migrate data
            query = f"""
                INSERT INTO {self.partitioned_table_name}
                SELECT * FROM {self.table_name}
            """

            self.client.query(query)

            # Verify count
            result = self.client.query(f"""
                SELECT count() FROM {self.partitioned_table_name}
            """)
            count = result.result_rows[0][0]

            print(f"✅ Migrated {count:,} rows to '{self.partitioned_table_name}'")
            return count

        except Exception as err:
            print(f"❌ Migration failed: {err}")
            return 0

    # ============================================
    # REPLACE TABLE
    # ============================================

    def replace_with_partitioned(self, backup: bool = True) -> bool:
        """
        Replace original table with partitioned table

        Args:
            backup: If True, keep original table as backup

        Returns:
            bool: True if successful
        """
        try:
            if backup:
                # Rename original to backup
                backup_name = f"{self.table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.client.query(f"""
                    RENAME TABLE {self.table_name} TO {backup_name}
                """)
                print(f"✅ Original table backed up as '{backup_name}'")

            # Rename partitioned table to original
            self.client.query(f"""
                RENAME TABLE {self.partitioned_table_name} TO {self.table_name}
            """)

            print(f"✅ Table '{self.table_name}' is now partitioned!")
            return True

        except Exception as err:
            print(f"❌ Replace failed: {err}")
            return False

    # ============================================
    # SHOW PARTITIONS
    # ============================================

    def show_partitions(self, table: Optional[str] = None) -> None:
        """
        Display partition information for the table

        Args:
            table: Table name (default: self.table_name)
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

            # Summary
            total_rows = sum(row[2] for row in rows)
            print(f"\n📌 Total partitions: {len(rows)}")
            print(f"📌 Total rows: {total_rows:,}")

        except Exception as err:
            print(f"❌ Failed to get partitions: {err}")

    # ============================================
    # DROP PARTITION
    # ============================================

    def drop_partition(self, partition_value: str, table: Optional[str] = None) -> bool:
        """
        Drop a specific partition

        Args:
            partition_value: Partition value (e.g., '202401')
            table: Table name (default: self.table_name)

        Returns:
            bool: True if successful
        """
        table_name = table or self.table_name

        try:
            # Confirm before dropping
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

    # ============================================
    # DROP OLD PARTITIONS
    # ============================================

    def drop_partitions_older_than(self, months: int, table: Optional[str] = None) -> int:
        """
        Drop partitions older than specified months

        Args:
            months: Number of months to keep (e.g., 6 months)
            table: Table name (default: self.table_name)

        Returns:
            int: Number of partitions dropped
        """
        table_name = table or self.table_name

        try:
            # Get current date in YYYYMM format
            current_date = datetime.now()
            cutoff_date = current_date - timedelta(days=months * 30)
            cutoff_partition = cutoff_date.strftime("%Y%m")

            # Get list of partitions
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

            print(f"⚠️  Found {len(partitions)} partitions older than {months} months:")
            print(f"   {', '.join(partitions)}")

            confirm = input(f"⚠️  Drop all these partitions? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Operation cancelled")
                return 0

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

    # ============================================
    # MERGE PARTITIONS
    # ============================================

    def merge_partitions(self, partition_range: Optional[str] = None, table: Optional[str] = None) -> bool:
        """
        Merge partitions for optimization

        Args:
            partition_range: Partition range (e.g., '202401', '202402')
            table: Table name (default: self.table_name)

        Returns:
            bool: True if successful
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

    # ============================================
    # CHECK TABLE STATUS
    # ============================================

    def get_table_status(self) -> Dict[str, Any]:
        """
        Get status of both original and partitioned tables

        Returns:
            Dict with table status information
        """
        status = {
            "original": {},
            "partitioned": {},
            "partitioned_exists": False
        }

        try:
            # Check original table
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

        try:
            # Check partitioned table
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

    # ============================================
    # HELPER METHODS
    # ============================================

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
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