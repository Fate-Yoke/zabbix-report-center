# API 文档

Zabbix Report Center RESTful API 接口文档。

## 基础信息

- **Base URL**: `http://localhost:37201/api`
- **认证方式**: JWT Token (Cookie)
- **数据格式**: JSON

## 认证

### 注册

创建新用户账号。首个注册用户自动成为管理员。

**请求**

```http
POST /api/register
Content-Type: application/json

{
  "username": "admin",
  "password": "password123",
  "email": "admin@example.com"
}
```

**响应**

```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### 登录

用户登录获取访问令牌。

**请求**

```http
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123",
  "captcha_id": "uuid",
  "captcha_code": "1234"
}
```

**响应**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true
  }
}
```

### 获取验证码

获取图形验证码。

**请求**

```http
GET /api/captcha
```

**响应**

```json
{
  "captcha_id": "550e8400-e29b-41d4-a716-446655440000",
  "captcha_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### 获取当前用户信息

**请求**

```http
GET /api/me
Cookie: access_token=<token>
```

**响应**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_admin": true,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

## 用户管理

### 获取用户列表

**权限**: 管理员

**请求**

```http
GET /api/users
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 更新用户

**权限**: 管理员

**请求**

```http
PUT /api/users/{user_id}
Cookie: access_token=<token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "is_admin": false,
  "is_active": true
}
```

**响应**

```json
{
  "message": "用户更新成功"
}
```

### 删除用户

**权限**: 管理员

**请求**

```http
DELETE /api/users/{user_id}
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "用户删除成功"
}
```

### 修改密码

**请求**

```http
POST /api/users/change-password
Cookie: access_token=<token>
Content-Type: application/json

{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**响应**

```json
{
  "message": "密码修改成功"
}
```

## Zabbix 配置管理

### 获取配置列表

**请求**

```http
GET /api/zabbix-configs
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "id": 1,
    "name": "生产环境",
    "url": "http://zabbix.example.com",
    "auth_type": "token",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 创建配置

**权限**: 管理员

**请求**

```http
POST /api/zabbix-configs
Cookie: access_token=<token>
Content-Type: application/json

{
  "name": "生产环境",
  "url": "http://zabbix.example.com",
  "auth_type": "token",
  "token": "your-api-token"
}
```

或使用用户名密码：

```json
{
  "name": "测试环境",
  "url": "http://zabbix-test.example.com",
  "auth_type": "password",
  "username": "Admin",
  "password": "zabbix"
}
```

**响应**

```json
{
  "message": "配置创建成功",
  "id": 1
}
```

### 更新配置

**权限**: 管理员

**请求**

```http
PUT /api/zabbix-configs/{config_id}
Cookie: access_token=<token>
Content-Type: application/json

{
  "name": "生产环境（更新）",
  "url": "http://zabbix.example.com",
  "is_active": true
}
```

**响应**

```json
{
  "message": "配置更新成功"
}
```

### 删除配置

**权限**: 管理员

**请求**

```http
DELETE /api/zabbix-configs/{config_id}
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "配置删除成功"
}
```

### 测试连接

**请求**

```http
POST /api/zabbix-configs/{config_id}/test
Cookie: access_token=<token>
```

**响应**

```json
{
  "success": true,
  "message": "连接成功",
  "version": "6.0.10"
}
```

## 邮件配置管理

### 获取配置列表

**权限**: 管理员

**请求**

```http
GET /api/email-configs
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "id": 1,
    "name": "企业邮箱",
    "smtp_server": "smtp.example.com",
    "smtp_port": 465,
    "smtp_user": "noreply@example.com",
    "use_ssl": true,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 创建配置

**权限**: 管理员

**请求**

```http
POST /api/email-configs
Cookie: access_token=<token>
Content-Type: application/json

{
  "name": "企业邮箱",
  "smtp_server": "smtp.example.com",
  "smtp_port": 465,
  "smtp_user": "noreply@example.com",
  "smtp_pass": "password123",
  "use_ssl": true
}
```

**响应**

```json
{
  "message": "配置创建成功",
  "id": 1
}
```

### 测试邮件发送

**权限**: 管理员

**请求**

```http
POST /api/email-configs/{config_id}/test
Cookie: access_token=<token>
Content-Type: application/json

{
  "to_email": "test@example.com"
}
```

**响应**

```json
{
  "success": true,
  "message": "测试邮件发送成功"
}
```

## 监控信息查询

### 获取主机组列表

**请求**

```http
GET /api/monitor/hostgroups?config_id=1
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "groupid": "2",
    "name": "Linux servers"
  },
  {
    "groupid": "4",
    "name": "Zabbix servers"
  }
]
```

### 获取主机列表

**请求**

```http
GET /api/monitor/hosts?config_id=1&groupid=2
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "hostid": "10084",
    "host": "web-server-01",
    "name": "Web Server 01",
    "status": "0",
    "available": "1"
  }
]
```

### 获取监控项

**请求**

```http
GET /api/monitor/items?config_id=1&hostid=10084&search=cpu
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "itemid": "23296",
    "name": "CPU utilization",
    "key_": "system.cpu.util",
    "lastvalue": "15.5",
    "units": "%",
    "lastclock": "1704067200"
  }
]
```

### 获取历史数据

**请求**

```http
GET /api/monitor/history?config_id=1&itemid=23296&time_from=1704067200&time_till=1704153600
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "clock": "1704067200",
    "value": "15.5"
  },
  {
    "clock": "1704067260",
    "value": "16.2"
  }
]
```

### 导出监控数据

**请求**

```http
POST /api/monitor/export
Cookie: access_token=<token>
Content-Type: application/json

