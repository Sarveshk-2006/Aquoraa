from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as top_health_router
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger, setup_logging
from app.core.middleware import RequestIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Starting Aquora Backend Service",
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

    yield
    logger.info("Shutting down Aquora Backend Service")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# 1. Register Request Correlation Middleware
app.add_middleware(RequestIDMiddleware)

# 2. Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://aquora-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Standard Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 4. Register Routers
app.include_router(api_router)
app.include_router(top_health_router)

@app.api_route("/", methods=["GET", "HEAD"], summary="Root Metadata Endpoint")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "tagline": "See the flood before it becomes a crisis.",
        "phase": "Phase 1 - Repository + Infrastructure Foundation Hardening",
        "docs": "/docs",
        "endpoints": {
            "liveness": "/api/v1/health/live",
            "readiness": "/api/v1/health/ready"
        }
    }
