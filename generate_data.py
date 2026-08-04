# generate_data.py
# Generates synthetic telecom data for testing and development.
# Creates realistic-looking data with weighted distributions.

import random
import time
from datetime import datetime, timedelta

import clickhouse_connect
from faker import Faker

# ============================================
# CONFIGURATION - Change these to adjust data generation
# ============================================

HOST = "192.168.247.128"
DATABASE = "telecom_analytics"
BATCH_SIZE = 50_000  # Records per batch
TOTAL_RECORDS = 900_000  # Total records to generate

# ============================================
# DATA POOLS
# ============================================

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

# Cities with base weights (will be randomized each run)
CITIES = [
    "Tehran",
    "Mashhad",
    "Isfahan",
    "Karaj",
    "Shiraz",
    "Tabriz",
    "Ahvaz",
    "Qom",
    "Kermanshah",
    "Rasht",
    "Zahedan",
    "Hamadan",
    "Yazd",
    "Ardabil",
    "Bandar_Abbas",
]

DEVICES = [
    "Android_Samsung_Galaxy",
    "Android_Samsung_A",
    "Android_Xiaomi",
    "Android_Huawei",
    "Android_OnePlus",
    "Android_Google_Pixel",
    "Android_Nokia",
    "Android_LG",
    "Android_Sony",
    "Android_Realme",
    "iPhone_14",
    "iPhone_15",
    "iPhone_16",
    "iPhone_Pro",
    "iPhone_SE",
    "iPhone_12",
    "iPhone_13",
    "iPhone_Pro_Max",
    "Windows_PC",
    "Windows_Laptop",
    "MacBook",
    "MacMini",
    "Linux_Desktop",
    "Linux_Laptop",
]

NETWORKS = [
    "2G",
    "3G",
    "3G_HSDPA",
    "3G_HSPA",
    "3G_HSPA+",
    "4G_LTE",
    "4G_LTE-A",
    "5G",
    "5G_NSA",
    "5G_SA",
    "WiFi",
]

APPS = [
    "YouTube",
    "Instagram",
    "Telegram",
    "WhatsApp",
    "Facebook",
    "Twitter_X",
    "TikTok",
    "Snapchat",
    "Spotify",
    "Netflix",
    "YouTube_Music",
    "Google",
    "Google_Maps",
    "Gmail",
    "Chrome",
    "Edge",
    "Firefox",
    "Zoom",
    "Discord",
    "Reddit",
    "LinkedIn",
    "GitHub",
    "Stack_Overflow",
    "Amazon",
    "AliExpress",
    "eBay",
    "Booking",
    "Uber",
    "Soroush",
    "Eitaa",
    "Bale",
    "Rubika",
    "Divar",
    "Digikala",
    "Snapp",
    "Tapsi",
    "Namava",
    "Filimo",
    "Alibaba_Travel",
    "Torob",
    "Telewebion",
    "Sheypoor",
]


# ============================================
# WEIGHT GENERATION FUNCTIONS
# ============================================

def generate_city_weights():
    """
    Creates weights for cities with Tehran always having the highest weight,
    but the exact values change each run.
    """
    # Base weights - Tehran should always be highest
    base_weights = {
        "Tehran": 30,
        "Mashhad": 15,
        "Isfahan": 12,
        "Karaj": 10,
        "Shiraz": 8,
        "Tabriz": 6,
        "Ahvaz": 5,
        "Qom": 4,
        "Kermanshah": 3,
        "Rasht": 2,
        "Zahedan": 2,
        "Hamadan": 1,
        "Yazd": 1,
        "Ardabil": 1,
        "Bandar_Abbas": 1,
    }

    # Add randomness while preserving the order
    weights = []
    for city in CITIES:
        base = base_weights.get(city, 1)
        # Add random variation (±30%) but keep Tehran on top
        random_factor = random.uniform(0.7, 1.3)
        # Ensure Tehran stays highest by adding a bonus
        if city == "Tehran":
            random_factor = random.uniform(1.0, 1.2)  # Extra boost for Tehran
        weights.append(base * random_factor)

    return weights


def generate_app_weights():
    """
    Creates weights for apps where a few apps are very popular
    and most have lower usage, with randomness each run.
    """
    # Define popularity tiers
    tiers = {
        # Super popular (international + Iranian)
        "super": ["YouTube", "Instagram", "Telegram", "Soroush", "WhatsApp"],
        # Very popular
        "very": ["Chrome", "Google", "TikTok", "Divar", "Digikala"],
        # Popular
        "popular": ["Snapp", "Tapsi", "Netflix", "Bale", "Twitter_X"],
        # Medium
        "medium": ["Spotify", "Gmail", "Rubika", "Eitaa", "Namava", "Filimo"],
        # Lower
        "lower": [
            "Snapchat", "Zoom", "Discord", "Reddit", "Facebook",
            "LinkedIn", "GitHub", "Google_Maps", "Amazon", "AliExpress",
            "Alibaba_Travel", "Torob", "Telewebion", "Sheypoor", "Booking",
            "Edge", "Firefox", "YouTube_Music"
        ],
    }

    weights = []
    for app in APPS:
        if app in tiers["super"]:
            # Super popular: 20-40 weight
            weight = random.uniform(20, 40)
        elif app in tiers["very"]:
            # Very popular: 10-20 weight
            weight = random.uniform(10, 20)
        elif app in tiers["popular"]:
            # Popular: 5-10 weight
            weight = random.uniform(5, 10)
        elif app in tiers["medium"]:
            # Medium: 2-5 weight
            weight = random.uniform(2, 5)
        else:
            # Lower: 0.5-2 weight
            weight = random.uniform(0.5, 2)

        # Add some randomness to make each run different
        weights.append(weight * random.uniform(0.8, 1.2))

    return weights


