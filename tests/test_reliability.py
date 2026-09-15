import math

import pytest

from tevv import (
    binomial_cdf,
    demonstrated_reliability,
    rule_of_three,
    runs_with_failures,
    success_run_n,
    zero_failure_upper_bound,
)


@pytest.mark.parametrize(
    "reliability, confidence, expected",
    [(0.90, 0.90, 22), (0.95, 0.95, 59), (0.99, 0.90, 230)],
)
def test_success_run_worked_examples(reliability, confidence, expected):
    assert success_run_n(reliability, confidence) == expected


def test_raw_success_run_value():
    # n = ln(0.10) / ln(0.90) = 21.85 before rounding up
    assert math.log(0.10) / math.log(0.90) == pytest.approx(21.85, abs=0.01)


def test_ten_clean_launches_show_only_79_percent():
    assert demonstrated_reliability(10, 0.90) == pytest.approx(0.794, abs=5e-4)


def test_demonstrated_reliability_inverts_success_run():
    n = success_run_n(0.90, 0.90)
    assert demonstrated_reliability(n, 0.90) >= 0.90


def test_one_allowed_failure_needs_more_runs():
    zero = runs_with_failures(0.90, 0.90, 0)
    one = runs_with_failures(0.90, 0.90, 1)
    assert zero == success_run_n(0.90, 0.90)
    assert one == 38
    assert binomial_cdf(1, one, 0.10) <= 0.10 < binomial_cdf(1, one - 1, 0.10)


def test_rule_of_three_and_exact_bound():
    assert rule_of_three(30) == pytest.approx(0.10)
    assert zero_failure_upper_bound(30, 0.95) == pytest.approx(0.095, abs=5e-4)


def test_binomial_cdf_sums_to_one():
    assert binomial_cdf(20, 20, 0.3) == pytest.approx(1.0)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.2])
def test_rejects_degenerate_probabilities(bad):
    with pytest.raises(ValueError):
        success_run_n(bad, 0.9)
    with pytest.raises(ValueError):
        success_run_n(0.9, bad)
