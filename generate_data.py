import clickhouse_connect
from faker import Faker
import random
from datetime import datetime, timedelta
import time
import calendar

# ============================================
# CONFIG
# ============================================
HOST = "192.168.247.128"
DATABASE = "telecom_analytics"
BATCH_SIZE = 50000  # Records per batch
TOTAL_RECORDS = 90_000  # number of records

# ============================================
# DATA POOLS
# ============================================

# Event Types (more realistic)
EVENTS = [
    "DATA_SESSION_START",
    "DATA_SESSION_END",
    "CALL_START",
    "CALL_END",
    "HANDOVER",
    "CONNECT",
    "DISCONNECT",
    "SMS_SEND",
    "SMS_RECEIVE",
    "MMS_SEND",
    "MMS_RECEIVE",
    "VOIP_CALL_START",
    "VOIP_CALL_END",
    "VIDEO_CALL_START",
    "VIDEO_CALL_END",
    "GAME_SESSION_START",
    "GAME_SESSION_END",
]

# Cities (15 major Iranian cities with population-based distribution)
CITIES = [
    "Tehran",  # Capital
    "Mashhad",  # Second largest
    "Isfahan",  # Third largest
    "Karaj",  # Alborz
    "Shiraz",  # Fars
    "Tabriz",  # East Azerbaijan
    "Ahvaz",  # Khuzestan
    "Qom",  # Qom
    "Kermanshah",  # Kermanshah
    "Rasht",  # Gilan
    "Zahedan",  # Sistan and Baluchestan
    "Hamadan",  # Hamedan
    "Yazd",  # Yazd
    "Ardabil",  # Ardabil
    "Bandar_Abbas",  # Hormozgan
]

# Devices (Mobile + Desktop)
DEVICES = [
    # Android (10)
    "Android_Samsung_Galaxy", "Android_Samsung_A", "Android_Xiaomi",
    "Android_Huawei", "Android_OnePlus", "Android_Google_Pixel",
    "Android_Nokia", "Android_LG", "Android_Sony", "Android_Realme",
    # iPhone (7)
    "iPhone_14", "iPhone_15", "iPhone_16", "iPhone_Pro",
    "iPhone_SE", "iPhone_12", "iPhone_13",
    # iPhone Pro Max (1)
    "iPhone_Pro_Max",
    # Desktop (6)
    "Windows_PC", "Windows_Laptop", "MacBook", "MacMini",
    "Linux_Desktop", "Linux_Laptop",
]

# Network Types (more realistic)
NETWORKS = [
    "2G",  # Oldest
    "3G",  # Third generation
    "3G_HSDPA",  # Advanced 3G
    "3G_HSPA",  # Advanced 3G
    "3G_HSPA+",  # More advanced 3G
    "4G_LTE",  # Fourth generation
    "4G_LTE-A",  # Advanced 4G
    "5G",  # Fifth generation
    "5G_NSA",  # 5G Non-Standalone
    "5G_SA",  # 5G Standalone
    "WiFi",  # WiFi connection
]

# Apps (International + Iranian)
APPS = [
    # International (28)
    "YouTube", "Instagram", "Telegram", "WhatsApp", "Facebook",
    "Twitter_X", "TikTok", "Snapchat", "Spotify", "Netflix",
    "YouTube_Music", "Google", "Google_Maps", "Gmail", "Chrome",
    "Edge", "Firefox", "Zoom", "Discord", "Reddit",
    "LinkedIn", "GitHub", "Stack_Overflow", "Amazon", "AliExpress",
    "eBay", "Booking", "Uber",
    # Iranian (14)
    "Soroush", "Eitaa", "Bale", "Rubika", "Divar",
    "Digikala", "Snapp", "Tapsi", "Namava", "Filimo",
    "Alibaba_Travel", "Torob", "Telewebion", "Sheypoor",
]

# ============================================
# INITIALIZE
# ============================================
fake = Faker()
fake.seed_instance(42)  # For reproducibility

client = clickhouse_connect.get_client(
    host=HOST,
    port=8123,
    database=DATABASE,
    username="default",
    password=""
)


# ============================================
# GENERATION FUNCTIONS
# ============================================

