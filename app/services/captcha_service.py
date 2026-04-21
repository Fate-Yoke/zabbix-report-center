"""
验证码服务
"""
import io
import secrets
import time
from typing import Tuple, Optional
from captcha.image import ImageCaptcha

from app.config import CAPTCHA_EXPIRE_SECONDS


class CaptchaService:
    """验证码服务类"""

    def __init__(self):
        # 存储验证码的字典 {key: {"code": str, "expire": int}}
        self._captchas = {}
        self._generator = ImageCaptcha(width=140, height=50, fonts=None)

    def generate(self) -> Tuple[str, bytes]:
        """
        生成验证码
        返回: (captcha_key, image_bytes)
        """
        # 生成随机验证码
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(4))

        # 生成唯一key
        captcha_key = secrets.token_urlsafe(16)

        # 存储验证码
        self._captchas[captcha_key] = {
            "code": code.lower(),
            "expire": int(time.time()) + CAPTCHA_EXPIRE_SECONDS
        }

        # 生成图片
        image = self._generator.generate_image(code)

        # 转换为bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        # 清理过期验证码
        self._cleanup_expired()

        return captcha_key, image_bytes

    def verify(self, captcha_key: str, code: str) -> bool:
        """
        验证验证码
        """
        if not captcha_key or not code:
            return False

        captcha_data = self._captchas.get(captcha_key)
        if not captcha_data:
            return False

        # 检查是否过期
        if time.time() > captcha_data["expire"]:
            del self._captchas[captcha_key]
            return False

        # 验证码正确则删除(一次性使用)
        if captcha_data["code"] == code.lower():
            del self._captchas[captcha_key]
            return True

        return False

    def _cleanup_expired(self):
        """清理过期的验证码"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self._captchas.items()
            if current_time > v["expire"]
        ]
        for k in expired_keys:
            del self._captchas[k]


# 全局实例
captcha_service = CaptchaService()
