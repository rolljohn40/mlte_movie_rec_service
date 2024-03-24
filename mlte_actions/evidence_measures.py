from typing import List
import pandas as pd
import numpy as np
from everything.svd_ratings_model import SVDRecommender
import time


# function to get rmse score for each age group
def rmse_score_by_age_group(age_bins: List[int], test_data: pd.DataFrame, svd: SVDRecommender):
    # store rmse by age group
    age_group_rmse = []
    # iterate through each age sub population
    for i,age in enumerate(age_bins):
        if i == 0:
            sub_group_data = test_data[test_data.age <= age_bins[i]].reset_index()
        else:
            sub_group_data = test_data[(test_data.age <= age_bins[i]) & (test_data.age > age_bins[i-1])].reset_index()
    
        # store results of predicted ratings/ true ratings
        predicted_ratings = []
        actual_ratings = []
        # store prediction/ truth for each test data point
        for i in range(len(sub_group_data)):
            user_id = sub_group_data.iloc[i,:].user_id
            movie_id = sub_group_data.iloc[i,:].movie_id
            predicted_rating = svd.predict_movie_rating_for_eval(userid = user_id, movieid = movie_id)
            actual_rating = sub_group_data.iloc[i,:].rating
            predicted_ratings.append(predicted_rating)
            actual_ratings.append(actual_rating)
        rmse = np.sqrt(np.mean((np.array(predicted_ratings) - np.array(actual_ratings)) ** 2))
        age_group_rmse.append(rmse)
    return age_group_rmse

# function to check that recommender system provides recs for cold start (unknown users)
def check_unknown_users_have_recs(unknown_users: List[int], svd: SVDRecommender):
    user_recs = []
    for userid in unknown_users:
        rec = svd.recommend_movies_for_user(user_id = userid)
        user_recs.append(rec)
    return user_recs

# function to check inference time for rec system
def get_prediction_latencies(test_userids: List[int], svd: SVDRecommender):
    latencies = []
    for userid in test_userids:
        start = time.time()
        svd.recommend_movies_for_user(user_id=userid)
        stop = time.time()
        latencies.append( stop - start)
    return latencies

