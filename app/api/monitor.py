"""
监控信息API
"""
import os
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from cachetools import TTLCache

from app.config import BASE_DIR
from app.database import get_db
from app.models.user import User
from app.models.zabbix_config import ZabbixConfig
from app.models.monitor_filter import MonitorFilter
from app.models.export_task import ExportTask
from app.schemas.monitor import MonitorFilterCreate, MonitorFilterUpdate, MonitorFilterResponse
from app.schemas.export import ExportTaskCreate, ExportTaskResponse
from app.api.auth import get_current_user_required
from app.services.zabbix_service import ZabbixService
from app.services.monitor_service import MonitorService
from app.services.export_service import do_export

router = APIRouter(prefix="/monitor", tags=["监控信息"])
logger = logging.getLogger(__name__)

# Dashboard数据缓存：key为(zabbix_config_id, cache_time)，value为(data, timestamp)
# 使用字典存储不同缓存时间的数据
dashboard_cache: Dict[str, tuple] = {}

# 导出目录
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def check_zabbix_access(user: User, zabbix_config_id: int) -> None:
    """检查用户是否有权限访问指定的Zabbix配置"""
    if not user.can_access_zabbix(zabbix_config_id):
        raise HTTPException(status_code=403, detail="您没有权限访问此Zabbix配置")


class MonitorDataRequest(BaseModel):
    """监控数据请求模型"""
    filter_ids: List[int]
    zabbix_config_id: int
    time_range: int = 86400


class ExportRequest(BaseModel):
    """导出请求模型"""
    filter_ids: List[int]
    zabbix_config_id: int
    include_device_overview: bool = True


