"""v1 路由模块包。

为了在不同环境/打包方式下保持稳定的 import 行为，显式导出各子模块。
"""

from . import auth, calendar, elf, events, reviews

__all__ = ["auth", "calendar", "elf", "events", "reviews"]

