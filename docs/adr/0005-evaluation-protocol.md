# ADR 0005: Evaluation protocol

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the evaluation code passes the checks of `docs/07-evaluation-plan.md` §8, the rubric has been frozen after the calibration round, and the pass rules (accepted as written by the author on 2026-10-09 and kept provisional) have been applied to the first results without needing a change |
| **Date** | 2026-10-09 |
| **Deciders** | Marwan |
| **Related** | `docs/07-evaluation-plan.md`; `docs/06-training-plan.md`; `docs/adr/0001-training-corpus.md`; `docs/adr/0002-tokenizer.md`; PRD G4, M1, M2, NG3, NG8; Design §4.5, §4.6, §9; CLAUDE.md ("Comparable metrics") |
| **Evidence** | `docs/07-evaluation-plan.md` §4, §5 and Appendix A (rehearsal with throwaway code, a 16k pilot model, and trial tokenizers; not the production pipeline) |

## Context

PRD M1 requires the model's test perplexity to be lower than an n-gram baseline with the same tokenizer and test set; M2 requires 70% of continuations to be rated grammatically acceptable MSA on a fixed prompt set. Neither says how the baseline is built, how a model with a fixed context window is scored, how much evidence is enough, or how the human rating is protected from bias. The authors are the only raters available, there is no budget for paid services, and the machine has 16 GB of RAM.

## Decision

1. **Baseline:** a token-level interpolated modified Kneser-Ney n-gram model written in numpy, trained on the full train split with a memory-aware count store (target peak under 8 GiB at order 5, fallback order 4, never less data); the order is chosen on the validation split (2 to 7, within that limit); a unigram model is the sanity floor.
2. **Metric:** negative log-likelihood per word as the primary quantity, with per-token perplexity (same tokenizer only) and bits per UTF-8 byte alongside.
3. **Scoring:** the neural model is scored with a strided window (512, stride 256) as the primary protocol and with non-overlapping windows as the secondary one.
4. **Evidence for M1:** a paired document-level bootstrap (10,000 resamples) of the baseline-minus-model difference; M1 is met if its 95% interval excludes zero under both protocols.
5. **M2 protocol:** 50 prompts (30 test-split openings, 20 hand-written), one continuation per prompt from the model and from the baseline, shuffled blind into one sheet per rater; two raters (Marwan and Ghada) label independently, 1 or 0, against a written rubric (grammatical, coherent for at least one sentence, no dialect, no script mixing) agreed in a calibration round beforehand; report each rater's acceptable rate with a Wilson interval, raw agreement, and Cohen's kappa. M2 is met if each rater accepts at least 70% of the model's continuations.
6. **Decoding for M2:** temperature 0.8, top-k 40, 80 new tokens, one sample per prompt, fixed seeds, the same procedure for the baseline; chosen on a separate development set before rating.
7. **Probes:** 10 sensitive prompts, 5 samples each, unscored. The Model Card gives a one-line description per probe and no verbatim explicit or hateful text; the full outputs are kept in a git-ignored file under `reports/`.
8. **Discipline:** the test split is evaluated once per final candidate, after the code, prompts, rubric, and settings are frozen and hashed.

Reasons:

- A hand-written Kneser-Ney model keeps the baseline inside the project's own code (no extra dependency to justify), is a strong classical baseline (Chen and Goodman), and was verified in the rehearsal (probabilities sum to 1 to 2·10⁻¹⁶).
- Per-word loss lets the vocabulary decision (`06` §7) and the M1 comparison use one metric; bits per byte follows the Pile's argument for tokenizer-independent comparison.
- A strided window removes an artificial handicap against an unbounded-context baseline: in the rehearsal the non-overlapping score was 1.0% worse than the strided one (7.2954 against 7.2218 nats per word).
- The bootstrap answers "is the difference more than noise" in the unit that is independent (the document). The rehearsal difference of 0.69 nats per word had an interval of 0.66 to 0.72.
- Blind, shuffled, two-rater labelling with a written rubric is the cheapest design that controls the main biases available to two raters who are also the authors; kappa and raw agreement show whether the rubric is applied alike.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| KenLM or another n-gram library | Not chosen | Faster and handles large corpora, but building it on Windows was not tested and it adds a dependency to document; the hand-written model's memory limits are the cost (see Consequences). Remains the fallback if the numpy version cannot reach a competitive order |
| Unigram or bigram baseline only | Rejected | Easy to beat; would make M1 weak (the rehearsal shows a bigram is 1.1 nats per word worse than a 7-gram) |
| Evaluate with non-overlapping windows only | Rejected | Handicaps the model against the baseline; kept as a secondary number for continuity with the training log |
| Point comparison without a confidence interval | Rejected | Cannot tell a real difference from noise; the production baseline is expected to get close to the pilot model (indicative extrapolation 6.8 to 7.1 nats per word) |
| A model as judge of generated text | Rejected | No independent validation for Arabic at this scale, no budget for paid services, and the judge's own biases would be unmeasured |
| One rater, 100 prompts | Rejected (author, Q2) | Tighter interval, but no agreement check |
| 30 prompts | Rejected | Wilson interval 52 to 83% at a true 70%; too wide to say whether 70% was reached |
| Rate only the model's text | Rejected | Without the baseline's text mixed in, raters know every item is the model's and calibrate against nothing |
| Rubric agreed after seeing outputs | Rejected | Allows the standard to move toward the results |
| BLEU, MAUVE, or other reference-based scores | Not used | No reference continuation exists for open-ended generation; not investigated further |
| Skip the probe set | Rejected (author, Q4) | The limitations in the Model Card would rest on prose only |
| Publish the probe outputs verbatim in the Model Card | Rejected (author) | Explicit or hateful text in a public portfolio document; the one-line descriptions keep the limitation visible |

