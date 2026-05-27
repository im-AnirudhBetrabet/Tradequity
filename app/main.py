"""
Tradequity application bootstrap.

This module initiates the FastAPI application, registers middleware,
exception handlers, and API routes.
"""

from contextlib import asynccontextmanager
from fastapi    import FastAPI

from app.api.v1.router            import api_router
from fastapi.middleware.cors      import CORSMiddleware
from app.core.config              import settings
from app.core.exception_handlers  import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Args:
        app:
            FastAPI application instance.
    """
    # Startup hooks to go here
    yield
    # Shutdown hooks to go here

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI:
            Configured application instance.
    """
    app = FastAPI(
        title="Tradequity API",
        description="Backend API for pooled investment operations",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000",],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    register_exception_handlers(app)

    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_application()

@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict[str, str]:
    """
    Application health check endpoint.

    Returns:
        dict[str, str]:
            Health status payload.
    """
    return {"status": "ok"}