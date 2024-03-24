from mlte.spec.condition import Condition
from mlte.validation.result import Failure, Success
from mlte.value.types.array import Array


# class for inference latencies
# Copied/Modified from :
# https://github.com/mlte-team/mlte/blob/master/demo/scenarios/values/multiple_accuracy.py
class MultipleLatency(Array):
    """Array object with multiple latency values"""

    @classmethod
    def check_all_latencies(cls, threshold: float) -> Condition:
        """Checks if the prediction latencies are below the given threshold."""
        condition: Condition = Condition(
            'all_latencies_less_than',
            [threshold],
            lambda value: Success(
                f"All latencies are less than or equal to threshold {threshold}"
            ) if sum(g <= threshold for g in value.array) == len(value.array)
            else Failure(
                f"One or more latencies are above threshold {threshold}: {value.array}"
            ),
        )
        return condition