# Bug-injection procedure

What the injection runner does for one manifest entry, from the temporary copy to DETECTED, NOT DETECTED or STALE; it illustrates `08-testing-strategy.md` §6.2 and §6.3.

```mermaid
flowchart TB
    ENTRY["manifest entry in tests/injections/manifest.yaml<br/>id, file, find, replace, must_fail, expect_message, must_pass"]
    COPY["copy the tracked source to a temporary directory<br/>the working tree is never modified"]
    FIND{"find occurs exactly once?"}
    SUBST["apply the substitution find to replace"]
    RUN["run the named tests in the copy"]
    FAILED{"every must_fail test failed<br/>and its message matches expect_message?"}
    PASSED{"every must_pass test still passes?"}
    DET["DETECTED"]
    NOT["NOT DETECTED"]
    STALE["STALE<br/>blocks the gate until the manifest is updated"]
    CLEAN["delete the copy"]
    OUT["write reports/injections/date.json<br/>record in the experiment log:<br/>INJ I-xx verified date at commit"]

    ENTRY --> COPY
    COPY --> FIND
    FIND -->|"no"| STALE
    FIND -->|"yes"| SUBST
    SUBST --> RUN
    RUN --> FAILED
    FAILED -->|"no"| NOT
    FAILED -->|"yes"| PASSED
    PASSED -->|"no"| NOT
    PASSED -->|"yes"| DET
    DET --> CLEAN
    NOT --> CLEAN
    STALE --> CLEAN
    CLEAN --> OUT
```

<!-- Sources: 08-testing-strategy.md §6.2 (no switches in production code; manifest and runner steps; entry fields; STALE when the anchor no longer matches; the runner prints DETECTED, NOT DETECTED or STALE and exits non-zero for the last two; results written to reports/injections/<date>.json), §6.3 (the record format "INJ I-xx verified <date> at <commit>: detected by <test id> with message"). -->

Reads with: `docs/08-testing-strategy.md` §6.2 and §6.3.
