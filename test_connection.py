import clickhouse_connect
import logging
import sys
from datetime import datetime
from typing import Tuple, Optional
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)



# Optional: Read from environment variables
# import os
# HOST = os.getenv("CLICKHOUSE_HOST", "192.168.247.128")
# PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
# USERNAME = os.getenv("CLICKHOUSE_USER", "default")
# PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
# DATABASE = os.getenv("CLICKHOUSE_DB", "default")


def test_clickhouse_connection() -> Tuple[bool, Optional[str]]:
    """
    Test connection to ClickHouse server and display its version

    Returns:
        Tuple[bool, Optional[str]]: (success_status, version_string)
    """
    client = None

    try:
        logger.info(f"Attempting to connect to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}...")

        # Create connection with timeout settings
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            connect_timeout=CONNECTION_TIMEOUT,
            send_receive_timeout=QUERY_TIMEOUT,
            # Uncomment if authentication is needed:
            # username=USERNAME,
            # password=PASSWORD,
            # database=DATABASE
        )

        # Test connection with a simple query
        logger.info("Executing test query...")
        result = client.query("SELECT version()")

        # Extract version from result
        version = result.result_rows[0][0] if result.result_rows else "Unknown"

        logger.info("✅ Connection established successfully!")
        logger.info(f"📌 ClickHouse version: {version}")
        logger.info(f"📊 Records returned: {len(result.result_rows)}")

        return True, version

    except clickhouse_connect.driver.exceptions.DatabaseError as db_err:
        logger.error(f"❌ Database error: {db_err}")
        logger.error("   Possible causes: Invalid username/password or database doesn't exist")
        return False, None

    except clickhouse_connect.driver.exceptions.ConnectionError as conn_err:
        logger.error(f"❌ Connection error: {conn_err}")
        logger.error(f"   Please verify ClickHouse server is running on {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
        logger.error("   Check service status: systemctl status clickhouse-server")
        logger.error("   Or check logs: tail -f /var/log/clickhouse-server/clickhouse-server.log")
        return False, None

    except TimeoutError as timeout_err:
        logger.error(f"❌ Timeout error: {timeout_err}")
        logger.error(f"   Connection timeout: {CONNECTION_TIMEOUT}s, Query timeout: {QUERY_TIMEOUT}s")
        logger.error("   Consider increasing timeout values for slower networks")
        return False, None

    except clickhouse_connect.driver.exceptions.OperationalError as op_err:
        logger.error(f"❌ Operational error: {op_err}")
        logger.error("   This could be due to network issues or server overload")
        return False, None

    except Exception as e:
        logger.error(f"❌ Unexpected error: {type(e).__name__} - {e}")
        logger.error("   Please check the full traceback for more details")
        import traceback
        logger.debug(traceback.format_exc())
        return False, None

    finally:
        if client:
            try:
                client.close()
                logger.info("🔌 Connection closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Error while closing connection: {e}")


def check_server_health() -> dict:
    """
    Perform additional health checks on the ClickHouse server

    Returns:
        dict: Dictionary with health check results
    """
    health_info = {
        "timestamp": datetime.now().isoformat(),
        "host": CLICKHOUSE_HOST,
        "port": CLICKHOUSE_PORT,
        "checks": {}
    }

    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            connect_timeout=5,
            send_receive_timeout=5
        )

        # Check system metrics
        uptime_result = client.query("SELECT uptime()")
        health_info["checks"]["uptime"] = uptime_result.result_rows[0][0]

        # Check database size
        size_result = client.query("""
            SELECT 
                sum(bytes) as total_bytes,
                formatReadableSize(sum(bytes)) as total_size
            FROM system.tables 
            WHERE database != 'system'
        """)
        health_info["checks"]["database_size_bytes"] = size_result.result_rows[0][0]
        health_info["checks"]["database_size_human"] = size_result.result_rows[0][1]

        # Check number of tables
        tables_result = client.query("SELECT count() FROM system.tables WHERE database != 'system'")
        health_info["checks"]["table_count"] = tables_result.result_rows[0][0]

        client.close()
        health_info["status"] = "healthy"

    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)

    return health_info



def main():
    """
    Main function to run the connection test
    """
    print("=" * 70)
    print("🔍 ClickHouse Connection Test")
    print("=" * 70)
    print(f"📍 Host: {CLICKHOUSE_HOST}")
    print(f"🔢 Port: {CLICKHOUSE_PORT}")
    print(f"⏱️  Connection timeout: {CONNECTION_TIMEOUT} seconds")
    print(f"⏱️  Query timeout: {QUERY_TIMEOUT} seconds")
    print("=" * 70)

    # Run the connection test
    start_time = datetime.now()
    success, version = test_clickhouse_connection()
    elapsed_time = (datetime.now() - start_time).total_seconds()

    # Display results
    print("=" * 70)
    if success:
        print("✅ STATUS: Connection successful")
        print(f"📌 Version: {version}")
        print(f"⏱️  Execution time: {elapsed_time:.2f} seconds")

        # Ask if user wants additional health checks
        print("\n" + "=" * 70)
        response = input("🔍 Run additional health checks? (y/n): ").strip().lower()
        if response == 'y':
            print("\nRunning health checks...")
            health_info = check_server_health()
            print("=" * 70)
            print("🏥 Server Health Report:")
            print(f"   Status: {health_info.get('status', 'unknown')}")
            if 'checks' in health_info:
                for key, value in health_info['checks'].items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            if 'error' in health_info:
                print(f"   Error: {health_info['error']}")
    else:
        print("❌ STATUS: Connection failed")
        print(f"⏱️  Execution time: {elapsed_time:.2f} seconds")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify ClickHouse server is running")
        print("   2. Check network connectivity")
        print("   3. Verify host and port are correct")
        print("   4. Check firewall settings")
        print("   5. Review server logs for errors")

    print("=" * 70)

    # Return exit code for scripting
    sys.exit(0 if success else 1)


def test_with_authentication():
    """
    Example function for testing with authentication
    """
    try:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USERNAME,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
            connect_timeout=10,
            send_receive_timeout=10
        )

        result = client.query("SELECT version()")
        print(f"✅ Connected with authentication! Version: {result.result_rows[0][0]}")
        client.close()

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")

# hostname -I
if __name__ == "__main__":
    main()