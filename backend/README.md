# Backend Service

## Prerequisites
- Python 3.11+
- PostgreSQL (local or remote)
- Redis (for Celery tasks)

## Setup
1. Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

2. Create a `.env` file in `backend/`:

```env
DEBUG=false
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me
```

## Run (local)

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Celery (optional)

```bash
cd backend
celery -A app.workers.celery_app worker -l info
```

## Docs

- Model notes: `backend/docs/models.md`
- Team task assignment: `backend/docs/task_assignment.md`
