# Data Spec

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Draft (corpus selection pending inspection) |
| **Version** | 0.1 |
| **Last updated** | 2026-10-04 |
| **Depends on** | `01-prd.md`, `02-design-doc.md` §4.1 |

## 1. Purpose

This document specifies the training data: where it comes from, how much is needed, how it is evaluated, cleaned, deduplicated, and split, and what the final dataset looks like.

It is written in two passes. **Pass 1 (this version)** fixes the requirements, the candidate corpora, and the procedure for choosing between them. **Pass 2** records the inspection results, the final choice, and the real dataset statistics. Sections to be completed in pass 2 are marked **[TBD after inspection]**.

## 2. Requirements

| ID | Requirement | Source |
|---|---|---|
| DR1 | Modern Standard Arabic. Dialects are out of scope. | PRD NG1 |
| DR2 | License permits use for training and for a public demo. | PRD §9 |
| DR3 | Free to download, no account-gated or paid sources. | PRD §9 |
| DR4 | Enough tokens for the target model size (see §3). | PRD NFR2 |
| DR5 | Downloadable and processable on the project machine (16 GB RAM, ~100 GB free disk). | PRD §9 |
| DR6 | Documents are available as discrete units, so splitting and deduplication can be done per document. | Design §4.1 |

## 3. How much data

**Rule of thumb:** a language model trained from scratch needs roughly **20 tokens per parameter** to be reasonably trained (the "Chinchilla" ratio). Below this, the model tends to memorize the data rather than learn from it.

| Model size | Minimum tokens (20×) | Comfortable (40×) |
|---|---|---|
| 10M params | 200M | 400M |
| 20M params | 400M | 800M |
| 30M params | 600M | 1.2B |

**Target: 400M–800M training tokens.** This covers a 20M-parameter model comfortably and a 30M model at the minimum.

**Converting text size to tokens:** Arabic tokenizes less efficiently than English. As a working assumption, one Arabic word produces **about 1.5–2.5 subword tokens**, depending on the tokenizer and vocabulary size. So 400M tokens is roughly **160M–270M words**, or about **1.5–2.5 GB of UTF-8 text** (Arabic characters take 2 bytes each). **This assumption is provisional** and will be replaced by a measured value once the tokenizer is trained (`04-tokenizer-spec.md`).

**Training budget check:** PRD M3 limits a training run to 6 hours. The number of tokens the model can actually process in 6 hours is estimated in `06-training-plan.md`. If it is lower than the dataset size, the dataset is not the bottleneck and we simply train on a subset. More data than we can consume is not a problem; too little is.

## 4. Candidate corpora

| | Candidate A: Arabic Wikipedia | Candidate B: FineWeb-2 (Arabic) |
|---|---|---|
| **Source** | `wikimedia/wikipedia`, config `20231101.ar` on the Hugging Face Hub | `HuggingFaceFW/fineweb-2`, config `arb_Arab` on the Hugging Face Hub |
| **Content** | Encyclopedia articles | Filtered web pages from Common Crawl |
| **License** | CC BY-SA 3.0 / GFDL | ODC-By 1.0, subject to Common Crawl terms of use |
| **Approx. size** | ~1.3 GB of Parquet files (7 shards); roughly 1.2M articles | ~57M documents; far larger than needed. Only a subset would be used |
| **Language** | MSA, consistent | Mostly MSA; the `arb_Arab` config is already language-filtered, but some dialect and noise is expected |
| **Expected strengths** | Clean, well-formed, consistent; easy to download in full | Diverse writing styles and topics; very large |
| **Expected weaknesses** | Single style (encyclopedic); many short stub articles, lists, and tables; may be below the token target after cleaning | Web noise (boilerplate, ads, navigation text); quality varies; needs more filtering |
| **Figures to verify** | Article count, word count after cleaning | Per-shard size, documents per shard, noise rate |

**A third option** is a **mix** of both: Wikipedia for a clean base plus a FineWeb-2 subset for diversity. This is considered after inspecting each one separately.

Sizes above come from the Hub pages at the time of writing and are **[TBD after inspection]**: they will be replaced with measured numbers.

## 5. Selection procedure

The choice is made by inspection, not by assumption. The procedure:

1. **Download a sample** from each candidate. One Parquet shard is enough (hundreds of MB), not the full corpus.
2. **Compute the metrics in §6** on each sample with a script (`scripts/inspect_data.py`, written during this phase).
3. **Read 100 random documents** from each sample. Random, not the first 100: the first rows of a file are often not representative.
4. **Fill in the comparison table in §7** with the measured numbers and reading notes.
5. **Decide** and record the decision as `docs/adr/0001-training-corpus.md`.

The inspection script and its output are committed, so the comparison is reproducible.

## 6. Quality metrics

Each metric is computed per candidate on the same sample size.

| Metric | Definition | What it tells us |
|---|---|---|
| **Document count** | Number of documents in the sample | Scale |
| **Word count** | Whitespace-separated tokens, total and per document (mean, median, 5th/95th percentile) | Scale and document length profile. Very short documents are usually stubs or noise |
| **Arabic character ratio** | Arabic letters ÷ all letters, per document | Language purity. Flags documents dominated by Latin text, code, or symbols |
| **Non-letter ratio** | Digits, punctuation, and symbols ÷ all characters | Flags tables, lists, and markup residue |
| **Exact duplicate rate** | Share of documents whose normalized text matches another document exactly | Redundancy; risk of train/test leakage |
| **Near-duplicate rate** | Share of documents sharing a high overlap of word n-grams with another document (MinHash or similar) | Catches templated pages and copies with minor edits |
| **Boilerplate rate** | Share of documents containing common web boilerplate phrases ("اقرأ أيضا", "جميع الحقوق محفوظة", cookie notices, navigation menus) | Web noise (mainly relevant for FineWeb-2) |
| **Diacritics rate** | Share of Arabic characters that are diacritics (tashkeel) | Informs the normalization decision in the Tokenizer Spec |
| **Manual quality score** | For 100 random documents: fraction rated "clean MSA prose" vs. "noisy / list / dialect / other" | The ground truth that the automatic metrics approximate |

