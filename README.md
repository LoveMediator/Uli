# LoveMediator

LoveMediator 是一个前后端分离的 AI 辅助关系调解项目，目标不是做“聊天陪伴”，而是把伴侣之间一次真实冲突拆解成可理解、可确认、可复盘的业务流程。系统围绕 `Relationship` 和 `Event` 两个核心对象展开：A 侧先与 AI 私有对话整理事实，生成冻结的 `Snapshot_A`；B 侧通过邀请链接进入后，可以直接同意，也可以补充自己的视角生成 `Snapshot_B`；随后后端生成 `JudgeResult`，自动产出复盘 `Review`，并将结果沉淀到日历中。

这份 README 以“当前仓库已经实现的代码”为准，面向维护者、交接同学和新加入的开发者，重点讲清楚三件事：

- 这个项目解决什么业务问题
- 前后端分别是怎么实现这条业务链路的
- 接手后应从哪里开始阅读、运行和维护

## 1. 项目定位

### 1.1 解决的问题

项目试图解决的不是“谁对谁错”，而是把冲突双方的表达过程产品化：

- 把情绪化、碎片化的原始表达先转成结构化事实
- 让双方围绕同一事件各自确认自己的版本
- 在后端受控状态机里生成裁决和复盘，而不是让前端自由拼装业务状态
- 把一次次冲突沉淀成可回看的关系记录

### 1.2 核心角色

- `User A`：事件发起方，先进入私有分析会话
- `User B`：通过邀请页进入事件，可同意 A 的描述或补充自己的视角
- `AI`：在不同业务阶段扮演不同角色
  - 私有分析助手
  - 裁决生成器
  - 复盘生成器
  - 后续追问助手
  - 消息润色 / 代转达助手

### 1.3 当前产品形态

当前实现是移动端优先的 Web SPA：

- 主要页面采用 `DeviceFrame` 包裹，视觉上更接近移动端产品
- 已有完整前后端链路，适合本地联调、功能迭代和业务验证
- 部分能力已经落到真实持久化链路，部分仍是 mock / 预留实现，README 会明确标出

## 2. 业务术语与核心对象

理解这个项目时，建议先记住下面几个术语。

| 名称 | 含义 | 代码位置 |
| --- | --- | --- |
| `Relationship` | 一对用户的关系容器，是权限与事件归属的上层边界 | `backend/app/models/relationship.py` |
| `Event` | 一次冲突 / 调解事件 | `backend/app/models/event.py` |
| `AnalysisSession` | A 侧或 B 侧进入正式事件前的私有分析会话，存放在 Redis 中，有 TTL | `backend/app/services/analysis_session_store.py` |
| `Snapshot_A` / `Snapshot_B` | 某一侧确认后的事实快照，一旦提交即冻结 | `backend/app/models/snapshot.py` |
| `JudgeResult` | 基于快照生成的裁决结果 | `backend/app/models/judge.py` |
| `Review` | 基于裁决自动生成、可继续编辑的复盘内容 | `backend/app/models/review.py` |
| `CalendarEntry` | 将复盘挂到某个日期，用于月历聚合展示 | `backend/app/models/review.py` |
| `FollowupMessage` | 裁决后继续围绕同一事件的追问聊天记录 | `backend/app/models/review.py` |
| `Elf` | 首页和调解页中的“小精灵”能力，包括消息润色和代转达 | `backend/app/services/elf_service.py` |

## 3. 核心业务流程

这是项目最重要的部分。建议把它理解成“前端页面状态”和“后端事件状态”共同驱动的一条主链路。

### 3.1 关系建立

业务前提是先有一条 `Relationship`。

流程如下：

1. 用户 A 登录后调用 `POST /api/v1/relationships/invite`
2. 后端生成邀请 token 和邀请 URL
3. 用户 B 登录后调用 `POST /api/v1/relationships/accept`
4. 后端创建 `Relationship`

当前实现特点：

