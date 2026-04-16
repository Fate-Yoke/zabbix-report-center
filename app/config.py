"""
配置管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/zabbix_web.db")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "zabbix-web-secret-key-2024-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 加密密钥（用于敏感信息加密存储）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "zabbix-encryption-key-32bytes!")

# 验证码配置
CAPTCHA_EXPIRE_SECONDS = 300  # 5分钟

# 应用配置
APP_NAME = "Zabbix Report Center"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 监控配置
DEFAULT_TIME_RANGE = 86400  # 默认24小时
