# LoveMediator 数据库设计文档（DB v1.0）

## 1. 文档信息
- 对应功能文档：`docs/FD_LoveMediator_v1.md`
- 对应接口文档：`docs/API_LoveMediator_v1.md`
- 数据库：PostgreSQL 16+
- 命名规范：表/字段使用 `snake_case`
- 时间规范：统一 `timestamptz`（UTC）

## 2. 设计目标
- 支撑登录注册、AI 调解、吵架日历、互动模块。
- 保证状态机可控、快照可冻结、结果可追溯。
- 为后续 API 实现提供可直接建表的结构。

## 3. 全局约定
- 每张业务表包含：`created_at`, `updated_at`。
- 关键数据采用软删除字段：`deleted_at`（按需）。
- 统一主键：`bigserial`。
- 对外标识统一：`public_id varchar(40)`（ULID/雪花ID/业务前缀均可）。
- 事件共享权限统一通过 `relationship_id` 控制。

## 4. 枚举定义

### 4.1 user_status
- `active`
- `locked`
- `disabled`

### 4.2 relationship_status
- `pending`
- `active`
- `closed`

### 4.3 event_status
- `draft`
- `waiting_b`
- `judged`
- `reviewed`
- `closed`

### 4.4 snapshot_side
- `a`
- `b`

### 4.5 moderation_risk_level
- `low`
- `medium`
- `high`

## 5. 表设计

### 5.1 用户与认证

#### 5.1.1 users
用途：账号主表。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `username varchar(32) not null unique`
- `password_hash varchar(255) not null`
- `status user_status not null default 'active'`
- `failed_login_count int not null default 0`
- `locked_until timestamptz null`
- `last_login_at timestamptz null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

索引：
- `ux_users_username (username)`
- `ix_users_status (status)`

#### 5.1.2 refresh_tokens
用途：刷新令牌管理与吊销。

字段：
- `id bigserial pk`
- `user_id bigint not null references users(id)`
- `token_hash varchar(128) not null unique`
- `expires_at timestamptz not null`
- `revoked_at timestamptz null`
- `created_at timestamptz not null default now()`

索引：
- `ux_refresh_tokens_token_hash (token_hash)`
- `ix_refresh_tokens_user_id (user_id)`
- `ix_refresh_tokens_expires_at (expires_at)`

#### 5.1.3 auth_login_logs
用途：登录审计、风控分析。

字段：
- `id bigserial pk`
- `user_id bigint null references users(id)`
- `username_input varchar(32) not null`
- `success boolean not null`
- `error_code varchar(20) null`
- `ip inet null`
- `user_agent text null`
- `created_at timestamptz not null default now()`

索引：
- `ix_auth_login_logs_user_id_created_at (user_id, created_at desc)`
- `ix_auth_login_logs_username_input_created_at (username_input, created_at desc)`

### 5.2 关系与事件

#### 5.2.1 relationships
用途：情侣绑定关系与共享域。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `user_a_id bigint not null references users(id)`
- `user_b_id bigint not null references users(id)`
- `status relationship_status not null default 'active'`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

约束：
- `check (user_a_id <> user_b_id)`
- 建议在应用层**约定有序对**：存库时保证 `user_a_id < user_b_id`，避免 `(A,B)` 与 `(B,A)` 视为不同记录。
- 唯一活跃关系推荐使用**部分唯一索引**保证：同一对用户在 `status='active'` 下最多一条记录（见 10 章 SQL 片段）。

索引：
- `ix_relationships_user_a_id (user_a_id)`
- `ix_relationships_user_b_id (user_b_id)`
- `ix_relationships_status (status)`

#### 5.2.2 events
用途：冲突事件主表（状态机锚点）。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `relationship_id bigint not null references relationships(id)`
- `initiator_user_id bigint not null references users(id)`
- `title varchar(120) null`
- `status event_status not null default 'draft'`
- `judged_at timestamptz null`
- `reviewed_at timestamptz null`
- `closed_at timestamptz null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

索引：
- `ix_events_relationship_status_created (relationship_id, status, created_at desc)`
- `ix_events_initiator_created (initiator_user_id, created_at desc)`

### 5.3 私有会话与冻结快照

#### 5.3.1 private_sessions
用途：A/B 私有分析会话。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `event_id bigint not null references events(id)`
- `user_id bigint not null references users(id)`
- `is_active boolean not null default true`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

