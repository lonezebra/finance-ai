from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from finance_ai.config import DATA_DIR, DB_PATH


class Base(DeclarativeBase):
    pass


def get_engine():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)


SessionLocal = sessionmaker(
    bind=get_engine(),
    autoflush=False,
    autocommit=False,
    future=True,
)