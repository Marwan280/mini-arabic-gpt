# Critical path

The dependency graph of the plan: the critical path (thick arrows) from the Part D marks to the Model Card, the parallel branches that join at the pilot, and the evaluation branch that joins at the M1 evaluation; it illustrates `11-roadmap.md` §7.5.

```mermaid
graph LR
    M01["M01 Part D marks<br/>10-11"]
    M02["M02 decision on EXP-005<br/>10-12"]
    M22["M22 tokenizer tests<br/>10-15"]
    G05["G05 tokenizer code<br/>10-16"]
    M07["M07 production data run<br/>10-17"]
    M08["M08 pilot<br/>10-20"]
    M09["M09 main run<br/>10-20, latest start 10-21"]
    M12["M12 M1 evaluation<br/>10-23"]
    M13["M13 analysis<br/>10-23"]
    M14["M14 Model Card<br/>10-24"]

    G03["G03 data tests<br/>10-13"]
    M04["M04 data pipeline<br/>10-15"]
    M06["M06 model tests<br/>10-16"]
    M05["M05 model code<br/>10-16"]
    G06["G06 training tests<br/>10-17"]
    G07["G07 training code<br/>10-19"]
    G08["G08 injection runner<br/>10-20"]
    G1{{"gate G1<br/>10-20"}}

    M10["M10 evaluation code<br/>10-21"]
    M11["M11 baseline store<br/>10-22"]
    G3{{"gate G3<br/>10-23"}}

    M01 ==> M02 ==> M22 ==> G05 ==> M07 ==> M08 ==> M09 ==> M12 ==> M13 ==> M14

    G03 --> M04 --> M07
    M06 --> M05 --> G07
    G06 --> G07
    G07 --> G08
    M05 --> G08
    G07 --> M08
    G08 --> M08
    M08 --> G1
    G1 --> M09

    M05 --> M10 --> M11 --> M12
    G3 --> M12
```

<!-- Sources: 11-roadmap.md §7.5 (the critical path M01 to M14 and the parallel branches joining at the pilot and the evaluation branch joining at the M1 evaluation), §7.2 (the "Needs" column: M02 needs M01, M22 needs M02, G05 needs M22, M07 needs M04 and G05, M04 needs G03, M05 needs M06, G07 needs G06 and M05, G08 needs G07 and M05, M08 needs G07, G08 and M07, M09 needs M08, M10 needs M05, M11 needs M10, M12 needs the main run, M11 and gate G3, M13 needs M12, M14 needs M13) and due dates, §8 (G1 on 10-20, G3 on 10-23; the main run starts only after G1, RM1). G01 (test scaffold) is a need of the tests and is omitted. -->

Reads with: `docs/11-roadmap.md` §7.5.
