"""
加密服务
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import ENCRYPTION_KEY


class EncryptionService:
    """加密服务类"""

    def __init__(self):
        # 从配置的密钥生成Fernet密钥
        key = self._derive_key(ENCRYPTION_KEY)
        self.fernet = Fernet(key)

    def _derive_key(self, password: str) -> bytes:
        """从密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'zabbix_web_salt',  # 固定盐值
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plain_text: str) -> str:
        """加密字符串"""
        if not plain_text:
            return ""
        encrypted = self.fernet.encrypt(plain_text.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """解密字符串"""
        if not encrypted_text:
            return ""
        try:
            decrypted = self.fernet.decrypt(encrypted_text.encode())
            return decrypted.decode()
        except Exception:
            return ""


# 全局实例
encryption_service = EncryptionService()
