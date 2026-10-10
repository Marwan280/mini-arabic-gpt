# Learning-rate schedule

Linear warmup of 400 steps, cosine decay to 1e-4 over the whole run, then constant, with the run lengths at V = 16,000 and V = 32,000; it illustrates `06-training-plan.md` §4.4.

```mermaid
flowchart LR
    W["warmup, steps 0 to 400<br/>peak/401 up to peak = 1e-3"]
    C["cosine decay<br/>1e-3 down to min_lr = 1e-4 at the last step"]
    K["constant<br/>min_lr = 1e-4"]
    W --> C --> K
    R16["total_steps = 20,021 at V = 16,000 (chosen)"]
    R32["total_steps = 18,381 at V = 32,000 (comparison)"]
    C --- R16
    C --- R32
```

The curve at V = 16,000 (20,021 steps), sampled every 1,000 steps; the unit is 1e-4, so 10 is the peak 1e-3 and 1 is the minimum 1e-4.

```mermaid
xychart-beta
    title "Learning rate, V = 16,000 (x 1e-4)"
    x-axis "step" [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000]
    y-axis "learning rate (x 1e-4)" 0 --> 10
    line [0.025, 9.979, 9.853, 9.616, 9.273, 8.834, 8.309, 7.712, 7.059, 6.366, 5.651, 4.932, 4.228, 3.556, 2.934, 2.377, 1.901, 1.516, 1.233, 1.060, 1.0]
```

<!-- Sources: 06-training-plan.md §4.4 (warmup 400 steps from peak/401 to peak, then cosine decay to min_lr at the last step, then constant min_lr; peak 1e-3, minimum 1e-4; cycle over the whole run; total_steps 20,021 at V = 16,000 and 18,381 at 32,000), §5 (the step counts). The plotted values are computed from that formula (lr = peak * (step + 1) / 401 during warmup; min + 0.5 * (1 + cos(pi * (step - 400) / (total_steps - 1 - 400))) * (peak - min) afterwards) and are an illustration, not measurements. -->

Reads with: `docs/06-training-plan.md` §4.4 and §5.
