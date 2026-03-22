"""
app/api/routes/history.py
GET  /history             — paginated query log
GET  /history/{query_id}  — single log entry
POST /admin/cache/purge   — delete expired cache rows
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import (
    get_query_log,
    list_query_logs,
    purge_expired_cache,
)
from app.db.session import get_db
from app.db.schemas import AgentStatus, HistoryItem

router = APIRouter(tags=["history"])


@router.get(
    "/history",
    response_model=list[HistoryItem],
    summary="Paginated query history",
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: AgentStatus | None = Query(default=None),
    country: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[HistoryItem]:
    rows = await list_query_logs(
        db,
        limit=limit,
        offset=offset,
        status=status.value if status else None,
        country=country,
    )
    return [
        HistoryItem(
            query_id=row.id,
            created_at=row.created_at,
            user_query=row.user_query,
            country_name=row.country_name,
            status=AgentStatus(row.status),
            answer=row.answer,
            duration_ms=row.duration_ms,
        )
        for row in rows
    ]


@router.get(
    "/history/{query_id}",
    response_model=HistoryItem,
    summary="Single query log entry",
)
async def get_history_item(
    query_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> HistoryItem:
    row = await get_query_log(db, query_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return HistoryItem(
        query_id=row.id,
        created_at=row.created_at,
        user_query=row.user_query,
        country_name=row.country_name,
        status=AgentStatus(row.status),
        answer=row.answer,
        duration_ms=row.duration_ms,
    )


@router.post(
    "/admin/cache/purge",
    summary="Delete expired country cache rows",
)
async def purge_cache(db: AsyncSession = Depends(get_db)) -> dict:
    deleted = await purge_expired_cache(db)
    return {"deleted": deleted}