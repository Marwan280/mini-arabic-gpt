# Memory against micro-batch

Peak GPU memory against micro-batch size for the two attention implementations, measured at V = 32,000, with the card's 7.96 GiB limit and the spill at B = 24 for the explicit version (8.42 GiB reserved); it illustrates `05-model-architecture.md` §8.2.

Explicit attention (the implementation chosen for v1): bars are peak allocated, the rising line is peak reserved, the flat line is the 7.96 GiB limit.

```mermaid
xychart-beta
    title "Explicit attention, GiB"
    x-axis "micro-batch B (sequences)" [4, 8, 12, 16, 20, 24]
    y-axis "GiB" 0 --> 9
    bar [1.48, 2.59, 3.69, 4.79, 5.91, 7.01]
    line [1.79, 2.91, 5.03, 5.66, 7.05, 8.42]
    line [7.96, 7.96, 7.96, 7.96, 7.96, 7.96]
```

`scaled_dot_product_attention` (kept behind `attention: sdpa`): same encoding.

```mermaid
xychart-beta
    title "Fused attention (sdpa), GiB"
    x-axis "micro-batch B (sequences)" [4, 8, 12, 16, 20, 24]
    y-axis "GiB" 0 --> 9
    bar [1.27, 2.16, 3.06, 3.96, 4.86, 5.75]
    line [1.58, 2.49, 4.37, 4.77, 7.20, 7.06]
    line [7.96, 7.96, 7.96, 7.96, 7.96, 7.96]
```

<!-- Sources: 05-model-architecture.md §8.2 (the table of peak allocated / reserved GiB for B = 4, 8, 12, 16, 20, 24, both attention paths; measured at T = 512, V = 32,000; the 7.96 GiB limit and the explicit version's 8.42 GiB reserved at B = 24, where throughput falls from 63k to 37k tokens/s; B = 16 chosen). At the chosen V = 16,000 the real pipeline measures 3.31 GiB allocated and 3.68 GiB reserved at B = 16 (06-training-plan.md §5, 05 §8.2). -->

Reads with: `docs/05-model-architecture.md` §8.2 and `docs/06-training-plan.md` §5.
