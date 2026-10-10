# Diagrams

Status: **planned, none drawn.** The 14 diagrams below are the ones the specifications ask for (PRD M6 and deliverable 3). Each is a Mermaid diagram stored as a `.md` file in this folder, named after its title, and is drawn when the component it describes is built. The source for each description is the section "Diagrams this document needs" of the document in the first column.

| # | Document | Diagram | What it shows |
|---|---|---|---|
| 1 | `05` | Model overview | Token and position embeddings, `L` blocks, final LayerNorm, tied head, with the tensor shape at every arrow. |
| 2 | `05` | Block and attention | Pre-LN residual wiring, split into heads, the lower-triangular causal mask, MLP expansion. |
| 3 | `05` | Memory against micro-batch | Peak allocated and reserved GiB against micro-batch for both attention paths, with the 7.96 GiB line and the spill cliff. |
| 4 | `06` | One optimizer step | Sampler, micro-batches, forward under `bfloat16` autocast, loss scaling by the accumulation steps, backward, clip, AdamW, logging, with shapes and dtypes. |
| 5 | `06` | Learning-rate schedule | Linear warmup of 400 steps, cosine decay to 1e-4 over the whole run, with the step numbers at each vocabulary size. |
| 6 | `06` | Vocabulary pilot curves | Validation loss per word against fraction of the pass for the four scratchpad runs, showing the crossing at 4/6. |
| 7 | `07` | Evaluation pipeline and test-split discipline | Validation split, checkpoint and baseline-order selection, frozen code and rubric, test split read once, report; what each step may touch. |
| 8 | `07` | M2 rating workflow | Prompts, generation by model and baseline, seeded shuffle with random ids, two blind sheets and a separate key, independent ratings, rates, Wilson intervals, kappa. |
| 9 | `08` | Test tiers and gates | The four tiers with commands and times, and gates G1, G2, G3 on the timeline with what must pass at each. |
| 10 | `08` | Bug-injection procedure | Manifest entry, temporary copy, substitution, named tests, message check, DETECTED / NOT DETECTED / STALE, record for the experiment log. |
| 11 | `09` | Interface layout | The demo wireframe with the limitations text directly above the output and the right-to-left fields marked. |
| 12 | `09` | Request flow | Generate click, validation, normalization and encoding, generation loop, streamed text, final status and token tables, Stop cancelling the loop. |
| 13 | `11` | Timeline | Gantt-style chart of 2026-10-11 to 2026-10-26 with the two people as rows, tasks, GPU windows, gates, checkpoints, and the two buffer days. |
| 14 | `11` | Critical path | Dependency graph with the parallel branches joining at the production pilot and the evaluation branch joining at the M1 evaluation. |

Count by document: 05 × 3, 06 × 3, 07 × 2, 08 × 2, 09 × 2, 11 × 2 = 14. Documents 01 to 04 and 10 ask for none.
