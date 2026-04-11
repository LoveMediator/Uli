# Uli

Uli 是一个面向真实亲密关系冲突场景的 AI 仲裁与复盘项目。它不是泛化聊天机器人，而是围绕“争吵发生后，如何帮助双方整理事实、生成裁判结果、沉淀复盘记录并继续沟通”这一主链路构建的完整 Web 产品。

当前仓库是一个前后端分离的单体仓库，包含：

- `backend/`：FastAPI 后端服务、数据库模型、业务服务、AI 调用与异步任务骨架
- `fontend/`：React + Vite 前端应用
- `docs/`：架构、API、数据库、功能和前端技术文档

## 1. 项目目标

Uli 当前主要解决 4 类问题：

1. 让 A 先通过私有分析会话把事件整理成可确认的事实快照，而不是直接把情绪抛给对方。
2. 让 B 通过邀请链接查看 `Snapshot_A`，并选择“直接同意”或“补充自己的版本”。
3. 在双方输入基础上调用 AI 生成结构化裁判结果，并进一步生成可编辑的复盘内容。
4. 将已完成事件沉淀到“吵架日历”，形成可复查、可编辑、可延续的关系资产。

## 2. 核心能力

- 用户注册、登录、刷新 token、登出
- 关系邀请、接受邀请、关系列表
- A / B 双侧私有分析会话
- 快照冻结与事件状态流转
- AI 裁判结果生成
- 复盘聊天（follow-up）
- 吵架日历、复盘详情与复盘编辑
- 互动模块：代转达与过激语言柔化

## 3. 系统架构概览

### 3.1 总体架构

```text
React + Vite SPA
  -> Axios API Client
  -> FastAPI /api/v1
  -> Service / Repo / Model layers
  -> PostgreSQL

Private analysis session state
  -> Redis

Long-running / async capability skeleton
  -> Celery + Redis

LLM integration
  -> Kimi-compatible HTTP API
```

### 3.2 架构特点

- 前后端完全分离，前端通过 `/api/v1` 调用后端。
- 后端采用典型分层结构：`api -> service -> repo -> model`。
- 统一响应使用 envelope 结构，便于前端集中处理错误与状态。
- 私有分析会话不直接落正式业务表，而是先放在 Redis，只有 commit 后才进入 `events` / `event_snapshots` 主链路。
- 裁判结果与复盘内容是两个连续步骤：先生成 `judge_results`，再创建 `reviews` 和 `calendar_entries`。

## 4. 仓库结构

```text
.
|- backend/                  # FastAPI backend
|  |- app/
|  |  |- api/               # 路由、依赖注入、异常处理
|  |  |- constants/         # 枚举、错误码
|  |  |- core/              # 配置、安全、日志、Redis/Kimi 客户端
|  |  |- db/                # Engine、Session、Base
|  |  |- models/            # SQLAlchemy 模型
|  |  |- repos/             # 数据访问层
|  |  |- schemas/           # Pydantic 请求/响应结构
|  |  |- services/          # 业务编排、AI 调用、状态流转
|  |  |- utils/             # 权限、ID、上下文等工具
|  |  `- workers/           # Celery 骨架
|  |- alembic/              # 数据库迁移
|  |- tests/                # API / service / schema 测试
|  `- scripts/              # 种子数据等脚本
|- fontend/                 # React frontend（目录名当前保留现状）
|  |- src/
|  |  |- app/               # router、providers、应用级 store
|  |  |- domains/           # 按业务域拆分：auth/home/mediation/calendar/invite/profile
|  |  `- shared/            # 通用 API、布局、组件、样式、工具
|  |- public/
|  `- build/                # Vite chunking 辅助脚本
|- docs/
|  |- Uli_ARCH.md
|  |- API_Uli_v1.md
|  |- DB_Uli_v1.md
|  |- FD_Uli_v1.md
|  `- FE_Uli_v1.md
`- README.md
```

## 5. 技术栈

### 5.1 前端技术栈

- React 19
- TypeScript 5
- Vite 7
- React Router 7
- TanStack Query 5
- Zustand 5
- Axios
- Tailwind CSS 3
- Framer Motion
- React Hook Form + Zod
- Lucide React

### 5.2 后端技术栈

- FastAPI
- SQLAlchemy 2
- Pydantic 2 / pydantic-settings
- PostgreSQL + Psycopg
- Redis
- Celery 5（当前仓库内为可启用骨架）
- JWT（PyJWT）
- HTTPX（Kimi / 外部模型调用）
- Alembic
- Pytest

## 6. 前端实现细节

### 6.1 前端目录职责

- `src/app/`
  - 放应用级路由、全局 provider、应用状态与懒加载预取逻辑
- `src/domains/`
  - 按业务拆分页面、API、模型与 UI，避免以技术层面横切造成耦合