- 后端已经具备邀请、接受、取消关系的完整接口和服务层逻辑
- 前端当前没有完整的“关系管理页面”，而是通过环境变量 `VITE_DEFAULT_RELATIONSHIP_ID` 预置一个默认关系 ID 进入主流程
- `backend/scripts/seed_db.py` 会生成默认种子数据，包含：
  - 用户 `alice / Secret123!`
  - 用户 `bob / Secret123!`
  - 关系 `r_seed_ab_1`

### 3.2 A 侧发起事件

这一阶段的目标不是立刻创建正式事件，而是先让 A 和 AI 把事情说清楚。

前端：

- 页面：`/app/mediation`
- 组件：`fontend/src/domains/mediation/page/MediationPage.tsx`
- 用户点击“开始分析”后，前端调用 `POST /api/v1/relationships/{relationshipId}/analysis-sessions/a`

后端：

- 路由：`backend/app/api/v1/relationships.py`
- 服务：`backend/app/services/analysis_session_chat_service.py`
- 会话存储：`backend/app/services/analysis_session_store.py`

实现细节：

- A 侧分析会话不是持久化到 PostgreSQL，而是写入 Redis
- Redis 中会为会话维护：
  - session 本体
  - relationship 维度索引
  - event 维度索引
  - `phase + scope + user` 维度索引
- 会话有 TTL，默认由 `ANALYSIS_SESSION_TTL_SECONDS` 控制
- 如果同一个用户在同一个 relationship 范围内已经有未完成会话，后端会恢复而不是重复新建

### 3.3 A 侧与 AI 私有分析

用户进入分析会话后，可以通过文本甚至图片继续补充信息。

相关接口：

- `POST /api/v1/analysis-sessions/{sessionId}/messages`
- `POST /api/v1/analysis-sessions/{sessionId}/images`
- `POST /api/v1/analysis-sessions/{sessionId}/commit`

实现细节：

- 文本消息和图片消息都先写回 Redis 中的会话历史
- 后端会把最近历史整理成 private-chat prompt，再调用 Kimi
- 如果消息中包含图片，`private_chat_ai_service.py` 会自动切换到视觉模型
- AI 返回结构化 JSON：
  - `reply`
  - `can_confirm`
  - `fact_summary`
- 当前端拿到 `canCommit=true` 后，才会显示“确认提交”按钮

提交后发生的事情：

1. 后端创建 `Event`
2. 创建 `Snapshot_A`
3. 状态从 `draft` 进入 `waiting_b`
4. 记录 `event_state_logs`
5. 返回 `eventId`，前端展示邀请链接 `/invite/{eventId}`

### 3.4 B 侧进入邀请页

页面：`/invite/:eventId`

这是 B 侧进入业务的公开入口，但它并不是完全匿名操作页面。

前端流程：

1. 先调用 `GET /api/v1/events/{eventId}/invite` 获取公开邀请信息
2. 如果未登录，引导跳转 `/login` 或 `/register`
3. 登录后调用 `GET /api/v1/events/{eventId}/snapshot-a`
4. 向 B 展示 A 已确认的快照内容

后端控制点：

- `get_invite` 允许公开读取事件邀请元信息
- `get_snapshot_a` 则要求用户已登录并通过 relationship / event 权限校验
- 发起方不能冒充 B 侧去走 B 的后续流程

### 3.5 B 侧两条分支

当 B 看完 `Snapshot_A` 后，业务分成两条线。

#### 分支 A：直接同意

接口：

- `POST /api/v1/events/{eventId}/b-agree`

行为：

- 不创建 `Snapshot_B`
- 直接基于 `Snapshot_A` 生成 `JudgeResult`

#### 分支 B：补充自己的视角

接口：

- `POST /api/v1/events/{eventId}/analysis-sessions/b`
- `POST /api/v1/analysis-sessions/{sessionId}/messages`
- `POST /api/v1/analysis-sessions/{sessionId}/commit`

