"""Reporting 2-D position accuracy as a distribution: CEP50, R95, maximum.

Closed forms hold only for a circular, zero-mean bivariate normal error.
Real navigation errors have bias, unequal axes and heavy tails, so the
empirical percentiles are what should be reported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

__all__ = [
    "CEP_FACTOR",
    "R95_FACTOR",
    "cep_from_sigma",
    "r95_from_sigma",
    "percentile",
    "AccuracySummary",
    "summarise_errors",
]

CEP_FACTOR = math.sqrt(2.0 * math.log(2.0))  # 1.1774
R95_FACTOR = math.sqrt(-2.0 * math.log(0.05))  # 2.4477


def cep_from_sigma(sigma: float) -> float:
    """CEP50 = sigma * sqrt(2 ln 2) for circular normal error, zero bias."""
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    return CEP_FACTOR * sigma


def r95_from_sigma(sigma: float) -> float:
    """R95 = sigma * sqrt(-2 ln 0.05) for circular normal error, zero bias."""
    if sigma < 0:
        raise ValueError("sigma must be non-negative")
    return R95_FACTOR * sigma


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile (same convention as numpy's default)."""
    if not values:
        raise ValueError("values must not be empty")
    if not 0 <= q <= 100:
        raise ValueError("q must lie in [0, 100]")
    data = sorted(values)
    pos = (len(data) - 1) * q / 100.0
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return data[lo]
    return data[lo] + (data[hi] - data[lo]) * (pos - lo)


@dataclass(frozen=True)
class AccuracySummary:
    n: int
    bias_east: float
    bias_north: float
    cep50: float
    r95: float
    maximum: float
    rms_radial: float

    def as_text(self, unit: str = "m") -> str:
        return "\n".join(
            [
                f"samples      {self.n}",
                f"bias (E, N)  {self.bias_east:+.2f}, {self.bias_north:+.2f} {unit}",
                f"CEP50        {self.cep50:.2f} {unit}",
                f"R95          {self.r95:.2f} {unit}",
                f"maximum      {self.maximum:.2f} {unit}",
                f"RMS radial   {self.rms_radial:.2f} {unit}",
                f"R95 / CEP50  {self.r95 / self.cep50:.2f}  (2.08 if circular normal)"
                if self.cep50
                else "R95 / CEP50  undefined",
            ]
        )


def summarise_errors(errors: Iterable[tuple[float, float]]) -> AccuracySummary:
    """Summarise (east, north) errors against ground truth.

    Radii are measured from truth, not from the mean, so bias is included in
    CEP50 and R95. Bias is also reported separately so it can be seen.
    """
    pts = [(float(e), float(n)) for e, n in errors]
    if not pts:
        raise ValueError("no error samples")
    radii = [math.hypot(e, n) for e, n in pts]
    return AccuracySummary(
        n=len(pts),
        bias_east=sum(e for e, _ in pts) / len(pts),
        bias_north=sum(n for _, n in pts) / len(pts),
        cep50=percentile(radii, 50),
        r95=percentile(radii, 95),
        maximum=max(radii),
        rms_radial=math.sqrt(sum(r * r for r in radii) / len(radii)),
    )
