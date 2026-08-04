"""
Module: test_connection.py
Purpose: Test and verify connection to ClickHouse database server.
This module provides utilities for connection testing, health checks,
and troubleshooting ClickHouse connectivity issues.

Usage:
    python test_connection.py          # Run basic connection test
    python test_connection.py --health # Run with additional health checks

Author: [Your Name]
Date: 2026-08-03
Version: 1.0.0
"""

import logging
import sys
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

import clickhouse_connect

from core.config import get_settings

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Configure logging format and level
# - %(asctime)s: Timestamp of the log entry
# - %(levelname)s: Log level (INFO, ERROR, DEBUG, etc.)
# - %(message)s: The actual log message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONNECTION TEST FUNCTIONS
# ============================================================================

def test_clickhouse_connection() -> Tuple[bool, Optional[str]]:
    """
    Test connection to ClickHouse server and retrieve its version.

    This function attempts to establish a connection to the ClickHouse server
    using the settings from the central configuration. It performs a simple
    query to verify connectivity and returns the server version.

    Returns:
        Tuple[bool, Optional[str]]:
            - First element: True if connection successful, False otherwise
            - Second element: Server version string if successful, None if failed

    Raises:
        No exceptions are raised; all errors are caught and logged.

    Example:
        >>> success, version = test_clickhouse_connection()
        >>> if success:
        ...     print(f"Connected to ClickHouse version {version}")
        ... else:
        ...     print("Connection failed")
    """
    client = None
    settings = get_settings()  # Get centralized configuration

    try:
        logger.info(f"Attempting to connect to ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port}...")

        # Create connection with timeout settings
        # - connect_timeout: Maximum time to wait for establishing connection
        # - send_receive_timeout: Maximum time for query execution
        client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            connect_timeout=settings.connection_timeout,
            send_receive_timeout=settings.query_timeout,
            # Uncomment if authentication is needed:
            # username=settings.clickhouse_username,
            # password=settings.clickhouse_password,
            # database=settings.clickhouse_database
        )

        # Test connection with a simple query
        # The version() function returns the ClickHouse server version
        logger.info("Executing test query...")
        result = client.query("SELECT version()")

        # Extract version from result
        # result.result_rows is a list of tuples, each tuple represents a row
        version = result.result_rows[0][0] if result.result_rows else "Unknown"

        logger.info("✅ Connection established successfully!")
        logger.info(f"📌 ClickHouse version: {version}")
        logger.info(f"📊 Records returned: {len(result.result_rows)}")

        return True, version

    # ====== ERROR HANDLING ======
    # Different exception types help identify the root cause of failures

    except clickhouse_connect.driver.exceptions.DatabaseError as db_err:
        """Database-level errors (e.g., authentication failure, database doesn't exist)"""
        logger.error(f"❌ Database error: {db_err}")
        logger.error("   Possible causes: Invalid username/password or database doesn't exist")
        return False, None

    except clickhouse_connect.driver.exceptions.ConnectionError as conn_err:
        """Network-level errors (e.g., server not reachable, wrong host/port)"""
        logger.error(f"❌ Connection error: {conn_err}")
        logger.error(
            f"   Please verify ClickHouse server is running on {settings.clickhouse_host}:{settings.clickhouse_port}")
        logger.error("   Check service status: systemctl status clickhouse-server")
        logger.error("   Or check logs: tail -f /var/log/clickhouse-server/clickhouse-server.log")
        return False, None

    except TimeoutError as timeout_err:
        """Timeout errors (e.g., slow network, server overload)"""
        logger.error(f"❌ Timeout error: {timeout_err}")
        logger.error(f"   Connection timeout: {settings.connection_timeout}s, Query timeout: {settings.query_timeout}s")
        logger.error("   Consider increasing timeout values in config.py for slower networks")
        return False, None

    except clickhouse_connect.driver.exceptions.OperationalError as op_err:
        """Operational errors (e.g., server overload, network issues)"""
        logger.error(f"❌ Operational error: {op_err}")
        logger.error("   This could be due to network issues or server overload")
        return False, None

    except Exception as e:
        """Catch-all for any unexpected errors"""
        logger.error(f"❌ Unexpected error: {type(e).__name__} - {e}")
        logger.error("   Please check the full traceback for more details")
        import traceback
        logger.debug(traceback.format_exc())  # Debug-level traceback for developers
        return False, None

    finally:
        # Always close the connection to free resources
        if client:
            try:
                client.close()
                logger.info("🔌 Connection closed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Error while closing connection: {e}")


# ============================================================================
# HEALTH CHECK FUNCTIONS
# ============================================================================

