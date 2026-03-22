"""
app/main.py
FastAPI application factory.

Uses lifespan context manager (preferred over deprecated on_event) to:
  - Run DB migrations on startup (dev/staging only)
  - Dispose the SQLAlchemy engine on shutdown
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, history, query
from app.config import get_settings
from app.db.session import engine

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
# Quiet noisy third-party loggers
for _pkg in ("httpx", "httpcore", "anthropic", "sqlalchemy.engine.base"):
    logging.getLogger(_pkg).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment)

    # In non-production envs, auto-create tables (Alembic handles production)
    if settings.environment != "production":
        from app.db.models import Base
        from sqlalchemy.ext.asyncio import create_async_engine as _eng
        _e = _eng(settings.database_url)
        try:
            async with _e.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables verified/created via SQLAlchemy metadata")
        except Exception as exc:
            logger.warning("Could not auto-create tables: %s", exc)
        finally:
            await _e.dispose()

    yield

    logger.info("Shutting down — disposing engine")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "LangGraph-powered agent that answers natural language questions "
            "about countries using the REST Countries API, backed by PostgreSQL."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment != "production" else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ───────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(query.router)
    app.include_router(history.router)

    return app


app = create_app()