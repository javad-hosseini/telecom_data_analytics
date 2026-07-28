import clickhouse_connect


class ClickHouseClient:
    def __init__(
            self,
            host: str,
            port: int,
            database: str,
            username: str = "default",
            password: str = "",
    ):
        self._client = clickhouse_connect.get_client(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )

    @property
    def client(self):
        return self._client
