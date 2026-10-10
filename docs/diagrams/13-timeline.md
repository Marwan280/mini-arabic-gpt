# Timeline

The plan of 2026-10-11 to 2026-10-26 as two Gantt charts (the first week, then the second), with the two people and the project machine as rows, the gates G1 to G3, the checkpoints C1 to C3, and the two buffer days; it illustrates `11-roadmap.md` §7.1 to §7.4 and §8.

Part 1, 2026-10-11 to 2026-10-17:

```mermaid
gantt
    title Plan, part 1 (2026-10-11 to 2026-10-17)
    dateFormat YYYY-MM-DD
    axisFormat %m-%d
    section Marwan
    M01 Mark the Part D table           :m01, 2026-10-11, 1d
    M02 Decide EXP-005 and open rules   :m02, 2026-10-12, 1d
    M22 Tokenizer tests first           :m22, 2026-10-12, 4d
    M03 Review the fixture              :m03, 2026-10-13, 1d
    M04 Data pipeline                   :m04, 2026-10-13, 3d
    M06 Model tests first               :m06, 2026-10-15, 2d
    M05 Model code                      :m05, 2026-10-16, 1d
    M07 Production data run             :m07, 2026-10-17, 1d
    section Ghada
    G01 Test scaffold                   :g01, 2026-10-11, 1d
    G03 Data tests first                :g03, 2026-10-12, 2d
    G02 Review the fixture              :g02, 2026-10-13, 1d
    G05 Tokenizer code                  :g05, 2026-10-15, 2d
    G06 Training tests first            :g06, 2026-10-16, 2d
    section Project machine
    Data pipeline and tokenizer run     :crit, pm1, 2026-10-17, 1d
    section Gates and checkpoints
    Docs merged into main               :milestone, md, 2026-10-11, 0d
    C1                                  :milestone, c1, 2026-10-15, 0d
    C2                                  :milestone, c2, 2026-10-17, 0d
```

Part 2, 2026-10-18 to 2026-10-26:

```mermaid
gantt
    title Plan, part 2 (2026-10-18 to 2026-10-26)
    dateFormat YYYY-MM-DD
    axisFormat %m-%d
    section Marwan
    M08 Pilot                           :m08, 2026-10-20, 1d
    M09 Main run launched               :m09, 2026-10-20, 1d
    M19 Approve prompts and texts       :m19, 2026-10-21, 1d
    M10 Evaluation code                 :m10, 2026-10-21, 1d
    M11 Baseline store                  :m11, 2026-10-22, 1d
    M17 Rating items                    :m17, 2026-10-22, 1d
    M18 Calibration and rating          :m18, 2026-10-22, 1d
    M12 M1 on the test split            :m12, 2026-10-23, 1d
    M13 Analyse M1                      :m13, 2026-10-23, 1d
    M14 Model Card                      :m14, 2026-10-24, 1d
    section Ghada
    G07 Training code                   :g07, 2026-10-18, 2d
    G08 Injection runner G1 subset      :g08, 2026-10-19, 2d
    G09 Core evaluation tests           :g09, 2026-10-21, 1d
    G18 Generation module               :g18, 2026-10-21, 1d
    G11 Generation tests                :g11, 2026-10-21, 1d
    G12 Approve prompts                 :g12, 2026-10-21, 1d
    G14 Calibration and rating          :g14, 2026-10-22, 1d
    G13 Demo and 14 demo tests          :g13, 2026-10-23, 1d
    G19 Recording                       :g19, 2026-10-23, 1d
    G10 Review README and Model Card    :g10, 2026-10-24, 1d
    G20 Final consistency check         :g20, 2026-10-24, 1d
    section Project machine
    Pilot on the GPU, morning           :crit, pm2, 2026-10-20, 1d
    Main run planned                    :crit, pm3, 2026-10-20, 1d
    Spare slot and latest start         :pm4, 2026-10-21, 1d
    Baseline build                      :pm5, 2026-10-23, 1d
    section Gates and checkpoints
    G1 and G2                           :milestone, g1, 2026-10-20, 0d
    C3                                  :milestone, c3, 2026-10-21, 0d
    G3                                  :milestone, g3, 2026-10-23, 0d
    Last planned working day            :milestone, lw, 2026-10-24, 0d
    section Buffer
    Buffer                              :bf1, 2026-10-25, 1d
    Buffer and end date                 :bf2, 2026-10-26, 1d
```

<!-- Sources: 11-roadmap.md §7.1 (calendar, gates and checkpoints per date, buffer days 10-25 and 10-26, end date 10-26), §7.2 and §7.3 (task ids, owners, names, due dates; start dates are read from the calendar of §7.1 where it names a start, otherwise the bar spans the hours of the task ending on its due date), §7.4 (machine schedule: data run on 10-17, pilot on the morning of 10-20, main run 10-20 of about 2.6 h, spare slot on 10-21, baseline build on 10-23), §8 (C1 end of 10-15, C2 end of 10-17, G1 on 10-20, G2 on 10-20 after the pilot, C3 end of 10-21, G3 on 10-23). Year 2026. -->

Reads with: `docs/11-roadmap.md` §7 and §8.
