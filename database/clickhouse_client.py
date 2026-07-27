import clickhouse_connect


class ClickHouseClient:

    def __init__(
        self,
        host,
        port,
        database,
        username=None,
        password=None
    ):

        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password
        )

    def get_client(self):
        return self.client