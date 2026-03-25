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
. .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
```

若系统默认 `python` 版本低于 3.11（例如仍为 3.8），在 Windows 上可用已安装的 3.11+ 显式创建虚拟环境：`py -3.13 -m venv .venv`（版本号按本机 `py -0p` 输出调整）。

2. 在 `backend/` 准备 `.env`（首次可复制模板并改库名/账号）：

```powershell
copy .env.example .env
```

至少设置 `DATABASE_URL`（示例：`postgresql+psycopg://USER:PASS@localhost:5432/lovemediator_dev`）。PostgreSQL 中只需建空库，表结构由迁移创建。

## Database migrations

在已激活的虚拟环境中、且数据库已可连接时：

```bash
python -m alembic upgrade head
python -m alembic current   # 应显示当前 revision，与最新迁移一致即成功
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
