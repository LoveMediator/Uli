# Backend 三人分工文档

## 1. 文档目的

本文件用于明确 LoveMediator 后端三位开发成员的任务边界、交付物、依赖关系与验收标准。

分工原则不是按 `api / service / repo` 机械横切，而是按当前仓库真实状态拆成：

- 1 号：公共底座与认证
- 2 号：事件调解主链
- 3 号：复盘、日历与互动链

这样拆分的原因：

- 当前后端已有 **models + migration** 雏形，但 `api / services / repos / schemas / tests` 基本未落地。
- 如果按分层拆分，三个人会互相阻塞。
- 先由 1 号把公共基础设施铺好，2 号和 3 号才能并行推进。

## 2. 当前后端状态

### 2.1 已有内容

- 数据模型已定义：
  - `app/models/user.py`
  - `app/models/relationship.py`
  - `app/models/event.py`
  - `app/models/snapshot.py`
  - `app/models/judge.py`
  - `app/models/review.py`
  - `app/models/elf.py`
  - `app/models/audit.py`
- 首个 Alembic migration 已存在：
  - `alembic/versions/9f41939eaaea_init.py`
- 应用入口和基础配置已存在：
  - `app/main.py`
  - `app/core/config.py`
  - `app/db/session.py`
  - `app/api/deps.py`

### 2.2 未完成内容

- 路由注册未完成：
  - `app/api/router.py`
- v1 API 基本为空：
  - `app/api/v1/auth.py`
  - `app/api/v1/events.py`
  - `app/api/v1/calendar.py`
  - `app/api/v1/reviews.py`
  - `app/api/v1/elf.py`
- service 层为空：
  - `app/services/*.py`
- repo 层为空：
  - `app/repos/*.py`
- schema 层为空：
  - `app/schemas/*.py`
- 测试基本为空：
  - `tests/conftest.py`
  - `tests/api/`
  - `tests/services/`

### 2.3 当前统一约束

- 接口契约以 `docs/API_LoveMediator_v1.md` 和 `docs/openapi.yaml` 为准。
- 架构口径已统一为：
  - B 通过分享链接进入邀请页
  - 必须注册/登录
  - 再用 JWT 访问业务接口
- Event 状态统一使用：
  - `draft`
  - `waiting_b`
  - `judged`
  - `reviewed`
  - `closed`
- 所有路径 ID 使用 `public_id`，不是数据库自增主键。

## 3. 团队协作规则

### 3.1 公共约定

- 所有接口统一返回：
  - `code`
  - `message`
  - `data`
- 所有需要登录的接口统一走 Bearer JWT。
- 所有 `eventId`、`reviewId`、`relationshipId`、`userId` 按 `public_id` 查询。
- 所有写操作都必须做权限校验与状态校验。
- `judge-result` 严禁实时触发 LLM，只能读落库结果。
- B 侧接口不允许绕过登录。

### 3.2 提交协作

- 1 号负责公共依赖、响应封装、错误模型、JWT 依赖，其他人不得重复造一套。
- 2 号和 3 号不得私自改动 1 号已经定好的响应结构和认证依赖。
- 涉及跨人边界变更时，先同步文档，再改代码。
- 每人负责自己的接口测试和 service 测试。

### 3.3 联调顺序

1. 1 号先完成基础底座与 auth。
2. 2 号并行完成事件主链。
3. 3 号在 1 号底座就绪后先搭 review/calendar/elf 骨架，等待 2 号提供 judged 数据流转。

## 4. 1号后端：公共底座与认证负责人

### 4.1 角色目标

1 号负责把整个后端的“基础设施层”先搭起来，让其他两个人不用再处理认证、统一响应、错误处理、测试基建这些横向问题。

一句话定义：

- 1 号不是只做 auth，而是做“所有人都要依赖的基础能力”。

### 4.2 负责模块

- 统一响应结构
- 全局异常与错误码
- JWT 鉴权
- refresh token 管理
- 密码哈希与登录安全
- 路由聚合
- 依赖注入
- 测试基建
- seed 数据脚本
- auth 相关 API / schema / service / repo