行为：

- 为 B 创建或恢复私有分析会话
- 仍然使用 Redis 存储中间过程
- 最终提交时创建 `Snapshot_B`
- 然后进入裁决生成

### 3.6 裁决、复盘与日历沉淀

裁决逻辑由 `backend/app/services/event_service.py` 驱动，是整个项目的状态机核心。

`execute_judge()` 执行时会：

1. 调用 `judge_service.generate_judge_result()` 生成 `JudgeResult`
2. 将事件状态改为 `judged`
3. 写入 `event_state_logs`
4. 写入 `ai_call_logs`
5. 调用 `review_service.generate_review_content_from_judge()` 生成复盘正文
6. 调用 `review_service.create_review_from_judge()` 创建：
   - `Review`
   - `CalendarEntry`
7. 清理当前 relationship 相关的分析会话缓存

这意味着在当前实现里：

- 裁决成功后，复盘和日历也会同步可见
- 日历不是额外独立维护的模块，而是裁决链路的下游结果

### 3.7 裁决后的 follow-up

裁决不是流程终点。用户还可以继续围绕同一事件追问“接下来怎么沟通”。

接口：

- `POST /api/v1/events/{eventId}/followup-chat/messages`

上下文来源：

- `Snapshot_A`
- `Snapshot_B`
- `JudgeResult`
- `Review`
- 最近几条 follow-up 消息

实现特点：

- follow-up 不再围绕“确认事实”，而是围绕“理解、反思、下一步表达”
- 会写入 `followup_messages`
- 会继续写 `ai_call_logs`

## 4. 已实现能力与当前限制

这一节很重要，方便后续维护时快速判断哪些能力已成熟，哪些还是占位实现。

### 4.1 已完整打通的主链路

- 注册 / 登录 / 刷新 token / 退出登录
- 关系邀请与接受
- A 侧私有分析会话
- B 侧邀请页与快照查看
- B 侧直接同意或补充视角
- 裁决生成
- 自动生成复盘与日历
- 日历按月 / 按日查看复盘
- 复盘编辑
- 裁决后的 follow-up 聊天

### 4.2 已接到页面但仍是 mock 的能力

- `Elf` 消息润色：当前使用 mock 规则，不是实际 LLM 审核
- `Elf` 代转达：当前也为 mock 生成内容

对应位置：

- 路由：`backend/app/api/v1/elf.py`
- 服务：`backend/app/services/elf_service.py`

### 4.3 当前明显的产品层限制

- 前端没有完整关系管理页面，默认通过 `VITE_DEFAULT_RELATIONSHIP_ID` 进入流程
- 关系列表接口已存在，但尚未完整接入主页面
- Celery 基础设施已经接入，但大部分核心 AI 调用仍在请求链路内同步执行
- 控制台与部分旧文档存在历史中文编码问题，不影响代码逻辑，但会影响阅读体验

## 5. 技术栈

### 5.1 前端技术栈

| 类别 | 选型 | 用途 |
| --- | --- | --- |
| UI 框架 | React 19 | 页面与组件开发 |
| 构建工具 | Vite 7 | 本地开发与生产构建 |
| 语言 | TypeScript 5 | 类型约束 |
| 路由 | React Router 7 | 路由守卫与页面切换 |
| 服务端状态 | TanStack Query 5 | 查询、缓存、Mutation |
| 客户端状态 | Zustand 5 | 登录态、当前关系、当前事件等本地状态 |
| 表单 | React Hook Form + Zod | 登录 / 注册等表单校验 |
| 动画 | Framer Motion | 页面切换与部分动效 |
| 样式 | Tailwind CSS 3 | 原子化样式与主题扩展 |
| 图标 | lucide-react | 图标系统 |
| HTTP | Axios | API 客户端与拦截器 |

补充实现细节：

