"""Reliability demonstration arithmetic for small field trials.

All functions assume independent, identically distributed trials run in
representative conditions (a binomial model). That assumption is the first
thing a real trial breaks: ten runs over the same patch of ground are closer
to one run repeated than to ten independent samples.
"""

from __future__ import annotations

import math

__all__ = [
    "success_run_n",
    "demonstrated_reliability",
    "binomial_cdf",
    "runs_with_failures",
    "rule_of_three",
    "zero_failure_upper_bound",
]


def _check_prob(name: str, value: float, *, open_interval: bool = True) -> None:
    lo_ok = value > 0 if open_interval else value >= 0
    hi_ok = value < 1 if open_interval else value <= 1
    if not (lo_ok and hi_ok):
        bounds = "(0, 1)" if open_interval else "[0, 1]"
        raise ValueError(f"{name} must lie in {bounds}, got {value!r}")


def success_run_n(reliability: float, confidence: float) -> int:
    """Consecutive successes needed, with zero failures, to demonstrate
    ``reliability`` at ``confidence``.

    n = ln(1 - C) / ln(R), rounded up.

    >>> success_run_n(0.90, 0.90)
    22
    >>> success_run_n(0.95, 0.95)
    59
    """
    _check_prob("reliability", reliability)
    _check_prob("confidence", confidence)
    raw = math.log(1.0 - confidence) / math.log(reliability)
    # Guard against floating point pushing an exact integer just above itself.
    return math.ceil(raw - 1e-9)


def demonstrated_reliability(n: int, confidence: float) -> float:
    """Lower confidence bound on reliability after ``n`` clean runs.

    Solves (1 - C) = R^n for R, so R = (1 - C)^(1/n).

    >>> round(demonstrated_reliability(10, 0.90), 3)
    0.794
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    _check_prob("confidence", confidence)
    return (1.0 - confidence) ** (1.0 / n)


def binomial_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if n < 0 or k < 0:
        raise ValueError("n and k must be non-negative")
    _check_prob("p", p, open_interval=False)
    k = min(k, n)
    return sum(math.comb(n, i) * p**i * (1.0 - p) ** (n - i) for i in range(k + 1))


def runs_with_failures(reliability: float, confidence: float, failures: int) -> int:
    """Smallest n such that observing at most ``failures`` failures in n runs
    demonstrates ``reliability`` at ``confidence``.

    Condition: P(failures <= f | true reliability = R) <= 1 - C.
    With ``failures=0`` this reduces to :func:`success_run_n`.
    """
    _check_prob("reliability", reliability)
    _check_prob("confidence", confidence)
    if failures < 0:
        raise ValueError("failures must be non-negative")
    q = 1.0 - reliability  # per-run failure probability at the boundary
    n = failures + 1
    while binomial_cdf(failures, n, q) > (1.0 - confidence) + 1e-12:
        n += 1
        if n > 1_000_000:  # pragma: no cover - defensive
            raise RuntimeError("sample size search did not converge")
    return n


def rule_of_three(n: int) -> float:
    """Approximate 95% upper bound on the failure rate after ``n`` trials
    with zero failures: 3 / n (Hanley and Lippman-Hand, 1983)."""
    if n < 1:
        raise ValueError("n must be at least 1")
    return 3.0 / n


def zero_failure_upper_bound(n: int, confidence: float = 0.95) -> float:
    """Exact one-sided upper bound on the failure rate after ``n`` clean
    trials: 1 - (1 - C)^(1/n). The rule of three approximates this at 95%."""
    return 1.0 - demonstrated_reliability(n, confidence)
