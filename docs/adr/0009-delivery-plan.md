# ADR 0009: Delivery plan: end date, capacity, tiers, schedule rules, and roles

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the first checkpoint (C1, 2026-10-15) shows the plan is being followed (the dates of the main run were confirmed by the author on 2026-10-10) |
| **Date** | 2026-10-10 |
| **Deciders** | Marwan |
| **Related** | `docs/11-roadmap.md`; PRD §9, §10, M1 to M6; `docs/08-testing-strategy.md` §5.2; `docs/adr/0006-testing-strategy.md`; `experiments/experiment-log.md` (EXP-009) |
| **Evidence** | `docs/11-roadmap.md` §2.1, §5 and Appendix A (hour estimates by Claude, not measured; machine times measured or computed in earlier documents) |

## Context

The specifications are done (documents 01 to 11 and ADRs 0001 to 0008). The PRD fixed the end date at **2026-10-23** and mitigated the risk of a long documentation phase with a time box of 4 to 5 days; the documentation took **9 days** (2026-10-02 to 2026-10-10). Two people have 4 hours a day each and 2 days off each; all GPU work is on one laptop operated by one of them. The remaining work is the data pipeline, tokenizer, model, training, evaluation, the human rating, the local demo, and the Model Card, with a test-first rule and gates between phases.

The hour arithmetic of the roadmap showed, on the original window (12 planned days to 2026-10-22), that the tasks needed to meet the PRD's success metrics (Levels 1 and 2) were 124% of the planned hours (99% of the stated ones), and that the stretch to the main run needed 104%. This is recorded as EXP-009.

## Decision

1. **End date:** moved from 2026-10-23 to **2026-10-26** (the author, 2026-10-10: lever D). The original target, the reason (the docs phase overran; the main run must not be rushed), and the arithmetic are recorded in `11` §2.1.
2. **Capacity:** 14 planned days (2026-10-11 to 2026-10-24), 4 hours a day each, 2 days off each (spread evenly), planned at 80% of the stated hours: **76.8 planned hours** (96 stated). **2026-10-25 and 2026-10-26 are unplanned buffer days.**
3. **Scope:** Levels 1 (Tier A) and 2 (the M2 rating and the local demo, Tier B) are scheduled; Level 3 is not. Lever E (Claude Code drafting) is not assumed; if it frees time, the time goes to Level 3 in the reverse of the cut order.
4. **Tiers and cut order:** A (never cut), B (cut after C: demo polish, then the injections beyond the G1 subset), C (cut first). M1 and the main run are never cut.
5. **Schedule rules:** the main run is planned for 2026-10-20 and **starts by 2026-10-21** (the earlier rule "by 2026-10-18" carried forward with the new end date; confirmed by the author on 2026-10-10), and only after gate G1; G1 is never waived. Checkpoints C1 (10-15), C2 (10-17), and C3 (10-21) apply the cut order. Gate G2 is reduced to the G1 injection subset plus the `data` and GPU tests.
6. **Roles and machines:** README roles; all work on the project machine and on `data/` operated by Marwan; Ghada works on CPU-only parts from her own machine and pushes her own commits. Cross-writing of tests (confirmed by the author): Marwan writes the tokenizer tests (the code is Ghada's); Ghada writes the data tests and the core evaluation tests (the code is Marwan's) and takes the generation module from Marwan. The model, training, and generation tests are written by the code's author.
7. **Workflow:** short-lived branches from `main`, one pull request per component, merged only with its tests passing; the other person reviews.
8. **Part D:** one table of every proposed edit; the author marks each row; Claude applies the approved rows in one commit; `CLAUDE.md` rows are left to the author.

Reasons:

- The PRD's success metrics (M1 to M5) need Levels 1 and 2; moving the date keeps them in scope and restores a reserve (about 17% instead of the planned 20%) instead of hiding the shortfall.
- The extra three days go mainly to the stretch before the main run (the tasks due by the launch need 81% of the planned hours instead of 104%), which is what "the main run must not be rushed" requires.
- Cut triggers decided in advance avoid choosing under pressure which part of the plan to drop.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| Keep 2026-10-23 and work about 5 hours a day (lever A) | Not chosen; held as a recovery | The author preferred moving the date; lever A would add 3.1 stated hours on the new window if a checkpoint trigger fires |
| Keep 2026-10-23 and plan only Level 1 | Rejected | Leaves PRD M2 and M5 unmet |
| Keep 2026-10-23 and cut the demo and the rating to their minimum from the start (levers B and C) | Held as cut triggers | Saves about 4 hours (estimates); not enough alone |
| Plan at 100% of the stated hours | Rejected | Zero reserve; the first slip breaks every later date |
| Draft code and tests with Claude Code (lever E) | Not assumed | Allowed by CLAUDE.md only when the author asks; the saving is unmeasured |
| Run the baseline build in parallel with the main run | Rejected | Risks the 16 GB of RAM (RAM use of training not measured) |
| One person writes both a component and its tests | Rejected for the tokenizer, the data pipeline, and the core evaluation code; accepted for the model, training, and generation | Independence where the load allows; the injections of `08` §6 are the independent check for the rest |
| Let `main` take commits without pull requests | Rejected | The test-first rule needs a merge gate |

## Consequences

**Positive**

- Every task promised by documents 07 to 10 has an owner, a date, and a done criterion, or an explicit deferral.
- The cut order and the triggers are known in advance; the hour arithmetic is generated from one task table and can be recomputed at each checkpoint.
- The original target and the reason for the move are on the record (EXP-009).

**Negative and risks**

- **The reserve is thinner than planned:** Levels 1 and 2 need 79.3 hours against 76.8 planned (103%) and 96 stated (83%).
- **The hour estimates are Claude's and unmeasured** (plus or minus 50%).
- **The tail is tight:** each person ends 10-24 about 1 to 1.5 hours over the planned capacity; the buffer days absorb it.
- **The end date is later than the PRD's**; every document that states 2026-10-23 needs a consistency check (Part D).
- **The cross-writing of tests departs from the README** (testing is Ghada's); the author confirmed it.
- **Gate G2 is weaker than `08` specified;** the full injection catalog may not run.
- **The vocabulary re-confirmation on the production tokenizer is Level 3;** if it is cut, the Model Card must say the choice rests on the scratchpad pilot.

**Changes this decision requires**

- Edits to the PRD (§9 time and end date, §10 realized risk), `08` §5.2 (gate G2), the README (cross-writing), and `CLAUDE.md` ("Project" timeline and "Current phase", flagged for the author), listed in `11` §12.3; a search of every document for the old date.
- A daily record of hours spent, kept by each person, for the checkpoints.

**Limits of the evidence**

- No production code exists; the only anchor for the hour estimates is the size of the prototypes.
- The machine times of the data run (deduplication, tokenizer training) are extrapolations.
- The RAM use of training and of the baseline build on the full split was not measured.

## Revisit triggers

1. Any checkpoint trigger of `11` §8 fires.
2. The author changes the end date, the capacity, or the days off.
3. G1 is not passed by 2026-10-21.
4. The main run fails or does not meet M1: the plan has no second main run; the result is reported as it is.
