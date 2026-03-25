"""Celery 应用初始化骨架。

当前为预留结构。启用方法：
1. pip install celery[redis]
2. 配置 CELERY_BROKER_URL 环境变量
3. celery -A app.workers.celery_app worker --loglevel=info
"""

try:
    from celery import Celery

    celery_app = Celery(
        "love_mediator",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/1",
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
