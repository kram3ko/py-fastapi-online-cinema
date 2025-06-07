import asyncio
import math
import os

import pandas as pd
from sqlalchemy import func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from config import get_settings
from database.deps import get_db_contextmanager
from database.models.accounts import UserGroupEnum, UserGroupModel
from database.models.movies import MovieModel, StarModel
from database.models.orders import OrderModel
from database.models.shopping_cart import Cart

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        result = await self._db_session.execute(select(UserGroupModel).limit(1))
        first_group = result.scalars().first()
        return first_group is not None

    def _preprocess_csv(self) -> pd.DataFrame:
        data = pd.read_csv(self._csv_file_path)
        data = data.drop_duplicates(subset=["names", "date_x"], keep="first")

        for col in ["star", "country", "orig_lang", "status"]:
            data[col] = data[col].fillna("Unknown").astype(str)

        data["star"] = (
            data["star"]
            .str.replace(r"\s+", "", regex=True)
            .apply(lambda x: ",".join(sorted(set(x.split(",")))) if x != "Unknown" else x)
        )

        data["date_x"] = data["date_x"].astype(str).str.strip()
        data["date_x"] = pd.to_datetime(data["date_x"], format="%Y-%m-%d", errors="raise")
        data["date_x"] = data["date_x"].dt.date
        data["orig_lang"] = data["orig_lang"].str.replace(r"\s+", "", regex=True)
        data["status"] = data["status"].str.strip()

        print("Preprocessing CSV file...")
        data.to_csv(self._csv_file_path, index=False)
        print(f"CSV file saved to {self._csv_file_path}")
        return data

    async def _seed_user_groups(self) -> None:
        """
        Seeds user groups from enums.
        """
        # Seed user groups
        user_groups = [{"name": group.value} for group in UserGroupEnum]
        if user_groups:
            await self._db_session.execute(insert(UserGroupModel).values(user_groups))
            await self._db_session.flush()
            print("User groups seeded successfully.")

    async def _get_or_create_bulk(self, model, items: list[str], unique_field: str) -> dict[str, object]:
        existing_dict: dict[str, object] = {}

        if items:
            for i in range(0, len(items), CHUNK_SIZE):
                chunk = items[i : i + CHUNK_SIZE]
                result = await self._db_session.execute(select(model).where(getattr(model, unique_field).in_(chunk)))
                existing_in_chunk = result.scalars().all()
                for obj in existing_in_chunk:
                    key = getattr(obj, unique_field)
                    existing_dict[key] = obj

        new_items = [item for item in items if item not in existing_dict]
        new_records = [{unique_field: item} for item in new_items]

        if new_records:
            for i in range(0, len(new_records), CHUNK_SIZE):
                chunk = new_records[i : i + CHUNK_SIZE]
                await self._db_session.execute(insert(model).values(chunk))
                await self._db_session.flush()

            for i in range(0, len(new_items), CHUNK_SIZE):
                chunk = new_items[i : i + CHUNK_SIZE]
                result_new = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk))
                )
                inserted_in_chunk = result_new.scalars().all()
                for obj in inserted_in_chunk:
                    key = getattr(obj, unique_field)
                    existing_dict[key] = obj

        return existing_dict

    async def _bulk_insert(self, table, data_list: list[dict[str, int]]) -> None:
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
        stars = {star.strip() for stars_ in data["star"].dropna() for star in stars_.split(",") if star.strip()}
        star_map = await self._get_or_create_bulk(StarModel, list(stars), "name")
        return star_map

    def _prepare_associations(
        self,
        data: pd.DataFrame,
        movie_ids: list[int],
        star_map: dict[str, object],
    ) -> list[dict[str, int]]:
        movie_stars_data: list[dict[str, int]] = []

        for i, (_, row) in enumerate(tqdm(data.iterrows(), total=data.shape[0], desc="Processing associations")):
            movie_id = movie_ids[i]
            for star_name in row["star"].split(","):
                star_name_clean = star_name.strip()
                if star_name_clean:
                    star = star_map[star_name_clean]
                    movie_stars_data.append({"movie_id": movie_id, "star_id": star.id})

        return movie_stars_data

    def _prepare_movies_data(self, data: pd.DataFrame) -> list[dict]:
        movies_data = []
        for _, row in data.iterrows():
            movies_data.append(
                {
                    "names": row["names"],
                    "date_x": row["date_x"],
                    "country": row["country"],
                    "orig_lang": row["orig_lang"],
                    "status": row["status"],
                }
            )
        return movies_data

    async def seed(self) -> None:
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            await self._seed_user_groups()
            await self._db_session.commit()
            print("Seeding completed.")

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
