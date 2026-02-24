# LoveMediator 前端技术文档（FE v1.0）

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| **对应功能文档** | `docs/FD_LoveMediator_v1.md` |
| **对应接口文档** | `docs/API_LoveMediator_v1.md` |
| **对应数据库文档** | `docs/DB_LoveMediator_v1.md` |
| **对应架构文档** | `docs/LoveMediator_ARCH.md` |
| **UI 原型** | `demo.html`（单文件样板，仅供视觉参考） |
| **技术栈** | TypeScript + React 18 + Vite + Tailwind CSS 3 |
| **目标平台** | Mobile-first H5 / PWA |
| **文档版本** | v1.0 |

---

## 2. 技术选型与依赖

### 2.1 核心依赖

| 分类 | 库 | 用途 |
|------|----|------|
| 框架 | React 18 | UI 渲染 |
| 构建 | Vite 5 | 开发服务器 & 生产构建 |
| 语言 | TypeScript 5 (strict) | 类型安全 |
| 样式 | Tailwind CSS 3 | 原子化 CSS |
| 路由 | React Router 7 | SPA 路由 |
| 状态 | Zustand | 轻量全局状态管理 |
| 请求 | Axios + TanStack Query (React Query) | HTTP 请求 & 服务端状态缓存 |
| 图标 | Lucide React | 图标库（与 demo.html 一致） |
| 动画 | Framer Motion | 页面/组件动画 |
| 表单 | React Hook Form + Zod | 表单管理 & 校验 |

### 2.2 开发依赖

| 库 | 用途 |
|----|------|
| ESLint + Prettier | 代码规范 |
| openapi-typescript-codegen | 后端 OpenAPI → TS 类型 & API Client 生成 |
| vite-plugin-pwa | PWA 支持（Service Worker、离线缓存、添加到主屏） |
| tailwind-merge + clsx | 样式条件合并工具 |

### 2.3 与架构文档的差异说明

架构文档 (`LoveMediator_ARCH.md`) 中前端选型为 Next.js + Shadcn UI。实际开发采用 **React + Vite** 方案，原因：

- MVP 阶段无 SSR/SEO 强需求，SPA 开发效率更高。
- Vite 冷启动与 HMR 极快，适合快速迭代。
- 微信分享 OG 信息可由后端 API 或独立预渲染服务提供，不依赖 Next.js SSR。
- 后续如需 SSR 可平滑迁移至 Vite SSR 或 Next.js，组件与业务逻辑可复用。

---

## 3. 工程目录结构

