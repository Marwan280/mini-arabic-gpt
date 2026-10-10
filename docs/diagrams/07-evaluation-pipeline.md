# Evaluation pipeline and test-split discipline

The order of operations of the evaluation and which split each step may touch: everything is chosen on the validation split, the evaluation items are frozen, and the test split is scored once; it illustrates `07-evaluation-plan.md` §7 (with the scoring of §4.3).

```mermaid
flowchart TB
    FREEZE["1. Freeze<br/>evaluation code, prompt files, rubric, decoding settings<br/>record their hashes, run the checks of section 8"]
    SELECT["2. Select on the validation split only<br/>checkpoint (ckpt_best or ckpt_final)<br/>baseline order (2 to 7)"]
    GEN["3. Generate final continuations and probe outputs<br/>50 prompts: 30 test-split openings, 20 hand-written<br/>model and baseline, 1 sample each, seed 1000 + prompt index"]
    RATE["3. Rate (M2)<br/>blind, shuffled, two raters"]
    G3{{"gate G3<br/>evaluation tests pass<br/>config and prompts frozen and hashed"}}
    M1["4. Evaluate M1 on the test split, once per final candidate<br/>strided window 512, stride 256 (primary)<br/>non-overlapping windows of 512 also reported"]
    REPORT["5. Write reports/eval/<br/>propose an experiment-log entry"]
    DEV["validation split"]
    TEST["test split"]

    FREEZE --> SELECT
    DEV -->|"read"| SELECT
    SELECT --> GEN
    TEST -->|"openings used as prompts, no tuning"| GEN
    GEN --> RATE
    RATE --> G3
    G3 --> M1
    TEST -->|"scored once"| M1
    M1 --> REPORT
```

<!-- Sources: 07-evaluation-plan.md §7 (steps 1 to 5 and the rule that anything found after step 4 is reported as a deviation), §2 EV2 (test split never used for tuning, choosing a checkpoint, the baseline's order, or decoding settings), §4.3 (strided protocol 512 / 256 primary, non-overlapping 512 also computed), §4.4 (baseline order chosen on validation among 2 to 7), §5.1 (50 final prompts: 30 from the test split, 20 hand-written), §5.2 (seed 1000 + prompt index, 1 sample per prompt), 08-testing-strategy.md §5.2 (gate G3: before the test split is read), 11-roadmap.md §8 (G3 on 2026-10-23). -->

Reads with: `docs/07-evaluation-plan.md` §7, §4.3 and §5.1.
