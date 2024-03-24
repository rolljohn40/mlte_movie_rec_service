import argparse

from everything.pipeline.process_model_data.create_model_data import *

parser = argparse.ArgumentParser(description="Begin creation of new training data")
parser.add_argument('arg1', type=str, help="max timestamp present in training data")
parser.add_argument('arg2', type=str, help="path to store training data")


# handles creation of new training data for svd model, uses modules in .\process_model_data
if __name__=='__main__':

    args = parser.parse_args()
    
    # create and save movie dicts
    movieid_movieindex_dict, movieindex_movieid_dict = create_movie_dicts()
    save_movie_dicts(movieid_movieindex_dict= movieid_movieindex_dict, 
                     movieindex_movieid_dict= movieindex_movieid_dict,
                     path = args.arg2)
    
    # create and save user dict
    userid_userindex_dict = create_user_dict()
    save_user_dict(userid_userindex_dict= userid_userindex_dict, path = args.arg2)

    # create and save sparse ratings matrix
    rating_matrix = create_sparse_matrix(timestamp= args.arg1, userid_userindex_dict= userid_userindex_dict,
                                         movieid_movieindex_dict= movieid_movieindex_dict)
    
    save_sparse_matrix(sparse_matrix= rating_matrix, path = args.arg2, max_timestamp= args.arg1)

    # create and save top 1000 movies df
    top1000MoviesDf = create_top1000_movies()
    save_top1000_movies(top1000moviesDf= top1000MoviesDf, path= args.arg2)



