import os

async def get_db():
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sqlite_db
        async for session in get_sqlite_db():
            yield session
    else:
        from database.session_postgresql import get_postgresql_db
        async for session in get_postgresql_db():
            yield session


def get_db_contextmanager():
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sqlite_db_contextmanager
        return get_sqlite_db_contextmanager()
    else:
        from database.session_postgresql import get_postgresql_db_contextmanager
        return get_postgresql_db_contextmanager()


def get_sync_db():
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sync_sqlite_db
        return get_sync_sqlite_db()
    else:
        from database.session_postgresql import get_sync_postgresql_db
        return get_sync_postgresql_db()


def get_sync_db_contextmanager():
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sync_sqlite_db_contextmanager
        return get_sync_sqlite_db_contextmanager()
    else:
        from database.session_postgresql import get_sync_postgresql_db_contextmanager
        return get_sync_postgresql_db_contextmanager()