```
/frontend
├── public/
│   ├── favicon.ico
│   ├── manifest.json              # PWA manifest
│   └── icons/                     # PWA 图标
├── src/
│   ├── main.tsx                   # 应用入口
│   ├── App.tsx                    # 根组件，路由挂载
│   ├── vite-env.d.ts
│   │
│   ├── api/                       # API 层
│   │   ├── client.ts              # Axios 实例（baseURL、拦截器、token 注入）
│   │   ├── auth.ts                # AUTH 模块请求函数
│   │   ├── events.ts              # 事件/调解模块请求函数
│   │   ├── calendar.ts            # 日历模块请求函数
│   │   └── elf.ts                 # 互动模块请求函数（V1.5+）
│   │
│   ├── types/                     # 全局类型定义
│   │   ├── api.ts                 # 统一响应结构、错误码
│   │   ├── auth.ts                # 用户、Token 相关类型
│   │   ├── event.ts               # Event、Snapshot、JudgeResult 类型
│   │   ├── calendar.ts            # 日历、Review 类型
│   │   └── enums.ts               # 前端枚举（与后端对齐）
│   │
│   ├── stores/                    # Zustand 状态管理
│   │   ├── useAuthStore.ts        # 用户认证状态
│   │   ├── useEventStore.ts       # 当前事件/调解流程状态
│   │   └── useUIStore.ts          # UI 状态（底部导航、弹窗、Sheet）
│   │
│   ├── hooks/                     # 自定义 Hooks
│   │   ├── useAuth.ts             # 登录/登出/token 刷新逻辑
│   │   ├── useEvent.ts            # 事件 CRUD 与状态流转
│   │   ├── useChat.ts             # 聊天消息发送/接收（私有分析 & 复盘）
│   │   ├── useCalendar.ts         # 日历数据查询
│   │   └── useMediaUpload.ts      # 图片压缩 & 上传
│   │
│   ├── pages/                     # 页面组件（路由级）
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── home/
│   │   │   └── HomePage.tsx       # 主页（宠物互动 + 传话入口）
│   │   ├── mediation/
│   │   │   └── MediationPage.tsx  # AI 调解室（聊天 + 分析流程）
│   │   ├── calendar/
│   │   │   └── CalendarPage.tsx   # 吵架日历
│   │   └── profile/
│   │       └── ProfilePage.tsx    # 个人中心
│   │
│   ├── components/                # 组件
│   │   ├── ui/                    # 基础 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Textarea.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── BottomSheet.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Loading.tsx
│   │   │
│   │   ├── layout/                # 布局组件
│   │   │   ├── AppShell.tsx       # 移动端壳子（含底部导航）
│   │   │   ├── BottomNav.tsx      # 底部导航栏
│   │   │   └── PageHeader.tsx     # 页面头部
│   │   │
│   │   └── business/              # 业务组件
│   │       ├── chat/
│   │       │   ├── ChatBubble.tsx        # 消息气泡（AI/用户）
│   │       │   ├── ChatInput.tsx         # 聊天输入框
│   │       │   └── ChatContainer.tsx     # 聊天消息列表容器
│   │       ├── mediation/
│   │       │   ├── AnalysisInputPanel.tsx    # 事件记录面板（文字+截图上传）
│   │       │   ├── TempAnalysisChat.tsx      # 临时分析对话
│   │       │   ├── GenerateReviewModal.tsx   # "生成复盘"确认弹窗
│   │       │   └── ReviewReport.tsx          # 复盘报告全页
│   │       ├── home/
│   │       │   ├── PetArea.tsx          # 宠物展示区
│   │       │   ├── PetBubble.tsx        # 宠物对话气泡
│   │       │   └── RelayOverlay.tsx     # 传话浮层
│   │       ├── calendar/
│   │       │   ├── MonthView.tsx        # 月历网格
│   │       │   ├── DayCell.tsx          # 单日格子
│   │       │   ├── MoodPicker.tsx       # 今日心情选择
│   │       │   └── HistoryList.tsx      # 记录板列表
│   │       └── profile/
│   │           ├── UserCard.tsx         # 用户头像卡片
│   │           ├── StatsCard.tsx        # 统计数据卡片
│   │           └── MenuSection.tsx      # 设置菜单组
│   │
│   ├── lib/                       # 工具函数
│   │   ├── cn.ts                  # className 合并工具 (clsx + twMerge)
│   │   ├── storage.ts             # localStorage/sessionStorage 封装
│   │   ├── imageCompress.ts       # 前端图片压缩（上传前）
│   │   ├── date.ts                # 日期格式化工具
│   │   └── constants.ts           # 常量定义
│   │
│   └── styles/
│       └── index.css              # Tailwind 入口 + 全局样式
│
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── postcss.config.js
├── eslint.config.js
└── package.json
```

---

## 4. 设计系统 (Design Tokens)

基于 `demo.html` 中的 Tailwind Config 提取统一设计规范。

### 4.1 色彩体系

```typescript
// tailwind.config.ts → theme.extend.colors
const colors = {
  milk: {
    50:  '#FFFEF9',   // 主背景色
    100: '#FFF9E1',   // 奶油色
    200: '#FFEBB6',   // 浅黄
    300: '#FFD988',   // 暖黄
    400: '#FFC85C',
    500: '#FFB302',
  },
  coffee: {
    50:  '#FBF7F4',
    100: '#F2E8DF',   // 拿铁
    200: '#D7CCC8',
    800: '#5D4037',   // 深棕文字
    900: '#3E2723',   // 最深棕
  },
  accent: {
    pink:  '#FFAB91', // 强调粉（按钮、标签）
    green: '#A5D6A7', // 强调绿
    blue:  '#90CAF9', // 强调蓝
  },
};
```

### 4.2 字体

| Token | 字体 | CSS 变量 | 用途 |
|-------|------|----------|------|
| `font-sans` | Nunito, sans-serif | 默认正文 | 全局文字 |
| `font-hand` | Zhi Mang Xing, cursive | 手写风格 | 复盘标题、日历装饰 |

字体通过 Google Fonts 引入，在 `index.html` 中 preconnect + link。

### 4.3 阴影

```typescript
boxShadow: {
  soft:          '0 10px 40px -10px rgba(93, 64, 55, 0.08)',
  float:         '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
  'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.3)',
},
```

### 4.4 动画

| 名称 | 描述 | 用途 |
|------|------|------|
| `bounce-slow` | 3s 慢弹跳 | 宠物名称标签 |
| `float` | 4s 上下浮动 | 宠物图片 |
| `slide-up` | 0.4s 上滑（贝塞尔曲线） | BottomSheet、Modal 入场 |
| `wiggle` | 1s 左右摇摆 | 提示气泡 |

