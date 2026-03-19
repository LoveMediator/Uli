"""公共 ID 生成工具。

DB 全局约定：对外标识统一使用 public_id varchar(40)。
当前使用 UUID4 作为默认实现，不引入额外依赖。
后续可替换为 ULID / 雪花 ID 等，保持函数签名不变即可。
"""

import uuid


def generate_public_id() -> str:
    """生成一个全局唯一的 public_id（当前为 UUID4 hex，32 字符）。"""
    return uuid.uuid4().hex
