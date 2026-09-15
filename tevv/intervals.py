"""Confidence intervals for a success proportion from few trials.

The Wilson score interval is the default recommendation for small samples
(Brown, Cai and DasGupta, 2001). The exact Clopper-Pearson interval is
provided for comparison: it is conservative, so it is wider.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from .reliability import binomial_cdf

__all__ = ["Interval", "z_for_confidence", "wilson", "clopper_pearson", "wald"]


@dataclass(frozen=True)
class Interval:
    """A two-sided interval for a proportion."""

    estimate: float
    low: float
    high: float
    confidence: float
    method: str

    @property
    def width(self) -> float:
        return self.high - self.low

    def as_text(self) -> str:
        return (
            f"{self.method}: p_hat = {self.estimate:.3f}, "
            f"{self.confidence:.0%} CI [{self.low:.3f}, {self.high:.3f}]"
        )


def z_for_confidence(confidence: float) -> float:
    """Two-sided standard normal quantile, e.g. 0.95 -> 1.95996."""
    if not 0 < confidence < 1:
        raise ValueError("confidence must lie in (0, 1)")
    return NormalDist().inv_cdf(0.5 + confidence / 2.0)


def _validate(k: int, n: int) -> None:
    if n < 1:
        raise ValueError("n must be at least 1")
    if not 0 <= k <= n:
        raise ValueError("k must satisfy 0 <= k <= n")


def wilson(k: int, n: int, confidence: float = 0.95, z: float | None = None) -> Interval:
    """Wilson score interval for k successes out of n trials.

    centre = (p + z^2 / 2n) / (1 + z^2 / n)
    half   = z / (1 + z^2 / n) * sqrt(p (1 - p) / n + z^2 / 4n^2)
    """
    _validate(k, n)
    if z is None:
        z = z_for_confidence(confidence)
    p = k / n
    z2n = z * z / n
    centre = (p + z2n / 2.0) / (1.0 + z2n)
    half = (z / (1.0 + z2n)) * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return Interval(p, max(0.0, centre - half), min(1.0, centre + half), confidence, "Wilson")


def wald(k: int, n: int, confidence: float = 0.95) -> Interval:
    """Textbook normal-approximation interval. Included to show why not to use
    it: at k = n it collapses to zero width."""
    _validate(k, n)
    z = z_for_confidence(confidence)
    p = k / n
    half = z * math.sqrt(p * (1.0 - p) / n)
    return Interval(p, max(0.0, p - half), min(1.0, p + half), confidence, "Wald")


def _bisect(fn, lo: float, hi: float, iters: int = 200) -> float:
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if fn(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def clopper_pearson(k: int, n: int, confidence: float = 0.95) -> Interval:
    """Exact (Clopper-Pearson) interval by inverting the binomial CDF.

    Pure standard library; uses bisection rather than the beta quantile.
    """
    _validate(k, n)
    alpha = 1.0 - confidence
    if k == 0:
        low = 0.0
    else:
        # smallest p with P(X >= k | p) >= alpha/2
        low = _bisect(lambda p: 1.0 - binomial_cdf(k - 1, n, p) >= alpha / 2.0, 0.0, 1.0)
    if k == n:
        high = 1.0
    else:
        # largest p with P(X <= k | p) >= alpha/2
        high = _bisect(lambda p: binomial_cdf(k, n, p) < alpha / 2.0, 0.0, 1.0)
    return Interval(k / n, low, high, confidence, "Clopper-Pearson")