## Consequences

**Positive**

- Every number has a definition, a protocol, an uncertainty estimate, and a test (`07` §8).
- The ratings are reproducible: frozen prompts, rubric, settings, seeds, hashes, and a stored key.
- The test split is touched once per final model.

**Negative and risks**

- **The baseline may be much stronger on the production split than in the rehearsal.** Its loss falls about 0.32 nats per word per doubling of data (order 5: 8.59, 8.24, 7.92 at 7.5M, 15M, 30M tokens); extrapolated to 328M tokens it reaches about 6.8 to 7.1, close to the pilot model's 7.2. M1 therefore depends on the main run being clearly better than the pilot; this is likely (the main run sees about 20 times more tokens) but not established.
- **The numpy baseline does not fit the full split as written.** The rehearsal implementation peaks at 4.5 to 5.5 GiB for 30M tokens; the production split is 11 times larger. A memory-aware count store is required (`07` §4.4, EV9). An arithmetic estimate on extrapolated counts puts order 4 at about 6.4 GiB and order 5 at about 9.8 GiB with a simple layout, so order 5 under the 8 GiB target needs a more compact layout and order 4 is the real fallback; neither is measured. Reducing the order costs little (orders 4 to 7 differ by 0.6%); reducing the data costs a lot, so the rule is to reduce the order, never the data. A weakened baseline makes M1 easier to pass and must be disclosed.
- **Both raters are the project's authors.** Blinding and the rubric reduce bias and do not remove it.
- **50 prompts give a wide interval** (56 to 81% at a true 70%); passing M2 does not mean the true rate is above 70%.
- **Decoding settings are untuned guesses** (temperature 0.8, top-k 40); they are checked on development prompts only.
- **Sensitive outputs are described, not published.** The reader of the Model Card cannot check the probe outputs; the full file exists only locally. A `.gitignore` entry is needed (`07` §11, item 13).
- **Refines a CLAUDE.md rule.** Per-word and per-byte metrics are compared across tokenizers (already used in `06` §7), which the rule "perplexity is only comparable between runs using the same tokenizer" does not literally allow. A clarifying sentence is proposed in `07` §11 (item 11); the author approved it for Part D and it is not yet applied.

**Changes this decision requires**

- Evaluation code, a typed evaluation config, and the baseline (after the documents are approved), with the tests of `07` §8 in `08-testing-strategy.md`.
- `reports/eval/` (committed) and the Model Card inputs.
- A `.gitignore` entry for `reports/eval/*/probes_full.md` (`07` §11, item 13).
- Edits to the PRD (M1, M2), Design (§4.5, §4.6, §9), and Data Spec §10 listed in `07` §11.

**Limits of the evidence**

- The rehearsal used a pilot model that saw 30M tokens once, trial tokenizers, and held-out documents that are not the final validation or test split.
- The discount formulas of modified Kneser-Ney came from secondary descriptions; the sum-to-one check supports the implementation but is not a proof that it matches the paper.
- The rating times and the generation settings are estimates and guesses.

## Revisit triggers

1. The production baseline's validation loss is within the bootstrap interval of the model's (M1 not met), or the two scoring protocols disagree.
2. The numpy baseline cannot reach order 4 on the full split within memory: reconsider an external library.
3. Cohen's kappa between the raters is low or the raters' acceptable rates for the model straddle 70%: revise the rubric and rerun the rating on new prompts; the first result stays on record.
4. The calibration round finds that the rubric cannot be applied alike by both raters.
5. The author decides to publish probe outputs in a different form.