动画在 Tailwind 的 `theme.extend.animation` + `keyframes` 中定义，同时配合 Framer Motion 用于路由切换与条件渲染动画。

### 4.5 全局样式

```css
/* src/styles/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-200 font-sans text-coffee-800;
  }
}

@layer utilities {
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  .glass-nav {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-top: 1px solid rgba(255, 255, 255, 0.6);
  }
}
```

---

## 5. 路由设计

采用 React Router 7，所有主页面在 `AppShell` 内呈现底部导航栏。

### 5.1 路由表

| 路径 | 页面组件 | 是否需要登录 | 底部导航 | 说明 |
|------|----------|-------------|---------|------|
| `/login` | `LoginPage` | 否 | 隐藏 | 登录页 |
| `/register` | `RegisterPage` | 否 | 隐藏 | 注册页 |
| `/` | `HomePage` | 是 | 显示 | 主页（宠物 + 传话） |
| `/mediation` | `MediationPage` | 是 | 显示 | AI 调解室 |
| `/mediation/:eventId/analysis` | `MediationPage`（内部子视图） | 是 | 隐藏 | 事件分析流程 |
| `/calendar` | `CalendarPage` | 是 | 显示 | 吵架日历 |
| `/calendar/:date` | `CalendarPage`（Sheet 展开） | 是 | 显示 | 指定日期详情 |
| `/profile` | `ProfilePage` | 是 | 显示 | 个人中心 |
| `/review/:reviewId` | `ReviewReport`（全屏） | 是 | 隐藏 | 复盘报告详情 |

### 5.2 路由守卫

```typescript
// 伪代码：ProtectedRoute 组件
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) return <Loading />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

### 5.3 路由结构

```tsx
<Routes>
  {/* 公开路由 */}
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />

  {/* 受保护路由 - 带底部导航 */}
  <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
    <Route path="/" element={<HomePage />} />
    <Route path="/mediation" element={<MediationPage />} />
    <Route path="/calendar" element={<CalendarPage />} />
    <Route path="/profile" element={<ProfilePage />} />
  </Route>

  {/* 受保护路由 - 全屏（无底部导航） */}
  <Route element={<ProtectedRoute><Outlet /></ProtectedRoute>}>
    <Route path="/review/:reviewId" element={<ReviewReport />} />
  </Route>
</Routes>
```

---

## 6. 页面与组件拆解

### 6.1 HomePage（主页）

对应 `demo.html` 中 `page-home`。

```
HomePage
├── Header
│   ├── AvatarPair（双头像 + 关系名称）
│   └── NotificationBell（通知铃铛 + 红点）
├── RoomBackground（条纹墙 + 网格地板装饰）
├── PetArea
│   ├── PetNameBadge（可编辑宠物名，弹跳动画）
│   ├── PetImage（宠物图片，浮动动画，点击触发传话）
│   └── PetBubble（提示气泡："点我传话!"）
└── RelayOverlay（传话浮层，点击宠物时滑出）
    ├── Textarea（"告诉糯米团子你想说什么..."）
    └── SendButton
```

**交互逻辑**：
1. 点击宠物图片 → 展开 `RelayOverlay`（从底部滑入，背景模糊遮罩）。
2. 输入消息后点击发送 → 调用 `POST /api/v1/elf/relay`（V1.5+，MVP 可先做本地 Mock）。
3. 发送成功后隐藏浮层，宠物气泡显示润色后的消息。

### 6.2 MediationPage（AI 调解室）

对应 `demo.html` 中 `page-mediation` 及其全部子视图。此页面包含多层嵌套视图，通过组件内部状态控制展示层级。

```
MediationPage
├── PageHeader（"AI 调解室" + Bot 图标）
├── ChatContainer（聊天消息列表，可滚动）
│   └── ChatBubble[]（AI 消息 / 用户消息）
├── BottomArea
│   ├── AnalysisModeButton（"进入争吵事件分析模式"，脉冲红点）
│   └── ChatInput（输入框 + 麦克风 + 发送）
│
├── [Overlay] AnalysisInputPanel（全屏覆盖）
│   ├── BackButton + 标题 "📝 记录事件"
│   ├── ImageUploadZone（虚线框，拖拽/点击上传截图）
│   ├── Textarea（事件描述）
│   └── SubmitButton（"✨ 开始 AI 分析"）
│
├── [Overlay] TempAnalysisChat（全屏覆盖）
│   ├── AnalysisHeader（红色脉冲 "分析中..." + 结束按钮）
│   ├── ChatContainer（分析对话）
│   └── DisabledInput（"正在生成建议..."）
│
├── [Modal] GenerateReviewModal（居中弹窗）
│   ├── 图标 + 标题 "分析完成"
│   ├── 描述文案
│   └── ActionButtons（"不了，谢谢" / "生成复盘"）
│
└── [FullPage] ReviewReport（全屏复盘页）
    ├── Header（关闭按钮 + "复盘小本本" 手写字体）
    ├── PaperCard（纸质卡片风格）
    │   ├── Section "事情经过"
    │   ├── Section "双方观点"（Me / Partner 双栏）
    │   └── Section "改进建议"
    └── BottomActions（"不保存" / "保存到吵架日记"）
