import logging
import everything.db

from datetime import datetime, timedelta
from flask import Flask
from sqlalchemy import select
from sqlalchemy.orm import Session
from everything import svd_ratings_model
from everything.db import User, Movie, Recommendation

recommender = svd_ratings_model.SVDRecommender(
    training_data_path="data/offline_eval",
    max_timestamp="2024-03-17"
)
app = Flask(__name__)


@app.route("/recommend/<user_id>")
def recommend(user_id: str):
    # Check whether user_id is in database
    with Session(everything.db.ENGINE) as session:
        stmt = select(User).where(User.id == user_id)
        user_exists = session.scalar(stmt) is not None

    # Generate recommendations
    t0 = datetime.now()
    recommendations = recommender.recommend_movies_for_user(user_id)
    latency = int((datetime.now() - t0) / timedelta(milliseconds=1))
    logging.info(
        "Recommendations for user %s (exist=%s, latency=%dms): %s",
        user_id,
        user_exists,
        latency,
        recommendations,
    )

    # Write log to database
    with Session(everything.db.ENGINE) as session:
        movie_ids = recommendations.split(",")
        movies = list(session.scalars(select(Movie).where(Movie.id.in_(movie_ids))))
        recommendation_log = Recommendation(
            timestamp=datetime.now(),
            user_id=user_id if user_exists else None,
            latency_ms=latency,
            response_code=200,
            results=movies,
        )
        session.add(recommendation_log)
        session.commit()

    return recommendations


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (PID %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    app.run(host="0.0.0.0", port=8082)
