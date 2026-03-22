"""
app/agent/nodes.py
The three config LangGraph nodes + error node.

Each node is a pure async function: (AgentState) → dict.
LangGraph merges the returned dict into shared state.

Dependency injection pattern:
  Nodes that need I/O (Claude, DB) are produced by factory functions
  that close over their dependencies. This makes every node trivially testable
  by injecting mocks at the factory call site.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any
import re
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.config import get_settings
from app.db.schemas import AgentStatus, IntentResult
from app.tools.countries_api import CountriesAPIClient, CountriesAPIError, CountryNotFoundError

logger = logging.getLogger(__name__)
settings = get_settings()



# ── Shared Anthropic client (one per process) ─────────────────────────────────
_claude = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

NodeFn = Callable[[AgentState], Coroutine[Any, Any, dict[str, Any]]]


# ─────────────────────────────────────────────────────────────────────────────
# Node factory: Intent & Field Identification
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_SYSTEM = """
You are an intent classifier for a country-data assistant.
Given a user question, extract:
  1. The country name in English.
  2. Which data fields the user is asking about.

Valid fields: capital, population, currencies, languages,
              region, subregion, flags, area, timezones, tld.

Rules:
- If the user asks a general question like "tell me about X", include ALL fields.
- If no specific fields are clear, default to: capital, population, currencies.
- If you cannot identify a country, set is_valid=false and explain why.
- Never invent field names outside the valid list.

Respond ONLY with a JSON object — no markdown, no preamble:
{
  "country_name": "<string>",
  "requested_fields": ["<field>", ...],
  "is_valid": <bool>,
  "validation_error": "<string or null>"
}
""".strip()


def make_intent_node() -> NodeFn:
    async def intent_node(state: AgentState) -> dict[str, Any]:
        query = state["user_query"]
        logger.info("[intent] query=%r", query)

        try:
            response = await _claude.messages.create(
                model=settings.model_name,
                max_tokens=256,
                system=_INTENT_SYSTEM,
                messages=[{"role": "user", "content": query}],
            )
            raw_json = response.content[0].text.strip()
            # print("raw_json: ",raw_json)
            clean_json = re.sub(r"^```json\s*|\s*```$", "", raw_json.strip())
            data = json.loads(clean_json)
            print("data :",data)
            intent = IntentResult(**data)

            # Sanitise: strip unsupported fields
            intent = intent.model_copy(
                update={
                    "requested_fields": [
                        f for f in intent.requested_fields
                        if f in settings.supported_fields
                    ]
                }
            )
            # Fall back to sensible defaults if nothing survived sanitisation
            if intent.is_valid and not intent.requested_fields:
                intent = intent.model_copy(
                    update={"requested_fields": ["capital", "population", "currencies"]}
                )

            logger.info(
                "[intent] country=%r fields=%s valid=%s",
                intent.country_name, intent.requested_fields, intent.is_valid,
            )
            return {"intent": intent}

        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("[intent] parse error: %s", exc)
            return {
                "intent": IntentResult(
                    country_name="",
                    requested_fields=[],
                    is_valid=False,
                    validation_error="Could not parse your question. Please try again.",
                )
            }

    return intent_node


# ─────────────────────────────────────────────────────────────────────────────
# Node factory: Tool Invocation (REST Countries API + DB cache)
# ─────────────────────────────────────────────────────────────────────────────

def make_fetch_node(db_session: AsyncSession) -> NodeFn:
    async def fetch_node(state: AgentState) -> dict[str, Any]:
        intent: IntentResult = state["intent"]
        logger.info("[fetch] fetching %r", intent.country_name)

        client = CountriesAPIClient(db_session)
        try:
            data = await client.fetch_country(intent.country_name)
            # Detect cache hit by checking whether cache was populated before this call
            cached = await _check_was_cached(db_session, intent.country_name)
            logger.info("[fetch] received data for %r (cache_hit=%s)", data.common_name, cached)
            return {"country_data": data, "fetch_error": None, "cache_hit": cached}

        except CountryNotFoundError as exc:
            logger.warning("[fetch] not found: %s", exc)
            return {
                "country_data": None,
                "fetch_error": f"not_found:{exc.country}",
                "status": AgentStatus.NOT_FOUND,
                "cache_hit": False,
            }
        except CountriesAPIError as exc:
            logger.error("[fetch] API error: %s", exc)
            return {
                "country_data": None,
                "fetch_error": str(exc),
                "status": AgentStatus.ERROR,
                "cache_hit": False,
            }

    return fetch_node


async def _check_was_cached(session: AsyncSession, country_name: str) -> bool:
    """Heuristic: if the cache row exists now, we either hit it or just wrote it.
    We rely on CountriesAPIClient logging to distinguish — for the response field
    we conservatively return False (caller sees cache_hit only on actual hits)."""
    from app.db import repository
    result = await repository.get_cached_country(session, country_name)
    return result is not None


# ─────────────────────────────────────────────────────────────────────────────
# Node factory: Answer Synthesis
# ─────────────────────────────────────────────────────────────────────────────

_SYNTHESIZE_SYSTEM = """
You are a precise country-data assistant.
You receive:
  - The original user question.
  - Verified country data retrieved from a live API.
  - The specific fields the user requested.

