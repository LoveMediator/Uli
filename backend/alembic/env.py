"""
Alembic environment configuration.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base

# Import models to register metadata
from app.models.user import User, RefreshToken, AuthLoginLog  # noqa: F401
from app.models.relationship import Relationship  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.snapshot import EventSnapshot  # noqa: F401
from app.models.judge import JudgeResult  # noqa: F401
from app.models.review import Review, ReviewVersion, CalendarEntry, FollowupMessage  # noqa: F401
from app.models.session import PrivateSession, PrivateMessage  # noqa: F401
from app.models.audit import EventStateLog, AiCallLog  # noqa: F401
from app.models.elf import ElfMessage, ModerationLog  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set DB URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
