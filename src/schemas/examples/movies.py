movie_item_schema_example = {
    "id": 1,
    "uuid_movie": "38e6c48d-8a93-4e1e-9df5-4316cbf3f9a1",
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2000000,
    "mate_score": 74.0,
    "gross": 829.89,
    "descriptions": "A thief who steals corporate secrets through the use of dream-sharing technology...",
    "price": 12.99,
    "certification": {
        "id": 2,
        "name": "PG-13",
    },
    "genres": [
        {"id": 1, "name": "Action"},
        {"id": 2, "name": "Sci-Fi"},
    ],
    "stars": [
        {"id": 1, "name": "Leonardo DiCaprio"},
        {"id": 2, "name": "Joseph Gordon-Levitt"}
    ],
    "directors": [
        {"id": 1, "name": "Christopher Nolan"},
    ]
}

movie_list_response_schema_example = {
    "movies": [
        movie_item_schema_example
    ],
    "prev_page": "/movies/?page=1&per_page=10",
    "next_page": "/movies/?page=3&per_page=10",
    "total_pages": 99,
    "total_items": 990
}

movie_create_schema_example = {
    "name": "New Movie",
    "year": 2025,
    "time": 120,
    "imdb": 7.9,
    "votes": 1000,
    "meta_score": 80.5,
    "gross": 1000000.00,
    "descriptions": "A band-new sci-fi movie about AI in the future.",
    "price": 12.99,
    "certification_id": 1,
    "genres_id": [1, 2],
    "stars_id": [1, 2],
    "directors_id": [3]
}


director_schema_example = {
    "id": 1,
    "name": "Christopher Nolan"
}

certification_schema_example = {
    "id": 1,
    "name": "PG-13"
}

genre_schema_example = {
    "id": 1,
    "genre": "Comedy"
}

star_schema_example = {
    "id": 1,
    "name": "Leonardo DiCaprio",
}

movie_detail_schema_example = {
    **movie_item_schema_example,
    "genres": [genre_schema_example],
    "stars": [star_schema_example],
    "directors": [director_schema_example]
}

movie_update_schema_example = {
    "name": "Update Movie Title",
    "year": 2024,
    "time": 135,
    "imdb": 8.2,
    "votes": 500000,
    "meta_score": 77.0,
    "gross": 4500000.00,
    "descriptions": "Updated description of the movie.",
    "price": 11.99,
    "certification_id": 2,
    "genres_id": [1, 4],
    "stars_id": [1],
    "directors_id": [1]
}