索引：
- `ix_private_sessions_event_user (event_id, user_id)`

#### 5.3.2 private_messages
用途：私有会话消息记录（上下文短期记忆来源）。

字段：
- `id bigserial pk`
- `session_id bigint not null references private_sessions(id)`
- `sender_role varchar(10) not null`  
  取值建议：`user` / `assistant`
- `content text not null`
- `token_count int null`
- `created_at timestamptz not null default now()`

索引：
- `ix_private_messages_session_created (session_id, created_at desc)`

#### 5.3.3 event_snapshots
用途：A/B 冻结事实快照。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `event_id bigint not null references events(id)`
- `side snapshot_side not null`
- `summary text not null`
- `points_a jsonb not null default '[]'::jsonb`
- `points_b jsonb not null default '[]'::jsonb`
- `raw_payload jsonb null`
- `is_frozen boolean not null default true`
- `confirmed_by_user_id bigint not null references users(id)`
- `confirmed_at timestamptz not null default now()`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

约束：
- `unique (event_id, side)`（每个事件每侧仅一份快照）

索引：
- `ux_event_snapshots_event_side (event_id, side)`
- `ix_event_snapshots_confirmed_at (confirmed_at desc)`

不可变规则：
- `is_frozen=true` 后禁止更新 `summary/points_a/points_b/raw_payload`。
- 建议用 `before update trigger` 拦截。

### 5.4 裁判结果与后续对话

#### 5.4.1 judge_results
用途：事件裁判结论（只读展示，不实时重算）。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `event_id bigint not null unique references events(id)`
- `objective_summary text not null`
- `triggers jsonb not null default '[]'::jsonb`
- `misunderstandings jsonb not null default '[]'::jsonb`
- `advice_for_a jsonb not null default '[]'::jsonb`
- `advice_for_b jsonb not null default '[]'::jsonb`
- `model_name varchar(60) null`
- `input_tokens int null`
- `output_tokens int null`
- `created_at timestamptz not null default now()`

索引：
- `ux_judge_results_event_id (event_id)`
- `ix_judge_results_created_at (created_at desc)`

#### 5.4.2 followup_messages
用途：裁判后复盘问答记录。

字段：
- `id bigserial pk`
- `event_id bigint not null references events(id)`
- `user_id bigint not null references users(id)`
- `user_message text not null`
- `assistant_reply text not null`
- `context_meta jsonb null`  
  示例：`{"recentMessages":8,"snapshots":2,"judgeResults":1}`
- `created_at timestamptz not null default now()`

索引：
- `ix_followup_messages_event_created (event_id, created_at desc)`
- `ix_followup_messages_user_created (user_id, created_at desc)`

### 5.5 日历与复盘

#### 5.5.1 reviews
用途：复盘正文（自动生成后可编辑）。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `event_id bigint not null unique references events(id)`
- `relationship_id bigint not null references relationships(id)`
- `content text not null`
- `source varchar(20) not null default 'judge_result'`
- `created_by_user_id bigint null references users(id)`
- `updated_by_user_id bigint null references users(id)`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

索引：
- `ux_reviews_event_id (event_id)`
- `ix_reviews_relationship_updated (relationship_id, updated_at desc)`

#### 5.5.2 review_versions
用途：复盘编辑历史。

字段：
- `id bigserial pk`
- `review_id bigint not null references reviews(id)`
- `version_no int not null`
- `content text not null`
- `edited_by_user_id bigint not null references users(id)`
- `edited_at timestamptz not null default now()`

约束：
- `unique (review_id, version_no)`

索引：
- `ix_review_versions_review_id_version_no (review_id, version_no desc)`

#### 5.5.3 calendar_entries
用途：月历查询加速（按日期聚合）。

字段：
- `id bigserial pk`
- `review_id bigint not null unique references reviews(id)`
- `event_id bigint not null unique references events(id)`
- `relationship_id bigint not null references relationships(id)`
- `calendar_date date not null`
- `created_at timestamptz not null default now()`

索引：
- `ix_calendar_entries_relationship_date (relationship_id, calendar_date)`
- `ix_calendar_entries_date (calendar_date)`

### 5.6 互动模块（V1.5+）

