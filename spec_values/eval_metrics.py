from mlte.spec.condition import Condition
from mlte.validation.result import Failure, Success
from mlte.value.types.array import Array


# class for rmse metrics by sub-populations
# Copied/Modified from :
# https://github.com/mlte-team/mlte/blob/master/demo/scenarios/values/multiple_accuracy.py
class MultipleRmse(Array):
    """Array object with multiple accurcacy values"""

    @classmethod
    def check_all_sub_pop_rmse_by_threshold(cls, threshold: float) -> Condition:
        """Checks if the rmse for multiple populations is fair by checking if all of them are below the given threshold."""
        condition: Condition = Condition(
            'all_rmse_less_than',
            [threshold],
            lambda value: Success(
                f"All rmse are less than or equal to threshold {threshold}"
            ) if sum(g <= threshold for g in value.array) == len(value.array)
            else Failure(
                f"One or more rmse are above threshold {threshold}: {value.array}"
            ),
        )
        return condition
    
