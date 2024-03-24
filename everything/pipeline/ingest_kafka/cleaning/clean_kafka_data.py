from typing import List
from datetime import datetime
from everything.pipeline.ingest_kafka.cleaning.call_api.get_movie_data import (
    get_movie_details,
)
from everything.pipeline.ingest_kafka.cleaning.call_api.get_user_data import (
    get_user_data,
)
from everything.db_ops import *


def check_user_exists(userid: int):
    # see if user within db
    try:
        exists = check_user_exists_in_db(user_id=userid)
    except:
        exists = False
    return exists


def check_movie_exists(movieid: str):
    # see if movie within current movie map
    try:
        exists = check_movie_exists_in_db(movie_id=movieid)
    except:
        exists = False
    return exists


def add_user(userid: str):
    # call api for user info, returns json {'userid','age','occupation','gender'}
    user_data = get_user_data(user_id=userid)
    # create user in db if user_data present
    if user_data is not None:
        if not check_user_exists_in_db(user_id=user_data["user_id"]):
            add_new_user_in_db(
                user_id=user_data["user_id"],
                age=user_data["age"],
                occupation=user_data["occupation"],
                gender=user_data["gender"],
            )
        return True
    return False


def add_movie(movieid: str):
    success = False
    # call api for movieinfo
    # print('got top')
    movie_data = get_movie_details(movie_id=movieid)

    # create movie in db if movie data present
    if movie_data:
        try:
            genre_list = [genre for genre in movie_data["genres"]]

            new_movieid = add_new_movie_in_db(
                movie_id=movie_data["id"],
                tmdb_id=movie_data["tmdb_id"],
                imdb_id=movie_data["imdb_id"],
                adult=bool(movie_data["adult"]),
                original_language=movie_data["original_language"],
                popularity=float(movie_data["popularity"]),
                runtime=int(movie_data["runtime"]),
                vote_average=float(movie_data["vote_average"]),
                vote_count=int(movie_data["vote_count"]),
                genres=genre_list,
            )
            # check if success
            if new_movieid:
                # add the genres to the movie in the movie genres table
                success = True
            return success
        except Exception:
            # db add didn't work
            success = False
            return success

    return False


def check_rating_format(request_split: List[str]):
    good_format = True
    if len(request_split) != 3:
        good_format = False
    return good_format


def clean_kafka_rating(request_split: List[str]):
    # print('rec rating request')
    # check format of request_split
    if not check_rating_format(request_split=request_split):
        return "error: kafka rating data format"
    try:
        # check timestamp type
        timestamp = datetime.fromisoformat(request_split[0])

        # check user type
        userid = int(request_split[1])

        # create user if not present
        if not check_user_exists(userid=userid):
            if not add_user(userid=userid):
                return f"error: user {userid} not added"

        # index of beginning of movie id
        movieid_start_index = request_split[2].index("/rate/") + len("/rate/")
        # split remainder of reqeust split into movieid/ movie rating
        split_movie_rate = request_split[2][movieid_start_index:].split("=")

        movie_id = split_movie_rate[0]

        # create movie if not present
        if not check_movie_exists(movieid=movie_id):
            add_movie(movieid=movie_id)

        # change rating to int
        movie_rate = int(split_movie_rate[1])
    except:
        return "error: kafka rating data format"

    # add user movie rating to db
    try:
        add_rating_in_db(
            timestamp=timestamp, user_id=userid, movie_id=movie_id, rating=movie_rate
        )
    except Exception as ex:
        return f"kafka rating not added to db: {ex}"


def check_watch_timestamp_format(request_split: List[str]):

    good_format = True

    if len(request_split) != 3:
        good_format = False
    return good_format


def clean_kafka_watch_timestamp(request_split: List[str]):

    # check length of request, return error if wrong
    if not check_watch_timestamp_format(request_split):
        return "error: kafka timestamp format"

    try:
        # clean and make fields correct type
        timestamp = datetime.fromisoformat(request_split[0])
        userid = int(request_split[1])

        movieid_start_index = request_split[2].index("/data/m/") + len("/data/m/")
        end_index = request_split[2].index(".mpg")

        split_movie_minute = request_split[2][movieid_start_index:end_index].split("/")

        movie_id = split_movie_minute[0]

        movie_minute = int(split_movie_minute[1])
    except:
        return "error: kafka timestamp format"
    # create user if not present
    if not check_user_exists(userid=userid):
        if not add_user(userid=userid):
            return f"error: user {userid} cannot be added to db"

    # create movie if not present
    if not check_movie_exists(movieid=movie_id):
        if not add_movie(movieid=movie_id):
            return f"error: movie {movie_id} cannot be added to db"

    try:
        add_user_movie_watch_duration(
            timestamp=timestamp,
            user_id=userid,
            movie_id=movie_id,
            duration=movie_minute,
        )
    except:
        return "error: timestamp not added"


def check_recommendation_request_split_format(request_split: List[str]):

    good_format = True

    if len(request_split) != 15:
        good_format = False
    return good_format


def clean_kafka_recommendation_request(request_split: List[str]):
    # print('rec rec request')
    if not check_recommendation_request_split_format(request_split=request_split):
        return "error: kafka recommendation format"
    try:
        # timestamp of user watch duration data
        timestamp = datetime.fromisoformat(request_split[0])

        # userid
        userid = int(request_split[1])
        # request status
        response_code = int(request_split[3].split(" ")[-1])
        # recommended movies (list of comma separated str)
        results = request_split[4:-1]
        results[0] = results[0].split(" ")[-1]
        results = [res.strip(" ") for res in results]
        # response time
        latency_ms = int(request_split[-1].strip().split(" ")[0])

    except:
        return "error: kafka recommendation format"

    if not check_user_exists(userid=userid):
        add_user(userid=userid)
    # add movie to db if not present
    for mov in results:
        if not check_movie_exists(movieid=mov):
            add_movie(movieid=mov)

    try:
        add_recommendation_result(
            timestamp=timestamp,
            user_id=userid,
            latency_ms=latency_ms,
            response_code=response_code,
            results=results,
        )
    except:
        return "error: kafka recommendation not added"


def log_unknown_request():
    pass
