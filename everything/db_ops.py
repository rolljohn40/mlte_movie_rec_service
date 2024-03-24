import pandas as pd
import everything.db

from typing import List
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, select, insert
from sqlalchemy.orm import Session, joinedload
from everything.db import (
    User,
    Movie,
    Genre,
    UserMovieRating,
    UserMovieWatchDuration,
    Recommendation,
)


def check_user_exists_in_db(user_id):
    # Create session
    session = Session(everything.db.ENGINE)
    try:
        # Query the User table to check if the user exists
        user = session.query(User).filter(User.id == user_id).first()
        # Check if the user exists
        user_exists = user is not None
    finally:
        session.close()
    return user_exists


def add_new_user_in_db(user_id, age, occupation, gender):
    with Session(everything.db.ENGINE) as session:

        new_user = User(id=user_id, age=age, occupation=occupation, gender=gender)

        session.add(new_user)
        session.commit()
    return new_user


def check_genre_exists_in_db(genre_name):
    session = Session(everything.db.ENGINE)
    try:
        genre = session.query(Genre).filter(Genre.name == genre_name).first()

        genre_exists = genre is not None
    finally:
        session.close()
    return genre_exists


def check_movie_exists_in_db(movie_id):
    session = Session(everything.db.ENGINE)
    try:
        movie = session.query(Movie).filter(Movie.id == movie_id).first()

        movie_exists = movie is not None
    finally:
        session.close()

    return movie_exists


def add_new_movie_in_db(
    movie_id,
    tmdb_id,
    imdb_id,
    adult,
    original_language,
    popularity,
    runtime,
    vote_average,
    vote_count,
    genres,
):
    with Session(everything.db.ENGINE) as session:
        genre_list = []
        for genre in genres:
            if not check_genre_exists_in_db(genre):

                new_genre = Genre(name=genre)
                session.add(new_genre)
                session.commit()
                genre_list.append(new_genre)
            else:

                genre_list.append(
                    session.query(Genre).filter(Genre.name == genre).first()
                )

        new_movie = Movie(
            id=movie_id,
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            adult=adult,
            original_language=original_language,
            popularity=popularity,
            runtime=runtime,
            vote_average=vote_average,
            vote_count=vote_count,
            genres=genre_list,
        )

        session.add(new_movie)
        session.commit()
        return new_movie


def add_rating_in_db(timestamp, user_id, movie_id, rating):

    with Session(everything.db.ENGINE) as session:

        new_rating = UserMovieRating(
            timestamp=timestamp,
            user_id=user_id,
            movie_id=movie_id,
            rating=rating,
        )
        session.add(new_rating)
        session.commit()


def add_user_movie_watch_duration(timestamp, user_id, movie_id, duration):
    with Session(everything.db.ENGINE) as session:

        new_watch_duration = UserMovieWatchDuration(
            timestamp=timestamp, user_id=user_id, movie_id=movie_id, duration=duration
        )
        session.add(new_watch_duration)
        session.commit()


def add_recommendation_result(
    timestamp, user_id, latency_ms, response_code, results: List[str]
):
    with Session(everything.db.ENGINE) as session:

        # get movie objects
        movie_results = session.query(Movie).filter(Movie.id.in_(results)).all()

        new_rec_res = Recommendation(
            timestamp=timestamp,
            user_id=user_id,
            latency_ms=latency_ms,
            response_code=response_code,
            results=movie_results,
        )

        session.add(new_rec_res)
        session.commit()


def get_movie_id_to_index_map():
    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=everything.db.ENGINE)

    # Get the movies table
    movies_table = metadata.tables["movie"]

    # Create a SQLAlchemy select query to fetch movie_id and movie_index
    query = select(movies_table.c.id)

    # Execute the query
    with everything.db.ENGINE.connect() as connection:
        result = connection.execute(query).all()

        # Create a dictionary mapping movie_id to movie_index
        movie_id_to_index_map = {row[0]: index for index, row in enumerate(result)}

    return movie_id_to_index_map


