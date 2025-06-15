import asyncio
import math
import uuid
from decimal import Decimal

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from config import get_settings
from database.deps import get_db_contextmanager
from database.models.accounts import UserGroupEnum, UserGroupModel, UserModel
from database.models.movies import CertificationModel, DirectorModel, GenreModel, MovieModel, StarModel
from database.models.orders import OrderModel, OrderItemModel, OrderStatus
from database.models.shopping_cart import Cart, CartItem

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        result = await self._db_session.execute(select(MovieModel).limit(1))
        first_movie = result.scalars().first()
        return first_movie is not None

    async def _seed_movies_from_csv(self) -> None:
        """
        Seeds movies from CSV file.
        """
        data = pd.read_csv(self._csv_file_path)

        # Create stars
        all_stars: set[str] = set()
        for stars_str in data["stars"].dropna():
            all_stars.update(star.strip() for star in stars_str.split(","))
        stars = {star: StarModel(name=star) for star in all_stars}
        for star in stars.values():
            self._db_session.add(star)
        await self._db_session.flush()

        # Create certifications
        certifications = {cert: CertificationModel(name=cert) for cert in data["certification"].dropna().unique()}
        for cert in certifications.values():
            self._db_session.add(cert)
        await self._db_session.flush()

        # Create genres
        all_genres: set[str] = set()
        for genres_str in data["genres"]:
            all_genres.update(genre.strip() for genre in genres_str.split(","))
        genres = {genre: GenreModel(name=genre) for genre in all_genres}
        for genre in genres.values():
            self._db_session.add(genre)
        await self._db_session.flush()

        # Create directors
        all_directors: set[str] = set()
        for directors_str in data["directors"]:
            all_directors.update(director.strip() for director in directors_str.split(","))
        directors = {director: DirectorModel(name=director) for director in all_directors}
        for director in directors.values():
            self._db_session.add(director)
        await self._db_session.flush()

        # Create movies
        for _, row in data.iterrows():
            movie = MovieModel(
                uuid_movie=uuid.uuid4(),
                name=row["name"],
                year=row["year"],
                time=row["time"],
                imdb=row["imdb"],
                votes=row["votes"],
                meta_score=row["meta_score"],
                gross=row["gross"],
                descriptions=row["descriptions"],
                price=row["price"],
                certification_id=certifications[row["certification"]].id,
                genres=[genres[genre.strip()] for genre in row["genres"].split(",")],
                directors=[directors[director.strip()] for director in row["directors"].split(",")],
                stars=[stars[star.strip()] for star in row["stars"].split(",")] if pd.notna(row["stars"]) else [],
            )
            self._db_session.add(movie)

        await self._db_session.flush()
        print("Movies seeded successfully.")

    def _preprocess_csv(self) -> pd.DataFrame:
        """
        Preprocesses CSV data to ensure correct data types and formats.
        """
        data = pd.read_csv(self._csv_file_path)

        # Ensure all required columns are present
        required_columns = [
            "name",
            "year",
            "time",
            "imdb",
            "votes",
            "meta_score",
            "gross",
            "descriptions",
            "price",
            "certification",
            "genres",
            "directors",
            "stars",
        ]

        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Required column '{col}' is missing in the CSV file")

        # Clean up data
        data["name"] = data["name"].astype(str)
        data["year"] = data["year"].astype(int)
        data["time"] = data["time"].astype(int)
        data["imdb"] = data["imdb"].astype(float)
        data["votes"] = data["votes"].astype(int)
        data["meta_score"] = data["meta_score"].astype(float)
        data["gross"] = data["gross"].astype(float)
        data["descriptions"] = data["descriptions"].astype(str)
        data["price"] = data["price"].astype(float)
        data["certification"] = data["certification"].astype(str)
        data["genres"] = data["genres"].astype(str)
        data["directors"] = data["directors"].astype(str)
        data["stars"] = data["stars"].astype(str)

        # Clean up genres, directors and stars
        data["genres"] = data["genres"].apply(lambda x: ",".join(sorted(set(g.strip() for g in x.split(",")))))
        data["directors"] = data["directors"].apply(lambda x: ",".join(sorted(set(d.strip() for d in x.split(",")))))
        data["stars"] = data["stars"].apply(lambda x: ",".join(sorted(set(s.strip() for s in x.split(",")))))

        print("Preprocessing CSV file...")
        data.to_csv(self._csv_file_path, index=False)
        print(f"CSV file saved to {self._csv_file_path}")
        return data

    async def _get_or_create_bulk(self, model, items: list[str], unique_field: str) -> dict[str, object]:
        """
        Gets or creates multiple records in bulk.
        """
        existing_dict: dict[str, object] = {}

        if items:
            for i in range(0, len(items), CHUNK_SIZE):
                chunk_str: list[str] = items[i: i + CHUNK_SIZE]
                result = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk_str))
                )
                existing_in_chunk = result.scalars().all()
                for obj in existing_in_chunk:
                    key = getattr(obj, unique_field)
                    existing_dict[key] = obj

        new_items: list[str] = [item for item in items if item not in existing_dict]
        new_records: list[dict[str, str]] = [{unique_field: item} for item in new_items]

        if new_records:
            for i in range(0, len(new_records), CHUNK_SIZE):
                chunk_dict: list[dict[str, str]] = new_records[i: i + CHUNK_SIZE]
                await self._db_session.execute(insert(model).values(chunk_dict))
                await self._db_session.flush()

            for i in range(0, len(new_items), CHUNK_SIZE):
                chunk_str_new: list[str] = new_items[i: i + CHUNK_SIZE]
                result_new = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk_str_new))
                )
                inserted_in_chunk = result_new.scalars().all()
                for obj in inserted_in_chunk:
                    key = getattr(obj, unique_field)
                    existing_dict[key] = obj

        return existing_dict

    async def _bulk_insert(self, table, data_list: list[dict[str, int]]) -> None:
        """
        Inserts multiple records in bulk.
        """
        total_records = len(data_list)
        if total_records == 0:
            return

        num_chunks = math.ceil(total_records / CHUNK_SIZE)
        table_name = getattr(table, "__tablename__", str(table))

        for chunk_index in tqdm(range(num_chunks), desc=f"Inserting into {table_name}"):
            start = chunk_index * CHUNK_SIZE
            end = start + CHUNK_SIZE
            chunk = data_list[start:end]
            if chunk:
                await self._db_session.execute(insert(table).values(chunk))

        await self._db_session.flush()

    async def _prepare_reference_data(self, data: pd.DataFrame) -> dict[str, object]:
        """
        Prepares reference data for bulk operations.
        """
        stars = {star.strip() for stars_ in data["stars"].dropna() for star in stars_.split(",") if star.strip()}
        star_map = await self._get_or_create_bulk(StarModel, list(stars), "name")
        return star_map

    def _prepare_associations(
        self,
        data: pd.DataFrame,
        movie_ids: list[int],
        star_map: dict[str, StarModel],
    ) -> list[dict[str, int]]:
        """
        Prepares association data for bulk operations.
        """
        movie_stars_data: list[dict[str, int]] = []

        for i, (_, row) in enumerate(tqdm(data.iterrows(), total=data.shape[0], desc="Processing associations")):
            movie_id = movie_ids[i]
            for star_name in row["stars"].split(","):
                star_name_clean = star_name.strip()
                if star_name_clean:
                    star = star_map[star_name_clean]
                    movie_stars_data.append({"movie_id": movie_id, "star_id": star.id})

        return movie_stars_data

    def _prepare_movies_data(self, data: pd.DataFrame) -> list[dict[str, int | str]]:
        """
        Prepares movie data for bulk operations.
        """
        movies_data: list[dict[str, int | str]] = []
        for _, row in data.iterrows():
            movies_data.append(
                {
                    "names": str(row["names"]),
                    "date_x": str(row["date_x"]),
                    "country": str(row["country"]),
                    "orig_lang": str(row["orig_lang"]),
                    "status": str(row["status"]),
                }
            )
        return movies_data

    async def _seed_orders_from_csv(self) -> None:
        """
        Seeds orders from CSV file.
        """
        data = pd.read_csv("database/seed_data/orders.csv")

        # Get all existing movie IDs
        result = await self._db_session.execute(select(MovieModel.id))
        existing_movie_ids = {row[0] for row in result.all()}

        for _, row in data.iterrows():
            movie_id = int(row["movie_id"])
            # Skip if movie doesn't exist
            if movie_id not in existing_movie_ids:
                continue

            # Create order
            order = OrderModel(
                user_id=int(row["user_id"]),
                status=OrderStatus[row["status"].upper()],
                total_amount=Decimal(str(row["price_at_order"]))
            )
            self._db_session.add(order)
            await self._db_session.flush()  # To get order.id

            # Create order item
            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=movie_id,
                price_at_order=Decimal(str(row["price_at_order"]))
            )
            self._db_session.add(order_item)

        await self._db_session.commit()
        print("Orders seeded successfully.")

    async def _seed_carts_from_csv(self) -> None:
        """
        Seeds shopping carts from CSV file.
        """
        # Create carts for users
        for user_id in range(1, 6):  # For users 1 through 5
            cart = Cart(user_id=user_id)
            self._db_session.add(cart)
        await self._db_session.commit()
        print("Carts created successfully.")

        # Read cart data from CSV
        data = pd.read_csv("database/seed_data/carts.csv")

        # Get all existing movie IDs
        result = await self._db_session.execute(select(MovieModel.id))
        existing_movie_ids = {row[0] for row in result.all()}

        for _, row in data.iterrows():
            movie_id = int(row["movie_id"])
            # Skip if movie doesn't exist
            if movie_id not in existing_movie_ids:
                continue

            # Add movie to user's cart
            result = await self._db_session.execute(
                select(Cart).where(Cart.user_id == int(row["user_id"]))
            )
            cart = result.scalar_one_or_none()
            if cart:
                cart_item = CartItem(cart_id=cart.id, movie_id=movie_id)
                self._db_session.add(cart_item)

        await self._db_session.commit()
        print("Cart items added successfully.")

    async def _seed_user_groups(self) -> None:
        """
        Seeds user groups from enums.
        """
        # Get group names from enum
        group_names = [group.value for group in UserGroupEnum]

        # Use _get_or_create_bulk to handle existing groups
        await self._get_or_create_bulk(UserGroupModel, group_names, "name")
        await self._db_session.flush()
        print("User groups seeded successfully.")

    async def _seed_test_users(self) -> None:
        """
        Seeds test users.
        """
        # Create test users
        test_users = [
            {
                "email": f"user{i}@example.com",
                "password": "Password123!",
                "is_active": True,
                "group_id": 1
            }
            for i in range(1, 6)
        ]

        for user_data in test_users:
            user = UserModel.create(
                email=user_data["email"],
                raw_password=user_data["password"],
                group_id=user_data["group_id"]
            )
            user.is_active = user_data["is_active"]
            self._db_session.add(user)

        await self._db_session.commit()
        print("Test users created successfully.")

    async def seed(self) -> None:
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            print("\nStarting database seeding...")
            await self._seed_user_groups()
            await self._seed_test_users()
            await self._seed_movies_from_csv()
            await self._seed_carts_from_csv()
            await self._seed_orders_from_csv()
            await self._db_session.commit()

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


async def main() -> None:
    settings = get_settings()
    async with get_db_contextmanager() as db_session:
        seeder = CSVDatabaseSeeder(settings.PATH_TO_MOVIES_CSV, db_session)
        if not await seeder.is_db_populated():
            try:
                await seeder.seed()
                print("Database seeding completed successfully.")
            except Exception as e:
                print(f"Failed to seed the database: {e}")
        else:
            print("Database is already populated. Skipping seeding.")


if __name__ == "__main__":
    asyncio.run(main())
