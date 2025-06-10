import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    get_settings,
    get_accounts_email_notificator,
    get_s3_storage_client,
)
from database.deps import get_db_contextmanager
from database.models.accounts import UserGroupEnum, UserGroupModel, UserModel
from database.models.movies import MovieModel, CertificationModel
from database.populate import CSVDatabaseSeeder
from database.session_sqlite import reset_sqlite_database as reset_database
from main import app
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from storages import S3StorageClient
from tests.doubles.fakes.storage import FakeS3Storage
from tests.doubles.stubs.emails import StubEmailSender
from database.models.shopping_cart import Cart, CartItem


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "order: Specify the order of test execution"
    )
    config.addinivalue_line("markers", "unit: Unit tests")


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_db(request):
    """
    Reset the SQLite database before each test function, except for tests marked with 'e2e'.

    By default, this fixture ensures that the database is cleared and recreated before every
    test function to maintain test isolation. However, if the test is marked with 'e2e',
    the database reset is skipped to allow preserving state between end-to-end tests.
    """
    await reset_database()
    yield


@pytest_asyncio.fixture(scope="function")
async def settings():
    """
    Provide application settings.

    This fixture returns the application settings by calling get_settings().
    """
    return get_settings()


@pytest_asyncio.fixture(scope="function")
async def email_sender_stub():
    """
    Provide a stub implementation of the email sender.

    This fixture returns an instance of StubEmailSender for testing purposes.
    """
    return StubEmailSender()


@pytest_asyncio.fixture(scope="function")
async def s3_storage_fake():
    """
    Provide a fake S3 storage client.

    This fixture returns an instance of FakeS3Storage for testing purposes.
    """
    return FakeS3Storage()


@pytest_asyncio.fixture(scope="function")
async def s3_client(settings):
    """
    Provide an S3 storage client.

    This fixture returns an instance of S3StorageClient configured with the application settings.
    """
    return S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )


@pytest_asyncio.fixture(scope="function")
async def client(email_sender_stub, s3_storage_fake):
    """
    Provide an asynchronous HTTP client for testing.

    Overrides the dependencies for email sender and S3 storage with test doubles.
    """
    app.dependency_overrides[get_accounts_email_notificator] = (
        lambda: email_sender_stub
    )
    app.dependency_overrides[get_s3_storage_client] = lambda: s3_storage_fake

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Provide an async database session for database interactions.

    This fixture yields an async session using `get_db_contextmanager`, ensuring that the session
    is properly closed after each test.
    """
    async with get_db_contextmanager() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def jwt_manager() -> JWTAuthManagerInterface:
    """
    Asynchronous fixture to create a JWT authentication manager instance.

    This fixture retrieves the application settings via `get_settings()` and uses them to
    instantiate a `JWTAuthManager`. The manager is configured with the secret keys for
    access and refresh tokens, as well as the JWT signing algorithm specified in the settings.

    Returns:
        JWTAuthManagerInterface: An instance of JWTAuthManager configured with the appropriate
        secret keys and algorithm.
    """
    settings = get_settings()
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


@pytest_asyncio.fixture(scope="function")
async def seed_user_groups(db_session: AsyncSession):
    """
    Asynchronously seed the UserGroupModel table with default user groups.

    This fixture inserts all user groups defined in UserGroupEnum into the database and commits the transaction.
    It then yields the asynchronous database session for further testing.
    """
    groups = [{"name": group.value} for group in UserGroupEnum]
    await db_session.execute(insert(UserGroupModel).values(groups))
    await db_session.commit()
    yield db_session


@pytest_asyncio.fixture(scope="function")
async def seed_database(db_session):
    """
    Seed the database with test data if it is empty.

    This fixture initializes a `CSVDatabaseSeeder` and ensures the test database is populated before
    running tests that require existing data.

    :param db_session: The async database session fixture.
    :type db_session: AsyncSession
    """
    settings = get_settings()
    seeder = CSVDatabaseSeeder(
        csv_file_path=settings.PATH_TO_MOVIES_CSV, db_session=db_session
    )

    if not await seeder.is_db_populated():
        await seeder.seed()

    yield db_session


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create a test user for shopping cart tests."""
    from database.models.accounts import UserModel, UserGroupEnum
    from database.models import UserGroupModel

    group = UserGroupModel(name=UserGroupEnum.USER)
    db_session.add(group)
    await db_session.flush()

    user = UserModel(
        email="test@example.com", is_active=True, group_id=group.id
    )
    user.password = "TestPassword17%"
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_movie(db_session: AsyncSession):
    """Create a test movie for shopping cart tests."""
    from database.models.movies import MovieModel, CertificationModel

    certification = CertificationModel(name="PG-13")
    db_session.add(certification)
    await db_session.flush()

    movie = MovieModel(
        name="Test Movie",
        descriptions="Test Description",
        price=10.0,
        year=2024,
        time=120,
        certification_id=certification.id,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


@pytest_asyncio.fixture(scope="function")
async def test_cart(db_session: AsyncSession, test_user: UserModel):
    """Create a test cart for the test user."""
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest_asyncio.fixture(scope="function")
async def auth_client(
    client: AsyncClient,
    test_user: UserModel,
    jwt_manager: JWTAuthManagerInterface,
):
    """
    Provide an authenticated async HTTP client for testing.
    """
    access_token = jwt_manager.create_access_token({"user_id": test_user.id})
    client.headers["Authorization"] = f"Bearer {access_token}"

    return client
