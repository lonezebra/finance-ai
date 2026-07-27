from finance_ai.db.migrate import ensure_schema_up_to_date


def init_db():
    ensure_schema_up_to_date()
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
