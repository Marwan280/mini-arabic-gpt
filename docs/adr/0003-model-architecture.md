# ADR 0003: Model architecture

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the vocabulary size is confirmed by `docs/04-tokenizer-spec.md` §10 and the first full training run (`06-training-plan.md`) completes without the provisional decisions being reversed |
| **Date** | 2026-10-09 |
| **Deciders** | Marwan |
| **Related** | `docs/05-model-architecture.md`; `docs/02-design-doc.md` §4.3, D5; `docs/adr/0001-training-corpus.md`; `docs/adr/0002-tokenizer.md`; PRD G1, NFR2, NFR3, M3 |
| **Evidence** | `docs/05-model-architecture.md` §5 to §9 and Appendix A (measurements on the project machine with a throwaway implementation) |

## Context

The Design Doc (§4.3) fixed a decoder-only transformer and deferred the size, context length, positional encoding, weight tying, and dropout to the model specification. The constraints are 10M to 30M parameters (NFR2), 8 GB of VRAM (NFR3), a training run under 6 hours (M3), and about 328M training tokens of cleaned Wikipedia at the decided vocabulary of 16,000 entries (preliminary: 1.6073 tokens per word on a trial tokenizer; about 301M at 32,000 entries with 1.4755, `05` §6).

## Decision

1. **Size class `base`:** 6 layers, width 384, 6 heads (head size 64), MLP width 1,536; 16,967,424 parameters at the decided 16,000-entry vocabulary (23,111,424 at 32,000, the first-draft vocabulary; ADR-0002 Amendment 1).
2. **Context length 512.**
3. **Learned absolute position embeddings.**
4. **Output head tied to the token embedding.**
5. **Attention written explicitly with an explicit causal mask** for v1. The fused `scaled_dot_product_attention` path is a tested option behind a config field, not the default.
6. **Pre-LayerNorm blocks, GELU 4× MLP, no bias in `Linear`, dropout 0.0 (provisional), GPT-2 style initialization** (N(0, 0.02); residual projections scaled by 1/√(2L)).
7. **`bfloat16` autocast with `float32` parameters and optimizer state.**
8. **Two configurations:** `base` and `tiny` (2 layers, width 128, 4,506,880 parameters) for the smoke test.

Reasons:

- `base` equals the nanoGPT "baby GPT" depth and width and the GPT-2 head size. It leaves room under NFR2 (a vocabulary up to 48,000 still fits, 29.26M parameters), and a 20-tokens-per-parameter run needs 1.53 epochs of the supply, inside the 1 to 2 epochs accepted as a guideline (`05` §6.3).
- Compute is not the constraint: 2 epochs take an estimated 2.66 hours (measured 63k tokens/s, explicit attention), well under M3. Data supply is.
- Tying is required, not optional: untied the model has 35,399,424 parameters.
- The explicit attention is the specification that the causal-mask test targets (CLAUDE.md), and costs 0.83 GiB at micro-batch 16 and 36% less throughput than the fused path (measured), which still fits the budget.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| 8 layers × 256 width (14.6M) | Rejected | Fits easily and needs only 0.97 epochs, but the author preferred the nanoGPT-reference shape with more width; no experiment compared them |
| 6 × 320 (17.8M) | Rejected | Same as above; 5 heads of 64 is valid but not a reference configuration |
| 8 × 384 (26.7M, at 32,000) | Rejected | 1.77 epochs for 20 tokens/param; closer to the 30M limit, so a larger vocabulary (48k) would break NFR2 (≈32.8M) |
| 12 × 384 (33.7M) | Rejected | Over NFR2 |
| Untied embedding and head | Rejected | 35.40M parameters at 32,000, over NFR2; at the decided 16,000 it would be 23.11M, inside NFR2, so the limit no longer forces tying (`05` §4.6). Tying is kept for the 6.14M parameters it saves and the nanoGPT/GPT-2 convention |
| Rotary position embeddings (RoPE) | Deferred as a future extension | No extra parameters and not tied to a maximum length, but more code and more silent-bug surface (Design P1). Not compared empirically |
| Context 256 / 1,024 | Rejected | 256 covers about 40% of a mean article; 1,024 quadruples attention-score memory and slows CPU generation |
| Fused attention (`scaled_dot_product_attention`) as default | Deferred as option (c) | Numerically equal (max gradient difference 1.7e-8), 56% faster, 0.83 GiB less at micro-batch 16. Kept behind `attention: sdpa` if the schedule needs the speed |
| Bias in `Linear`; dropout 0.1; document-masked attention | Rejected for v1 | Not needed for correctness; dropout is reconsidered if validation loss diverges in epoch 2 |

## Consequences

**Positive**

- Every parameter count and memory figure was measured on the project machine, and the mask, initial loss, and single-batch overfit were checked before any real code exists.
- The design leaves 2.3 GiB of VRAM headroom at micro-batch 16.

**Negative and risks**

- **The embedding matrix is 53.2% of the parameters.** The non-embedding model is 10.6M, so quality may be closer to a 10M model than to a 23M one.
- **Logits dominate activation memory** (about 3.1 GiB of 4.79 GiB at micro-batch 16), so memory depends strongly on the vocabulary size (0.096 GiB per 1,000 entries).
- **Learned positions cannot represent positions past 512.**
- **Cross-document windows** let some positions attend to an unrelated previous document; accepted.
- **Repeating data for up to 2 epochs** rests on Muennighoff et al., measured at larger scale; it is verified by the validation curve, not assumed.
- **The size was not chosen by experiment.** It is a reference-based judgement.
- **The token supply is preliminary** and below the Data Spec's estimate; ADR-0001's first revisit trigger is met by the preliminary measurement; the corpus was not reopened (ADR-0001, Amendment 1).

**Changes this decision requires**

- `src/mini_arabic_gpt/model.py` and a typed model config; `tests/` for shape, mask, initialization, parameter count, and overfit (`08`).
- `06-training-plan.md` takes parameter count, FLOPs per token (151,644,672), and the memory table as inputs.

**Limits of the evidence**

- Throughput was measured on random data without a data loader, while a CPU job ran in the background.
- The GPT-2 paper text could not be read in this session; GPT-2 facts come from the released configuration and nanoGPT's code.
- Tokens per word comes from a trial tokenizer trained on 8.7% of the corpus's words with approximated normalization.

## Revisit triggers

1. The real tokenizer's vocabulary differs from 16,000 (the decided value; the repeat of the matched comparison on the production tokenizer, `04` §10, may reopen it): recompute `05` §5 and §8.2.
2. Validation loss rises while training loss falls in epoch 2: set dropout to 0.1 or reduce epochs.
3. The first full run does not reach the M1/M2 targets: reconsider the size class or RoPE.
4. Measured tokens per word makes the supply less than 1 epoch at 20 tokens/param for `base`: revisit ADR-0001.
