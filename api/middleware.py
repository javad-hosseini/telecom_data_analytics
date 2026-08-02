from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    """لاگ درخواست‌ها"""
    start_time = time.time()

    # اضافه کردن زمان به state برای استفاده در هندلرهای خطا
    request.state.request_time = start_time

    # لاگ درخواست
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )

    response = await call_next(request)

    # محاسبه زمان پاسخ
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
    """اندازه‌گیری زمان پاسخ"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # اضافه کردن هدر زمان
    response.headers["X-Response-Time"] = f"{process_time:.4f}s"

    return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """محدودیت نرخ درخواست‌ها (ساده)"""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host

        # پاکسازی درخواست‌های قدیمی
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if current_time - t < 60
            ]
        else:
            self.requests[client_ip] = []

        # بررسی محدودیت
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # ثبت درخواست جدید
        self.requests[client_ip].append(current_time)

        return await call_next(request)