### 4.3 负责文件

- `app/api/router.py`
- `app/api/deps.py`
- `app/api/v1/auth.py`
- `app/core/config.py`
- `app/core/errors.py`
- `app/core/security.py`
- `app/schemas/common.py`
- `app/schemas/auth.py`
- `app/services/auth_service.py`
- `app/repos/user_repo.py`
- `tests/conftest.py`
- `scripts/seed_db.py`

### 4.4 详细任务拆分

#### 任务 A1：统一响应模型

- 定义统一响应 envelope：
  - 成功：`code=0, message="ok", data={...}`
  - 失败：`code!=0, message=错误信息, data=null`
- 在 `app/schemas/common.py` 中建立基础响应模型
- 确保 auth、events、calendar、reviews、elf 都能复用
- 约束字段命名，避免后续出现一部分接口裸返回、一部分接口包 envelope

验收标准：

- 所有新增接口都使用同一套响应包装
- OpenAPI 与代码实现字段一致

#### 任务 A2：错误码和异常体系

- 在 `app/core/errors.py` 中扩展应用异常类型
- 至少覆盖：
  - 参数错误
  - 资源不存在
  - 状态不允许
  - 认证失败
  - 权限不足
  - 账号锁定/禁用
  - 用户名重复
  - 系统异常
- 建立异常到 `code/message` 的映射
- 在 FastAPI 层统一注册异常处理器

验收标准：

- 业务异常不再直接抛 500
- 前端能稳定拿到错误码

#### 任务 A3：JWT 与认证依赖

- 在 `app/core/security.py` 中实现：
  - 密码哈希
  - 密码校验
  - access token 生成
  - refresh token 生成或管理策略
  - access token 解析
- 在 `app/api/deps.py` 中实现：
  - `get_current_user`
  - `get_current_active_user`
- 明确 token 过期、无效、登出后的行为

验收标准：

- 受保护接口可以通过依赖注入拿到当前用户
- 无效 token 会返回统一 `2001`

#### 任务 A4：Auth 全链路接口

- 实现：
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
- 登录时记录 `auth_login_logs`
- refresh 时校验 token 是否过期或吊销
- logout 时吊销 refresh token
- 注册时校验用户名重复

验收标准：

- 4 个 auth 接口可用
- 登录后可拿 JWT 调用其他接口

#### 任务 A5：路由与应用注册

- 在 `app/api/router.py` 中 include 所有 v1 router
- 按模块拆 tags：
  - auth
  - events
  - calendar
  - reviews
  - elf
- 让 FastAPI `/docs` 能展示完整路由

验收标准：

- 运行后 `/docs` 能看到所有已经实现的接口

#### 任务 A6：配置项与环境变量整理

- 补全 `app/core/config.py`
- 补充 `.env.example` 和 README 的配置说明
- 至少明确：
  - `DATABASE_URL`
  - `REDIS_URL`
  - `SECRET_KEY`
  - token 过期时间
  - 调试开关

验收标准：

- 新成员按 README 能启动服务

#### 任务 A7：测试基建

- 完成 `tests/conftest.py`
- 建立测试数据库 session
- 提供测试用户和鉴权 header fixture
- 提供创建 event / relationship 的基础 fixture

验收标准：

- 2 号和 3 号可以在自己的测试里直接复用 fixture

#### 任务 A8：seed 数据脚本

- 编写 `scripts/seed_db.py`
- 至少写入：
  - User A
  - User B
  - relationship
  - 一个 `draft` event
  - 一个 `waiting_b` event
  - 可选 judged / reviewed event

验收标准：

- 本地联调不需要手工造数据

### 4.5 1号交付物

- auth 4 接口可跑通
- 公共响应和错误码可复用
- JWT 依赖可被 events/reviews/calendar/elf 直接使用
- 测试基建和 seed 数据可用

### 4.6 1号风险点

- 如果 1 号把响应结构和错误码定得太晚，2 号和 3 号会返工
- 如果 `get_current_user` 定义不稳，其他所有受保护接口都会受影响