def get_unique_user_ids():
    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=everything.db.ENGINE)

    # Get the users table
    users_table = metadata.tables["user"]

    # Create a SQLAlchemy select query to fetch unique user IDs
    query = select(users_table.c.id).distinct()

    # Execute the query
    with everything.db.ENGINE.connect() as connection:
        result = connection.execute(query).all()

        # Extract unique user IDs
        unique_user_ids = [row[0] for row in result]

    return unique_user_ids


def get_userid_userindex_map():
    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=everything.db.ENGINE)

    # Get the users table
    users_table = metadata.tables["user"]

    # Create a SQLAlchemy select query to fetch unique user IDs
    query = select(users_table.c.id)

    # Execute the query
    with everything.db.ENGINE.connect() as connection:
        result = connection.execute(query).all()

        # Create a dictionary mapping user IDs to indices
        user_id_index_map = {row[0]: index for index, row in enumerate(result)}

    return user_id_index_map


def populate_dok_matrix(
    dok_matrix, userid_userindex_dict, movieid_movieindex_dict, max_timestamp
):
    max_timestamp = datetime.fromisoformat(max_timestamp)

    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=everything.db.ENGINE)

    # Get the ratings table
    ratings_table = metadata.tables["user_movie_rating"]

    # Create a SQLAlchemy select query to fetch user_id, movie_id, rating, and timestamp
    query = select(
        ratings_table.c.user_id,
        ratings_table.c.movie_id,
        ratings_table.c.rating,
        ratings_table.c.timestamp,
    ).where(ratings_table.c.timestamp < max_timestamp)

    # Execute the query
    with everything.db.ENGINE.connect() as connection:
        result = connection.execute(query).all()

        # Populate the DOK matrix with the fetched data
        for row in result:
            user_id = row[0]
            movie_id = row[1]
            rating = row[2]
            if user_id in userid_userindex_dict and movie_id in movieid_movieindex_dict:
                user_index = userid_userindex_dict[user_id]
                movie_index = movieid_movieindex_dict[movie_id]
                dok_matrix[user_index, movie_index] = rating

    return dok_matrix


def get_top_1000_popular_movies():
    # Reflect the existing database schema
    metadata = MetaData()
    metadata.reflect(bind=everything.db.ENGINE)

    # Get the movies table
    movies_table = metadata.tables["movie"]

    # Create a SQLAlchemy select query to fetch movie_id and popularity
    query = (
        select(movies_table.c.id, movies_table.c.popularity)
        .order_by(movies_table.c.popularity.desc())
        .limit(1000)
    )

    # Execute the query
    with everything.db.ENGINE.connect() as connection:
        result = connection.execute(query)

        # Convert the result into a Pandas DataFrame
        df = pd.DataFrame(result, columns=["id", "popularity"])

    return df


def get_ratings_before_or_after_date(before: bool, date: str, num_ratings: int):

    with Session(everything.db.ENGINE) as session:
        if before:
            rating_results = (
                session.query(UserMovieRating)
                .filter(UserMovieRating.timestamp < date)
                .order_by(UserMovieRating.timestamp.desc())
                .limit(num_ratings)
                .all()
            )
        else:
            rating_results = (
                session.query(UserMovieRating)
                .filter(UserMovieRating.timestamp > date)
                .order_by(UserMovieRating.timestamp)
                .limit(num_ratings)
                .all()
            )

    return rating_results

def get_ratings_before_or_after_date_with_user_info(before: bool, date: str, num_ratings: int):

    with Session(everything.db.ENGINE) as session:


        if before:
            stmt = (select(UserMovieRating,User)
                    .join(User, User.id == UserMovieRating.user_id)
                    .where(UserMovieRating.timestamp < date).limit(num_ratings))
            rating_results = session.execute(stmt).all()
        else:
            stmt = (select(UserMovieRating, User)
                    .join(User, User.id == UserMovieRating.user_id)
                    .where(UserMovieRating.timestamp > date).limit(num_ratings))
            rating_results = session.execute(stmt).all()
    return rating_results