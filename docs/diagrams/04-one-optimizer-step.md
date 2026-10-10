# One optimizer step

One optimizer step of 4 accumulated micro-batches (32,768 tokens), with tensor shapes and the float32 / bfloat16 boundaries; it illustrates `06-training-plan.md` §4.2.

```mermaid
sequenceDiagram
    participant S as Sampler
    participant M as Model (float32 parameters)
    participant L as Loss (float32)
    participant O as AdamW (float32 state)
    participant G as Log

    Note over O: lr = lr_at(step), set in every parameter group
    loop micro in range(4)
        S->>M: x (16, 512) int64, y (16, 512) int64
        Note over M: forward under autocast bfloat16
        M->>L: logits (16, 512, V) bfloat16, V = 16,000
        Note over L: mean cross-entropy over reshape(-1, V)
        L->>M: (loss / 4).backward(), gradients float32
    end
    M->>O: clip_grad_norm_(parameters, 1.0), returns grad_norm
    O->>O: step(), then zero_grad(set_to_none=True)
    O->>G: step, lr, mean of the 4 micro-batch losses, grad_norm
```

<!-- Sources: 06-training-plan.md §4.2 (the loop, shapes (16, 512), loss / 4, clip 1.0, zero_grad(set_to_none=True), logged loss is the mean of the 4 micro-batch losses), §4.5 (micro-batch 16 x 4 accumulation = 32,768 tokens per step), 05-model-architecture.md §4.8 (parameters, gradients, AdamW state float32; forward and loss under bfloat16 autocast; logits bfloat16; loss float32; no scaler), V = 16,000 per ADR-0002 Amendment 1. -->

Reads with: `docs/06-training-plan.md` §4.2 and `docs/05-model-architecture.md` §4.8.