def check_server_health() -> Dict[str, Any]:
    """
    Perform comprehensive health checks on the ClickHouse server.

    This function collects various system metrics to assess the health
    and performance of the ClickHouse server. It's useful for monitoring
    and debugging purposes.

    Returns:
        Dict[str, Any]: Dictionary containing health check results with:
            - timestamp: Time of the health check
            - host: Server hostname
            - port: Server port
            - status: 'healthy' or 'unhealthy'
            - checks: Dictionary of individual health metrics
                - uptime: Server uptime in seconds
                - database_size_bytes: Total database size in bytes
                - database_size_human: Human-readable database size
                - table_count: Number of tables in the database

    Example:
        >>> health = check_server_health()
        >>> if health['status'] == 'healthy':
        ...     print("Server is healthy!")
        ...     print(f"Uptime: {health['checks']['uptime']} seconds")
    """
    settings = get_settings()

    # Initialize the health info dictionary with basic metadata
    health_info = {
        "timestamp": datetime.now().isoformat(),
        "host": settings.clickhouse_host,
        "port": settings.clickhouse_port,
        "checks": {}
    }

    try:
        # Create a client with shorter timeouts for health checks
        # (we don't want health checks to hang if the server is slow)
        client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            connect_timeout=5,  # 5 second connection timeout
            send_receive_timeout=5  # 5 second query timeout
        )

        # --- Check 1: Server Uptime ---
        # The uptime() function returns server uptime in seconds
        uptime_result = client.query("SELECT uptime()")
        health_info["checks"]["uptime"] = uptime_result.result_rows[0][0]

        # --- Check 2: Database Size ---
        # Calculate total database size from system.tables
        # sum(bytes) gives total bytes, formatReadableSize() makes it human-readable
        size_result = client.query("""
            SELECT 
                sum(bytes) as total_bytes,
                formatReadableSize(sum(bytes)) as total_size
            FROM system.tables 
            WHERE database != 'system'
        """)
        health_info["checks"]["database_size_bytes"] = size_result.result_rows[0][0]
        health_info["checks"]["database_size_human"] = size_result.result_rows[0][1]

        # --- Check 3: Number of Tables ---
        # Count tables excluding system tables
        tables_result = client.query("SELECT count() FROM system.tables WHERE database != 'system'")
        health_info["checks"]["table_count"] = tables_result.result_rows[0][0]

        # Close the connection
        client.close()

        # Mark as healthy if all checks passed
        health_info["status"] = "healthy"

    except Exception as e:
        # If any check fails, mark as unhealthy and record the error
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)

    return health_info


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point for the connection test script.

    This function orchestrates the connection testing workflow:
    1. Displays connection parameters
    2. Runs the connection test
    3. Optionally runs additional health checks
    4. Displays results and troubleshooting tips if needed

    Returns:
        None (exits with status code 0 on success, 1 on failure)
    """
    settings = get_settings()

    # ====== Display Connection Configuration ======
    print("=" * 70)
    print("🔍 ClickHouse Connection Test")
    print("=" * 70)
    print(f"📍 Host: {settings.clickhouse_host}")
    print(f"🔢 Port: {settings.clickhouse_port}")
    print(f"⏱️  Connection timeout: {settings.connection_timeout} seconds")
    print(f"⏱️  Query timeout: {settings.query_timeout} seconds")
    print("=" * 70)

    # ====== Run the Connection Test ======
    start_time = datetime.now()
    success, version = test_clickhouse_connection()
    elapsed_time = (datetime.now() - start_time).total_seconds()

    # ====== Display Results ======
    print("=" * 70)
    if success:
        print("✅ STATUS: Connection successful")
        print(f"📌 Version: {version}")
        print(f"⏱️  Execution time: {elapsed_time:.2f} seconds")

        # ====== Optional Health Checks ======
        # Ask user if they want to run additional health checks
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
                    # Convert snake_case to Title Case for display
                    display_key = key.replace('_', ' ').title()
                    print(f"   {display_key}: {value}")
            if 'error' in health_info:
                print(f"   Error: {health_info['error']}")
    else:
        # ====== Troubleshooting Help ======
        print("❌ STATUS: Connection failed")
        print(f"⏱️  Execution time: {elapsed_time:.2f} seconds")
        print("\n💡 Troubleshooting tips:")
        print("   1. Verify ClickHouse server is running")
        print("      - Linux: sudo systemctl status clickhouse-server")
        print("      - Check logs: tail -f /var/log/clickhouse-server/clickhouse-server.log")
        print("   2. Check network connectivity")
        print("      - Ping test: ping <server_ip>")
        print("      - Port test: telnet <server_ip> 8123")
        print("   3. Verify host and port are correct in config.py")
        print("   4. Check firewall settings (port 8123 should be open)")
        print("   5. Review server logs for errors")

    print("=" * 70)

    # ====== Return Exit Code ======
    # Exit code 0: Success, 1: Failure (useful for scripting)
    sys.exit(0 if success else 1)


# ============================================================================
# ADDITIONAL UTILITY FUNCTIONS
# ============================================================================

def test_with_authentication():
    """
    Example function for testing ClickHouse with authentication.

    This demonstrates how to connect when authentication is required.
    Uncomment and use if your ClickHouse server uses username/password.

    Note: This function is not called by default and is provided as a reference.
    """
    settings = get_settings()

    try:
        client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_username,  # Username from config
            password=settings.clickhouse_password,  # Password from config
            database=settings.clickhouse_database,  # Database from config
            connect_timeout=10,
            send_receive_timeout=10
        )

        result = client.query("SELECT version()")
        print(f"✅ Connected with authentication! Version: {result.result_rows[0][0]}")
        client.close()

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    When this script is run directly (not imported as a module):
    1. Execute the main() function
    2. This allows the script to be used as a standalone tool
    3. Also allows importing functions for use in other modules
    """
    main()