## 5. 2号后端：事件调解主链负责人

### 5.1 角色目标

2 号负责 MVP 的主价值闭环：从创建事件到获取裁判结果。

一句话定义：

- 2 号负责把“事件如何从 `draft` 走到 `judged`”彻底做通。

### 5.2 负责模块

- Event
- Snapshot_A / Snapshot_B
- JudgeResult
- 事件状态流转
- 审计日志
- AI 调用日志
- 事件主链 API / schema / service / repo
- 后续 Celery judge 骨架

### 5.3 负责文件

- `app/api/v1/events.py`
- `app/schemas/event.py`
- `app/schemas/judge.py`
- `app/services/event_service.py`
- `app/services/judge_service.py`
- `app/services/ai_service.py`
- `app/repos/event_repo.py`
- `app/repos/snapshot_repo.py`
- `app/repos/judge_repo.py`
- `app/repos/audit_repo.py`
- `app/workers/celery_app.py`
- `app/workers/tasks.py`
- `tests/api/` 下事件主链测试
- `tests/services/` 下事件 service 测试

### 5.4 详细任务拆分

#### 任务 B1：事件创建接口

- 实现 `POST /api/v1/events`
- 校验当前用户是否属于 `relationshipId`
- 写入 `events`
- 初始化状态为 `draft`
- 返回 `eventId` 与 `status`

验收标准：

- 已登录用户可创建自己的事件
- 非关系成员不能创建

#### 任务 B2：A 侧提交 Snapshot_A

- 实现 `POST /api/v1/events/{eventId}/commit-a`
- 仅允许 A 侧用户调用
- 校验当前状态必须是 `draft`
- 写入 `event_snapshots(side='a')`
- 更新 `events.status` 为 `waiting_b`
- 写入 `event_state_logs`

验收标准：

- 同一事件不能重复提交 A 快照
- 非 `draft` 状态调用会报 `1003`

#### 任务 B3：邀请页与 Snapshot_A 读取

- 实现 `GET /api/v1/events/{eventId}/invite`
- 未登录可访问，但只返回邀请页展示信息
- 不返回完整 Snapshot_A 正文
- 实现 `GET /api/v1/events/{eventId}/snapshot-a`
- 仅 A 或已登录且有权限的 B 可访问
- 返回 `summary / pointsA / pointsB`

验收标准：

- 邀请页接口不会泄露敏感正文
- Snapshot_A 接口不会被未登录用户访问

#### 任务 B4：B 同意裁判

- 实现 `POST /api/v1/events/{eventId}/b-agree`
- 仅允许 B 调用
- 校验当前状态是 `waiting_b`
- 校验 A 快照已存在
- 生成 `judge_results`
- 更新事件为 `judged`
- 记录 `judged_at`
- 写入 `event_state_logs`
- 写入 `ai_call_logs`

验收标准：

- 成功后能查询到 `judge-result`
- 重复触发需处理幂等或明确报错

#### 任务 B5：B 提交 Snapshot_B

- 实现 `POST /api/v1/events/{eventId}/commit-b`
- 仅允许 B 调用
- 校验当前状态是 `waiting_b`
- 写入 `event_snapshots(side='b')`
- 再生成 `judge_results`
- 更新事件为 `judged`
- 写入状态日志和 AI 调用日志

验收标准：

- 有 B 快照时能进入“双方视角裁判”分支
- 同一事件不能重复写多个 B 快照

#### 任务 B6：裁判结果查询

- 实现 `GET /api/v1/events/{eventId}/judge-result`
- 只读查库
- 仅关系双方可访问
- 严禁在查询接口里实时触发 LLM

验收标准：

- 已 judged 的事件能稳定返回结果
- 未生成结果时按约定返回 `3003` 或 `1002`

#### 任务 B7：事件状态机和事务边界

- 明确状态迁移：
  - `draft -> waiting_b`
  - `waiting_b -> judged`
- 在 service 中处理事务
- 关键写操作需要保证一致性：
  - snapshot 写入
  - event 状态更新
  - 审计日志写入

验收标准：

