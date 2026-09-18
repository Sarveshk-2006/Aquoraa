import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger("aquora.exceptions")

class AppException(Exception):
    """Base application exception for controlled business logic errors."""
    def __init__(self, message: str, code: str = "BAD_REQUEST", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = get_request_id(request)
    logger.warning("Application exception occurred", code=exc.code, message=exc.message, request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id(request)
    error_messages = [f"{err.get('loc', [])}: {err.get('msg', '')}" for err in exc.errors()]
    combined_message = f"Validation failed: {', '.join(error_messages)}"
    logger.warning("Validation error", details=error_messages, request_id=request_id)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": combined_message,
                "request_id": request_id
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from fastapi import HTTPException
    request_id = get_request_id(request)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "request_id": request_id
                }
            }
        )
    logger.error("Unhandled internal server error", error_type=type(exc).__name__, error=str(exc), request_id=request_id)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"Unhandled error ({type(exc).__name__}): {exc!s}",
                "request_id": request_id
            }
        }
    )