def generate_batch(batch_size: int, start_date: datetime) -> list:
    """
    Generate a batch of telecom event records

    Args:
        batch_size: Number of records to generate
        start_date: Reference date for time generation

    Returns:
        List of record rows
    """
    rows = []

    # Real-world hourly traffic weights
    hour_weights = [
        0.3, 0.3, 0.3, 0.3, 0.3, 0.3,  # 00-05: Very low (sleeping)
        1.5, 1.5,  # 06-07: Morning wake-up
        2.5, 2.5,  # 08-09: Commuting (high)
        2.0, 2.0, 2.0,  # 10-12: Morning work
        1.8, 1.8,  # 13-14: Lunch break
        2.2, 2.2,  # 15-16: Afternoon work
        3.0, 3.0,  # 17-18: Evening peak (highest)
        2.5, 2.5, 2.5,  # 19-21: Evening leisure
        1.0, 1.0,  # 22-23: Late night
    ]

    hours = list(range(24))

    # Population distribution weights for cities (Tehran has highest weight)
    city_weights = [30, 15, 12, 10, 8, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1]

    # Network distribution (5G less, 4G more, 3G medium, 2G low)
    network_weights = [2, 8, 12, 15, 10, 20, 15, 10, 5, 2, 1]  # Matches NETWORKS order

    # Device distribution (Android most, iPhone medium, Desktop low)
    device_weights = [
        # Android (10)
        15, 12, 10, 8, 6, 5, 4, 3, 2, 1,
        # iPhone (7)
        8, 7, 6, 5, 4, 3, 2,
        # iPhone Pro Max (1)
        1,
        # Desktop (6)
        0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    ]

    for _ in range(batch_size):
        hour = random.choices(hours, weights=hour_weights, k=1)[0]

        event_time = start_date + timedelta(
            days=random.randint(0, 365),
            hours=hour,
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )

        row = [
            event_time,
            random.randint(100000, 999999),  # user_id
            random.choice(EVENTS),
            "Iran",
            random.choices(CITIES, weights=city_weights, k=1)[0],
            random.choices(DEVICES, weights=device_weights, k=1)[0],
            random.choices(NETWORKS, weights=network_weights, k=1)[0],
            random.choice(APPS),
            random.randint(5, 500),  # latency_ms (5 to 500 ms)
            round(random.uniform(0.5, 150), 2),  # download_speed (0.5 to 150 Mbps)
            round(random.uniform(0, 10), 2),  # packet_loss (0 to 10%)
        ]
        rows.append(row)

    return rows


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """
    Main execution function to generate and insert telecom events
    """
    print("=" * 70)
    print(f"📊 Generating {TOTAL_RECORDS:,} telecom events...")
    print("=" * 70)

    start_time = time.time()
    total_inserted = 0
    batch_count = 0

    # Reference date: one year ago from today
    start_date = datetime.now() - timedelta(days=365)

    while total_inserted < TOTAL_RECORDS:
        batch_count += 1
        remaining = TOTAL_RECORDS - total_inserted
        current_batch_size = min(BATCH_SIZE, remaining)

        # Generate a batch of records
        rows = generate_batch(current_batch_size, start_date)

        # Insert into ClickHouse
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

        total_inserted += len(rows)

        # Display progress
        progress = (total_inserted / TOTAL_RECORDS) * 100
        elapsed = time.time() - start_time
        speed = total_inserted / elapsed if elapsed > 0 else 0

        print(f"📦 Batch {batch_count}: Inserted {len(rows):,} rows "
              f"| Total: {total_inserted:,} ({progress:.1f}%) "
              f"| Speed: {speed:.0f} rows/sec")

    # ============================================
    # FINAL RESULTS
    # ============================================
    elapsed_total = time.time() - start_time
    print("=" * 70)
    print("✅ DONE!")
    print(f"📊 Total inserted: {total_inserted:,} rows")
    print(f"⏱️  Total time: {elapsed_total:.2f} seconds")
    print(f"🚀 Average speed: {total_inserted / elapsed_total:.0f} rows/sec")
    print("=" * 70)

    # Verify insertion
    result = client.query("SELECT count() FROM network_events")
    count = result.result_rows[0][0]
    print(f"✅ Verification: {count:,} rows in ClickHouse")


if __name__ == "__main__":
    main()