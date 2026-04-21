# Zabbix Report Center Frontend

基于 Vue 3 + TypeScript + Element Plus 的企业级监控报表前端应用。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架，使用 Composition API
- **TypeScript** - 类型安全的 JavaScript 超集
- **Element Plus** - Vue 3 组件库
- **Pinia** - Vue 3 状态管理
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP 请求库
- **Vite** - 下一代前端构建工具

## 开发

### 环境要求

- Node.js 18+
- npm 9+

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:37201

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist` 目录。

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
src/
├── api/           # API 接口封装
│   ├── index.ts   # Axios 实例和拦截器
│   ├── auth.ts    # 认证相关 API
│   ├── monitor.ts # 监控数据 API
│   ├── tasks.ts   # 定时任务 API
│   └── ...
├── components/    # 公共组件
│   └── layout/    # 布局组件
│       ├── AppLayout.vue    # 主布局
│       ├── AppHeader.vue    # 顶部导航
│       ├── AppSidebar.vue   # 侧边栏
│       └── ZabbixSelector.vue # Zabbix 配置选择器
├── composables/   # 组合式函数
├── router/        # 路由配置
│   └── index.ts   # 路由定义和导航守卫
├── stores/        # Pinia 状态管理
│   ├── auth.ts    # 用户认证状态
│   └── zabbixConfig.ts # Zabbix 配置状态
├── types/         # TypeScript 类型定义
│   └── index.ts
├── utils/         # 工具函数
├── views/         # 页面组件
│   ├── dashboard/ # 首页仪表盘
│   ├── login/     # 登录页
│   ├── register/  # 注册页
│   ├── monitor/   # 监控信息
│   ├── alerts/    # 告警信息
│   ├── tasks/     # 定时任务
│   ├── profile/   # 个人信息
│   └── admin/     # 管理页面
│       ├── Users.vue      # 用户管理
│       ├── ZabbixConfig.vue # Zabbix 配置
│       ├── EmailConfig.vue # 邮件配置
│       ├── System.vue     # 系统设置
│       └── Logs.vue       # 系统日志
├── App.vue        # 根组件
├── main.ts        # 应用入口
└── style.css      # 全局样式
```

## 功能模块

### 认证
- 登录 / 注册
- JWT Token 认证
- 自动刷新 Token
- 登出

### 首页仪表盘
- 设备总量 / 在线 / 离线统计
- 离线设备列表
- 在线设备列表
- 缓存数据自动刷新

### 监控信息
- 筛选配置管理
- 监控数据查询
- 数据导出 Excel

### 告警信息
- 告警列表查看
- 告警数据导出
- 导出历史记录

### 定时任务
- 任务 CRUD
- 任务执行日志
- 任务启用 / 禁用

### 系统管理
- 用户管理
- Zabbix 配置管理
- 邮件配置管理
- 系统设置
- 系统日志

## 配置

### 开发环境

Vite 开发服务器代理配置在 `vite.config.ts`：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:38204',
      changeOrigin: true
    }
  }
}
```

### 生产环境

创建 `.env.production` 文件：

```
VITE_API_BASE_URL=https://your-api-domain.com
```

## 代码规范

- 使用 Composition API 和 `<script setup>` 语法
- TypeScript 类型定义放在 `src/types/` 目录
- API 接口封装放在 `src/api/` 目录
- 组件命名使用 PascalCase
- 文件命名使用 PascalCase（组件）或 camelCase（工具函数）

## 相关文档

- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