```

**调解流程状态机**（前端内部）：

```
idle → analysisInput → tempChat → reviewPrompt → reviewReport
  ↑         ↓               ↓            ↓              ↓
  └─────────┴───────────────┴────────────┴──────────────┘
                        (任意阶段可返回 idle)
```

| 前端状态 | 展示 | 触发条件 |
|----------|------|----------|
| `idle` | 基础聊天界面 | 默认 / 点击返回 |
| `analysisInput` | 全屏事件输入面板 | 点击"进入争吵事件分析模式" |
| `tempChat` | 临时分析对话 | 提交事件描述后 |
| `reviewPrompt` | "生成复盘"弹窗 | AI 分析完成 / 点击"结束分析" |
| `reviewReport` | 全屏复盘报告 | 点击"生成复盘" |

**关键 API 调用映射**：

| 前端动作 | API 调用 | 说明 |
|----------|----------|------|
| 进入分析，发送事件描述 | `POST /events` → `POST /events/{id}/private-chat/messages` | 创建事件 + 私有分析 |
| 在临时分析对话中交互 | `POST /events/{id}/private-chat/messages` | 继续私有分析 |
| 确认事实 | `POST /events/{id}/commit-a` | 冻结 Snapshot_A，状态 → waiting_B |
| 生成复盘 | `GET /events/{id}/judge-result` | 获取裁判结果 |
| 保存到日历 | 内部状态跳转到日历页 | 对应 `reviewed` 状态流转 |
| 基础聊天（非分析） | `POST /events/{id}/followup-chat/messages` | 复盘对话 |

### 6.3 CalendarPage（吵架日历）

对应 `demo.html` 中 `page-calendar`。

```
CalendarPage
├── CalendarHeader（月份 + 年份）
├── WeekHeader（日/一/二/.../六）
├── MonthView（日历网格）
│   └── DayCell[]
│       ├── 日期数字
│       └── 事件标记（红点=争吵 / 蓝点=开心 / 高亮=今天）
│
└── HistorySheet（底部可拖拽面板，默认 45% 高度）
    ├── DragHandle（拖拽条）
    ├── MoodPicker（今日心情：😆😭😡😐）
    └── HistoryList
        ├── FilterButton（筛选按钮）
        └── HistoryItem[]
            ├── DateBadge（日期方块）
            ├── Title（事件标题）
            ├── StatusBadge（争吵/开心 + 已复盘）
            └── → 点击跳转 /review/:reviewId
```

**交互逻辑**：
1. 页面加载 → `GET /api/v1/calendar?month=YYYY-MM` 获取月度事件数据。
2. 日历格子上标记有事件的日期（红/蓝圆点）。
3. 底部面板支持手势拖拽展开（45% → 85%），可通过 Framer Motion 的 drag 手势实现。
4. 点击心情 → 记录今日心情（MVP 可存本地，后续接 API）。
5. 点击历史条目 → `GET /api/v1/calendar/days/{date}/reviews` → 跳转复盘详情。

### 6.4 ProfilePage（个人中心）

对应 `demo.html` 中 `page-profile`。

```
ProfilePage
├── UserCard（头像 + 昵称 + 绑定状态 + 设置入口）
├── StatsCard（恋爱天数 / 解决事件 / 开心时刻）
├── MenuSection "常用功能"
│   ├── MenuItem "恋爱相册"
│   └── MenuItem "纪念日"
└── MenuSection "设置"
    ├── MenuItem "主题风格"
    ├── MenuItem "通知提醒"
    └── MenuItem "解除关系"（红色警示）
