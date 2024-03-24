from everything.db_ops import get_movie_id_to_index_map, get_unique_user_ids, populate_dok_matrix, get_top_1000_popular_movies, get_userid_userindex_map
from scipy.sparse import save_npz, dok_matrix
import pandas as pd
import pickle
import os

# function to create dicts, movieid -> movieindex in sparse matrix, movieindex -> movieid
def create_movie_dicts():
    movieid_movieindex_dict = get_movie_id_to_index_map()
    movieindex_movieid_dict = {value: key for key,value in movieid_movieindex_dict.items()}
    return movieid_movieindex_dict, movieindex_movieid_dict

# function create dict, userid -> userindex in sparse matrix
def create_user_dict():
    userid_userindex_map = get_userid_userindex_map()
    return userid_userindex_map

# function to create sparse matrix used for training data
def create_sparse_matrix(timestamp: str, userid_userindex_dict: dict, movieid_movieindex_dict: dict):
    # define shape of matrix
    shape = (len(userid_userindex_dict), len(movieid_movieindex_dict))
    # initialize dok sparse matrix
    new_dok_matrix = dok_matrix(shape)
    # populate dok_matrix
    new_dok_matrix = populate_dok_matrix(dok_matrix=new_dok_matrix, userid_userindex_dict= userid_userindex_dict, movieid_movieindex_dict= movieid_movieindex_dict, max_timestamp= timestamp)
    # convert to csr and return
    return new_dok_matrix.tocsr()

# function to create df holding most popular movies, holds movieid, popularity
def create_top1000_movies():
    return get_top_1000_popular_movies()

def save_movie_dicts(movieid_movieindex_dict, movieindex_movieid_dict, path):
    print(path + '/movieid_movieindex_dict.pkl')
    print(os.getcwd())
    with open(path+'/movieid_movieindex_dict.pkl','wb') as pickle_file:
        pickle.dump(movieid_movieindex_dict, pickle_file)
    with open(path+'/movieindex_movieid_dict.pkl','wb') as pickle_file:
        pickle.dump(movieindex_movieid_dict, pickle_file)

def save_user_dict(userid_userindex_dict, path):
    with open(path+'//userid_userindex_dict.pkl','wb') as pickle_file:
        pickle.dump(userid_userindex_dict, pickle_file)    

def save_sparse_matrix(sparse_matrix, path: str, max_timestamp: str):
    save_npz(path+'//user_movie_sparse_rating_matrix_'+max_timestamp[:10]+'.npz', sparse_matrix)

def save_top1000_movies(top1000moviesDf: pd.DataFrame, path: str):
    top1000moviesDf.to_csv(path+'//top_1000_movies.csv',index=False)

