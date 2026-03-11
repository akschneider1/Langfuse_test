# Langfuse v3 Self-Hosted (Replit)

Self-hosted [Langfuse v3](https://langfuse.com) setup with Docker Compose, configured for Replit, plus Python scripts to seed and stream test data.

## What's Included

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full v3 stack: Langfuse web + worker, Postgres, ClickHouse, Redis, MinIO |
| `start.sh` | One-command startup (installs deps, launches all services) |
| `scripts/seed_test_data.py` | Batch-create realistic traces, spans, generations, and scores |
| `scripts/stream_test_data.py` | Continuously stream traces at a configurable rate |
| `scripts/test_api_direct.py` | Raw REST API examples (no SDK) |

## Architecture (Langfuse v3)

```
                    ┌──────────────────┐
         port 3000  │  langfuse-web    │  UI + API
                    │  (langfuse:3)    │
                    └────────┬─────────┘
                             │
                    ┌────────┴─────────┐
                    │  langfuse-worker  │  Async event processing
                    │  (langfuse-      │
                    │   worker:3)      │
                    └──┬───┬───┬───┬───┘
         ┌─────────────┘   │   │   └──────────────┐
         ▼                 ▼   ▼                   ▼
  ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐
  │  Postgres   │  │ ClickHouse │  │  Redis   │  │  MinIO   │
  │  (port 5432)│  │ (port 8123)│  │ (6379)   │  │ (9090)   │
  │  Relational │  │  OLAP for  │  │ Queue +  │  │ S3 blob  │
  │  data       │  │  traces    │  │ cache    │  │ storage  │
  └─────────────┘  └────────────┘  └──────────┘  └──────────┘
```

## Quick Start

### 1. Start Langfuse

```bash
bash start.sh
```

This spins up all 6 services. First run pulls images and may take a few minutes.

### 2. Create a Project

1. Open `http://localhost:3000` (or your Replit URL)
2. Sign up for an account (first user becomes admin)
3. Create a new project
4. Go to **Settings → API Keys** and copy your public/secret keys

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env and paste your keys
```

### 4. Feed Test Data

```bash
# Batch seed — creates 20 traces with spans, generations, and scores
python scripts/seed_test_data.py

# Seed more traces
python scripts/seed_test_data.py --count 100

# Stream continuously at 2 traces/sec, stop after 500
python scripts/stream_test_data.py --rate 2 --limit 500

# Stream indefinitely at 1/sec (Ctrl+C to stop)
python scripts/stream_test_data.py

# Test the REST API directly (no SDK)
python scripts/test_api_direct.py
```

## What the Test Data Covers

- **Traces** across multiple use cases: chatbot, code-assistant, RAG Q&A, summarization, translation, content generation
- **Nested spans**: pipeline → preprocessing → LLM call → post-processing
- **Generations** with model info, token usage, latency, and parameters
- **Scores**: quality, relevance, and simulated user feedback
- **Error simulation**: ~5% of streamed traces include errors
- **Sessions and users**: grouped by session and user IDs for dashboard testing

## Useful Commands

```bash
# View logs (all services)
docker-compose logs -f

# View only the web server logs
docker-compose logs -f langfuse-web

# View worker logs
docker-compose logs -f langfuse-worker

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Stop and delete ALL data (Postgres, ClickHouse, MinIO, Redis)
docker-compose down -v
```

## Resource Requirements

Langfuse v3 recommends at least **2 CPUs and 4 GB RAM** for the full stack. On Replit, use a plan that provides sufficient resources for Docker.
