"""Command line interface: python -m tevv <command> ..."""

from __future__ import annotations

import argparse
import csv
import sys
from typing import Sequence

from .accuracy import cep_from_sigma, r95_from_sigma, summarise_errors
from .detection import ConfusionMatrix, base_rate_table, false_alarms_per_hour
from .evidence import TRL_LADDER, trl
from .intervals import clopper_pearson, wald, wilson
from .reliability import (
    demonstrated_reliability,
    rule_of_three,
    runs_with_failures,
    success_run_n,
    zero_failure_upper_bound,
)


def _pct(text: str) -> float:
    """Accept 0.9, 90 or 90%."""
    value = float(text.rstrip("%"))
    if value > 1:
        value /= 100.0
    if not 0 < value < 1:
        raise argparse.ArgumentTypeError(f"expected a probability, got {text!r}")
    return value


def _prob(text: str) -> float:
    value = float(text)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError(f"expected a value in [0, 1], got {text!r}")
    return value


def cmd_success_run(args: argparse.Namespace) -> None:
    if args.failures:
        n = runs_with_failures(args.reliability, args.confidence, args.failures)
        print(f"runs needed with at most {args.failures} failure(s): {n}")
    else:
        n = success_run_n(args.reliability, args.confidence)
        print(f"consecutive successes needed (zero failures): {n}")
    print(f"demonstrates R >= {args.reliability:.3f} at {args.confidence:.0%} confidence")


def cmd_demonstrated(args: argparse.Namespace) -> None:
    r = demonstrated_reliability(args.runs, args.confidence)
    print(f"{args.runs} clean runs demonstrate R >= {r:.3f} at {args.confidence:.0%} confidence")
    print(f"exact upper bound on failure rate: {zero_failure_upper_bound(args.runs, args.confidence):.3f}")
    if abs(args.confidence - 0.95) < 1e-9:
        print(f"rule of three approximation:       {rule_of_three(args.runs):.3f}")


def cmd_interval(args: argparse.Namespace) -> None:
    for fn in (wilson, clopper_pearson, wald):
        print(fn(args.successes, args.trials, args.confidence).as_text())


def cmd_ppv(args: argparse.Namespace) -> None:
    table = base_rate_table(args.pd, args.pfa, args.prevalence, args.population)
    print(f"out of {table['population']:,} decision opportunities")
    print(f"  target present      {table['present']:,.0f}")
    print(f"  target absent       {table['absent']:,.0f}")
    print(f"  true alarms         {table['true_alarms']:,.1f}")
    print(f"  false alarms        {table['false_alarms']:,.1f}")
    print(f"PPV (alarm is real)   {table['ppv']:.3f}")
    if args.decisions_per_hour:
        far = false_alarms_per_hour(args.pfa, args.decisions_per_hour)
        print(f"false alarms per hour at {args.decisions_per_hour:,.0f} decisions/h: {far:.2f}")


def cmd_confusion(args: argparse.Namespace) -> None:
    print(ConfusionMatrix(args.tp, args.fp, args.fn, args.tn).as_text())


def cmd_accuracy(args: argparse.Namespace) -> None:
    if args.sigma is not None:
        print(f"circular normal, sigma = {args.sigma} per axis, zero bias")
        print(f"CEP50 {cep_from_sigma(args.sigma):.2f}   R95 {r95_from_sigma(args.sigma):.2f}")
        return
    with open(args.csv, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        errors = [(float(row[args.east]), float(row[args.north])) for row in reader]
    print(summarise_errors(errors).as_text(args.unit))


def cmd_trl(args: argparse.Namespace) -> None:
    levels = [trl(args.level)] if args.level else list(TRL_LADDER)
    for item in levels:
        print(f"TRL {item.level}: {item.definition}")
        print(f"  article:     {item.article}")
        print(f"  environment: {item.environment}")
        print(f"  exit gate:   {item.exit_evidence}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tevv", description="Field-trial statistics for test and evaluation."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("success-run", help="runs needed to demonstrate reliability")
    p.add_argument("--reliability", "-R", type=_pct, required=True)
    p.add_argument("--confidence", "-C", type=_pct, required=True)
    p.add_argument("--failures", type=int, default=0, help="allowed failures (default 0)")
    p.set_defaults(func=cmd_success_run)

    p = sub.add_parser("demonstrated", help="reliability shown by n clean runs")
    p.add_argument("--runs", "-n", type=int, required=True)
    p.add_argument("--confidence", "-C", type=_pct, default=0.95)
    p.set_defaults(func=cmd_demonstrated)

    p = sub.add_parser("interval", help="confidence interval for k successes in n trials")
    p.add_argument("successes", type=int)
    p.add_argument("trials", type=int)
    p.add_argument("--confidence", "-C", type=_pct, default=0.95)
    p.set_defaults(func=cmd_interval)

    p = sub.add_parser("ppv", help="positive predictive value and the base-rate effect")
    p.add_argument("--pd", type=_prob, required=True)
    p.add_argument("--pfa", type=_prob, required=True)
    p.add_argument("--prevalence", type=_prob, required=True)
    p.add_argument("--population", type=int, default=10_000)
    p.add_argument("--decisions-per-hour", type=float, default=0.0)
    p.set_defaults(func=cmd_ppv)

    p = sub.add_parser("confusion", help="metrics from a confusion matrix")
    p.add_argument("--tp", type=int, required=True)
    p.add_argument("--fp", type=int, required=True)
    p.add_argument("--fn", type=int, required=True)
    p.add_argument("--tn", type=int, default=None, help="omit if not counted")
    p.set_defaults(func=cmd_confusion)

    p = sub.add_parser("accuracy", help="CEP50, R95 and maximum from error samples")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--csv", help="CSV with east and north error columns")
    group.add_argument("--sigma", type=float, help="closed form for circular normal error")
    p.add_argument("--east", default="east_m")
    p.add_argument("--north", default="north_m")
    p.add_argument("--unit", default="m")
    p.set_defaults(func=cmd_accuracy)

    p = sub.add_parser("trl", help="TRL ladder with evidence gates")
    p.add_argument("level", type=int, nargs="?")
    p.set_defaults(func=cmd_trl)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, KeyError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
