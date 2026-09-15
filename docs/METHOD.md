# Method notes

These notes explain the vocabulary and arithmetic behind the package. Every formula is standard; the framing and worked examples are original synthesis from the public sources in [SOURCES.md](SOURCES.md).

## 01 Verification versus validation

Verification asks whether the system was built right: does it conform to its specified requirements. Validation asks whether it is the right system: does it meet the user's need, in the intended environment, with the intended users.

| Aspect | Verification | Validation |
|---|---|---|
| Question | Built to specification? | Right system for the mission? |
| Reference | Requirements, design, interface documents | Operational need, concept of operations, user |
| Methods | Inspection, analysis, demonstration, test | Scenarios, user trials, exercises, experimentation |
| Who | Engineering, QA, independent verification | End users, operational test agency, capability owner |
| Failure looks like | Non-conformance report | "It meets the spec but we cannot use it" |

A system can pass every verification and fail validation when the requirement itself was written for a different mission. In defence programmes, developmental test mostly verifies and operational test mostly validates.

## 02 TRL as evidence gates

A Technology Readiness Level is defined by two fidelities: of the article tested and of the environment it was tested in. The level is only as good as the documented evidence for the transition into it.

| TRL | Short definition (EU H2020 Annex G) | Evidence to exit the level |
|---|---|---|
| 1 | Basic principles observed | Literature or experiments establishing the principle |
| 2 | Technology concept formulated | Feasibility argument, identified applications |
| 3 | Experimental proof of concept | Critical parameters measured and compared with prediction |
| 4 | Technology validated in lab | Components working together; deviations explained |
| 5 | Technology validated in relevant environment | Lab-versus-real difference analysis |
| 6 | Technology demonstrated in relevant environment | Representative prototype, all functions, statistically relevant results |
| 7 | System prototype demonstration in operational environment | Characterised envelope; production risk addressed |
| 8 | System complete and qualified | Qualification across environments; readiness review |
| 9 | Actual system proven in operational environment | In-service performance data |

TRL measures technology maturity, not manufacturability (MRL) or integration maturity (IRL), and it holds per application: the same module can be TRL 7 on one airframe and TRL 5 on another. `python -m tevv trl` prints the ladder.

The step from 6 to 7 is where most overclaiming lives, because it is the step from demonstration to characterisation.

## 03 Demonstration versus characterisation

| | Demonstration | Characterisation |
|---|---|---|
| Purpose | Show the function can work | Measure how performance varies and where it stops |
| Conditions | Chosen, usually favourable | Sampled across the envelope, including unfavourable |
| Runs | Few, often selected after the fact | Sized and selected in advance |
| Reference | Optional | Independent ground truth, time synchronised |
| Output | A result under conditions | Distributions and intervals per condition |
| Supports | Architecture claims | Specification, acceptance, commitment |

## 04 How many runs: the success-run test

With zero failures allowed, the number of consecutive successes that demonstrates reliability R at confidence C is

```
n = ln(1 − C) / ln(R)
```

| R | C | n (raw) | runs |
|---|---|---|---|
| 0.90 | 0.90 | 21.85 | 22 |
| 0.95 | 0.95 | 58.4 | 59 |
| 0.99 | 0.90 | 229.1 | 230 |

Inverted, ten clean launches demonstrate only R ≥ 0.10^(1/10) = 0.794 at 90% confidence. One failure changes the arithmetic: under the binomial model, 90%/90% with one allowed failure needs 38 runs (`--failures 1`).

## 05 Intervals for a proportion

The Wilson score interval behaves well at small n and near 0 or 1:

```
p̃ = (p̂ + z²/2n) / (1 + z²/n)
h  = z / (1 + z²/n) · sqrt( p̂(1 − p̂)/n + z²/4n² )
```

Worked example: 18 detections in 20 approaches, z = 1.96. z²/n = 0.1921, p̃ = 0.8356, h = 0.1366, so the 95% interval is **0.699 to 0.972**. "90% detection" is compatible with a true Pd below 70%. The exact Clopper-Pearson interval, 0.683 to 0.988, is wider still; the Wald interval, 0.769 to 1.000, is the one not to use.

Rule of three: after n trials with zero failures, the 95% upper bound on the failure rate is about 3/n. Thirty clean flights bound it at 10% (exact 9.5%), which is far weaker than "zero failures" sounds.

## 06 Confusion matrix, Pd, Pfa, precision, recall, F1

| | Target present | Target absent |
|---|---|---|
| Alarm | TP | FP |
| No alarm | FN | TN |

- Pd = recall = TP / (TP + FN)
- Precision = PPV = TP / (TP + FP)
- Pfa = FP / (FP + TN), per decision opportunity
- F1 = 2 · precision · recall / (precision + recall)

Object detectors usually cannot count true negatives; the package then reports Pfa as undefined rather than inventing a denominator.

## 07 Base rates and PPV

```
PPV = Pd·π / (Pd·π + Pfa·(1 − π))        FAR = Pfa · N_dec
```

With Pd = 0.95, Pfa = 0.02 and prevalence π = 1%: PPV = 0.0095 / (0.0095 + 0.0198) = **0.324**. On a balanced test set (π = 50%) the same detector has PPV 0.979. The test set flatters; the site does not. One decision per second with Pfa = 0.0001 gives 0.36 false alarms per hour; the same Pfa at a thousand candidates per second gives 360.

## 08 Accuracy as a distribution

For a circular, zero-mean bivariate normal error with per-axis σ:

```
CEP50 = σ·sqrt(2 ln 2) ≈ 1.1774 σ        R95 = σ·sqrt(−2 ln 0.05) ≈ 2.4477 σ
```

σ = 4 m gives CEP50 4.71 m and R95 9.79 m. Real errors have bias and heavy tails, so the package computes empirical percentiles of the radial error measured from truth, and reports bias separately. On the synthetic sample in `examples/nav_errors.csv` (bias plus 4% outlier fixes) R95/CEP50 is 2.34 instead of 2.08, and the maximum is three times R95.

## 09 Vendor-claim checklist

Twelve questions before a number enters a proposal, comparison or post. `tevv.check_claim` encodes the rule that if any of the first eight is unanswered, the number is a result under unstated conditions.

1. What exactly is the metric?
2. Against what target or threat configuration?
3. At what distance and geometry?
4. In what environment?
5. With which software and firmware version?
6. How much operator involvement?
7. What test method and independent reference?
8. What threshold, number of runs and confidence?
9. What were the false positives and misses?
10. Is the raw evidence available?
11. Who independently witnessed it?
12. Can the customer reproduce it on their site?

Three recurring failure patterns: condition stripping (a figure travels without its conditions), best-of selection (the headline is the best run), and title-evidence contradiction (the plot on the same page shows something else).
