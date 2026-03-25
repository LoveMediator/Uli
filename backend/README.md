# Backend Service

## Prerequisites
- Python 3.11+
- **本机 PostgreSQL**（默认 `localhost:5432`；用 pgAdmin 建空库 `lovemediator_dev`）
- Redis（本机 `6379` 或下文 Docker；仅跑 HTTP API 可先不启）

## 本机库（推荐默认流程）

1. 启动 PostgreSQL 服务，在 pgAdmin 中 **Create Database** → 名称 **`lovemediator_dev`**（只建库，不手建表）。
2. `cd backend`，复制环境变量并改密码：

```powershell
copy .env.example .env
```

编辑 `.env`：把 `DATABASE_URL` 里的 **`你的密码`** 改成安装 PostgreSQL 时设置的密码（用户名若不是 `postgres` 一并修改）。
3. 虚拟环境与依赖（首次）：

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell
pip install -U pip
pip install -e .
```

若默认 `python` 低于 3.11，可用：`py -3.13 -m venv .venv`。

4. 迁移并启动：

```bash
python -m alembic upgrade head
python -m alembic current
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. 健康检查：

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready   # 需数据库可连，否则 503
```

## Docker（可选：无本机 PostgreSQL 时）

在 `backend/`：

```bash
docker compose up -d
```

使用映射端口 **5433 / 6380**，将 `.env` 改为 `.env.example` 注释块中的 Docker 版 `DATABASE_URL` / `REDIS_URL`，再执行迁移。

## Celery (optional)

```bash
cd backend
celery -A app.workers.celery_app worker -l info
```

## Docs

- Model notes: `backend/docs/models.md`
- Team task assignment: `backend/docs/task_assignment.md`
