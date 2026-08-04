# repositories/network_event_repository.py
# All database queries live here. This is where we actually talk to ClickHouse.

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta


class NetworkEventRepository:
    """
    Handles all CRUD operations for the network_events table.

    Think of this as the "data layer" - services call these methods
    to get or modify data without worrying about SQL details.
    """

    def __init__(self, client):
        self.client = client
        self.table_name = "network_events"

    # ------------------------------------------------------------------
    # Generic query execution - used by services for custom queries
    # ------------------------------------------------------------------

    def execute_query(self, query: str) -> List[Any]:
        """Run any SQL query and return the results. Used by service layer."""
        return self.client.query(query).result_rows

    # ------------------------------------------------------------------
    # Inserting data
    # ------------------------------------------------------------------

    def create(self, rows: List[List[Any]]) -> int:
        """
        Insert multiple rows into the table.

        Each row should be a list of values in the exact order of columns.
        Returns the number of rows inserted.
        """
        self.client.insert(
            self.table_name,
            rows,
            column_names=[
                "event_time",
                "user_id",
                "event_type",
                "country",
                "city",
                "device",
                "network_type",
                "app_name",
                "latency_ms",
                "download_speed",
                "packet_loss"
            ]
        )
        return len(rows)

    def create_from_dicts(self, events: List[Dict[str, Any]]) -> int:
        """
        Insert events from dictionaries.

        More convenient than create() - just pass a list of dicts
        with column names as keys.
        """
        if not events:
            return 0

        rows = []
        columns = [
            "event_time", "user_id", "event_type", "country", "city",
            "device", "network_type", "app_name", "latency_ms",
            "download_speed", "packet_loss"
        ]

        for event in events:
            row = [event.get(col) for col in columns]
            rows.append(row)

        return self.create(rows)

    # ------------------------------------------------------------------
    # Reading data - various ways to fetch events
    # ------------------------------------------------------------------

    def get_all(self, limit: int = 100) -> List[List[Any]]:
        """Get all events, but with a limit to avoid overload."""
        query = f"""
            SELECT *
            FROM {self.table_name}
            LIMIT {limit}
        """
        return self.client.query(query).result_rows

    def get_by_id(self, event_time: datetime, user_id: int) -> Optional[List[Any]]:
        """
        Fetch a specific event using its composite key.

        The primary key is (event_time, user_id) so we need both.
        """
        query = """
            SELECT *
            FROM {table}
            WHERE event_time = %(event_time)s 
            AND user_id = %(user_id)s
            LIMIT 1
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={
                "event_time": event_time,
                "user_id": user_id
            }
        )

        return result.result_rows[0] if result.result_rows else None

    def get_by_user_id(self, user_id: int, limit: int = 100) -> List[List[Any]]:
        """Get all events for a specific user, newest first."""
        query = """
            SELECT *
            FROM {table}
            WHERE user_id = %(user_id)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={"user_id": user_id}
        ).result_rows

    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[List[Any]]:
        """Get events of a specific type (like CALL_START, DATA_SESSION, etc.)."""
        query = """
            SELECT *
            FROM {table}
            WHERE event_type = %(event_type)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={"event_type": event_type}
        ).result_rows

    def get_by_city(self, city: str, limit: int = 100) -> List[List[Any]]:
        """Get events from a specific city."""
        query = """
            SELECT *
            FROM {table}
            WHERE city = %(city)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={"city": city}
        ).result_rows

    def get_by_network_type(self, network_type: str, limit: int = 100) -> List[List[Any]]:
        """Get events by network type - 4G, 5G, WiFi, etc."""
        query = """
            SELECT *
            FROM {table}
            WHERE network_type = %(network_type)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={"network_type": network_type}
        ).result_rows

    def get_by_app(self, app_name: str, limit: int = 100) -> List[List[Any]]:
        """Get events for a specific application (YouTube, Instagram, etc.)."""
        query = """
            SELECT *
            FROM {table}
            WHERE app_name = %(app_name)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={"app_name": app_name}
        ).result_rows

    def get_by_time_range(
            self,
            start_time: datetime,
            end_time: datetime,
            limit: int = 1000
    ) -> List[List[Any]]:
        """Get events between two timestamps."""
        query = """
            SELECT *
            FROM {table}
            WHERE event_time >= %(start_time)s
            AND event_time <= %(end_time)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={
                "start_time": start_time,
                "end_time": end_time
            }
        ).result_rows

    def get_by_user_and_time_range(
            self,
            user_id: int,
            start_time: datetime,
            end_time: datetime,
            limit: int = 1000
    ) -> List[List[Any]]:
        """Get events for a user within a specific time range."""
        query = """
            SELECT *
            FROM {table}
            WHERE user_id = %(user_id)s
            AND event_time >= %(start_time)s
            AND event_time <= %(end_time)s
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(
            query,
            parameters={
                "user_id": user_id,
                "start_time": start_time,
                "end_time": end_time
            }
        ).result_rows

    def get_with_filters(
            self,
            user_id: Optional[int] = None,
            event_type: Optional[str] = None,
            city: Optional[str] = None,
            network_type: Optional[str] = None,
            app_name: Optional[str] = None,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 100
    ) -> List[List[Any]]:
        """
        The Swiss Army knife of queries - apply any combination of filters.

        All parameters are optional. Only the ones you provide will be used.
        Great for building dynamic search/filter functionality.
        """
        conditions = []
        params = {}

        if user_id is not None:
            conditions.append("user_id = %(user_id)s")
            params["user_id"] = user_id

        if event_type is not None:
            conditions.append("event_type = %(event_type)s")
            params["event_type"] = event_type

        if city is not None:
            conditions.append("city = %(city)s")
            params["city"] = city

        if network_type is not None:
            conditions.append("network_type = %(network_type)s")
            params["network_type"] = network_type

        if app_name is not None:
            conditions.append("app_name = %(app_name)s")
            params["app_name"] = app_name

        if start_time is not None:
            conditions.append("event_time >= %(start_time)s")
            params["start_time"] = start_time

        if end_time is not None:
            conditions.append("event_time <= %(end_time)s")
            params["end_time"] = end_time

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = """
            SELECT *
            FROM {table}
            WHERE {where}
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(
            table=self.table_name,
            where=where_clause,
            limit=limit
        )

        return self.client.query(query, parameters=params).result_rows

    # ------------------------------------------------------------------
    # Counting - get row counts with various filters
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Total number of events in the table."""
        query = f"SELECT count() FROM {self.table_name}"
        result = self.client.query(query)
        return result.result_rows[0][0]

    def count_by_user(self, user_id: int) -> int:
        """How many events does a user have?"""
        query = """
            SELECT count()
            FROM {table}
            WHERE user_id = %(user_id)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"user_id": user_id}
        )
        return result.result_rows[0][0]

    def count_by_event_type(self, event_type: str) -> int:
        """How many events of a specific type?"""
        query = """
            SELECT count()
            FROM {table}
            WHERE event_type = %(event_type)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"event_type": event_type}
        )
        return result.result_rows[0][0]

    def count_by_city(self, city: str) -> int:
        """How many events from a specific city?"""
        query = """
            SELECT count()
            FROM {table}
            WHERE city = %(city)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"city": city}
        )
        return result.result_rows[0][0]

    def count_by_network_type(self, network_type: str) -> int:
        """How many events on a specific network type?"""
        query = """
            SELECT count()
            FROM {table}
            WHERE network_type = %(network_type)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"network_type": network_type}
        )
        return result.result_rows[0][0]

    def get_sample(self, sample_size: int = 10) -> List[List[Any]]:
        """Get a random sample of events. Great for quick exploration."""
        query = """
            SELECT *
            FROM {table}
            ORDER BY rand()
            LIMIT {limit}
        """.format(table=self.table_name, limit=sample_size)

        return self.client.query(query).result_rows

    def get_latest(self, limit: int = 10) -> List[List[Any]]:
        """Get the most recent events."""
        query = """
            SELECT *
            FROM {table}
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(query).result_rows

    # ------------------------------------------------------------------
    # Aggregations - summary statistics
    # ------------------------------------------------------------------

    def get_stats_by_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive stats for a user.

        Returns things like:
        - total events
        - average/min/max latency
        - average/min/max download speed
        - average packet loss
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
            WHERE user_id = %(user_id)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"user_id": user_id}
        )

        row = result.result_rows[0]
        return {
            "total_events": row[0],
            "avg_latency_ms": row[1],
            "min_latency_ms": row[2],
            "max_latency_ms": row[3],
            "avg_download_speed_mbps": row[4],
            "min_download_speed_mbps": row[5],
            "max_download_speed_mbps": row[6],
            "avg_packet_loss_pct": row[7]
        }

    # ------------------------------------------------------------------
    # Deleting data - be careful with these!
    # ------------------------------------------------------------------

    def delete_by_user(self, user_id: int) -> int:
        """Delete all events for a user. Returns number of rows deleted."""
        query = """
            DELETE FROM {table}
            WHERE user_id = %(user_id)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={"user_id": user_id}
        )
        return result.result_rows[0][0] if result.result_rows else 0

    def delete_by_time_range(self, start_time: datetime, end_time: datetime) -> int:
        """Delete events within a time range."""
        query = """
            DELETE FROM {table}
            WHERE event_time >= %(start_time)s
            AND event_time <= %(end_time)s
        """.format(table=self.table_name)

        result = self.client.query(
            query,
            parameters={
                "start_time": start_time,
                "end_time": end_time
            }
        )
        return result.result_rows[0][0] if result.result_rows else 0

    def delete_old_events(self, days: int = 30) -> int:
        """Delete events older than N days. Useful for data retention policies."""
        query = """
            DELETE FROM {table}
            WHERE event_time < now() - INTERVAL {days} DAY
        """.format(table=self.table_name, days=days)

        result = self.client.query(query)
        return result.result_rows[0][0] if result.result_rows else 0

    # ------------------------------------------------------------------
    # Pagination - for when you have lots of data
    # ------------------------------------------------------------------

    def paginate(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get a page of results.

        Page numbers start at 1.
        Returns items plus pagination metadata (total, total_pages, etc.).
        """
        offset = (page - 1) * per_page

        query = """
            SELECT *
            FROM {table}
            ORDER BY event_time DESC
            LIMIT {limit}
            OFFSET {offset}
        """.format(
            table=self.table_name,
            limit=per_page,
            offset=offset
        )

        items = self.client.query(query).result_rows
        total = self.count()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
        }

    # ------------------------------------------------------------------
    # Utility methods - helpful for debugging and exploration
    # ------------------------------------------------------------------

    def get_column_names(self) -> List[str]:
        """Get list of all column names in the table."""
        query = """
            SELECT name
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = '{table}'
        """.format(table=self.table_name)

        result = self.client.query(query)
        return [row[0] for row in result.result_rows]

    def get_table_info(self) -> Dict[str, Any]:
        """Get metadata about the table - name, engine, size, row count."""
        query = """
            SELECT
                name,
                engine,
                total_rows,
                total_bytes,
                formatReadableSize(total_bytes) as total_size
            FROM system.tables
            WHERE database = currentDatabase()
            AND name = '{table}'
        """.format(table=self.table_name)

        result = self.client.query(query)
        row = result.result_rows[0]

        return {
            "name": row[0],
            "engine": row[1],
            "total_rows": row[2],
            "total_bytes": row[3],
            "total_size_human": row[4]
        }

    def get_distinct_values(self, column: str) -> List[str]:
        """Get all unique values for a column. Useful for building dropdowns."""
        query = """
            SELECT DISTINCT {column}
            FROM {table}
            ORDER BY {column}
        """.format(table=self.table_name, column=column)

        result = self.client.query(query)
        return [row[0] for row in result.result_rows]

    def get_date_range(self) -> Dict[str, Optional[datetime]]:
        """Get the earliest and latest event timestamps in the table."""
        query = """
            SELECT
                min(event_time) as min_date,
                max(event_time) as max_date
            FROM {table}
        """.format(table=self.table_name)

        result = self.client.query(query)
        row = result.result_rows[0]

        return {
            "min_date": row[0],
            "max_date": row[1]
        }