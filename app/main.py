"""Main FastAPI application"""

from contextlib import asynccontextmanager
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.models import ErrorResponse

logger = get_logger(__name__)

# Application startup time
startup_time = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create async HTTP client
    app.state.http_client = httpx.AsyncClient(
        timeout=settings.YR_NO_TIMEOUT_SECONDS,
        limits=httpx.Limits(max_connections=100),
        headers={
            "User-Agent": settings.YR_NO_USER_AGENT
        }
    )
    logger.info("HTTP client initialized")

    app.state.startup_time = startup_time

    yield

    # Shutdown
    await app.state.http_client.aclose()
    logger.info("HTTP client closed")
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with standardized error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            details=getattr(exc, "details", None)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details=None
        ).model_dump()
    )


# Register web interface routes first (so they take precedence)
from app.api.web_routes import router as web_router
app.include_router(web_router, tags=["Web Interface"])

# Register API routes
from app.api.routes import router as api_router
app.include_router(api_router, prefix="/api", tags=["Weather Forecast"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
