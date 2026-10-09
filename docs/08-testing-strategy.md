# Testing Strategy

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Draft, pending ADR-0006 |
| **Version** | 0.1 |
| **Last updated** | 2026-10-09 |
| **Depends on** | `01-prd.md` (FR1 to FR8, NFR1 to NFR5, M3 to M5), `02-design-doc.md` §8, §9, D9, `03-data-spec.md` §8 to §10, §12, `04-tokenizer-spec.md` §2, §10, `05-model-architecture.md` §2, §9, `06-training-plan.md` §2, §8, `07-evaluation-plan.md` §2, §8, `docs/adr/0001-training-corpus.md` to `docs/adr/0005-evaluation-protocol.md` |
| **Feeds** | `09-ui-spec.md` (demo tests), `11-roadmap.md` (test-first schedule, injection runs, gates) |

## 1. Purpose and scope

This document says how the project proves that its code does what the specifications say. It lists every test that earlier documents promised, maps every requirement identifier to a test, defines the tiers in which tests run and the gates between project phases, and specifies a set of **bug-injection procedures** (§6): documented, repeatable ways to break the code on purpose and confirm that a named test notices.

The injection procedures are the core of this document. The project's main risk (PRD §10, CLAUDE.md) is a silent bug that produces plausible numbers, and a test that has never been seen failing is not evidence that it can fail.

**Status of numbers.** No production code exists yet. Every timing and every failure message below comes from a **prototype**: throwaway code in the session scratchpad that implements the components of documents 04 to 07 in miniature (a tiny GPT, the sampler, the training step, splits, strided scoring, a bootstrap, rating-sheet generation, and the trial tokenizer) plus the tests of this document and the 16 injections. It is labelled **preliminary (scratchpad, not the production pipeline)**. The prototype shows that each test can pass and that each injection is detected; it does not show that the production code will pass. Commands and outputs are in Appendix A.

**Out of scope:** the tests' source code (written test-first, after this document is approved), the Gradio interface's appearance (`09`), and the quality of the model (`07`).

## 2. Requirements

| ID | Requirement | Source |
|---|---|---|
| TS1 | Tests use pytest and add no other test dependency. | Design D9; author's decision |
| TS2 | **Test-first:** a component's tests are written from this document before or with the component, and **no component is merged unless its tests pass**. | Author's decision (Q4) |
| TS3 | Tests are organized in tiers by marker: `fast` (default), `slow`, `gpu`, `data`. The default tier runs on CPU, needs no data files, and finishes in under 60 seconds. | Author's decisions (assumptions); §4 |
| TS4 | **Traceability:** every requirement identifier in documents 01 to 07 maps to at least one named test, or is listed as documentary with the reason. A requirement with neither is a gap and blocks the phase gate. | Author's decision (Q2) |
| TS5 | **Bug injection:** each silent failure of Design §9, and each other safeguard that can fail silently, has an injection procedure that is documented, repeatable, and names the test that must fail and the message it must give. | Author's priority |
| TS6 | Every test sets or fixes its seeds, uses `tmp_path` for files it writes, opens files with `encoding="utf-8"`, and does not touch `data/`, `checkpoints/`, or the network (except tests marked `data`). | CLAUDE.md, PRD NFR1, NFR4 |
| TS7 | Failure messages name the violated invariant and the measured and expected values, so that an injection's expected message is stable and a real failure is diagnosable. | §6 |
| TS8 | Tokenizer tests use a small synthetic Arabic fixture file, reviewed by a native speaker before it is merged, plus hand-derived rule cases; tests on real documents carry the `data` marker. | Author's decision (Q3) |
| TS9 | Tests run locally. A continuous-integration workflow (GitHub Actions, CPU tests only) is added later only if time remains. | Author's decision (Q1) |

## 3. Decisions at a glance

Status: **Decided** = decided with the author (planning questions Q1 to Q4 and the injection instruction); **Provisional** = depends on a measurement named in §10.

| ID | Decision | Status | Evidence |
|---|---|---|---|
| X1 | pytest only; no Hypothesis or other new dependency; properties are checked with parametrized cases and seeded random generators | Decided | §4 |
| X2 | Markers `fast` (the default, unmarked), `slow`, `gpu`, `data`, registered and enforced with strict markers | Decided | §4 |
| X3 | Fast tier budget: under 60 s on the project machine | Provisional | §4: prototype 6.1 s for 63 cases |
| X4 | Test-first; Ghada owns the tests (README); nothing merges without its tests passing | Decided (Q4) | §5 |
| X5 | Traceability matrix instead of a coverage percentage | Decided (Q2) | §5.3 |
| X6 | Fixtures: synthetic Arabic file plus hand-derived rule table, both committed; real-data checks behind `data`; the fixture is reviewed by Marwan or Ghada (native speakers) before the tokenizer code is merged | Decided (Q3; reviewer set by the author) | §7 |
| X7 | Bug injections are exact find-and-replace anchors applied to a temporary copy by a runner, driven by a manifest (not diff patch files); production code contains no injection switches | Decided (author: anchors) | §6.2 |
| X8 | Sixteen injections specified and all sixteen detected by the prototype | Provisional (production re-run) | §6.5 |
| X9 | Exact equality for determinism tests on the project machine; `torch.testing.assert_close` with an explicit tolerance for anything else | Provisional | §4.4 |
| X10 | Local only now; CI deferred | Decided (Q1c) | §4.5 |
| X11 | Gates: G1 before any training, G2 before the main run, G3 before the test split is read | Decided | §5.2 |

## 4. Test tiers, commands, and time

### 4.1 Tiers

| Tier | Marker | Contents | Needs | Prototype time |
|---|---|---|---|---|
| fast | none (default) | shapes, mask, initialization, accumulation, determinism, resume, schedule, sampler, splits, normalization rules, round trips, metrics, statistics, sheets | CPU only | 63 cases in 6.1 s |
| slow | `slow` | single-batch overfit, end-to-end smoke on the tiny model, demo latency | CPU, seconds | CPU overfit 6.7 s |
| gpu | `gpu` | base-size mask and shape check, GPU overfit, autocast dtypes, memory budget | CUDA; skipped otherwise | base-size shapes and mask 0.95 s; GPU overfit 4.0 s |
| data | `data` | round trip on real documents, token-file bounds, memory of the baseline count store | the real data files; skipped when absent | 3 tests in 8.0 s (round trip of 600 real documents 5.1 s) |

Whole prototype suite, all tiers: 68 passed and 1 expected failure in 21.3 s. The production suite will have more tests than the prototype (91 planned, 36 prototyped; one row stands for several parametrized cases), so the fast tier is expected to grow; a plain estimate of 2 to 4 times the prototype's 6 s still leaves it under 60 s, and the budget is re-checked whenever a test is added (§9).

### 4.2 Commands

```
.venv/Scripts/python.exe -m pytest -m "not slow and not gpu and not data"   # fast tier, before every commit
.venv/Scripts/python.exe -m pytest -m "slow or gpu"                         # before training
.venv/Scripts/python.exe -m pytest                                          # everything, before a main run
```

