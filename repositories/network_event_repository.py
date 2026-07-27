class NetworkEventRepository:

    def __init__(self, client):
        self.client = client


    def get_all(self, limit=100):
        return self.client.query(
            f"""
            SELECT *
            FROM network_events
            LIMIT {limit}
            """
        ).result_rows


    def get_by_user_id(self, user_id):
        return self.client.query(
            """
            SELECT *
            FROM network_events
            WHERE user_id = %(user_id)s
            """,
            parameters={
                "user_id": user_id
            }
        ).result_rows


    def count(self):
        result = self.client.query(
            """
            SELECT count()
            FROM network_events
            """
        )

        return result.result_rows[0][0]


    def get_latest(self, limit=10):
        return self.client.query(
            f"""
            SELECT *
            FROM network_events
            ORDER BY event_time DESC
            LIMIT {limit}
            """
        ).result_rows


    def create(self, rows):
        self.client.insert(
            "network_events",
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