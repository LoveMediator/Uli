# Kimi 后端接入笔记

更新时间：2026-03-27  
适用范围：LoveMediator 后端私聊分析能力接入  
资料来源：Moonshot / Kimi 官方站点公开资料

## 1. 这份文档解决什么问题

这份文档只整理当前项目接入 Kimi 私聊功能最关键的官方信息，目标不是覆盖官网全部能力，而是回答下面这些工程问题：

- 后端应该怎么接 Kimi
- API Key 应该放在哪
- 多轮对话的上下文到底由谁维护
- thinking 模型有什么额外注意事项
- Context Caching 适不适合当前私聊场景
- 工具调用现在要不要接进私聊主链路

当前代码里最直接相关的入口是：

- `backend/app/services/ai_service.py`
- `backend/app/services/analysis_session_service.py`

目前 `ai_service.call_llm` 还是 mock，实现真 AI 时建议以这里作为统一出口。

## 2. 接入基础

### 2.1 认证和请求入口

根据官方快速入门：

- Kimi API 使用 API Key 认证
- 认证方式是 `Bearer Token`
- 聊天主入口是 `POST https://api.moonshot.cn/v1/chat/completions`

对当前后端的含义：

- API Key 只放后端环境变量，不放前端，不写死进仓库
- 每次请求都由后端代发，前端不直接调用 Kimi
- 建议把 Kimi 配置抽到 `Settings` 中，例如：

```env
KIMI_API_KEY=replace_with_new_key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

注意：

- 你之前贴出来的旧 key 应视为已泄露，应该撤销并重建
- Key 只用于认证，不负责“记住上下文”
- 模型名以平台控制台和最新官方文档为准；上面的 `kimi-k2.5` 是当前项目计划使用的目标值，不代表官方博客中的所有示例模型名

### 2.2 OpenAI 兼容模式

官方快速入门明确说明，Kimi 兼容 OpenAI 风格接口，示例使用的也是 OpenAI Python SDK。

这对当前项目的直接意义是：

- 后端可以直接使用 `openai>=1.0`
- `ai_service.py` 不需要自造底层 HTTP SDK
- 你只需要替换三项配置：
  - `api_key`
  - `base_url`
  - `model`

推荐的后端调用骨架：

```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.kimi_api_key,
    base_url=settings.kimi_base_url,
)

