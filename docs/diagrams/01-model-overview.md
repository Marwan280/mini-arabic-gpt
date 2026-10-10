# Model overview

The `base` model from token IDs to logits, with the tensor shape on every arrow; it illustrates `05-model-architecture.md` §4.1 (the block itself is drawn in `02-block-and-attention.md`).

```mermaid
flowchart TB
    IDS["token IDs<br/>int64"]
    WTE["token embedding wte<br/>(V, C), V = 16,000, C = 384"]
    WPE["position embedding wpe<br/>(T, C), T = 512"]
    ADD["add"]
    BLK["transformer block, repeated L = 6 times<br/>x = x + Attention(LayerNorm(x))<br/>x = x + MLP(LayerNorm(x))"]
    FLN["final LayerNorm"]
    HEAD["linear head, no bias<br/>weight tied to wte"]
    OUT["logits"]

    IDS -->|"(B, T)"| WTE
    IDS -->|"positions 0 to T-1"| WPE
    WTE -->|"(B, T, C)"| ADD
    WPE -->|"(T, C)"| ADD
    ADD -->|"x (B, T, C)"| BLK
    BLK -->|"(B, T, C)"| FLN
    FLN -->|"(B, T, C)"| HEAD
    HEAD -->|"(B, T, V)"| OUT
    WTE -. "the same (V, C) matrix" .- HEAD
```

<!-- Sources: 05-model-architecture.md §4.1 (flow and shapes), §4.6 (weight tying), §4.4 (no bias), §4.5 (wpe is Embedding(T, C)), §1 symbol table (V = 16,000 per ADR-0002 Amendment 1, C = 384, T = 512, L = 6), §3 decisions. -->

Reads with: `docs/05-model-architecture.md` §4.1 and §4.6.