- 不出现只写入 snapshot、未更新 event 的半成功状态

#### 任务 B8：审计和 AI 调用日志

- 通过 `audit_repo` 写 `event_state_logs`
- 写 `ai_call_logs`
- 至少记录：
  - event_id
  - action / scene
  - success
  - trace_id 预留字段

验收标准：

- 主链每次关键状态变化都有可追踪日志

#### 任务 B9：judge service 占位与 Celery 预留

- 先实现同步可用版 `judge_service`
- 返回固定结构或规则生成假数据也可以
- 再在 `workers/tasks.py` 中补上异步任务骨架
- 为后续接真实 LLM 留接口

验收标准：

- 不等真实 AI 接入也能完成联调

### 5.5 2号交付物

- 事件主链接口可用：
  - create event
  - invite
  - commit-a
  - snapshot-a
  - b-agree
  - commit-b
  - judge-result
- 主链服务层事务清晰
- 审计日志和 AI 日志落库

### 5.6 2号风险点

- 最容易返工的是状态机和权限判断
- 如果 2 号把 `eventId` 当数据库主键用，会直接破坏对外契约
- 如果在 `judge-result` 里实时调 AI，会和文档硬冲突

## 6. 3号后端：复盘、日历与互动负责人

### 6.1 角色目标

3 号负责事件裁判完成后的沉淀与扩展链路。

一句话定义：

- 3 号负责把“judged 之后怎么沉淀成 review、calendar 和互动能力”做通。

### 6.2 负责模块

- Review
- ReviewVersion
- CalendarEntry
- Followup chat
- Elf relay
- Moderate
- 上下文构建
- 复盘与日历 API / schema / service / repo

### 6.3 负责文件

- `app/api/v1/calendar.py`
- `app/api/v1/reviews.py`
- `app/api/v1/elf.py`
- `app/schemas/review.py`
- `app/schemas/calendar.py`
- `app/schemas/elf.py`
- `app/services/review_service.py`
- `app/services/calendar_service.py`
- `app/repos/review_repo.py`
- `app/utils/context_builder.py`
- `tests/api/` 下 review / calendar / elf 测试
- `tests/services/` 下 review / calendar / followup 测试

### 6.4 详细任务拆分

#### 任务 C1：review 生成与读取模型

- 梳理 `reviews`、`review_versions`、`calendar_entries` 的关系
- 明确 review 与 event 是 1:1
- 补全 repo 查询能力
- 为“judged 后生成 review”留 service 接口

验收标准：

- review / version / calendar 的 repo 方法可独立使用

#### 任务 C2：复盘详情接口

- 实现 `GET /api/v1/reviews/{reviewId}`
- 仅关系双方可访问
- 返回：
  - reviewId
  - eventId
  - content
  - source
  - createdAt
  - updatedAt

验收标准：

- review 可按 `public_id` 查询
- 非参与方不可读取

#### 任务 C3：编辑复盘接口

- 实现 `PUT /api/v1/reviews/{reviewId}`
- 更新 `reviews.content`
- 写入 `updated_by_user_id`
- 写入 `updated_at`
- 同时插入 `review_versions`

验收标准：

- 每次编辑都会新增 version 记录
- 不会只更新正文、不写历史

#### 任务 C4：月历查询接口

- 实现 `GET /api/v1/calendar?month=YYYY-MM`
- 按 relationship 维度查 `calendar_entries`
- 返回每天 review 数量

验收标准：

- 能正确聚合一个月的事件数量
- 非本关系数据不会串出

#### 任务 C5：日期复盘列表接口

- 实现 `GET /api/v1/calendar/days/{date}/reviews`
- 按日期返回 review 列表
- 包括：
  - reviewId
  - eventId
  - title
  - updatedAt

验收标准：

- 日期筛选准确
- 返回字段与 API 文档一致

#### 任务 C6：followup chat

- 实现 `POST /api/v1/events/{eventId}/followup-chat/messages`
- 必须走 `build_context(user_id, event_id)`
- 从以下数据拼接上下文：
  - 近期 followup messages
  - snapshots
  - judge result
  - 可选 review 内容