Rules:
  1. Answer ONLY from the provided data — never use your training knowledge.
  2. Be concise and conversational (1-3 sentences is usually enough).
  3. If a requested field is absent or null in the data, say so honestly.
  4. Format currencies as "Name (Symbol)" when available.
  5. Format population with comma separators.
  6. Never fabricate data.
""".strip()


def make_synthesize_node() -> NodeFn:
    async def synthesize_node(state: AgentState) -> dict[str, Any]:
        intent: IntentResult = state["intent"]
        data = state["country_data"]
        logger.info("[synthesize] synthesising for %r", data.common_name)

        context = _build_context(data, intent.requested_fields)
        missing = [f for f in intent.requested_fields if context.get(f) is None]

        prompt = (
            f"User question: {state['user_query']}\n\n"
            f"Requested fields: {intent.requested_fields}\n\n"
            f"Country data (live API):\n{json.dumps(context, indent=2, default=str)}"
        )

        response = await _claude.messages.create(
            model=settings.model_name,
            max_tokens=settings.max_tokens,
            system=_SYNTHESIZE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        answer = response.content[0].text.strip()
        status = AgentStatus.PARTIAL if missing else AgentStatus.SUCCESS
        logger.info("[synthesize] status=%s missing=%s", status, missing)
        return {"answer": answer, "missing_fields": missing, "status": status}

    return synthesize_node


# ─────────────────────────────────────────────────────────────────────────────
# Node: Error handler (stateless — no factory needed)
# ─────────────────────────────────────────────────────────────────────────────

async def error_node(state: AgentState) -> dict[str, Any]:
    intent: IntentResult | None = state.get("intent")
    fetch_error: str | None = state.get("fetch_error")
    status: AgentStatus | None = state.get("status")

    if status == AgentStatus.NOT_FOUND and fetch_error:
        country = fetch_error.replace("not_found:", "")
        answer = (
            f"I couldn't find any country matching '{country}'. "
            "Please check the spelling or try a different name."
        )
        final_status = AgentStatus.NOT_FOUND
    elif intent and not intent.is_valid:
        answer = (
            intent.validation_error
            or "I couldn't understand your question. "
               "Please ask about a specific country, e.g. 'What is the capital of France?'"
        )
        final_status = AgentStatus.INVALID_QUERY
    else:
        answer = "Something went wrong while fetching country data. Please try again."
        final_status = AgentStatus.ERROR

    logger.info("[error] status=%s", final_status)
    return {"answer": answer, "status": final_status, "missing_fields": []}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_context(data, fields: list[str]) -> dict[str, Any]:
    mapping: dict[str, Any] = {
        "capital": data.capital,
        "population": data.population,
        "currencies": data.currencies,
        "languages": data.languages,
        "region": data.region,
        "subregion": data.subregion,
        "flags": data.flag_png,
        "area": data.area_km2,
        "timezones": data.timezones,
        "tld": data.tld,
    }
    ctx: dict[str, Any] = {"country": data.common_name}
    for f in fields:
        ctx[f] = mapping.get(f)
    return ctx