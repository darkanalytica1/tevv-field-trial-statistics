"""tevv: small, tested statistics for test, evaluation, verification and
validation of field trials. Pure standard library."""

from .accuracy import cep_from_sigma, percentile, r95_from_sigma, summarise_errors
from .detection import ConfusionMatrix, base_rate_table, false_alarms_per_hour, ppv
from .evidence import CLAIM_CHECKLIST, TRL_LADDER, check_claim, trl
from .intervals import Interval, clopper_pearson, wald, wilson, z_for_confidence
from .reliability import (
    binomial_cdf,
    demonstrated_reliability,
    rule_of_three,
    runs_with_failures,
    success_run_n,
    zero_failure_upper_bound,
)

__version__ = "0.1.0"

__all__ = [
    "CLAIM_CHECKLIST",
    "ConfusionMatrix",
    "Interval",
    "TRL_LADDER",
    "base_rate_table",
    "binomial_cdf",
    "cep_from_sigma",
    "check_claim",
    "clopper_pearson",
    "demonstrated_reliability",
    "false_alarms_per_hour",
    "percentile",
    "ppv",
    "r95_from_sigma",
    "rule_of_three",
    "runs_with_failures",
    "success_run_n",
    "summarise_errors",
    "trl",
    "wald",
    "wilson",
    "z_for_confidence",
    "zero_failure_upper_bound",
]
