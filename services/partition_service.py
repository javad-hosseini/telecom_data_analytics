# services/partition_service.py
# Manages table partitions - checking status, dropping old ones, cleaning up.
# Partitions help keep the database fast by splitting data by month.

from datetime import datetime, timedelta
from typing import List, Dict, Any

from repositories.network_event_repository import NetworkEventRepository


class PartitionService:
    """
    Handles all partition-related operations.

    Partitions in ClickHouse are like monthly folders for your data.
    This service helps you see what partitions exist and clean up old ones.
    """

    def __init__(self, repository: NetworkEventRepository):
        self.repo = repository

    async def get_partition_status(self) -> List[Dict[str, Any]]:
        """
        Get detailed info about all active partitions.

        Shows:
        - Partition name (like 202401 for January 2024)
        - How many rows it contains
        - Size on disk (both bytes and human-readable)
        - Date range of events in that partition
        """
        query = """
            SELECT 
                partition,
                count() as row_count,
                sum(bytes) as size_bytes,
                min(event_time) as min_date,
                max(event_time) as max_date
            FROM system.parts
            WHERE database = 'telecom_analytics'
            AND table = 'network_events'
            AND active = 1
            GROUP BY partition
            ORDER BY partition
        """
        result = self.repo.execute_query(query)

        # Helper function to make file sizes readable
        def format_size(bytes_val):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.2f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.2f} TB"

        return [
            {
                "partition_name": row[0],
                "row_count": row[1],
                "size_bytes": row[2],
                "size_human": format_size(row[2]),
                "min_date": row[3],
                "max_date": row[4]
            }
            for row in result
        ]

    async def drop_partition(self, year_month: str) -> Dict[str, Any]:
        """
        Delete a specific partition.

        WARNING: This permanently deletes all data in that partition!
        Only use this if you're sure you want to remove that month's data.

        The format must be YYYYMM (e.g., '202401' for January 2024).
        """
        # Make sure the format is correct before doing anything
        if not (len(year_month) == 6 and year_month.isdigit()):
            raise ValueError("Invalid partition format. Use YYYYMM")

        query = f"ALTER TABLE network_events DROP PARTITION {year_month}"
        self.repo.execute_query(query)

        return {
            "partition": year_month,
            "status": "dropped",
            "message": f"Partition {year_month} dropped successfully"
        }

    async def clean_old_partitions(self, months: int) -> Dict[str, Any]:
        """
        Automatically delete partitions older than N months.

        This is useful for data retention policies - keep only recent data
        and automatically clean up old stuff to save storage.

        For example: clean_old_partitions(6) keeps 6 months of data
        and deletes everything older than that.
        """
        # Calculate the cutoff date (e.g., 6 months ago from today)
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        cutoff_month = cutoff_date.strftime("%Y%m")

        # Get all partitions and figure out which ones are old
        partitions = await self.get_partition_status()
        dropped = []

        for partition in partitions:
            # If the partition name is smaller than cutoff, it's older
            if partition["partition_name"] < cutoff_month:
                await self.drop_partition(partition["partition_name"])
                dropped.append(partition["partition_name"])

        return {
            "cutoff_month": cutoff_month,
            "dropped_partitions": dropped,
            "total_dropped": len(dropped)
        }
