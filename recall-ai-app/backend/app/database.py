"""SQLAlchemy 引擎与会话管理。

使用 SQLite 单文件数据库;启用 WAL 提升并发读性能。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite 需要 check_same_thread=False 以支持 FastAPI 线程池
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖:提供数据库会话,请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表(首次启动调用)。"""
    from app.models import question, user  # noqa: F401  确保模型注册

    Base.metadata.create_all(bind=engine)
