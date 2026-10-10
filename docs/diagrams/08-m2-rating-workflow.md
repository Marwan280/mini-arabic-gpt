# M2 rating workflow

How the 50 final prompts become two blind, shuffled rating sheets and a separate key, and how the ratings become acceptable rates, Wilson intervals and Cohen's kappa; it illustrates `07-evaluation-plan.md` §5.4 and §5.5.

```mermaid
flowchart TB
    PROMPTS["50 final prompts<br/>30 test-split openings, 20 hand-written"]
    GENM["model continuations (50)"]
    GENB["baseline continuations (50)"]
    CAL["10 calibration items<br/>5 development prompts, each with a model and a baseline continuation"]
    POOL["110 items in total<br/>100 final + 10 calibration"]
    SHUF["shuffle with a recorded seed<br/>random item ids"]
    SHA["sheet for rater A<br/>item id, prompt, continuation"]
    SHB["sheet for rater B<br/>item id, prompt, continuation"]
    KEY["key: item id to system<br/>separate file, opened only after both raters finish"]
    RATEA["rater A: acceptable 1 or 0<br/>failed criteria from G, C, D, S, note"]
    RATEB["rater B: acceptable 1 or 0<br/>failed criteria from G, C, D, S, note"]
    APPLY["apply the key"]
    ANALYSE["acceptable rate per system and per rater<br/>Wilson 95% interval<br/>raw agreement and Cohen's kappa<br/>failure breakdown by G, C, D, S"]
    RULE["M2 rule: each rater labels at least 70%<br/>of the model's 50 continuations acceptable"]

    PROMPTS --> GENM
    PROMPTS --> GENB
    GENM --> POOL
    GENB --> POOL
    CAL --> POOL
    POOL --> SHUF
    SHUF --> SHA
    SHUF --> SHB
    SHUF --> KEY
    SHA --> RATEA
    SHB --> RATEB
    RATEA --> APPLY
    RATEB --> APPLY
    KEY --> APPLY
    APPLY --> ANALYSE
    ANALYSE --> RULE
```

<!-- Sources: 07-evaluation-plan.md §5.4 (steps 1 to 6: 100 items plus 10 calibration items, shuffled with a recorded seed, random item ids, one sheet per rater, the key in a separate file, columns acceptable / failed / note, raters work separately), §5.3 (criteria G, C, D, S; calibration round of 10 items, 5 development prompts each with a model and a baseline continuation), §5.1 (50 final prompts: 30 test-split, 20 hand-written), §5.5 (Wilson 95% interval, raw agreement and Cohen's kappa, failure breakdown, M2 rule E11: each rater at least 70% of the model's 50 continuations). -->

Reads with: `docs/07-evaluation-plan.md` §5.3 to §5.5.
