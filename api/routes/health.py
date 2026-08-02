from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict

from database.clickhouse_client import ClickHouseClient
from core.config import get_settings, Settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict:
    """بررسی سلامت کلی سیستم"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    # بررسی ClickHouse
    try:
        client = ClickHouseClient.get_instance()
        # کوئری ساده برای تست
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

    # اطلاعات نسخه
    try:
        version_result = client.query("SELECT version()")
        status["services"]["clickhouse"]["version"] = version_result.result_rows[0][0]
    except:
        pass

    return status


@router.get("/ready")
async def readiness_check() -> Dict:
    """بررسی آمادگی برای پذیرش ترافیک"""
    try:
        client = ClickHouseClient.get_instance()
        client.query("SELECT 1")
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    