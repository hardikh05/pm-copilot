from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.config import settings
from app.db import Base, _build_engine
from app.models import register_all  # noqa: F401  (ensures models import)

config = context.config

# Don't push the URL through ConfigParser — % in passwords (URL-encoded) breaks
# its interpolation. We build the Engine directly from settings.

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = _build_engine(settings.database_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
