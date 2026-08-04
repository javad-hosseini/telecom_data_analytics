# api/routes/health.py
# Health check endpoints for monitoring the API and its dependencies.
# Used by load balancers, monitoring tools, and Kubernetes probes.

from datetime import datetime
from typing import Dict

from fastapi import APIRouter

from database.clickhouse_client import ClickHouseClient

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict:
    """
    Comprehensive health check for the entire system.

    Checks:
    - API is running
    - ClickHouse connection is working
    - ClickHouse version

    Returns a detailed status report.
    """
    global client
    status = {
        "status": "healthy",  # Will change to "unhealthy" if something fails
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    # Check if ClickHouse is reachable
    try:
        client = ClickHouseClient.get_instance()
        # Simple query to verify connection
        result = client.query("SELECT 1")
        status["services"]["clickhouse"] = {
            "status": "healthy",
            "message": "Connected"
        }
    except Exception as e:
        status["status"] = "unhealthy"
        status["services"]["clickhouse"] = {
            "status": "unhealthy",
            "message": str(e)
        }

    # Try to get ClickHouse version for extra info
    try:
        version_result = client.query("SELECT version()")
        status["services"]["clickhouse"]["version"] = version_result.result_rows[0][0]
    except:
        pass

    return status


@router.get("/ready")
async def readiness_check() -> Dict:
    """
    Simple readiness probe for Kubernetes and load balancers.

    Returns:
    - "ready": API is ready to accept traffic
    - "not ready": Something is wrong, don't send traffic here

    Usually called before sending traffic to this instance.
    """
    try:
        client = ClickHouseClient.get_instance()
        client.query("SELECT 1")  # Quick sanity check
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # If DB is down, we're not ready to serve requests
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
