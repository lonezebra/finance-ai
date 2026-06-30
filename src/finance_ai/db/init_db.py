from finance_ai.db import models  # noqa: F401
from finance_ai.db.database import Base, get_engine


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database initialized.")


if __name__ == "__main__":
    init_db()