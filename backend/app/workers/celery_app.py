"""Celery 应用初始化骨架。

当前为预留结构。启用方法：
1. pip install celery[redis]
2. 配置环境变量 REDIS_URL（与 config.py 统一）
3. celery -A app.workers.celery_app worker --loglevel=info
"""

try:
    from celery import Celery

    from app.core.config import settings

    celery_app = Celery(
        "love_mediator",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Shanghai",
        enable_utc=True,
    )
except ImportError:
    celery_app = None
