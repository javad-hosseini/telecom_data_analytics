# analytics/network_event_analytics.py
# Analytics queries specifically for the CLI.
# This is the CLI version of AnalyticsService - similar queries but returns tuples.

from typing import List, Dict, Any, Tuple


class NetworkEventAnalytics:
    """
    Analytics layer for the CLI interface.

    This is the CLI counterpart to the API's AnalyticsService.
    Returns data as tuples (not Pydantic models) since CLI doesn't need them.
    Used by main.py for all analytics commands.
    """

    def __init__(self, client):
        self.client = client
        self.table_name = "network_events"

    # ------------------------------------------------------------------
    # Application analytics - which apps are most used?
    # ------------------------------------------------------------------

    def get_top_applications(self, limit: int = 10) -> List[Tuple[str, int, float, float]]:
        """
        Get top apps by usage count with performance metrics.

        Returns tuples: (app_name, event_count, avg_latency, avg_speed)
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
        Get detailed performance metrics for a specific app.

        Returns a dict with everything about that app's performance.
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

    # ------------------------------------------------------------------
    # City analytics - where is the traffic coming from?
    # ------------------------------------------------------------------

    def get_top_cities_by_traffic(self, limit: int = 10) -> List[Tuple[str, int, float, float]]:
        """
        Get cities with the most traffic.

        Returns tuples: (city, event_count, avg_latency, avg_speed)
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
        Get network quality metrics for a specific city.

        Includes 5G and 4G penetration percentages.
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

    # ------------------------------------------------------------------
    # Network analytics - how do different networks perform?
    # ------------------------------------------------------------------

    def get_network_quality_report(self) -> List[Tuple[str, int, float, float, float]]:
        """
        Compare performance across different network types.

        Returns tuples: (network_type, event_count, avg_latency, avg_speed, avg_packet_loss)
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
        Direct comparison between 4G and 5G networks.

        Returns a dict with both networks' metrics for easy comparison.
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

    # ------------------------------------------------------------------
    # Time series analytics - trends over time
    # ------------------------------------------------------------------

    def get_daily_events_report(self, days: int = 7) -> List[Tuple[str, int, float, float]]:
        """
        Daily breakdown of events and performance for the last N days.

        Returns tuples: (date, event_count, avg_latency, avg_speed)
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
        Get hourly event distribution (0-23 hours).

        Returns tuples: (hour, event_count)
        Useful for finding peak usage times.
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
        Get events grouped by hour within a specific time range.

        Returns tuples: (hour, event_count, avg_latency, avg_speed)
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

    # ------------------------------------------------------------------
    # Device analytics - which devices perform best?
    # ------------------------------------------------------------------

    def get_device_statistics(self) -> List[Tuple[str, int, float, float]]:
        """
        Get device usage and performance statistics.

        Returns tuples: (device, event_count, avg_latency, avg_speed)
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
        Rank devices by speed (best performers first).

        Only includes devices with more than 100 events for statistical significance.
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

    # ------------------------------------------------------------------
    # User analytics - who are the heavy users?
    # ------------------------------------------------------------------

    def get_top_users_by_traffic(self, limit: int = 10) -> List[Tuple[int, int, float, float]]:
        """
        Find users with the most events.

        Returns tuples: (user_id, event_count, avg_latency, avg_speed)
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
        Get comprehensive activity pattern for a specific user.

        Shows how many cities they've been to, apps they use, etc.
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

    # ------------------------------------------------------------------
    # Event type analytics - what types of events happen most?
    # ------------------------------------------------------------------

    def get_event_type_distribution(self) -> List[Tuple[str, int, float]]:
        """
        Get distribution of event types with percentages.

        Returns tuples: (event_type, count, percentage_of_total)
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
        See how different event types trend over time.

        Returns tuples: (date, event_type, count)
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

    # ------------------------------------------------------------------
    # Composite reports - everything in one place
    # ------------------------------------------------------------------

    def get_comprehensive_city_report(self, city: str) -> Dict[str, Any]:
        """
        Get everything about a city in one report.

        Includes: overview, top apps, and hourly distribution.
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
        Get overall system performance metrics.

        The big picture: total events, avg latency, unique users, etc.
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
