from collections.abc import Generator
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _build_engine(url: str, **kwargs):
    """Build an Engine that's safe for PgBouncer transaction-pool mode (Supabase
    pooler, port 6543). Prepared statements are disabled by default because they
    break under transaction pooling — different requests get different backends
    and don't see each other's prepared statements.

    Override by adding ?prepare_threshold=N to the URL (N=0 prepares immediately,
    N>0 prepares after N uses, 'none' explicitly disables). For direct Postgres
    connections (not via pooler) you can set it to 5 or so for a small perf win."""
    parts = urlsplit(url)
    q = parse_qs(parts.query)
    threshold: int | None = None  # safe default for pgbouncer
    if "prepare_threshold" in q:
        val = q.pop("prepare_threshold")[0]
        threshold = None if val.lower() in {"none", "null", "off"} else int(val)
    clean_url = urlunsplit(parts._replace(query=urlencode(q, doseq=True)))
    return create_engine(
        clean_url,
        pool_pre_ping=True,
        future=True,
        connect_args={"prepare_threshold": threshold},
        **kwargs,
    )


engine = _build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
