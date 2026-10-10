# Model Architecture Spec

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Draft, pending ADR-0003 |
| **Version** | 0.1 |
| **Last updated** | 2026-10-10 |
| **Depends on** | `01-prd.md` (G1, G3, NFR2, NFR3, M3), `02-design-doc.md` §4.3 and D5, `03-data-spec.md` §3 and §10, `04-tokenizer-spec.md` §6 and §7, `docs/adr/0001-training-corpus.md`, `docs/adr/0002-tokenizer.md` |
| **Feeds** | `06-training-plan.md` (parameter count, FLOPs per token, memory per micro-batch), `07-evaluation-plan.md` (context length), `08-testing-strategy.md` (shape, mask, and initialization tests), `09-ui-spec.md` (context length, model size) |

## 1. Purpose

This document specifies the model: its tensors and shapes, layers and sizes, initialization, numeric precision, and the memory and compute it needs on the project machine. It fixes the choices that `02-design-doc.md` §4.3 deferred: number of layers, heads, and embedding size; context length; positional encoding; weight tying; dropout.

It does **not** set training hyperparameters (batch size, learning rate, schedule, steps). Those belong to `06-training-plan.md`, which takes the parameter count, FLOPs per token, and memory per micro-batch from this document.

**Conventions.** Shapes are annotated in code as `# (B, T, C)`.

| Symbol | Meaning | Value (`base`) |
|---|---|---|
| `B` | micro-batch size (sequences) | set in 06 |
| `T` | sequence length, at most the context length | 512 |
| `C` | model width (`d_model`) | 384 |
| `H` | attention heads | 6 |
| `d_head` | `C / H` | 64 |
| `L` | transformer blocks (`n_layer`) | 6 |
| `V` | vocabulary size, from the tokenizer (`04` §6) | 16,000 (decided, ADR-0002 Amendment 1; provisional until `04` §10 is repeated on the production tokenizer). 32,000 in the first draft of this document |
| `N` | total parameters | 16,967,424 (23,111,424 at `V` = 32,000) |

**How the numbers were obtained.** Several values below are measured, not estimated: parameter counts, initial loss, mask behaviour, memory, and throughput come from a throwaway implementation of this spec run on the project machine (§9, Appendix A). That code lives in the session scratchpad, not in the repository; the real model (`src/mini_arabic_gpt/model.py`) is written later against this document and the tests in `08-testing-strategy.md`.

## 2. Requirements

| ID | Requirement | Source |
|---|---|---|
| MR1 | Decoder-only transformer of the GPT family: token embedding plus position information, `L` blocks with causal multi-head self-attention and an MLP, pre-layer normalization, residual connections, final layer normalization, linear output head. | Design §4.3 |
| MR2 | Total parameters between 10M and 30M. The exact count is given by a formula and confirmed by counting. | PRD NFR2 |
| MR3 | Training fits in 8 GB of VRAM. Measured against the dedicated memory (7.96 GiB), not the shared-memory figure Task Manager shows. | PRD NFR3, CLAUDE.md |
| MR4 | A position never attends to a later position. Proven by a test, not assumed. | Design §4.3, §8; CLAUDE.md |
| MR5 | Written from scratch with PyTorch primitives; no pretrained weights; no `transformers` model classes. The attention computation is written explicitly. | PRD NG5, G1 |
| MR6 | Input: token IDs `(B, T)`; output: logits `(B, T, V)`. `V` comes from the tokenizer; every input ID is below `V`. | Design §4.3 |
| MR7 | Tensor shapes are annotated in comments in all model code. | CLAUDE.md |
| MR8 | `bfloat16` autocast with `float32` parameters. | Design D5 |
| MR9 | A tiny configuration exists for the end-to-end smoke test before scaling up. | Design P5 |
| MR10 | Every architecture setting is a field of a typed config; unknown keys are an error. | Design §7 |

## 3. Decisions at a glance