#### 5.6.1 elf_messages
用途：小精灵代转达消息。

字段：
- `id bigserial pk`
- `public_id varchar(40) not null unique`
- `event_id bigint null references events(id)`
- `from_user_id bigint not null references users(id)`
- `to_user_id bigint not null references users(id)`
- `raw_message text not null`
- `final_message text not null`
- `delivered boolean not null default false`
- `delivered_at timestamptz null`
- `created_at timestamptz not null default now()`

索引：
- `ix_elf_messages_to_user_created (to_user_id, created_at desc)`

#### 5.6.2 moderation_logs
用途：过激语言检测与柔化审计。

字段：
- `id bigserial pk`
- `user_id bigint not null references users(id)`
- `raw_message text not null`
- `risk_level moderation_risk_level not null`
- `blocked boolean not null default false`
- `suggested_message text null`
- `created_at timestamptz not null default now()`

索引：
- `ix_moderation_logs_user_created (user_id, created_at desc)`
- `ix_moderation_logs_risk_level_created (risk_level, created_at desc)`

### 5.7 审计与可观测

#### 5.7.1 event_state_logs
用途：事件状态流转审计。

字段：
- `id bigserial pk`
- `event_id bigint not null references events(id)`
- `from_status event_status not null`
- `to_status event_status not null`
- `action varchar(40) not null`  
  示例：`commit_a`（A 确认快照）、`judge`（裁判完成，含 b-agree 和 commit-b 两条路径）、`close_event`（关闭事件，待实现）。注：当前代码中 b-agree 与 commit-b 统一使用 `judge` 作为 action（见 `services/event_service._execute_judge`）。
- `operator_user_id bigint null references users(id)`
- `trace_id varchar(64) null`
- `created_at timestamptz not null default now()`

索引：
- `ix_event_state_logs_event_created (event_id, created_at desc)`

#### 5.7.2 ai_call_logs
用途：LLM 调用审计和成本统计。

字段：
- `id bigserial pk`
- `event_id bigint null references events(id)`
- `scene varchar(40) not null`  
  示例：`private_chat`, `judge`, `followup`
- `model_name varchar(60) not null`
- `input_tokens int not null default 0`
- `output_tokens int not null default 0`
- `success boolean not null`
- `error_code varchar(40) null`
- `trace_id varchar(64) null`
- `created_at timestamptz not null default now()`

索引：
- `ix_ai_call_logs_event_created (event_id, created_at desc)`
- `ix_ai_call_logs_scene_created (scene, created_at desc)`

## 6. 关键约束与事务边界

### 6.1 commit_a（A 冻结）
同一事务内：
0. 对目标事件加**行级锁**：`select * from events where id = ? for update;`
1. 校验 `events.status='draft'`。
2. 插入 `event_snapshots(side='a')`。
3. 更新 `events.status='waiting_b'`。
4. 写入 `event_state_logs`。

### 6.2 b_agree（B 同意）
同一事务内：
0. 对目标事件加**行级锁**：`select * from events where id = ? for update;`
1. 校验 `events.status='waiting_b'` 且存在 snapshot_a。
2. 生成并插入 `judge_results`（若已存在则按幂等策略处理，避免重复生成）。
3. 更新 `events.status='judged'`, `judged_at=now()`。
4. 写入 `event_state_logs`。

### 6.3 commit_b（B 不同意后提交）
同一事务内：
0. 对目标事件加**行级锁**：`select * from events where id = ? for update;`
1. 校验 `events.status='waiting_b'`。
2. 插入 `event_snapshots(side='b')`。
3. 生成并插入 `judge_results`（若已存在则按幂等策略处理）。
4. 更新 `events.status='judged'`。
5. 写入 `event_state_logs`。

### 6.4 复盘编辑
同一事务内：
1. 更新 `reviews.content/updated_by_user_id/updated_at`。
2. 插入 `review_versions` 新版本。

## 7. 查询与索引策略
- 月历页：走 `calendar_entries(relationship_id, calendar_date)`。
- 事件详情：走 `events.public_id` + `relationship_id`。
- 结果页：`judge_results.event_id unique` 直查。
- 私有会话最近消息：`private_messages(session_id, created_at desc)`。
- 风控：`auth_login_logs(username_input, created_at desc)`。