```

### 6.5 Auth Pages（登录/注册）

`demo.html` 中未体现，需自行设计，风格保持一致。

```
LoginPage / RegisterPage
├── Logo + App 名称
├── Form
│   ├── UsernameInput
│   ├── PasswordInput
│   └── [Register] ConfirmPasswordInput
├── SubmitButton
└── SwitchLink（"没有账号？去注册" / "已有账号？去登录"）
```

**校验规则**（与 `FD_LoveMediator_v1.md` §4.2 对齐）：

| 字段 | 校验 |
|------|------|
| username | 必填，3~32 字符，字母数字下划线 |
| password | 必填，8~64 字符，至少包含字母和数字 |
| confirmPassword | 必填，与 password 一致 |

---

## 7. 状态管理

### 7.1 Zustand Store 设计

#### useAuthStore

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
  clear: () => void;
}
```

Token 存储策略：
- `accessToken` → 内存（Zustand store）+ `localStorage`（持久化，刷新页面恢复）。
- `refreshToken` → `localStorage`。
- 应用启动时从 `localStorage` 读取并尝试静默刷新。

#### useEventStore

```typescript
interface EventState {
  currentEventId: string | null;
  mediationPhase: 'idle' | 'analysisInput' | 'tempChat' | 'reviewPrompt' | 'reviewReport';
  chatMessages: ChatMessage[];

  setCurrentEvent: (eventId: string) => void;
  setMediationPhase: (phase: EventState['mediationPhase']) => void;
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
  reset: () => void;
}
```

#### useUIStore

```typescript
interface UIState {
  activeTab: 'home' | 'mediation' | 'calendar' | 'profile';
  isRelayOverlayOpen: boolean;
  isCalendarSheetExpanded: boolean;

  setActiveTab: (tab: UIState['activeTab']) => void;
  toggleRelayOverlay: () => void;
  toggleCalendarSheet: () => void;
}
```

### 7.2 服务端状态（TanStack Query）

所有 API 数据获取通过 TanStack Query 管理缓存与重新请求：

| Query Key | API | staleTime | 说明 |
|-----------|-----|-----------|------|
| `['calendar', month]` | `GET /calendar?month=` | 5min | 月历数据 |
| `['reviews', date]` | `GET /calendar/days/{date}/reviews` | 2min | 日期复盘列表 |
| `['review', reviewId]` | `GET /reviews/{id}` | 5min | 复盘详情 |
| `['judgeResult', eventId]` | `GET /events/{id}/judge-result` | Infinity | 裁判结果（不可变） |
| `['snapshotA', eventId]` | `GET /events/{id}/snapshot-a` | Infinity | A 快照（冻结后不变） |

Mutation 使用 `useMutation` 封装，成功后通过 `queryClient.invalidateQueries` 刷新关联缓存。

---

## 8. API 对接层

### 8.1 Axios 实例配置

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截器：注入 Token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一错误处理 & Token 自动刷新
apiClient.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    if (error.response?.status === 401) {
      // 尝试 refresh，失败则跳登录
    }
    return Promise.reject(error);
  }
);
```

### 8.2 统一响应类型

```typescript
// src/types/api.ts
interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

interface ApiError {
  code: number;
  message: string;
  data: null;
}
```

### 8.3 错误码前端映射

基于 `API_LoveMediator_v1.md` §2.4：

| code | 前端处理 |
|------|----------|
| `1001` | 表单校验提示（Toast） |
| `1002` | "资源不存在"提示 |
| `1003` | "当前状态不允许此操作"提示 |
| `2001` | 跳转登录页 |
| `2002` | "无权限"提示 |
| `2003` | "账号已锁定"提示 |
| `2004` | "请求过于频繁，请稍后再试" |
| `3001` | "用户名已存在"（注册页字段提示） |
| `3002` | "快照已冻结"提示 |
| `3003` | "前置条件未满足"提示 |
| `5000` | "系统繁忙，请稍后再试" |

### 8.4 Token 刷新机制

```
accessToken 过期 → 401
  → 请求拦截器检测
  → 用 refreshToken 调 POST /auth/refresh
    → 成功：更新 token，重发原请求
    → 失败：清除认证状态，跳转 /login
```

使用请求队列防止并发刷新：当多个请求同时 401 时，只触发一次 refresh，其余请求排队等待 refresh 完成后重发。

---

## 9. 类型定义（与后端对齐）

### 9.1 枚举

```typescript
// src/types/enums.ts
export enum EventStatus {
  Draft = 'draft',
  WaitingB = 'waiting_b',
  Judged = 'judged',
  Reviewed = 'reviewed',
  Closed = 'closed',
}

