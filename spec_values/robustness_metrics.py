from mlte.spec.condition import Condition
from mlte.validation.result import Failure, Success
from mlte.value.types.array import Array

# class for rmse metrics by sub-populations
# Copied/Modified from :
# https://github.com/mlte-team/mlte/blob/master/demo/scenarios/values/ranksums.py
class UnknownUserRobustness(Array):
    """Array holding success/failure result for service recommending to unknown users"""

    @ classmethod
    def check_all_unknown_userids_have_recommendations(cls, ) -> Condition:
        condition: Condition = Condition(
            'all_unknown_users_have_movie_recs',
            [None],
            lambda recs: Success(
                f"All unknown users have non null movie recs"
            ) if sum(r != None for r in recs.array) == len(recs.array)
            else Failure(
                f"One or more unknown user ids have null recommendations"
            ),
        )
        return condition