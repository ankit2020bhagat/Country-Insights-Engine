
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent
from app.config import get_settings
from app.db.repository import create_query_log
from app.db.session import get_db
from app.db.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "",
    response_model=QueryResponse,
    summary="Ask a question about a country",
    status_code=status.HTTP_200_OK,
)
async def ask_country_question(
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """
    Run the LangGraph agent against the user's natural-language question
    and return a grounded answer backed by the REST Countries API.

    The request is persisted to the `query_log` table regardless of outcome.
    """
    start = time.monotonic()

    try:
        agent_response = await run_agent(body.query, db)
    except Exception as exc:
        logger.exception("Unhandled agent error for query=%r", body.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        ) from exc

    duration_ms = int((time.monotonic() - start) * 1000)

    # Persist audit log (best-effort — don't fail the response if logging fails)
    try:
        log_row = await create_query_log(
            db,
            user_query=body.query,
            country_name=agent_response.country,
            requested_fields=agent_response.requested_fields,
            status=agent_response.status.value,
            answer=agent_response.answer,
            missing_fields=agent_response.missing_fields,
            duration_ms=duration_ms,
        )
        query_id = log_row.id
    except Exception:
        logger.exception("Failed to write query_log — continuing")
        query_id = uuid.uuid4()

    return QueryResponse(
        query_id=query_id,
        status=agent_response.status,
        answer=agent_response.answer,
        country=agent_response.country,
        requested_fields=agent_response.requested_fields,
        missing_fields=agent_response.missing_fields,
        cache_hit=agent_response.cache_hit,
        duration_ms=duration_ms,
    )