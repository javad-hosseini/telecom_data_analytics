# api/exceptions.py
# Custom exception classes and global error handlers for the API.
# Makes sure all errors are returned in a consistent format.

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for all custom errors in the app"""

    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(AppException):
    """Raised when something goes wrong with the database"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=503, details=details)


class ValidationException(AppException):
    """Raised when input data fails validation"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


def setup_exception_handlers(app: FastAPI):
    """
    Register global error handlers for the FastAPI app.

    This catches all exceptions and returns them in a consistent
    JSON format so clients always know what to expect.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        # Log the error with any extra details
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
        # Catch-all for any unexpected errors we didn't anticipate
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "timestamp": request.state.get("request_time", None)
            }
        )
