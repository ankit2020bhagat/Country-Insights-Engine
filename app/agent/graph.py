
from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.nodes import (
    error_node,
    make_fetch_node,
    make_intent_node,
    make_synthesize_node,
)
from app.agent.state import AgentState
from app.db.schemas import AgentResponse, AgentStatus

logger = logging.getLogger(__name__)



def _route_after_intent(state: AgentState) -> str:
    intent = state.get("intent")
    if not intent or not intent.is_valid:
        return "error_node"
    return "fetch_node"


def _route_after_fetch(state: AgentState) -> str:
    if state.get("country_data") is not None:
        return "synthesize_node"
    return "error_node"



def build_graph(db_session: AsyncSession) -> StateGraph:

    intent_node = make_intent_node()
    fetch_node = make_fetch_node(db_session)
    synthesize_node = make_synthesize_node()

    graph = StateGraph(AgentState)
    graph.add_node("intent_node", intent_node)
    graph.add_node("fetch_node", fetch_node)
    graph.add_node("synthesize_node", synthesize_node)
    graph.add_node("error_node", error_node)

    graph.add_edge(START, "intent_node")
    graph.add_conditional_edges(
        "intent_node",
        _route_after_intent,
        {"fetch_node": "fetch_node", "error_node": "error_node"},
    )
    graph.add_conditional_edges(
        "fetch_node",
        _route_after_fetch,
        {"synthesize_node": "synthesize_node", "error_node": "error_node"},
    )
    graph.add_edge("synthesize_node", END)
    graph.add_edge("error_node", END)

    return graph.compile()




async def run_agent(user_query: str, db_session: AsyncSession) -> AgentResponse:

    logger.info("[run_agent] START query=%r", user_query)

    compiled = build_graph(db_session)

    initial: AgentState = {
        "user_query": user_query,
        "intent": None,
        "country_data": None,
        "fetch_error": None,
        "cache_hit": False,
        "answer": None,
        "missing_fields": [],
        "status": None,
    }

    final: AgentState = await compiled.ainvoke(initial)

    intent = final.get("intent")
    result = AgentResponse(
        status=final.get("status") or AgentStatus.ERROR,
        answer=final.get("answer") or "No answer produced.",
        country=intent.country_name if intent and intent.is_valid else None,
        requested_fields=intent.requested_fields if intent else [],
        missing_fields=final.get("missing_fields") or [],
        raw_country_data=final.get("country_data"),
        cache_hit=final.get("cache_hit", False),
    )

    logger.info(
        "[run_agent] END status=%s country=%r cache_hit=%s",
        result.status, result.country, result.cache_hit,
    )
    return result