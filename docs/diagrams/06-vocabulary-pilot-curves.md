# Vocabulary pilot curves

Validation loss per word at 1/6 to 6/6 of the pass for the four scratchpad pilot runs (two seeds at V = 32,000 and two at V = 16,000), and the 16k-minus-32k difference that crosses zero at 4/6; it illustrates `06-training-plan.md` §7.2 (preliminary: scratchpad, not the production pipeline).

V = 32,000, seed 1 (first line) and seed 2 (second line):

```mermaid
xychart-beta
    title "V = 32,000, nats per word (seed 1, seed 2)"
    x-axis "fraction of the pass" ["1/6", "2/6", "3/6", "4/6", "5/6", "6/6"]
    y-axis "nats per word" 7 --> 9.6
    line [9.2469, 8.4517, 8.0068, 7.7024, 7.5114, 7.4103]
    line [9.2556, 8.4624, 8.0160, 7.6991, 7.5005, 7.3971]
```

V = 16,000, seed 1 (first line) and seed 2 (second line):

```mermaid
xychart-beta
    title "V = 16,000, nats per word (seed 1, seed 2)"
    x-axis "fraction of the pass" ["1/6", "2/6", "3/6", "4/6", "5/6", "6/6"]
    y-axis "nats per word" 7 --> 9.6
    line [9.3926, 8.5131, 8.0329, 7.6777, 7.4261, 7.2954]
    line [9.4394, 8.5591, 8.0700, 7.7116, 7.4615, 7.3347]
```

Difference of the means of two seeds, 16,000 minus 32,000 (positive: 16k is worse, negative: 16k is better; the crossing is at 4/6):

```mermaid
xychart-beta
    title "16,000 minus 32,000, mean nats per word"
    x-axis "fraction of the pass" ["1/6", "2/6", "3/6", "4/6", "5/6", "6/6"]
    y-axis "nats per word" -0.1 --> 0.2
    bar [0.1648, 0.0791, 0.0401, -0.0061, -0.0622, -0.0887]
```

<!-- Sources: 06-training-plan.md §7.2 (the table of validation loss per word at 1/6 to 6/6 for 32k seeds 1 and 2 and 16k seeds 1 and 2; final means 7.4037 at 32k and 7.3150 at 16k, a gap of 0.089; 16k overtakes at 4/6), §7.1 (matched on text, two seeds per vocabulary), §7.4 (V = 16,000 decided). The difference series is computed from the table: mean of the two 16k seeds minus mean of the two 32k seeds, rounded to four decimals. Preliminary: scratchpad code and trial tokenizers. -->

Reads with: `docs/06-training-plan.md` §7.
