# Experiment Log

## Entry template

Copy this block for each new entry. Use the next free ID. Dates are ISO (YYYY-MM-DD).

```
### EXP-NNN: <short title>

- **ID:** EXP-NNN
- **Date:** YYYY-MM-DD
- **Stage:** <pipeline stage, for example data download, tokenizer, training>
- **What happened:**
- **How it was caught:**
- **Root cause:**
- **Fix:**
- **Lesson:**
```

## Entries

### EXP-001: Shard size in the Data Spec was an unverified assumption

- **ID:** EXP-001
- **Date:** 2026-10-05
- **Stage:** Data selection (planning the corpus inspection)
- **What happened:** Data Spec §5 (v0.1) said one Parquet shard per candidate is "hundreds of MB". The FineWeb-2 shard `000_00000` is 4.84 GB (2,693,000 documents), and the 25 train shards range from 1.67 to 4.84 GB.
- **How it was caught:** By Claude while writing the inspection plan, from a read-only listing of file sizes on the Hugging Face Hub, before anything was downloaded.
- **Root cause:** The figure was an unverified assumption. It holds for the Wikipedia shards (65–408 MB), not for FineWeb-2.
- **Fix:** Data Spec §4 and §5 corrected with measured sizes. The plan was changed to download the full 4.84 GB shard, and all 7 Wikipedia shards.
- **Lesson:** Every number in a doc must cite a source or be marked as an estimate.

### EXP-002: FineWeb-2 download failed with a xet/CAS error

- **ID:** EXP-002
- **Date:** 2026-10-05
- **Stage:** Data download (FineWeb-2 shard `000_00000`)
- **What happened:** The first full run of `scripts/inspect_data.py` aborted after about 30 minutes while downloading the 4.84 GB shard, with `RuntimeError: ... CAS Client Error: Format error: I/O error: error decoding response body`. Nothing from the failed attempt was kept in the cache. The Wikipedia shards had downloaded fine.
- **How it was caught:** The script exited with a traceback. The xet log (`~/.cache/huggingface/xet/logs`) showed repeated `s3::get_range` retries with the connection flagged as struggling, then "No more retries; aborting".
- **Root cause:** Not determined. The failure was in the xet transfer path; whether the cause was the local network or the xet backend could not be established from the log.
- **Fix:** Rerun with `HF_HUB_DISABLE_XET=1` (plain HTTPS, about 2.3 MB/s). The download completed.
- **Lesson:** Record environment workarounds in CLAUDE.md and README. (CLAUDE.md updated; README not yet updated.)

### EXP-003: Generic boilerplate list gave false positives on Wikipedia

- **ID:** EXP-003
- **Date:** 2026-10-05
- **Stage:** Data inspection (quality metrics)
- **What happened:** The boilerplate phrase list, written for web text, flagged Wikipedia documents on "اقرأ أيضا" / "اقرأ أيضاً" (250 + 95 documents in the 50,000-document sample) and "مواضيع ذات صلة" (62). These are ordinary Wikipedia section headings, so they inflated Wikipedia's boilerplate rate (0.64%). A later scan of the full Wikipedia set confirmed it: for example, in 2,320 of the 2,331 documents containing "اقرأ أيضاً" the match is a standalone heading line.
- **How it was caught:** Through the per-phrase hit counts printed next to the aggregate rate in `metrics.md`.
- **Root cause:** One generic list was applied to both corpora without checking how it behaves on encyclopedic text.
- **Fix:** The boilerplate filter is web-only in Data Spec §8 (step 7), and those headings are treated as trailing sections to strip in Wikipedia (step 3a). In the post-cleaning simulation the filter removed none of the 100 Wikipedia documents.
- **Lesson:** Calibrate filters per source; always report per-item counts next to aggregate rates.

### EXP-004: Raw volume pointed to FineWeb-2; simulated cleaning reversed it

- **ID:** EXP-004
- **Date:** 2026-10-08
- **Stage:** Corpus selection
- **What happened:** The initial lean was FineWeb-2, based on raw volume and on the raw manual scores (71% clean against 40% for Wikipedia). Rating 200 documents by hand and then applying the Data Spec §8 filters to them reversed the conclusion: among the documents retained after cleaning, 94% were clean for Wikipedia and 72% for FineWeb-2. Wikipedia keeps 35 of the 100 rated documents (40% of articles in the full set) but about 78% of its raw words, and the cleaned corpus (≈214M words) is still large enough.
- **How it was caught:** By running the cleaning filters over the rated documents instead of comparing the raw numbers.
- **Root cause:** The corpora were compared before cleaning. Wikipedia's defects are structural (stubs, trailing category lines) and hid the quality of its articles, while raw size and the raw clean rate favoured FineWeb-2.
- **Fix:** Decision recorded in `docs/adr/0001-training-corpus.md`; the post-cleaning simulation added to Data Spec §7.
- **Lesson:** Raw size is misleading before cleaning; compare corpora after simulated cleaning, not before.

