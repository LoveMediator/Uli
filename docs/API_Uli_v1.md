# Uli API 设计文档（API v1.0）

## 1. 文档信息
- 对应功能文档：`docs/FD_Uli_v1.md`
- API 前缀：`/api/v1`
- 数据格式：`application/json; charset=utf-8`
- 鉴权方式：Bearer JWT（`Authorization: Bearer <access_token>`）

## 2. 全局规范

### 2.1 统一响应结构
成功：
```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

失败：
```json
{
  "code": 2001,
  "message": "用户名或密码错误",
  "data": null
}
```

### 2.2 时间与 ID 规范
- 时间字段统一为 ISO8601（UTC），如 `2026-02-12T08:30:00Z`。
- 业务对象 ID 用字符串返回（内部可为 bigint/uuid）。
- 路径中的 `eventId`、`reviewId`、`relationshipId`、`userId` 均表示对外公开 ID（`public_id`），不是数据库自增主键。

### 2.3 鉴权规范
- 需要登录的接口必须携带 `Authorization` 头。
- `access_token` 过期后通过 refresh 接口换新。
- 分享链接仅用于打开邀请页或跳转注册/登录，不直接授予业务接口访问权限。

### 2.4 通用错误码
- `1001` 参数校验失败
- `1002` 资源不存在
- `1003` 状态不允许该操作
- `2001` 认证失败（未登录/凭证无效）
- `2002` 无权限访问资源
- `2003` 账号锁定或禁用
- `2004` 请求过频（限流）
- `3001` 用户名已存在
- `3002` 快照已冻结不可修改
- `3003` 事件尚未满足分析前置条件
- `5000` 系统内部错误

## 3. 状态与枚举

### 3.1 EventStatus
- `draft`
- `waiting_b`
- `judged`
- `reviewed`
- `closed`

### 3.2 UserStatus
- `active`
- `locked`
- `disabled`

## 4. 大模块一：登录注册 API（AUTH）

### 4.1 注册（AUTH-FR-001）
- 方法与路径：`POST /api/v1/auth/register`
- 鉴权：否
- 请求体：
```json
{
  "username": "alice_01",
  "password": "Pass123456",
  "confirmPassword": "Pass123456"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "userId": "u_1001",
    "username": "alice_01",
    "status": "active"
  }
}
```
- 业务错误：`1001` `3001` `5000`

### 4.2 登录（AUTH-FR-002）
- 方法与路径：`POST /api/v1/auth/login`
- 鉴权：否
- 请求体：
```json
{
  "username": "alice_01",
  "password": "Pass123456"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "accessToken": "jwt_access_xxx",
    "refreshToken": "jwt_refresh_xxx",
    "expiresIn": 3600,
    "user": {
      "userId": "u_1001",
      "username": "alice_01",
      "status": "active"
    }
  }
}
```
- 业务错误：`1001` `2001` `2003` `2004` `5000`

### 4.3 刷新 token（AUTH-FR-004）
- 方法与路径：`POST /api/v1/auth/refresh`
- 鉴权：否（依赖 refresh token）
- 请求体：
```json
{
  "refreshToken": "jwt_refresh_xxx"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "accessToken": "jwt_access_new",
    "expiresIn": 3600
  }
}
```
- 业务错误：`2001` `5000`

### 4.4 登出（AUTH-FR-004）
- 方法与路径：`POST /api/v1/auth/logout`
- 鉴权：是
- 请求体：
```json
{
  "refreshToken": "jwt_refresh_xxx"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "success": true
  }
}
```
- 业务错误：`2001` `5000`

## 5. 大模块二：AI 调解 API（MED）

### 5.1 A 开启私有分析会话（MED-FR-001）
- 方法与路径：`POST /api/v1/relationships/{relationshipId}/analysis-sessions/a`
- 鉴权：是（仅关系参与者本人）
- 说明：创建或恢复 A 的临时私有分析会话；此阶段不创建 `Event`，不写共享快照。
- 成功响应中的 `data` 至少包含：`sessionId`、`phase='a'`、`relationshipId`、`expiresAt`、`messages`
- 业务错误：`1002` `2002` `1003` `5000`

### 5.2 私有分析会话发消息（MED-FR-001）
- 方法与路径：`POST /api/v1/analysis-sessions/{sessionId}/messages`
- 鉴权：是（仅会话所属用户）
- 说明：读取 Redis 临时会话、调用 AI、将本轮 user/assistant 消息回写到缓存；不写共享快照。
- 请求体：
```json
{
  "message": "我们昨天因为家务吵架..."
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "sessionId": "as_001",
    "reply": "我先帮你把事实和感受拆开。"
  }
}
```
- 业务错误：`1001` `1003` `2001` `2002` `5000`

### 5.3 确认私有分析并进入正式事件流（MED-FR-002）
- 方法与路径：`POST /api/v1/analysis-sessions/{sessionId}/commit`
- 鉴权：是（仅会话所属用户）
- 说明：
  - A 会话确认：从当前会话生成结构化事实，事务内创建 `Event + Snapshot_A`，并把状态置为 `waiting_b`
  - B 会话确认：从当前会话生成 `Snapshot_B`，随后裁判并把状态置为 `judged`
- 说明：`POST /api/v1/events`、`POST /api/v1/events/{eventId}/commit-a`、`POST /api/v1/events/{eventId}/commit-b` 已降级为兼容旧流程的废弃入口，不再是标准主路径。
- 请求体：
```json
{}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "eventId": "ev_001",
    "status": "waiting_b"
  }
}
```
- 业务错误：`1003` `2002` `5000`

### 5.4 获取邀请页信息（MED-FR-003）
- 方法与路径：`GET /api/v1/events/{eventId}/invite`
- 鉴权：否
- 说明：通过分享链接进入时使用。仅返回邀请页展示所需的最小信息，不返回 Snapshot_A 正文，不绕过登录。
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "eventId": "ev_001",
    "status": "waiting_b",
    "title": "2月争吵",
    "inviteMessage": "对方邀请你参与本次事件，请先登录后继续。",
    "requiresAuth": true
  }
}
```
- 业务错误：`1002` `1003` `5000`