{
  "config_id": 1,
  "hostgroup_id": "2",
  "item_pattern": "cpu|memory",
  "time_from": 1704067200,
  "time_till": 1704153600
}
```

**响应**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "导出任务已创建"
}
```

### 下载导出文件

**请求**

```http
GET /api/monitor/download/{task_id}
Cookie: access_token=<token>
```

**响应**

Excel 文件下载

## 定时任务管理

### 获取任务列表

**请求**

```http
GET /api/tasks?config_id=1
Cookie: access_token=<token>
```

**响应**

```json
[
  {
    "id": 1,
    "name": "每日CPU报表",
    "config_id": 1,
    "config_name": "生产环境",
    "cron_expression": "0 9 * * *",
    "hostgroup_id": "2",
    "hostgroup_name": "Linux servers",
    "item_pattern": "cpu",
    "recipients": "admin@example.com,ops@example.com",
    "is_active": true,
    "last_run_time": "2024-01-01T09:00:00",
    "last_run_status": "success",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 创建任务

**请求**

```http
POST /api/tasks
Cookie: access_token=<token>
Content-Type: application/json

{
  "name": "每日CPU报表",
  "config_id": 1,
  "cron_expression": "0 9 * * *",
  "hostgroup_id": "2",
  "item_pattern": "cpu",
  "recipients": "admin@example.com,ops@example.com",
  "email_config_id": 1
}
```

**响应**

```json
{
  "message": "任务创建成功",
  "id": 1
}
```

### 更新任务

**请求**

```http
PUT /api/tasks/{task_id}
Cookie: access_token=<token>
Content-Type: application/json

{
  "name": "每日CPU报表（更新）",
  "cron_expression": "0 10 * * *",
  "is_active": true
}
```

**响应**

```json
{
  "message": "任务更新成功"
}
```

### 删除任务

**请求**

```http
DELETE /api/tasks/{task_id}
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "任务删除成功"
}
```

### 手动执行任务

**请求**

```http
POST /api/tasks/{task_id}/run
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "任务已加入执行队列"
}
```

### 暂停/恢复任务

**请求**

```http
POST /api/tasks/{task_id}/toggle
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "任务已暂停",
  "is_active": false
}
```

## 系统日志

### 获取日志列表

**权限**: 管理员

**请求**

```http
GET /api/logs?level=INFO&limit=100&offset=0
Cookie: access_token=<token>
```

**查询参数**

- `level`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `search`: 搜索关键字
- `limit`: 每页数量
- `offset`: 偏移量

**响应**

```json
{
  "total": 1000,
  "logs": [
    {
      "id": 1,
      "level": "INFO",
      "message": "用户 admin 登录成功",
      "module": "app.api.auth",
      "created_at": "2024-01-01T09:00:00"
    }
  ]
}
```

### 清理旧日志

**权限**: 管理员

**请求**

```http
DELETE /api/logs/cleanup?days=30
Cookie: access_token=<token>
```

**响应**

```json
{
  "message": "已删除 500 条日志"
}
```

## 系统设置

### 获取系统设置

**权限**: 管理员

**请求**

```http
GET /api/system/settings
Cookie: access_token=<token>
```

**响应**

```json
{
  "timezone": "Asia/Shanghai",
  "log_retention_days": 30,
  "max_export_rows": 10000
}
```

### 更新系统设置

**权限**: 管理员

**请求**

```http
PUT /api/system/settings
Cookie: access_token=<token>
Content-Type: application/json

{
  "timezone": "Asia/Shanghai",
  "log_retention_days": 60
}
```

**响应**

```json
{
  "message": "设置更新成功"
}
```

## 错误响应

所有 API 在发生错误时返回统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或认证失败
- `403 Forbidden`: 无权限访问
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 认证说明

大部分 API 需要用户认证。认证通过 Cookie 中的 JWT Token 实现。

登录成功后，服务器会设置 `access_token` Cookie，后续请求会自动携带。

Token 有效期为 24 小时，过期后需要重新登录。

## 速率限制

当前版本暂未实现速率限制，建议客户端合理控制请求频率。

## 分页

列表类 API 支持分页参数：

- `limit`: 每页数量（默认 50，最大 1000）
- `offset`: 偏移量（默认 0）

响应包含 `total` 字段表示总数。

## 时间格式

所有时间字段使用 ISO 8601 格式：`YYYY-MM-DDTHH:MM:SS`

时区为系统设置的时区（默认 Asia/Shanghai）。
