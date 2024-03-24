import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from scipy.sparse.linalg import svds
# from ..db_ops import get_movie_id_to_index_map, get_unique_user_ids, populate_dok_matrix, get_top_1000_popular_movies
import pickle
import argparse

class SVDRecommender:


    def __init__(self, num_latent_factors=50, num_recommendations=10, training_data_path = '', max_timestamp = '', eval_mode = False):
        """
        Initialize the SVDRecommender.

        Args:
            training_data_cutoff_timestamp: cutoff for most recent data to be used in training
            num_latent_factors (int): The number of latent factors to use for SVD.
            num_recommendations (int): The number of recommendations to generate.
            training_data_path (str): path to directory with training data
            eval_mode (bool): whether model being used for production or eval
        """
        
        # todo likely have to change ends of paths
        movieindex_movieid_dict_path = training_data_path + '/movieindex_movieid_dict.pkl'
        userid_userindex_dict_path= training_data_path + '/userid_userindex_dict.pkl'
        sparse_matrix_path = training_data_path + '/user_movie_sparse_rating_matrix_'+max_timestamp[:10]+'.npz'
        movieid_movieindex_dict_path = training_data_path +  '/movieid_movieindex_dict.pkl'
        top1000_movies_path = training_data_path + '/top_1000_movies.csv'

        # max timestamp of training data
        self.max_timestamp = max_timestamp
        # load the sparse matrix
        self.sparse_matrix = load_npz(sparse_matrix_path).astype(float)
        # load map from userid to userindex
        with open(userid_userindex_dict_path,'rb') as f:
            self.userid_userindex_dict = pickle.load(f)
        # load the dict that maps movie index in matrix to movieid
        with open(movieindex_movieid_dict_path,'rb') as f:
            self.movieindex_movieid_dict = pickle.load(f)
        with open(movieid_movieindex_dict_path,'rb') as f:
            self.movieid_movieindex_dict = pickle.load(f)
        self.top1000_movies = pd.read_csv(top1000_movies_path)

        # hyperparameter
        self.num_latent_factors = num_latent_factors
        self.num_recommendations = num_recommendations
        # U: user latent features, sigma: singular values, Vt: movie latent features
        self.U, self.sigma, self.Vt = svds(self.sparse_matrix, k=num_latent_factors)
        # construct diagonal matrix
        self.sigma = np.diag(self.sigma)
        # indicator on if being used in model tuning/ eval suite
        self.eval_mode = eval_mode

    def recommend_movies_for_user(self, user_id):
        """
        Generate recommendations for a user.

        Args:
            user_id (int): The index of the user.

        Returns:
            list: Indices of recommended items.
        """
        # change user_id to user_index
        try:
            user_index = self.userid_userindex_dict[user_id]
        except:
            self.log_unknown_user(user_id=user_id)
            # return random sample of popular movies
            return self.get_random_movie_sample()
        # Get the user's predicted ratings
        # saves memory by only reconstructing the indicated user's row of the rating matrix
        user_pred_ratings = np.dot(np.dot(self.U[user_index], self.sigma), self.Vt)
        # Sort the items by their predicted ratings, ascending
        sorted_indices = np.argsort(user_pred_ratings)
        # Exclude items the user has already rated
        unrated_items_mask = (~(self.sparse_matrix[user_index] != 0).toarray()).flatten()
        # use mask to remove rated movies from the predictions in sorted_indices
        sorted_filtered_indices = sorted_indices[unrated_items_mask[sorted_indices]]
        # choose the requested number of highest predicted value movies
        # order from most confident to least confident
        recommended_movie_indices = sorted_filtered_indices[-self.num_recommendations:][::-1]
        # change from movie indices to movie ids
        recommended_movie_ids = [self.movieindex_movieid_dict[index] for index in recommended_movie_indices]
        return ','.join(recommended_movie_ids)

    # get random weighted sample based on movie popularity from movie data
    # used if userid not present in data
    def get_random_movie_sample(self,):
        movie_sample = self.top1000_movies.sample(n=self.num_recommendations, weights=self.top1000_movies.popularity)
        return ','.join(movie_sample.id)

    def log_unknown_user(self, user_id):
        pass
    

    def predict_movie_rating_for_eval(self,userid, movieid):
        # overide default class parameter eval_mode if used for evaluating hyperparameters
        if not self.eval_mode:
            raise ValueError('Method only allowed for testing/eval purposes')
        # todo: allow for use when tuning hyperparameters/ evaluating on train/test sets?
        try:
            userindex = self.userid_userindex_dict[userid]
            movieindex = self.movieid_movieindex_dict[movieid]
        except:
            return -2
        pred = np.dot(np.dot(self.U[userindex], self.sigma), self.Vt)[movieindex]
        return pred

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create new model")
    parser.add_argument('arg1', type=int, help="number of latent features")
    parser.add_argument('arg2', type=int, help="number of recommendations to provide")
    parser.add_argument('arg3', type=str, help="path to training data")
    parser.add_argument('arg4', type=str, help="max timestamp in training data")
    parser.add_argument('arg5', type=bool, help="eval mode, optional")


    args = parser.parse_args()
    
    num_latent_factors = args.arg1
    num_recommendations = args.arg2
    training_data_path = args.arg3
    max_timestamp = args.arg4
    try:
        eval_mode = args.arg5
    except:
        eval_mode = False

    # create new model
    svd_model = SVDRecommender(num_latent_factors= num_latent_factors,
                               num_recommendations= num_recommendations,
                               training_data_path= training_data_path,
                               max_timestamp= max_timestamp,
                               eval_mode= eval_mode)