export enum UserStatus {
  Active = 'active',
  Locked = 'locked',
  Disabled = 'disabled',
}
```

### 9.2 核心业务类型

```typescript
// src/types/auth.ts
export interface User {
  userId: string;
  username: string;
  status: UserStatus;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
}

// src/types/event.ts
export interface Event {
  eventId: string;
  status: EventStatus;
}

export interface Snapshot {
  summary: string;
  pointsA: string[];
  pointsB: string[];
}

export interface SnapshotResponse {
  eventId: string;
  status: EventStatus;
  snapshotA: Snapshot;
}

export interface JudgeResult {
  judgeResultId: string;
  eventId: string;
  status: EventStatus;
  objectiveSummary: string;
  analysis: {
    triggers: string[];
    misunderstandings: string[];
    adviceForA: string[];
    adviceForB: string[];
  };
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  reply: string;
  sessionId?: string;
  contextMeta?: {
    recentMessages: number;
    snapshots: number;
    judgeResults: number;
  };
}

// src/types/calendar.ts
export interface CalendarDay {
  date: string;
  count: number;
}

export interface CalendarMonthResponse {
  month: string;
  days: CalendarDay[];
}

export interface ReviewItem {
  reviewId: string;
  eventId: string;
  title: string;
  updatedAt: string;
}

export interface ReviewDetail {
  reviewId: string;
  eventId: string;
  content: string;
  source: string;
  createdAt: string;
  updatedAt: string;
}
```

### 9.3 OpenAPI 生成

通过 `scripts/generate_client.sh` 从后端 OpenAPI Schema 自动生成类型和 API 客户端，保证前后端类型严格一致：

```bash
#!/bin/bash
npx openapi-typescript-codegen \
  --input http://localhost:8000/openapi.json \
  --output ./src/api/generated \
  --client axios
```

手写类型仅作为 OpenAPI 生成前的过渡方案。生成后以生成代码为准。

---

## 10. 关键交互流程（时序）

### 10.1 登录流程

```
用户 → LoginPage → 输入用户名密码 → 点击登录
  → [前端] React Hook Form + Zod 校验
  → [API] POST /auth/login
  → [成功] 存储 token → 跳转 /
  → [失败] Toast 显示错误消息
```

### 10.2 AI 调解完整流程

```
用户 → MediationPage

1. 点击"进入争吵事件分析模式"
   → phase: idle → analysisInput
   → 全屏 AnalysisInputPanel 滑入

2. 填写事件描述 + 可选上传截图 → 点击"开始 AI 分析"
   → [API] POST /events（创建事件，获取 eventId）
   → [API] POST /events/{id}/private-chat/messages（发送描述内容）
   → phase: analysisInput → tempChat
   → AnalysisInputPanel 关闭，TempAnalysisChat 展示

3. AI 流式回复（或轮询）分析过程

4. 用户点击"结束分析"或 AI 分析完成
   → phase: tempChat → reviewPrompt
   → GenerateReviewModal 弹出

5a. 点击"生成复盘"
   → [API] POST /events/{id}/commit-a（确认事实，冻结 Snapshot_A）
   → [API] GET /events/{id}/judge-result（获取裁判结果）
   → phase: reviewPrompt → reviewReport
   → ReviewReport 全屏展示

5b. 点击"不了，谢谢"
   → phase → idle

6. ReviewReport 中点击"保存到吵架日记"
   → 内部逻辑处理
   → 跳转至 CalendarPage
   → phase → idle
```

### 10.3 B 方参与流程（V1.5+ 影子模式预留）

```
B 收到分享链接 → 打开 /case/{uuid}/preview
  → 后端签发 Shadow Token（Set-Cookie）
  → 展示 A 方快照

B 选择"同意" → POST /events/{id}/b-agree → 生成裁判结果
B 选择"不同意" → 进入 B 方私有分析流程 → POST /events/{id}/commit-b
```

---

## 11. 组件设计规范

### 11.1 基础 UI 组件接口

#### Button

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
}
```

样式映射：
- `primary` → `bg-coffee-800 text-white`
- `secondary` → `bg-white text-coffee-800 border border-gray-200`
- `ghost` → `bg-transparent text-coffee-800 hover:bg-milk-100`
- `danger` → `bg-red-50 text-red-400`

#### Modal

```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}
```

- 背景遮罩：`bg-coffee-900/40 backdrop-blur-sm`
- 内容卡片：`bg-white rounded-[32px] p-6 shadow-2xl animate-slide-up`

#### BottomSheet

```typescript
interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  initialHeight?: string;   // 默认 '45%'
  expandedHeight?: string;  // 默认 '85%'
  children: React.ReactNode;
}
```

