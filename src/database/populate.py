import asyncio
import math
import uuid

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from config import get_settings
from database.deps import get_db_contextmanager
from database.models.accounts import UserGroupEnum, UserGroupModel
from database.models.movies import CertificationModel, DirectorModel, GenreModel, MovieModel, StarModel

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        result = await self._db_session.execute(select(UserGroupModel).limit(1))
        first_group = result.scalars().first()
        return first_group is not None

    async def _seed_movies_from_csv(self) -> None:
        """
        Seeds movies from CSV file.
        """
        data = pd.read_csv(self._csv_file_path)

        # Create stars
        all_stars: set[str] = set()
        for stars_str in data["star"].dropna():
            all_stars.update(star.strip() for star in stars_str.split(","))
        stars = {star: StarModel(name=star) for star in all_stars}
        for star in stars.values():
            self._db_session.add(star)
        await self._db_session.flush()

        # Create certifications
        certifications = {cert: CertificationModel(name=cert) for cert in data["certification"].unique()}
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
                stars=[stars[star.strip()] for star in row["star"].split(",")] if pd.notna(row["star"]) else []
            )
            self._db_session.add(movie)

        await self._db_session.flush()
        print("Movies seeded successfully.")

    def _preprocess_csv(self) -> pd.DataFrame:
        data = pd.read_csv(self._csv_file_path)

        # Ensure all required columns are present
        required_columns = ["name", "year", "time", "imdb", "votes", "meta_score",
                          "gross", "descriptions", "price", "certification",
                          "genres", "directors", "star"]

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
        data["star"] = data["star"].astype(str)

        # Clean up genres, directors and stars
        data["genres"] = data["genres"].apply(lambda x: ",".join(sorted(set(g.strip() for g in x.split(",")))))
        data["directors"] = data["directors"].apply(lambda x: ",".join(sorted(set(d.strip() for d in x.split(",")))))
        data["star"] = data["star"].apply(lambda x: ",".join(sorted(set(s.strip() for s in x.split(",")))))

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
                chunk_str: list[str] = items[i : i + CHUNK_SIZE]
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
                chunk_dict: list[dict[str, str]] = new_records[i : i + CHUNK_SIZE]
                await self._db_session.execute(insert(model).values(chunk_dict))
                await self._db_session.flush()

            for i in range(0, len(new_items), CHUNK_SIZE):
                chunk_str_new: list[str] = new_items[i : i + CHUNK_SIZE]
                result_new = await self._db_session.execute(
                    select(model).where(getattr(model, unique_field).in_(chunk_str_new))
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
        star_map: dict[str, StarModel],
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

    def _prepare_movies_data(self, data: pd.DataFrame) -> list[dict[str, int | str]]:
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

    async def seed(self) -> None:
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            await self._seed_user_groups()
            await self._seed_movies_from_csv()
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
