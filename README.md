# RegTech — AI-Powered Regulatory Compliance System

Organizations upload policy/SOP documents; the system ingests regulatory corpora (RBI, SEBI, IRDAI, GDPR, ISO), retrieves relevant clauses via semantic search, and evaluates compliance with risk scoring and report generation.

## Tech Stack

- **Backend:** Python 3.11, FastAPI
- **Vector DB:** Qdrant
- **Embeddings:** BAAI/bge-large-en-v1.5 (Sentence Transformers)
- **Database:** PostgreSQL + SQLAlchemy
- **Tasks:** Celery + Redis
- **PDF:** PyMuPDF, pdfplumber, Unstructured

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start infrastructure
docker compose up -d postgres redis qdrant

# 3. Install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn main:app --reload

# 6. Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info -Q ingestion,embedding,compliance,reports
```

Or run everything with Docker:

```bash
docker compose up --build
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Project Structure

```
app/
├── api/           # HTTP routes, schemas, middleware
├── core/          # Config, logging, exceptions, security
├── domain/        # Entities, value objects, port interfaces
├── ingestion/     # PDF → clauses pipeline
├── embeddings/    # Model loading & batch embedding
├── vectordb/      # Qdrant client & collections
├── retrieval/     # Semantic & hybrid search
├── compliance/    # Evaluation, scoring, rules
├── reports/       # JSON & PDF report generation
├── models/        # SQLAlchemy ORM
├── services/      # Application use-case layer
├── database/      # Engine, sessions, repositories
└── workers/       # Celery tasks
```

## API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/health/ready` | Readiness (DB, Qdrant, Redis) |
| POST | `/api/v1/regulations/upload` | Upload regulatory PDF |
| GET | `/api/v1/regulations` | List regulations |
| GET | `/api/v1/regulations/{id}` | Get regulation detail |
| POST | `/api/v1/documents/upload` | Upload org document |
| GET | `/api/v1/documents` | List org documents |
| POST | `/api/v1/compliance/evaluate` | Start compliance evaluation |
| GET | `/api/v1/compliance/runs/{id}` | Get evaluation run |
| GET | `/api/v1/compliance/runs/{id}/findings` | List findings |
| POST | `/api/v1/reports/generate` | Generate compliance report |
| GET | `/api/v1/reports/{id}` | Download report |

## Development

```bash
# Lint
ruff check app tests

# Type check
mypy app

# Tests
pytest
```

## License

Proprietary — All rights reserved.
