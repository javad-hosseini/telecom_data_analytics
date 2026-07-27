import clickhouse_connect
from faker import Faker
import random
from datetime import datetime, timedelta


# config
HOST="192.168.247.128"
DATABASE="telecom_analytics"
NUMBER_OF_EVENTS = 1000


# to make sure that the data has been inserted successfully
# clickhouse-client
# USE <database_name>;
# SELECT count()
# FROM <table_name>;
# SELECT *
# FROM <table_name>
# LIMIT 5;


fake = Faker()


client = clickhouse_connect.get_client(
    host=HOST,
    port=8123,
    database=DATABASE
)


events = [
    "DATA_SESSION",
    "CALL_START",
    "CALL_END",
    "HANDOVER",
    "CONNECT"
]


cities = [
    "Tehran",
    "Mashhad",
    "Isfahan",
    "Shiraz",
    "Tabriz"
]


devices = [
    "Android",
    "iPhone"
]


networks = [
    "4G",
    "5G"
]


apps = [
    "YouTube",
    "Instagram",
    "Telegram",
    "WhatsApp"
]


rows = []


for _ in range(NUMBER_OF_EVENTS):

    row = [
        fake.date_time_between(
            start_date="-30d",
            end_date="now"
        ),

        random.randint(100000, 999999),

        random.choice(events),

        "Iran",

        random.choice(cities),

        random.choice(devices),

        random.choice(networks),

        random.choice(apps),

        random.randint(10, 200),

        round(random.uniform(1, 100), 2),

        round(random.uniform(0, 5), 2)
    ]

    rows.append(row)



client.insert(
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


print("Inserted:", len(rows))