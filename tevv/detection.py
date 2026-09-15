"""Detection statistics: confusion matrix, Pd, Pfa, PPV and base rates."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ConfusionMatrix", "ppv", "false_alarms_per_hour", "base_rate_table"]


def _safe_div(num: float, den: float) -> float:
    return num / den if den else float("nan")


@dataclass(frozen=True)
class ConfusionMatrix:
    """Decisions tabulated against truth.

    tp: alarm, target present      fn: no alarm, target present (miss)
    fp: alarm, target absent       tn: no alarm, target absent
    """

    tp: int
    fp: int
    fn: int
    tn: int | None = None  # None: true negatives were not counted

    def __post_init__(self) -> None:
        for name in ("tp", "fp", "fn", "tn"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def total(self) -> int | None:
        if self.tn is None:
            return None
        return self.tp + self.fp + self.fn + self.tn

    @property
    def recall(self) -> float:
        """Recall, sensitivity, probability of detection: TP / (TP + FN)."""
        return _safe_div(self.tp, self.tp + self.fn)

    pd = recall

    @property
    def precision(self) -> float:
        """Precision, positive predictive value: TP / (TP + FP)."""
        return _safe_div(self.tp, self.tp + self.fp)

    @property
    def pfa(self) -> float:
        """False alarm probability per decision opportunity: FP / (FP + TN).
        Undefined (nan) when true negatives were not counted."""
        if self.tn is None:
            return float("nan")
        return _safe_div(self.fp, self.fp + self.tn)

    @property
    def specificity(self) -> float:
        if self.tn is None:
            return float("nan")
        return _safe_div(self.tn, self.fp + self.tn)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return _safe_div(2 * p * r, p + r)

    @property
    def accuracy(self) -> float:
        if self.tn is None:
            return float("nan")
        return _safe_div(self.tp + self.tn, self.total)

    @property
    def prevalence(self) -> float:
        if self.tn is None:
            return float("nan")
        return _safe_div(self.tp + self.fn, self.total)

    def as_text(self) -> str:
        rows = [
            "                 target present   target absent",
            f"alarm            TP = {self.tp:<12} FP = {self.fp}",
            f"no alarm         FN = {self.fn:<12} TN = {'not counted' if self.tn is None else self.tn}",
            "",
            f"recall / Pd      {self.recall:.3f}",
            f"precision / PPV  {self.precision:.3f}",
            f"F1               {self.f1:.3f}",
        ]
        if self.tn is not None:
            rows += [f"Pfa              {self.pfa:.4f}", f"accuracy         {self.accuracy:.3f}"]
        else:
            rows.append("Pfa              undefined (no true negatives counted)")
        return "\n".join(rows)


def ppv(pd: float, pfa: float, prevalence: float) -> float:
    """Probability that an alarm is real, given Pd, Pfa and prevalence.

    PPV = Pd * pi / (Pd * pi + Pfa * (1 - pi))

    >>> round(ppv(0.95, 0.02, 0.01), 3)
    0.324
    """
    for name, v in (("pd", pd), ("pfa", pfa), ("prevalence", prevalence)):
        if not 0 <= v <= 1:
            raise ValueError(f"{name} must lie in [0, 1]")
    true_alarms = pd * prevalence
    false_alarms = pfa * (1.0 - prevalence)
    return _safe_div(true_alarms, true_alarms + false_alarms)


def false_alarms_per_hour(pfa: float, decisions_per_hour: float) -> float:
    """FAR = Pfa * N_dec. Converts a per-decision figure into operator reality.

    >>> round(false_alarms_per_hour(0.0001, 3600), 2)
    0.36
    """
    if pfa < 0 or decisions_per_hour < 0:
        raise ValueError("inputs must be non-negative")
    return pfa * decisions_per_hour


def base_rate_table(pd: float, pfa: float, prevalence: float, population: int = 10_000) -> dict:
    """Natural-frequency breakdown used for the base-rate funnel diagram."""
    present = population * prevalence
    absent = population - present
    tp = present * pd
    fp = absent * pfa
    return {
        "population": population,
        "present": present,
        "absent": absent,
        "true_alarms": tp,
        "false_alarms": fp,
        "alarms": tp + fp,
        "ppv": _safe_div(tp, tp + fp),
    }
