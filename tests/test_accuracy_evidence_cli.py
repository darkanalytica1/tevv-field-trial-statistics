import csv
import random

import pytest

from tevv import (
    CLAIM_CHECKLIST,
    TRL_LADDER,
    cep_from_sigma,
    check_claim,
    percentile,
    r95_from_sigma,
    summarise_errors,
    trl,
)
from tevv.cli import main


def test_cep_r95_worked_example_sigma_4m():
    assert cep_from_sigma(4) == pytest.approx(4.71, abs=0.005)
    assert r95_from_sigma(4) == pytest.approx(9.79, abs=0.005)


def test_empirical_percentiles_converge_to_closed_form():
    rng = random.Random(7)
    errors = [(rng.gauss(0, 4), rng.gauss(0, 4)) for _ in range(20_000)]
    s = summarise_errors(errors)
    assert s.cep50 == pytest.approx(4.71, rel=0.03)
    assert s.r95 == pytest.approx(9.79, rel=0.03)


def test_bias_inflates_cep_and_is_reported():
    rng = random.Random(11)
    errors = [(rng.gauss(3, 1), rng.gauss(0, 1)) for _ in range(5_000)]
    s = summarise_errors(errors)
    assert s.bias_east == pytest.approx(3, abs=0.1)
    assert s.cep50 > cep_from_sigma(1) * 2


def test_percentile_interpolation():
    assert percentile([1, 2, 3, 4], 50) == pytest.approx(2.5)
    assert percentile([5], 95) == 5


def test_trl_ladder():
    assert len(TRL_LADDER) == 9
    assert trl(6).environment.startswith("Relevant")
    with pytest.raises(ValueError):
        trl(10)


def test_claim_checklist_verdicts():
    keys = [k for k, _ in CLAIM_CHECKLIST]
    assert len(keys) == 12
    bare = check_claim({"metric": "detection range"})
    assert bare.status == "result under unstated conditions"
    core = check_claim({k: "stated" for k in keys[:8]})
    assert core.status.startswith("conditioned result")
    full = check_claim({k: "stated" for k in keys})
    assert full.status.startswith("specification-grade")
    with pytest.raises(KeyError):
        check_claim({"brochure": "yes"})


def test_cli_worked_examples(capsys, tmp_path):
    assert main(["success-run", "-R", "90", "-C", "90"]) == 0
    assert "22" in capsys.readouterr().out
    assert main(["interval", "18", "20"]) == 0
    assert "[0.699, 0.972]" in capsys.readouterr().out
    assert main(["ppv", "--pd", "0.95", "--pfa", "0.02", "--prevalence", "0.01"]) == 0
    assert "0.324" in capsys.readouterr().out
    assert main(["accuracy", "--sigma", "4"]) == 0
    assert "CEP50 4.71" in capsys.readouterr().out

    path = tmp_path / "errors.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["east_m", "north_m"])
        writer.writerows([(1, 0), (0, 2), (3, 4), (-1, -1)])
    assert main(["accuracy", "--csv", str(path)]) == 0
    assert "maximum      5.00 m" in capsys.readouterr().out


def test_cli_reports_errors(capsys):
    assert main(["interval", "5", "3"]) == 2
    assert "error" in capsys.readouterr().err