### 5.5 获取 B 预览的 Snapshot_A（MED-FR-003）
- 方法与路径：`GET /api/v1/events/{eventId}/snapshot-a`
- 鉴权：是（仅 A 或已登录的 B）
- 说明：B 必须先通过分享链接完成注册或登录，再访问该接口。
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "eventId": "ev_001",
    "status": "waiting_b",
    "snapshotA": {
      "summary": "...",
      "pointsA": ["..."],
      "pointsB": ["..."]
    }
  }
}
```
- 业务错误：`1002` `2002` `5000`

### 5.6 B 同意并触发裁判（MED-FR-003, MED-FR-004）
- 方法与路径：`POST /api/v1/events/{eventId}/b-agree`
- 鉴权：是（仅已登录的 B）
- 说明：B 必须先登录；内部执行 `judge(snapshot_A, inferred_snapshot_B)`。
- 请求体：
```json
{
  "agree": true
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "eventId": "ev_001",
    "status": "judged",
    "judgeResultId": "jr_001"
  }
}
```
- 业务错误：`1003` `2002` `3003` `5000`

### 5.7 B 提交 Snapshot_B 并触发裁判（MED-FR-003, MED-FR-004）
- 方法与路径：`POST /api/v1/events/{eventId}/commit-b`
- 鉴权：是（仅已登录的 B）
- 说明：B 必须先登录，再提交自己的 Snapshot_B。
- 请求体：
```json
{
  "summary": "我认为争吵是因为沟通方式...",
  "pointsA": ["..."],
  "pointsB": ["..."]
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "eventId": "ev_001",
    "status": "judged",
    "snapshotBId": "sb_001",
    "judgeResultId": "jr_001"
  }
}
```
- 业务错误：`1001` `1003` `2002` `5000`

### 5.8 获取裁判结果（MED-FR-005）
- 方法与路径：`GET /api/v1/events/{eventId}/judge-result`
- 鉴权：是（仅关系双方）
- 说明：只读落库结果，不触发实时 LLM。
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "judgeResultId": "jr_001",
    "eventId": "ev_001",
    "status": "judged",
    "objectiveSummary": "...",
    "analysis": {
      "triggers": ["..."],
      "misunderstandings": ["..."],
      "adviceForA": ["..."],
      "adviceForB": ["..."]
    },
    "createdAt": "2026-02-12T09:00:00Z"
  }
}
```
- 业务错误：`1002` `2002` `3003` `5000`

### 5.9 复盘聊天（MED-FR-006）
- 方法与路径：`POST /api/v1/events/{eventId}/followup-chat/messages`
- 鉴权：是
- 说明：服务端执行 `build_context(user_id, event_id)` 拼接上下文后调用 LLM。
- 请求体：
```json
{
  "message": "以后类似问题我们怎么避免？"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "reply": "结合你们确认的事实，我建议...",
    "contextMeta": {
      "recentMessages": 8,
      "snapshots": 2,
      "judgeResults": 1
    }
  }
}
```
- 业务错误：`1001` `1002` `2002` `5000`

## 6. 大模块三：吵架日历 API（CAL）