- `src/shared/`
  - 放通用 HTTP client、基础组件、布局组件、工具函数和样式

### 6.2 路由结构

前端路由由 [fontend/src/app/router.tsx](fontend/src/app/router.tsx) 统一定义，主要包括：

- 公共页
  - `/login`
  - `/register`
  - `/invite/:eventId`
- 登录后主应用壳
  - `/app/home`
  - `/app/mediation`
  - `/app/calendar`
  - `/app/profile`

实现特点：

- 使用 `PublicOnly` 和 `RequireAuth` 做路由守卫
- 使用 `framer-motion` 做页面切换动画
- 使用 [route-preload.ts](fontend/src/app/routes/route-preload.ts) 预加载关键页面模块，降低首屏切换成本

### 6.3 状态管理

前端状态分为两类：

- 客户端状态：Zustand
  - `auth-store.ts` 保存 access token、refresh token、当前用户信息、登录草稿
  - `app-store.ts` 保存当前关系、当前事件、UI 展开状态
- 服务端状态：TanStack Query
  - 负责邀请信息、裁判结果、日历、复盘详情等请求缓存与刷新

额外实现：

- 持久化 key 已切换为 `uli-auth` / `uli-app`
- 通过 [persist-migration.ts](fontend/src/shared/lib/persist-migration.ts) 自动兼容旧 `love-mediator-*` key

### 6.4 HTTP 层实现

[fontend/src/shared/api/http/client.ts](fontend/src/shared/api/http/client.ts) 负责全局 Axios 实例，主要功能包括：

- 统一 `baseURL` 和超时配置
- 自动注入 `Authorization: Bearer <token>`
- 自动生成并注入 `X-Trace-Id`
- 在收到 `401` 时自动用 refresh token 换取新的 access token
- 统一解析 envelope 响应
- 将常见网络/鉴权/服务端错误推入全局消息视图

### 6.5 页面实现要点

- `HomePage`
  - 当前偏轻量入口页，包含互动模块的柔化能力入口
- `MediationPage`
  - A 侧主调解室
  - 启动分析会话、与 AI 多轮对话、commit、复制邀请链接、查看裁判结果、继续 follow-up、发送代转达消息
- `InvitePage`
  - B 侧入口页
  - 登录后查看 `Snapshot_A`
  - 支持“直接同意生成裁判”或“开启自己的分析会话后再提交”
- `CalendarPage`
  - 以月历方式查询复盘数据
  - 支持按日查看 review 列表并打开编辑抽屉
- `ProfilePage`
  - 当前为用户相关信息与后续扩展占位页

### 6.6 UI 与设计系统

前端视觉系统定义在 [fontend/tailwind.config.ts](fontend/tailwind.config.ts)：

- 色彩：`milk` / `coffee` / `accent`
- 字体：`Nunito` + `"Zhi Mang Xing"`
- 动画：`float` / `slide-up` / `wiggle`
- 移动端框架：`AppShell + DeviceFrame + BottomNav`

## 7. 后端实现细节

### 7.1 分层结构

后端代码位于 `backend/app/`，遵循以下分层：

- `api/`
  - 路由定义、依赖注入、异常处理
- `schemas/`
  - 请求体、响应体、统一 envelope、类型验证
- `services/`
  - 业务编排、权限校验、状态流转、AI 调用
- `repos/`
  - 纯数据库访问逻辑
- `models/`
  - SQLAlchemy ORM 模型
- `core/`
  - 配置、日志、安全、Redis/Kimi 客户端
- `utils/`
  - 权限、ID、上下文等工具函数

### 7.2 应用入口

[backend/app/main.py](backend/app/main.py) 负责：

- 初始化 FastAPI 应用
- 注册异常处理器
- 按环境变量注入 CORS
- 加载 `/api` 路由树
- 暴露 `/health` 与 `/health/ready`
- 在应用关闭时关闭 Kimi 客户端

路由注册位于 [backend/app/api/router.py](backend/app/api/router.py)，当前主要模块有：

- `auth`
- `relationships`
- `events`
- `analysis-sessions`
- `calendar`
- `reviews`
- `elf`

### 7.3 配置与环境变量

