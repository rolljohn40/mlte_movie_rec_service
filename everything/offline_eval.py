from datetime import datetime
import pandas as pd
from everything.db_ops import *
from everything.svd_ratings_model import *
import os
import scipy
import numpy as np
from everything.pipeline.process_model_data.create_model_data import *


max_timestamp = "2024-03-17T07:01:25"
# max_timestamp = "2023-12-31T19:56:37"
path = "data/offline_eval"
os.makedirs(path, exist_ok=True)


def create_new_training_data(max_timestamp, path):

    # create and save movie dicts
    movieid_movieindex_dict, movieindex_movieid_dict = create_movie_dicts()
    save_movie_dicts(
        movieid_movieindex_dict=movieid_movieindex_dict,
        movieindex_movieid_dict=movieindex_movieid_dict,
        path=path,
    )

    # create and save user dict
    userid_userindex_dict = create_user_dict()
    save_user_dict(userid_userindex_dict=userid_userindex_dict, path=path)
    # create and save sparse ratings matrix
    rating_matrix = create_sparse_matrix(
        timestamp=max_timestamp,
        userid_userindex_dict=userid_userindex_dict,
        movieid_movieindex_dict=movieid_movieindex_dict,
    )

    save_sparse_matrix(
        sparse_matrix=rating_matrix, path=path, max_timestamp=max_timestamp
    )

    # create and save top 1000 movies df
    top1000MoviesDf = create_top1000_movies()
    save_top1000_movies(top1000moviesDf=top1000MoviesDf, path=path)


if __name__ == "__main__":
    # build the new training data -- all files will be dumped in: everything/pipeline/new_timestap_model_data
    create_new_training_data(max_timestamp, path)

    after_max_timestamp_ratings = get_ratings_before_or_after_date(
        before=False, date=max_timestamp, num_ratings=5000
    )
    val_size = len(after_max_timestamp_ratings) // 3
    val_data = after_max_timestamp_ratings[: 2 * val_size]
    val_data_lst = []
    for obj in val_data:
        val_data_lst.append(
            {
                "timestamp": obj.timestamp,
                "user_id": obj.user_id,
                "movie_id": obj.movie_id,
                "rating": obj.rating,
            }
        )
    val_ratings_df = pd.DataFrame(val_data_lst)
    test_data = after_max_timestamp_ratings[2 * val_size :]
    test_data_lst = []
    for obj in test_data:
        test_data_lst.append(
            {
                "timestamp": obj.timestamp,
                "user_id": obj.user_id,
                "movie_id": obj.movie_id,
                "rating": obj.rating,
            }
        )

    test_ratings_df = pd.DataFrame(test_data_lst)

    # for checking model performance on val data:
    hyper_params = {"num_latent_factors": [10, 20, 30, 40, 50]}

    rmse_scores = {}

    for hp in hyper_params["num_latent_factors"]:
        # instantiate the recommender with this new training data (built based on timestamp)

        svd_model = SVDRecommender(
            num_latent_factors=hp,
            training_data_path=path,
            max_timestamp=max_timestamp,
            eval_mode=True,
        )
        preds = []
        real_vals = []
        for row in range(len(val_ratings_df)):
            pred_rating = svd_model.predict_movie_rating_for_eval(
                int(val_ratings_df.iloc[row, 1]), val_ratings_df.iloc[row, 2]
            )
            if pred_rating != -2:
                preds.append(pred_rating)
                real_vals.append(val_ratings_df.iloc[row, 3])

        rmse = np.sqrt(np.mean((np.array(preds) - np.array(real_vals)) ** 2))
        rmse_scores[hp] = rmse

    print(rmse_scores)

    # best score so far with 50 latent features so final test accuracy evaluation  (on test data):

    svd_model_test = SVDRecommender(
        num_latent_factors=50,
        training_data_path=path,
        max_timestamp=max_timestamp,
        eval_mode=True,
    )
    preds = []
    real_vals = []
    for row in range(len(test_ratings_df)):
        pred_rating = svd_model_test.predict_movie_rating_for_eval(
            int(test_ratings_df.iloc[row, 1]), test_ratings_df.iloc[row, 2]
        )
        if pred_rating != -2:
            preds.append(pred_rating)
            real_vals.append(test_ratings_df.iloc[row, 3])

    rmse_test = np.sqrt(np.mean((np.array(preds) - np.array(real_vals)) ** 2))
    print(rmse_test)
