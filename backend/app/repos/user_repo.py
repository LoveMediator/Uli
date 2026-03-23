"""User 数据访问（1 号底座；供 auth / deps 使用）。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """按主键查询用户。"""
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    """按用户名查询用户。"""
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()


def create_user(
    db: Session,
    *,
    public_id: str,
    username: str,
    password_hash: str,
) -> User:
    """创建用户并 flush（不提交事务）。"""
    user = User(
        public_id=public_id,
        username=username,
        password_hash=password_hash,
    )
    db.add(user)
    db.flush()
    return user
