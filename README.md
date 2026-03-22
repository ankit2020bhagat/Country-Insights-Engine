# Country-Insights-Engine
A production-grade AI agent that answers natural-language questions about countries. Built with LangGraph, FastAPI, and PostgreSQL, backed by the public REST Countries API.

Table of Contents

Overview
Tech Stack
Project Structure
Architecture
Business Logic
API Reference
Database Schema
Getting Started
Running Tests
Test Case Breakdown
Design Decisions
Environment Variables


Overview
Users ask plain English questions like:
"What is the population of Germany?"
"What currency does Japan use?"
"What is the capital and population of Brazil?"
The agent parses the question, fetches live data from the REST Countries API (with a PostgreSQL-backed cache), and returns a grounded, accurate answer — never relying on the LLM's training knowledge for factual data.

Tech Stack
LayerTechnologyAPI frameworkFastAPIAgent orchestrationLangGraphLLMAnthropic Claude (claude-sonnet-4)DatabasePostgreSQL (via SQLAlchemy async + asyncpg)MigrationsAlembicHTTP clienthttpx (async)ValidationPydantic v2 + pydantic-settingsTestspytest + pytest-asyncioContainerisationDocker + docker-compose

Project Structure
country_agent/
├── app/
│   ├── main.py                    # FastAPI app factory, lifespan hooks
│   ├── config.py                  # All settings via pydantic-settings
│   ├── agent/
│   │   ├── state.py               # AgentState TypedDict (shared graph state)
│   │   ├── nodes.py               # Node factories: intent, fetch, synthesize, error
│   │   └── graph.py               # LangGraph topology + run_agent() entry point
│   ├── api/
│   │   └── routes/
│   │       ├── query.py           # POST /query
│   │       ├── history.py         # GET /history, GET /history/{id}, POST /admin/cache/purge
│   │       └── health.py          # GET /health
│   ├── db/
│   │   ├── models.py              # SQLAlchemy ORM: QueryLog, CountryCache
│   │   ├── repository.py          # All SQL — nodes and routes are SQL-free
│   │   └── session.py             # Async engine, get_db() FastAPI dependency
│   ├── models/
│   │   └── schemas.py             # All Pydantic models (internal + API contracts)
│   └── tools/
│       └── countries_api.py       # Async REST Countries client + DB cache logic
├── alembic/
│   ├── env.py                     # Alembic async-compatible config
│   └── versions/
│       └── 0001_initial_schema.py # Initial migration: query_log + country_cache
├── tests/
│   ├── test_agent.py              # Unit tests: nodes, routing predicates
│   ├── test_api.py                # Integration tests: FastAPI endpoints
│   └── test_repository.py        # DB layer tests: SQLite in-memory
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
└── requirements.txt

Architecture
HTTP Request (POST /query)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI — routes/query.py                                  │
│  • Validates request body (Pydantic)                        │
│  • Starts request timer                                     │
│  • Calls run_agent(query, db_session)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  LangGraph Compiled Graph                                   │
│                                                             │
│  START                                                      │
│    │                                                        │
│    ▼                                                        │
│  [Node 1] intent_node                                       │
│    Claude parses the query into structured JSON             │
│    → IntentResult { country_name, requested_fields }        │
│    │                                                        │
│    ├── is_valid=False ──────────────────► error_node        │
│    │                                          │             │
│    ▼                                          ▼             │
│  [Node 2] fetch_node                         END            │
│    1. Check country_cache (PostgreSQL)                      │
│    2. On miss → GET restcountries.com (retry ×2)            │
│    3. Write result to cache (TTL 24h)                       │
│    → CountryData                                            │
│    │                                                        │
│    ├── 404 / error ─────────────────────► error_node        │
│    │                                                        │
│    ▼                                                        │
│  [Node 3] synthesize_node                                   │
│    Claude answers using ONLY the API data                   │
│    → answer string + missing_fields list                    │
│    │                                                        │
│    ▼                                                        │
│   END                                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Post-agent (FastAPI route)                                 │
│  • Write QueryLog row to PostgreSQL (audit trail)           │
│  • Return QueryResponse JSON                                │
└─────────────────────────────────────────────────────────────┘
