import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    get_settings,
    get_accounts_email_notificator,
)
from config.dependencies import get_dropbox_storage_client
from database.deps import get_db_contextmanager
from database.models import CertificationModel, GenreModel, StarModel, DirectorModel
from database.models.accounts import UserGroupEnum, UserGroupModel, UserModel
from database.models.shopping_cart import Cart
from database.populate import CSVDatabaseSeeder
from database.session_sqlite import reset_sqlite_database as reset_database
from main import app
from security.interfaces import JWTAuthManagerInterface
from security.token_manager import JWTAuthManager
from storages import DropboxStorageClient
from tests.doubles.fakes.storage import FakeDropboxStorage
from tests.doubles.stubs.emails import StubEmailSender


from unittest.mock import AsyncMock
from services.stripe_service import StripeService


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
async def dropbox_storage_fake():
    """
    Provide a fake S3 storage client.

    This fixture returns an instance of FakeDropboxStorage for testing purposes.
    """
    return FakeDropboxStorage()


@pytest_asyncio.fixture(scope="function")
async def dropbox_client(settings):
    """
    Provide an S3 storage client.

    This fixture returns an instance of S3StorageClient configured with the application settings.
    """
    return DropboxStorageClient(
        access_token=settings.DROPBOX_ACCESS_TOKEN,
        app_key=settings.DROPBOX_APP_KEY,
        app_secret=settings.DROPBOX_APP_SECRET,
        refresh_token=settings.DROPBOX_REFRESH_TOKEN
    )


@pytest_asyncio.fixture(scope="function")
async def client(email_sender_stub, dropbox_storage_fake):
    """
    Provide an asynchronous HTTP client for testing.


    Overrides the dependencies for email sender and S3 storage with test doubles.
    """
    app.dependency_overrides[get_accounts_email_notificator] = (
        lambda: email_sender_stub
    )
    app.dependency_overrides[get_dropbox_storage_client] = lambda: dropbox_storage_fake

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
async def test_user(db_session, seed_user_groups):
    """
    Create a test user for validation tests.
    
    This fixture creates a test user with the following properties:
    - email: test@mate.com
    - password: TestPassword123!
    - group_id: 1 (User group)
    - is_active: True
    
    The user is created before each test and cleaned up after.
    """
    user = UserModel.create(email="test@mate.com", raw_password="TestPassword123!", group_id=1)
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_client(
    client: AsyncClient,
    test_user: UserModel,
    jwt_manager: JWTAuthManagerInterface,
):
    """
    Provide an authenticated async HTTP client for testing with regular user privileges.
    """
    access_token = jwt_manager.create_access_token({"user_id": test_user.id})
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def test_moderator(db_session, seed_user_groups):
    """
    Create a test moderator for validation tests.

    This fixture creates a test moderator with the following properties:
    - email: moderator@mate.com
    - password: TestPassword123!
    - group_id: 2 (Moderator group)
    - is_active: True

    The moderator is created before each test and cleaned up after.
    """
    moderator = UserModel.create(email="moderator@mate.com", raw_password="TestPassword123!", group_id=2)
    moderator.is_active = True
    db_session.add(moderator)
    await db_session.commit()
    return moderator


@pytest_asyncio.fixture(scope="function")
async def auth_moderator_client(
    client: AsyncClient,
    test_moderator: UserModel,
    jwt_manager: JWTAuthManagerInterface,
):
    """
    Provide an authenticated async HTTP client for testing with moderator privileges.
    """
    access_token = jwt_manager.create_access_token({"user_id": test_moderator.id})
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


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
async def seed_movie_relations(db_session: AsyncSession):
    """
    Ensure that at least one genre, star, director, and certification exist in the database with id=1.
    """
    # Certification
    cert = await db_session.get(CertificationModel, 1)
    if not cert:
        cert = CertificationModel(id=1, name="PG-13")
        db_session.add(cert)
    # Genre
    genre = await db_session.get(GenreModel, 1)
    if not genre:
        genre = GenreModel(id=1, name="Action")
        db_session.add(genre)
    # Star
    star = await db_session.get(StarModel, 1)
    if not star:
        star = StarModel(id=1, name="Leonardo DiCaprio")
        db_session.add(star)
    # Director
    director = await db_session.get(DirectorModel, 1)
    if not director:
        director = DirectorModel(id=1, name="Christopher Nolan")
        db_session.add(director)
    await db_session.commit()
    yield


@pytest_asyncio.fixture(autouse=True)
def mock_stripe_service(monkeypatch):
    """
    Automatically patch StripeService methods for all tests using mocked behavior.
    """
    monkeypatch.setattr(
        StripeService,
        "create_payment_intent",
        AsyncMock(return_value={
            "payment_intent_id": "pi_test_123456",
            "payment_url": "https://mock.stripe.test/pay/pi_test_123456"
        }),
    )
    monkeypatch.setattr(
        StripeService,
        "handle_webhook",
        AsyncMock(return_value={
            "external_payment_id": "pi_test_123456",
            "status": "SUCCESSFUL"
        }),
    )
    monkeypatch.setattr(
        StripeService,
        "refund_payment",
        AsyncMock(return_value=True),
    )


# ⬇️ Авторизовані клієнти (користувач / адмін)
@pytest_asyncio.fixture(scope="function")
async def auth_user_token(test_user: UserModel, jwt_manager: JWTAuthManagerInterface):
    return jwt_manager.create_access_token({"user_id": test_user.id})


@pytest_asyncio.fixture(scope="function")
async def auth_admin_token(test_moderator: UserModel, jwt_manager: JWTAuthManagerInterface):
    return jwt_manager.create_access_token({"user_id": test_moderator.id})


@pytest_asyncio.fixture(scope="function")
async def auth_user_client(
    client: AsyncClient,
    auth_user_token: str,
):
    client.headers["Authorization"] = f"Bearer {auth_user_token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def auth_admin_client(
    client: AsyncClient,
    auth_admin_token: str,
):
    client.headers["Authorization"] = f"Bearer {auth_admin_token}"
    return client
