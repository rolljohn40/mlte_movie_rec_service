from mlte_actions.init_mlte_context import set_context_and_store
from mlte_actions.init_mlte_spec import set_spec
from mlte_actions.collect_evidence import get_evidence
from mlte.spec.spec import Spec
from mlte.validation.spec_validator import SpecValidator
from mlte.value.artifact import Value


# set the mlte context and location for artifact storage
set_context_and_store()
# create the specification
set_spec()

# collect evidence
evidence_pieces = get_evidence()
# save evidence to context store
for ev in evidence_pieces:
    ev.save(force=True)

# load the specification
spec = Spec.load()

# load all values into validator
spec_validator = SpecValidator(spec)
spec_validator.add_values(Value.load_all())

# validate requirements and get validated details
validated_spec = spec_validator.validate()
validated_spec.save(force=True)

# visualize results of specification valiidation
validated_spec.print_results()

## deploy model or refuse pending results