- `vite.config.ts` 中配置了 `/api` 代理到 `VITE_API_PROXY_TARGET`
- 使用 `babel-plugin-react-compiler`
- 路由页面通过 `lazyWithPreload` 延迟加载
- `QueryClient` 默认设置为：
  - query 重试 1 次
  - window focus 不自动 refetch
  - mutation 不自动重试
- Tailwind 扩展了 `milk / coffee / accent` 三组设计色板与移动端视觉风格

### 5.2 后端技术栈

| 类别 | 选型 | 用途 |
| --- | --- | --- |
| Web 框架 | FastAPI | API、依赖注入、参数校验 |
| ORM | SQLAlchemy 2 | 数据持久化 |
| 迁移 | Alembic | 数据库 schema 管理 |
| 数据库 | PostgreSQL | 业务数据持久化 |
| 缓存 / 会话 | Redis | AnalysisSession 缓存与索引 |
| 鉴权 | JWT + Refresh Token | 登录态管理 |
| 密码安全 | bcrypt | 密码哈希 |
| 异步基础设施 | Celery | 异步任务基础设施，当前多为预留 |
| HTTP Client | httpx | 调用 Kimi API |
| AI 模型 | Kimi 文本 / 视觉模型 | 私有分析、裁决、复盘、follow-up |
| 测试 | pytest + 自定义脚本 | API / service / 全链路测试 |

## 6. 前端实现细节

### 6.1 路由与页面骨架

路由定义在 `fontend/src/app/router.tsx`：

- `PublicOnly`：拦截已登录用户访问 `/login`、`/register`
- `RequireAuth`：保护 `/app/*` 路由
- `/invite/:eventId` 是公开入口，但内部仍会根据登录态决定是否继续读取 `Snapshot_A`

主壳层：

- `AppShell` 统一包裹 `DeviceFrame`
- 底部导航在 `BottomNav.tsx`
- 主要页面：
  - `HomePage`
  - `MediationPage`
  - `CalendarPage`
  - `ProfilePage`

### 6.2 状态管理

前端目前有两类 Zustand store：

- `love-mediator-auth`
  - 保存 access token、refresh token、publicId、usernameDraft
- `love-mediator-app`
  - 保存 relationshipId、currentEvent、calendarExpanded 等业务态

这意味着刷新页面后，登录态和“当前进行中的事件”会尽量被恢复。

### 6.3 HTTP 客户端

`fontend/src/shared/api/http/client.ts` 负责统一请求行为：

- 自动注入 `Authorization: Bearer <token>`
- 自动注入 `X-Trace-Id`
- `401` 时尝试使用 refresh token 刷新 access token
- 刷新失败后清空本地会话并跳转登录页
- 统一把后端 envelope 解包为业务数据
- 通过 `MessageViewport` 统一展示全局消息提示

### 6.4 页面与业务的对应关系

- `HomePage`
  - 当前主要承载 Elf 消息润色入口
- `MediationPage`
  - A 侧发起分析、等待 B、查看裁决、继续 follow-up
- `InvitePage`
  - B 侧读邀请、读 `Snapshot_A`、选择同意或补充视角
- `CalendarPage`
  - 月历聚合、按天查看 review 列表、打开 review 编辑抽屉
- `ProfilePage`
  - 主要是当前登录态和当前事件状态的只读展示，加退出登录

## 7. 后端实现细节

### 7.1 应用入口

`backend/app/main.py` 的 `create_app()` 负责：

- 初始化日志
- 注册统一异常处理
- 配置 CORS
- 挂载 `/api` 路由
- 暴露 `/health` 和 `/health/ready`

### 7.2 路由组织

总路由挂载在 `backend/app/api/router.py`，目前包含：

- `auth`
- `relationships`
- `events`
- `analysis_sessions`
- `calendar`
- `reviews`
- `elf`

### 7.3 鉴权与权限

`backend/app/api/deps.py` 中定义了：

- `CurrentUser`
- `CurrentActiveUser`
- `Db`
- `PublicId`

鉴权机制：

