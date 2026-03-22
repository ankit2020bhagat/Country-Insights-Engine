
# 🌍 Country-Insights-Engine

**A production-grade AI agent that answers natural-language questions about countries**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Anthropic](https://img.shields.io/badge/Claude-Sonnet_4-D4451A?style=flat-square)](https://anthropic.com)
[![Tests](https://img.shields.io/badge/Tests-25_passed-22C55E?style=flat-square)](./tests)
[![Deploy](https://img.shields.io/badge/Deploy-Fly.io-8B5CF6?style=flat-square&logo=fly.io&logoColor=white)](https://fly.io)

<br/>

```bash
curl -X POST https://your-app.fly.dev/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What currency does Japan use?"}'
```

```json
{
  "status": "success",
  "answer": "Japan uses the Japanese Yen (¥).",
  "country": "Japan",
  "cache_hit": false,
  "duration_ms": 743
}
```

</div>

---

## What It Does

Ask plain English questions about any country. The agent fetches live data from the [REST Countries API](https://restcountries.com) and returns a grounded answer — never guessing from the LLM's training knowledge.

| Question | Answer |
|---|---|
| *"What is the population of Germany?"* | Germany's population is approximately 83,240,525. |
| *"What currency does Japan use?"* | Japan uses the Japanese Yen (¥). |
| *"Capital and population of Brazil?"* | The capital of Brazil is Brasília, with a population of ~214,326,223. |
| *"What languages are spoken in Switzerland?"* | Switzerland has four official languages: German, French, Italian, and Romansh. |
| *"Tell me about New Zealand"* | New Zealand is located in Oceania, covers 268,838 km², and uses the NZ Dollar (NZ$). |

---

## Architecture

```
POST /query
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI                                             │
│  Validates · times the request · calls run_agent()  │
└─────────────────────┬────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────┐
│  LangGraph Graph                                     │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Node 1 — Intent                              │   │
│  │ Claude parses query → {country, fields}      │   │
│  └──────────────────┬─────────────────────────  ┘   │
│           valid     │         invalid                │
│                     ▼               ▼                │
│  ┌─────────────────────────┐  ┌────────────┐        │
│  │ Node 2 — Fetch          │  │ error_node │        │
│  │ 1. Check Postgres cache │  └────────────┘        │
│  │ 2. GET restcountries.com│                        │
│  │ 3. Write back to cache  │                        │
│  └───────────┬─────────────┘                        │
│      found   │     404 / error                      │
│              ▼               ▼                      │
│  ┌────────────────────┐  ┌────────────┐             │
│  │ Node 3 — Synthesize│  │ error_node │             │
│  │ Claude answers from│  └────────────┘             │
│  │ API data only —    │                             │
│  │ not from training  │                             │
│  └────────────────────┘                             │
└─────────────────────┬────────────────────────────────┘
                      │
                      ▼
       Write audit log → PostgreSQL (query_log)
                      │
                      ▼
               QueryResponse JSON
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| LLM | [Anthropic Claude Sonnet 4](https://anthropic.com) |
| Database | [PostgreSQL](https://postgresql.org) via [SQLAlchemy async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) + [asyncpg](https://github.com/MagicStack/asyncpg) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org) |
| HTTP client | [httpx](https://www.python-httpx.org) (async, with retry) |
| Validation | [Pydantic v2](https://docs.pydantic.dev) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Tests | [pytest](https://pytest.org) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io) |
| Deployment | [Fly.io](https://fly.io) (Docker + managed Postgres) |

---

## Project Structure

```
country_agent/
├── app/
│   ├── main.py                    # FastAPI factory + lifespan hooks
│   ├── config.py                  # All settings — reads .env locally, Fly secrets in prod
│   │
│   ├── agent/
│   │   ├── state.py               # AgentState TypedDict — shared across all nodes
│   │   ├── nodes.py               # Node factories: intent, fetch, synthesize, error
│   │   └── graph.py               # LangGraph topology + run_agent() entry point
│   │
│   ├── api/routes/
│   │   ├── query.py               # POST /query
│   │   ├── history.py             # GET /history · GET /history/{id} · POST /admin/cache/purge
│   │   └── health.py              # GET /health
│   │
│   ├── db/
│   │   ├── models.py              # ORM models: QueryLog, CountryCache
│   │   ├── repository.py          # All SQL lives here — nodes and routes are SQL-free
│   │   └── session.py             # Async engine + get_db() FastAPI dependency
│   │
│   ├── models/
│   │   └── schemas.py             # All Pydantic models (API contracts + internal)
│   │
│   └── tools/
│       └── countries_api.py       # Async REST Countries client + PostgreSQL cache logic
│
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py # Creates query_log + country_cache tables
│
├── tests/
│   ├── test_agent.py              # 15 node & routing unit tests (fully mocked)
│   ├── test_api.py                # FastAPI endpoint integration tests
│   └── test_repository.py        # 10 DB layer tests (SQLite in-memory)
│
├── fly.toml                       # Fly.io deployment config
├── deploy.sh                      # One-shot deploy script
├── Dockerfile
├── docker-compose.yml             # Local dev with Postgres
├── .env.example
└── requirements.txt
```

---

## Quick Start

### Option 1 — Docker (recommended for local dev)

```bash
git clone https://github.com/your-username/country-agent.git
cd country-agent

cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

docker compose up --build
```

- API: **http://localhost:8000**
- Swagger docs: **http://localhost:8000/docs**

---

### Option 2 — Local without Docker

```bash
# Requires Python 3.12+ and a running PostgreSQL instance

git clone https://github.com/your-username/country-agent.git
cd country-agent

pip install -r requirements.txt

cp .env.example .env
# Set ANTHROPIC_API_KEY + Postgres credentials in .env

createdb country_agent
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

---

### Option 3 — Deploy to Fly.io

```bash
brew install flyctl          # macOS
# curl -L https://fly.io/install.sh | sh  (Linux)

fly auth login

# Edit APP_NAME in deploy.sh to something unique, then:
ANTHROPIC_API_KEY="sk-ant-..." ./deploy.sh
```

Your live URL: `https://your-app-name.fly.dev`

Full details in the [Fly.io section](#deploying-to-flyio) below.

---

## API Reference

### `POST /query`

Run the agent on a natural-language question.

**Request**
```json
{ "query": "What is the capital and population of Brazil?" }
```

**Response**
```json
{
  "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "success",
  "answer": "The capital of Brazil is Brasília, and its population is approximately 214,326,223.",
  "country": "Brazil",
  "requested_fields": ["capital", "population"],
  "missing_fields": [],
  "cache_hit": false,
  "duration_ms": 812
}
```

**Status values**

| Value | Meaning |
|---|---|
| `success` | All requested fields answered from live data |
| `partial` | Answer returned but some fields were absent in the API |
| `not_found` | Country not recognised by the REST Countries API |
| `invalid_query` | No country could be identified in the query |
| `error` | Upstream API or internal failure |

---

### `GET /history`

Paginated query audit log.

```
GET /history?limit=20&offset=0&status=success&country=Japan
```

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 20 | Rows per page (max 200) |
| `offset` | int | 0 | Pagination offset |
| `status` | string | — | Filter by status value |
| `country` | string | — | Partial country name match |

---

### `GET /history/{query_id}`

Single audit log entry by UUID.

---

### `GET /health`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "db": "ok"
}
```

---

### `POST /admin/cache/purge`

Delete all expired rows from `country_cache`.

```json
{ "deleted": 14 }
```

---

## Database Schema

### `query_log` — immutable audit trail

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` PK | Auto-generated |
| `created_at` | `timestamptz` | Indexed |
| `user_query` | `text` | Raw user input |
| `country_name` | `varchar(120)` | Null when query is invalid |
| `requested_fields` | `JSON` | e.g. `["capital", "population"]` |
| `status` | `varchar(32)` | Indexed |
| `answer` | `text` | Final answer text |
| `missing_fields` | `JSON` | Fields absent in API response |
| `duration_ms` | `int` | End-to-end latency |

### `country_cache` — 24-hour TTL cache

| Column | Type | Notes |
|---|---|---|
| `id` | `int` PK | Auto-increment |
| `country_key` | `varchar(120)` UNIQUE | Lowercased name, indexed |
| `cached_at` | `timestamptz` | Write timestamp |
| `expires_at` | `timestamptz` | `cached_at + 24h`, indexed |
| `data` | `JSON` | Full `CountryData` blob |

---

## Running Tests

No live Postgres, no REST API, and no Anthropic API key required.

```bash
# All 25 tests
pytest tests/ -v

# By file
pytest tests/test_agent.py -v       # node + routing unit tests
pytest tests/test_repository.py -v  # DB layer (SQLite in-memory)
pytest tests/test_api.py -v         # FastAPI integration tests
```

**Coverage breakdown**

| Suite | Count | Covers |
|---|---|---|
| `test_agent.py` | 15 | Intent parsing, field sanitisation, bad JSON fallback, fetch 200/404/error, synthesis success/partial, all 5 routing predicates |
| `test_repository.py` | 10 | QueryLog CRUD, pagination, status filter, cache miss/hit/expiry, case-insensitive lookup, upsert conflict, TTL purge |
| `test_api.py` | 6 | Happy path, not found, invalid query, Pydantic validation rejection, health check |

---

## Deploying to Fly.io

### Prerequisites

- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed and logged in
- A [Fly.io account](https://fly.io) (free tier is enough)
- Your Anthropic API key

### One-command deploy

```bash
# 1. Set a unique app name in deploy.sh
nano deploy.sh   # change APP_NAME="country-agent-yourname"

# 2. Run
ANTHROPIC_API_KEY="sk-ant-..." ./deploy.sh
```

The script does the following automatically:

| Step | What happens |
|---|---|
| 1 | Creates the Fly app |
| 2 | Provisions a Postgres cluster (1 GB, shared-cpu-1x) |
| 3 | Attaches Postgres — sets `DATABASE_URL` secret automatically |
| 4 | Sets `ANTHROPIC_API_KEY` secret |
| 5 | Builds Docker image remotely on Fly's builders |
| 6 | Runs `alembic upgrade head` on first container start |
| 7 | Prints your live URL |

### Manual deploy (step by step)

```bash
fly auth login

fly apps create your-app-name --machines

fly postgres create \
  --name your-app-db \
  --region sin \
  --vm-size shared-cpu-1x \
  --volume-size 1

fly postgres attach your-app-db --app your-app-name

fly secrets set ANTHROPIC_API_KEY="sk-ant-..." --app your-app-name

fly deploy --app your-app-name --remote-only
```

### Useful Fly commands

```bash
fly logs --app your-app-name                          # live log stream
fly status --app your-app-name                        # machine health
fly ssh console --app your-app-name                   # SSH into container
fly scale count 2 --app your-app-name                 # scale up
fly ssh console -C "alembic upgrade head"             # run migration manually
```

### Regions

Edit `primary_region` in `fly.toml` or `deploy.sh`:

| Code | Location |
|---|---|
| `sin` | Singapore |
| `bom` | Mumbai |
| `nrt` | Tokyo |
| `syd` | Sydney |
| `lhr` | London |
| `iad` | Washington DC |
| `ord` | Chicago |
| `fra` | Frankfurt |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic key (`sk-ant-...`) |
| `DATABASE_URL` | Fly.io only | — | Auto-set by `fly postgres attach` |
| `POSTGRES_HOST` | Local dev | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | Local dev | `5432` | PostgreSQL port |
| `POSTGRES_DB` | Local dev | `country_agent` | Database name |
| `POSTGRES_USER` | Local dev | `postgres` | DB username |
| `POSTGRES_PASSWORD` | Local dev | `postgres` | DB password |
| `ENVIRONMENT` | — | `development` | `development` · `staging` · `production` |
| `LOG_LEVEL` | — | `INFO` | Python log level |
| `MODEL_NAME` | — | `claude-sonnet-4-20250514` | Claude model |
| `MAX_TOKENS` | — | `512` | Max tokens for synthesis responses |
| `HTTP_TIMEOUT_SECONDS` | — | `10.0` | Upstream API request timeout |
| `HTTP_MAX_RETRIES` | — | `2` | Retry attempts on transient failures |

```bash
cp .env.example .env   # for local development
```

---

## Key Design Decisions

**Grounded synthesis.** The synthesize node passes only the data returned by the REST Countries API to Claude. Claude is explicitly instructed not to use training knowledge. Even if Claude "knows" a population figure, it must use the verified API value.

**PostgreSQL-backed TTL cache.** Upstream API responses are cached for 24 hours. Repeated queries return in ~100ms instead of ~800ms, and the service stays functional during upstream outages within the TTL window.

**Per-request DB session.** SQLAlchemy async sessions must not be shared across requests. The LangGraph graph is compiled fresh per-request with the session injected via closure — keeping connection lifecycle clean and every node independently testable.

**Repository pattern.** All SQL lives in `app/db/repository.py`. Nodes and routes call named functions. The storage layer can be swapped by editing one file.

**Node factories for dependency injection.** Nodes that need I/O are produced by factory functions that close over their dependencies. Unit tests call the factory with mocks — no module-level patching required.

**Immutable audit log.** Every invocation writes to `query_log` regardless of outcome. The write is best-effort — a log failure never surfaces as an API error to the caller.

---

## Contributing

```bash
git clone https://github.com/your-username/country-agent.git
cd country-agent
pip install -r requirements.txt
cp .env.example .env

pytest tests/ -v   # must pass before opening a PR
```

---

## License

MIT
>>>>>>> 52e5ba4595f3e86c5534b9f962248decb79ebe3b