completion = client.chat.completions.create(
    model=settings.kimi_model,
    messages=messages,
)
```

## 3. 多轮对话和上下文

### 3.1 上下文不是 API Key 提供的

官方快速入门和 thinking 模型文章都表明，Kimi 的多轮对话依赖 `messages`。也就是说：

- API Key 只是调用权限
- 多轮上下文靠你每次请求传入的 `messages`

这对当前项目非常重要：

- A 和 AI 的聊天上下文不能寄希望于模型服务端“自动记忆”
- 你们必须自己维护私聊会话状态
- 现在已经有的 Redis `analysis session` 设计方向是对的

### 3.2 当前项目应该怎么组织上下文

对 LoveMediator 的推荐方式：

1. `analysis_session_service` 按 `sessionId` 读取 Redis 会话
2. 取出最近若干轮 `user/assistant` 消息
3. 拼接 `system + history + current user message`
4. 调用 Kimi
5. 把新的 assistant 回复写回 Redis

推荐的消息结构：

```python
messages = [
    {"role": "system", "content": "...私聊分析规则..."},
    *history_messages,
    {"role": "user", "content": clean_message},
]
```

当前私聊场景建议：

- Redis 仍作为会话真相源
- Kimi 只作为推理/生成器，不当状态存储
- 每个 `sessionId` 对应一个用户的一段私聊上下文

### 3.3 对当前后端的建议

`analysis_session_service.send_analysis_message` 现在是先拼 prompt 再调 mock。接真 AI 时更建议改成直接构造 `messages` 列表，而不是把所有历史先压成一段长字符串 prompt。

原因：

- 更符合 Kimi / OpenAI 接口习惯
- 多轮会话更自然
- 后续更容易扩展结构化输出、stream、工具调用

## 4. thinking 模型要点

## 4.1 `reasoning_content` 是什么

官方 `Kimi 长思考模型 API 正式发布` 说明：

- thinking 模型会在响应里提供 `reasoning_content`
- 它和正常 `content` 是并列信息
- 在 OpenAI SDK 中，不能直接当成标准字段访问，需要通过 `hasattr/getattr` 读取

这意味着：

- 如果你们后续接的是 thinking 模型，后端要明确区分“思考过程”和“最终回复”
- 默认不应该把 `reasoning_content` 直接展示给最终用户，除非产品明确需要

### 4.2 多轮时不要把 `reasoning_content` 回灌进上下文

官方文章对这一点说得很明确：

- 多轮会话时，不需要把 `reasoning_content` 放回上下文
- 正确做法是只把正常的 assistant message 放回 `messages`

对当前项目的建议：

- Redis 里只保存用户消息和最终 assistant 回复
- 不把 `reasoning_content` 存进私聊上下文主链路
- 如果后续想做调试，可以单独放到审计日志，不进入正式上下文

### 4.3 thinking 模型的已知限制

官方文章列出的 `kimi-thinking-preview` 限制包括：

- 不支持 ToolCalls
- 不支持联网搜索
- 不支持 JSON Mode
- 不支持 Partial 模式
- 不支持 Context Caching

对当前私聊接入的含义：

- 如果你想尽快落地“私聊 + 确认事实卡片”，不要优先选 thinking 预览模型
- 因为你后续大概率需要更稳定的结构化输出，而官方明确说该预览模型不支持 JSON Mode

结论：

- 私聊主链路优先选择普通聊天模型
- thinking 模型更适合后续做复杂推理实验，不适合作为当前主流程默认模型

### 4.4 官方给出的实践建议

官方给 `kimi-thinking-preview` 的建议包括：

- 优先使用流式输出
- 建议 `temperature=0.8`
- 建议 `max_tokens>=4096`

对当前项目的建议：

- 这一版私聊后端可以先不做 stream
- 如果后续切到 thinking，再补流式输出

## 5. Context Caching 适不适合当前私聊

### 5.1 官方能力是什么

官方 `Context Caching 正式公测` 和后续实践文章给出的要点是：

- 适合“频繁请求、重复引用大量初始上下文”的场景
- 官方给出的典型收益是降低费用和降低首 token 延迟
- Cache 创建接口是 `/v1/caching`
- 使用时可以通过 `role="cache"` 引用已经创建的 cache
- 官方实践文章也展示了基于业务 key 管理 cache id 的做法

### 5.2 对当前私聊场景的判断

LoveMediator 当前私聊场景里，每次变化最大的内容其实是：

- 用户最新发言
- 当前会话最近几轮消息
- 当前整理出的事实摘要

这些内容是高频变化的，因此：

- **不要把整段私聊会话本身当成 Context Caching 的第一落点**
- 这样收益不稳定，维护成本反而更高

更适合缓存的部分是：

- 固定 system prompt
- 很长且稳定的规则说明
- 很少变化的工具描述

### 5.3 当前项目的建议

这一版建议：

- 先不把 Context Caching 作为私聊主链路必需项
- 等真 AI 接通且上下文稳定后，再评估是否只缓存稳定前缀
- 如果后续启用缓存，建议通过“业务唯一 key -> cache id”的方式管理，而不是把 cache id 散落在业务代码里

## 6. 工具调用相关

官方 `Kimi Playground 一站式体验 Kimi K2 的工具调用能力` 说明了：

- Kimi 具备工具调用能力
- Playground 已经支持内置官方工具和第三方 MCP server 工具

但对你们当前私聊主流程，我的建议是：

- **先不要把工具调用放进私聊主链路**

原因：

- 你们当前最重要的是“让 AI 能稳定多轮聊天，并在合适时机给出确认事实卡片”
- 工具调用会增加模型选择、schema、错误处理、权限边界和测试复杂度

更适合后续再接工具调用的场景：

- 从后端受控工具里读取某些固定业务数据
- 为复盘阶段生成更复杂的结构化建议
- 调用内部检索能力，而不是直接暴露数据库

## 7. 对当前后端的落地建议

### 7.1 `ai_service.py`

建议把 `call_llm` 改造成统一 AI 出口，至少返回：

- `model_name`
- `input_tokens`
- `output_tokens`
- `content`
- 可选：`reasoning_content`

同时：

- 统一处理 Kimi SDK 异常
- 不把底层原始错误和 Key 信息直接透给前端
- 统一在这里做 provider 配置读取

### 7.2 `analysis_session_service.py`

当前 `send_analysis_message` 里是把历史压成一段字符串 prompt。建议改成：

- 直接组装 `messages`
- 从 Redis 取最近轮次
- 追加 system message
- 调用 `ai_service.call_llm`
- 把 assistant 回复写回 Redis

再进一步，为了支持“让用户确认事实并做选择”，私聊消息响应建议扩成：

```json
{
  "reply": "我先帮你整理一下，你看这版事实描述是否基本准确？",
  "interaction": {
    "mode": "confirm_fact",
    "summary": "昨天因为家务分工发生争执，你感觉自己的付出没有被看见。",
    "choices": [
      {"id": "confirm", "label": "对，基本是这样"},
      {"id": "continue", "label": "还不准确，继续聊"},
      {"id": "restart", "label": "重新整理"}
    ]
  }
}
```

其中：

- 是否进入 `confirm_fact` 由后端决定
- 前端只负责渲染卡片和按钮
- 这更适合你们之前已经确定的“结构化驱动”方案

### 7.3 模型选择建议

如果是当前“私聊 + 确认事实卡片”目标，建议优先顺序是：

1. 普通聊天模型作为主链路默认模型
2. thinking 模型只做实验性能力或后续增强

核心原因：

- 当前主链路更看重稳定多轮、结构化输出、业务控制
- 而官方对 thinking 预览模型明确列出了 JSON Mode 和工具调用限制

## 8. 当前接入时的工程检查清单

- `.env` 中配置新的 Kimi API Key，不复用已泄露的旧 key
- `Settings` 增加 Kimi 相关配置项
- `pyproject.toml` 增加 `openai>=1.0`
- `ai_service.py` 替换 mock 调用
- `analysis_session_service.py` 从“拼字符串 prompt”改为“组装 messages”
- Redis 仍负责上下文，不把上下文交给模型服务端
- `ai_call_logs` 记录模型名和 tokens，不记录密钥
- 如果后续启用 thinking：
  - 不把 `reasoning_content` 回灌进上下文
  - 默认不直接回显给用户

## 9. 结论

对当前 LoveMediator 后端来说，最稳的路线是：

- 用 Kimi 的 OpenAI 兼容接口接入真实模型
- API Key 只放后端
- Redis 继续维护私聊上下文
- 多轮靠 `messages`，不是靠 API Key
- 私聊主链路先不用 Context Caching 和工具调用
- 优先把“稳定多轮 + 结构化确认事实卡片”做好

## 10. 官方来源索引

以下链接均为 Moonshot / Kimi 官方站点：

1. Kimi API 还没用起来？请看这篇无门槛快速入门指南  
   https://platform.moonshot.cn/blog/posts/kimi-api-quick-start-guide

2. Kimi 长思考模型 API 正式发布  
   https://platform.moonshot.cn/blog/posts/kimi-thinking

3. Context Caching 正式公测  
   https://platform.moonshot.cn/blog/posts/context-caching

4. Kimi API 助手的氮气加速装置 —— 以 Golang 为例实践 Context Caching  
   https://platform.moonshot.cn/blog/posts/enhance-kimi-api-bot-with-context-caching

5. Kimi Playground 一站式体验 Kimi K2 的工具调用能力  
   https://platform.moonshot.cn/blog/posts/kimi-playground
