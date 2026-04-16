"""
系统日志API
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import asyncio

from app.database import get_db
from app.models.system_log import SystemLog
from app.models.user import User
from app.api.auth import get_current_user_required

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/")
async def get_logs(
    level: Optional[str] = Query(None, description="日志级别过滤"),
    start_time: Optional[str] = Query(None, description="开始时间 ISO格式"),
    end_time: Optional[str] = Query(None, description="结束时间 ISO格式"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取系统日志（仅管理员）"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    query = db.query(SystemLog)

    # 级别过滤
    if level:
        query = query.filter(SystemLog.level == level.upper())

    # 时间范围过滤
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(SystemLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始时间格式错误")

    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(SystemLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束时间格式错误")

    # 获取总数
    total = query.count()

    # 按时间倒序排列
    logs = query.order_by(desc(SystemLog.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/stream")
async def stream_logs(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """实时流式推送最新日志（仅管理员）"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    async def generate():
        """生成日志流"""
        from app.database import SessionLocal

        # 使用独立的数据库会话
        db_session = SessionLocal()

        try:
            last_id = 0

            # 先发送最近的100条日志
            initial_logs = db_session.query(SystemLog).order_by(desc(SystemLog.created_at)).limit(100).all()
            initial_logs.reverse()  # 反转顺序，从旧到新

            for log in initial_logs:
                yield f"data: {json.dumps(log.to_dict())}\n\n"
                last_id = max(last_id, log.id)

            # 持续推送新日志
            while True:
                await asyncio.sleep(1)  # 每秒检查一次

                new_logs = db_session.query(SystemLog).filter(
                    SystemLog.id > last_id
                ).order_by(SystemLog.id).all()

                for log in new_logs:
                    yield f"data: {json.dumps(log.to_dict())}\n\n"
                    last_id = log.id

                # 刷新会话以获取最新数据
                db_session.expire_all()
        finally:
            db_session.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/")
async def clear_logs(
    days: int = Query(30, ge=1, description="保留最近N天的日志"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """清理旧日志（仅管理员）"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

    cutoff_date = datetime.now() - timedelta(days=days)
    deleted = db.query(SystemLog).filter(SystemLog.created_at < cutoff_date).delete()
    db.commit()

    return {"message": f"已删除 {deleted} 条日志", "deleted": deleted}