@router.get("/dashboard")
async def get_dashboard(
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    force_refresh: bool = Query(False, description="强制刷新，忽略缓存"),
    cache_time: int = Query(300, description="缓存时间（秒），0表示不使用缓存"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取仪表盘数据（带缓存）"""
    # 检查权限
    check_zabbix_access(user, zabbix_config_id)

    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    # 检查缓存（如果不是强制刷新且缓存时间大于0）
    cache_key = f"dashboard_{zabbix_config_id}"
    if not force_refresh and cache_time > 0 and cache_key in dashboard_cache:
        cached_data, cached_time_str = dashboard_cache[cache_key]
        cached_time = datetime.fromisoformat(cached_time_str)

        # 检查缓存是否过期
        elapsed = (datetime.now() - cached_time).total_seconds()
        if elapsed < cache_time:
            # 返回缓存数据，并附带缓存时间
            return {
                **cached_data,
                "cached": True,
                "cached_at": cached_time_str
            }

    # 获取新数据
    zabbix_service = ZabbixService.from_config(config)
    monitor_service = MonitorService(zabbix_service)

    try:
        data = monitor_service.get_dashboard_stats()
        current_time = datetime.now().isoformat()

        # 存入缓存（如果缓存时间大于0）
        if cache_time > 0:
            dashboard_cache[cache_key] = (data, current_time)

        # 返回数据，附带更新时间
        return {
            **data,
            "cached": False,
            "cached_at": current_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/hosts")
async def get_hosts(
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取所有主机列表"""
    # 检查权限
    check_zabbix_access(user, zabbix_config_id)

    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    zabbix_service = ZabbixService.from_config(config)
    try:
        hosts = zabbix_service.get_hosts()
        return hosts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主机失败: {str(e)}")


@router.get("/items/{hostid}")
async def get_host_items(
    hostid: str,
    zabbix_config_id: int = Query(..., description="Zabbix配置ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取主机的监控项列表"""
    # 检查权限
    check_zabbix_access(user, zabbix_config_id)

    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    zabbix_service = ZabbixService.from_config(config)
    try:
        items = zabbix_service.get_items(hostid, search)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控项失败: {str(e)}")


# ========== 监控筛选配置 ==========

@router.get("/filters", response_model=List[MonitorFilterResponse])
async def list_filters(
    zabbix_config_id: Optional[int] = Query(None, description="Zabbix配置ID，用于筛选关联的配置"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取监控筛选配置列表"""
    query = db.query(MonitorFilter)

    if zabbix_config_id is not None:
        # 筛选关联到此Zabbix配置的筛选配置
        query = query.filter(
            MonitorFilter.zabbix_config_ids.contains(zabbix_config_id)
        )

    all_filters = query.all()

    # 获取所有有效的 Zabbix 配置ID
    valid_zabbix_ids = set(
        id[0] for id in db.query(ZabbixConfig.id).all()
    )

    # 如果是普通用户，只返回其有权限访问的筛选配置
    if not user.is_admin:
        allowed_ids = user.allowed_zabbix_ids or []
        if not allowed_ids:
            return []

        # 过滤：只保留至少包含一个用户有权限且有效的Zabbix配置的筛选配置
        filtered = []
        for f in all_filters:
            if f.zabbix_config_ids:
                # 检查是否有交集（配置ID必须既在用户权限内，又是有效的）
                valid_accessible_ids = [zid for zid in f.zabbix_config_ids
                                       if zid in allowed_ids and zid in valid_zabbix_ids]
                if valid_accessible_ids:
                    filtered.append(f)
        all_filters = filtered

    # 转换为响应模型，兼容旧格式数据
    result = []
    for f in all_filters:
        # 兼容旧格式：如果 item_patterns 是字符串数组，转换为对象数组
        item_patterns = f.item_patterns or []
        if item_patterns and isinstance(item_patterns[0], str):
            # 旧格式：字符串数组，转换为对象数组
            item_patterns = [{"pattern": p, "match_type": "exact"} for p in item_patterns]

        response = MonitorFilterResponse(
            id=f.id,
            name=f.name,
            description=f.description,
            item_patterns=item_patterns,
            history_type=f.history_type,
            is_network=f.is_network,
            zabbix_config_ids=f.zabbix_config_ids or [],
            use_regex=f.use_regex or False,
            regex_pattern=f.regex_pattern,
            created_at=f.created_at
        )
        result.append(response)

    return result


@router.post("/filters", response_model=MonitorFilterResponse)
async def create_filter(
    filter_data: MonitorFilterCreate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """创建监控筛选配置"""
    # 验证 Zabbix 配置ID是否存在（创建时必须至少选择一个）
    if not filter_data.zabbix_config_ids or len(filter_data.zabbix_config_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="创建筛选配置时必须至少选择一个 Zabbix 配置"
        )

    valid_ids = db.query(ZabbixConfig.id).filter(
        ZabbixConfig.id.in_(filter_data.zabbix_config_ids)
    ).all()
    valid_ids = [id[0] for id in valid_ids]

    invalid_ids = set(filter_data.zabbix_config_ids) - set(valid_ids)
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"以下 Zabbix 配置不存在: {', '.join(map(str, invalid_ids))}"
        )

    filter_obj = MonitorFilter(
        name=filter_data.name,
        description=filter_data.description,
        use_regex=filter_data.use_regex,
        regex_pattern=filter_data.regex_pattern,
        item_patterns=[p.dict() for p in filter_data.item_patterns] if filter_data.item_patterns else None,
        history_type=filter_data.history_type,
        is_network=filter_data.is_network,
        thresholds=filter_data.thresholds,
        zabbix_config_ids=filter_data.zabbix_config_ids,
        created_by=user.id
    )
    db.add(filter_obj)
    db.commit()
    db.refresh(filter_obj)

    logger.info(f"用户 {user.username} 创建监控筛选配置: {filter_obj.name} (ID: {filter_obj.id})")

    return filter_obj


@router.get("/filters/{filter_id}", response_model=MonitorFilterResponse)
async def get_filter(
    filter_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取监控筛选配置详情"""
    filter_obj = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="配置不存在")
    return filter_obj


@router.put("/filters/{filter_id}", response_model=MonitorFilterResponse)
async def update_filter(
    filter_id: int,
    filter_data: MonitorFilterUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """更新监控筛选配置"""
    filter_obj = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 验证 Zabbix 配置ID是否存在（更新时允许为空，表示所有关联配置都被删除了）
    if filter_data.zabbix_config_ids is not None and len(filter_data.zabbix_config_ids) > 0:
        valid_ids = db.query(ZabbixConfig.id).filter(
            ZabbixConfig.id.in_(filter_data.zabbix_config_ids)
        ).all()
        valid_ids = [id[0] for id in valid_ids]

        invalid_ids = set(filter_data.zabbix_config_ids) - set(valid_ids)
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"以下 Zabbix 配置不存在: {', '.join(map(str, invalid_ids))}"
            )

    if filter_data.name is not None:
        filter_obj.name = filter_data.name
    if filter_data.description is not None:
        filter_obj.description = filter_data.description
    if filter_data.use_regex is not None:
        filter_obj.use_regex = filter_data.use_regex
    if filter_data.regex_pattern is not None:
        filter_obj.regex_pattern = filter_data.regex_pattern
    if filter_data.item_patterns is not None:
        filter_obj.item_patterns = [p.dict() for p in filter_data.item_patterns] if filter_data.item_patterns else None
    if filter_data.history_type is not None:
        filter_obj.history_type = filter_data.history_type
    if filter_data.is_network is not None:
        filter_obj.is_network = filter_data.is_network
    if filter_data.thresholds is not None:
        filter_obj.thresholds = filter_data.thresholds
    if filter_data.zabbix_config_ids is not None:
        filter_obj.zabbix_config_ids = filter_data.zabbix_config_ids

    db.commit()
    db.refresh(filter_obj)

    logger.info(f"用户 {user.username} 更新监控筛选配置: {filter_obj.name} (ID: {filter_obj.id})")

    return filter_obj


@router.delete("/filters/{filter_id}")
async def delete_filter(
    filter_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """删除监控筛选配置"""
    filter_obj = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
    if not filter_obj:
        raise HTTPException(status_code=404, detail="配置不存在")

    filter_name = filter_obj.name
    db.delete(filter_obj)
    db.commit()

    logger.info(f"用户 {user.username} 删除监控筛选配置: {filter_name} (ID: {filter_id})")

    return {"message": "删除成功"}


@router.post("/data")
async def get_monitor_data(
    request: MonitorDataRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """根据筛选配置获取监控数据"""
    # 检查权限
    check_zabbix_access(user, request.zabbix_config_id)

    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == request.zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    zabbix_service = ZabbixService.from_config(config)
    monitor_service = MonitorService(zabbix_service)

    try:
        data = monitor_service.get_multiple_filters_data(db, request.filter_ids, request.time_range)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.post("/data-stream")
async def get_monitor_data_stream(
    request: MonitorDataRequest,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """流式获取监控数据（边查询边返回）"""
    # 检查权限
    check_zabbix_access(user, request.zabbix_config_id)

    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == request.zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    async def generate():
        """生成器函数，逐步返回数据"""
        try:
            zabbix_service = ZabbixService.from_config(config)
            monitor_service = MonitorService(zabbix_service)

            # 获取所有在线主机（只查询一次）
            hosts_data = zabbix_service.get_all_hosts_with_status()
            online_hosts = hosts_data["online"]
            total_hosts = len(online_hosts)

            # 发送初始化信息
            yield f"data: {json.dumps({'type': 'init', 'total_hosts': total_hosts, 'filter_count': len(request.filter_ids)})}\n\n"

            # 计算时间范围
            time_till = int(time.time())
            time_from = time_till - request.time_range

            # 处理每个筛选配置
            for filter_id in request.filter_ids:
                filter_config = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
                if not filter_config:
                    continue

                filter_name = filter_config.name
                processed_hosts = 0

                # 发送筛选配置开始信息
                yield f"data: {json.dumps({'type': 'filter_start', 'filter_name': filter_name})}\n\n"

                # 处理每个主机
                for host in online_hosts:
                    hostid = host["hostid"]
                    hostname = host["name"]
                    ip = host["ip"]
                    groups = host["groups"]

                    # 获取该主机的监控数据
                    host_results = []

                    if filter_config.use_regex:
                        # 正则表达式模式
                        pattern = filter_config.regex_pattern
                        if pattern:
                            items_data = zabbix_service.get_item_stats(
                                hostid=hostid,
                                item_pattern=pattern,
                                history_type=filter_config.history_type,
                                use_regex=True,
                                is_network=filter_config.is_network,
                                time_from=time_from,
                                time_till=time_till
                            )

                            for item in items_data:
                                host_results.append({
                                    "hostid": hostid,
                                    "hostname": hostname,
                                    "ip": ip,
                                    "groups": groups,
                                    "item_name": item["name"],
                                    "current": item["current"],
                                    "max": item["max"],
                                    "min": item["min"],
                                    "avg": item["avg"]
                                })
                    else:
                        # 列表模式
                        for pattern_obj in filter_config.item_patterns:
                            if isinstance(pattern_obj, dict):
                                pattern = pattern_obj.get('pattern', '')
                                match_type = pattern_obj.get('match_type', 'exact')
                            else:
                                pattern = pattern_obj
                                match_type = 'exact'

                            if not pattern:
                                continue

                            use_regex = (match_type == 'fuzzy')

                            items_data = zabbix_service.get_item_stats(
                                hostid=hostid,
                                item_pattern=pattern,
                                history_type=filter_config.history_type,
                                use_regex=use_regex,
                                is_network=filter_config.is_network,
                                time_from=time_from,
                                time_till=time_till
                            )

                            for item in items_data:
                                host_results.append({
                                    "hostid": hostid,
                                    "hostname": hostname,
                                    "ip": ip,
                                    "groups": groups,
                                    "item_name": item["name"],
                                    "current": item["current"],
                                    "max": item["max"],
                                    "min": item["min"],
                                    "avg": item["avg"]
                                })

                    # 如果该主机有数据，立即发送
                    if host_results:
                        yield f"data: {json.dumps({'type': 'data', 'filter_name': filter_name, 'rows': host_results})}\n\n"

                    processed_hosts += 1

                    # 发送进度更新
                    if processed_hosts % 5 == 0 or processed_hosts == total_hosts:
                        progress = int((processed_hosts / total_hosts) * 100)
                        yield f"data: {json.dumps({'type': 'progress', 'filter_name': filter_name, 'progress': progress, 'processed': processed_hosts, 'total': total_hosts})}\n\n"

                # 发送筛选配置完成信息
                yield f"data: {json.dumps({'type': 'filter_complete', 'filter_name': filter_name})}\n\n"

            # 发送完成信息
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ========== 导出任务 ==========

@router.post("/export", response_model=ExportTaskResponse)
async def create_export_task(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """创建导出任务（后台执行）"""
    # 检查权限
    check_zabbix_access(user, request.zabbix_config_id)

    # 验证Zabbix配置
    config = db.query(ZabbixConfig).filter(ZabbixConfig.id == request.zabbix_config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Zabbix配置不存在")

    # 获取筛选配置名称
    filter_names = []
    for filter_id in request.filter_ids:
        filter_obj = db.query(MonitorFilter).filter(MonitorFilter.id == filter_id).first()
        if filter_obj:
            filter_names.append(filter_obj.name)

    # 创建导出任务记录
    task = ExportTask(
        zabbix_config_id=request.zabbix_config_id,
        zabbix_config_name=config.name,
        filter_ids=request.filter_ids,
        filter_names=filter_names,
        include_device_overview=request.include_device_overview,
        status="pending",
        created_by=user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 启动后台任务
    background_tasks.add_task(do_export, task.id)

    logger.info(f"用户 {user.username} 创建监控数据导出任务 (ID: {task.id}), 配置: {config.name}, 筛选: {', '.join(filter_names)}")

    return task


@router.get("/export/tasks", response_model=List[ExportTaskResponse])
async def list_export_tasks(
    limit: int = Query(20, description="返回数量限制"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取导出任务历史列表（仅返回用户有权限访问的Zabbix配置的任务）"""
    # 管理员可以看到所有任务
    if user.is_admin:
        tasks = db.query(ExportTask).order_by(
            ExportTask.created_at.desc()
        ).limit(limit).all()
    else:
        # 普通用户只能看到自己有权限的Zabbix配置的任务
        allowed_zabbix_ids = user.allowed_zabbix_ids or []
        if not allowed_zabbix_ids:
            # 如果用户没有任何Zabbix配置权限，返回空列表
            return []
        tasks = db.query(ExportTask).filter(
            ExportTask.zabbix_config_id.in_(allowed_zabbix_ids)
        ).order_by(
            ExportTask.created_at.desc()
        ).limit(limit).all()
    return tasks


@router.get("/export/tasks/{task_id}", response_model=ExportTaskResponse)
async def get_export_task(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """获取导出任务详情"""
    task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查权限：管理员或有该Zabbix配置权限的用户
    if not user.is_admin:
        check_zabbix_access(user, task.zabbix_config_id)

    return task


@router.get("/export/download/{task_id}")
async def download_export_file(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """下载导出文件"""
    task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查权限：管理员或有该Zabbix配置权限的用户
    if not user.is_admin:
        check_zabbix_access(user, task.zabbix_config_id)

    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"任务状态为{task.status}，无法下载")

    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=task.file_path,
        filename=task.filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.delete("/export/tasks/{task_id}")
async def delete_export_task(
    task_id: int,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """删除导出任务记录"""
    task = db.query(ExportTask).filter(ExportTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查权限：管理员或有该Zabbix配置权限的用户
    if not user.is_admin:
        check_zabbix_access(user, task.zabbix_config_id)

    # 删除文件
    if task.file_path and os.path.exists(task.file_path):
        try:
            os.remove(task.file_path)
        except:
            pass

    db.delete(task)
    db.commit()
    return {"message": "删除成功"}