- 写入 `followup_messages`
- 写入 `ai_call_logs`（可与 2 号协作接口）

验收标准：

- followup 接口不是直接裸调 AI
- 能返回 `reply + contextMeta`

#### 任务 C7：自动入历逻辑

- 明确 review 生成后的 calendar 入历规则
- 选择具体触发点：
  - judged 后立即生成
  - review 首次生成后入历
- 保证 `calendar_entries.review_id` 与 `event_id` 唯一约束不冲突

验收标准：

- 同一 event 不会生成重复 calendar entry

#### 任务 C8：小精灵转达接口

- 实现 `POST /api/v1/elf/relay`
- 校验 event 与双方关系
- 写入 `elf_messages`
- 返回润色后的 `finalMessage`

验收标准：

- 能落库
- 返回结构符合 API 契约

#### 任务 C9：过激语言检测与柔化

- 实现 `POST /api/v1/elf/moderate`
- 输出：
  - `blocked`
  - `riskLevel`
  - `suggestedMessage`
- 写入 `moderation_logs`

验收标准：

- moderate 接口至少能稳定返回结构化结果

### 6.5 3号交付物

- review 详情和编辑接口可用
- calendar 月历与日历详情接口可用
- followup chat 可用
- elf relay / moderate 可用
- review version 与 calendar entry 正常落库

### 6.6 3号风险点

- 最容易卡住的是 review 生成时机和 calendar 入历时机
- 如果不提前和 2 号约定 judged 后的数据流转，联调会反复改

## 7. 三人接口边界与依赖表

### 7.1 1号提供给 2号、3号的能力

- `get_current_user`
- 统一响应 envelope
- 错误码体系
- auth 可用 token
- 测试 fixture

### 7.2 2号提供给 3号的能力

- `events.status = judged` 的主链结果
- `judge_results`
- event 与 relationship 的权限判断模型

### 7.3 3号对 2号的依赖

- 3 号依赖 2 号提供稳定的 `judged` 数据
- 3 号不能自己定义一套 event 状态或 judge result 字段

## 8. 推荐排期

### 第 1 阶段：底座先行

- 1 号：
  - 完成 auth
  - 完成响应封装
  - 完成错误体系
  - 完成测试基建
- 2 号：
  - 完成 events 主链 schema / repo / service 骨架
- 3 号：
  - 完成 review / calendar / elf schema / repo / service 骨架

### 第 2 阶段：核心主链闭环

- 2 号：
  - 完成 create event / commit-a / invite / snapshot-a / b-agree / commit-b / judge-result
- 1 号：
  - 完善 refresh / logout / login log
- 3 号：
  - 开始联调 review 读取和 calendar 读取

### 第 3 阶段：结果沉淀与互动

- 3 号：
  - 完成 review detail / update / calendar / followup / elf
- 2 号：
  - 完成审计日志和 AI 调用日志补全
- 1 号：
  - 完成 seed 数据与联调收尾

## 9. 最终验收标准

项目后端完成度以以下三个闭环为准：

### 9.1 闭环一：认证闭环

- 用户可注册
- 用户可登录
- 用户可刷新 token
- 用户可登出

### 9.2 闭环二：事件主链闭环

- 创建 Event
- A 提交 Snapshot_A
- B 通过邀请页进入并登录
- B 查看 Snapshot_A
- B 同意或提交 Snapshot_B
- 系统生成 JudgeResult
- 可读取 JudgeResult

### 9.3 闭环三：复盘与日历闭环

- judged 后能读取 review
- review 可编辑并记录版本
- review 可进入 calendar
- 用户可继续 followup
- 用户可调用 elf relay / moderate

## 10. 建议落地方式

如果按最小返工策略推进，建议：

1. 先由 1 号把 auth、响应、异常、测试基建做完再开放联调。
2. 2 号先做同步版 judge，不等真实 AI。
3. 3 号先把 review/calendar/elf 的接口骨架写好，再等 judged 数据对接。
4. 所有人都以 `docs/openapi.yaml` 作为字段和路径唯一准绳。