## 8. API 到表映射
- `POST /auth/register` -> `users`
- `POST /auth/login` -> `users`, `auth_login_logs`, `refresh_tokens`
- `POST /auth/refresh` -> `refresh_tokens`
- `POST /auth/logout` -> `refresh_tokens`
- `POST /events` -> `events`
- `POST /events/{id}/private-chat/messages` -> `private_sessions`, `private_messages`, `ai_call_logs`（⚠ 未实现）
- `POST /events/{id}/commit-a` -> `event_snapshots`, `events`, `event_state_logs`
- `GET /events/{id}/invite` -> `events`（只读，无需鉴权）
- `GET /events/{id}/snapshot-a` -> `event_snapshots`（只读）
- `POST /events/{id}/b-agree` -> `judge_results`, `events`, `event_state_logs`, `ai_call_logs`, `reviews`, `calendar_entries`
- `POST /events/{id}/commit-b` -> `event_snapshots`, `judge_results`, `events`, `event_state_logs`, `ai_call_logs`, `reviews`, `calendar_entries`
- `GET /events/{id}/judge-result` -> `judge_results`（只读）
- `POST /events/{id}/followup-chat/messages` -> `followup_messages`, `ai_call_logs`
- `GET /calendar` -> `calendar_entries`
- `GET /calendar/days/{date}/reviews` -> `calendar_entries`, `reviews`
- `GET /reviews/{id}` -> `reviews`
- `PUT /reviews/{id}` -> `reviews`, `review_versions`
- `POST /elf/relay` -> `elf_messages`
- `POST /elf/moderate` -> `moderation_logs`

## 9. 数据保留与清理建议
- `auth_login_logs`：保留 180 天。
- `ai_call_logs`：保留 365 天（成本分析）。
- `private_messages`：默认保留 365 天，可配置。
- `moderation_logs`：保留 180 天。
- 通过定时任务归档或清理历史数据。

## 10. 建表 SQL 骨架（核心片段）
```sql
create table users (
  id bigserial primary key,
  public_id varchar(40) not null unique,
  username varchar(32) not null unique,
  password_hash varchar(255) not null,
  status varchar(16) not null default 'active',
  failed_login_count int not null default 0,
  locked_until timestamptz,
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (status in ('active','locked','disabled'))
);

create table events (
  id bigserial primary key,
  public_id varchar(40) not null unique,
  relationship_id bigint not null references relationships(id),
  initiator_user_id bigint not null references users(id),
  title varchar(120),
  status varchar(16) not null default 'draft',
  judged_at timestamptz,
  reviewed_at timestamptz,
  closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (status in ('draft','waiting_b','judged','reviewed','closed'))
);

-- relationships 正确约束（推荐版本）：
-- 1）业务约定：入库前保证 user_a_id < user_b_id，避免 (A,B) / (B,A) 重复；
-- 2）部分唯一索引：同一对用户在 active 状态下最多一条记录。
create unique index ux_relationships_active_pair
  on relationships(user_a_id, user_b_id)
  where status = 'active';

create table event_snapshots (
  id bigserial primary key,
  public_id varchar(40) not null unique,
  event_id bigint not null references events(id),
  side varchar(2) not null,
  summary text not null,
  points_a jsonb not null default '[]'::jsonb,
  points_b jsonb not null default '[]'::jsonb,
  raw_payload jsonb,
  is_frozen boolean not null default true,
  confirmed_by_user_id bigint not null references users(id),
  confirmed_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (event_id, side),
  check (side in ('a','b'))
);

create table judge_results (
  id bigserial primary key,
  public_id varchar(40) not null unique,
  event_id bigint not null unique references events(id),
  objective_summary text not null,
  triggers jsonb not null default '[]'::jsonb,
  misunderstandings jsonb not null default '[]'::jsonb,
  advice_for_a jsonb not null default '[]'::jsonb,
  advice_for_b jsonb not null default '[]'::jsonb,
  model_name varchar(60),
  input_tokens int,
  output_tokens int,
  created_at timestamptz not null default now()
);
```

## 11. 下一步实现建议
- 先落 Alembic 首版迁移（Auth + Events + Snapshots + Judge + Reviews）。
- 再补审计表与互动表，避免首版范围过大。
- 迁移后执行最小数据种子，联调 `auth -> event -> commit -> judge -> calendar` 主链路。
