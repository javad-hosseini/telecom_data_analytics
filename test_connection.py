import clickhouse_connect

# hostname -I
HOST = "192.168.247.128"


client = clickhouse_connect.get_client(
    host=HOST,
    port=8123
)


result = client.query(
    "SELECT version()"
)

# if it establishes a connection it will print the version
print(result.result_rows)