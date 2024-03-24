import logging
import argparse

from typing import List, Optional
from datetime import datetime
from sqlalchemy import Table, Column, ForeignKey, create_engine, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import os
from dotenv import load_dotenv
load_dotenv()
POSTGRES_PW = os.getenv('POSTGRES_PW')

DATABASE_URL = "postgresql://postgres:{}@localhost/everything_test".format(POSTGRES_PW)
ENGINE = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


MOVIE_GENRE_RELATIONSHIP = Table(
    "movie_genre_relationship",
    Base.metadata,
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("genre_id", ForeignKey("genre.id"), primary_key=True),
)

MOVIE_RECOMMENDATION_RELATIONSHIP = Table(
    "movie_recommendation_relationship",
    Base.metadata,
    Column("movie_id", ForeignKey("movie.id"), primary_key=True),
    Column("recommendation_id", ForeignKey("recommendation.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    age: Mapped[int]
    occupation: Mapped[str]
    gender: Mapped[str]

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, age={self.age!r}, "
            f"occupation={self.occupation!r}, gender={self.gender!r})"
        )


class Movie(Base):
    __tablename__ = "movie"

    id: Mapped[str] = mapped_column(primary_key=True)
    tmdb_id: Mapped[str]
    imdb_id: Mapped[str]
    adult: Mapped[bool]
    original_language: Mapped[str]
    popularity: Mapped[float]
    runtime: Mapped[int]
    vote_average: Mapped[float]
    vote_count: Mapped[int]
    genres: Mapped[List["Genre"]] = relationship(secondary=MOVIE_GENRE_RELATIONSHIP)

    def __repr__(self) -> str:
        return (
            f"Movie(id={self.id!r}, tmdb_id={self.tmdb_id!r}, "
            f"imdb_id={self.imdb_id!r}, adult={self.adult!r}, "
            f"original_language={self.original_language!r}, "
            f"popularity={self.popularity!r}, runtime={self.runtime!r}, "
            f"vote_average={self.vote_average!r}, vote_count={self.vote_count!r}, "
            f"genres={self.genres!r})"
        )


class Genre(Base):
    __tablename__ = "genre"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    def __repr__(self) -> str:
        return f"Genre(id={self.id!r}, name={self.name!r})"


class UserMovieRating(Base):
    __tablename__ = "user_movie_rating"
    __table_args__ = (
        UniqueConstraint(
            "timestamp", "user_id", "movie_id", name="_timestamp_user_movie_rating_uc"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    movie_id: Mapped[str] = mapped_column(ForeignKey("movie.id"))
    rating: Mapped[int]

    def __repr__(self) -> str:
        return (
            f"UserMovieRating(id={self.id!r}, timestamp={self.timestamp!r}, "
            f"user_id={self.user_id!r}, movie_id={self.movie_id!r}, "
            f"rating={self.rating!r})"
        )


class UserMovieWatchDuration(Base):
    __tablename__ = "user_movie_watch_duration"
    __table_args__ = (
        UniqueConstraint(
            "timestamp", "user_id", "movie_id", name="_timestamp_user_movie_watch_uc"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    movie_id: Mapped[str] = mapped_column(ForeignKey("movie.id"))
    duration: Mapped[int]

    def __repr__(self) -> str:
        return (
            f"UserMovieWatchDuration(id={self.id!r}, timestamp={self.timestamp!r}, "
            f"user_id={self.user_id!r}, movie_id={self.movie_id!r}, "
            f"duration={self.duration!r})"
        )


class Recommendation(Base):
    __tablename__ = "recommendation"
    __table_args__ = (
        UniqueConstraint(
            "timestamp", "user_id", name="_timestamp_user_recommendation_uc"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    latency_ms: Mapped[int]
    response_code: Mapped[int]
    results: Mapped[List[Movie]] = relationship(
        secondary=MOVIE_RECOMMENDATION_RELATIONSHIP
    )

    def __repr__(self) -> str:
        return (
            f"Recommendation(id={self.id!r}, timestamp={self.timestamp!r}, "
            f"user_id={self.user_id!r}, latency_ms={self.latency_ms!r}, "
            f"response_code={self.response_code!r}, results={self.results!r})"
        )


def init_db(verbose: bool):
    if verbose:
        prev_level = logging.getLogger("sqlalchemy.engine.Engine").getEffectiveLevel()
        logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.INFO)
    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)
    if verbose:
        logging.getLogger("sqlalchemy.engine.Engine").setLevel(prev_level)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", default=False)
    if parser.parse_args().init:
        init_db(verbose=True)
    else:
        logging.warning(f"Will delete and re-init the entire DB in {DATABASE_URL}!")
        logging.warning(f"Call with --init argument to confirm")
