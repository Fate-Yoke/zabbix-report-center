# Zabbix Report Center

企业级 Zabbix 监控报表中心，支持自动化数据采集、报表生成和邮件推送。

## 功能

- 多 Zabbix 实例管理
- API Token 和用户名密码两种认证方式
- 定时采集监控数据并生成 Excel 报表
- 自动发送报表到指定邮箱
- 基于 Cron 表达式的任务调度
- 监控信息实时查询
- 用户权限管理
- 操作日志审计
- 敏感信息加密存储

## 界面预览

### 管理员界面

![管理员界面](doc/images/admin-dashboard.png)

管理员可访问所有功能模块，包括系统管理、用户管理等。

### 普通用户界面

![普通用户界面](doc/images/user-dashboard.png)

普通用户仅可访问监控信息、定时任务和告警信息等业务功能。

## 技术栈

### 后端
- FastAPI + Uvicorn
- MySQL / SQLite / PostgreSQL
- APScheduler
- Pandas + OpenPyXL

### 前端
- Vue 3 + Composition API
- TypeScript
- Element Plus UI 框架
- Pinia 状态管理
- Vue Router 路由
- Axios HTTP 请求
- Vite 构建工具

## 快速开始

### 本地部署

环境要求：Python 3.8+、Node.js 20.19+

**后端：**

```bash
# 1. 克隆项目
git clone https://github.com/Fate-Yoke/zabbix-report-center.git
cd zabbix-report-center

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 生成随机密钥（Linux/Mac）
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env

# 或 Windows PowerShell
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" | Out-File -Append .env -Encoding utf8
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" | Out-File -Append .env -Encoding utf8

# 4. 启动后端服务
python run.py
```

**前端：**

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

后端访问 http://localhost:38204，前端开发服务器访问 http://localhost:37201

### 生产部署

```bash
# 构建前端
cd frontend
npm run build

# 前端构建产物在 frontend/dist 目录
# 可使用 Nginx 托管，或由后端服务托管
```

### Docker 部署

环境要求：Docker + Docker Compose

**方式一：使用 Docker Hub 镜像（推荐）**

```bash
# 1. 创建配置文件目录
mkdir zabbix-report-center && cd zabbix-report-center

# 2. 下载配置文件模板
curl -O https://raw.githubusercontent.com/Fate-Yoke/zabbix-report-center/main/docker-compose.yml.example
curl -O https://raw.githubusercontent.com/Fate-Yoke/zabbix-report-center/main/.env.example

# 3. 重命名配置文件
mv docker-compose.yml.example docker-compose.yml
mv .env.example .env

# 4. 编辑 docker-compose.yml，将 build: . 改为：
# image: yoke68/zabbix-report-center:latest
# 并根据需要修改端口映射和密码

# 5. 启动服务
docker-compose up -d
```

**方式二：本地构建镜像**

```bash
# 1. 克隆项目
git clone https://github.com/Fate-Yoke/zabbix-report-center.git
cd zabbix-report-center

# 2. 复制并修改配置文件
cp docker-compose.yml.example docker-compose.yml
cp .env.example .env
# 根据实际情况编辑配置文件

# 3. 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

访问 http://localhost:37201，首次注册的用户自动成为管理员。

## 配置

### 环境变量

在 `.env` 文件中配置：

```env
# JWT 密钥
SECRET_KEY=your-random-secret-key

# 加密密钥（用于 Zabbix 密码、邮件密码等敏感信息加密）
ENCRYPTION_KEY=your-random-encryption-key

# 数据库（可选，默认 SQLite）
# DATABASE_URL=mysql+pymysql://user:password@localhost/zabbix_report_center

# 调试模式
DEBUG=false
```

生成密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Zabbix 配置

在「系统管理 > Zabbix 配置」中添加 Zabbix 服务器，支持 API Token（Zabbix 5.4+）或用户名密码认证。

### 邮件配置

在「系统管理 > 邮件配置」中设置 SMTP 服务器信息。

## 使用

### 创建定时任务

1. 进入「定时任务」页面
2. 点击「添加任务」
3. 填写任务信息并保存

Cron 表达式示例：
```
0 9 * * *      # 每天 9:00
0 */6 * * *    # 每 6 小时
0 9 * * 1      # 每周一 9:00
0 9 1 * *      # 每月 1 号 9:00
```

### 监控信息查询

在「监控信息」页面可以查询主机、监控项、触发器信息，并导出 Excel。

## 项目结构

```
zabbix-report-center/
├── app/                # 后端应用代码
│   ├── api/           # API 路由
│   ├── models/        # 数据模型
│   ├── schemas/       # Pydantic 模型
│   ├── services/      # 业务逻辑
│   └── utils/         # 工具函数
├── frontend/           # Vue 3 前端项目
│   ├── src/
│   │   ├── api/       # API 接口封装
│   │   ├── components/# 公共组件
│   │   ├── composables/# 组合式函数
│   │   ├── router/    # 路由配置
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── types/     # TypeScript 类型
│   │   ├── utils/     # 工具函数
│   │   └── views/     # 页面组件
│   └── dist/          # 构建产物
├── doc/                # 文档
│   └── images/        # 截图
├── exports/            # 导出文件
├── .env.example        # 环境变量模板
├── Dockerfile          # Docker 镜像配置
├── docker-compose.yml.example  # Docker Compose 配置模板
├── requirements.txt    # Python 依赖
└── run.py             # 启动脚本
```

## 数据库支持

| 数据库 | 说明 |
|--------|------|
| SQLite | 默认，无需配置 |
| MySQL | 推荐生产环境使用 |
| PostgreSQL | 高并发场景推荐 |

切换数据库只需修改 `DATABASE_URL` 环境变量，表结构自动创建。

## 安全

- 用户密码使用 Bcrypt 加密
- Zabbix/邮件密码使用 Fernet 对称加密
- JWT Token 认证，有效期 24 小时
- 敏感配置通过环境变量管理

详见 [doc/SECURITY.md](doc/SECURITY.md)

## 文档

- [API 文档](doc/API.md)
- [部署指南](doc/DEPLOYMENT.md)
- [开发指南](doc/DEVELOPMENT.md)
- [安全说明](doc/SECURITY.md)

## 常见问题

**无法连接 Zabbix**
- 检查 URL 和网络连通性
- 验证认证信息

**邮件发送失败**
- 检查 SMTP 配置
- 确认是否需要 SSL

**定时任务未执行**
- 确认任务已启用
- 检查 Cron 表达式

**SQLite 数据库锁定**
- 避免并发任务
- 或迁移到 MySQL/PostgreSQL

## 许可证

MIT License
