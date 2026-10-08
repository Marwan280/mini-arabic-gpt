# ADR 0001: Training corpus

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-10-08 |
| **Deciders** | Marwan (Wikipedia inspection and rating), Ghada (FineWeb-2 inspection and rating) |
| **Related** | `docs/03-data-spec.md` §4–§8, §13; `docs/01-prd.md` FR1, NFR2, NG8; `experiments/experiment-log.md` EXP-001 to EXP-004 |
| **Evidence** | `reports/data-inspection/metrics.json`, `metrics.md`, `reading_sample_wikipedia.txt`, `reading_sample_fineweb2.txt` |

## Context

The project needs one public Modern Standard Arabic text corpus (PRD FR1) that is free, licensed for training and a public demo, processable on the project machine (16 GB RAM, 8 GB VRAM), and large enough for a 10–30M parameter model (NFR2). The Data Spec (§3) sets a target of 400–800M training tokens, at roughly 20 tokens per parameter.

Two candidates were specified in Data Spec §4 and compared by inspection (§5), not by assumption:

- **Arabic Wikipedia** (`wikimedia/wikipedia`, `20231101.ar`): all 7 shards, 1,219,201 articles.
- **FineWeb-2** (`HuggingFaceFW/fineweb-2`, `arb_Arab`): one of 25 train shards, `000_00000`, 2,693,000 documents.

For each, 50,000 documents were sampled uniformly (seed 42) for the automatic metrics, and 100 random documents were rated by hand as clean / noisy / list / dialect / other. The Data Spec §8 cleaning filters were then applied to the 200 rated documents to compare the corpora after cleaning (Data Spec §7, "Post-cleaning simulation").

| Evidence | Arabic Wikipedia | FineWeb-2 |
|---|---|---|
| Documents under 50 words (sample) | 30.05% | 0.21% |
| Arabic character ratio (mean) | 0.9832 | 0.9835 |
| Exact / near-duplicate rate | 0.10% / 0.45% | 0.00% / 0.00% |
| Manual score before cleaning (clean / list / noisy) | 40 / 53 / 7 | 71 / 2 / 27 |
| Documents retained after §8 filters (of 100) | 35 | 98 |
| Clean among retained documents | 33 of 35 (94%) | 71 of 98 (72%) |
| Rated-noisy documents removed by the filters | 7 of 7 | 2 of 27 |
| Words after cleaning | ≈214M (full set) | ≈1.3B (estimate, one shard) |
| Tokens after cleaning (1.5–2.5 per word, provisional) | ≈321–535M | ≈2–3.3B |

## Decision

**Arabic Wikipedia (`wikimedia/wikipedia`, `20231101.ar`) is the sole training corpus for v1. FineWeb-2 `arb_Arab` is held in reserve.**

Reasons:

1. **Cleaned Wikipedia is cleaner.** After §8 cleaning, Wikipedia yields 94% clean documents against 72% for FineWeb-2. Wikipedia's defects are structural (stubs, trailing category and reference lines, broken template fields) and are removable by rules: the filters removed 65 of 100 documents, including every document rated noisy and 51 of 53 rated list. FineWeb-2's defects are semantic (SEO spam, machine-translated text, site navigation), and no filter in the spec catches them: only 2 of its 27 noisy documents were removed.
2. **Cleaned Wikipedia is large enough.** About 214M words, or ≈321–535M tokens at the provisional 1.5–2.5 tokens per word, which is sufficient for a 16–26M parameter model at 20 tokens per parameter, within the PRD range (NFR2). It sits at the lower end of the token target: the low estimate is below the 400M floor.
3. **A single controlled source simplifies debugging.** Silent failures are the main project risk (PRD §10); one corpus with a deterministic cleaning pipeline leaves fewer confounders than a heterogeneous web corpus.
4. **FineWeb-2 carries content risks the project has chosen not to handle.** The reading sample contained adult content (document 66) and phone numbers (document 99; both redacted in the published reading-sample file), and, as a qualitative observation (not measured), politically biased media. The demo is public, and content filtering is out of scope (PRD NG8).
5. **Cleaning Wikipedia is deterministic and fits the 3-week timeline.** The rules are a heading-based strip, a length filter, and the existing §8 thresholds. Cleaning FineWeb-2 to a comparable quality would be open-ended research.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| FineWeb-2 alone | Rejected | Reasons 1, 4, and 5: lower clean share after cleaning, no spec filter for its dominant defects, content risks, and open-ended cleaning effort. Its size advantage (billions of tokens) is not needed |
| Mix of Wikipedia and a FineWeb-2 subset | Deferred, not rejected | Would add stylistic diversity (Wikipedia is a single encyclopedic style) but brings in FineWeb-2's noise and content risks. Becomes the first option if a revisit trigger fires |
| One Wikipedia shard only | Not pursued | All 7 shards total 1.32 GB, smaller than one FineWeb-2 shard, and one shard may not be representative |

## Consequences

**Positive**

- A clean, reproducible corpus (fixed 20231101 snapshot) with a rule-based cleaning pipeline.
- No content filtering needed for v1, so PRD NG8 stays unchanged.
- Smaller data and shorter preprocessing, which helps the 6-hour training limit (PRD M3).

**Negative and risks** (also recorded in Data Spec §13)

- **Token supply is tight.** The estimated 321–535M tokens may not reach the 400M floor, and the 20 tokens-per-parameter rule limits the model to ≈16–26M parameters. The model size must be chosen from the measured token count after the tokenizer is trained.
- **Single encyclopedic style.** The model will generate in that tone. To be disclosed in the Model Card.
- **Bot-generated template articles** (for example census-place articles) survive cleaning and may cause repetitive generations. Their share is unknown.
- **License.** Wikipedia is CC BY-SA 3.0 / GFDL. Whether share-alike applies to model weights is unresolved (no legal review). Mitigation: release the weights under CC BY-SA with attribution to Arabic Wikipedia.

**Changes this decision requires**

- Data Spec §8 gains step 3a (Wikipedia structure strip) and makes the boilerplate filter (step 7) web-only.
- The Wikipedia cleaning rules and heading list move into `scripts/prepare_data.py` and `configs/data.yaml` when those are written.

**Limits of the evidence**

- 100 rated documents per corpus and one rater per corpus, with different raters for the two corpora, so rating criteria may differ slightly (95% intervals for the clean share among retained documents: 81–98% for Wikipedia, 63–80% for FineWeb-2). Several ratings were borderline.
- FineWeb-2 was sampled from one shard of 25, and the full-corpus quality may differ.
- The post-cleaning simulation used a heading-based approximation of step 3a, did not apply the line filter or deduplication, and used provisional thresholds. It was run with ad hoc scripts that are not in the repository.
- Tokens per word is a provisional assumption (Data Spec §3), so every token count here is an estimate.
- Licenses were taken from the Data Spec and have not been independently verified.

## Revisit triggers

Reopen this decision if any of the following occurs:

1. **Measured tokens per word is below 1.5** after the tokenizer is trained, so cleaned Wikipedia gives fewer than ≈320M tokens.
2. **The training plan shows the GPU can consume far more tokens than are available** within the 6-hour limit (`06-training-plan.md`).
3. **A small pilot run shows repetitive bot-template generations** that cleaning does not remove.

If FineWeb-2 is added later, a content filter becomes necessary and PRD NG8 must be amended through a new ADR (see PRD §11, Open questions). New quality filters would also be needed, since the current §8 filters do not catch its dominant noise.
