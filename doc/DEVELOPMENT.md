# 开发指南

## 开发环境

### Docker 环境

```bash
git clone https://github.com/your-username/zabbix-report-center.git
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

### 本地环境

```bash
git clone https://github.com/your-username/zabbix-report-center.git
cd zabbix-report-center

python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
cp .env.example .env
python run.py
```

## 项目结构

```
app/
├── api/           # API 路由
├── models/        # 数据模型（ORM）
├── schemas/       # Pydantic 数据验证
├── services/      # 业务逻辑
├── templates/     # Jinja2 模板
├── static/        # 静态资源
├── utils/         # 工具函数
├── config.py      # 配置
├── database.py    # 数据库连接
└── main.py        # 应用入口
```

## 架构

```
前端（Bootstrap + jQuery）
        ↓
API 路由（FastAPI）
        ↓
业务服务（Services）
        ↓
数据模型（SQLAlchemy）
        ↓
数据库（MySQL/SQLite）
```

## 代码规范

- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

## 添加新功能

1. 在 `app/models/` 定义数据模型
2. 在 `app/schemas/` 定义 Pydantic 模型
3. 在 `app/services/` 实现业务逻辑
4. 在 `app/api/` 添加路由
5. 在 `app/templates/` 创建页面

## API 文档

启动后访问 http://localhost:37201/docs 查看自动生成的 Swagger 文档。

## 调试

启用 SQL 日志：
```python
# app/database.py
engine = create_engine(DATABASE_URL, echo=True)
```

使用断点：
```python
breakpoint()
```

## 数据库迁移

项目使用 SQLAlchemy 自动建表。如需迁移支持：

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## 相关文档

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Bootstrap](https://getbootstrap.com/docs/)
- [APScheduler](https://apscheduler.readthedocs.io/)
