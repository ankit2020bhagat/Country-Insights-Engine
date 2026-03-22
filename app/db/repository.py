"""
app/db/repository.py
Data-access layer. All SQL is here — nodes and routes stay SQL-free.

Pattern: thin async functions that accept a session and return typed objects.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CountryCache, QueryLog

logger = logging.getLogger(__name__)

# ── Cache TTL ─────────────────────────────────────────────────────────────────
CACHE_TTL_HOURS = 24


# ── QueryLog ──────────────────────────────────────────────────────────────────

async def create_query_log(
    session: AsyncSession,
    *,
    user_query: str,
    country_name: str | None,
    requested_fields: list[str] | None,
    status: str,
    answer: str | None,
    missing_fields: list[str] | None,
    duration_ms: int | None,
) -> QueryLog:
    row = QueryLog(
        user_query=user_query,
        country_name=country_name,
        requested_fields=requested_fields,
        status=status,
        answer=answer,
        missing_fields=missing_fields,
        duration_ms=duration_ms,
    )
    session.add(row)
    await session.flush()
    logger.debug("QueryLog created id=%s status=%s", row.id, status)
    return row


async def get_query_log(
    session: AsyncSession, log_id: uuid.UUID
) -> QueryLog | None:
    result = await session.execute(select(QueryLog).where(QueryLog.id == log_id))
    return result.scalar_one_or_none()


async def list_query_logs(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    country: str | None = None,
) -> list[QueryLog]:
    q = select(QueryLog).order_by(QueryLog.created_at.desc())
    if status:
        q = q.where(QueryLog.status == status)
    if country:
        q = q.where(QueryLog.country_name.ilike(f"%{country}%"))
    q = q.limit(limit).offset(offset)
    result = await session.execute(q)
    return list(result.scalars().all())


# ── CountryCache ──────────────────────────────────────────────────────────────

def _cache_key(country_name: str) -> str:
    return country_name.strip().lower()


async def get_cached_country(
    session: AsyncSession, country_name: str
) -> dict | None:
    """Return cached data if present and not expired, else None."""
    key = _cache_key(country_name)
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(CountryCache).where(
            CountryCache.country_key == key,
            CountryCache.expires_at > now,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        logger.debug("Cache HIT for %r", key)
        return row.data
    logger.debug("Cache MISS for %r", key)
    return None


async def upsert_cached_country(
    session: AsyncSession, country_name: str, data: dict
) -> None:
    """Insert or update the cache row for country_name."""
    key = _cache_key(country_name)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=CACHE_TTL_HOURS)

    stmt = (
        pg_insert(CountryCache)
        .values(
            country_key=key,
            cached_at=now,
            expires_at=expires,
            data=data,
        )
        .on_conflict_do_update(
            index_elements=["country_key"],
            set_={"cached_at": now, "expires_at": expires, "data": data},
        )
    )
    await session.execute(stmt)
    logger.debug("Cache upserted for %r (expires %s)", key, expires.isoformat())


async def purge_expired_cache(session: AsyncSession) -> int:
    """Delete all expired cache rows. Returns number of rows deleted."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        delete(CountryCache).where(CountryCache.expires_at <= now)
    )
    count = result.rowcount
    logger.info("Purged %d expired cache rows", count)
    return count