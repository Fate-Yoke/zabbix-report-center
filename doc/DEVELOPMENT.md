# 开发指南

## 开发环境

### 环境要求

- Python 3.8+
- Node.js 20.19+
- MySQL / SQLite（可选）

### 后端开发

```bash
# 克隆项目
git clone https://github.com/Fate-Yoke/zabbix-report-center.git
cd zabbix-report-center

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动后端服务
python run.py
```

后端服务运行在 http://localhost:38204

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器运行在 http://localhost:37201，会自动代理 API 请求到后端 38204 端口。

访问 http://localhost:37201 即可使用完整应用。

### Docker 环境

```bash
git clone https://github.com/Fate-Yoke/zabbix-report-center.git
cd zabbix-report-center
cp docker-compose.yml.example docker-compose.yml
cp .env.example .env
# 根据实际情况编辑配置文件
docker-compose up -d
```

修改代码后重新构建：
```bash
docker-compose up -d --build
```

## 项目结构

### 后端结构

```
app/
├── api/           # API 路由
│   ├── auth.py    # 认证相关
│   ├── monitor.py # 监控数据
│   ├── tasks.py   # 定时任务
│   └── ...
├── models/        # 数据模型（ORM）
├── schemas/       # Pydantic 数据验证
├── services/      # 业务逻辑
├── utils/         # 工具函数
├── config.py      # 配置
├── database.py    # 数据库连接
└── main.py        # 应用入口
```

### 前端结构

```
frontend/
├── src/
│   ├── api/           # API 接口封装
│   │   ├── index.ts   # Axios 实例和拦截器
│   │   ├── auth.ts    # 认证 API
│   │   ├── monitor.ts # 监控 API
│   │   └── ...
│   ├── components/    # 公共组件
│   │   └── layout/    # 布局组件
│   ├── composables/   # 组合式函数
│   ├── router/        # 路由配置
│   │   └── index.ts   # 路由定义和守卫
│   ├── stores/        # Pinia 状态管理
│   │   ├── auth.ts    # 认证状态
│   │   └── zabbixConfig.ts # Zabbix 配置状态
│   ├── types/         # TypeScript 类型定义
│   │   └── index.ts
│   ├── utils/         # 工具函数
│   ├── views/         # 页面组件
│   │   ├── dashboard/ # 首页
│   │   ├── monitor/   # 监控信息
│   │   ├── alerts/    # 告警信息
│   │   ├── tasks/     # 定时任务
│   │   ├── profile/   # 个人信息
│   │   └── admin/     # 管理页面
│   ├── App.vue        # 根组件
│   └── main.ts        # 入口文件
├── public/            # 静态资源
├── index.html         # HTML 模板
├── vite.config.ts     # Vite 配置
├── tsconfig.json      # TypeScript 配置
└── package.json       # 依赖配置
```

## 架构

```
前端（Vue 3 + Element Plus）
        ↓ Axios
API 路由（FastAPI）
        ↓
业务服务（Services）
        ↓
数据模型（SQLAlchemy）
        ↓
数据库（MySQL/SQLite）
```

### 前后端交互

1. 前端通过 Axios 发送 HTTP 请求
2. 后端 FastAPI 处理请求，返回 JSON 数据
3. 认证使用 JWT Token（Bearer Token）
4. 前端 Pinia Store 管理全局状态

## 代码规范

### Python

- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

### TypeScript/Vue

- 使用 Composition API
- 组件使用 `<script setup>` 语法
- 类型定义放在 `src/types/` 目录

## 添加新功能

### 后端

1. 在 `app/models/` 定义数据模型
2. 在 `app/schemas/` 定义 Pydantic 模型
3. 在 `app/services/` 实现业务逻辑
4. 在 `app/api/` 添加路由

### 前端

1. 在 `src/types/` 定义 TypeScript 类型
2. 在 `src/api/` 添加 API 接口
3. 在 `src/views/` 创建页面组件
4. 在 `src/router/` 添加路由

## API 文档

启动后端后访问 http://localhost:38204/docs 查看自动生成的 Swagger 文档。

## 调试

### 后端调试

启用 SQL 日志：
```python
# app/database.py
engine = create_engine(DATABASE_URL, echo=True)
```

使用断点：
```python
breakpoint()
```

### 前端调试

使用浏览器开发者工具（F12），支持 Vue Devtools 扩展。

Vite 配置了代理，API 请求会自动转发到后端：
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:38204'
  }
}
```

## 数据库迁移

项目使用 SQLAlchemy 自动建表。如需迁移支持：

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## 构建部署

### 前端构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录，可由 Nginx 托管或后端服务托管。

### 生产配置

前端需要配置 API 地址，编辑 `frontend/.env.production`：
```
VITE_API_BASE_URL=https://your-domain.com
```

## 相关文档

### 后端
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [APScheduler](https://apscheduler.readthedocs.io/)

### 前端
- [Vue 3](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [Pinia](https://pinia.vuejs.org/)
- [Vue Router](https://router.vuejs.org/)
- [Vite](https://vitejs.dev/)
- [TypeScript](https://www.typescriptlang.org/)