Status: **Fixed** = set by an earlier document; **Decided** = decided here (with the author's agreement); **Provisional** = depends on a later measurement (§11).

| ID | Decision | Status | Evidence |
|---|---|---|---|
| A1 | Decoder-only GPT, pre-LN, residual connections | Fixed | Design §4.3 |
| A2 | `L` = 6, `C` = 384, `H` = 6, `d_head` = 64, MLP width `4C` = 1,536 | Decided | §5, §6, reference points below |
| A3 | Context length `T` = 512 | Decided | §7 |
| A4 | Learned absolute position embeddings | Decided | §4.5 |
| A5 | Output head tied to the token embedding | Decided | §4.6: untied would be 35.40M, over NFR2 |
| A6 | No bias in `Linear` layers; `LayerNorm` with weight and bias | Decided | §4.2 |
| A7 | GELU activation, MLP expansion 4× | Decided | reference points below |
| A8 | Dropout 0.0 | Provisional | §6, §11 |
| A9 | Initialization: N(0, 0.02); residual projections N(0, 0.02/√(2L)) | Decided | §4.7 |
| A10 | Attention written explicitly with an explicit mask; `scaled_dot_product_attention` kept as a tested option | Decided | §4.3, §8.4 |
| A11 | `bfloat16` autocast, `float32` parameters and optimizer state, no gradient scaler | Fixed (D5), verification in 06 | §4.8 |
| A12 | Training windows may span documents; `<\|endoftext\|>` is the only separator | Decided | §4.9 |
| A13 | `V` = 16,000 (32,000 in the first draft) | Decided by the author on 2026-10-09 (ADR-0002 Amendment 1); re-confirmed by `04` §10 | `04` §6, §10; `06` §7; formula in §5.3 |
| A14 | Two configurations: `tiny` (smoke test) and `base` (training) | Decided | §4.10 |

**Reference points** (verified against the sources, not from memory):

| Model | Layers | Heads | Width | Context | Dropout | Source |
|---|---|---|---|---|---|---|
| nanoGPT "baby GPT" (character-level Shakespeare) | 6 | 6 | 384 | 256 | 0.2 | [config/train_shakespeare_char.py](https://github.com/karpathy/nanoGPT/blob/master/config/train_shakespeare_char.py) |
| GPT-2 small (released `gpt2` configuration) | 12 | 12 | 768 | 1,024 (vocabulary 50,257) | 0.1 (embedding, residual, attention) | [config.json](https://huggingface.co/openai-community/gpt2/blob/main/config.json) |
| nanoGPT `GPTConfig` defaults | 12 | 12 | 768 | 1,024 (vocabulary 50,304) | 0.0 (bias on) | [model.py](https://github.com/karpathy/nanoGPT/blob/master/model.py) |
| **This project, `base`** | **6** | **6** | **384** | **512** (vocabulary 16,000) | **0.0** (bias off) | this document |

`base` has the depth and width of the nanoGPT baby model, a longer context, and the head size (64) used by GPT-2 small. The GELU activation, 4× MLP expansion, pre-norm blocks, weight tying, and N(0, 0.02) initialization follow nanoGPT's implementation of GPT-2 ([model.py](https://github.com/karpathy/nanoGPT/blob/master/model.py)).

## 4. Architecture

### 4.1 Overview

```
token IDs (B, T)
   │
   ├─ token embedding   wte: (V, C)  ─┐
   └─ position embedding wpe: (T, C) ─┴─ add ─►  x (B, T, C)
                                                   │
                                  ┌────────────────┘
                                  ▼   repeat L = 6 times
                          x = x + Attention(LayerNorm(x))     # (B, T, C)
                          x = x + MLP(LayerNorm(x))           # (B, T, C)
                                  │
                                  ▼
                          LayerNorm  ─►  linear head (weight tied to wte)  ─►  logits (B, T, V)
```

### 4.2 Block

Pre-layer normalization: each sub-layer reads a normalized copy of `x` and adds its output back to the unnormalized `x`. `LayerNorm` is PyTorch's `nn.LayerNorm` (learned weight and bias, ε = 1e-5). `Linear` layers have no bias (A6). This matches the structure of [nanoGPT's `Block`](https://github.com/karpathy/nanoGPT/blob/master/model.py); the placement of normalization at the input of each sub-block is the GPT-2 design.

*Source note:* the GPT-2 paper's text could not be extracted in this session (its PDF is not machine-readable here). The statements about GPT-2 are taken from the released configuration and from nanoGPT's code, which cites the paper for the scaled initialization (§4.7).

### 4.3 Causal self-attention (written explicitly)

```
q, k, v = split(c_attn(x))                          # three tensors, each (B, T, C); c_attn: Linear(C, 3C)
reshape each to (B, H, T, d_head)
scores  = (q @ k^T) / sqrt(d_head)                  # (B, H, T, T)
scores  = masked_fill(scores, ~lower_triangular, -inf)   # position t sees positions <= t only
weights = softmax(scores, dim=-1)                   # (B, H, T, T)
y       = weights @ v                               # (B, H, T, d_head)
out     = c_proj(merge_heads(y))                    # (B, T, C); c_proj: Linear(C, C)
```

- The mask is a `(1, 1, T, T)` boolean lower-triangular buffer, not saved in checkpoints.
- No attention dropout (A8).
- This is the computation that [`torch.nn.functional.scaled_dot_product_attention`](https://docs.pytorch.org/docs/2.14/generated/torch.nn.functional.scaled_dot_product_attention.html) documents as its equivalent reference implementation (PyTorch 2.14), so the explicit version is also the specification of the fused one.
- The causal-mask test (`08-testing-strategy.md`) targets this code directly: change tokens at positions ≥ k and assert the logits at positions < k do not change.

### 4.4 MLP

`Linear(C, 4C)`, `GELU` (PyTorch default, exact form), `Linear(4C, C)`; no bias. Width 1,536 for `base`.

### 4.5 Position information: learned absolute embeddings

`wpe` is an `Embedding(T, C)` indexed by position 0 … `T`−1 and added to the token embedding. It costs `T·C` = 196,608 parameters (0.9% of `N`).

- Sequences shorter than `T` are allowed; longer ones are an error.
- Training windows start at random offsets inside documents (Design §4.4), so a window that begins mid-document at position 0 is ordinary training data. The sliding window used when generation exceeds the context length (Design §4.6) therefore stays in the training distribution.
- **Limitation:** the model cannot represent positions beyond `T`.
- **Alternative recorded in ADR-0003:** rotary embeddings ([RoFormer](https://arxiv.org/abs/2104.09864)) add no parameters and are described by their authors as working across sequence lengths, at the cost of more code and more places for silent bugs (Design P1).

### 4.6 Weight tying

The output head and the token embedding share one matrix of shape `(V, C)`. Tying is used in the nanoGPT/GPT-2 implementation and was reported to reduce perplexity in [Press and Wolf (2017)](https://arxiv.org/abs/1608.05859).

At the first-draft vocabulary it was also required by the size limit: with `V` = 32,000 and `C` = 384 the matrix has 12,288,000 parameters, so an untied model would have 35,399,424 parameters, over the 30M limit of NFR2. **At the decided `V` = 16,000 it is no longer required:** the matrix has 6,144,000 parameters and an untied model would have 23,111,424, inside NFR2. Tying stays as decided (A-table): it saves 6.14M parameters and is the nanoGPT/GPT-2 convention; the `base` configuration is unchanged. The reason "required by the size limit" applies only to 32,000.

### 4.7 Initialization

| Parameter | Initialization |
|---|---|
| `Linear` and `Embedding` weights | N(0, 0.02) |
| Residual projections (`c_proj` of attention and of the MLP) | N(0, 0.02 / √(2L)) = N(0, 0.005774) for `L` = 6 |
| `LayerNorm` | weight 1, bias 0 (PyTorch default) |

The scaling of residual projections follows nanoGPT, whose comment on the code cites the GPT-2 paper ("apply special scaled init to the residual projections, per GPT-2 paper"); the factor 2 counts the two residual additions per block ([model.py](https://github.com/karpathy/nanoGPT/blob/master/model.py)).

**Check:** an untrained model must give a loss near ln `V`. Measured at `V` = 32,000: 10.4373 against ln 32,000 = 10.3735 (§9). At `V` = 16,000 the expected value is ln 16,000 = 9.6803 (computed, not measured here; `06` §6 gates the first loss of the production pilot against ln `V`).

### 4.8 Numeric precision

- Parameters, gradients, and AdamW state are `float32`. The forward pass and loss run under `torch.autocast("cuda", dtype=torch.bfloat16)`; backward is not wrapped, as the [PyTorch AMP documentation](https://docs.pytorch.org/docs/2.14/amp.html) recommends ("autocast should wrap only the forward pass(es) of your network, including the loss computation(s)").
- Measured dtypes under autocast on this machine: parameters `float32`; attention scores `bfloat16`; softmax output `float32`; logits `bfloat16`; cross-entropy loss `float32`. The softmax and loss therefore run in `float32` without extra code.
- No gradient scaler is used (Design D5). The AMP page describes the scaler's purpose as protecting small `float16` gradients; it does not state the `bfloat16` case, so "no scaler needed" is **provisional** and checked in 06 (no NaN or infinity, loss curve smooth).
- Do not call `.bfloat16()` on the model; autocast handles casts (AMP documentation).

### 4.9 Documents and the context window

Training windows are `T`+1 contiguous tokens from the memory-mapped token file (Design §4.4). A window can contain the end of one document, a `<|endoftext|>` token, and the start of the next. There is **no** attention mask between documents (A12): the separator token is the only signal. This is the GPT-2 convention and the simplest to test; the cost is that some training positions attend to an unrelated previous document.

### 4.10 Configurations

| Field | `base` | `tiny` |
|---|---|---|
| `n_layer` | 6 | 2 |
| `d_model` | 384 | 128 |
| `n_head` | 6 | 2 |
| `d_head` | 64 | 64 |
| `d_ff` (= 4 × `d_model`) | 1,536 | 512 |
| `context_length` | 512 | 128 |
| `vocab_size` | 16,000 (from the tokenizer) | 16,000 |
| `dropout` | 0.0 | 0.0 |
| bias in `Linear` | false | false |
| tied head | true | true |
| attention | `explicit` | `explicit` |
| **Parameters** | **16,967,424** (23,111,424 at 32,000) | **2,458,880** (4,506,880 at 32,000) |
| Use | training | smoke test and single-batch overfit test |

`tiny` uses the real vocabulary so the whole pipeline (tokenizer, encoder, sampler, model) is exercised; its parameters are 83.3% embedding (90.9% at 32,000), so it says nothing about model quality.

```yaml
model:                    # sketch of the config fields (Design §7); unknown keys are an error
  n_layer: 6
  d_model: 384
  n_head: 6
  context_length: 512
  vocab_size: 16000       # read from the tokenizer file; asserted equal
  dropout: 0.0
  bias: false
  tie_weights: true
  attention: explicit     # or: sdpa (see §8.4)
```

## 5. Parameter count

### 5.1 Formula

With learned positions, a tied head, `Linear` layers without bias, and `LayerNorm` with weight and bias:

```
N = V·C  +  T·C  +  L·(12·C² + 4·C)  +  2·C
    token    pos     per block          final
```

Per block: attention `c_attn` 3C² + `c_proj` C²; MLP 4C² + 4C²; two `LayerNorm`s 4C.

### 5.2 `base`, term by term

| Term | Parameters at `V` = 32,000 (first draft) | Parameters at `V` = 16,000 (decided) |
|---|---|---|
| Token embedding, shared with the head (`V·C`) | 12,288,000 | 6,144,000 |
| Position embedding (`T·C`) | 196,608 | 196,608 |
| One block: attention 589,824 + MLP 1,179,648 + two LayerNorms 1,536 | 1,771,008 | 1,771,008 |
| Six blocks | 10,626,048 | 10,626,048 |
| Final `LayerNorm` | 768 | 768 |
| **Total `N`** | 23,111,424 | **16,967,424** |
| Everything except token and position embeddings (the convention of [Kaplan et al. 2020](https://arxiv.org/abs/2001.08361)) | 10,626,816 | 10,626,816 |

Counting the parameters of the throwaway implementation (unique parameters, so the tied matrix counts once) gives exactly 23,111,424 at `V` = 32,000, and 4,506,880 for `tiny` (§9). The formula gives 16,967,424 for `base` and 2,458,880 for `tiny` at `V` = 16,000. The token embedding is 36.2% of `base` at 16,000 (53.2% at 32,000).

### 5.3 Dependence on the vocabulary size

`V` is provisional until the real tokenizer passes `04` §10. The count changes by 384 per vocabulary entry:

| `V` | Parameters | Within NFR2 (10M to 30M) |
|---|---|---|
| **16,000** (decided) | **16,967,424** | yes |
| 32,000 (first draft) | 23,111,424 | yes |
| 48,000 | 29,255,424 | yes, 744,576 below the limit |
| 65,535 (the `uint16` maximum) | 35,988,864 | **no** |

The last row shows why NFR2 (parameter limit) and TR2 (ID range) are separate constraints: a vocabulary that satisfies TR2 can still violate NFR2.

## 6. Token supply and how long to train

### 6.1 The supply, preliminary

| Quantity | Value | Source |
|---|---|---|
| Wikipedia articles, raw words | 1,219,201; 273,803,280 | `scripts/inspect_data.py` functions, full scan (Appendix A.1) |
| After Data Spec §8 step 3a and steps 4–6 | 480,404 articles; **207,947,124 words** (75.9% of raw words) | same scan |
| Same, but step 3a and the length filter only | 490,669 articles; 214,042,453 words | same scan; this is the "≈214M" of `03` §7 and ADR-0001 |
| Tokens per word, 32k byte-level BPE, **preliminary** | **1.4755** (3,057,304 tokens over 2,071,980 words) | trial tokenizer, §6.2 |
| Train share | 98% (Data Spec §10) | `03` §10 |
| Working token supply `S` at 32,000 (train split, with one `<\|endoftext\|>` per document) | ≈ 301.2M | 207,947,124 × 1.4755 × 0.98 + 480,404 × 0.98 |
| Tokens per word, 16k byte-level BPE, **preliminary** | 1.6073 | same trial method (§6.2) |
| **Working token supply `S` at 16,000 (decided vocabulary)** | **≈ 328.0M** | 207,947,124 × 1.6073 × 0.98 + 480,404 × 0.98 |

Deduplication (exact: 0.09% removable; near-duplicates: at most 0.5% in the sample, a lower bound, `metrics.md`) would reduce `S` by at most about 0.5%; it is not applied here.

`S` is below the 321–535M range in `03` §7 and ADR-0001. The cause is the measured tokens per word, 1.4755, being under the assumed range of 1.5 to 2.5, together with 207.9M instead of 214.1M words. **ADR-0001's first revisit trigger ("measured tokens per word below 1.5") is met by this preliminary measurement.** The final value comes from the real tokenizer (`04` §10); see §12 for the question this raises.

### 6.2 The trial tokenizer (preliminary measurement)

Purpose: replace the assumed 1.5 to 2.5 tokens per word with a measured value before sizing the model. The method follows `04` §4 to §6 as closely as practical, using the library's own normalizers and a regular-expression pre-tokenizer.

| Item | Detail |
|---|---|
| Library | Hugging Face `tokenizers` 0.23.3, installed in the project venv for this trial only; not in any requirements file |
| Sample | Seeded hash of the article id (seed 42), 10% of cleaned articles: 43,190 for training (18,726,882 words), 4,858 held out (2,071,980 words). Cleaning = §8 step 3a and steps 4–6 as in `scripts/inspect_data.py` |
| Normalization | N1 to N12 and N14; N13 not applied (quotes kept) |
| Pre-tokenization | P1 to P5 as regular expressions (see the finding in §13, item 5) |
| Training | byte-level BPE, special tokens `<\|endoftext\|>`, `<\|pad\|>`, `<\|unk\|>` at IDs 0 to 2 |
| Measure | tokens divided by whitespace-separated words of the cleaned text (before normalization, the same word definition as `03`) on the held-out articles |

| Vocabulary | Training articles | Tokens per word | vs 32k |
|---|---|---|---|
| 16,000 | 43,190 | 1.6073 | +8.9% |
| **32,000** | **43,190** | **1.4755** | – |
| 32,000 | 10,000 | 1.4875 | +0.8% |
| 48,000 | 43,190 | 1.4175 | −3.9% |

- Against the `04` §10 rule as first written: 16k is not within 5% of 32k, and 48k does not improve by more than 15%, so **32k stays** (preliminary). **Superseded on 2026-10-09:** the criterion became validation loss per word and the author chose 16,000 (§12, ADR-0002 Amendment 1).
- Training on 4.3× more words lowered tokens per word by 0.8%. Extrapolating that trend (log-linear in training size, two points) to the full train split (about 204M words) suggests roughly **1.45**. This extrapolation is indicative only; if it holds, `S` is about 296M.
- Other checks on the held-out text: `<|unk|>` count 0; largest ID used 31,999; single-byte tokens 10.7% of all tokens; `decode(encode(x))` equals the normalized text for the first 600 articles.
- Caveats: the trial trained on 8.7% of the corpus's words; normalization and pre-tokenization are approximations of the spec; the number is not the §10 measurement.

### 6.3 Tokens per parameter: a guideline, not a floor

The Data Spec §3 states the rule of thumb of about 20 training tokens per parameter. [Hoffmann et al. (2022)](https://arxiv.org/abs/2203.15556) report that model size and training tokens should be scaled equally ("for every doubling of model size the number of training tokens should also be doubled"); the figure 20 is the Data Spec's convention and was not re-derived here.

**In this project the ratio is a guideline.** Training for 1 to 2 epochs over the supply `S` is accepted. [Muennighoff et al. (2023)](https://arxiv.org/abs/2305.16264) report that repeating data for up to 4 epochs, at a fixed compute budget, changes the loss negligibly compared with unique data. Their experiments use much larger models, so this is **provisional** here (verified by the validation-loss curve in 06).

| Epochs over `S` | Tokens at 32,000 | Per parameter, total `N` (32,000) | Per parameter, non-embedding (32,000) | Tokens at 16,000 (decided) | Per parameter, total `N` (16,000) | Per parameter, non-embedding (16,000) |
|---|---|---|---|---|---|---|
| 1 | 301.2M | 13.0 | 28.3 | 328.0M | 19.3 | 30.9 |
| 1.5 | 451.8M | 19.5 | 42.5 | 492.0M | 29.0 | 46.3 |
| **2** | 602.3M | 26.1 | 56.7 | **656.0M** | **38.7** | **61.7** |
| 4 | 1,204.7M | 52.1 | 113.4 | 1,312.1M | 77.3 | 123.5 |

The 20-tokens-per-parameter figure is reached at 1.53 epochs for total parameters. Counted the way Kaplan et al. count (excluding the token and position embeddings, 53% of this model), it is reached at 0.71 epochs. At `V` = 16,000 the figures are 1.03 epochs (total) and 0.65 epochs (non-embedding, 36% of the model is embedding). Which count the rule refers to is not settled by the sources used here; both are shown so the training plan can state its choice.

### 6.4 Size options considered

All with `T` = 512, `V` = 32,000 (the first-draft vocabulary; at the decided `V` = 16,000 `base` has 16,967,424 parameters, 114,780,672 FLOPs per token, and `S` = 328.0M), tied head, learned positions, from the §5.1 formula. Time is an **estimate**: tokens at 20 per parameter times FLOPs per token (§8.1 formula for each size), divided by the 9.55 TFLOP/s effective rate measured for `base` with explicit attention (§8.3). Smaller models may reach a different effective rate; 06 re-measures.

| `L` × `C` × `H` | Parameters | FLOPs per token | Tokens at 20 per parameter | Epochs over `S` (301.2M) | Estimated time at 20 per parameter | Estimated time for 2 epochs |
|---|---|---|---|---|---|---|
| 8 × 256 × 4 | 14,623,232 | 99,535,872 | 292M | 0.97 | 0.85 h | 1.74 h |
| 6 × 320 × 5 | 17,784,960 | 117,523,200 | 356M | 1.18 | 1.22 h | 2.06 h |
| **6 × 384 × 6** (`base`) | **23,111,424** | **151,644,672** | **462M** | **1.53** | **2.04 h** | **2.66 h** |
| 8 × 384 × 6 | 26,653,440 | 177,615,360 | 533M | 1.77 | 2.75 h | 3.11 h |

All four fit in the 6-hour budget (M3). The choice among them is a quality judgement, not a resource constraint; it is recorded in ADR-0003.

## 7. Context length

`T` = 512 tokens.

- At 1.4755 tokens per word (`V` = 32,000), 512 tokens are about 347 words. The mean cleaned article is 432.9 words (207,947,124 / 480,404), about 639 tokens, so one window covers about 80% of a mean article. At the decided `V` = 16,000 (1.6073 tokens per word) 512 tokens are about 318 words, the mean article is about 696 tokens, and one window covers about 74% of it. Longer articles are cut into several windows by the sampler (06).
- Cost: the attention matrix multiplications are 14,155,776 of the 151,644,672 FLOPs per token (9.3%); with the explicit implementation the attention-score memory grows with `T²` (§8.2).
- 256 (the nanoGPT baby model) would halve that memory but cover only 40% of a mean article; 1,024 (GPT-2 small) would quadruple the score memory and slow CPU generation in the demo, which has no KV cache (Design §4.6).

## 8. Compute and memory (measured)

Machine: NVIDIA GeForce RTX 5050 Laptop GPU, compute capability 12.0, 7.96 GiB total, 20 multiprocessors; PyTorch 2.14.1+cu130. Throughput and memory below are for one optimizer step of the `base` model (forward, backward, fused AdamW) on random token IDs, `bfloat16` autocast, `T` = 512, `V` = 32,000 (the first-draft vocabulary; the vocabulary sweep in §8.2 includes 16,000); each point is a fresh process (Appendix A.3).

### 8.1 Floating-point operations

Matrix-multiplication throughput measured on shapes from this model: 24.0 to 28.1 TFLOP/s in `bfloat16`, 6.9 to 8.4 in `float32` (Appendix A.2), so `bfloat16` is about 3.3 times faster.

FLOPs per training token:

```
6·(N − T·C) + 12·L·T·C  =  6 × 22,914,816  +  12 × 6 × 512 × 384  =  137,488,896 + 14,155,776  =  151,644,672
```

The first term is the standard 6 FLOPs per parameter per token ([Kaplan et al. 2020](https://arxiv.org/abs/2001.08361): "the factor of 6 accounts for the forward and backward passes"); the position table is a lookup, so it is excluded, while the tied matrix counts once because the output head multiplies by it. The second term is the two attention matrix products (`QKᵀ` and weights × `V`) over the full `T`×`T` matrix, which the explicit implementation computes.

### 8.2 Memory

Static memory is 16 bytes per parameter (`float32` weight, gradient, and two AdamW moments): 23,111,424 × 16 = 369.8 MB = 0.344 GiB. The measurements below include that.

| Micro-batch `B` | Explicit attention: peak allocated / reserved | `scaled_dot_product_attention`: peak allocated / reserved |
|---|---|---|
| 4 | 1.48 / 1.79 GiB | 1.27 / 1.58 GiB |
| 8 | 2.59 / 2.91 | 2.16 / 2.49 |
| 12 | 3.69 / 5.03 | 3.06 / 4.37 |
| **16** | **4.79 / 5.66** | **3.96 / 4.77** |
| 20 | 5.91 / 7.05 | 4.86 / 7.20 |
| 24 | 7.01 / **8.42** | 5.75 / 7.06 |

Fitted from the table: peak allocated ≈ 0.37 + 0.277·`B` GiB (explicit) and 0.37 + 0.225·`B` GiB (fused). The intercept 0.37 GiB matches the static 0.344 GiB.

- **Limit.** The card reports 7.96 GiB. At `B` = 24 the explicit version reserves 8.42 GiB, spills into shared system memory, and its throughput drops from 63k to 37k tokens/s. So MR3 is judged on reserved memory against 7.96 GiB, and the explicit version's practical limit is `B` ≤ 20; **`B` = 16 (8,192 tokens) leaves 2.3 GiB of headroom.**
- **The vocabulary is the largest activation cost.** At `B` = 16 the peak is 3.25, 4.79, and 6.34 GiB (allocated) for `V` = 16,000, 32,000, and 48,000: 0.096 GiB per 1,000 vocabulary entries, so about 3.1 GiB of the 4.79 GiB at 32k comes from the `(B, T, V)` logits and the loss. At the decided 16k the benchmark peak is 3.25 GiB allocated at 76.9k tokens/s; the real pipeline of `06` measures 3.31 GiB allocated and 3.68 GiB reserved at `B` = 16. At 48k the reserved memory (7.63 GiB) is close to the limit and throughput falls to 52k tokens/s. The training plan (06) can reduce this cost (smaller micro-batch, or computing the loss in chunks).
- **Attention-score memory.** The difference between the two implementations is 0.0525 GiB per sequence (53.8 MiB) at `T` = 512, 0.83 GiB at `B` = 16. It scales with `T²`: about 215 MiB per sequence at `T` = 1,024.

### 8.3 Throughput and the time budget

| Attention | Tokens/s at `B` = 16 | FLOP/s implied (× 151.6M) | Share of the measured 25 TFLOP/s | Tokens in 6 h | Epochs over `S` in 6 h | 2 epochs take |
|---|---|---|---|---|---|---|
| Explicit | 63.0k | 9.55 T | 38% | 1.36B | 4.5 | 2.66 h |
| `scaled_dot_product_attention` | 98.1k | 14.88 T | 60% | 2.12B | 7.0 | 1.71 h |

For M3 (a run under 6 hours), compute is not the constraint; the token supply is. These are throughput numbers on random data without data loading, validation, or checkpointing, taken while a CPU-only job ran in the background; `06-training-plan.md` re-measures with the real pipeline: 60.7k tokens/s at 32,000 and **74.6k tokens/s at 16,000** with the real loader, gradient clipping, and fused AdamW (`06` §5).

### 8.4 The fused attention path (option, not used in v1)

`scaled_dot_product_attention(q, k, v, is_causal=True)` computes the same function (documented in [PyTorch 2.14](https://docs.pytorch.org/docs/2.14/generated/torch.nn.functional.scaled_dot_product_attention.html)). Measured against the explicit version with identical weights: maximum logit difference 2.4e-6 in `float32` and 1.6e-2 in `bfloat16` (logits of magnitude about 2.5); loss 10.442615 against 10.442614; maximum gradient difference over all parameters 1.7e-8.

It is 56% faster and uses 0.83 GiB less at `B` = 16. It is **not** the v1 path: the explicit version is the specification and the target of the mask test. If the training schedule needs the speed, `attention: sdpa` is added behind the config field, with a test that the two paths agree within the tolerances above.

## 9. What was verified, and how

All with the throwaway implementation of this document (Appendix A); each becomes a test in `08-testing-strategy.md`.

| Check | Result |
|---|---|
| Parameter count equals the formula | At `V` = 32,000: `base` 23,111,424 = formula; `tiny` 4,506,880 = formula. At `V` = 16,000 the formula gives 16,967,424 and 2,458,880 |
| Untied count | 35,399,424 (`base`), over NFR2 |
| Initial loss near ln `V` | 10.4373 against 10.3735 |
| Causal mask | changing tokens at positions ≥ 300 changed logits at positions < 300 by exactly 0.0, and logits at positions ≥ 300 by up to 2.6 |
| Single-batch overfit (one fixed batch, targets shifted by one) | `tiny`: 10.407 → 0.0112 (step 50) → 0.0003 (step 200) → 0.0 (step 300). `base`: 10.463 → 0.0279 (step 50) → 0.0003 (step 200) |
| Dtypes under autocast | parameters `float32`, scores `bfloat16`, softmax `float32`, logits `bfloat16`, loss `float32` |
| Explicit and fused attention agree | §8.4 |

One implementation finding: slicing the shifted targets (`x[:, 1:]`) gives a non-contiguous tensor, and `.view(-1)` on it raises an error. The loss inputs must use `reshape(-1)` (or a contiguous copy). The first version of the probe failed on exactly this.

## 10. Interfaces

- `GPT(config)`; `forward(idx, targets=None)` returns `(logits, loss)`. `idx` is `(B, T)` `int64`; the sampler converts from the `uint16` token file. `targets` is `(B, T)`, already shifted by one (06). Logits are `(B, T, V)`.
- Assertions at the model boundary (Design P4): `idx.max() < vocab_size`; `T <= context_length`; the config `vocab_size` equals the tokenizer's.
- The padding token (ID 1) never appears in training data; its embedding row exists and is never trained on.
- Generation (Design §4.6) calls the same `forward` on the last `context_length` tokens.

## 11. Provisional decisions and how each is confirmed

| Decision | Confirmed or changed by |
|---|---|
| `V` = 16,000, and every parameter count that depends on it (§5.3) | `04` §10 (repeat of the matched comparison on the real tokenizer); recompute §5 from the formula |
| Tokens per word 1.6073 and `S` ≈ 328.0M at 16,000 (1.4755 and ≈ 301M at 32,000) (§6.1) | `04` §10 on the validation split; Data Spec §11 final statistics after the pipeline runs |
| Dropout 0.0 (A8) | 06: if validation loss rises while training loss falls during epoch 2, set dropout to 0.1 (a config field) |
| 1 to 2 epochs as acceptable (§6.3) | 06: validation-loss curve against tokens seen, compared with the single-epoch regime |
| No gradient scaler under `bfloat16` (§4.8) | 06: no NaN or infinity; a short `float32` comparison on `tiny` |
| Micro-batch region `B` ≤ 20 and the 63k / 98k tokens/s (§8) | 06: re-measured with the real model and data pipeline |
| Model size class (A2) | The first full run (06) and the results against M1 and M2 (07). No size ablation is planned; this is a judgement, not an experiment. |
| Learned positions (A4) | Qualitative checks near the context limit in 07; RoPE remains a future extension |

## 12. Open questions

| Question | Resolved in |
|---|---|
| ~~ADR-0001 revisit trigger 1 is met by the preliminary 1.4755 tokens per word. Reopen the corpus?~~ **Decided 2026-10-09: no.** Stay with Wikipedia and accept 1.5 to 2 epochs; recorded as Amendment 1 of ADR-0001 | Done; the final tokens-per-word value still comes from `04` §10 |
| Does the "20 tokens per parameter" rule count total or non-embedding parameters? | 06, which states which it uses |
| ~~**Vocabulary size. Leading option: 16,000** (see below). `V` stays 32,000 and provisional in this document; every formula is in terms of `V`~~ **Decided 2026-10-09: `V` = 16,000** (ADR-0002 Amendment 1); this document carries the 16,000 values with the 32,000 values as the comparison | Done; re-confirmed by `04` §10 on the production tokenizer |

**Vocabulary 16k against 32k, measured with the same sample and rules (§6.2).** All figures use `base` with `T` = 512, 207,947,124 words and 480,404 articles, train share 98%.

| | 16,000 | 32,000 | 48,000 |
|---|---|---|---|
| Tokens per word (preliminary) | 1.6073 | 1.4755 | 1.4175 |
| Parameters | 16,967,424 | 23,111,424 | 29,255,424 |
| Embedding share of parameters | 36.2% | 53.2% | 63.0% |
| Train tokens `S` | 328.0M | 301.2M | 289.3M |
| Epochs for 20 tokens per parameter | **1.03** | 1.53 | 2.02 |
| Tokens per parameter at 1.5 / 2 epochs | 29.0 / 38.7 | 19.5 / 26.1 | 14.8 / 19.8 |
| Peak allocated GiB at `B` = 16 (explicit attention) | 3.25 | 4.79 | 6.34 (reserved 7.63) |
| Tokens/s at `B` = 16, explicit (measured) | 76.9k | 62.9k | 52.3k |
| Estimated time, 20 tokens per parameter (339M tokens at 76.9k tokens/s, 462M at 62.9k) | 1.2 h | 2.0 h | – |

What 16k changes: 6.14M fewer parameters (−26.6%), 1.54 GiB less memory at `B` = 16 (−32%, the saving is the `(B, T, V)` logits), 22% more tokens/s, and 8.9% more tokens per word, so the training-token supply rises by 8.9% for the same text. The transformer blocks (10.6M parameters) are identical.

**Two cautions before 16k is chosen:**

1. **Tokens per parameter favours a small vocabulary mechanically.** The extra 26.8M tokens are the same text cut into smaller pieces, not new information. The criterion that matters is validation quality per word at equal compute, which this project has not measured at either size.
2. **`04` §10 as written selects 32k.** It keeps 32k unless 16k is within 5% of its tokens per word; the measured gap is 8.9%. Making 16k the choice means amending that criterion (for example, compare validation loss per word of two short `base` runs, one per vocabulary). That amendment belongs to the `04` owner and is not made here.

## 13. Proposed edits to earlier documents

*Part D (2026-10-10): every row below has a status in the last column; "Applied" refers to the row identifiers of the Part D table (PD-nn), "Left to the author" rows are edits to `CLAUDE.md`.*

Before Part D: not applied; listed for the author's decision (Part D of the plan).

| # | Document | Proposed edit | Part D status |
|---|---|---|---|
| 1 | `03-data-spec.md` §7 and ADR-0001 (Decision reason 2, evidence table, revisit trigger 1) | The cleaned size "≈214M words in 490,832 articles" applies only step 3a and the length filter. With steps 4 to 6 the full-set count is **480,404 articles, 207,947,124 words**. The token estimate "≈321–535M" becomes "≈307M in total, ≈301M in the train split, at 1.4755 tokens per word (preliminary)". | Applied to the Data Spec (PD-33); the ADR-0001 part **rejected** (PD-40): Amendment 1 records the measured values |
| 2 | ADR-0001, Revisit triggers | **Applied 2026-10-09** as Amendment 1 of ADR-0001 (trigger 1 fired, corpus not reopened; trigger 2 also met in the literal sense). No further edit. | No action: already applied as Amendment 1 of ADR-0001 on 2026-10-09 |
| 3 | `03-data-spec.md` §3 | The "Target: 400M–800M training tokens" is not reachable from cleaned Wikipedia alone (≈301M train tokens); add a pointer to §6.3 of this document. | Applied (PD-34) |
| 4 | `03-data-spec.md` §13, token row | Same numbers as item 1 ("estimated 321–535M tokens (≈214M words…)"). | Applied (PD-35) |
| 5 | `04-tokenizer-spec.md` P3 and P5, §10 | The exception in P3 (a one-letter prefix is not split from a following digit) combines with P5 (digit groups of at most three, from the right) so that "و2010" becomes the pre-tokens "و2" and "010", with the prefix attached to the first digit group. The §10 check expects the prefix "as its own piece, not merged into the digits". Decide between keeping the prefix with the digits (and rewording §10) or making the prefix its own pre-token (and rewording P3). Found by running the rules, `04` is otherwise consistent with this document. | Applied (PD-44): option (b), extended to the era markers (no exceptions in P3); see EXP-005 and ADR-0002 Amendment 2 |
| 6 | `02-design-doc.md` §4.3 | The deferred list ("number of layers … dropout") is resolved by this document: replace "Deferred to `05-model-architecture.md` (provisional)" with a pointer to §3. | Applied (PD-18) |
| 7 | `02-design-doc.md` §4.2 and D8; §12 | The tokenizer algorithm and library are decided in ADR-0002 (byte-level BPE, Hugging Face `tokenizers`, Proposed); D8 is no longer "provisional, decided in 04". | Applied (PD-17) |
| 8 | `02-design-doc.md` §12; `01-prd.md` §11 | Rows for the layer/head/width/context/positional-encoding question and the corpus and tokenizer questions are resolved (05, ADR-0001, ADR-0002). | Applied (PD-14, PD-19) |
| 9 | `02-design-doc.md` header | The table lacks its separator row, and the version (0.1, 2026-10-04) disagrees with the commit history (v0.2). `01-prd.md` has the opposite defect (separator without a header row). | Applied (PD-01, PD-16) |
| 10 | `04-tokenizer-spec.md` §9 | The configuration sketch has no entry for N4 (tab to space, collapse spaces). | Applied (PD-45) |
| 11 | `04-tokenizer-spec.md` §10 | Vocabulary-size rule: 16k loses on tokens per word (+8.9%) but is smaller and faster; decide the criterion (see §12). | Applied (PD-41): the criterion was decided in `06` §7 |

## 14. Diagrams this document needs

| Diagram | What it must show |
|---|---|
| Model overview | Token and position embeddings, `L` blocks, final LayerNorm, tied head, with the shape at every arrow ((B, T), (B, T, C), (B, T, V)) |
| Block and attention | Pre-LN residual wiring; split into heads; the `T`×`T` lower-triangular mask; MLP expansion |
| Memory against micro-batch | Peak allocated and reserved GiB against `B` for both attention paths, with the 7.96 GiB line and the shared-memory cliff at `B` = 24 |

## 15. Related documents

- `01-prd.md`: requirements this specification satisfies
- `02-design-doc.md` §4.3: the component this document details
- `03-data-spec.md` §3, §10: token budget and splits
- `04-tokenizer-spec.md`: vocabulary size and special tokens
- `docs/adr/0003-model-architecture.md`: size class, positional encoding, attention implementation (proposed)
- `06-training-plan.md`: consumes the parameter count, FLOPs per token, and memory per micro-batch
- `08-testing-strategy.md`: shape, mask, initialization, and overfit tests

## 16. References

- nanoGPT: [config/train_shakespeare_char.py](https://github.com/karpathy/nanoGPT/blob/master/config/train_shakespeare_char.py), [model.py](https://github.com/karpathy/nanoGPT/blob/master/model.py)
- GPT-2 small configuration: [openai-community/gpt2 config.json](https://huggingface.co/openai-community/gpt2/blob/main/config.json)
- Kaplan et al., [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361) (2020)
- Hoffmann et al., [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556) (2022)
- Muennighoff et al., [Scaling Data-Constrained Language Models](https://arxiv.org/abs/2305.16264) (2023)
- Press and Wolf, [Using the Output Embedding to Improve Language Models](https://arxiv.org/abs/1608.05859) (2016)
- Su et al., [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864) (2021)
- PyTorch 2.14: [scaled_dot_product_attention](https://docs.pytorch.org/docs/2.14/generated/torch.nn.functional.scaled_dot_product_attention.html), [Automatic Mixed Precision](https://docs.pytorch.org/docs/2.14/amp.html)

## Appendix A. Measurement log

All commands use `.venv/Scripts/python.exe`. The scripts are throwaway files in the session scratchpad (not in the repository); command lines are shown with their file names and arguments. Environment: Windows 11, Python 3.12.10, PyTorch 2.14.1+cu130, `tokenizers` 0.23.3 (venv only).

### A.1 Cleaned size of the full Wikipedia set

`cleaned_words_full.py` (uses `strip_trailing_sections` and `passes_cleaning_wikipedia` from `scripts/inspect_data.py`):

```
articles 1,219,201 | raw words 273,803,280
step 3a + length>=50 only : 490,669 docs, 214,042,453 words
step 3a + steps 4,5,6     : 480,404 docs, 207,947,124 words   (75.9% of raw words)  [507s]
```

### A.2 Matrix-multiplication throughput

`bench_gpu.py`: TFLOP/s, median of three repeats.

```
torch 2.14.1+cu130 | NVIDIA GeForce RTX 5050 Laptop GPU | compute capability 12.0 | total memory 7.96 GiB | SMs 20
square 4096                       bf16 28.1   fp32 8.4
qkv-like  16384x384 @ 384x1152    bf16 24.0   fp32 7.3
mlp-up    16384x384 @ 384x1536    bf16 25.7   fp32 6.9
mlp-down  16384x1536 @ 1536x384   bf16 26.6   fp32 8.2
head      16384x384 @ 384x32000   bf16 25.6   fp32 8.0
```

### A.3 Trial tokenizer

```
build_sample.py <dir>      -> train 43,190 docs / 18,726,882 words ; held-out 4,858 docs / 2,071,980 words
measure.py <dir>           -> 32k (43,190 docs): tokens/word 1.4755 | 16k: 1.6073 | 32k (10,000 docs): 1.4875
measure48.py <dir>         -> 48k (43,190 docs): tokens/word 1.4175
```

### A.4 Model probe

`run_probe.py` (parameter counts, initial loss, mask test, dtypes), `one_point.py <dir> <sdpa 0|1> <B> <V> <steps>` (one fresh process per memory/throughput point; peak allocated and reserved GiB, tokens/s), `overfit.py`, `sdpa_equal.py`:

```
base  L=6 d=384 h=6 T=512: measured 23,111,424 | formula 23,111,424 | equal: True | untied 35,399,424
tiny  L=2 d=128 h=2 T=128: measured  4,506,880 | formula  4,506,880 | equal: True | untied  8,602,880
init loss: 10.4373  vs ln(V) = 10.3735
causal mask: max |logit diff| at positions <300 when tokens >=300 change: 0.000e+00 ; at positions >=300: 2.622e+00
dtypes under autocast(bf16): params float32 | scores bfloat16 | softmax out float32 | logits bfloat16 | loss float32
V sweep, explicit attention, B=16: V=16000 3.25 GiB 76.9k tok/s | V=32000 4.79 GiB 62.9k | V=48000 6.34 GiB (reserved 7.63) 52.3k
fp32: max |logit diff| explicit vs SDPA 2.384e-06 | bf16: 1.562e-02 | loss 10.442615 vs 10.442614 | max |grad diff| 1.671e-08
```