`pytest.ini` sets `testpaths = tests` and `strict_markers = true`: pytest warns about an unregistered marker by default, and the `strict_markers` option turns that into an error ([pytest documentation, custom markers](https://docs.pytest.org/en/stable/how-to/mark.html)). `gpu` tests are skipped automatically when no CUDA device is present, and `data` tests when the data files are absent; the skip is reported, never silent.

### 4.3 Conventions

- `tmp_path` provides a fresh temporary directory for each test ([pytest documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)); no test writes elsewhere.
- Known defects are recorded with `xfail(strict=True)`: the test is expected to fail and the suite fails if it unexpectedly passes ([pytest documentation, skipping](https://docs.pytest.org/en/stable/how-to/skipping.html)). Example: the prefix-before-digits check that EXP-005 shows currently fails.
- Failure messages follow TS7 (see the messages in §6).
- A test that needs the model uses the `tiny` configuration (`05` §4.10) unless it is about the base size.

### 4.4 Determinism and tolerances

[PyTorch's reproducibility notes](https://docs.pytorch.org/docs/2.14/notes/randomness.html) state that completely reproducible results are not guaranteed across releases, commits, or platforms, nor between CPU and GPU even with identical seeds. The prototype measured the situation on this machine:

- two CPU runs with the same seed gave identical losses for 15 steps; the resumed run of the resume test is identical to the uninterrupted one;
- on the GPU, two runs with the same seed gave bit-identical losses over 150 steps (`06` Appendix A.6, explicit attention).

So determinism and resume tests demand **exact equality on the project machine**, and anything else (a different device, an SDPA-versus-explicit comparison, a different PyTorch version) uses [`torch.testing.assert_close`](https://docs.pytorch.org/docs/2.14/testing.html) with an explicit `rtol` and `atol` written in the test, derived from a measurement (for example `06` §8 and `05` §8.4: 1.6e-2 in `bfloat16`, 2.4e-6 in `float32`). A tolerance is never widened to make a test pass; a change needs a note explaining the measurement.

### 4.5 Where tests run

Local only (author's decision). The fast tier runs before every commit. A GitHub Actions workflow that runs the fast tier on CPU can be added later; it would need its own requirements file (the CPU-only PyTorch rule in CLAUDE.md is about the project machine) and is listed as a low-priority task in §11.

## 5. Process: test-first, gates, and traceability

### 5.1 Definition of done for a component

1. The component's tests are written first, from the inventory in §5.4; they fail for the right reason (a missing implementation, not a typo).
2. The component is implemented until its tests pass.
3. The fast tier passes, together with every `slow`, `gpu`, or `data` test that the component has.
4. If the component appears in the injection catalog (§6.5), its injections are run and every one is detected.
5. The commit message lists the tests added. (Commits and pushes still need the author's explicit approval, CLAUDE.md.)

**No component is merged without its tests passing** (X4). Tests are owned by Ghada (README, Contributors); this document is the contract she writes them from, so a test that cannot be written from this document is a defect in the document.

### 5.2 Gates

| Gate | When | What must pass |
|---|---|---|
| **G1** | before any training run (the pilot included) | all tiers except `data`; the injections I-01 to I-05, I-10, I-13, I-14; the existing `scripts/inspect_data.py` guard test |
| **G2** | before the main run | everything, including `data`; all sixteen injections; the pilot gates of `06` §6 (P-a to P-d) |
| **G3** | before the test split is read | the evaluation tests of `07` §8; the injections I-11, I-12, I-15, I-16; rubric and prompt files frozen and hashed |

### 5.3 Traceability

The matrix below maps every requirement identifier of documents 01 to 07 (and the tests promised by Design §8 and §9) to the tests that check it. The rule (TS4): a requirement has at least one named test, or is documentary with a reason. 70 identifiers: 66 have tests, 4 are documentary, 0 are gaps.

| Requirement | Meaning | Tests (or why none) |
|---|---|---|
| FR1 | Download, clean, deduplicate a corpus | `test_cleaning_nfc`; `test_cleaning_markup_url_removed`; `test_cleaning_whitespace`; `test_cleaning_wikipedia_trailing_sections`; `test_cleaning_language_filter`; `test_cleaning_length_filter`; `test_cleaning_nonletter_filter`; `test_every_filter_logs_its_drop_count`; `test_exact_dedup_keeps_first_occurrence`; `test_near_dedup_keeps_one_per_cluster`; `test_clean_split_files_roundtrip_documents_containing_blank_lines` |
| FR2 | Split before the tokenizer is trained | `test_dedup_runs_before_split`; `test_split_integrity_pairwise_disjoint` |
| FR3 | Tokenizer trained on the train split only | `test_tokenizer_trains_on_train_split_only` |
| FR4 | Causal next-token prediction | `test_forward_shapes`; `test_causal_mask_future_tokens_do_not_change_past_logits` |
| FR5 | Checkpoints, metrics, full config per run | `test_resume_reproduces_the_next_steps`; `test_config_and_seed_saved_with_every_checkpoint`; `test_metrics_jsonl_schema` |
| FR6 | Test perplexity for model and baseline | `test_loss_per_token_matches_hand_computation`; `test_kn_probabilities_sum_to_one` |
| FR7 | Generation with temperature and length | `test_generation_uses_only_the_last_context_length_tokens`; `test_same_seed_same_continuation`; `test_top_k_restricts_the_support`; `test_temperature_limit_matches_argmax`; `test_stops_at_endoftext_and_respects_max_new_tokens` |
| FR8 | Demo shows continuation and tokenization | `test_demo_returns_continuation_and_tokenization_for_a_prompt`; `test_demo_uses_the_same_generate_and_tokenizer_as_the_pipeline` |
| NFR1 | UTF-8 explicit everywhere | `test_clean_files_are_utf8_lf`; `test_utf8_file_io_preserves_arabic` |
| NFR2 | 10M to 30M parameters | `test_param_count_matches_formula`; `test_head_is_tied_to_embedding` |
| NFR3 | Peak training memory within 8 GB | `test_eval_batch_keeps_reserved_memory_under_budget`; `test_micro_batch_16_step_fits_in_7_gib` |
| NFR4 | Seeds set and logged | `test_split_is_deterministic_for_a_seed_and_document_level`; `test_batch_is_pure_function_of_seed_epoch_step`; `test_same_seed_gives_identical_losses` |
| NFR5 | Mask test and overfit test exist | `test_causal_mask_future_tokens_do_not_change_past_logits`; `test_overfit_single_batch_cpu` |
| M3 | Training run under 6 h and 8 GB | measured in the pilot and the main run logs (06 §6 gates); not an automated test |
| M4 | Run re-executable from config and seed | `test_same_seed_gives_identical_losses`; `test_config_and_seed_saved_with_every_checkpoint` |
| M5 | Demo answers in under 10 s | `test_demo_latency_on_cpu_under_10_seconds` (provisional target) |
| TR1 | Tokenizer trained on train only | `test_tokenizer_trains_on_train_split_only` |
| TR2 | Vocabulary at most 65,535 | `test_uint16_bound_raises_on_overflow`; `test_token_file_ids_in_bounds_one_eos_per_document` |
| TR3 | Normalization inside the tokenizer object | `test_normalization_rule`; `test_encode_applies_normalization` |
| TR4 | Every input is encodable | `test_roundtrip_and_no_unk_on_fixture`; `test_roundtrip_adversarial_strings` |
| TR5 | decode(encode(x)) equals normalize(x) | `test_roundtrip_and_no_unk_on_fixture`; `test_roundtrip_adversarial_strings`; `test_real_documents_roundtrip_no_unk` |
| TR6 | Rules in a versioned config table | `test_normalization_rule`; `test_pretokenization_rule`; `test_digits_split_in_groups_of_three_from_the_right`; `test_config_table_builds_the_pipeline_and_unknown_keys_fail` |
| TR7 | All I/O UTF-8 | `test_clean_files_are_utf8_lf`; `test_utf8_file_io_preserves_arabic` |
| MR1 | Pre-LN decoder-only GPT structure and init | `test_head_is_tied_to_embedding`; `test_init_std`; `test_initial_loss_near_ln_vocab` |
| MR2 | 10M to 30M parameters, counted | `test_param_count_matches_formula`; `test_forward_shapes_and_mask_on_gpu_at_base_size` |
| MR3 | Training fits in 8 GB | `test_micro_batch_16_step_fits_in_7_gib` |
| MR4 | No attention to later positions | `test_causal_mask_future_tokens_do_not_change_past_logits`; `test_forward_shapes_and_mask_on_gpu_at_base_size` |
| MR5 | From scratch, explicit attention | `test_explicit_attention_equals_sdpa_option` (the from-scratch rule itself is checked in review: no transformers model classes are imported) |
| MR6 | Input (B, T), output (B, T, V), ids below V | `test_forward_shapes`; `test_forward_shapes_and_mask_on_gpu_at_base_size`; `test_position_beyond_context_length_raises`; `test_token_id_at_or_above_vocab_size_raises` |
| MR7 | Shape comments in model code | `test_forward_shapes` (the shape tests cover the outputs; the comments themselves are checked in review) |
| MR8 | bfloat16 autocast, float32 parameters | `test_overfit_single_batch_gpu`; `test_dtypes_under_autocast` |
| MR9 | A tiny configuration exists | `test_end_to_end_smoke_tiny` (the tiny configuration is also what every fast model test uses) |
| MR10 | Typed config, unknown keys are an error | `test_config_unknown_keys_raise_and_vocab_matches_tokenizer` |
| TP1 | Next-token cross-entropy, targets shifted | `test_targets_are_inputs_shifted_by_one`; `test_epoch_covers_each_window_once_and_second_epoch_differs`; `test_accumulation_equals_one_large_batch` |
| TP2 | Run under 6 h and within 8 GB | `test_eval_batch_keeps_reserved_memory_under_budget`; `test_micro_batch_16_step_fits_in_7_gib` (memory part automated; time part documentary) |
| TP3 | Re-executable from config and seed | `test_batch_is_pure_function_of_seed_epoch_step`; `test_same_seed_gives_identical_losses` |
| TP4 | Train-only data for updates | `test_split_integrity_pairwise_disjoint`; `test_tokenizer_trains_on_train_split_only` (covered by the split-integrity and tokenizer-on-train-only tests) |
| TP5 | Single-batch overfit before a full run | `test_overfit_single_batch_cpu`; `test_overfit_single_batch_gpu` |
| TP6 | Seeds and full config saved | `test_same_seed_gives_identical_losses`; `test_config_and_seed_saved_with_every_checkpoint` |
| TP7 | CUDA asserted at startup | `test_training_refuses_to_run_without_cuda` |
| TP8 | Resume reproduces the next steps | `test_batch_is_pure_function_of_seed_epoch_step`; `test_resume_reproduces_the_next_steps` |
| TP9 | Metrics as JSON Lines | `test_metrics_jsonl_schema` |
| TP10 | Typed training config | `test_config_unknown_keys_raise_and_vocab_matches_tokenizer` |
| TP11 | Suspicious loss stops the run | `test_initial_loss_near_ln_vocab`; `test_non_finite_loss_stops_the_run_without_overwriting_latest`; `test_first_logged_loss_within_0_5_of_ln_vocab_or_run_stops` |
| EV1 | Model vs baseline with evidence | `test_strided_scoring_scores_every_token_exactly_once`; `test_bootstrap_is_paired`; `test_bootstrap_interval_covers_known_difference`; `test_loss_per_token_matches_hand_computation`; `test_kn_probabilities_sum_to_one` |
| EV2 | Test split used only for final evaluation | `test_test_split_requires_explicit_flag` |
| EV3 | Refuse cross-tokenizer comparison | `test_metric_comparison_refuses_different_tokenizers` |
| EV4 | Blind shuffled two-rater protocol | `test_rating_sheets_do_not_reveal_the_system` (the sheet and key mechanics are tested; the raters' behaviour is a process (calibration round)) |
| EV5 | Seeds logged, evaluation deterministic | `test_evaluation_is_deterministic`; `test_report_files_written_with_hashes_and_seeds`; `test_same_seed_same_continuation` |
| EV6 | Reports written to reports/ | `test_report_files_written_with_hashes_and_seeds` |
| EV7 | Probe outputs: summary committed, full file ignored | `test_probe_full_outputs_are_gitignored` |
| EV8 | Evaluation code verified before the test split | this inventory and the gate in 07 §7 step 1 are that verification; checked by the gate lists (§5.2) |
| EV9 | Memory-aware baseline, under 8 GiB at order 5 | `test_kn_regression_against_rehearsal_numbers`; `test_kn_count_store_peak_memory_under_8_gib` |
| DS8-1 | Design §8: causal mask test | `test_causal_mask_future_tokens_do_not_change_past_logits` |
| DS8-3 | Design §8: single-batch overfit test | `test_overfit_single_batch_cpu` |
| DS8-4 | Design §8: tokenizer round trip | `test_roundtrip_and_no_unk_on_fixture` |
| DS8-5 | Design §8: vocabulary bound test | `test_uint16_bound_raises_on_overflow` |
| DS8-6 | Design §8: split integrity test | `test_split_integrity_pairwise_disjoint` |
| DS8-7 | Design §8: checkpoint resume test | `test_resume_reproduces_the_next_steps` |
| DS8-2 | Design §8: shape tests | `test_forward_shapes` (covered by MR6 tests) |
| DS9-1 | Design §9: missing causal mask | `test_causal_mask_future_tokens_do_not_change_past_logits` |
| DS9-2 | Design §9: targets not shifted | `test_initial_loss_near_ln_vocab`; `test_targets_are_inputs_shifted_by_one`; `test_first_logged_loss_within_0_5_of_ln_vocab_or_run_stops` |
| DS9-3 | Design §9: test data leaked into training | `test_dedup_runs_before_split`; `test_split_integrity_pairwise_disjoint` |
| DS9-4 | Design §9: token ids overflow uint16 | `test_uint16_bound_raises_on_overflow`; `test_token_id_at_or_above_vocab_size_raises` |
| DS9-5 | Design §9: non-UTF-8 I/O | `test_clean_files_are_utf8_lf`; `test_utf8_file_io_preserves_arabic` |
| DS9-6 | Design §9: different normalization at training and inference | `test_encode_applies_normalization` |
| DS9-7 | Design §9: perplexity across tokenizers | `test_tokenizer_file_hash_recorded`; `test_metric_comparison_refuses_different_tokenizers` |
| DS9-8 | Design §9: training silently on CPU | `test_training_refuses_to_run_without_cuda` |
| DR2 | Licence permits training and public demo | recorded in ADR-0001 and the Data Spec |
| DR3 | Free, no account-gated source | recorded in ADR-0001 |

The four documentary rows cannot be an automated test: the 6-hour training time and the licence checks are facts about a run or a document, and EV8 is this inventory itself.

### 5.4 Test inventory

91 planned tests (parametrized cases count once). "Prototyped" means the prototype contains a version of the test and it passed on the correct code and failed under the relevant injection.

| File | Test | Tier | Prototyped |
|---|---|---|---|
| `test_data.py` | `test_cleaning_nfc` | fast | no |
| `test_data.py` | `test_cleaning_markup_url_removed` | fast | no |
| `test_data.py` | `test_cleaning_whitespace` | fast | no |
| `test_data.py` | `test_cleaning_wikipedia_trailing_sections` | fast | no |
| `test_data.py` | `test_cleaning_language_filter` | fast | no |
| `test_data.py` | `test_cleaning_length_filter` | fast | no |
| `test_data.py` | `test_cleaning_nonletter_filter` | fast | no |
| `test_data.py` | `test_cleaning_web_only_steps_not_applied_to_wikipedia` | fast | no |
| `test_data.py` | `test_every_filter_logs_its_drop_count` | fast | no |
| `test_data.py` | `test_exact_dedup_keeps_first_occurrence` | fast | no |
| `test_data.py` | `test_near_dedup_keeps_one_per_cluster` | fast | no |
| `test_data.py` | `test_dedup_runs_before_split` | fast | no |
| `test_data.py` | `test_split_integrity_pairwise_disjoint` | fast | yes |
| `test_data.py` | `test_split_is_deterministic_for_a_seed_and_document_level` | fast | no |
| `test_data.py` | `test_split_proportions_98_1_1` | fast | no |
| `test_data.py` | `test_clean_split_files_roundtrip_documents_containing_blank_lines` | fast | no |
| `test_data.py` | `test_clean_files_are_utf8_lf` | fast | no |
| `test_data.py` | `test_inspect_data_refuses_to_overwrite_filled_ratings_without_force` | fast | no |
| `test_tokenizer.py` | `test_normalization_rule[N1..N14]  (33 hand-derived cases)` | fast | yes |
| `test_tokenizer.py` | `test_pretokenization_rule[P1..P4]` | fast | no |
| `test_tokenizer.py` | `test_digits_split_in_groups_of_three_from_the_right  (P5)` | fast | yes |
| `test_tokenizer.py` | `test_prefix_before_digits_is_its_own_piece  (xfail strict, EXP-005)` | fast | yes |
| `test_tokenizer.py` | `test_encode_applies_normalization` | fast | yes |
| `test_tokenizer.py` | `test_roundtrip_and_no_unk_on_fixture` | fast | yes |
| `test_tokenizer.py` | `test_roundtrip_adversarial_strings  (empty, emoji, 10,000 characters, every character of TN §11)` | fast | no |
| `test_tokenizer.py` | `test_utf8_file_io_preserves_arabic` | fast | yes |
| `test_tokenizer.py` | `test_uint16_bound_raises_on_overflow` | fast | yes |
| `test_tokenizer.py` | `test_special_token_ids_and_byte_tokens` | fast | no |
| `test_tokenizer.py` | `test_tokenizer_trains_on_train_split_only` | fast | no |
| `test_tokenizer.py` | `test_config_table_builds_the_pipeline_and_unknown_keys_fail` | fast | no |
| `test_tokenizer.py` | `test_tokenizer_file_hash_recorded` | fast | no |
| `test_tokenizer.py` | `test_real_documents_roundtrip_no_unk  (600 documents)` | data | yes |
| `test_tokenizer.py` | `test_token_file_ids_in_bounds_one_eos_per_document` | data | yes |
| `test_tokenizer.py` | `test_tokens_per_word_recorded_and_in_range` | data | no |
| `test_model.py` | `test_forward_shapes` | fast | yes |
| `test_model.py` | `test_param_count_matches_formula` | fast | yes |
| `test_model.py` | `test_head_is_tied_to_embedding` | fast | yes |
| `test_model.py` | `test_init_std` | fast | yes |
| `test_model.py` | `test_initial_loss_near_ln_vocab` | fast | yes |
| `test_model.py` | `test_causal_mask_future_tokens_do_not_change_past_logits` | fast | yes |
| `test_model.py` | `test_uniform_model_loss_is_ln_vocab` | fast | yes |
| `test_model.py` | `test_overfit_single_batch_cpu` | slow | yes |
| `test_model.py` | `test_forward_shapes_and_mask_on_gpu_at_base_size` | gpu | yes |
| `test_model.py` | `test_overfit_single_batch_gpu` | slow+gpu | yes |
| `test_model.py` | `test_dtypes_under_autocast  (parameters float32, loss float32)` | gpu | no |
| `test_model.py` | `test_config_unknown_keys_raise_and_vocab_matches_tokenizer` | fast | no |
| `test_model.py` | `test_position_beyond_context_length_raises` | fast | no |
| `test_model.py` | `test_token_id_at_or_above_vocab_size_raises` | fast | no |
| `test_model.py` | `test_explicit_attention_equals_sdpa_option` | gpu | no |
| `test_train.py` | `test_targets_are_inputs_shifted_by_one` | fast | yes |
| `test_train.py` | `test_epoch_covers_each_window_once_and_second_epoch_differs` | fast | yes |
| `test_train.py` | `test_batch_is_pure_function_of_seed_epoch_step` | fast | yes |
| `test_train.py` | `test_accumulation_equals_one_large_batch` | fast | yes |
| `test_train.py` | `test_lr_schedule_values` | fast | yes |
| `test_train.py` | `test_same_seed_gives_identical_losses` | fast | yes |
| `test_train.py` | `test_resume_reproduces_the_next_steps` | fast | yes |
| `test_train.py` | `test_training_refuses_to_run_without_cuda` | fast | yes |
| `test_train.py` | `test_gradient_clipping_bounds_the_global_norm` | fast | no |
| `test_train.py` | `test_non_finite_loss_stops_the_run_without_overwriting_latest` | fast | no |
| `test_train.py` | `test_first_logged_loss_within_0_5_of_ln_vocab_or_run_stops` | fast | no |
| `test_train.py` | `test_config_and_seed_saved_with_every_checkpoint` | fast | no |
| `test_train.py` | `test_checkpoint_is_written_atomically` | fast | no |
| `test_train.py` | `test_metrics_jsonl_schema` | fast | no |
| `test_train.py` | `test_eval_batch_keeps_reserved_memory_under_budget` | slow+gpu | no |
| `test_train.py` | `test_micro_batch_16_step_fits_in_7_gib` | slow+gpu | no |
| `test_eval.py` | `test_strided_scoring_scores_every_token_exactly_once` | fast | yes |
| `test_eval.py` | `test_stride_equal_to_window_is_the_nonoverlapping_plan` | fast | yes |
| `test_eval.py` | `test_metric_comparison_refuses_different_tokenizers` | fast | yes |
| `test_eval.py` | `test_bootstrap_is_paired` | fast | yes |
| `test_eval.py` | `test_bootstrap_interval_covers_known_difference` | fast | yes |
| `test_eval.py` | `test_rating_sheets_do_not_reveal_the_system` | fast | yes |
| `test_eval.py` | `test_wilson_interval_known_values` | fast | yes |
| `test_eval.py` | `test_cohen_kappa_known_value` | fast | yes |
| `test_eval.py` | `test_loss_per_token_matches_hand_computation` | fast | no |
| `test_eval.py` | `test_kn_probabilities_sum_to_one` | fast | no |
| `test_eval.py` | `test_kn_beats_unigram_and_extra_order_does_not_hurt` | fast | no |
| `test_eval.py` | `test_kn_regression_against_rehearsal_numbers` | data | no |
| `test_eval.py` | `test_kn_count_store_peak_memory_under_8_gib` | slow+data | no |
| `test_eval.py` | `test_evaluation_is_deterministic` | fast | no |
| `test_eval.py` | `test_test_split_requires_explicit_flag` | fast | no |
| `test_eval.py` | `test_report_files_written_with_hashes_and_seeds` | fast | no |
| `test_eval.py` | `test_probe_full_outputs_are_gitignored` | fast | no |
| `test_pipeline.py` | `test_end_to_end_smoke_tiny  (tokenizer, token file, sampler, tiny model, 20 steps, checkpoint, evaluation)` | slow | no |
| `test_generate.py` | `test_generation_uses_only_the_last_context_length_tokens` | fast | no |
| `test_generate.py` | `test_same_seed_same_continuation` | fast | no |
| `test_generate.py` | `test_top_k_restricts_the_support` | fast | no |
| `test_generate.py` | `test_temperature_limit_matches_argmax` | fast | no |
| `test_generate.py` | `test_stops_at_endoftext_and_respects_max_new_tokens` | fast | no |
| `test_app.py` | `test_demo_returns_continuation_and_tokenization_for_a_prompt` | slow | no |
| `test_app.py` | `test_demo_uses_the_same_generate_and_tokenizer_as_the_pipeline` | fast | no |
| `test_app.py` | `test_demo_latency_on_cpu_under_10_seconds` | slow | no |

## 6. Bug-injection procedures

**The single most important result of this document: the single-batch overfit test passes with no causal mask and with unshifted targets.** CLAUDE.md names the overfit test as the check that a model and training loop are not silently broken. In the injection runs for I-01 (causal mask removed) and I-02 (targets not shifted), the CPU and GPU overfit tests both still passed: the loss went to nearly zero, because a model that can see the future, or whose targets are its inputs, memorizes a batch more easily, not less. Only the dedicated mask test and shift test (and, for I-02 with a tied head, the initial-loss test) failed. A green overfit test therefore says nothing about these two defects, which are the ones the PRD fears most; they are checked by their own tests, and each of those tests has an injection that proves it can fail (I-01, I-02).

### 6.1 Purpose

A test suite that has only ever passed proves little: the test may not be able to fail. For each way the code can go wrong silently, there is a procedure that makes it go wrong in a controlled, repeatable way and checks that a specific test fails with a specific message. This is the evidence that a safeguard works, and the experiment log refers to these procedures by their identifiers.

### 6.2 Mechanism (X7)

- **No switches in production code.** The production source never contains a "defect on" option.
- **Manifest and runner.** `tests/injections/manifest.yaml` lists the injections; a runner (`python -m tests.injections run I-01`, `run all`) does the following for each: copies the tracked source into a temporary directory (the working tree is never modified); applies the substitution; runs the named tests there; checks that each test in `must_fail` failed and that its message matches `expect_message`; checks that each test in `must_pass` still passes; deletes the copy; prints `DETECTED`, `NOT DETECTED`, or `STALE`; exits non-zero for the last two.
- **Entry format.**

```yaml
- id: I-01
  name: causal mask removed
  silent_failure: "Design §9: missing or wrong causal mask"
  file: src/mini_arabic_gpt/model.py
  find: "<the exact statement that applies the mask to the attention scores>"   # must occur exactly once, else STALE
  replace: "<the same statement without the mask>"
  must_fail:
    - tests/test_model.py::test_causal_mask_future_tokens_do_not_change_past_logits
    - tests/test_model.py::test_forward_shapes_and_mask_on_gpu_at_base_size
  expect_message: ["causal mask violated"]
  must_pass:
    - tests/test_model.py::test_overfit_single_batch_cpu    # documents what this defect does NOT trip
```

- **STALE** means the anchor no longer matches because the code changed. A stale injection blocks the gate until the manifest is updated and the injection is re-run, so the catalog cannot rot silently.
- **Results** are written to `reports/injections/<date>.json` (injection id, commit, tests failed, message, runner version).

### 6.3 Record for the experiment log

Each verification is recorded as: `INJ I-xx verified <date> at <commit>: detected by <test id> with message "<message>"`. A change to a test or to the code of a covered component requires a new record. A real escape (an injection not detected) is a log entry in the usual mistake format (what went wrong, how caught, fix).

### 6.4 Schedule

| When | What |
|---|---|
| A covered component is created or changed | its injections (definition of done, §5.1) |
| Gates G1, G2, G3 | the injections listed in §5.2 |
| After any change to a test in the catalog | that test's injections |
| After any dependency or PyTorch version change | all injections |

### 6.5 Catalog

Sixteen injections. "Run" is the prototype's whole suite (68 passing tests and one expected failure on the correct code) with the single defect active: only the listed tests failed, all others passed.

| ID | Defect injected | Silent failure | Tests that fail | Gate |
|---|---|---|---|---|
| I-01 | causal mask removed | Design §9: missing mask | mask test (CPU, tiny); mask test (GPU, base size) | G1 |
| I-02 | targets not shifted | Design §9: targets not shifted | targets-shifted test; initial-loss test | G1 |
| I-03 | loss not divided by the accumulation steps | `06` §4.2 | accumulation-equality test | G1 |
| I-04 | residual projections initialized without 1/√(2L) | `05` §4.7 | init-std test | G1 |
| I-05 | output head untied from the embedding | `05` §4.6 | parameter-count test; tied-head test; base-size GPU test | G1 |
| I-06 | no `uint16` bound check | Design §9: ids overflow | uint16-bound test | G2 |
| I-07 | file opened without `encoding="utf-8"` | Design §9: non-UTF-8 I/O | UTF-8 I/O test; fixture round trip | G2 |
| I-08 | encoder bypasses the normalizer | Design §9: different normalization | encode-applies-normalization test | G2 |
| I-09 | some test documents also in train | Design §9: leakage | split-integrity test | G2 |
| I-10 | resume does not restore the optimizer state | Design §8: resume | resume test | G1 |
| I-11 | strided scoring scores every window's targets | `07` §4.3 | strided-once test | G3 |
| I-12 | tokenizer-hash guard removed | Design §9: cross-tokenizer perplexity | tokenizer-guard test | G3 |
| I-13 | training accepts CPU silently | Design §9: silent CPU | refuses-without-CUDA test | G1 |
| I-14 | warmup off by one step | `06` §4.4 | lr-schedule test | G1 |
| I-15 | rating-sheet id leaks the system | `07` §5.4 blinding | blinding test | G3 |
| I-16 | bootstrap resamples the two systems independently | `07` §4.5 paired bootstrap | paired-bootstrap test | G3 |

### 6.6 Procedures

Each procedure gives: what to change in the production code (a description; the exact `find` text is written when the code exists), the test or tests that must fail, the expected message (the prototype's message; numbers vary), the tests that must not fail, and the prototype result. Messages are written so that the part before the first number is stable.

**I-01. Causal mask removed.**

| | |
|---|---|
| Change | In the attention forward pass, delete the statement that sets the scores of future positions to −∞ before the softmax |
| Must fail | `test_causal_mask_future_tokens_do_not_change_past_logits`; `test_forward_shapes_and_mask_on_gpu_at_base_size` |
| Expected message | `causal mask violated: logits at positions < 20 changed by 7.502e-02 when later tokens changed`; `causal mask violated at base size on GPU` |
| Must not fail | `test_overfit_single_batch_cpu` and `_gpu`: **both still pass** |
| Prototype | detected; 2 failed, 66 passed, 1 expected failure |
| Note | The overfit test passes without a mask (the model reads the answer from the future and overfits faster). The overfit test alone cannot detect this defect, which is why the mask test exists (CLAUDE.md) |

**I-02. Targets not shifted.**

| | |
|---|---|
| Change | In the batch builder, return `y = w[:, :-1]` (the inputs) instead of `w[:, 1:]` |
| Must fail | `test_targets_are_inputs_shifted_by_one`; `test_initial_loss_near_ln_vocab` |
| Expected message | `targets are not the inputs shifted by one position`; `initial loss 6.171 not within 0.5 of ln V = 6.908` |
| Must not fail | the overfit tests (**they pass**), accumulation, schedule |
| Prototype | detected; 2 failed, 66 passed, 1 expected failure |
| Note | With a tied head the model can read the current token from its own embedding, so the initial loss with unshifted targets is lower than ln V (6.17 against 6.91 at width 64). The initial-loss check therefore catches this defect for a tied model, but that is an accident of tying; the dedicated shift test is the real safeguard. The initial-loss test must use independent targets (§8, finding F2) |

**I-03. Accumulation without loss scaling.**

| | |
|---|---|
| Change | In the micro-batch loop, call `loss.backward()` on the loss without dividing by the number of accumulation steps |
| Must fail | `test_accumulation_equals_one_large_batch` |
| Expected message | `accumulated gradient differs from the large-batch gradient by 8.98e-02 (loss must be divided by the number of accumulation steps)` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-04. Residual projections not scaled.**

| | |
|---|---|
| Change | Initialize the attention and MLP output projections with standard deviation 0.02 instead of 0.02/√(2L) |
| Must fail | `test_init_std` |
| Expected message | `residual projection std 0.0201 != 0.02/sqrt(2L) = 0.0100` |
| Must not fail | the initial-loss test (it still passes) |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-05. Output head untied.**

| | |
|---|---|
| Change | Give the output head its own weight instead of sharing the embedding matrix |
| Must fail | `test_param_count_matches_formula`; `test_head_is_tied_to_embedding`; `test_forward_shapes_and_mask_on_gpu_at_base_size` |
| Expected message | `parameter count 231040 != formula 167040 (tied head expected)`; `output head must share the token-embedding matrix`; at base size `23111424 == 16967424` (an untied model at V = 16,000 has the parameter count of a tied model at V = 32,000) |
| Prototype | detected; 3 failed, 65 passed, 1 expected failure |

**I-06. No `uint16` bound check.**

| | |
|---|---|
| Change | In the encoder's conversion to `uint16`, remove the check that raises on ids above 65,535 |
| Must fail | `test_uint16_bound_raises_on_overflow` |
| Expected message | `Failed: DID NOT RAISE ValueError` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-07. File opened without `encoding="utf-8"`.**

| | |
|---|---|
| Change | In the text reader, open the file without the `encoding` argument |
| Must fail | `test_roundtrip_and_no_unk_on_fixture`; `test_utf8_file_io_preserves_arabic` |
| Expected message | `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 32: character maps to <undefined>`; `text read back differs: file was opened without encoding='utf-8'` |
| Prototype | detected; 2 failed, 66 passed, 1 expected failure |
| Note | **Platform dependent.** On this machine the default encoding is cp1252 and the defect shows; on a machine whose default is UTF-8 it would not be detected, so the injection record names the platform. The grep rule in review (`open(` without `encoding`) remains useful |

**I-08. Encoder bypasses the normalizer.**

| | |
|---|---|
| Change | In the encode path, use a tokenizer object without the normalizer (or encode raw text without calling it) |
| Must fail | `test_encode_applies_normalization` |
| Expected message | `encode(text) must equal encode(normalize(text)): the encoder is not applying the shared normalizer` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-09. Test documents also in train.**

| | |
|---|---|
| Change | In the split builder, append a few test document ids to the train list |
| Must fail | `test_split_integrity_pairwise_disjoint` |
| Expected message | `2 document(s) appear in both train and test, e.g. ['doc234', 'doc98']` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-10. Resume without the optimizer state.**

| | |
|---|---|
| Change | In checkpoint loading, skip restoring the optimizer's state |
| Must fail | `test_resume_reproduces_the_next_steps` |
| Expected message | `resumed run diverges from the uninterrupted run (max \|diff\| 3.45e-03, first at step index 11)` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |
| Note | The first resumed step still gives the same loss (the weights are restored); the divergence starts one step later, after the first update with empty moments |

**I-11. Strided scoring double counts.**

| | |
|---|---|
| Change | In the strided evaluation, score all targets of every window instead of only the not-yet-scored ones |
| Must fail | `test_strided_scoring_scores_every_token_exactly_once` |
| Expected message | `n=5000: tokens scored 1..3 times (expected exactly once); first bad index 257` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-12. Tokenizer guard removed.**

| | |
|---|---|
| Change | In the metric comparison, remove the check that the two tokenizer hashes are equal |
| Must fail | `test_metric_comparison_refuses_different_tokenizers` |
| Expected message | `Failed: DID NOT RAISE ValueError` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-13. Silent CPU fallback.**

| | |
|---|---|
| Change | In the start-up check, return instead of raising when CUDA is unavailable |
| Must fail | `test_training_refuses_to_run_without_cuda` |
| Expected message | `Failed: DID NOT RAISE RuntimeError` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-14. Warmup off by one.**

| | |
|---|---|
| Change | In the learning-rate function, use `peak * step / warmup` instead of `peak * (step + 1) / (warmup + 1)` during warmup |
| Must fail | `test_lr_schedule_values` |
| Expected message | `lr at step 0 is 0.000e+00, expected peak/(warmup+1) = 9.091e-05` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-15. Rating-sheet id leaks the system.**

| | |
|---|---|
| Change | Build item ids that contain the system name (for example `model-017`) |
| Must fail | `test_rating_sheets_do_not_reveal_the_system` |
| Expected message | `a rating sheet contains a system label (item id or other cell)` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |

**I-16. Bootstrap resamples the systems independently.**

| | |
|---|---|
| Change | In the bootstrap, draw a separate set of document indices for the second system |
| Must fail | `test_bootstrap_is_paired` |
| Expected message | `identical systems must have difference exactly 0 in every resample, got interval (-0.1255, 0.1253); resampling is not paired` |
| Prototype | detected; 1 failed, 67 passed, 1 expected failure |
| Note | The first version of this test used per-document losses with a constant ratio to the word counts, so any resample gave the same ratio and only floating-point noise made the test fail. Running the injection exposed it; the test now uses losses that vary by document. A reminder that an injection run also tests the test |

### 6.7 What running the injections showed

- **Every injection was detected, and by the intended test.** In each run only the listed tests failed.
- **Two defects are invisible to the overfit test** (I-01 and I-02), which is the test CLAUDE.md names as the check against silent failure. Both need their dedicated tests.
- **Two tests of mine were wrong on first run** and were found by running the correct code and the injections: the initial-loss test used targets equal to the inputs, which fails at baseline for a tied head (§8, F2), and the bootstrap test used degenerate data (I-16). Both are fixed in the prototype and recorded as EXP-007 in the experiment log.
- **One injection depends on the platform** (I-07).
- **Not covered by an injection yet** (candidates for later, no prototype): weight decay applied to LayerNorm parameters; gradient clipping applied before the last micro-batch; autocast wrapped around the backward pass; evaluation run in training mode; no `<|endoftext|>` between documents; a strided window that scores a token with its future in context.

## 7. Fixtures and test data

| Data | Content | Where | Reviewed by |
|---|---|---|---|
| Arabic fixture file | 31 short invented sentences (Appendix B) covering diacritics, tatweel, era markers, Arabic-Indic digits and separators, Persian letters, gaf/peh/tcheh, Latin words and parenthesized Latin, ASCII digits with commas, quotes, a tab and repeated spaces, a zero-width non-joiner, an en dash, a vulgar fraction, a date. **Invented by Claude, copied from no corpus**, so no licence question arises | `tests/fixtures/sentences_ar.txt` | **Marwan or Ghada, before the tokenizer code is merged** (task 1 of §11) |
| Rule table | 33 cases for N1 to N14: an input (with invisible characters written as escapes) and the expected output **derived by hand from `04` §4**, not by running the code | in `tests/test_tokenizer.py`; listed in Appendix B | the tokenizer-spec owner |
| Adversarial strings | the empty string, one emoji, a 10,000-character string, every special character of the tokenizer notes (TN §11) | in the test file | — |
| Synthetic token arrays | seeded random ids | generated in the test | — |
| Real documents | 600 held-out documents, the token files | `data/`, `data` marker | — |

The fixture is invented text, so it does not depend on Wikipedia's licence and can be committed (`data/` stays ignored). Invisible characters (N2, N3) are written as escapes in the rule table because a reviewer cannot see them; the fixture file does contain one zero-width non-joiner (line 22) and one tab (line 21), which the reviewer is told about.

## 8. Findings from designing and prototyping the tests

These are defects or traps found while writing the tests. None is applied to an earlier document; proposed edits are in §10.

| # | Finding | Evidence |
|---|---|---|
| F1 | **Data Spec §12 cannot store documents that contain blank lines.** The clean split files separate documents "by a blank line" (§12), but Data Spec §8 step 3 keeps up to two newlines inside a document (one blank line), so a reader cannot tell a paragraph break from a document boundary. The test `test_clean_split_files_roundtrip_documents_containing_blank_lines` would fail with the format as written. A format with an unambiguous separator is needed (for example one JSON object per line) | reasoning from the two sections; the rehearsal files of `05`/`06` already use JSON Lines |
| F2 | **An initial-loss test with targets equal to the inputs fails for a tied model:** the loss was 6.17 against ln V = 6.91 at width 64, because the output head can read the current token from the shared embedding. The test must use independent targets, as real data has | the prototype's first run |
| F3 | **EXP-005 as a test:** the prefix-before-digits check of `04` §10 fails with the rules as written; it is recorded as a strict expected failure until `04` decides which behaviour is right | prototype: `xfail(strict=True)` |
| F4 | **`scripts/inspect_data.py` has no automated tests.** Its guard that refuses to overwrite filled ratings (needed to protect the manual ratings) was only tried by hand; a test is in the inventory | the repository |
| F5 | **`pytest` is not in `requirements-dev.txt`.** Version 9.1.1 was installed into the virtual environment for the prototype only; the requirement needs a pinned entry (Design §7) | `pip list` |
| F6 | **Data Spec §10 says "shuffle document ids with a fixed seed, then slice"; the rehearsals assigned splits by a hash of the id.** The disjointness test does not depend on the method, but the determinism and proportions tests do | Data Spec §10 against `05` Appendix A.3 |
| F7 | **Same-seed GPU runs were bit-identical for 150 steps, and CPU runs for 15 steps,** so exact equality is a practical test on this machine; the PyTorch notes warn it is not portable | `06` Appendix A.6; Appendix A here |

## 9. Maintenance rules

- A test is never deleted or loosened to make a gate pass; a change comes with a note of what changed and why, and (for a test in the injection catalog) a fresh injection record.
- Skipped tests are listed in the run report. A `gpu` or `data` test skipped at a gate counts as not passed.
- The fast-tier time is printed with `--durations=10` at G1 and G2; if it exceeds 45 s, the slowest tests are moved to `slow` or made smaller before the budget of 60 s is reached.
- A flaky test is a defect: it is fixed or reported in the experiment log, not retried until it passes.
- The traceability matrix and the inventory are regenerated from one source when tests are added, so their counts cannot disagree.

## 10. Provisional decisions, open questions, and proposed edits

### 10.1 Provisional decisions and how each is confirmed

| Decision | Confirmed or changed by |
|---|---|
| Fast tier under 60 s (X3) | The first complete fast tier; printed durations at G1 and G2 |
| Exact equality for determinism on this machine (X9) | The production resume and same-seed tests; tolerance only if they fail for a measured reason |
| Sixteen injections detected (X8) | Re-running the catalog on the production code at G1, G2, and G3 |
| Expected messages | The production tests; the manifest stores the final messages |
| 91 planned tests and the matrix | Updated when the tests are written |

### 10.2 Open questions

| # | Question | Resolved in |
|---|---|---|
| 1 | ~~Who reviews the Arabic fixture, and by when?~~ **Decided:** Marwan or Ghada, before the tokenizer code is merged | Done; scheduled by `11-roadmap.md` (task 1) |
| 2 | ~~Anchor-based manifest or unified-diff patch files?~~ **Decided:** anchors (a stale anchor is reported clearly, while a patch that no longer applies is harder to diagnose) | Done (§6.2) |

### 10.3 Proposed edits to earlier documents

Not applied; listed for Part D.

| # | Document | Old | New |
|---|---|---|---|
| 1 | `03-data-spec.md` §12, `data/clean/{train,val,test}.txt` | "One document per block, documents separated by a blank line" | One JSON object per line (`id`, `text`), UTF-8, LF, as the rehearsals used; reason: Data Spec §8 step 3 keeps blank lines inside documents (finding F1). Also `data/clean/*.jsonl` in the storage table |
| 2 | `03-data-spec.md` §10, Method | "shuffle document IDs with a fixed seed (`seed: 42`), then slice" | state the method used, or the hash-of-id method if that is chosen, so that the determinism test can assert it (F6) |
| 3 | `02-design-doc.md` §8, table of required tests | seven tests | add the row "Bug-injection checks: each safeguard has a documented injection that a named test detects (`08` §6)"; D9 text: add "markers `slow`, `gpu`, `data`" |
| 4 | `01-prd.md` NFR5 | "Core components are covered by automated tests, including a causal-masking test and a single-batch overfitting test." | add "and every requirement identifier is traceable to a test or marked documentary (`08` §5.3); the safeguards against silent failures are checked by bug-injection procedures (`08` §6)" |
| 5 | `04-tokenizer-spec.md` §10, "Rule spot-checks" | "a unit test with one input and the expected output" | add "expected output derived by hand from §4/§5 (not from the code), see `08` §7" |
| 6 | `requirements-dev.txt` (outside this task's allowed edits) | no pytest | add `pytest==9.1.1` (the version used for the prototype) |
| 7 | `experiments/experiment-log.md` | — | **EXP-007 written** with the author's approval on 2026-10-09: two of my own tests were wrong on their first run (initial-loss test with unshifted-looking targets under a tied head; degenerate bootstrap data), found by running the correct code and the injections; fix: independent targets, per-document varying losses; lesson: run each test against the correct code and against its injection before trusting it |
| 8 | `01-prd.md` M6 and `02-design-doc.md` §3 (diagram count) | "14 diagrams" | running list: 3 (doc 05) + 3 (doc 06) + 2 (doc 07) + 2 (doc 08) = 10 |

## 11. Tasks handed to `11-roadmap.md`

| # | Task | Must be done before |
|---|---|---|
| 1 | Review of `tests/fixtures/sentences_ar.txt` (Appendix B) by Marwan or Ghada | the tokenizer code is merged |
| 2 | Pin `pytest` in `requirements-dev.txt` | the first test is committed |
| 3 | Write each component's tests first (inventory §5.4); Ghada owns them | the component is merged |
| 4 | Implement the injection runner and manifest, with the exact `find` anchors, once the code exists; run all sixteen | gates G1 (subset), G2, G3 |
| 5 | Add the tests for the existing `scripts/inspect_data.py` guard | the next change to that script |
| 6 | Print and review fast-tier durations at G1 and G2 | G1 |
| 7 | Optional: a CPU-only GitHub Actions workflow for the fast tier | only if time remains |

## 12. Diagrams this document needs

| Diagram | What it must show |
|---|---|
| Test tiers and gates | The four tiers with their commands and times; gates G1, G2, G3 on the project timeline with what must pass at each |
| Bug-injection procedure | Manifest entry → temporary copy → substitution → named tests run → message check → DETECTED / NOT DETECTED / STALE → record for the experiment log |

## 13. Related documents

- `01-prd.md`: FR1 to FR8, NFR1 to NFR5, M3 to M5
- `02-design-doc.md` §8, §9, D9
- `03-data-spec.md` §8 to §10, §12
- `04-tokenizer-spec.md` §10
- `05-model-architecture.md` §9
- `06-training-plan.md` §8
- `07-evaluation-plan.md` §8
- `docs/adr/0006-testing-strategy.md`: decisions of this document (proposed)
- `09-ui-spec.md`: demo behaviour that `test_app.py` checks
- `11-roadmap.md`: test-first schedule, injection runs, gates

## 14. References

- pytest: [How to mark test functions](https://docs.pytest.org/en/stable/how-to/mark.html), [skip and xfail](https://docs.pytest.org/en/stable/how-to/skipping.html), [temporary directories](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- PyTorch 2.14: [`torch.testing.assert_close`](https://docs.pytorch.org/docs/2.14/testing.html), [Reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html)
- Pages read on 2026-10-09. Automated mutation-testing tools were not evaluated (their Windows support was not checked).

## Appendix A. Measurement log

The prototype is in the session scratchpad (`proto/lib.py`, `proto/conftest.py`, `proto/tests/`, `proto/fixtures/`), not in the repository. Environment: Windows 11, Python 3.12.10, PyTorch 2.14.1+cu130, pytest 9.1.1 (installed in the virtual environment only), `tokenizers` 0.23.3. The trial 16k tokenizer of `06` §7 is the tokenizer under test. **Everything is preliminary (scratchpad, not the production pipeline).**

### A.1 Suite times

```
fast tier:        pytest -m "not slow and not gpu and not data"  -> 62 passed, 1 xfailed, 6 deselected in 6.10 s   (63 cases)
data tier:        pytest -m data                                 -> 3 passed in 8.02 s   (round trip of 600 real documents 5.07 s; jsonl read 1.77 s; token-file check 0.06 s)
everything:       pytest                                         -> 68 passed, 1 xfailed in 21.33 s
collected by marker: fast 63 | slow 2 | gpu 2 | data 3 (69 cases; the GPU overfit test carries both slow and gpu, so the markers add to 70)
slowest: CPU single-batch overfit 6.69 s | GPU single-batch overfit 3.98 s | base-size shapes and mask on GPU 0.95 s | resume 0.51 s | same-seed 0.45 s
```

### A.2 Injection runs

For each id the whole final prototype suite (69 cases) was run with `INJECT=<id>` (an environment switch inside the prototype only). All sixteen were run twice: once on the suite before the three `data` tests and the last fixture line were added (65 passing cases on the correct code), and again on the final suite. The counts below are from the final run; the first run gave the same failing tests.

```
final suite, correct code: 68 passed, 1 xfailed in 21.3 s
I-01 2 failed, 66 passed, 1 xfailed | I-02 2 failed, 66 passed | I-03 1 failed, 67 passed | I-04 1 failed | I-05 3 failed, 65 passed | I-06 1 failed | I-07 2 failed, 66 passed | I-08 1 failed
I-09 1 failed | I-10 1 failed | I-11 1 failed | I-12 1 failed | I-13 1 failed | I-14 1 failed | I-15 1 failed | I-16 1 failed      (each run 20.1 s to 21.3 s)
```

The failing tests and messages of each run are quoted in §6.6. The first run of the correct code failed one test (`test_initial_loss_near_ln_vocab`, finding F2); after the fix the correct code passed. The first I-16 run failed for the wrong reason (floating-point noise on degenerate data); after the fix it failed with an interval of (-0.1255, 0.1253).

### A.3 Traceability generator

The inventory (§5.4) and the matrix (§5.3) are produced from one Python data structure (`trace_gen.py` in the scratchpad), so the counts in the text come from it: 91 tests (fast: 76, data: 4, slow: 4, gpu: 3, slow+gpu: 3, slow+data: 1); 70 requirement identifiers; 66 with tests; 4 documentary; 0 gaps.

## Appendix B. Fixture and rule cases (draft, pending native-speaker review)

### B.1 `tests/fixtures/sentences_ar.txt` (31 lines)

Invented sentences, not taken from any corpus. A native speaker checks that each is natural Modern Standard Arabic (or deliberately unnatural where the test needs it, such as the repeated spaces) and that none contains an unintended error. Line 21 contains a tab, and line 22 a zero-width non-joiner.

```
تقع المدينة على ضفاف النهر وتعد من أقدم المدن في المنطقة.
كتب الطالب الدرس في دفتره ثم قرأه بصوت مرتفع.
مَدِينَةٌ جَمِيلَةٌ تَقَعُ عَلَى السَّاحِلِ، وَأَهْلُهَا طَيِّبُونَ.
قال المعلم: «العلم نور»، فأجاب الطالب بهدوء.
هل تعرف أين تقع الجامعة؟ نعم، تقع في وسط المدينة.
وُلد الكاتب عام 1920م وتوفي سنة 1313 هـ في مدينته الصغيرة.
وصل القطار في الساعة ٠٨:٣٠ من صباح يوم ١٥ مارس ٢٠٢٤.
بلغ عدد السكان ١٬٢٣٤ نسمة، وبلغت المساحة ٣٫٥ كيلومترا مربعا.
ارتفعت نسبة النجاح إلى 85٪ هذا العام مقارنة بالعام الماضي.
كتـاب جديد صدر عن دار النشر هذا الأسبوع.
اللغة العربية والفارسية تشتركان في كثير من الحروف، مثل «ک» و«ی» في الكتابة الفارسية.
تعلمت البرمجة بلغة Python في الجامعة.
استخدم الباحث مكتبة PyTorch لتدريب النموذج على بيانات عربية.
تأسست الشركة عام 1998 ومقرها الرئيسي في دبي (Dubai) بالإمارات.
بلغت قيمة الصفقة 1,500,000 دولار أمريكي، بحسب التقرير.
الحرب العالمية الثانية بدأت عام 1939 وانتهت عام 1945.
أعلنت الوزارة عن افتتاح ثلاث مدارس جديدة في المحافظة.
يعد ابن سينا من أبرز الأطباء والفلاسفة في العصر الإسلامي.
الماء يتكون من الهيدروجين والأكسجين، وهو ضروري للحياة.
قال: "سأذهب غدا"; ثم صمت قليلا.
هذه جملة فيها      مسافات كثيرة<TAB>وعلامة جدولة.
الاسم المركب مثل جهان‌آرا يحتوي على حرف غير واصل.
نهر النيل أطول أنهار أفريقيا، ويمر بعدة دول.
السعر 50 دولارا – أو أكثر – حسب النوع.
اشترى الرجل ½ كيلوغرام من التمر وكيلو من الرز.
الكهرباء شكل من أشكال الطاقة، تنتج من مصادر متعددة.
في عام 2010 افتتح المتحف أبوابه للزوار.
جامعة الدول العربية تأسست في القاهرة عام ١٩٤٥.
تتكون الذرة من نواة وإلكترونات تدور حولها.
أصدرت الجامعة كتابا بعنوان "مدخل إلى علم الاجتماع" هذا الشهر.
كتب الطالب كلمات مثل «گاز» و«پاکستان» و«چای» في دفتره.
```

### B.2 Rule cases (expected outputs derived by hand from `04` §4)

Invisible and ambiguous characters are written as `\uXXXX`.

| # | Rule | Input | Expected output |
|---|---|---|---|
| 1 | N1 | `\uFDF2` | `الله` |
| 2 | N1 | `\uFEFB` | `لا` |
| 3 | N1 | `a\u00A0b` | `a b` |
| 4 | N2 | `a\u200Db` | `ab` |
| 5 | N2 | `x\u200Bz` | `xz` |
| 6 | N2 | `\uFEFFabc` | `abc` |
| 7 | N3 | `جهان\u200Cآرا` | `جهانآرا` |
| 8 | N4 | `a\u0009b` | `a b` |
| 9 | N4 | `a    b` | `a b` |
| 10 | N4 | `a\u000Ab` | `a\u000Ab` |
| 11 | N5 | `کتاب فارسی` | `كتاب فارسي` |
| 12 | N6 | `گ پ چ ڤ` | `گ پ چ ڤ` |
| 13 | N7 | `ف\u064Eت\u0652ح\u064Eة\u064C` | `فتحة` |
| 14 | N7 | `أيضا\u064B` | `أيضا` |
| 15 | N7 | `ه\u064E\u0670ذ\u064Eا` | `هذا` |
| 16 | N8 | `كت\u0640اب` | `كتاب` |
| 17 | N8 | `1313 ه\u0640` | `1313 ه\u0640` |
| 18 | N9 | `٢٠٢٤` | `2024` |
| 19 | N9 | `\u06F1\u06F2\u06F3` | `123` |
| 20 | N10 | `٣\u066B١٤` | `3.14` |
| 21 | N10 | `١\u066C٠٠٠` | `1,000` |
| 22 | N11 | `كتاب, قلم` | `كتاب، قلم` |
| 23 | N11 | `ماذا?` | `ماذا؟` |
| 24 | N11 | `1,234` | `1,234` |
| 25 | N11 | `e.g., x` | `e.g., x` |
| 26 | N12 | `50\u066A` | `50%` |
| 27 | N13 | `\u201Cx\u201D` | `\u201Cx\u201D` |
| 28 | N13 | `"x"` | `"x"` |
| 29 | N14 | `a\u2013b` | `a-b` |
| 30 | N14 | `a\u2014b` | `a-b` |
| 31 | N14 | `a\u2212b` | `a-b` |
| 32 | N14 | `\u00BD` | `1/2` |
| 33 | N14 | `\u2026` | `...` |
