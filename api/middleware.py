# api/middleware.py
# Middleware functions that run on every request.
# Handles logging, timing, and rate limiting.

import logging
import time
from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    """
    Logs every incoming request and outgoing response.

    Captures:
    - HTTP method and path
    - Client IP
    - Response status code
    - Processing time

    Also stores the start time in request.state so exception handlers can use it.
    """
    start_time = time.time()

    # Store start time so exception handlers can include it
    request.state.request_time = start_time

    # Log the incoming request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )

    response = await call_next(request)

    # Calculate and log processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    logger.info(
        f"Response: {response.status_code}",
        extra={
            "status_code": response.status_code,
            "process_time": process_time
        }
    )

    return response


async def timing_middleware(request: Request, call_next):
    """
    Simple timing middleware that adds a response header.

    Adds X-Response-Time header with the total processing time.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Response-Time"] = f"{process_time:.4f}s"

    return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiter that limits requests per minute per IP.

    - Counts requests from each IP in a sliding 60-second window
    - Returns 429 Too Many Requests if limit is exceeded
    - Default limit: 60 requests per minute

    Note: This is a simple in-memory implementation. For production,
    consider using Redis for distributed rate limiting.
    """

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests: Dict[str, list] = {}  # IP -> list of timestamps

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host

        # Clean up old requests (older than 60 seconds)
        current_time = time.time()
        if client_ip in self.requests:
            # Keep only requests from the last 60 seconds
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if current_time - t < 60
            ]
        else:
            self.requests[client_ip] = []

        # Check if the client has exceeded the limit
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # Record this request
        self.requests[client_ip].append(current_time)

        return await call_next(request)