- access token 为 JWT
- refresh token 为随机 opaque token，数据库内只存 SHA-256 hash
- 所有登录失败与登录成功都会写入 `auth_login_logs`
- 连续登录失败会触发锁定逻辑

### 7.4 service / repo 分层

后端采用典型的“route -> service -> repo -> model”分层：

- route 负责：
  - 请求解析
  - 依赖注入
  - envelope 返回
- service 负责：
  - 状态机
  - 权限校验
  - AI 编排
  - 聚合多个 repo 操作
- repo 负责：
  - 单一数据表或聚合查询的数据库访问

对维护者来说，真正的业务核心在 `backend/app/services/`。

### 7.5 AnalysisSession 的后端实现

这是项目里最容易误解的部分。

- AnalysisSession 不在 PostgreSQL 中存表
- 它是 Redis 中的一段临时业务态
- 会话提交后，才会“固化”为正式业务数据：
  - `Event`
  - `Snapshot_A`
  - `Snapshot_B`

这样做的好处是：

- 私有分析过程可以频繁修改，不污染正式业务表
- 事件状态只有在用户确认后才推进
- 可以用 TTL 自然清理未完成的临时会话

### 7.6 裁决、复盘与审计

后端不仅存主业务结果，还存过程日志：

- `event_state_logs`
  - 记录状态流转与操作人
- `ai_call_logs`
  - 记录 AI 调用场景、模型、token、成功与否

这些日志对于后续做成本分析、故障排查和可观测性扩展非常关键。

### 7.7 AI 调用实现

AI 调用主要分成两类：

- `ai_service.py`
  - 通用文本 / JSON 输出调用封装
- `private_chat_ai_service.py`
  - 私有分析会话专用封装
  - 根据消息中是否含图片选择文本模型或视觉模型

Kimi HTTP 客户端在 `backend/app/core/kimi_client.py` 中以单例方式维护连接池，应用结束时关闭。

### 7.8 异常处理

`backend/app/api/exception_handlers.py` 统一处理：

- 业务异常 `AppError`
- 参数校验异常
- HTTPException
- 未捕获异常

所有异常都会回到统一的 envelope 格式，前端因此不需要为每个接口单独适配错误结构。

## 8. 数据模型与状态机

### 8.1 核心表

建议优先阅读以下模型文件：

- `backend/app/models/user.py`
- `backend/app/models/relationship.py`
- `backend/app/models/event.py`
- `backend/app/models/snapshot.py`
- `backend/app/models/judge.py`
- `backend/app/models/review.py`
- `backend/app/models/audit.py`

### 8.2 当前重要约束

- 同一 relationship 同一时间最多一个未完成事件
- 同一 event 每个 side 最多一个 snapshot
- 同一 event 最多一个 `JudgeResult`
- 同一 event 最多一个 `Review`
- `Snapshot` 一旦提交即冻结

### 8.3 Event 状态

当前枚举：

- `draft`
- `waiting_b`
- `judged`
- `reviewed`
- `closed`

主流程中的含义：

- `draft`
  - 事件已创建但尚未完成 A 侧确认
  - 当前主实现中更多通过分析会话提交后直接跨到 `waiting_b`
- `waiting_b`
  - A 侧已经确认，等待 B 侧查看和处理
- `judged`
  - 裁决已生成
- `reviewed`
  - 复盘已进入更后续状态
- `closed`
  - 已结束

## 9. 仓库结构

> 注意：前端目录名当前实际是 `fontend/`，不是 `frontend/`。这是仓库现状，不是 README 拼写错误。

