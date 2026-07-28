from typing import List, Dict, Any, Tuple


class NetworkEventAnalytics:
    """
    Analytics layer for business intelligence queries on network events

    This layer handles:
    - Aggregated analytics
    - Business reports
    - Performance metrics
    - Trend analysis
    """

    def __init__(self, client):
        self.client = client
        self.table_name = "network_events"

    # ============================================
    # APPLICATION ANALYTICS
    # ============================================

    def get_top_applications(self, limit: int = 10) -> List[Tuple[str, int, float, float]]:
        """
        Get top applications by event count with performance metrics

        Returns:
            List of (app_name, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                app_name,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            GROUP BY app_name
            ORDER BY event_count DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        result = self.client.query(query)
        return result.result_rows

    def get_app_performance(self, app_name: str) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific application

        Returns:
            Dict with performance metrics
        """
        query = """
            SELECT
                count() as total_events,
                avg(latency_ms) as avg_latency,
                min(latency_ms) as min_latency,
                max(latency_ms) as max_latency,
                avg(download_speed) as avg_speed,
                min(download_speed) as min_speed,
                max(download_speed) as max_speed,
                avg(packet_loss) as avg_packet_loss
            FROM {table}
            WHERE app_name = %(app_name)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"app_name": app_name}
        )

        row = result.result_rows[0]
        return {
            "total_events": row[0],
            "avg_latency_ms": row[1],
            "min_latency_ms": row[2],
            "max_latency_ms": row[3],
            "avg_speed_mbps": row[4],
            "min_speed_mbps": row[5],
            "max_speed_mbps": row[6],
            "avg_packet_loss_pct": row[7]
        }

    # ============================================
    # CITY ANALYTICS
    # ============================================

    def get_top_cities_by_traffic(self, limit: int = 10) -> List[Tuple[str, int, float, float]]:
        """
        Get top cities by traffic volume

        Returns:
            List of (city, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                city,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            GROUP BY city
            ORDER BY event_count DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        result = self.client.query(query)
        return result.result_rows

    def get_city_network_quality(self, city: str) -> Dict[str, Any]:
        """
        Get network quality metrics for a specific city

        Returns:
            Dict with network quality metrics
        """
        query = """
            SELECT
                count() as total_events,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed,
                avg(packet_loss) as avg_packet_loss,
                countIf(network_type = '5G') as _5g_count,
                countIf(network_type = '4G') as _4g_count
            FROM {table}
            WHERE city = %(city)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"city": city}
        )

        row = result.result_rows[0]
        total = row[0] or 1  # Avoid division by zero
        return {
            "total_events": row[0],
            "avg_latency_ms": row[1],
            "avg_speed_mbps": row[2],
            "avg_packet_loss_pct": row[3],
            "5g_percentage": (row[4] / total) * 100 if total > 0 else 0,
            "4g_percentage": (row[5] / total) * 100 if total > 0 else 0
        }

    # ============================================
    # NETWORK ANALYTICS
    # ============================================

    def get_network_quality_report(self) -> List[Tuple[str, int, float, float, float]]:
        """
        Get network quality report by network type

        Returns:
            List of (network_type, event_count, avg_latency, avg_speed, avg_packet_loss)
        """
        query = """
            SELECT
                network_type,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed,
                avg(packet_loss) as avg_packet_loss
            FROM {table}
            GROUP BY network_type
            ORDER BY network_type
        """.format(table=self.table_name)

        result = self.client.query(query)
        return result.result_rows

    def get_network_comparison(self) -> Dict[str, Any]:
        """
        Compare 4G vs 5G performance

        Returns:
            Dict with comparison metrics
        """
        query = """
            SELECT
                network_type,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed,
                avg(packet_loss) as avg_packet_loss,
                count() as total_events
            FROM {table}
            WHERE network_type IN ('4G', '5G')
            GROUP BY network_type
        """.format(table=self.table_name)

        result = self.client.query(query)

        comparison = {}
        for row in result.result_rows:
            comparison[row[0]] = {
                "avg_latency_ms": row[1],
                "avg_speed_mbps": row[2],
                "avg_packet_loss_pct": row[3],
                "total_events": row[4]
            }

        return comparison

    # ============================================
    # TIME SERIES ANALYTICS
    # ============================================

    def get_daily_events_report(self, days: int = 7) -> List[Tuple[str, int, float, float]]:
        """
        Get daily event counts and performance for last N days

        Returns:
            List of (date, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                toDate(event_time) as date,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            WHERE event_time >= now() - INTERVAL {days} DAY
            GROUP BY date
            ORDER BY date DESC
        """.format(table=self.table_name, days=days)

        result = self.client.query(query)
        return result.result_rows

    def get_hourly_heatmap(self) -> List[Tuple[int, int]]:
        """
        Get hourly distribution of events

        Returns:
            List of (hour, event_count)
        """
        query = """
            SELECT
                toHour(event_time) as hour,
                count() as event_count
            FROM {table}
            GROUP BY hour
            ORDER BY hour
        """.format(table=self.table_name)

        result = self.client.query(query)
        return result.result_rows

    def get_events_by_time_range(
            self,
            start_time: str,
            end_time: str
    ) -> List[Tuple[str, int, float, float]]:
        """
        Get events grouped by hour within a time range

        Returns:
            List of (hour, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                toStartOfHour(event_time) as hour,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            WHERE event_time BETWEEN %(start_time)s AND %(end_time)s
            GROUP BY hour
            ORDER BY hour
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={
                "start_time": start_time,
                "end_time": end_time
            }
        )
        return result.result_rows

    # ============================================
    # DEVICE ANALYTICS
    # ============================================

    def get_device_statistics(self) -> List[Tuple[str, int, float, float]]:
        """
        Get statistics by device type

        Returns:
            List of (device, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                device,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            GROUP BY device
            ORDER BY event_count DESC
        """.format(table=self.table_name)

        result = self.client.query(query)
        return result.result_rows

    def get_device_performance_ranking(self) -> List[Tuple[str, float, float, int]]:
        """
        Rank devices by performance (speed and latency)

        Returns:
            List of (device, avg_speed, avg_latency, event_count)
        """
        query = """
            SELECT
                device,
                avg(download_speed) as avg_speed,
                avg(latency_ms) as avg_latency,
                count() as event_count
            FROM {table}
            GROUP BY device
            HAVING event_count > 100
            ORDER BY avg_speed DESC, avg_latency ASC
        """.format(table=self.table_name)

        result = self.client.query(query)
        return result.result_rows

    # ============================================
    # USER ANALYTICS
    # ============================================

    def get_top_users_by_traffic(self, limit: int = 10) -> List[Tuple[int, int, float, float]]:
        """
        Get top users by traffic volume

        Returns:
            List of (user_id, event_count, avg_latency, avg_speed)
        """
        query = """
            SELECT
                user_id,
                count() as event_count,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed
            FROM {table}
            GROUP BY user_id
            ORDER BY event_count DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        result = self.client.query(query)
        return result.result_rows

    def get_user_activity_pattern(self, user_id: int) -> Dict[str, Any]:
        """
        Get activity pattern for a specific user

        Returns:
            Dict with user activity pattern
        """
        query = """
            SELECT
                count() as total_events,
                countDistinct(city) as cities_visited,
                countDistinct(app_name) as apps_used,
                avg(latency_ms) as avg_latency,
                avg(download_speed) as avg_speed,
                max(event_time) as last_active
            FROM {table}
            WHERE user_id = %(user_id)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"user_id": user_id}
        )

        row = result.result_rows[0]
        return {
            "total_events": row[0],
            "cities_visited": row[1],
            "apps_used": row[2],
            "avg_latency_ms": row[3],
            "avg_speed_mbps": row[4],
            "last_active": row[5]
        }

    # ============================================
    # EVENT TYPE ANALYTICS
    # ============================================

    def get_event_type_distribution(self) -> List[Tuple[str, int, float]]:
        """
        Get distribution of event types

        Returns:
            List of (event_type, count, percentage)
        """
        query = """
            SELECT
                event_type,
                count() as count,
                (count() * 100.0 / (SELECT count() FROM {table})) as percentage
            FROM {table}
            GROUP BY event_type
            ORDER BY count DESC
        """.format(table=self.table_name)

        result = self.client.query(query)
        return result.result_rows

    def get_event_type_trends(self, days: int = 7) -> List[Tuple[str, str, int]]:
        """
        Get event type trends over time

        Returns:
            List of (date, event_type, count)
        """
        query = """
            SELECT
                toDate(event_time) as date,
                event_type,
                count() as count
            FROM {table}
            WHERE event_time >= now() - INTERVAL {days} DAY
            GROUP BY date, event_type
            ORDER BY date DESC, count DESC
        """.format(table=self.table_name, days=days)

        result = self.client.query(query)
        return result.result_rows

    # ============================================
    # COMPOSITE REPORTS
    # ============================================

    def get_comprehensive_city_report(self, city: str) -> Dict[str, Any]:
        """
        Get comprehensive report for a city

        Returns:
            Dict with all city metrics
        """
        report = {
            "city": city,
            "overview": self.get_city_network_quality(city),
            "top_apps": self.client.query("""
                SELECT
                    app_name,
                    count() as event_count,
                    avg(latency_ms) as avg_latency
                FROM {table}
                WHERE city = %(city)s
                GROUP BY app_name
                ORDER BY event_count DESC
                LIMIT 5
            """.format(table=self.table_name), parameters={"city": city}).result_rows,
            "hourly_distribution": self.client.query("""
                SELECT
                    toHour(event_time) as hour,
                    count() as event_count
                FROM {table}
                WHERE city = %(city)s
                GROUP BY hour
                ORDER BY hour
            """.format(table=self.table_name), parameters={"city": city}).result_rows
        }

        return report

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get overall system performance metrics

        Returns:
            Dict with overall metrics
        """
        query = """
            SELECT
                count() as total_events,
                avg(latency_ms) as overall_avg_latency,
                avg(download_speed) as overall_avg_speed,
                avg(packet_loss) as overall_avg_packet_loss,
                countDistinct(user_id) as unique_users,
                countDistinct(city) as unique_cities,
                countDistinct(app_name) as unique_apps
            FROM {table}
        """.format(table=self.table_name)

        result = self.client.query(query)
        row = result.result_rows[0]

        return {
            "total_events": row[0],
            "overall_avg_latency_ms": row[1],
            "overall_avg_speed_mbps": row[2],
            "overall_avg_packet_loss_pct": row[3],
            "unique_users": row[4],
            "unique_cities": row[5],
            "unique_apps": row[6]
        }