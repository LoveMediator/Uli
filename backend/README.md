# Backend Service

## Prerequisites
- Python 3.11+
- PostgreSQL（本机安装 **或** 下文 Docker Compose）
- Redis（本机安装 **或** Docker；仅跑 API 可先不配 Celery）

## Docker（推荐：一键 PostgreSQL + Redis）

在 `backend/` 目录：

```bash
docker compose up -d
```

默认映射：**PostgreSQL `localhost:5433`**，**Redis `localhost:6380`**（避免与本机 5432/6379 冲突）。  
等待 `healthy` 后，将 `.env` 中的 `DATABASE_URL` / `REDIS_URL` 与 `.env.example` 中 Docker 示例保持一致，再执行迁移。

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

至少设置 `DATABASE_URL`；若用 Docker 则直接复制 `.env.example` 即可。  
联调前端时建议设置 `CORS_ORIGINS`（模板已含 Vite 默认源）。  
（不用 Docker 时）在本机 PostgreSQL 中建空库 `lovemediator_dev`，表结构由迁移创建。

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

健康检查：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready   # 需 PostgreSQL 可连，否则 503
```

## Celery (optional)

```bash
cd backend
celery -A app.workers.celery_app worker -l info
```

## Docs

- Model notes: `backend/docs/models.md`
- Team task assignment: `backend/docs/task_assignment.md`
