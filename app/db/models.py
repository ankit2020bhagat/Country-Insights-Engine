"""
app/db/models.py
SQLAlchemy ORM models.

Two tables:
  query_log   — immutable audit log of every agent invocation
  country_cache — short-lived cache of REST Countries API responses
                  (avoids hammering the upstream API on repeated queries)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class QueryLog(Base):
    """
    Immutable audit log: one row per agent invocation.
    Useful for debugging, analytics, and SLA reporting.
    """

    __tablename__ = "query_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    # Input
    user_query: Mapped[str] = mapped_column(Text, nullable=False)

    # Intent parse result
    country_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    requested_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Outcome
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Performance
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_query_log_country", "country_name"),
        Index("ix_query_log_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<QueryLog id={self.id} country={self.country_name!r} status={self.status!r}>"


class CountryCache(Base):
    """
    TTL-based cache for REST Countries API responses.
    Checked before every upstream call to reduce latency and rate-limit risk.
    Stale rows are pruned by the /admin/cache/purge endpoint or a cron job.
    """

    __tablename__ = "country_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_key: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
    )  # normalised lowercase name
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Full normalised CountryData as JSON
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (UniqueConstraint("country_key", name="uq_country_cache_key"),)

    def __repr__(self) -> str:
        return f"<CountryCache key={self.country_key!r} expires={self.expires_at}>"