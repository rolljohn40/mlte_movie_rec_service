import pandas as pd
from everything.db_ops import get_ratings_before_or_after_date_with_user_info
from everything.db import UserMovieRating, User
from everything.offline_eval import create_new_training_data
from everything.svd_ratings_model import SVDRecommender
from mlte_actions.evidence_measures import rmse_score_by_age_group, get_prediction_latencies, check_unknown_users_have_recs
from spec_values.eval_metrics import MultipleRmse
from spec_values.latency_metrics import MultipleLatency
from spec_values.robustness_metrics import UnknownUserRobustness

from mlte.measurement import ExternalMeasurement, ProcessMeasurement
from mlte.measurement.storage import LocalObjectSize
from mlte.measurement.memory import LocalProcessMemoryConsumption, MemoryStatistics
from mlte.value.types.integer import Integer


# get test data from postgres db
test_data = get_ratings_before_or_after_date_with_user_info(before=False, date='2024-02-09 00:00:00', num_ratings=9)

test_data_lst = []
for user_rating in test_data:
    test_data_lst.append(
        {
            "timestamp": user_rating[0].timestamp,
            "user_id": user_rating[0].user_id,
            "movie_id": user_rating[0].movie_id,
            "rating": user_rating[0].rating,
            "age": user_rating[1].age,
        }
    )
test_ratings_df = pd.DataFrame(test_data_lst)

# create model
svd = SVDRecommender(training_data_path='data/training_data/', max_timestamp= '2024-02-09 00:00:00',
                     eval_mode=True)

# collect evidence for rmse by age group
# define rmse measurement
rmse_measurement = ExternalMeasurement(
    "rmse across age groups", MultipleRmse, rmse_score_by_age_group
)
# evaluate with test data
age_bins = [27,35,60]
rmse = rmse_measurement.evaluate(age_bins, test_ratings_df, svd)

# collect evidence for unknown users getting recommendations
unknown_user_recs = ExternalMeasurement(
    "unknown users receive recs", UnknownUserRobustness, check_unknown_users_have_recs
)

# evaluate with test fake users
unk_users = [-1,-2,-3]
unk_user_recs = unknown_user_recs.evaluate(unk_users, svd)

# collect evidence for inference latency
inf_latency = ExternalMeasurement(
    "latency tests", MultipleLatency, get_prediction_latencies
)
# evaluate with test data
userids = test_ratings_df.user_id.tolist()
inf_latencies = inf_latency.evaluate(userids, svd)

# collect evidence for model storage requirements
model_size = LocalObjectSize("model size")
size: Integer = model_size.evaluate("data/training_data/")

# collect evidence for memory measurements
mem_measurement = LocalProcessMemoryConsumption("predicting memory")
mem_stats: MemoryStatistics = mem_measurement.evaluate(
    ProcessMeasurement.start_script('everything/svd_ratings_model.py',
                                     arguments=['50','10','data/training_data/','2024-02-09 00:00:00',
                                                'False'])
)

def get_evidence():
    return rmse, unk_user_recs, inf_latencies, size, mem_stats