- 使用 Framer Motion `drag="y"` + `dragConstraints` 实现手势拖拽。
- 圆角顶部：`rounded-t-[40px]`

#### ChatBubble

```typescript
interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  avatar?: string;
}
```

- AI 消息：左侧头像 + `bg-white rounded-2xl rounded-tl-none`
- 用户消息：右侧头像 + `bg-coffee-100 rounded-2xl rounded-tr-none`

### 11.2 组件编写规范

1. 每个组件一个文件，使用命名导出 `export function ComponentName`。
2. Props 接口定义在同文件顶部，使用 `interface` 而非 `type`。
3. 样式通过 `cn()` 工具函数合并 Tailwind 类名，支持条件样式。
4. 组件不直接调用 API，通过 props 回调或 hooks 间接调用。
5. 业务组件放 `components/business/`，通用 UI 组件放 `components/ui/`。

---

## 12. 前端安全与防御

### 12.1 Token 安全

- `accessToken` / `refreshToken` 存 `localStorage`，不放 Cookie（避免 CSRF）。
- 所有 API 请求通过 Axios 拦截器自动注入 `Authorization: Bearer` 头。
- Token 过期自动刷新，刷新失败清除所有凭证并跳登录。

### 12.2 XSS 防御

- React 默认转义 JSX 输出，不使用 `dangerouslySetInnerHTML`。
- AI 返回的 Markdown 内容如需渲染，使用安全的 Markdown 渲染库并配置白名单标签。

### 12.3 输入校验

- 所有表单使用 Zod Schema 校验，与后端校验规则对齐。
- 聊天输入限制最大字符数（如 2000 字），防止超长输入。

### 12.4 图片上传安全

- 前端压缩：上传前压缩图片（最大边长 1920px、质量 0.8），减少传输体积。
- 文件类型限制：仅允许 `image/jpeg`、`image/png`、`image/webp`。
- 单文件大小限制：5MB（与后端 `MAX_UPLOAD_SIZE_MB` 对齐）。
- 上传频率：前端不做硬限制，由后端 Rate Limiting 兜底。

### 12.5 敏感信息

- 前端日志中禁止输出 token、密码等敏感信息。
- 错误上报时附带 `X-Trace-Id`（从响应头获取），便于排查。

---

## 13. 性能优化策略

### 13.1 代码分割

- 页面级组件使用 `React.lazy` + `Suspense` 按路由分割。
- 重量级组件（如 Framer Motion 的复杂动画组件）按需加载。

```typescript
const CalendarPage = lazy(() => import('./pages/calendar/CalendarPage'));
const ReviewReport = lazy(() => import('./components/business/mediation/ReviewReport'));
```

### 13.2 图片优化

- 头像、宠物图片使用合适尺寸，非原始大图。
- 使用 `loading="lazy"` 延迟加载非首屏图片。
- 上传截图在前端压缩后再传（`lib/imageCompress.ts`）。

### 13.3 列表性能

- 聊天消息列表：消息量大时使用虚拟滚动（如 `@tanstack/react-virtual`）。
- 日历历史列表：数据量可控，无需虚拟化。

### 13.4 缓存策略

- TanStack Query 缓存 API 数据，减少重复请求。
- 裁判结果（不可变）设置 `staleTime: Infinity`。
- PWA Service Worker 缓存静态资源。

---

## 14. PWA 配置

### 14.1 manifest.json

```json
{
  "name": "LoveMediator - 温馨情侣调解",
  "short_name": "LoveMediator",
  "description": "AI 驱动的情侣关系调解工具",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FFFEF9",
  "theme_color": "#5D4037",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 14.2 Vite PWA 插件

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com/,
            handler: 'CacheFirst',
            options: { cacheName: 'google-fonts-stylesheets' },
          },
        ],
      },
    }),
  ],
});
```

---

## 15. 环境变量

```bash
# .env.example (frontend)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=LoveMediator
```

所有前端环境变量以 `VITE_` 前缀，通过 `import.meta.env` 访问。禁止在前端环境变量中放置任何密钥。

---

## 16. 开发规范

### 16.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `ChatBubble.tsx` |
| Hook 文件 | camelCase（use 前缀） | `useAuth.ts` |
| 工具函数 | camelCase | `imageCompress.ts` |
| 类型文件 | camelCase | `event.ts` |
| CSS 类名 | Tailwind 原子类 | `bg-coffee-800 text-white` |
| 常量 | UPPER_SNAKE_CASE | `MAX_CHAT_LENGTH` |
| 枚举值 | PascalCase | `EventStatus.WaitingB` |

