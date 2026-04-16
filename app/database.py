"""
数据库连接管理
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _init_default_settings():
    """初始化默认系统设置"""
    db = SessionLocal()
    try:
        from app.models.system_settings import SystemSettings

        # 默认设置项
        default_settings = [
            ("allow_registration", "true", "是否允许新用户注册"),
            ("require_activation", "false", "注册后是否需要管理员手动启用账户"),
        ]

        for key, value, description in default_settings:
            existing = db.query(SystemSettings).filter(
                SystemSettings.key == key
            ).first()

            if not existing:
                setting = SystemSettings(key=key, value=value, description=description)
                db.add(setting)

        db.commit()
    except Exception as e:
        print(f"初始化系统设置失败: {e}")
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册到Base.metadata
    from app.models.user import User
    from app.models.zabbix_config import ZabbixConfig
    from app.models.email_config import EmailConfig
    from app.models.monitor_filter import MonitorFilter
    from app.models.schedule_task import ScheduleTask, TaskLog
    from app.models.export_task import ExportTask
    from app.models.alert_export_task import AlertExportTask
    from app.models.system_settings import SystemSettings

    Base.metadata.create_all(bind=engine)

    # 初始化默认系统设置
    _init_default_settings()

    # 为已存在的表添加新列（兼容旧数据库）
    if "sqlite" in DATABASE_URL:
        with engine.connect() as conn:
            # 检查并添加 schedule_tasks 表的新列
            result = conn.execute(text("PRAGMA table_info(schedule_tasks)"))
            columns = [row[1] for row in result.fetchall()]

            new_columns = [
                ("include_device_overview", "BOOLEAN DEFAULT 0"),
                ("email_subject", "VARCHAR(200)"),
                ("email_body", "TEXT"),
                ("subject_suffix_config_name", "BOOLEAN DEFAULT 0"),
                ("subject_suffix_timestamp", "BOOLEAN DEFAULT 0"),
                ("email_include_device_overview", "BOOLEAN DEFAULT 1"),
                ("email_include_monitor_summary", "BOOLEAN DEFAULT 1"),
                ("email_include_alert_summary", "BOOLEAN DEFAULT 0"),
                ("include_alert_data", "BOOLEAN DEFAULT 0"),
            ]

            for col_name, col_type in new_columns:
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE schedule_tasks ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass

            # 检查并添加 task_logs 表的新列
            result = conn.execute(text("PRAGMA table_info(task_logs)"))
            log_columns = [row[1] for row in result.fetchall()]

            if "attachment_filename" not in log_columns:
                try:
                    conn.execute(text("ALTER TABLE task_logs ADD COLUMN attachment_filename VARCHAR(200)"))
                    conn.commit()
                except Exception:
                    pass

            # 检查并添加 users 表的新列
            result = conn.execute(text("PRAGMA table_info(users)"))
            user_columns = [row[1] for row in result.fetchall()]

            if "allowed_zabbix_ids" not in user_columns:
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN allowed_zabbix_ids JSON"))
                    conn.commit()
                except Exception:
                    pass

            # 检查并添加 monitor_filters 表的新列
            result = conn.execute(text("PRAGMA table_info(monitor_filters)"))
            filter_columns = [row[1] for row in result.fetchall()]

            if "zabbix_config_ids" not in filter_columns:
                try:
                    conn.execute(text("ALTER TABLE monitor_filters ADD COLUMN zabbix_config_ids JSON"))
                    conn.commit()
                except Exception:
                    pass

            if "regex_pattern" not in filter_columns:
                try:
                    conn.execute(text("ALTER TABLE monitor_filters ADD COLUMN regex_pattern VARCHAR(500)"))
                    conn.commit()
                except Exception:
                    pass
