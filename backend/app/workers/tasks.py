"""异步任务骨架。

主流程当前仍为同步（judge_service 直接调用）。
后续接入真实 LLM 后，可将耗时裁判迁移为异步任务。
"""

from app.workers.celery_app import celery_app

if celery_app is not None:

    @celery_app.task(name="judge_event_async")
    def judge_event_task(event_id: int) -> dict:
        """异步裁判任务骨架。当前占位，后续替换为真实实现。"""
        return {"event_id": event_id, "status": "placeholder"}