### EXP-005: Pre-tokenization rules P3 and P5 conflict on digits with a one-letter prefix

- **ID:** EXP-005
- **Date:** 2026-10-09
- **Stage:** Tokenizer specification (trial tokenizer for `05-model-architecture.md`)
- **What happened:** Implementing the rules of `docs/04-tokenizer-spec.md` §5 as regular expressions for a trial tokenizer showed that "و2010" becomes the pre-tokens "و2" and "010". P3 (a one-letter prefix is not split from a following digit) plus P5 (digit groups of at most three, counted from the right) attach the prefix to the first, shorter digit group. The check in §10 expects the prefix "as its own piece, not merged into the digits". Related results: "بـ59" stays one pre-token, "791هـ" stays one pre-token, "1920م" becomes "1" and "920م", "29004" becomes "29" and "004".
- **How it was caught:** By running the rules on real text (measurement), not by reading the spec; the spec reads as consistent.
- **Root cause:** Two rules were specified separately and their interaction on the same characters was not tested before writing §10's expected behaviour.
- **Fix:** Not applied at first. Two options were recorded in `05-model-architecture.md` §13 (item 5): keep the prefix with the digits and reword §10, or make the prefix its own pre-token and reword P3. **Decided on 2026-10-10 (Part D, the author): option (b), extended to the era markers.** P3 has no exceptions at all: digits are always split from letters on both sides, because the era-marker exception breaks the same way as the prefix exception (see the second case below). `04-tokenizer-spec.md` P3, the §9 configuration, and the §10 era-marker and prefix check are changed accordingly, and `adr/0002-tokenizer.md` Amendment 2 records the decision. The §10 unit tests cover prefix plus digits and the era-marker cases, with the expected pre-tokens listed there.
- **Second case (added 2026-10-10):** the era-marker exception has the same flaw. In the trial tokenizer "1920م" becomes "1" and "920م" (the marker is attached to the last digit group, so the number is split differently with and without the marker). The author's example "791هـ" → "7" + "91هـ" would arise if the marker counts toward the group width; the trial tokenizer kept "791هـ" whole (three digits), so that variant was not reproduced. With both exceptions removed, the same trial tokenizer gives "و", "2", "010" for "و2010"; "791", "هـ"; "1", "920", "م"; "1", "920", "ھ"; "بـ", "59" (scratchpad run, preliminary).
- **Lesson:** Test rule interactions on real strings when the rules are written, not only each rule alone.

### EXP-006: Evaluation batch of 32 pushed reserved GPU memory above the card's 7.96 GiB

- **ID:** EXP-006
- **Date:** 2026-10-09
- **Stage:** Training plan (vocabulary pilot, scratchpad code)
- **What happened:** The pilot script evaluated 32 sequences at a time and converted the `(B, T, V)` logits to `float32`. At V = 32,000 the evaluation peak was 5.21 GiB allocated and 8.0 GiB reserved, and the 32k training runs reserved 9.56 GiB in total, above the card's 7.96 GiB. Windows then uses shared system memory, so the wall-clock time of the pilot runs (764 s for 32k against about 440 s expected from 63k tokens/s) was not a valid throughput figure. The 16k runs reserved 5.63 GiB and were not affected.
- **How it was caught:** By the `peak reserved` line printed at the end of each run, and confirmed by a separate benchmark with the real loader that reproduced 8.0 GiB at evaluation batch 32 and 2.31 GiB at batch 8.
- **Root cause:** The memory plan covered training only. Evaluation was assumed to be cheap because it has no backward pass, but the logits and their `float32` copy dominate memory at this vocabulary size.
- **Fix:** The evaluation batch is fixed at 8 (`docs/06-training-plan.md` §4.6, §4.7) and `torch.cuda.empty_cache()` runs after each evaluation. The pilot's losses were not affected and were kept; the throughput figures come from the benchmark.
- **Lesson:** Budget memory for evaluation as well as training, and read the reserved-memory figure of every run, not only the loss.

### EXP-007: Two of the prototype tests were wrong on their first run

- **ID:** EXP-007
- **Date:** 2026-10-09
- **Stage:** Testing strategy (prototype of the tests and of the bug injections for `docs/08-testing-strategy.md`; scratchpad code)
- **What happened:** Two tests I wrote did not test what they claimed.
  1. `test_initial_loss_near_ln_vocab` used the same tensor as inputs and targets. On correct code it failed: the initial loss was 6.168 against ln 1000 = 6.908 (width 64). With a tied head, the output logit of the current token is raised by its own embedding, so targets equal to the inputs give a lower loss than ln V.
  2. `test_bootstrap_is_paired` used per-document losses with a constant ratio to the word counts, so every resample gave the same ratio. When the injection I-16 (unpaired bootstrap) was active, the test failed only through floating-point noise (interval printed as -0.0000 to 0.0000), not because the resampling was visibly unpaired.
