# ADR 0004: Training recipe

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the production pilot passes gates P-a to P-d of `docs/06-training-plan.md` §6 and the main run completes without the provisional settings being changed |
| **Date** | 2026-10-09 |
| **Deciders** | Marwan |
| **Related** | `docs/06-training-plan.md`; `docs/05-model-architecture.md`; `docs/adr/0003-model-architecture.md`; `docs/adr/0001-training-corpus.md` (Amendment 1); `docs/adr/0002-tokenizer.md`; PRD M3, M4, NFR3; Design §4.4, D5 |
| **Evidence** | `docs/06-training-plan.md` §4 to §7 and Appendix A (scratchpad measurements, not the production pipeline); nanoGPT configurations; Hoffmann et al. 2022; Loshchilov and Hutter 2017; Muennighoff et al. 2023 |

## Context

`docs/05-model-architecture.md` fixes the `base` model (16,967,424 parameters at the decided 16,000-entry vocabulary; 23.1M at 32,000). The corpus supplies about 328M training tokens at 16,000 entries (about 301M at 32,000; preliminary), the project GPU has 7.96 GiB, and one run must take under 6 hours (M3). The author set the run plan: one pilot, one main run of about 2 epochs, one spare, with the best-validation checkpoint kept as well as the final one. The vocabulary-size question left open by `05` was to be settled by matched short runs.

## Decision

1. **Budget:** a fixed 2 epochs over the train split; keep `ckpt_best` and `ckpt_final`.
2. **Optimizer:** AdamW (betas 0.9 and 0.95), weight decay 0.1 on tensors with two or more dimensions, none on LayerNorm, gradient clipping at 1.0, fused implementation.
3. **Schedule:** linear warmup of 400 steps, cosine decay over the whole run from 1e-3 to 1e-4.
4. **Batch:** 32,768 tokens per step (micro-batch 16 × 4 accumulation × 512).
5. **Precision:** `bfloat16` autocast, `float32` parameters and optimizer state, no gradient scaler.
6. **Sampling:** per epoch, non-overlapping windows at a random offset in random order, a pure function of (seed, epoch, step), so resume needs no sampler state.
7. **Evaluation:** full validation split every 1,000 steps, evaluation batch 8.
8. **No `torch.compile` in v1.**
9. **Run plan:** pilot (production code, about 10 minutes plus the `tiny` overfit), main run, spare.
10. **Vocabulary-size selection rule:** validation loss per word from matched short runs of `base` (same documents, same words seen, two seeds), replacing the tokens-per-word rule of `04` §10. Applied to the pilot, it selects **V = 16,000** (ADR-0002 Amendment 1); the comparison is repeated on the production tokenizer.

Reasons:

- The optimizer and schedule settings follow nanoGPT's published configurations for GPT-2 124M and for an 11M-parameter model, and Hoffmann et al.'s guidance to decay the cosine cycle by 10× over the training length. They were chosen because they are documented and widely used for models of this family, not because they were tuned.
- Compute is not the constraint: the main run is estimated at 2.4 hours at V = 16,000 (2.8 hours at 32,000), so 2 epochs fit M3 with margin and the unused budget is accepted (ADR-0001 Amendment 1).
- The loss-per-word rule compares vocabularies on what matters (modelling the same text) instead of on compression alone, which would always favour the larger vocabulary and ignores its cost in parameters and memory.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| Batch 65,536 tokens | Rejected for now | Fewer updates (about 9,200 in 2 epochs); no measurement supports it. Kept as an option if the pilot shows the noise is low |
| Batch 8,192 tokens, as in the vocabulary pilot | Fallback | Measured stable. About 4× more optimizer steps and no accumulation; the pilot gate P-d falls back to 16,384 |
| Peak learning rate 6e-4 | Fallback (spare run) | The GPT-2 124M value; slower on a small model |
| Learning-rate search | Rejected | One spare run only (author's run plan); a search needs several runs |
| Constant or linear-decay schedule | Rejected | Cosine to 10% is the documented practice; not compared here |
| `float16` with a gradient scaler | Rejected | Design D5: `bfloat16` needs no loss scaling |
| Early stopping on validation loss | Rejected (author) | Fixed 2-epoch budget with the best checkpoint also kept |
| 4 epochs or more | Rejected | Beyond the accepted 1.5 to 2 epochs; Muennighoff et al. report negligible loss change up to 4 epochs at much larger scale, unverified here |
| Weight decay without the LayerNorm exclusion, or with the embedding excluded | Not compared | Follows nanoGPT; the effect of decaying the tied embedding is unmeasured |
| `torch.compile` | Rejected for v1 | Speed is not the constraint; Windows behaviour untested |
| Selecting the vocabulary by tokens per word (`04` §10 as written) | Replaced | Chooses by compression only; with the pilot's measured gap (8.9% more tokens at 16k) it selects 32k while validation loss per word favours 16k |
| Selecting the vocabulary by a full 2-epoch run each | Not scheduled (author) | The better evidence (the pilot is in the 1.2 to 1.8 tokens per parameter regime), but 2.4 to 2.8 hours each; the author took 16,000 on the pilot evidence (`06` §7.4) |

## Consequences

**Positive**

- Every setting is a config field, logged, and re-measured by the pilot; the main run is restartable from `ckpt_latest` with exactly the same next batches.
- Same-seed runs gave bit-identical losses over 150 steps on this machine, so a regression is a real change, not noise.
- Seed-to-seed noise in validation loss per word was measured (0.013 and 0.039 nats for 32k and 16k), so a difference can be read against it.

**Negative and risks**

- **Hyperparameters are untuned.** The peak learning rate, batch size, betas, and weight decay come from reference configurations of other models; the single pilot runs that exist used 8,192 tokens per step.
- **The vocabulary evidence is from short training** (1.2 to 1.8 tokens per parameter), where a smaller model is expected to do relatively better. It may not carry over to 2 epochs on 300M tokens.
- **Epoch 2 repeats data.** Overfitting is checked by the validation curve; the spare run has the dropout fallback.
- **One spare run** covers one failure. Two independent failures exhaust the schedule.
- **Windows shared memory.** An evaluation batch of 32 reserved 8.0 GiB and would spill; the evaluation batch is fixed at 8 and reserved memory is logged.

**Changes this decision requires**

- `src/mini_arabic_gpt/train.py`, a typed training config, the sampler, and checkpoint code (after the doc is approved); tests for overfit, accumulation, determinism, resume, and the sampler (`08`).
- `04-tokenizer-spec.md` §10 and §6, `05` §12, Design §4.4, PRD M4 (proposed edits listed in `06` §11).

**Limits of the evidence**

- All measurements are from throwaway scratchpad code, one machine, and a 10% Wikipedia sample with trial tokenizers.
- Two seeds per vocabulary; no significance test.
- The nanoGPT configurations were read as code; their quality for Arabic text at this scale is not established.
- The pilot's wall-clock times were contaminated by an evaluation-memory spill; the benchmark with the real loader replaces them.

## Revisit triggers

1. The production pilot fails a gate in `06` §6.
2. The main run shows a loss spike that does not recover, a non-finite value, or validation loss rising in epoch 2.
3. The vocabulary decision on the production tokenizer disagrees with the scratchpad pilot.
4. The production pipeline's throughput differs from 60.7k (32k) or 74.6k (16k) tokens/s by more than 10%.
