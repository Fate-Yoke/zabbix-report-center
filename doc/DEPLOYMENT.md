# 部署指南

本文档详细说明如何在生产环境中部署 Zabbix Report Center。

## 目录

- [系统要求](#系统要求)
- [Docker 部署（推荐）](#docker-部署推荐)
- [本地部署](#本地部署)
- [配置说明](#配置说明)
- [使用 Systemd 管理](#使用-systemd-管理)
- [使用 Nginx 反向代理](#使用-nginx-反向代理)
- [数据库迁移](#数据库迁移)
- [备份与恢复](#备份与恢复)
- [监控与日志](#监控与日志)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

## 系统要求

### 硬件要求

- **CPU**: 2 核心及以上
- **内存**: 2GB 及以上
- **磁盘**: 10GB 及以上可用空间

### 软件要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+ / CentOS 7+) / Windows / macOS
- **Docker 部署**: Docker + Docker Compose
- **本地部署**: Python 3.8+ / MySQL 8.0+

## Docker 部署（推荐）

Docker 部署是推荐的生产环境部署方式，自动包含 MySQL 数据库。

### 1. 安装 Docker

**Ubuntu/Debian:**

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**

```bash
yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl start docker
systemctl enable docker
```

**Windows/macOS:**

下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2. 克隆项目

```bash
git clone <repository-url>
cd zabbix-report-center
```

### 3. 配置环境变量

```bash
# 复制配置文件模板
cp docker-compose.yml.example docker-compose.yml
cp .env.example .env

# 编辑配置
nano .env
nano docker-compose.yml
```

修改 `.env` 文件中的以下配置：

```env
# MySQL 数据库密码
MYSQL_ROOT_PASSWORD=your-strong-password

# JWT 密钥（生成方法见下方）
SECRET_KEY=your-secret-key

# 加密密钥（生成方法见下方）
ENCRYPTION_KEY=your-encryption-key

# 调试模式
DEBUG=false
```

根据需要修改 `docker-compose.yml` 中的端口映射等配置。

生成密钥：

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### 4. 启动服务

**Linux/macOS:**

```bash
chmod +x start.sh
./start.sh
```

**Windows:**

```cmd
start.bat
```

### 5. 访问系统

打开浏览器访问：http://localhost:38204

首次注册的用户将自动成为管理员。

### Docker 常用命令

```bash
# 查看运行状态
docker-compose ps

# 查看应用日志
docker-compose logs -f app

# 查看数据库日志
docker-compose logs -f mysql

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 进入容器
docker exec -it zabbix-report-center bash

# 备份数据库
docker exec zabbix-report-mysql mysqldump -u root -p zabbix_report_center > backup.sql

# 恢复数据库
docker exec -i zabbix-report-mysql mysql -u root -p zabbix_report_center < backup.sql
```

### 数据持久化

Docker 部署使用 volumes 持久化数据：

- `mysql_data`: MySQL 数据库文件
- `exports_data`: 导出的 Excel 文件

即使删除容器，数据也不会丢失。要完全清除数据：

```bash
docker-compose down -v
```

## 本地部署

## 本地部署

适合开发测试或无法使用 Docker 的环境。

### 1. 安装 Python 和 MySQL

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server
```

**CentOS/RHEL:**

```bash
sudo yum install python3 python3-pip mysql-server
```

### 2. 创建数据库

```bash
mysql -u root -p
```

```sql
CREATE DATABASE zabbix_report_center CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'zabbix'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON zabbix_report_center.* TO 'zabbix'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 创建部署用户

```bash
# 创建专用用户
sudo useradd -m -s /bin/bash zabbix-report
sudo su - zabbix-report
```

### 4. 下载项目

```bash
cd /opt
sudo git clone <repository-url> zabbix-report-center
sudo chown -R zabbix-report:zabbix-report zabbix-report-center
cd zabbix-report-center
```

### 5. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

`.env` 文件示例：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://zabbix:your-password@localhost/zabbix_report_center

# 应用密钥（必须修改）
SECRET_KEY=your-random-secret-key-here

# 加密密钥（必须修改）
ENCRYPTION_KEY=your-random-encryption-key-here

# 调试模式（生产环境设为 false）
DEBUG=false
```

生成密钥：

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### 8. 设置文件权限

```bash
# 设置环境变量文件权限
chmod 600 .env

# 创建导出目录
mkdir -p exports

# 设置目录权限
chmod 700 exports
```

### 9. 启动服务

```bash
python run.py
```

访问 http://服务器IP:38204 测试是否正常。

## 配置说明

### 应用配置

编辑 `app/config.py` 进行高级配置：

```python
# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zabbix_web.db")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 加密密钥
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# 应用配置
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

### 日志配置

日志级别在 `app/main.py` 中配置：

```python
logging.basicConfig(
    level=logging.INFO,  # 生产环境使用 INFO
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

## 使用 Systemd 管理

### 1. 创建 Systemd 服务文件

```bash
sudo nano /etc/systemd/system/zabbix-report.service
```

内容如下：

```ini
[Unit]
Description=Zabbix Report Center
After=network.target

[Service]
Type=simple
User=zabbix-report
Group=zabbix-report
WorkingDirectory=/opt/zabbix-report-center
Environment="PATH=/opt/zabbix-report-center/venv/bin"
ExecStart=/opt/zabbix-report-center/venv/bin/python run.py
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/zabbix-report-center/instance /opt/zabbix-report-center/logs

[Install]
WantedBy=multi-user.target
```

### 2. 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start zabbix-report

# 查看状态
sudo systemctl status zabbix-report

# 设置开机自启
sudo systemctl enable zabbix-report
```

### 3. 管理服务

```bash
# 停止服务
sudo systemctl stop zabbix-report

# 重启服务
sudo systemctl restart zabbix-report

# 查看日志
sudo journalctl -u zabbix-report -f
```

## 使用 Nginx 反向代理

### 1. 安装 Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. 配置 SSL 证书

```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 构建前端

```bash
cd /opt/zabbix-report-center/frontend
npm install
npm run build
```

前端构建产物在 `frontend/dist` 目录。

### 4. 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/zabbix-report
```

内容如下：

```nginx
# 后端 API 上游
upstream zabbix_report_api {
    server 127.0.0.1:38204;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/zabbix-report-access.log;
    error_log /var/log/nginx/zabbix-report-error.log;

    # 客户端上传大小限制
    client_max_body_size 50M;

    # 前端静态文件
    location / {
        root /opt/zabbix-report-center/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        proxy_pass http://zabbix_report_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 导出文件下载
    location /exports/ {
        proxy_pass http://zabbix_report_api;
        proxy_set_header Host $host;
    }
}
```

### 5. 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/zabbix-report /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

## 数据库迁移

### 从 SQLite 迁移到 PostgreSQL

#### 1. 安装 PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib
```

#### 2. 创建数据库

```bash
sudo -u postgres psql
CREATE DATABASE zabbix_report;
CREATE USER zabbix_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE zabbix_report TO zabbix_user;
\q
```

#### 3. 安装 PostgreSQL 驱动

```bash
pip install psycopg2-binary
```

#### 4. 修改配置

编辑 `.env`：

```env
DATABASE_URL=postgresql://zabbix_user:your_password@localhost/zabbix_report
```

#### 5. 导出和导入数据

```bash
# 导出 SQLite 数据
sqlite3 instance/zabbix_web.db .dump > backup.sql

# 转换并导入到 PostgreSQL
# 需要手动调整 SQL 语法差异
```

## 备份与恢复

### 自动备份脚本

创建 `/opt/zabbix-report-center/backup.sh`：

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/zabbix-report"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/zabbix-report-center"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $APP_DIR/zabbix_web.db $BACKUP_DIR/zabbix_web_$DATE.db

# 备份环境变量
cp $APP_DIR/.env $BACKUP_DIR/.env_$DATE

# 压缩备份
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz \
    $BACKUP_DIR/zabbix_web_$DATE.db \
    $BACKUP_DIR/.env_$DATE

# 删除临时文件
rm $BACKUP_DIR/zabbix_web_$DATE.db
rm $BACKUP_DIR/.env_$DATE

# 删除 30 天前的备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "备份完成: backup_$DATE.tar.gz"
```

### 设置定时备份

```bash
# 添加执行权限
chmod +x /opt/zabbix-report-center/backup.sh

# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /opt/zabbix-report-center/backup.sh
```

### 恢复备份

```bash
# 解压备份
tar -xzf backup_20240101_020000.tar.gz

# 停止服务
sudo systemctl stop zabbix-report

# 恢复数据库
cp zabbix_web_20240101_020000.db /opt/zabbix-report-center/zabbix_web.db

# 恢复环境变量
cp .env_20240101_020000 /opt/zabbix-report-center/.env

# 启动服务
sudo systemctl start zabbix-report
```

## 监控与日志

### 日志位置

- **应用日志**: 数据库 `system_logs` 表
- **Systemd 日志**: `journalctl -u zabbix-report`
- **Nginx 日志**: `/var/log/nginx/zabbix-report-*.log`

### 日志轮转

创建 `/etc/logrotate.d/zabbix-report`：

```
/var/log/nginx/zabbix-report-*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 监控检查

```bash
# 检查服务状态
systemctl status zabbix-report

# 检查端口监听
netstat -tlnp | grep 38204

# 检查进程
ps aux | grep python

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

## 性能优化

### 1. 使用 Gunicorn

安装 Gunicorn：

```bash
pip install gunicorn
```

修改启动命令：

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:38204
```

### 2. 启用 Nginx 缓存

在 Nginx 配置中添加：

```nginx
# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=zabbix_cache:10m max_size=1g inactive=60m;

location /api/ {
    proxy_cache zabbix_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status;
    
    proxy_pass http://zabbix_report;
}
```

### 3. 数据库优化

对于 SQLite：

```python
# 在 app/database.py 中添加
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": None  # 自动提交模式
    }
)
```

### 4. 限制并发任务

在 `app/config.py` 中：

```python
# 最大并发导出任务数
MAX_CONCURRENT_EXPORTS = 3

# 最大并发定时任务数
MAX_CONCURRENT_TASKS = 5
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u zabbix-report -n 100 --no-pager

# 检查端口占用
sudo lsof -i :38204

# 检查文件权限
ls -la /opt/zabbix-report-center
```

### 数据库锁定

```bash
# 检查数据库文件
file zabbix_web.db

# 检查是否有其他进程占用
lsof zabbix_web.db

# 重建数据库索引
sqlite3 zabbix_web.db "VACUUM;"
```

### 内存不足

```bash
# 查看内存使用
free -h
ps aux --sort=-%mem | head

# 限制进程内存（在 systemd 服务文件中）
MemoryLimit=1G
```

### Nginx 502 错误

```bash
# 检查应用是否运行
systemctl status zabbix-report

# 检查 Nginx 错误日志
tail -f /var/log/nginx/zabbix-report-error.log

# 检查 SELinux（CentOS）
sudo setsebool -P httpd_can_network_connect 1
```

## 安全加固

### 1. 防火墙配置

```bash
# 只允许 Nginx 访问应用端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 38204/tcp
sudo ufw enable
```

### 2. 限制文件权限

```bash
chmod 600 .env
chmod 600 zabbix_web.db
chmod 700 instance logs
```

### 3. 定期更新

```bash
# 更新系统
sudo apt update && sudo apt upgrade

# 更新 Python 依赖
pip install --upgrade -r requirements.txt
```

## 升级指南

### 1. 备份数据

```bash
./backup.sh
```

### 2. 拉取新代码

```bash
cd /opt/zabbix-report-center
git pull
```

### 3. 更新依赖

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 重启服务

```bash
sudo systemctl restart zabbix-report
```

### 5. 验证升级

```bash
# 检查服务状态
systemctl status zabbix-report

# 检查日志
journalctl -u zabbix-report -n 50
```

## 问题排查

遇到问题时：
1. 查看日志：`docker-compose logs -f app` 或 `journalctl -u zabbix-report -f`
2. 检查端口：`netstat -tlnp | grep 38204`
3. 检查进程：`ps aux | grep python`
4. 提交 Issue 并附上日志
