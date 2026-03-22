"""
app/tools/countries_api.py
Async REST Countries API client with PostgreSQL-backed caching.

Caching strategy:
  1. Check CountryCache table (TTL = 24 h).
  2. On miss, fetch from upstream API.
  3. Write result back to cache.

This makes the service resilient to upstream outages during the TTL window
and dramatically reduces latency on repeated queries for the same country.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import repository
from app.db.schemas import CountryData

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Typed exceptions ──────────────────────────────────────────────────────────

class CountryNotFoundError(Exception):
    def __init__(self, country: str) -> None:
        super().__init__(f"Country not found: {country!r}")
        self.country = country


class CountriesAPIError(Exception):
    pass


# ── Client ────────────────────────────────────────────────────────────────────

class CountriesAPIClient:
    """
    Async HTTP client for https://restcountries.com/v3.1.
    Accepts an AsyncSession so it can read/write the country cache.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._base = settings.countries_api_base
        self._fields = settings.countries_api_fields
        self._timeout = settings.http_timeout_seconds
        self._max_retries = settings.http_max_retries

    async def fetch_country(self, country_name: str) -> CountryData:
        """
        Return CountryData for *country_name*.
        Checks DB cache first; falls through to upstream API on miss.
        """
        # 1. Cache lookup
        cached = await repository.get_cached_country(self._session, country_name)
        if cached:
            return CountryData.from_cache_dict(cached)

        # 2. Upstream fetch
        raw = await self._fetch_with_retry(country_name)
        data = self._normalise(raw[0])

        # 3. Populate cache
        await repository.upsert_cached_country(
            self._session, country_name, data.to_cache_dict()
        )

        return data

    # ── Internal ──────────────────────────────────────────────────────────

    async def _fetch_with_retry(self, country_name: str) -> list[dict[str, Any]]:
        url = f"{self._base}/name/{country_name}"
        params = {"fields": self._fields, "fullText": "false"}
        last_exc: Exception | None = None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(1, self._max_retries + 1):
                try:
                    logger.debug("GET %s attempt=%d", url, attempt)
                    resp = await client.get(url, params=params)

                    if resp.status_code == 404:
                        raise CountryNotFoundError(country_name)

                    resp.raise_for_status()
                    return resp.json()

                except CountryNotFoundError:
                    raise

                except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                    logger.warning("Attempt %d failed: %s", attempt, exc)
                    last_exc = exc

        raise CountriesAPIError(
            f"All {self._max_retries} retries failed for {country_name!r}"
        ) from last_exc

    @staticmethod
    def _normalise(raw: dict[str, Any]) -> CountryData:
        name_block = raw.get("name", {})
        flags_block = raw.get("flags", {})
        return CountryData(
            common_name=name_block.get("common", "Unknown"),
            official_name=name_block.get("official", "Unknown"),
            capital=raw.get("capital"),
            population=raw.get("population"),
            currencies=raw.get("currencies"),
            languages=raw.get("languages"),
            region=raw.get("region"),
            subregion=raw.get("subregion"),
            flag_emoji=flags_block.get("alt") or None,
            flag_png=flags_block.get("png"),
            area_km2=raw.get("area"),
            timezones=raw.get("timezones"),
            tld=raw.get("tld"),
        )