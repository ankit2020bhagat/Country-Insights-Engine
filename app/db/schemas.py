"""
app/models/schemas.py
All Pydantic models used across the service.

Split into three groups:
  1. Internal agent models  (IntentResult, CountryData)
  2. Agent response         (AgentResponse, AgentStatus)
  3. API contracts          (QueryRequest, QueryResponse, HistoryItem, HealthResponse)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 1. Internal agent models ──────────────────────────────────────────────────

class IntentResult(BaseModel):
    country_name: str = Field(description="Country name in English.")
    requested_fields: list[str] = Field(
        description=(
            "Fields to retrieve. Valid: capital, population, currencies, "
            "languages, region, subregion, flags, area, timezones, tld."
        )
    )
    is_valid: bool = Field(description="False when no country can be identified.")
    validation_error: str | None = Field(
        default=None, description="Reason when is_valid is False."
    )


class CountryData(BaseModel):
    common_name: str
    official_name: str
    capital: list[str] | None = None
    population: int | None = None
    currencies: dict[str, Any] | None = None
    languages: dict[str, str] | None = None
    region: str | None = None
    subregion: str | None = None
    flag_emoji: str | None = None
    flag_png: str | None = None
    area_km2: float | None = None
    timezones: list[str] | None = None
    tld: list[str] | None = None

    def to_cache_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_cache_dict(cls, d: dict) -> "CountryData":
        return cls(**d)


# ── 2. Agent response ─────────────────────────────────────────────────────────

class AgentStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"
    INVALID_QUERY = "invalid_query"
    ERROR = "error"


class AgentResponse(BaseModel):
    status: AgentStatus
    answer: str
    country: str | None = None
    requested_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    raw_country_data: CountryData | None = None
    cache_hit: bool = False


# ── 3. API contracts ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=500,
        examples=["What is the population of Germany?"],
    )


class QueryResponse(BaseModel):
    query_id: uuid.UUID
    status: AgentStatus
    answer: str
    country: str | None = None
    requested_fields: list[str]
    missing_fields: list[str]
    cache_hit: bool
    duration_ms: int


class HistoryItem(BaseModel):
    query_id: uuid.UUID
    created_at: datetime
    user_query: str
    country_name: str | None
    status: AgentStatus
    answer: str | None
    duration_ms: int | None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    db: str  # "ok" | "error"