def generate_network_weights():
    """
    Creates weights for networks where 4G and WiFi are most common.
    """
    # Base weights
    base_weights = [2, 8, 12, 15, 10, 25, 15, 10, 5, 2, 1]  # Matches NETWORKS order

    # Add randomness (±15%)
    weights = [w * random.uniform(0.85, 1.15) for w in base_weights]

    return weights


def generate_device_weights():
    """
    Creates weights where Android and iPhone are most common.
    """
    # Base weights
    base_weights = [
        # Android (10)
        15, 12, 10, 8, 6, 5, 4, 3, 2, 1,
        # iPhone (7)
        8, 7, 6, 5, 4, 3, 2,
        # iPhone Pro Max (1)
        1,
        # Desktop (6)
        0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    ]

    # Add randomness (±20%)
    weights = [w * random.uniform(0.8, 1.2) for w in base_weights]

    return weights


# ============================================
# INITIALIZE
# ============================================

fake = Faker()
# Seed for reproducibility, but weights will still vary
fake.seed_instance(42)

client = clickhouse_connect.get_client(
    host=HOST,
    port=8123,
    database=DATABASE,
    username="default",
    password=""
)

# Generate weights once per run - they'll stay consistent during the run
# but change the next time you run the script
city_weights = generate_city_weights()
app_weights = generate_app_weights()
network_weights = generate_network_weights()
device_weights = generate_device_weights()


# ============================================
# GENERATION FUNCTIONS
# ============================================

def generate_batch(batch_size: int, start_date: datetime) -> list:
    """
    Generate a batch of telecom event records with realistic distributions.

    Args:
        batch_size: Number of records to generate
        start_date: Reference date for time generation

    Returns:
        List of record rows
    """
    rows = []

    # Hourly traffic weights - changes slightly each run
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

    # Add slight randomness to hour weights
    hour_weights = [w * random.uniform(0.9, 1.1) for w in hour_weights]

    hours = list(range(24))

    for _ in range(batch_size):
        # Choose hour based on traffic pattern
        hour = random.choices(hours, weights=hour_weights, k=1)[0]

        # Create event time with realistic distribution
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
            random.choices(APPS, weights=app_weights, k=1)[0],
            random.randint(5, 500),  # latency_ms
            round(random.uniform(0.5, 150), 2),  # download_speed
            round(random.uniform(0, 10), 2),  # packet_loss
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

    # Show the weights being used this run
    print("\n📊 Weight Distribution for this run:")
    print(f"   Top city: {CITIES[city_weights.index(max(city_weights))]} "
          f"({max(city_weights):.1f} weight)")
    print(f"   Top app: {APPS[app_weights.index(max(app_weights))]} "
          f"({max(app_weights):.1f} weight)")
    print("=" * 70)

    start_time = time.time()
    total_inserted = 0
    batch_count = 0

    start_date = datetime.now() - timedelta(days=365)

    while total_inserted < TOTAL_RECORDS:
        batch_count += 1
        remaining = TOTAL_RECORDS - total_inserted
        current_batch_size = min(BATCH_SIZE, remaining)

        rows = generate_batch(current_batch_size, start_date)

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

        progress = (total_inserted / TOTAL_RECORDS) * 100
        elapsed = time.time() - start_time
        speed = total_inserted / elapsed if elapsed > 0 else 0

        print(f"📦 Batch {batch_count}: Inserted {len(rows):,} rows "
              f"| Total: {total_inserted:,} ({progress:.1f}%) "
              f"| Speed: {speed:.0f} rows/sec")

    # Final results
    elapsed_total = time.time() - start_time
    print("=" * 70)
    print("✅ DONE!")
    print(f"📊 Total inserted: {total_inserted:,} rows")
    print(f"⏱️  Total time: {elapsed_total:.2f} seconds")
    print(f"🚀 Average speed: {total_inserted / elapsed_total:.0f} rows/sec")
    print("=" * 70)

    # Verify
    result = client.query("SELECT count() FROM network_events")
    count = result.result_rows[0][0]
    print(f"✅ Verification: {count:,} rows in ClickHouse")

    # Show distribution of top apps for this run
    print("\n📊 Top Applications in this dataset:")
    top_apps = client.query("""
        SELECT app_name, count() as cnt
        FROM network_events
        GROUP BY app_name
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in top_apps.result_rows:
        print(f"   {row[0]}: {row[1]:,}")


if __name__ == "__main__":
    main()
