# Uli

Uli 是一个面向真实亲密关系冲突场景的 AI 仲裁与复盘产品，当前仓库包含：

- `backend/`：FastAPI 后端服务、数据模型、AI 调用与异步任务入口
- `fontend/`：React + Vite 前端应用
- `docs/`：架构、API、数据库、功能与前端技术文档

## 当前状态

- 项目品牌名已从 `LoveMediator` 统一切换为 `Uli`
- 前端显示名、OpenAPI 标题、后端 AI 提示词、示例配置与核心文档文件名都已同步更新
- 前端持久化 key 已切换为 `uli-auth` / `uli-app`，并保留从旧 `love-mediator-*` key 的自动迁移

## 快速开始

### 后端

进入 `backend/` 后按 [backend/README.md](backend/README.md) 启动：

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
copy .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

进入 `fontend/` 后按 [fontend/README.md](fontend/README.md) 启动：

```bash
pnpm install
pnpm run dev
```

默认前端开发环境通过 `VITE_API_PROXY_TARGET=http://localhost:8000` 代理到本地后端。

## 关键文档

- [架构文档](docs/Uli_ARCH.md)
- [API 文档](docs/API_Uli_v1.md)
- [数据库文档](docs/DB_Uli_v1.md)
- [功能文档](docs/FD_Uli_v1.md)
- [前端技术文档](docs/FE_Uli_v1.md)

## 已记录但暂不处理的风险

### 1. Docker / 本地数据库兼容性

当前示例配置已经切换到 `uli_dev`、`uli_pgdata`、`uli-postgres` 等新命名。
这意味着如果开发者直接使用新版 `backend/docker-compose.yml`，可能会挂到一个全新的本地数据库/卷，而不是继续复用旧的 `lovemediator_*` 开发数据。

相关文件：

- [backend/docker-compose.yml](backend/docker-compose.yml)
- [backend/.env.example](backend/.env.example)

### 2. 前端持久化迁移缺少自动化测试

浏览器本地数据会从旧 key 自动迁移到新的 `uli-*` key，但目前这条迁移路径还没有自动化测试覆盖。
如果后续调整 store 初始化顺序或 persist 配置，存在回归后才在手工联调中暴露的风险。

相关文件：

- [fontend/src/shared/lib/persist-migration.ts](fontend/src/shared/lib/persist-migration.ts)
- [fontend/src/app/model/app-store.ts](fontend/src/app/model/app-store.ts)
- [fontend/src/domains/auth/model/auth-store.ts](fontend/src/domains/auth/model/auth-store.ts)

## 说明

- 仓库目录名当前仍是 `g:\\loveMediator`，这是有意保留，未纳入本轮改名范围
- `fontend/` 目录拼写也仍保持现状，避免把本次品牌名调整和目录级重构混在一起
