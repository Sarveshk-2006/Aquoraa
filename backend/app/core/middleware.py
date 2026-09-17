import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("aquora.middleware")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a correlation request ID.
    Propagates incoming 'X-Request-ID' header or generates a new UUID4.
    Binds the request ID to structlog context and adds it to response headers.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if hasattr(structlog, "contextvars"):
            try:
                structlog.contextvars.clear_contextvars()
            except Exception:
                pass
        
        incoming_id = request.headers.get("X-Request-ID")
        request_id = incoming_id if incoming_id else str(uuid.uuid4())
        
        request.state.request_id = request_id
        if hasattr(structlog, "contextvars"):
            try:
                structlog.contextvars.bind_contextvars(request_id=request_id)
            except Exception:
                pass

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
