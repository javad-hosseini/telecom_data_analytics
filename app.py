# app.py
# The main entry point for the FastAPI application.
# This is where we build and configure the API.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.exceptions import setup_exception_handlers
from api.middleware import log_requests, timing_middleware, RateLimitMiddleware
from api.routes import events, analytics, partitions, health
from core.config import get_settings
from database.clickhouse_client import ClickHouseClient

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.

    - On startup: Connect to ClickHouse and log the version
    - On shutdown: Clean up resources

    This runs automatically when the API starts and stops.
    """
    logger.info("🚀 Starting Telecom Analytics API...")
    settings = get_settings()

    try:
        client = ClickHouseClient.get_instance()
        # Quick test to make sure DB is reachable
        result = client.query("SELECT 1")
        logger.info("✅ Connected to ClickHouse successfully")

        # Show which ClickHouse version we're using
        version = client.query("SELECT version()")
        logger.info(f"📊 ClickHouse Version: {version.result_rows[0][0]}")

    except Exception as e:
        logger.error(f"❌ Failed to connect to ClickHouse: {e}")
        raise  # Don't start the API if DB is down

    yield  # The API runs here

    logger.info("🛑 Shutting down API...")


# Create the FastAPI app instance
app = FastAPI(
    title="Telecom Data Analytics API",
    version="1.0.0",
    description="""
    API for analyzing telecom data stored in ClickHouse.

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

# ============ MIDDLEWARE ============

# CORS - allows frontend apps to call this API from different domains
# In production, change "*" to your actual frontend URL for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production: replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting - prevents abuse by limiting requests per IP
app.add_middleware(RateLimitMiddleware, calls_per_minute=100)

# Custom middleware for logging and timing
app.middleware("http")(log_requests)
app.middleware("http")(timing_middleware)

# Setup global error handling
setup_exception_handlers(app)

# ============ ROUTES ============
# Register all route groups with their prefixes

app.include_router(health.router, tags=["Health"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(partitions.router, prefix="/api/partitions", tags=["Partitions"])


# ============ ROOT ENDPOINTS ============

@app.get("/")
async def root():
    """API home page - shows available endpoints"""
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
    """Get API version info"""
    return {
        "api_version": "1.0.0",
        "project": "Telecom Data Analytics",
        "framework": "FastAPI"
    }


# Serve the frontend dashboard (static files)
app.mount("/dashboard", StaticFiles(directory="telecom-dashboard", html=True), name="dashboard")

# ============ RUN THE API ============

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,  # Auto-reload when code changes (development only)
        log_level="info"
    )
