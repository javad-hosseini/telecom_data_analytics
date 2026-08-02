from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.routes import events, analytics, partitions, health
from api.middleware import log_requests, timing_middleware, RateLimitMiddleware
from api.exceptions import setup_exception_handlers
from core.config import get_settings
from database.clickhouse_client import ClickHouseClient

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """مدیریت چرخه حیات برنامه"""
    logger.info("🚀 Starting Telecom Analytics API...")
    settings = get_settings()

    try:
        client = ClickHouseClient.get_instance()
        # تست اتصال
        result = client.query("SELECT 1")
        logger.info("✅ Connected to ClickHouse successfully")

        # نمایش اطلاعات نسخه
        version = client.query("SELECT version()")
        logger.info(f"📊 ClickHouse Version: {version.result_rows[0][0]}")

    except Exception as e:
        logger.error(f"❌ Failed to connect to ClickHouse: {e}")
        raise

    yield

    logger.info("🛑 Shutting down API...")


# ایجاد اپلیکیشن
app = FastAPI(
    title="Telecom Data Analytics API",
    version="1.0.0",
    description="""
    🚀 API for analyzing telecom data stored in ClickHouse.

    ## Features:
    * **Events**: Query and explore network events
    * **Analytics**: Business intelligence queries
    * **Partitions**: Manage table partitions
    * **Health**: Monitor system status

    ## Documentation:
    * Swagger UI: `/docs`
    * ReDoc: `/redoc`
    """,
    lifespan=lifespan
)

# افزودن میان‌افزارها
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در محیط تولید محدود کنید
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, calls_per_minute=100)

# ثبت میان‌افزارهای سفارشی
app.middleware("http")(log_requests)
app.middleware("http")(timing_middleware)

# تنظیم مدیریت خطاها
setup_exception_handlers(app)

# ثبت روت‌ها
app.include_router(health.router, tags=["Health"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(partitions.router, prefix="/api/partitions", tags=["Partitions"])


@app.get("/")
async def root():
    """صفحه اصلی API"""
    return {
        "message": "📡 Telecom Data Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "ready": "/ready"
    }


@app.get("/version")
async def version():
    """اطلاعات نسخه"""
    return {
        "api_version": "1.0.0",
        "project": "Telecom Data Analytics",
        "framework": "FastAPI"
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level="info"
    )