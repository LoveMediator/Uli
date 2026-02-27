# LoveMediator 前端 API 接口层

## 📋 项目概述

基于 LoveMediator 项目文档（API v1.0、FE v1.0）实现的完整前端 API 接口层，包含类型定义、API 客户端、React Hooks 和使用示例。

## ✅ 已完成功能

### 1. 类型定义系统（`src/types/`）

- ✅ **api.ts** - 统一响应结构、错误码枚举
- ✅ **auth.ts** - 用户、Token、注册/登录请求类型
- ✅ **event.ts** - 事件、快照、聊天消息、裁判结果类型
- ✅ **calendar.ts** - 日历、复盘记录类型
- ✅ **elf.ts** - 小精灵传话、过激语言检测类型
- ✅ **enums.ts** - EventStatus、UserStatus、MessageRole 枚举

### 2. API 客户端（`src/api/`）

#### 核心功能
- ✅ **client.ts** - Axios 实例配置
  - 自动 Token 注入（Bearer JWT）
  - Token 过期自动刷新
  - 请求/响应拦截器
  - 统一错误处理

#### API 模块
- ✅ **auth.ts** - 认证模块
  - 注册 `register()`
  - 登录 `login()`
  - 登出 `logout()`
  - 刷新 Token `refreshAccessToken()`
  - 获取当前用户 `getCurrentUser()`

- ✅ **events.ts** - 事件/调解模块
  - 创建事件 `createEvent()`
  - 获取事件列表/详情 `getEvents()` / `getEvent()`
  - 私聊消息 `sendPrivateChat()` / `getPrivateChatHistory()`
  - 提交快照 A/B `commitSnapshotA()` / `commitSnapshotB()`
  - B 方同意/不同意 `submitBAgreement()`
  - 获取裁判结果 `getJudgeResult()`
  - 复盘对话 `sendFollowupChat()` / `getFollowupChatHistory()`
  - 获取快照 `getSnapshotA()` / `getSnapshotB()`

- ✅ **calendar.ts** - 日历模块
  - 获取日历数据 `getCalendar()`
  - 获取指定日期复盘 `getReviewsByDate()`
  - 复盘详情 `getReview()`
  - 更新/删除复盘 `updateReview()` / `deleteReview()`

- ✅ **elf.ts** - 小精灵互动模块
  - 小精灵传话 `relayMessage()`
  - 过激语言检测 `moderateMessage()`

### 3. React Hooks（`src/hooks/`）

- ✅ **useAuth** - 认证状态管理
  - 用户信息、登录状态
  - 登录/注册/登出方法
  - 自动初始化用户状态

- ✅ **useEvents** - 事件管理
  - 事件列表、当前事件
  - 完整的事件生命周期操作
  - 加载状态、错误处理

- ✅ **useCalendar** - 日历管理
  - 日历数据、复盘列表
  - 日期选择、复盘操作
  - 加载状态、错误处理

### 4. 工具函数（`src/utils/`）

- ✅ **errorHandler.ts** - 错误处理工具
  - 错误码到消息映射
  - 认证错误判断
  - 重新登录判断

### 5. 配置文件

- ✅ **.env.example** - 环境变量模板
- ✅ **.env.development** - 开发环境配置
- ✅ **.env.production** - 生产环境配置

### 6. 示例代码（`src/examples/`）

- ✅ **LoginExample.tsx** - 登录示例
- ✅ **EventsExample.tsx** - 事件管理示例
- ✅ **CalendarExample.tsx** - 日历示例

### 7. 文档

- ✅ **src/api/README.md** - 完整的 API 使用文档

## 🚀 快速开始

### 1. 安装依赖

```bash
cd fontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.development
```

修改 `.env.development`：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. 启动开发服务器

```bash
npm run dev
```

## 📖 使用示例

### 使用 Hooks（推荐）