[backend/app/core/config.py](backend/app/core/config.py) 使用 `BaseSettings` 读取配置，核心环境变量包括：

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `KIMI_API_KEY`
- `KIMI_BASE_URL`
- `KIMI_TEXT_MODEL`
- `KIMI_VISION_MODEL`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`

实现细节：

- `SECRET_KEY` 在 debug 环境下允许本地默认值
- 非 debug 且未配置密钥时会自动生成随机密钥并记录 warning
- 数据库连接启用了 `pool_pre_ping` 和连接超时

### 7.4 数据模型

核心表可以概括为 5 组：

- 用户与认证
  - `users`
  - `refresh_tokens`
  - `auth_login_logs`
- 关系与事件
  - `relationships`
  - `events`
  - `event_snapshots`
- AI 结果与过程记录
  - `judge_results`
  - `followup_messages`
  - `ai_call_logs`
  - `event_state_logs`
- 复盘与日历
  - `reviews`
  - `review_versions`
  - `calendar_entries`
- 扩展互动
  - `elf_messages`
  - `moderation_logs`

简化版表说明可看 [backend/docs/models.md](backend/docs/models.md)，完整设计见 [docs/DB_Uli_v1.md](docs/DB_Uli_v1.md)。

### 7.5 鉴权实现

后端当前使用 JWT 体系：

- `register` 创建用户
- `login` 签发 access token + refresh token
- `refresh` 续签 access token
- `logout` 吊销 refresh token

前端使用 access token 访问业务接口，refresh token 在 access token 失效时自动续签。

### 7.6 AI 与业务服务实现

#### 私有分析会话

[analysis_session_chat_service.py](backend/app/services/analysis_session_chat_service.py) 是主链路中最核心的服务之一，职责包括：

- 启动或恢复 A/B 侧分析会话
- 保存会话消息
- 处理文本与图片输入
- 调用私有聊天 AI 整理事实
- 当 `canCommit=true` 时允许将会话提交为正式业务状态

分析会话的临时状态存储在 Redis 中，存储适配器位于 [analysis_session_store.py](backend/app/services/analysis_session_store.py)：

- 使用 `analysis_session:*` 作为 key 前缀
- 记录按 relationship / event / user 的索引
- 使用 TTL 自动过期
- commit/judge 后清理相关会话缓存

#### 事件主链路

[event_service.py](backend/app/services/event_service.py) 负责正式事件流转：

- `create_event`
- `commit_a`
- `get_invite`
- `get_snapshot_a`
- `b_agree`
- `commit_b`
- `get_judge_result`

关键特点：

- 通过 `EventStatus` 严格控制状态流转
- A/B 权限通过 relationship 成员关系校验
- `b_agree` 和 `commit_b` 最终都会进入统一的 `execute_judge`

#### 裁判生成

[judge_service.py](backend/app/services/judge_service.py) 使用结构化 JSON 输出生成 `judge_results`：

- 输入：`Snapshot_A` 和可选的 `Snapshot_B`
- 输出字段：
  - `objective_summary`
  - `triggers`
  - `misunderstandings`
  - `adviceForA`
  - `adviceForB`
- 输出经 Pydantic 校验后落库

#### 复盘与日历

[review_service.py](backend/app/services/review_service.py) 负责：

- 根据裁判结果生成 review 正文
- 创建 `reviews`
- 自动写入 `calendar_entries`
- 支持 review 内容编辑与版本留痕

#### 互动模块

[elf_service.py](backend/app/services/elf_service.py) 当前提供两类能力：

- `relay`：将用户原始消息润色后代转达
- `moderate`：检测过激情绪并给出更柔和表达

### 7.7 异步能力

仓库中已经包含 Celery 骨架 [backend/app/workers/celery_app.py](backend/app/workers/celery_app.py)，当前用途主要是为后续 OCR、图片处理和更长链路的 AI 任务做准备。

目前关键业务仍以同步接口 + Redis 会话缓存为主，Celery 处于“结构已预留、可按需启用”的状态。

## 8. 服务流程

### 8.1 登录注册流程

```text
Register / Login
  -> FastAPI auth router
  -> auth_service
  -> users + refresh_tokens + auth_login_logs
  -> 前端持久化 token 到 uli-auth
```

### 8.2 A 侧调解主流程

```text
A 进入 /app/mediation
  -> startAAnalysisSession(relationshipId)
  -> Redis 中创建分析会话
  -> sendAnalysisMessage(sessionId, message)
  -> AI 返回 reply / canCommit / factSummary
  -> commitAnalysisSession(sessionId)
  -> 创建 Event + Snapshot_A
  -> 事件状态切换到 waiting_b
```

### 8.3 B 侧参与流程

```text
B 打开 /invite/:eventId
  -> 获取邀请页信息
  -> 登录/注册
  -> 获取 Snapshot_A
  -> 选择：
     A. 同意 -> bAgree -> 直接生成裁判
     B. 不同意 -> startBAnalysisSession -> sendAnalysisMessage -> commitAnalysisSession
          -> 生成 Snapshot_B -> 触发裁判
```

### 8.4 裁判与复盘流程

```text
execute_judge
  -> judge_service 生成结构化 judge result
  -> event 状态更新为 judged
  -> review_service 生成复盘正文
  -> reviews + calendar_entries 落库
  -> 分析会话缓存清理
