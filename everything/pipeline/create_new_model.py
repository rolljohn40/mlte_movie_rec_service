import argparse
from everything.svd_ratings_model import SVDRecommender


parser = argparse.ArgumentParser(description="Create new model")
parser.add_argument('arg1', type=int, help="number of latent features")
parser.add_argument('arg2', type=int, help="number of recommendations to provide")
parser.add_argument('arg3', type=str, help="path to training data")
parser.add_argument('arg4', type=str, help="max timestamp in training data")
parser.add_argument('arg5', type=bool, help="eval mode, optional")


# handles processing from kafka, uses modules within .\ingest_kafka for processing
if __name__=='__main__':

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
    
    # todo: save model? or what's next step




