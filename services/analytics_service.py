from typing import List, Dict, Any
from core.interfaces.services import IAnalyticsService
from repositories.network_event_repository import NetworkEventRepository


class AnalyticsService(IAnalyticsService):
    """سرویس تحلیل‌های آماری"""

    def __init__(self, repository: NetworkEventRepository):
        self.repo = repository

    async def get_top_apps(self, limit: int = 10) -> List[Dict]:
        """دریافت اپلیکیشن‌های پرمصرف"""
        query = f"""
            SELECT 
                app_name, 
                count() as event_count
            FROM network_events
            GROUP BY app_name
            ORDER BY event_count DESC
            LIMIT {limit}
        """
        result = self.repo.execute_query(query)
        return [
            {"app_name": row[0], "event_count": row[1]}
            for row in result
        ]

    async def get_network_quality(self) -> List[Dict]:
        """گزارش کیفیت شبکه"""
        query = """
            SELECT 
                network_type,
                avg(latency_ms) as avg_latency,
                avg(packet_loss) as avg_packet_loss,
                avg(download_speed) as avg_speed,
                count() as total_events
            FROM network_events
            GROUP BY network_type
            ORDER BY avg_latency ASC
        """
        result = self.repo.execute_query(query)
        return [
            {
                "network_type": row[0],
                "avg_latency": float(row[1]),
                "avg_packet_loss": float(row[2]),
                "avg_speed": float(row[3]),
                "total_events": row[4]
            }
            for row in result
        ]

    async def get_hourly_heatmap(self, days: int = 7) -> List[Dict]:
        """توزیع ساعتی رویدادها"""
        query = f"""
            SELECT 
                toHour(event_time) as hour,
                count() as event_count
            FROM network_events
            WHERE event_time >= now() - INTERVAL {days} DAY
            GROUP BY hour
            ORDER BY hour
        """
        result = self.repo.execute_query(query)
        return [
            {"hour": row[0], "event_count": row[1]}
            for row in result
        ]

    async def get_device_stats(self) -> List[Dict]:
        """آمار دستگاه‌ها"""
        query = """
            SELECT 
                device,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM network_events
            GROUP BY device
            ORDER BY event_count DESC
            LIMIT 20
        """
        result = self.repo.execute_query(query)
        return [
            {
                "device": row[0],
                "event_count": row[1],
                "avg_latency": float(row[2]),
                "avg_speed": float(row[3])
            }
            for row in result
        ]

    async def get_city_stats(self, limit: int = 10) -> List[Dict]:
        """آمار شهرها"""
        query = f"""
            SELECT 
                city,
                count() as event_count,
                count(DISTINCT user_id) as unique_users,
                avg(latency_ms) as avg_latency
            FROM network_events
            GROUP BY city
            ORDER BY event_count DESC
            LIMIT {limit}
        """
        result = self.repo.execute_query(query)
        return [
            {
                "city": row[0],
                "event_count": row[1],
                "unique_users": row[2],
                "avg_latency": float(row[3])
            }
            for row in result
        ]
