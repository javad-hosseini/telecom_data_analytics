from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """کلاس پایه برای خطاهای سفارشی"""

    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(AppException):
    """خطای دیتابیس"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=503, details=details)


class ValidationException(AppException):
    """خطای اعتبارسنجی"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


def setup_exception_handlers(app: FastAPI):
    """تنظیم هندلرهای خطا"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"App Exception: {exc.message}", extra=exc.details)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "details": exc.details,
                "timestamp": request.state.get("request_time", None)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "timestamp": request.state.get("request_time", None)
            }
        )