```tsx
import { useAuth, useEvents } from './hooks';

function App() {
  const { user, login, logout } = useAuth();
  const { events, createEvent } = useEvents();

  return (
    <div>
      {user ? (
        <>
          <h1>欢迎, {user.username}</h1>
          <button onClick={logout}>登出</button>
        </>
      ) : (
        <button onClick={() => login('username', 'password')}>
          登录
        </button>
      )}
    </div>
  );
}
```

### 直接调用 API

```tsx
import * as authApi from './api/auth';
import * as eventsApi from './api/events';

// 登录
const response = await authApi.login({
  username: 'alice',
  password: 'Pass123456'
});

// 创建事件
const event = await eventsApi.createEvent({
  title: '今天的争吵',
  initialMessage: '我们因为晚饭吃什么吵起来了'
});
```

## 📁 目录结构

```
fontend/src/
├── api/                    # API 请求层
│   ├── client.ts           # Axios 实例（Token 管理、拦截器）
│   ├── auth.ts             # 认证 API
│   ├── events.ts           # 事件 API
│   ├── calendar.ts         # 日历 API
│   ├── elf.ts              # 小精灵 API
│   ├── index.ts            # 统一导出
│   └── README.md           # 使用文档
├── types/                  # TypeScript 类型
│   ├── api.ts              # 通用响应结构
│   ├── auth.ts             # 认证类型
│   ├── event.ts            # 事件类型
│   ├── calendar.ts         # 日历类型
│   ├── elf.ts              # 小精灵类型
│   ├── enums.ts            # 枚举定义
│   └── index.ts            # 统一导出
├── hooks/                  # React Hooks
│   ├── useAuth.ts          # 认证 Hook
│   ├── useEvents.ts        # 事件 Hook
│   ├── useCalendar.ts      # 日历 Hook
│   └── index.ts            # 统一导出
├── utils/                  # 工具函数
│   ├── errorHandler.ts     # 错误处理
│   └── index.ts            # 统一导出
└── examples/               # 使用示例
    ├── LoginExample.tsx    # 登录示例
    ├── EventsExample.tsx   # 事件示例
    └── CalendarExample.tsx # 日历示例
```

## 🔑 核心特性

### 1. 自动 Token 管理
- 请求自动注入 Bearer Token
- Token 过期自动刷新
- 刷新失败自动跳转登录

### 2. 完整类型支持
- 所有 API 都有 TypeScript 类型定义
- 与后端 API 文档完全对齐
- 编译时类型检查

### 3. 统一错误处理
- 统一的错误码映射
- 友好的错误提示
- 错误分类处理

### 4. React Hooks 集成
- 状态管理自动化
- 加载状态、错误处理
- 简化组件逻辑

## 📝 API 覆盖率

根据 `docs/API_LoveMediator_v1.md` 文档：

- ✅ 认证模块（5/5）
- ✅ 事件模块（12/12）
- ✅ 日历模块（4/4）
- ✅ 小精灵模块（2/2）

**总计：23/23 接口已实现（100%）**

## 🔧 技术栈

- **TypeScript** - 类型安全
- **Axios** - HTTP 客户端
- **React 19** - UI 框架
- **Vite** - 构建工具

## 📚 相关文档

- [API 使用文档](src/api/README.md)
- [API 设计文档](../docs/API_LoveMediator_v1.md)
- [前端技术文档](../docs/FE_LoveMediator_v1.md)
- [架构文档](../docs/LoveMediator_ARCH.md)

## ⚠️ 注意事项

1. **环境变量**：确保正确配置 `VITE_API_BASE_URL`
2. **Token 存储**：Token 存储在 localStorage，注意安全性
3. **错误处理**：所有 API 调用都需要 try-catch
4. **类型一致性**：类型定义与后端 API 文档保持一致
5. **请求超时**：默认 30 秒超时

## 🎯 下一步

建议继续完成：

1. **UI 组件**：基于 API 层实现页面组件
2. **状态管理**：集成 Zustand 或 Redux
3. **路由配置**：React Router 路由设置
4. **样式系统**：Tailwind CSS 配置
5. **测试**：单元测试和集成测试
