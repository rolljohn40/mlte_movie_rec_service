import sys
import logging
import itertools
import pandas as pd
import everything.db

from datetime import datetime, timedelta
from pprint import pformat
from dataclasses import dataclass, asdict
from tqdm import tqdm
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sklearn.model_selection import train_test_split
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from everything.db import Recommendation, UserMovieRating, UserMovieWatchDuration


@dataclass
class RecommendationTrace:
    user_id: int
    recommendation_time: datetime
    recommendations: list[str]
    rated: list[str]
    watched: list[str]


def get_recommendation_traces(
    since: datetime,
) -> tuple[list[Recommendation], list[UserMovieRating], list[UserMovieWatchDuration]]:
    with Session(everything.db.ENGINE) as session:
        stmt = (
            select(Recommendation)
            .options(joinedload(Recommendation.results))
            .where(Recommendation.timestamp >= since)
        )
        recommendations = list(session.scalars(stmt).unique())

        stmt = select(UserMovieRating).where(UserMovieRating.timestamp >= since)
        ratings = list(session.scalars(stmt))

        stmt = select(UserMovieWatchDuration).where(
            UserMovieWatchDuration.timestamp >= since
        )
        watch_durations = list(session.scalars(stmt))
    logging.info(
        "Since %s: %d recommendations, %d ratings, %d watch durations",
        since,
        len(recommendations),
        len(ratings),
        len(watch_durations),
    )
    return recommendations, ratings, watch_durations


def convert_recommendation_traces(
    recommendations: list[Recommendation],
    ratings: list[UserMovieRating],
    watch_durations: list[UserMovieWatchDuration],
) -> list[RecommendationTrace]:
    traces = []

    user_ids = set(r.user_id for r in recommendations)
    logging.info("%d user ids in telemetry data", len(user_ids))
    for user_id in tqdm(user_ids):
        user_recs = [r for r in recommendations if r.user_id == user_id]
        user_ratings = [r for r in ratings if r.user_id == user_id]
        user_watch_durations = [r for r in watch_durations if r.user_id == user_id]
        if len(user_recs) == 1:
            traces.append(
                RecommendationTrace(
                    user_id=user_id,
                    recommendation_time=user_recs[0].timestamp,
                    recommendations=[r.id for r in user_recs[0].results],
                    rated=[r.movie_id for r in user_ratings],
                    watched=[r.movie_id for r in user_watch_durations],
                )
            )
        else:
            user_recs = sorted(user_recs, key=lambda r: r.timestamp)
            for rec1, rec2 in itertools.pairwise(user_recs):
                t1, t2 = rec1.timestamp, rec2.timestamp
                rs = [r for r in user_ratings if t1 <= r.timestamp < t2]
                ws = [r for r in user_watch_durations if t1 <= r.timestamp < t2]
                traces.append(
                    RecommendationTrace(
                        user_id=user_id,
                        recommendation_time=rec1.timestamp,
                        recommendations=[r.id for r in rec1.results],
                        rated=[r.movie_id for r in rs],
                        watched=[r.movie_id for r in ws],
                    )
                )
            last = user_recs[-1].timestamp
            traces.append(
                RecommendationTrace(
                    user_id=user_id,
                    recommendation_time=last,
                    recommendations=[r.id for r in user_recs[-1].results],
                    rated=[r.movie_id for r in user_ratings if r.timestamp >= last],
                    watched=[
                        r.movie_id for r in user_watch_durations if r.timestamp >= last
                    ],
                )
            )
    return traces


def get_ratio_followed_recs(traces: list[RecommendationTrace], activity: str):
    assert activity == "rated" or activity == "watched"
    if len(traces) == 0:
        return 0
    n_followed = 0
    for trace in traces:
        if len(set(trace.recommendations) & set(getattr(trace, activity))) > 0:
            n_followed += 1
    return n_followed / len(traces)


def get_avg_followed_recs_ranking(traces: list[RecommendationTrace], activity: str):
    assert activity == "rated" or activity == "watched"
    if len(traces) == 0:
        return -1
    rankings = []
    for trace in traces:
        for movie_id in getattr(trace, activity):
            if movie_id in trace.recommendations:
                rankings.append(trace.recommendations.index(movie_id))
    return sum(rankings) / len(traces)


def detect_rating_drift():
    report = Report(metrics=[DataDriftPreset()])
    with Session(everything.db.ENGINE) as session:
        ratings = list(
            session.scalars(
                select(UserMovieRating).order_by(UserMovieRating.timestamp).limit(10000)
            )
        )
    df = pd.DataFrame([{"rating": r.rating} for r in ratings])
    logging.info(df.head())
    old_df, new_df = train_test_split(df, test_size=0.2)
    report.run(reference_data=old_df, current_data=new_df)
    logging.info(pformat(report.as_dict()))
    
    for metric in report.as_dict()["metrics"]:
        if metric["result"]["dataset_drift"]:
            logging.warning("Drift detected: %s", pformat(metric))


def telemetry():
    since, now = datetime.now() - timedelta(hours=2), datetime.now()

    recommendations, ratings, watches = get_recommendation_traces(since)
    traces = convert_recommendation_traces(recommendations, ratings, watches)
    pd.DataFrame(list(map(asdict, traces))).to_csv(
        f"logs/traces_{datetime.now()}.csv", index=False
    )
    logging.info("From %s to %s: %d recommendation traces", since, now, len(traces))

    logging.info(
        "Ratio of Watches Following Recommendation: %.4f",
        get_ratio_followed_recs(traces, "watched"),
    )
    logging.info(
        "Avg Ranking of Watches Following Recommendation: %.4f",
        get_avg_followed_recs_ranking(traces, "watched"),
    )

    logging.info(
        "Ratio of Ratings Following Recommendation: %.4f",
        get_ratio_followed_recs(traces, "rated"),
    )
    logging.info(
        "Avg Ranking of Ratings Following Recommendation: %.4f",
        get_avg_followed_recs_ranking(traces, "rated"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )

    telemetry()

    detect_rating_drift()