- **How it was caught:** (1) by the first run of the suite on the correct code, which gave one failure. (2) by reading the failure message of injection I-16, which showed an interval of about zero instead of a real spread.
- **Root cause:** The tests were judged by whether they passed on correct code and failed under the injection, without checking that they failed for the intended reason, and the test data was not checked for being able to discriminate between a correct and a broken implementation.
- **Fix:** (1) the test builds its targets with the project's own batch builder on random windows (independent targets), which also lets it catch I-02 for a tied head. (2) per-document losses now vary; with I-16 the interval is (-0.1255, 0.1253). After the fixes the correct code passed (68 passed, 1 expected failure) and all 16 injections were detected by their intended tests.
- **Lesson:** Run every test against the correct code and against its injection before trusting it, and read the failure message of the injected run to confirm it shows the intended mechanism.

### EXP-008: The plan assumed free Gradio hosting on Hugging Face Spaces without checking the hosting terms

- **ID:** EXP-008
- **Date:** 2026-10-10
- **Stage:** UI specification (research for `docs/09-ui-spec.md`)
- **What happened:** The PRD (G5, M5, deliverable 5), the Design Doc (§4.7, D7: "Gradio demo on Hugging Face Spaces (CPU)", reason "free hosting"), and CLAUDE.md all assumed that a Gradio Space on the free CPU tier could host the demo. The current Hugging Face documentation, read on 2026-10-09, says that creating a Gradio or Docker Space requires a paid plan (PRO for personal accounts); the only free exception is up to two Gradio Spaces on ZeroGPU for personal accounts with a verified email and an age over 30 days. Static Spaces are free but cannot run the model server-side.
- **How it was caught:** By reading the Spaces Overview, GPU Upgrades, and ZeroGPU pages while researching the hosting section of the UI spec, before any code or deployment was attempted.
- **Root cause:** The hosting assumption was written as a fact in D7 and in the PRD without checking the platform's current terms; the project's docs-first process records decisions but did not require external service terms to be verified when a plan depends on them (compare EXP-001).
- **Fix:** v1 is a local Gradio demo (ADR-0007). Publishing on ZeroGPU is documented as an optional post-v1 step with its account conditions. The changes to PRD G5, M5, and deliverables 4 and 5, to Design D7 and §4.7, and to the README are listed in `docs/09-ui-spec.md` §12 for the consistency review; the change to CLAUDE.md is flagged for the author.
- **Lesson:** When a plan depends on an external service's terms, limits, or prices, read the current terms and cite them with the date when the decision is made, and record what was not checked.

### EXP-009: Planned 4–5 docs days became 9; caught by the hour arithmetic in doc 11

- **ID:** EXP-009
- **Date:** 2026-10-10
- **Stage:** Planning (`docs/11-roadmap.md`)
- **What happened:** The PRD's risk table (§10) mitigated the risk "documentation phase overruns and squeezes build time" with "time-box docs to 4–5 days". The documentation phase took 9 days (2026-10-02 to 2026-10-10), leaving 12 planned days to the PRD's end date of 2026-10-23. The hour arithmetic of the roadmap, run on the task list taken from documents 03 to 10, showed that Levels 1 and 2 (the tasks needed for the PRD's success metrics) needed 79.3 hours against 64.0 planned (124%) and 99% of the stated 80 hours, and that the stretch to the main run needed 104% of the planned hours.
- **How it was caught:** By computing the cumulative demand against the cumulative capacity at each due date, from the stated hours and days off of the two people, before any code was written. A first version of the arithmetic counted the buffer day in the capacity and hid the size of the problem; it was corrected before the document was shown.
- **Root cause:** The time box was a mitigation without a checkpoint date, a go or no-go rule, or an owner, so nothing forced the decision when the documentation grew. The documentation also grew in scope: each of documents 05 to 11 included research, measurements, and a throwaway prototype of its own, and nine ADRs were written. The date and the capacity were not compared until the roadmap.
- **Fix:** The end date moves from 2026-10-23 to 2026-10-26 (the author's choice, lever D), with 2026-10-25 and 2026-10-26 as buffer days; M2 and the local demo stay in scope; tiers, a cut order, and checkpoints C1 to C3 are defined (`docs/11-roadmap.md`, ADR-0009). The original target and the reason for the move are recorded in `11` §2.1.
- **Lesson:** A time box needs a checkpoint date and a rule for what happens when it is passed. Compare demand with capacity, per date and per person, when a plan is made, not when it is late; count only planned days, never the buffer.