### 16.2 Git 提交规范

```
<type>(<scope>): <description>

type: feat / fix / refactor / style / docs / test / chore
scope: auth / mediation / calendar / profile / ui / api
```

### 16.3 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 生产就绪代码 |
| `develop` | 开发集成分支 |
| `feat/<name>` | 功能开发分支 |
| `fix/<name>` | Bug 修复分支 |

---

## 17. 开发阶段计划

### Phase 1：基础架构 + 认证（P0）

- [ ] 项目初始化（Vite + React + TS + Tailwind）
- [ ] 设计系统搭建（颜色、字体、基础 UI 组件）
- [ ] AppShell + BottomNav + 路由配置
- [ ] 登录/注册页面 + API 对接
- [ ] Token 管理 + 路由守卫
- [ ] Axios 实例 + 拦截器

### Phase 2：AI 调解核心流程（P0）

- [ ] MediationPage 基础聊天
- [ ] AnalysisInputPanel（事件输入 + 图片上传）
- [ ] TempAnalysisChat（临时分析对话）
- [ ] GenerateReviewModal
- [ ] ReviewReport（复盘报告页）
- [ ] 调解流程状态机完整串通

### Phase 3：主页 + 日历（P1）

- [ ] HomePage（宠物区域 + 传话浮层）
- [ ] CalendarPage（月历 + 底部面板）
- [ ] MonthView + DayCell + 事件标记
- [ ] HistoryList + MoodPicker
- [ ] ReviewDetail 页面

### Phase 4：个人中心 + 完善（P1）

- [ ] ProfilePage
- [ ] StatsCard 数据展示
- [ ] PWA 配置与测试
- [ ] 全局错误处理优化
- [ ] 性能优化（代码分割、虚拟滚动）

### Phase 5：互动模块（P2，V1.5+）

- [ ] 小精灵传话功能
- [ ] 过激语言检测与柔化提示

---

## 18. FR 与前端页面/组件映射

| FR 编号 | 功能 | 前端页面/组件 |
|---------|------|--------------|
| AUTH-FR-001 | 注册 | `RegisterPage` |
| AUTH-FR-002 | 登录 | `LoginPage` |
| AUTH-FR-003 | 登录限流与锁定 | 后端处理，前端展示错误提示 |
| AUTH-FR-004 | 登出与 token 刷新 | `useAuth` hook + Axios 拦截器 |
| MED-FR-001 | A 私有分析 | `MediationPage` → `TempAnalysisChat` |
| MED-FR-002 | A 确认冻结 Snapshot_A | `GenerateReviewModal` → commit 按钮 |
| MED-FR-003 | B 同意/不同意 | B 方视图（V1.5+ 预留） |
| MED-FR-004 | 生成 JudgeResult | `ReviewReport`（展示裁判结果） |
| MED-FR-005 | 查看结果不触发 LLM | `ReviewReport` 直接读取缓存/API 数据 |
| MED-FR-006 | 复盘对话 | `MediationPage` 基础聊天模式 |
| CAL-FR-001 | 复盘自动入历 | 保存复盘后刷新日历缓存 |
| CAL-FR-002 | 月历展示与详情 | `CalendarPage` → `MonthView` + `HistoryList` |
| CAL-FR-003 | 复盘编辑与共享 | `ReviewReport` 编辑模式（后续） |
| IM-FR-001 | 代转达 | `HomePage` → `RelayOverlay`（V1.5+） |
| IM-FR-002 | 过激语言拦截 | 聊天输入前置中间件（V1.5+） |

---

## 19. 约束与注意事项

1. **前端不驱动状态流转**：所有 Event 状态变更（`draft → waiting_b → judged` 等）由后端状态机控制，前端仅发起请求并根据返回结果更新 UI。
2. **Snapshot 不可变**：前端展示 Snapshot 数据时不提供编辑入口，确保 UI 层面也体现冻结语义。
3. **JudgeResult 不实时调用**：复盘页直接读取已落库的裁判结果（`GET /events/{id}/judge-result`），TanStack Query 设置 `staleTime: Infinity`。
4. **类型一致性**：优先使用 OpenAPI 自动生成的类型（`scripts/generate_client.sh`），手写类型仅作为过渡。
5. **隐私与 PII**：前端不做 PII 脱敏（由后端 Privacy Middleware 处理），但前端日志/错误上报中禁止携带敏感信息。
6. **成本感知**：聊天输入限制最大字符数，图片上传前压缩，与后端的 Token 预算和上传限制对齐。