```text
loveMediator/
├─ backend/
│  ├─ app/
│  │  ├─ api/            # 路由、依赖、异常处理
│  │  ├─ core/           # 配置、安全、Kimi/Redis 客户端、日志
│  │  ├─ db/             # SQLAlchemy Base / Session
│  │  ├─ models/         # ORM 模型
│  │  ├─ repos/          # 数据访问层
│  │  ├─ schemas/        # Pydantic schema
│  │  ├─ services/       # 核心业务层
│  │  ├─ utils/          # 权限、ID、上下文等工具
│  │  └─ workers/        # Celery 预留结构
│  ├─ alembic/
│  ├─ docs/
│  ├─ scripts/
│  ├─ tests/
│  ├─ .env.example
│  ├─ docker-compose.yml
│  └─ pyproject.toml
├─ fontend/
│  ├─ public/
│  ├─ src/
│  │  ├─ app/            # App 入口、Provider、Router、全局 app store
│  │  ├─ domains/        # 业务域拆分
│  │  ├─ shared/         # 通用组件、布局、样式、API、工具
│  │  └─ main.tsx
│  ├─ .env.example
│  ├─ package.json
│  └─ vite.config.ts
├─ docs/
├─ demo.html
└─ README.md
```

## 10. 本地运行

### 10.1 启动后端

```powershell
cd backend
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .[dev]
python -m alembic upgrade head
python scripts\seed_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

### 10.2 使用 Docker 启动依赖

```powershell
cd backend
docker compose up -d
```

默认端口映射：

- PostgreSQL：`5433`
- Redis：`6380`

如果你使用这套依赖，需要同步调整 `backend/.env` 中的：

- `DATABASE_URL`
- `REDIS_URL`

### 10.3 启动前端

```powershell
cd fontend
copy .env.example .env
pnpm install
pnpm dev
```

关键前端环境变量：

- `VITE_API_BASE_URL=/api/v1`
- `VITE_API_PROXY_TARGET=http://localhost:8000`
- `VITE_DEFAULT_RELATIONSHIP_ID=r_seed_ab_1`

### 10.4 种子账号

运行 `backend/scripts/seed_db.py` 后可使用：

- `alice / Secret123!`
- `bob / Secret123!`

## 11. 测试与调试

### 11.1 自动化测试

后端当前已有两层测试入口：

- `backend/tests/`
  - API 层测试
  - service 层测试
- `backend/scripts/full_test_suite.py`
  - 偏端到端的非 AI 全链路测试脚本
  - 覆盖鉴权、状态机、安全边界、重复提交、取消关系等

### 11.2 常用命令

```powershell
cd backend
pytest
```

或：

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\full_test_suite.py
```

### 11.3 推荐阅读顺序

如果你是第一次接手，建议按下面顺序进入代码：

1. 本 README
2. `fontend/src/app/router.tsx`
3. `fontend/src/domains/mediation/page/MediationPage.tsx`
4. `fontend/src/domains/invite/page/InvitePage.tsx`
5. `backend/app/api/v1/events.py`
6. `backend/app/services/analysis_session_chat_service.py`
7. `backend/app/services/event_service.py`
8. `backend/app/services/review_service.py`
9. `backend/app/services/followup_service.py`

## 12. 维护建议

### 12.1 维护时优先坚持的边界

- 不要让前端直接拼装业务状态机
- AnalysisSession 只是临时态，正式业务数据必须落回 PostgreSQL
- 新功能尽量延续 `route -> service -> repo` 的后端分层
- 前端共享层 `shared/` 不要反向依赖业务 domain

### 12.2 后续可继续增强的方向

- 给关系管理做完整 UI，而不是依赖默认 relationshipId
- 把更多 AI 调用切到 Celery 异步执行
- 打通真正的 trace / observability 链路
- 替换 Elf 相关 mock 实现
- 逐步清理旧文档和控制台输出中的编码问题

## 13. 补充文档

以下文档仍有参考价值，但建议将它们视为“背景资料”，而把当前代码和本 README 视为“维护基线”：

- `docs/LoveMediator_ARCH.md`
- `docs/API_LoveMediator_v1.md`
- `docs/DB_LoveMediator_v1.md`
- `docs/FE_LoveMediator_v1.md`
- `backend/docs/models.md`
- `backend/docs/task_assignment.md`
