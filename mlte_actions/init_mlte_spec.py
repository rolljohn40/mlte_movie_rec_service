from mlte.spec.spec import Spec

# Import the Properties for this scenario
from mlte.property.costs.storage_cost import StorageCost
from mlte.property.fairness.fairness import Fairness
from mlte.property.robustness.robustness import Robustness
from mlte.property.costs.predicting_memory_cost import PredictingMemoryCost
from mlte.property.costs.predicting_compute_cost import PredictingComputeCost
from mlte.property.functionality.task_efficacy import TaskEfficacy

# Import Value types for each condition
from mlte.measurement.storage import LocalObjectSize
from mlte.measurement.cpu import LocalProcessCPUUtilization
from mlte.measurement.memory import LocalProcessMemoryConsumption

# Import Accuracy measure for sub-populations
from spec_values.eval_metrics import MultipleRmse
# Import Robustness measure for unknown user ids
from spec_values.robustness_metrics import UnknownUserRobustness
# Import Latency measure for inference
from spec_values.latency_metrics import MultipleLatency

def set_spec():
    # Define the Spec (Note that the Robustness Property contains conditions for both Robustness requirements)
    spec = Spec(
        properties={
            Fairness(
                "Important check if model performs well accross different populations"
            ): {
                "rmse across age groups": MultipleRmse.check_all_sub_pop_rmse_by_threshold(
                    4.0
                )
            },
            Robustness("Robust against unknown users"): {
                "unknown users receive recs": UnknownUserRobustness.check_all_unknown_userids_have_recommendations(),
            },
            StorageCost("Critical since model will be in an embedded device"): {
                "model size": LocalObjectSize.value().less_than(3000)
            },
            PredictingMemoryCost(
                "Useful to evaluate resources needed when predicting"
            ): {
                "predicting memory": LocalProcessMemoryConsumption.value().average_consumption_less_than(
                    512000.0
                )
            },
            TaskEfficacy('Inference time satisfies system requirements'):{
                'latency tests': MultipleLatency.check_all_latencies(threshold= 150)
            }
        }
    )
    spec.save(parents=True, force=True)