## 7. Comparison

**[TBD after inspection]**

| Metric | Arabic Wikipedia | FineWeb-2 Arabic |
|---|---|---|
| Sample size (documents) | | |
| Total words | | |
| Median words per document | | |
| Arabic character ratio (mean) | | |
| Non-letter ratio (mean) | | |
| Exact duplicate rate | | |
| Near-duplicate rate | | |
| Boilerplate rate | | |
| Diacritics rate | | |
| Manual quality score (clean MSA prose) | | |
| Reading notes | | |

**Decision:** [TBD] — see `docs/adr/0001-training-corpus.md`.

## 8. Cleaning pipeline

Applied to every document, in this order. Rules are implemented in `scripts/prepare_data.py` and configured in `configs/data.yaml`. Thresholds marked *provisional* are tuned during inspection.

| Step | Rule | Provisional threshold |
|---|---|---|
| 1. Unicode normalization | Apply NFC normalization so that identical text has identical bytes | — |
| 2. Markup removal | Strip any HTML tags, wiki markup residue, and URLs | — |
| 3. Whitespace normalization | Collapse runs of spaces; collapse 3+ newlines to 2; strip leading/trailing whitespace | — |
| 4. Language filter | Drop documents whose Arabic character ratio is below threshold | < 0.80 |
| 5. Length filter | Drop documents shorter than a minimum word count | < 50 words |
| 6. Non-letter filter | Drop documents whose non-letter ratio is above threshold | > 0.30 |
| 7. Boilerplate filter | Drop documents, or lines, matching the boilerplate list | list in `configs/data.yaml` |
| 8. Line filter | Drop lines with fewer than N words inside otherwise-kept documents (navigation items, list fragments) | < 4 words *(web data only)* |

**Not done here:** diacritic removal, hamza/alef normalization, tatweel removal, and digit normalization. These are tokenizer-level normalization (`04-tokenizer-spec.md`), so that the demo applies the same rules as training.

Every filter logs how many documents it dropped. Those counts go in §11 and in the Model Card.

## 9. Deduplication

Performed **after cleaning and before splitting**, at the document level.

1. **Exact deduplication:** hash each document's normalized text; keep the first occurrence.
2. **Near-deduplication:** MinHash over word 5-grams with a Jaccard similarity threshold of 0.8 *(provisional)*; keep one document per cluster.

Deduplication must run before splitting. Otherwise, copies of the same document can end up in both the training and test sets, and the test perplexity would be artificially low.

## 10. Splitting

| Split | Share | Purpose |
|---|---|---|
| train | 98% | Tokenizer training, model training |
| val | 1% | Loss monitoring during training; all tuning decisions |
| test | 1% | Final evaluation only (PRD M1), never used for tuning |

- **Unit:** the whole document. No document is divided across splits.
- **Method:** shuffle document IDs with a fixed seed (`seed: 42` in `configs/data.yaml`), then slice.
- **Why 98/1/1:** at hundreds of millions of tokens, 1% is already millions of tokens, more than enough for a stable perplexity estimate. Keeping train as large as possible matters more.
- **Integrity check:** a test asserts that the sets of document hashes in the three splits are pairwise disjoint (`08-testing-strategy.md`).

## 11. Final dataset statistics

**[TBD after the pipeline runs]**

| Stage | Documents | Words |
|---|---|---|
| Raw | | |
| After cleaning (per filter counts in the pipeline log) | | |
| After deduplication | | |
| train | | |
| val | | |
| test | | |

Token counts are added after the tokenizer is trained.

## 12. Storage

| Path | Content | Format | In Git? |
|---|---|---|---|
| `data/raw/<corpus>/` | Downloaded shards, unmodified | Parquet | No |
| `data/clean/{train,val,test}.txt` | One document per block, documents separated by a blank line, UTF-8 with `\n` line endings | Text | No |
| `data/clean/stats.json` | Pipeline statistics (§11) | JSON | No; copied into docs |
| `data/clean/manifest.json` | Source corpus, shard names, download date, config hash, seed | JSON | No; copied into docs |

**Document separator:** a dedicated end-of-document token is inserted by the tokenizer stage between documents, so the model learns where documents begin and end. Its exact form is defined in `04-tokenizer-spec.md`.

## 13. Known limitations and risks

| Issue | Impact | Handling |
|---|---|---|
| Web text (FineWeb-2) can contain offensive or biased content | Model may reproduce it | Disclosed in the Model Card (PRD NG8). No content filtering at this scale |
| Wikipedia's single style | Model generates in an encyclopedic tone only | Acceptable for the PRD goals; noted in the Model Card. Mixing in web text is the mitigation if chosen |
| Language filter is character-based, not a real language ID | Some dialect passes through | Acceptable; dialect share is estimated during manual reading |
| Thresholds in §8 are guesses until inspected | Over- or under-filtering | Tuned on the sample; every change recorded with its reason |
| Windows default encoding corrupts Arabic | Silent data corruption | Every file open uses `encoding="utf-8"` (CLAUDE.md rule) |

## 14. Related documents

- `02-design-doc.md` §4.1: data pipeline component
- `04-tokenizer-spec.md`: normalization rules and tokenization
- `08-testing-strategy.md`: split integrity test
- `docs/adr/0001-training-corpus.md`: corpus decision (to be written)