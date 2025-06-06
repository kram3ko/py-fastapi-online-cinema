import contextlib
import os
from collections.abc import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sqlite_db

        async for session in get_sqlite_db():
            yield session
    else:
        from database.session_postgresql import get_postgresql_db

        async for session in get_postgresql_db():
            yield session


def get_db_contextmanager() -> "contextlib.AbstractAsyncContextManager":
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sqlite_db_contextmanager

        return get_sqlite_db_contextmanager()
    else:
        from database.session_postgresql import get_postgresql_db_contextmanager

        return get_postgresql_db_contextmanager()


def get_sync_db() -> Generator["contextlib.AbstractContextManager", None, None]:
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sync_sqlite_db

        return get_sync_sqlite_db()
    else:
        from database.session_postgresql import get_sync_postgresql_db

        return get_sync_postgresql_db()


def get_sync_db_contextmanager() -> "contextlib.AbstractContextManager":
    environment = os.getenv("ENVIRONMENT", "developing")
    if environment == "testing":
        from database.session_sqlite import get_sync_sqlite_db_contextmanager

        return get_sync_sqlite_db_contextmanager()
    else:
        from database.session_postgresql import get_sync_postgresql_db_contextmanager

        return get_sync_postgresql_db_contextmanager()
