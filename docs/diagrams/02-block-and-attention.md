# Block and attention

The pre-LayerNorm residual wiring of one block and the explicit causal self-attention inside it, with the lower-triangular mask and the MLP expansion; it illustrates `05-model-architecture.md` §4.2 to §4.4.

```mermaid
flowchart TB
    XIN["x in"]
    LN1["LayerNorm"]
    ATT["causal self-attention (second diagram)"]
    ADD1["add: x + attention output"]
    LN2["LayerNorm"]
    FC1["Linear(C, 4C), no bias<br/>4C = 1,536"]
    GELU["GELU"]
    FC2["Linear(4C, C), no bias"]
    ADD2["add: x + MLP output"]
    XOUT["x out"]

    XIN -->|"(B, T, C)"| LN1
    LN1 -->|"(B, T, C)"| ATT
    ATT -->|"(B, T, C)"| ADD1
    XIN -->|"skip (B, T, C)"| ADD1
    ADD1 -->|"(B, T, C)"| LN2
    LN2 -->|"(B, T, C)"| FC1
    FC1 -->|"(B, T, 4C)"| GELU
    GELU -->|"(B, T, 4C)"| FC2
    FC2 -->|"(B, T, C)"| ADD2
    ADD1 -->|"skip (B, T, C)"| ADD2
    ADD2 -->|"(B, T, C)"| XOUT
```

```mermaid
flowchart TB
    X["x (normalized)"]
    CATTN["c_attn: Linear(C, 3C)"]
    SPLIT["split into q, k, v"]
    HEADS["reshape each to heads<br/>H = 6, d_head = 64"]
    SCORES["scores = q @ k^T / sqrt(d_head)"]
    MASK["masked_fill with -inf where not lower-triangular<br/>mask (1, 1, T, T), T = 512"]
    SOFT["softmax over the last dimension"]
    AV["weights @ v"]
    MERGE["merge heads"]
    CPROJ["c_proj: Linear(C, C)"]
    OUT["attention output"]

    X -->|"(B, T, C)"| CATTN
    CATTN -->|"(B, T, 3C)"| SPLIT
    SPLIT -->|"q, k, v each (B, T, C)"| HEADS
    HEADS -->|"q, k, v each (B, H, T, d_head)"| SCORES
    SCORES -->|"(B, H, T, T)"| MASK
    MASK -->|"(B, H, T, T)"| SOFT
    SOFT -->|"weights (B, H, T, T)"| AV
    HEADS -->|"v (B, H, T, d_head)"| AV
    AV -->|"(B, H, T, d_head)"| MERGE
    MERGE -->|"(B, T, C)"| CPROJ
    CPROJ -->|"(B, T, C)"| OUT
```

<!-- Sources: 05-model-architecture.md §4.2 (pre-LN wiring, residual adds, no bias), §4.3 (attention steps, shapes, mask (1, 1, T, T), no attention dropout), §4.4 (MLP Linear(C, 4C), GELU, Linear(4C, C), width 1,536), §1 symbol table and §3 (C = 384, H = 6, d_head = 64, T = 512). -->

Reads with: `docs/05-model-architecture.md` §4.2 to §4.4.
