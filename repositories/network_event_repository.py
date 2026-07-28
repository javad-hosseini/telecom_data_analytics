from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta


class NetworkEventRepository:
    """
    Repository for basic CRUD and retrieval operations on network_events table

    This layer handles:
    - Basic CRUD operations
    - Simple filters (by user, time, type)
    - Generic data access
    - Count operations
    """

    def __init__(self, client):
        self.client = client
        self.table_name = "network_events"

    # ============================================
    # CREATE OPERATIONS
    # ============================================

    def create(self, rows: List[List[Any]]) -> int:
        """
        Insert multiple rows into network_events table

        Args:
            rows: List of rows, each row is a list of values in correct order

        Returns:
            int: Number of rows inserted
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
        Insert multiple events from list of dictionaries

        Args:
            events: List of dicts with keys matching column names

        Returns:
            int: Number of rows inserted
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

    # ============================================
    # READ OPERATIONS
    # ============================================

    def get_all(self, limit: int = 100) -> List[List[Any]]:
        """
        Get all events with a limit

        Args:
            limit: Maximum number of rows to return

        Returns:
            List of rows
        """
        query = f"""
            SELECT *
            FROM {self.table_name}
            LIMIT {limit}
        """
        return self.client.query(query).result_rows

    def get_by_id(self, event_time: datetime, user_id: int) -> Optional[List[Any]]:
        """
        Get a specific event by primary key (event_time + user_id)

        Args:
            event_time: Timestamp of the event
            user_id: User identifier

        Returns:
            Single row or None
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
        """
        Get all events for a specific user

        Args:
            user_id: User identifier
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events by event type

        Args:
            event_type: Type of event (DATA_SESSION, CALL_START, etc.)
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events by city

        Args:
            city: City name
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events by network type (4G, 5G, etc.)

        Args:
            network_type: Network type
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events by application name

        Args:
            app_name: Application name
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events within a time range

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        """
        Get events for a specific user within a time range

        Args:
            user_id: User identifier
            start_time: Start timestamp
            end_time: End timestamp
            limit: Maximum number of rows

        Returns:
            List of rows
        """
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
        Get events with multiple optional filters

        Args:
            user_id: Filter by user
            event_type: Filter by event type
            city: Filter by city
            network_type: Filter by network type
            app_name: Filter by application
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of rows

        Returns:
            List of rows
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

    # ============================================
    # COUNT OPERATIONS
    # ============================================

    def count(self) -> int:
        """
        Get total number of events

        Returns:
            int: Total count
        """
        query = f"SELECT count() FROM {self.table_name}"
        result = self.client.query(query)
        return result.result_rows[0][0]

    def count_by_user(self, user_id: int) -> int:
        """
        Count events for a specific user

        Args:
            user_id: User identifier

        Returns:
            int: Number of events
        """
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
        """
        Count events by event type

        Args:
            event_type: Type of event

        Returns:
            int: Number of events
        """
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
        """
        Count events by city

        Args:
            city: City name

        Returns:
            int: Number of events
        """
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
        """
        Count events by network type

        Args:
            network_type: Network type

        Returns:
            int: Number of events
        """
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

    # ============================================
    # AGGREGATION OPERATIONS
    # ============================================

    def get_stats_by_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific user

        Args:
            user_id: User identifier

        Returns:
            Dict containing stats
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

    # ============================================
    # DELETE OPERATIONS
    # ============================================

    def delete_by_user(self, user_id: int) -> int:
        """
        Delete all events for a specific user

        Args:
            user_id: User identifier

        Returns:
            int: Number of rows deleted
        """
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
        """
        Delete events within a time range

        Args:
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            int: Number of rows deleted
        """
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
        """
        Delete events older than specified days

        Args:
            days: Number of days to keep

        Returns:
            int: Number of rows deleted
        """
        query = """
            DELETE FROM {table}
            WHERE event_time < now() - INTERVAL {days} DAY
        """.format(table=self.table_name, days=days)

        result = self.client.query(query)
        return result.result_rows[0][0] if result.result_rows else 0

    # ============================================
    # PAGINATION
    # ============================================

    def paginate(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get paginated results

        Args:
            page: Page number (starts from 1)
            per_page: Items per page

        Returns:
            Dict with items, total, page, per_page
        """
        offset = (page - 1) * per_page

        # Get items
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

        # Get total count
        total = self.count()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
        }

    # ============================================
    # UTILITY METHODS
    # ============================================

    def get_column_names(self) -> List[str]:
        """Get all column names of the table"""
        query = """
            SELECT name
            FROM system.columns
            WHERE database = currentDatabase()
            AND table = '{table}'
        """.format(table=self.table_name)

        result = self.client.query(query)
        return [row[0] for row in result.result_rows]

    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the table"""
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

    def get_sample(self, sample_size: int = 10) -> List[List[Any]]:
        """
        Get a random sample of events

        Args:
            sample_size: Number of random rows

        Returns:
            List of rows
        """
        query = """
            SELECT *
            FROM {table}
            ORDER BY rand()
            LIMIT {limit}
        """.format(table=self.table_name, limit=sample_size)

        return self.client.query(query).result_rows

    def get_distinct_values(self, column: str) -> List[str]:
        """
        Get all distinct values for a column

        Args:
            column: Column name

        Returns:
            List of distinct values
        """
        query = """
            SELECT DISTINCT {column}
            FROM {table}
            ORDER BY {column}
        """.format(table=self.table_name, column=column)

        result = self.client.query(query)
        return [row[0] for row in result.result_rows]

    def get_date_range(self) -> Dict[str, Optional[datetime]]:
        """
        Get min and max event_time in the table

        Returns:
            Dict with min_date and max_date
        """
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

    def get_latest(self, limit: int = 10) -> List[List[Any]]:
        """
        Get latest events

        Args:
            limit: Number of events to return

        Returns:
            List of rows
        """
        query = """
            SELECT *
            FROM {table}
            ORDER BY event_time DESC
            LIMIT {limit}
        """.format(table=self.table_name, limit=limit)

        return self.client.query(query).result_rows