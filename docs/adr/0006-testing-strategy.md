# ADR 0006: Testing strategy

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the production injection runner reproduces the detections of `docs/08-testing-strategy.md` §6 on the real code (gate G1) and the traceability matrix has no gaps |
| **Date** | 2026-10-09 |
| **Deciders** | Marwan |
| **Related** | `docs/08-testing-strategy.md`; `docs/02-design-doc.md` §8, §9, D9; `docs/05-model-architecture.md` §9; `docs/06-training-plan.md` §8; `docs/07-evaluation-plan.md` §8; PRD NFR5, §10; CLAUDE.md ("ML correctness rules") |
| **Evidence** | `docs/08-testing-strategy.md` §4, §6 and Appendix A (a prototype in the session scratchpad: 69 test cases, 16 injections; not the production code) |

## Context

The project's dominant risk is a bug that raises no error and produces plausible numbers: a missing causal mask, targets that are not shifted, leakage between splits, a normalizer that is skipped on one code path. The PRD requires a mask test and an overfit test (NFR5); the later documents promised many more checks. There are 14 days left, one GPU machine, no budget for paid services, and the tests are to be written test-first with a native-speaker review of the Arabic fixtures.

## Decision

1. **pytest only**, with no other test dependency.
2. **Test-first, and no component is merged without its tests passing.** Ghada owns the tests.
3. **Four tiers by marker:** fast (default, CPU, under 60 s), `slow`, `gpu`, `data`; strict markers; skips are reported.
4. **Traceability instead of a coverage percentage:** every requirement identifier maps to a named test or is documentary with a reason; a requirement with neither is a gap that blocks the phase gate.
5. **Fixtures:** a small invented Arabic file plus a rule table whose expected outputs are derived by hand from the specification; real-data checks behind `data`; review of the Arabic file by Marwan or Ghada before the tokenizer code is merged.
6. **Bug injection as a first-class part of the test suite:** sixteen documented injections, each an exact find-and-replace anchor (not a diff patch) applied to a temporary copy by a runner driven by a manifest, with the test that must fail and the message it must give; production code has no injection switches. Results are recorded by identifier in the experiment log.
7. **Determinism:** exact equality on the project machine, `torch.testing.assert_close` with an explicit tolerance elsewhere.
8. **Gates:** G1 before any training, G2 before the main run, G3 before the test split is read.
9. **Local only** for now; a CPU workflow in GitHub Actions only if time remains.

Reasons:

- A test that has never been seen failing is weak evidence. In the prototype, running the injections found two defects in my own tests (an initial-loss test that failed on correct code for a tied head, and a bootstrap test that detected the injection only through floating-point noise), and showed that the overfit test passes under two of the most dangerous defects (missing mask, unshifted targets).
- A coverage percentage measures lines executed, not whether a safeguard can fail; the traceability matrix measures whether each stated requirement is checked.
- Expected outputs derived by hand from the specification keep the tokenizer tests independent of the code under test.
- A manifest and runner keep injection logic out of production code and make a stale injection visible.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| Line-coverage target (for example 80%, `pytest-cov`) | Rejected (author, Q2) | Counts executed lines, not detected defects; in the prototype I-01 and I-02 pass the overfit test even though every line involved is executed |
| Both traceability and coverage | Rejected (author, Q2) | Extra dependency and a number to defend, without extra evidence of detection |
| Hypothesis (property-based testing) | Rejected | A new dependency; the properties needed are covered by parametrized cases and seeded generators |
| `unittest` | Rejected | Design D9 chose pytest (simpler syntax, markers, parametrization) |
| Injection switches (an environment variable) inside production code | Rejected | Defect code in production; a switch left on is itself a silent failure. (The prototype used switches only because it is throwaway code.) |
| Automated mutation testing (a tool that mutates code at random) | Not evaluated | Windows support and run time were not checked; the catalog targets the failures the project actually fears |
| Golden-file tests whose expected output is produced by the code | Rejected | Circular: they pass whatever the code does |
| Fixtures from the Wikipedia sample | Rejected for the default tier | Needs `data/`, and committing real text raises the licence question; kept for the `data` tier |
| Tests after the code | Rejected (author, Q4) | Defects found late; the tests would be shaped by the implementation |
| CI from the start | Deferred (author, Q1) | Cost of setting it up against 14 days; local runs suffice for a two-person project |

## Consequences

**Positive**

- Each documented silent failure has a repeatable procedure showing that a test notices it.
- The suite stays fast enough to run before every commit (prototype: 6.1 s for 63 cases; 21.3 s for all 69).
- The matrix shows at a glance what is not tested.

**Negative and risks**

- **Cost against the schedule.** 91 planned tests and 16 injections are a large share of 14 days; test-first adds effort per component. The gates are staged (G1 needs only a subset of injections) to keep the early cost low.
- **Injections can go stale** when the code changes; the runner reports STALE and blocks the gate, which costs time.
- **The prototype is not the production code.** All 16 injections were detected in the prototype; the production run may find escapes.
- **One injection depends on the platform** (I-07 shows only where the default encoding is not UTF-8).
- **Exact-equality determinism is not portable** (PyTorch's own notes); a test that passes here may need a tolerance elsewhere.
- **The Arabic fixture is invented and AI-written;** its quality depends on the review by Marwan or Ghada before the tokenizer code is merged, which is a task on the roadmap.
- **pytest is not yet in `requirements-dev.txt`.**

**Changes this decision requires**

- `tests/` with `conftest.py`, `pytest.ini` (`testpaths`, `strict_markers`), `tests/fixtures/sentences_ar.txt`, and `tests/injections/` (manifest and runner), after the documents are approved.
- `pytest==9.1.1` (or the then-current pinned version) in `requirements-dev.txt`.
- Edits to the Data Spec §12 and §10, Design §8 and D9, PRD NFR5, and the tokenizer spec §10 listed in `08` §10.3.

**Limits of the evidence**

- 36 of the 91 planned tests were prototyped.
- Timings are for the prototype on one machine.
- The expected messages are the prototype's; the production messages will be set when the tests are written.
- The traceability matrix covers the identifiers of documents 01 to 07; documents 09 to 11 will add rows.

## Revisit triggers

1. An injection escapes in the production code: fix the test, record it in the experiment log, and review the other tests of that component.
2. The fast tier exceeds 45 s.
3. The injection manifest costs more than a few minutes per gate to maintain.
4. A real bug is found that no injection or test would have caught: add a test and an injection for it.

## Amendment 1 (2026-10-10): demo tests and two injections

*The text above is unchanged. Where it says 91 planned tests and sixteen injections, read this amendment instead; the status stays Proposed.*

Part D of the specification work (the author approved the additions on 2026-10-10) replaced the three demo tests of `docs/08-testing-strategy.md` by the 14 tests of `docs/09-ui-spec.md` §8, so the plan has **102 tests**, and added **I-17** (limitations text removed or placed below the output) and **I-18** (telemetry left at the default) to the catalog: **eighteen injections**, of which sixteen were run in the prototype and two are not yet run. Gate G2 is reduced to the G1 injection subset (I-01 to I-05, I-10, I-13, I-14) plus the `data` and GPU tests, as decided in `docs/11-roadmap.md` (ADR-0009); the other injections run when capacity allows.
