"""Evidence frameworks as data: TRL gates, V&V, demonstration versus
characterisation, and the vendor-claim checklist.

The TRL short definitions follow the European Commission Horizon 2020
General Annex G. The "evidence to exit" column is an original synthesis of
public guidance (NASA, US GAO-20-48G) and is a reading aid, not an official
assessment method.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TRL",
    "TRL_LADDER",
    "trl",
    "VV_TABLE",
    "DEMO_VS_CHARACTERISATION",
    "CLAIM_CHECKLIST",
    "ClaimVerdict",
    "check_claim",
]


@dataclass(frozen=True)
class TRL:
    level: int
    definition: str
    article: str
    environment: str
    exit_evidence: str


TRL_LADDER: tuple[TRL, ...] = (
    TRL(1, "Basic principles observed", "None; science", "Paper",
        "Literature or experiments establishing the principle"),
    TRL(2, "Technology concept formulated", "Concept", "Paper, analysis",
        "Concept description, feasibility argument, identified applications"),
    TRL(3, "Experimental proof of concept", "Breadboard of critical functions", "Laboratory",
        "Lab measurements of critical parameters compared with analytic predictions"),
    TRL(4, "Technology validated in lab", "Integrated low-fidelity components", "Laboratory",
        "Components shown working together; reference values; deviations explained"),
    TRL(5, "Technology validated in relevant environment", "Components with realistic supporting elements",
        "Simulated or relevant environment",
        "Results in relevant conditions; analysis of lab-versus-real differences"),
    TRL(6, "Technology demonstrated in relevant environment", "Representative prototype system",
        "Relevant environment, high fidelity",
        "Prototype performing all required functions; scaling factors; statistically relevant results"),
    TRL(7, "System prototype demonstration in operational environment", "Near-final prototype",
        "Operational environment",
        "Characterised envelope; test-versus-real analysis; production risks addressed"),
    TRL(8, "System complete and qualified", "Final configuration", "Expected conditions including extremes",
        "Qualification reports across environments; final procedures; readiness review passed"),
    TRL(9, "Actual system proven in operational environment", "Production system", "Actual missions",
        "Operational test and in-service performance data from real deployment"),
)


def trl(level: int) -> TRL:
    if not 1 <= level <= 9:
        raise ValueError("TRL must be between 1 and 9")
    return TRL_LADDER[level - 1]


VV_TABLE = {
    "Question": ("Built to specification?", "Right system for the mission?"),
    "Reference": ("Requirements, design, interface documents", "Operational need, concept of operations, user"),
    "Methods": ("Inspection, analysis, demonstration, test", "Scenarios, user trials, exercises, experimentation"),
    "Who": ("Engineering, QA, independent verification", "End users, operational test agency, capability owner"),
    "Failure looks like": ("Non-conformance report", "It meets the spec but we cannot use it"),
}

DEMO_VS_CHARACTERISATION = {
    "Purpose": ("Show the function can work", "Measure how performance varies and where it stops"),
    "Conditions": ("Chosen, usually favourable", "Sampled across the envelope, incl. unfavourable"),
    "Runs": ("Few; selection often after the fact", "Sized in advance; selected before results are seen"),
    "Reference": ("Optional", "Independent ground truth, time synchronised"),
    "Output": ("A result under conditions", "Distributions and intervals per condition"),
    "Supports": ("Architecture claims", "Specification, acceptance and commitment decisions"),
}

# The first eight questions are the ones without which a number has no conditions.
CLAIM_CHECKLIST: tuple[tuple[str, str], ...] = (
    ("metric", "What exactly is the metric (CEP50, R95, Pd at stated Pfa)?"),
    ("target", "Against what target or threat configuration?"),
    ("geometry", "At what distance and geometry (line of sight, aspect, height)?"),
    ("environment", "In what environment (weather, clutter, RF background, light)?"),
    ("version", "With which software and firmware version?"),
    ("operator", "How much operator involvement?"),
    ("method", "What test method and independent reference?"),
    ("confidence", "What threshold, number of runs and confidence?"),
    ("false_alarms", "What were the false positives and misses?"),
    ("raw_evidence", "Is the raw evidence available?"),
    ("witness", "Who independently witnessed it?"),
    ("reproducible", "Can the customer reproduce it on their site?"),
)

_CORE_KEYS = tuple(key for key, _ in CLAIM_CHECKLIST[:8])


@dataclass(frozen=True)
class ClaimVerdict:
    status: str
    missing_core: tuple[str, ...]
    missing_support: tuple[str, ...]

    def as_text(self) -> str:
        lines = [f"verdict: {self.status}"]
        if self.missing_core:
            lines.append("missing conditions: " + ", ".join(self.missing_core))
        if self.missing_support:
            lines.append("missing support: " + ", ".join(self.missing_support))
        return "\n".join(lines)


def check_claim(answers: dict[str, str | None]) -> ClaimVerdict:
    """Classify a performance claim from checklist answers.

    Any missing core answer (the first eight) makes the number a result under
    unstated conditions. All eight present but support missing makes it a
    conditioned result. All twelve present makes it specification-grade
    evidence, still subject to review of the evidence itself.
    """
    unknown = set(answers) - {k for k, _ in CLAIM_CHECKLIST}
    if unknown:
        raise KeyError(f"unknown checklist keys: {sorted(unknown)}")

    def present(key: str) -> bool:
        value = answers.get(key)
        return value is not None and str(value).strip() != ""

    missing_core = tuple(k for k in _CORE_KEYS if not present(k))
    missing_support = tuple(k for k, _ in CLAIM_CHECKLIST[8:] if not present(k))
    if missing_core:
        status = "result under unstated conditions"
    elif missing_support:
        status = "conditioned result, not yet specification-grade"
    else:
        status = "specification-grade evidence (review the raw data)"
    return ClaimVerdict(status, missing_core, missing_support)
