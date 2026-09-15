import math

import pytest

from tevv import ConfusionMatrix, base_rate_table, false_alarms_per_hour, ppv


def test_ppv_base_rate_worked_example():
    assert ppv(0.95, 0.02, 0.01) == pytest.approx(0.324, abs=5e-4)


def test_ppv_balanced_test_set_looks_excellent():
    assert ppv(0.95, 0.02, 0.5) == pytest.approx(0.979, abs=5e-4)


def test_false_alarms_per_hour_worked_example():
    far = false_alarms_per_hour(0.0001, 3600)
    assert far == pytest.approx(0.36)
    assert 1 / far == pytest.approx(2.78, abs=0.01)  # hours between false alarms


def test_base_rate_table_natural_frequencies():
    t = base_rate_table(0.95, 0.02, 0.01, population=10_000)
    assert t["present"] == pytest.approx(100)
    assert t["true_alarms"] == pytest.approx(95)
    assert t["false_alarms"] == pytest.approx(198)
    assert t["alarms"] == pytest.approx(293)
    assert t["ppv"] == pytest.approx(ppv(0.95, 0.02, 0.01))


def test_confusion_matrix_metrics():
    cm = ConfusionMatrix(tp=80, fp=20, fn=10, tn=890)
    assert cm.recall == pytest.approx(80 / 90)
    assert cm.pd == cm.recall
    assert cm.precision == pytest.approx(0.8)
    assert cm.f1 == pytest.approx(2 * 0.8 * (8 / 9) / (0.8 + 8 / 9))
    assert cm.pfa == pytest.approx(20 / 910)
    assert cm.accuracy == pytest.approx(0.97)
    assert cm.prevalence == pytest.approx(0.09)
    assert "F1" in cm.as_text()


def test_detector_counts_without_true_negatives():
    # Object detectors usually cannot count true negatives.
    cm = ConfusionMatrix(tp=45, fp=5, fn=15)
    assert cm.precision == pytest.approx(0.9)
    assert cm.recall == pytest.approx(0.75)
    assert math.isnan(cm.pfa)
    assert "undefined" in cm.as_text()


def test_negative_counts_rejected():
    with pytest.raises(ValueError):
        ConfusionMatrix(tp=-1, fp=0, fn=0)
