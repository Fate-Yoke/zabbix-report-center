# 安全说明

## 安全机制

### 用户密码
- 使用 bcrypt 哈希算法，不可逆
- 自动加盐，防止彩虹表攻击
- 只存储哈希值，无法还原原始密码

### 敏感信息加密
使用 Fernet 对称加密（AES-128）存储：
- Zabbix API Token
- Zabbix 用户名和密码
- 邮件服务器密码

加密特性：
- 基于 PBKDF2 密钥派生（100,000 次迭代）
- 使用 SHA-256 哈希算法

### JWT Token
- 算法：HS256
- 有效期：24 小时
- Cookie 存储

## 生产环境配置

### 生成密钥

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

将生成的密钥写入 `.env` 文件。

### 保护密钥

1. 不要提交 `.env` 到 Git（已添加到 .gitignore）
2. 设置文件权限：`chmod 600 .env`
3. 备份密钥到安全位置

注意：更改 `ENCRYPTION_KEY` 后，已加密的数据将无法解密！

## Docker 安全

1. 修改 `.env` 中的 MySQL 密码
2. 不要暴露数据库端口到外网
3. 配合 Nginx 使用 HTTPS
4. 定期更新镜像

## 数据库安全

### 敏感字段

| 字段 | 加密方式 |
|------|----------|
| users.password_hash | bcrypt（不可逆） |
| zabbix_configs.token | Fernet（可逆） |
| zabbix_configs.password | Fernet（可逆） |
| email_configs.smtp_pass | Fernet（可逆） |

### 备份

```bash
# Docker
docker exec zabbix-report-mysql mysqldump -u root -p zabbix_report_center > backup.sql

# 本地
mysqldump -u zabbix -p zabbix_report_center > backup.sql
```

## 网络安全

### HTTPS 配置（Nginx）

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:37201;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 防火墙

```bash
ufw allow 443/tcp
ufw deny 37201/tcp
```

### 限制访问 IP

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["192.168.1.*", "10.0.0.*"]
)
```

## 检查清单

- [ ] 已修改 `.env` 中的密钥
- [ ] `.env` 文件权限为 600
- [ ] 配置 HTTPS
- [ ] 配置防火墙
- [ ] 定期备份数据库和密钥

## 日志审计

系统记录以下操作：
- 用户登录/登出
- 配置修改
- 任务执行

日志存储在 `system_logs` 表。
