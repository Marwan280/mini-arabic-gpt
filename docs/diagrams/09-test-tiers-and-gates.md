# Test tiers and gates

The four test tiers with their markers, commands and what they need, and gates G1, G2 and G3 on the project timeline with what must pass at each; it illustrates `08-testing-strategy.md` §4.1, §4.2 and §5.2.

```mermaid
flowchart LR
    FAST["fast tier<br/>no marker (default), CPU only<br/>prototype: 63 cases in 6.1 s<br/>-m 'not slow and not gpu and not data'<br/>before every commit"]
    SLOW["slow tier<br/>marker slow, CPU, seconds<br/>-m 'slow or gpu'<br/>before training"]
    GPU["gpu tier<br/>marker gpu, CUDA, skipped otherwise<br/>-m 'slow or gpu'<br/>before training"]
    DATA["data tier<br/>marker data, needs the real data files<br/>skipped when absent<br/>part of the full run"]
    ALL["pytest (everything)<br/>before a main run"]

    FAST --> ALL
    SLOW --> ALL
    GPU --> ALL
    DATA --> ALL
```

```mermaid
flowchart LR
    G1["G1, 2026-10-20<br/>before any training run, the pilot included<br/>all tiers except data<br/>injections I-01 to I-05, I-10, I-13, I-14<br/>the inspect_data.py guard test"]
    PILOT["pilot"]
    G2["G2, 2026-10-20, after the pilot<br/>before the main run<br/>everything including data<br/>the G1 injection subset<br/>pilot gates P-a to P-d"]
    MAIN["main run"]
    G3["G3, 2026-10-23<br/>before the test split is read<br/>evaluation tests of 07 section 8<br/>injections I-11, I-12, I-15, I-16<br/>rubric and prompt files frozen and hashed"]
    TESTSPLIT["test split read once"]

    G1 --> PILOT
    PILOT --> G2
    G2 --> MAIN
    MAIN --> G3
    G3 --> TESTSPLIT
```

<!-- Sources: 08-testing-strategy.md §4.1 (tiers, markers, needs, prototype times), §4.2 (the three pytest commands), §5.2 (gates G1, G2, G3 and what must pass; G2 reduced to the G1 injection subset, Part D), 11-roadmap.md §7.1 and §8 (dates: G1 on 10-20, G2 on 10-20 after the pilot, G3 on 10-23; 2026), 06-training-plan.md §6 (pilot gates P-a to P-d). -->

Reads with: `docs/08-testing-strategy.md` §4 and §5.2, and `docs/11-roadmap.md` §8.
