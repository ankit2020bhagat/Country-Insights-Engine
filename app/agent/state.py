"""
app/agent/state.py
The shared state dict that flows through every LangGraph node.
"""
from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from app.db.schemas import AgentStatus, CountryData, IntentResult


class AgentState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────
    user_query: str

    # ── Post-intent ────────────────────────────────────────────────────────
    intent: Optional[IntentResult]

    # ── Post-fetch ─────────────────────────────────────────────────────────
    country_data: Optional[CountryData]
    fetch_error: Optional[str]
    cache_hit: bool

    # ── Post-synthesis ─────────────────────────────────────────────────────
    answer: Optional[str]
    missing_fields: list[str]

    # ── Routing metadata ───────────────────────────────────────────────────
    status: Optional[AgentStatus]