### 6.1 月历查询（CAL-FR-002）
- 方法与路径：`GET /api/v1/calendar?month=2026-02&relationshipId=rel_001`
- 鉴权：是
- 必填查询参数：`month`（格式 `YYYY-MM`）、`relationshipId`（关系 public_id，用于区分多关系场景）
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "month": "2026-02",
    "days": [
      { "date": "2026-02-03", "count": 1 },
      { "date": "2026-02-09", "count": 2 }
    ]
  }
}
```
- 业务错误：`1001` `2001` `5000`

### 6.2 日期复盘列表（CAL-FR-002）
- 方法与路径：`GET /api/v1/calendar/days/{date}/reviews?relationshipId=rel_001`
- 鉴权：是
- 必填查询参数：`relationshipId`（关系 public_id）
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "date": "2026-02-09",
    "items": [
      {
        "reviewId": "rv_001",
        "eventId": "ev_001",
        "title": "2月争吵",
        "updatedAt": "2026-02-09T15:20:00Z"
      }
    ]
  }
}
```
- 业务错误：`1001` `2002` `5000`

### 6.3 复盘详情（CAL-FR-001, CAL-FR-002）
- 方法与路径：`GET /api/v1/reviews/{reviewId}`
- 鉴权：是
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "reviewId": "rv_001",
    "eventId": "ev_001",
    "content": "...",
    "source": "judge_result",
    "createdAt": "2026-02-09T15:00:00Z",
    "updatedAt": "2026-02-09T15:20:00Z"
  }
}
```
- 业务错误：`1002` `2002` `5000`

### 6.4 编辑复盘（CAL-FR-003）
- 方法与路径：`PUT /api/v1/reviews/{reviewId}`
- 鉴权：是
- 请求体：
```json
{
  "content": "复盘后更新：以后先冷静10分钟再沟通。"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "reviewId": "rv_001",
    "updatedAt": "2026-02-12T10:00:00Z",
    "updatedBy": "u_1001"
  }
}
```
- 业务错误：`1001` `1002` `2002` `5000`

## 7. 大模块四：互动 API（IM，V1.5+）

### 7.1 代转达消息（IM-FR-001）
- 方法与路径：`POST /api/v1/elf/relay`
- 鉴权：是
- 请求体：
```json
{
  "eventId": "ev_001",
  "targetUserId": "u_1002",
  "rawMessage": "帮我告诉他我不想吵架"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "messageId": "msg_001",
    "delivered": true,
    "finalMessage": "你的 Ta 想和你和好，不要再吵啦。"
  }
}
```
- 业务错误：`1001` `2002` `5000`

### 7.2 过激语言检测与柔化（IM-FR-002）
- 方法与路径：`POST /api/v1/elf/moderate`
- 鉴权：是
- 请求体：
```json
{
  "rawMessage": "你总是这样，别说话了"
}
```
- 成功响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "blocked": false,
    "riskLevel": "medium",
    "suggestedMessage": "我现在情绪有点上来，想先冷静一下再沟通。"
  }
}
```
- 业务错误：`1001` `5000`

## 8. FR 与 API 映射
- AUTH-FR-001 -> `POST /api/v1/auth/register`
- AUTH-FR-002 -> `POST /api/v1/auth/login`
- AUTH-FR-003 -> 登录接口内限流与锁定策略
- AUTH-FR-004 -> `POST /api/v1/auth/logout`, `POST /api/v1/auth/refresh`
- MED-FR-001 -> `POST /api/v1/relationships/{relationshipId}/analysis-sessions/a`, `POST /api/v1/events/{eventId}/analysis-sessions/b`, `POST /api/v1/analysis-sessions/{sessionId}/messages`
- MED-FR-002 -> `POST /api/v1/analysis-sessions/{sessionId}/commit`
- MED-FR-003 -> `GET /api/v1/events/{eventId}/invite`, `GET /api/v1/events/{eventId}/snapshot-a`, `POST /api/v1/events/{eventId}/b-agree`, `POST /api/v1/events/{eventId}/analysis-sessions/b`
- MED-FR-004 -> 裁判生成由 `b-agree/commit-b` 内部触发
- MED-FR-005 -> `GET /api/v1/events/{eventId}/judge-result`
- MED-FR-006 -> `POST /api/v1/events/{eventId}/followup-chat/messages`
- CAL-FR-001 -> 自动入历（内部流程）+ `GET /api/v1/reviews/{reviewId}`
- CAL-FR-002 -> `GET /api/v1/calendar`, `GET /api/v1/calendar/days/{date}/reviews`
- CAL-FR-003 -> `PUT /api/v1/reviews/{reviewId}`
- IM-FR-001 -> `POST /api/v1/elf/relay`
- IM-FR-002 -> `POST /api/v1/elf/moderate`

## 9. 实现约束
- `GET /api/v1/events/{eventId}/judge-result` 严禁实时触发 LLM。
- `commit-a` 后 Snapshot_A 不可更新。
- 所有事件读写必须校验 relationship 可见范围。
- 分享链接只允许打开邀请页，不允许绕过登录直接访问业务接口。
- followup chat 必须走 `build_context(user_id, event_id)`。
