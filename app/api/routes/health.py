"""
app/api/routes/health.py
GET /health — liveness + DB connectivity check
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.db.schemas import HealthResponse

router = APIRouter(tags=["ops"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        db=db_status,
    )