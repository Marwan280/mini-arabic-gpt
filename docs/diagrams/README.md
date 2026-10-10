# Diagrams

Status: **14 of 14 drawn** (2026-10-10). The diagrams below are the ones the specifications ask for (PRD M6 and deliverable 3). Each is a Mermaid diagram stored as a `.md` file in this folder, with a sentence on what it shows, a comment under each block that cites the section each value comes from, and a "Reads with" line; each is also embedded in its source document at the point where the document first refers to it. Every block was rendered with `@mermaid-js/mermaid-cli` 12.0.0 (Mermaid 12.1.0) without a syntax error. The `xychart-beta` charts (3, 5, 6) need a Mermaid version that supports them; a renderer without it shows the source instead.

| # | Document | Diagram | What it shows | Status |
|---|---|---|---|---|
| 1 | `05` | [Model overview](01-model-overview.md) | Token and position embeddings, `L` blocks, final LayerNorm, tied head, with the tensor shape at every arrow. | done |
| 2 | `05` | [Block and attention](02-block-and-attention.md) | Pre-LN residual wiring, split into heads, the lower-triangular causal mask, MLP expansion. | done |
| 3 | `05` | [Memory against micro-batch](03-memory-against-micro-batch.md) | Peak allocated and reserved GiB against micro-batch for both attention paths, with the 7.96 GiB line and the spill cliff. | done |
| 4 | `06` | [One optimizer step](04-one-optimizer-step.md) | Sampler, micro-batches, forward under `bfloat16` autocast, loss scaling by the accumulation steps, backward, clip, AdamW, logging, with shapes and dtypes. | done |
| 5 | `06` | [Learning-rate schedule](05-learning-rate-schedule.md) | Linear warmup of 400 steps, cosine decay to 1e-4 over the whole run, with the step numbers at each vocabulary size. | done |
| 6 | `06` | [Vocabulary pilot curves](06-vocabulary-pilot-curves.md) | Validation loss per word against fraction of the pass for the four scratchpad runs, showing the crossing at 4/6. | done |
| 7 | `07` | [Evaluation pipeline and test-split discipline](07-evaluation-pipeline.md) | Validation split, checkpoint and baseline-order selection, frozen code and rubric, test split read once, report; what each step may touch. | done |
| 8 | `07` | [M2 rating workflow](08-m2-rating-workflow.md) | Prompts, generation by model and baseline, seeded shuffle with random ids, two blind sheets and a separate key, independent ratings, rates, Wilson intervals, kappa. | done |
| 9 | `08` | [Test tiers and gates](09-test-tiers-and-gates.md) | The four tiers with commands and times, and gates G1, G2, G3 on the timeline with what must pass at each. | done |
| 10 | `08` | [Bug-injection procedure](10-bug-injection-procedure.md) | Manifest entry, temporary copy, substitution, named tests, message check, DETECTED / NOT DETECTED / STALE, record for the experiment log. | done |
| 11 | `09` | [Interface layout](11-interface-layout.md) | The demo wireframe with the limitations text directly above the output and the right-to-left fields marked. | done |
| 12 | `09` | [Request flow](12-request-flow.md) | Generate click, validation, normalization and encoding, generation loop, streamed text, final status and token tables, Stop cancelling the loop. | done |
| 13 | `11` | [Timeline](13-timeline.md) | Gantt-style chart of 2026-10-11 to 2026-10-26 with the two people as rows, tasks, GPU windows, gates, checkpoints, and the two buffer days. | done |
| 14 | `11` | [Critical path](14-critical-path.md) | Dependency graph with the parallel branches joining at the production pilot and the evaluation branch joining at the M1 evaluation. | done |

Count by document: 05 × 3, 06 × 3, 07 × 2, 08 × 2, 09 × 2, 11 × 2 = 14. Documents 01 to 04 and 10 ask for none.
