# Models 说明文档（与 docs/DB_Uli_v1.md 对齐）

## 1. users
- id: 主键
- public_id: 公开ID（对外使用）
- username: 用户名（唯一）
- password_hash: 密码哈希
- status: 账号状态（active/locked/disabled）
- failed_login_count: 连续失败次数
- locked_until: 锁定截止时间
- last_login_at: 上次登录时间
- created_at: 创建时间
- updated_at: 更新时间

## 2. refresh_tokens
- id: 主键
- user_id: 关联用户ID（FK -> users.id）
- token_hash: 刷新令牌哈希（唯一）
- expires_at: 过期时间
- revoked_at: 吊销时间
- created_at: 创建时间

## 3. auth_login_logs
- id: 主键
- user_id: 关联用户ID（可空，FK -> users.id）
- username_input: 登录输入用户名
- success: 是否成功
- error_code: 错误码
- ip: 登录IP（INET）
- user_agent: 浏览器信息
- created_at: 创建时间

## 4. relationships
- id: 主键
- public_id: 公开ID
- user_a_id: 用户A（FK -> users.id）
- user_b_id: 用户B（FK -> users.id）
- status: 关系状态
- created_at: 创建时间
- updated_at: 更新时间

## 5. events
- id: 主键
- public_id: 公开ID
- relationship_id: 关系ID（FK -> relationships.id）
- initiator_user_id: 发起人ID（FK -> users.id）
- title: 事件标题
- status: 事件状态
- judged_at: 裁判完成时间
- reviewed_at: 复盘完成时间
- closed_at: 关闭时间
- created_at: 创建时间
- updated_at: 更新时间

## 6. event_snapshots
- id: 主键
- public_id: 公开ID
- event_id: 事件ID（FK -> events.id）
- side: A/B 快照侧（唯一约束：event_id + side）
- summary: 客观摘要
- points_a: A方观点要点（JSONB）
- points_b: B方观点要点（JSONB）
- raw_payload: 原始结构化内容（JSONB）
- is_frozen: 是否冻结
- confirmed_by_user_id: 确认人（FK -> users.id）
- confirmed_at: 确认时间
- created_at: 创建时间
- updated_at: 更新时间

## 7. judge_results
- id: 主键
- public_id: 公开ID
- event_id: 事件ID（唯一，FK -> events.id）
- objective_summary: 客观摘要
- triggers: 触发点（JSONB）
- misunderstandings: 误解点（JSONB）
- advice_for_a: 给A建议（JSONB）
- advice_for_b: 给B建议（JSONB）
- model_name: 模型名称
- input_tokens: 输入token
- output_tokens: 输出token
- created_at: 创建时间

## 8. private_sessions
- id: 主键
- public_id: 公开ID
- event_id: 事件ID（FK -> events.id）
- user_id: 用户ID（FK -> users.id）
- is_active: 是否活跃
- created_at: 创建时间
- updated_at: 更新时间

## 9. private_messages
- id: 主键
- session_id: 会话ID（FK -> private_sessions.id）
- sender_role: 发送角色
- content: 消息内容
- token_count: token 数量
- created_at: 创建时间

## 10. followup_messages
- id: 主键
- event_id: 事件ID（FK -> events.id）
- user_id: 用户ID（FK -> users.id）
- user_message: 用户输入
- assistant_reply: AI 回复
- context_meta: 上下文信息（JSONB）
- created_at: 创建时间

## 11. reviews
- id: 主键
- public_id: 公开ID
- event_id: 事件ID（唯一，FK -> events.id）
- relationship_id: 关系ID（FK -> relationships.id）
- content: 复盘正文
- source: 来源
- created_by_user_id: 创建人（FK -> users.id）
- updated_by_user_id: 更新人（FK -> users.id）
- created_at: 创建时间
- updated_at: 更新时间

## 12. review_versions
- id: 主键
- review_id: 复盘ID（FK -> reviews.id）
- version_no: 版本号（唯一约束：review_id + version_no）
- content: 版本内容
- edited_by_user_id: 编辑人（FK -> users.id）
- edited_at: 编辑时间

## 13. calendar_entries
- id: 主键
- review_id: 复盘ID（唯一，FK -> reviews.id）
- event_id: 事件ID（唯一，FK -> events.id）
- relationship_id: 关系ID（FK -> relationships.id）
- calendar_date: 日历日期（Date）
- created_at: 创建时间

## 14. event_state_logs
- id: 主键
- event_id: 事件ID（FK -> events.id）
- from_status: 变更前状态（event_status）
- to_status: 变更后状态（event_status）
- action: 动作标识
- operator_user_id: 操作人（FK -> users.id）
- trace_id: 追踪ID
- created_at: 创建时间

## 15. ai_call_logs
- id: 主键
- event_id: 事件ID（可空，FK -> events.id）
- scene: 场景
- model_name: 模型名称
- input_tokens: 输入token
- output_tokens: 输出token
- success: 是否成功
- error_code: 错误码
- trace_id: 追踪ID
- created_at: 创建时间

## 16. elf_messages
- id: 主键
- public_id: 公开ID
- event_id: 事件ID（可空，FK -> events.id）
- from_user_id: 发送方（FK -> users.id）
- to_user_id: 接收方（FK -> users.id）
- raw_message: 原始消息
- final_message: 润色后消息
- delivered: 是否送达
- delivered_at: 送达时间
- created_at: 创建时间

## 17. moderation_logs
- id: 主键
- user_id: 用户ID（FK -> users.id）
- raw_message: 原始消息
- risk_level: 风险等级
- blocked: 是否拦截
- suggested_message: 建议文本
- created_at: 创建时间
