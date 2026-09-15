import pytest

from tevv import clopper_pearson, wald, wilson, z_for_confidence


def test_z_for_95_percent():
    assert z_for_confidence(0.95) == pytest.approx(1.95996, abs=1e-5)


def test_wilson_worked_example_18_of_20():
    ci = wilson(18, 20, z=1.96)
    assert ci.estimate == pytest.approx(0.90)
    assert ci.low == pytest.approx(0.699, abs=5e-4)
    assert ci.high == pytest.approx(0.972, abs=5e-4)
    # centre 0.8356, half-width 0.1366
    assert (ci.low + ci.high) / 2 == pytest.approx(0.8356, abs=5e-4)
    assert ci.width / 2 == pytest.approx(0.1366, abs=5e-4)


def test_clopper_pearson_is_wider_than_wilson():
    w = wilson(18, 20)
    cp = clopper_pearson(18, 20)
    assert cp.low < w.low
    assert cp.high > w.high
    # Reference values for the exact interval, 18/20 at 95%
    assert cp.low == pytest.approx(0.6830, abs=1e-3)
    assert cp.high == pytest.approx(0.9877, abs=1e-3)


def test_wald_collapses_at_all_successes():
    assert wald(20, 20).width == 0.0
    assert wilson(20, 20).width > 0.1


def test_clopper_pearson_zero_successes_matches_exact_bound():
    cp = clopper_pearson(0, 30, 0.90)  # one-sided 95% upper bound
    assert cp.low == 0.0
    assert cp.high == pytest.approx(1 - 0.05 ** (1 / 30), abs=1e-6)


def test_input_validation():
    with pytest.raises(ValueError):
        wilson(21, 20)
    with pytest.raises(ValueError):
        wilson(1, 0)
