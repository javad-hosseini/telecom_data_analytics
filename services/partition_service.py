from typing import List, Dict, Any
from datetime import datetime
from repositories.network_event_repository import NetworkEventRepository


class PartitionService:
    """سرویس مدیریت پارتیشن‌ها"""

    def __init__(self, repository: NetworkEventRepository):
        self.repo = repository

    async def get_partition_status(self) -> List[Dict[str, Any]]:
        """دریافت وضعیت پارتیشن‌ها"""
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
        """حذف یک پارتیشن"""
        # اعتبارسنجی فرمت
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
        """پاکسازی پارتیشن‌های قدیمی"""
        # محاسبه تاریخ برش
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        cutoff_month = cutoff_date.strftime("%Y%m")

        partitions = await self.get_partition_status()
        dropped = []

        for partition in partitions:
            if partition["partition_name"] < cutoff_month:
                await self.drop_partition(partition["partition_name"])
                dropped.append(partition["partition_name"])

        return {
            "cutoff_month": cutoff_month,
            "dropped_partitions": dropped,
            "total_dropped": len(dropped)
        }