```

### 8.5 裁判后的继续沟通流程

```text
前端查看 judge result
  -> FollowupChat
  -> /events/{eventId}/followup-chat/messages
  -> followup_service 基于 build_context 组织上下文
  -> AI 返回复盘陪伴式回复
  -> followup_messages 落库
```

## 9. API 与模块映射

### 9.1 后端 API 模块

- `/api/v1/auth`
  - 注册、登录、刷新、登出
- `/api/v1/relationships`
  - 关系列表、邀请、接受邀请、A 侧分析入口、取消关系
- `/api/v1/analysis-sessions`
  - 分析会话发消息、发图片、提交
- `/api/v1/events`
  - 邀请页、读取 `Snapshot_A`、B 同意、B 提交、裁判结果、follow-up
- `/api/v1/calendar`
  - 月历、按日 review 列表
- `/api/v1/reviews`
  - review 详情、编辑
- `/api/v1/elf`
  - 代转达、消息柔化

### 9.2 前端业务域映射

- `domains/auth`
  - 登录、注册、token 持久化
- `domains/home`
  - 首页与互动入口
- `domains/mediation`
  - A 侧调解、B 侧邀请参与、裁判结果、follow-up
- `domains/calendar`
  - 月历、review 列表、review 编辑
- `domains/profile`
  - 个人中心

## 10. 快速开始

### 10.1 启动顺序

建议本地开发按以下顺序启动：

1. 启动 PostgreSQL / Redis
2. 启动后端
3. 启动前端

### 10.2 后端启动

详细说明见 [backend/README.md](backend/README.md)。

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
copy .env.example .env
python -m alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

可选：使用 Docker 启动本地 PostgreSQL / Redis。

### 10.3 前端启动

详细说明见 [fontend/README.md](fontend/README.md)。

```bash
cd fontend
pnpm install
pnpm run dev
```

开发环境默认通过 `VITE_API_PROXY_TARGET=http://localhost:8000` 将 `/api` 代理到后端。

### 10.4 核心环境变量

前端：

- `VITE_API_BASE_URL`
- `VITE_API_PROXY_TARGET`
- `VITE_API_TIMEOUT_MS`
- `VITE_DEFAULT_RELATIONSHIP_ID`
- `VITE_APP_NAME`

后端：

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `KIMI_API_KEY`
- `KIMI_BASE_URL`
- `KIMI_TEXT_MODEL`
- `KIMI_VISION_MODEL`

## 11. 开发与测试

### 11.1 前端

```bash
cd fontend
pnpm run dev
pnpm run build
pnpm run lint
pnpm run preview
```

### 11.2 后端

```bash
cd backend
pytest
python -m compileall app
```

当前测试目录主要覆盖：

- API 层：`backend/tests/api`
- Service 层：`backend/tests/services`
- Schema / 通用响应层：`backend/tests/schemas`

## 12. 文档索引

- [架构文档](docs/Uli_ARCH.md)
- [API 文档](docs/API_Uli_v1.md)
- [数据库文档](docs/DB_Uli_v1.md)
- [功能文档](docs/FD_Uli_v1.md)
- [前端技术文档](docs/FE_Uli_v1.md)
- [OpenAPI 文件](docs/openapi.yaml)
- [Swagger 预览页](docs/swagger-preview.html)

## 13. 已记录但暂不处理的风险

### 13.1 Docker / 本地数据库兼容性

当前示例配置已经切换到 `uli_dev`、`uli_pgdata`、`uli-postgres` 等新命名。
这意味着如果开发者直接使用新版 `backend/docker-compose.yml`，可能会挂到一个全新的本地数据库/卷，而不是继续复用旧的 `lovemediator_*` 开发数据。

相关文件：

- [backend/docker-compose.yml](backend/docker-compose.yml)
- [backend/.env.example](backend/.env.example)

### 13.2 前端持久化迁移缺少自动化测试

浏览器本地数据会从旧 key 自动迁移到新的 `uli-*` key，但目前这条迁移路径还没有自动化测试覆盖。
如果后续调整 store 初始化顺序或 persist 配置，存在回归后才在手工联调中暴露的风险。

相关文件：

- [fontend/src/shared/lib/persist-migration.ts](fontend/src/shared/lib/persist-migration.ts)
- [fontend/src/app/model/app-store.ts](fontend/src/app/model/app-store.ts)
- [fontend/src/domains/auth/model/auth-store.ts](fontend/src/domains/auth/model/auth-store.ts)

## 14. 说明

- 仓库目录名当前仍是 `g:\\loveMediator`，这是有意保留，未纳入本轮改名范围。
- `fontend/` 目录拼写当前保持现状，避免把品牌名调整和目录级重构混在同一轮改动中。
- 后端包名已切换为 `uli-backend`，但某些历史性目录或运行时标识仍可能保留旧痕迹，这类问题建议单独作为工程清理任务处理。
