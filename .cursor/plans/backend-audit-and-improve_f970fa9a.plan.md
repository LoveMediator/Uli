---
name: backend-audit-and-improve
overview: 基于对 1/2/3 号全部代码的只读审查，汇报完成度、发现的可优化项与安全风险，并给出具体修复建议。
todos:
  - id: fix-b-agree-validation
    content: "P0: b_agree 未校验 agree 字段值，commit_b 未对 snapshot_a 缺失做保护"
    status: completed
  - id: fix-login-lock-unlock
    content: "P1: 修复登录锁定后永不自动解除的问题"
    status: completed
  - id: fix-refresh-check-status
    content: "P1: refresh_access_token 增加用户状态校验"
    status: completed
  - id: fix-weak-default-key
    content: "P1: 消除 config.py 弱默认密钥"
    status: completed
  - id: fix-code-quality
    content: "P2: followup 审计日志走 audit_repo、reviews 事件缺失处理、context_builder 复用 repo"
    status: completed
isProject: false
---

# 1/2/3 号后端审查报告与优化计划

## 一、完成度总览

### 1 号底座（认证 + 公共能力）— 完成度约 85%

- auth 4 接口（register/login/refresh/logout）已可用
- 统一 envelope、错误码、异常处理器、JWT 依赖注入、路由聚合、测试基建、seed 脚本均已落地
- **缺口**：auth 响应字段与 `docs/openapi.yaml` 有偏差（缺 `expiresIn`、`user` 嵌套等），但不影响联调闭环

### 2 号事件主链 — 完成度约 90%

- 7 个主链端点 + followup 共 8 个端点全部落地
- 状态机 `draft -> waiting_b -> judged` 正确实现
- `judge-result` 只读查库、不触发 AI（已验证）
- `event_state_logs` 和 `ai_call_logs` 在关键状态变更时写入
- judged 后自动调用 `create_review_from_judge` 沉淀 review + calendar
- **缺口**：`b_agree` 未校验 `agree` 字段值；`commit_b` 在 `snapshot_a` 缺失时缺保护；`private-chat`（MED-FR-001）未实现

### 3 号复盘/日历/互动 — 完成度约 92%

- reviews（GET/PUT）、calendar（month/day）、elf（relay/moderate）路由全部落地
- 所有路由统一使用 `CurrentActiveUser` + `ApiEnvelope`
- followup 正确挂在 events 路由下
- `create_review_from_judge` 串联点正确
- **缺口**：`reviews.get_review` 在事件缺失时返回空 `eventId`；followup 的 `AiCallLog` 写入未走 `audit_repo`（风格不一致）

---

## 二、发现的代码问题（需修复）

### 优先级 P0（功能性 Bug）

1. `**b_agree` 未校验 `agree` 字段** — [backend/app/services/event_service.py](backend/app/services/event_service.py)
  - 路由接收 `BAgreeRequest(agree: bool)` 但 service 函数完全忽略该字段
  - `agree=false` 时仍会触发裁判，违反 API 契约 §5.6
  - 修复：在 `b_agree` 中检查 `agree` 参数，为 `false` 时抛 `InvalidParamsError`
2. `**commit_b` 未对 `snapshot_a` 缺失做保护** — [backend/app/services/event_service.py](backend/app/services/event_service.py)
  - `commit_b` 取 `snapshot_a` 后直接传入 `_execute_judge`，若 `snapshot_a is None`（理论上不应出现但需防御），会在 `judge_service` 中对 `None.summary` 抛未捕获异常
  - 修复：添加与 `b_agree` 相同的 `snapshot_a is None` 检查

### 优先级 P1（安全风险）

1. **登录锁定后永久不解除** — [backend/app/services/auth_service.py](backend/app/services/auth_service.py)
  - `locked_until` 字段已写入，但登录流程中 **未检查是否已过期**；一旦 `status=LOCKED`，用户永远无法重新登录
  - 修复：在 `login_user` 中，当 `status == LOCKED` 且 `locked_until < now` 时自动恢复为 `ACTIVE`
2. `**refresh_access_token` 未校验用户状态** — [backend/app/services/auth_service.py](backend/app/services/auth_service.py)
  - 锁定/禁用用户的未过期 refresh token 仍可换发 access token
  - 修复：在 `refresh_access_token` 中获取用户后检查 `status == ACTIVE`
3. `**config.py` 默认 `secret_key` 为固定弱值** — [backend/app/core/config.py](backend/app/core/config.py)
  - `secret_key` 默认 `"0123456789abcdef0123456789abcdef"`，若生产未覆盖环境变量等同硬编码
  - 修复：去掉默认值或在启动时检测并警告

### 优先级 P2（代码质量 / 一致性）

1. `**followup_service` 直接 `db.add(AiCallLog(...))` 而非调用 `audit_repo.create_ai_call_log`** — [backend/app/services/followup_service.py](backend/app/services/followup_service.py)
  - 与 `event_service` 中使用 `audit_repo` 的模式不一致
  - 修复：改为调用 `audit_repo.create_ai_call_log`
2. `**reviews.get_review` 在关联事件缺失时返回空 `eventId`** — [backend/app/api/v1/reviews.py](backend/app/api/v1/reviews.py)
  - `event_public_id = event.public_id if event else ""`
  - 修复：事件不存在时应抛 `NotFoundError`（review 必有关联 event）
3. `**context_builder` 中近期消息查询与 `followup_repo.get_recent_messages` 重复** — [backend/app/utils/context_builder.py](backend/app/utils/context_builder.py)
  - 修复：复用 `followup_repo.get_recent_messages`

---

## 三、安全建议

### 已做好的安全措施

- bcrypt 密码哈希
- JWT 中指定 `algorithms` 和 `require` 字段，防算法混淆
- refresh token 入库用 sha256 摘要存储，明文不落库
- 双层权限校验（路由层 `CurrentActiveUser` + 服务层 `assert_relationship_member`）
- `.gitignore` 正确忽略 `.env`、`__pycache`__、`.pyc`

### 建议加强的安全措施


| 措施                       | 说明                            | 优先级 |
| ------------------------ | ----------------------------- | --- |
| 修复登录锁定自动解除逻辑             | 见 P1-3                        | 高   |
| refresh 时校验用户状态          | 见 P1-4                        | 高   |
| 消除 `config.py` 弱默认密钥     | 见 P1-5                        | 高   |
| 添加 CORS 中间件              | `main.py` 未配置，前端联调将被浏览器拦截     | 中   |
| JWT 添加 `iss`/`aud` 声明    | 多环境/多服务时防止令牌误用                | 低   |
| refresh token 轮换         | 当前刷新不废旧，泄露后长期有效               | 中   |
| 注册接口增加 `confirmPassword` | 与 openapi.yaml 对齐             | 低   |
| 请求限速（rate limiting）      | `RateLimitedError` 已定义但无实际中间件 | 低   |


---

## 四、测试覆盖缺口

### 已有测试

- 异常处理器、envelope 契约、事件主链 service（8 用例）、judge service（2 用例）、review/calendar/interaction service、events/reviews/calendar/elf API 路由

### 缺失的关键测试

- auth_service 全链路（注册/登录失败锁定/刷新/登出）
- security.py 错误路径（过期 token、错误 token_type）
- commit_b 完整流程（双快照 + 裁判）
- 横向越权（非关系成员访问 calendar/reviews 应 403）
- get_invite / get_snapshot_a 边界（状态组合）

