# Data Spec

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Corpus selected (ADR-0001) |
| **Version** | 0.2 |
| **Last updated** | 2026-10-08 |
| **Depends on** | `01-prd.md`, `02-design-doc.md` §4.1 |

## 1. Purpose

This document specifies the training data: where it comes from, how much is needed, how it is evaluated, cleaned, deduplicated, and split, and what the final dataset looks like.

It is written in two passes. **Pass 1** fixed the requirements, the candidate corpora, and the procedure for choosing between them. **Pass 2** recorded the inspection results and the final choice (`adr/0001-training-corpus.md`), and is complete except for the final dataset statistics (§11), which wait for the pipeline run and are marked **[TBD after the pipeline runs]**.

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
| **Size (measured)** | 7 shards, 1,323 MB of Parquet (408 / 172 / 145 / 131 / 65 / 156 / 246 MB); 1,219,201 articles | 25 train shards of 1.67–4.84 GB each (106 GB in total, per the Hub file listing); shard `000_00000` is 4.84 GB and holds 2,693,000 documents. The Hub reports ~57M documents in total (not measured here; scaling shard `000_00000` by file size gives ≈59M). Far larger than needed. Only a subset would be used |
| **Language** | MSA, consistent | Mostly MSA; the `arb_Arab` config is already language-filtered, but some dialect and noise is expected |
| **Expected strengths** | Clean, well-formed, consistent; easy to download in full | Diverse writing styles and topics; very large |
| **Expected weaknesses** | Single style (encyclopedic); many short stub articles, lists, and tables; may be below the token target after cleaning | Web noise (boilerplate, ads, navigation text); quality varies; needs more filtering |
| **Figures verified** | Article count: 1,219,201 (measured). Word count after cleaning: ≈214M (estimate from the full set, §7) | Shard size: 1.67–4.84 GB. Documents in shard `000_00000`: 2,693,000 (measured). Noise rate: see §7 |

**A third option** is a **mix** of both: Wikipedia for a clean base plus a FineWeb-2 subset for diversity. This is considered after inspecting each one separately.

Sizes above are measured (source: `reports/data-inspection/metrics.json`; the Hub revisions are pinned in `scripts/inspect_data.py`) unless marked as Hub-reported or estimated.

## 5. Selection procedure

The choice is made by inspection, not by assumption. The procedure:

1. **Download a sample** from each candidate. For Arabic Wikipedia, all 7 Parquet shards were used (1.32 GB, the full corpus): it is smaller than a single FineWeb-2 shard, and one Wikipedia shard may not be representative (shard order may follow article ID; not verified). For FineWeb-2, one shard was used, `000_00000` (4.84 GB, 2,693,000 documents), not the full corpus. An earlier version of this step said one shard is "hundreds of MB"; that was an unverified assumption that holds for Wikipedia shards (65–408 MB) but not for FineWeb-2 (see EXP-001 in `experiments/experiment-log.md`).
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
| **Non-letter ratio** | Digits, punctuation, and symbols ÷ all non-whitespace characters | Flags tables, lists, and markup residue |
| **Exact duplicate rate** | Share of documents whose normalized text matches another document exactly | Redundancy; risk of train/test leakage |
| **Near-duplicate rate** | Share of documents sharing a high overlap of word n-grams with another document (MinHash or similar) | Catches templated pages and copies with minor edits |
| **Boilerplate rate** | Share of documents containing common web boilerplate phrases ("اقرأ أيضا", "جميع الحقوق محفوظة", cookie notices, navigation menus) | Web noise (mainly relevant for FineWeb-2) |
| **Diacritics rate** | Share of Arabic characters that are diacritics (tashkeel) | Informs the normalization decision in the Tokenizer Spec |
| **Manual quality score** | For 100 random documents: fraction rated "clean MSA prose" vs. "noisy / list / dialect / other" | The ground truth that the automatic metrics approximate |

## 7. Comparison

Measured with `scripts/inspect_data.py` (seed 42): 50,000 documents drawn uniformly at random from each candidate. Exact duplicates are computed over the full data; near-duplicates on the sample only, so that rate is a lower bound. Source: `reports/data-inspection/metrics.json` and `metrics.md`.

| Metric | Arabic Wikipedia | FineWeb-2 Arabic |
|---|---|---|
| Documents in full set | 1,219,201 (all 7 shards) | 2,693,000 (shard `000_00000` only) |
| Sample size (documents) | 50,000 | 50,000 |
| Total words (sample) | 11,173,499 | 25,682,592 |
| Median words per document (mean) | 74 (223.5) | 267 (513.7) |
| Share of documents under 50 words | 30.05% | 0.21% |
| Arabic character ratio (mean) | 0.9832 | 0.9835 |
| Non-letter ratio, excluding whitespace (mean) | 0.0686 | 0.0375 |
| Exact duplicate rate | 0.10% (full set) | 0.00% (full shard) |
| Near-duplicate rate | 0.45% (sample; lower bound) | 0.00% (sample; lower bound) |
| Boilerplate rate | 0.64% (inflated by false positives, see below) | 3.08% |
| Diacritics rate (pooled) | 0.72% | 1.23% |
| Manual quality score (clean MSA prose) | 40% (40 clean / 53 list / 7 noisy) | 71% (71 clean / 2 list / 27 noisy) |
| Reading notes | See "Reading notes" below | See "Reading notes" below |

- **Non-letter ratio:** the denominator excludes whitespace, as defined in §6. An earlier version of §6 said "÷ all characters"; the whitespace exclusion was chosen when the inspection was specified.
- **Wikipedia boilerplate rate:** dominated by false positives. On the full Wikipedia set, the phrases "اقرأ أيضا" / "اقرأ أيضاً" and "مواضيع ذات صلة" occur almost always as standalone section-heading lines (for example in 2,320 of the 2,331 documents containing "اقرأ أيضاً", and in 1,403 of the 1,422 containing "مواضيع ذات صلة"). See EXP-003.
- **Manual quality score:** 100 documents per corpus, drawn uniformly at random (seed 42) and rated as clean / noisy / list / dialect / other. The ratings are in `reports/data-inspection/reading_sample_wikipedia.txt` and `reading_sample_fineweb2.txt`. No document was rated dialect or other. Document text was capped at 3,000 characters. With n = 100 each score has roughly ±10 points of sampling uncertainty (95%).
- Wikipedia rated by Marwan; FineWeb-2 rated by Ghada.

### Post-cleaning simulation

Raw numbers are misleading before cleaning, so the §8 filters were applied to the 200 rated documents (100 per corpus). Simulated: for Wikipedia, removal of the trailing sections from the first reference-type heading to the end of the article (step 3a); then, for both corpora, the length filter (< 50 words), the language filter (Arabic ratio < 0.80), the non-letter filter (> 0.30, excluding whitespace), and a document-level boilerplate check. Not simulated: Unicode, markup, and whitespace steps, the line filter, empty-section removal, and deduplication.

| | Arabic Wikipedia | FineWeb-2 Arabic |
|---|---|---|
| Documents retained (of 100) | 35 | 98 |
| Rated clean, retained | 33 of 40 | 71 of 71 |
| Rated list, retained | 2 of 53 | 2 of 2 |
| Rated noisy, retained | 0 of 7 | 25 of 27 |
| **Clean among retained documents** | **33 of 35 (94%)** | **71 of 98 (72%)** |

- **Why documents were removed:** Wikipedia, 65 documents, 62 of them flagged by the length filter (a document can trigger more than one filter). FineWeb-2, 2 documents, both by the boilerplate filter, both rated noisy.
- **Uncertainty:** the 95% Wilson intervals for the clean share among retained documents are 81–98% (Wikipedia) and 63–80% (FineWeb-2). They do not overlap, but each rests on 100 documents and one rater per corpus (different raters, so criteria may differ slightly).
- **Wikipedia after cleaning, full set:** 273.8M raw words in 1,219,201 articles. After stripping the trailing sections and keeping articles with at least 50 remaining words: **≈214.1M words in 490,832 articles** (40.3% of articles, 78.2% of raw words). At 1.5–2.5 tokens per word (provisional, §3) this is ≈321–535M tokens.
- **FineWeb-2 after cleaning, shard `000_00000`:** ≈1.3B words (estimate: 513.7 mean words × 2,693,000 documents ≈ 1.38B raw words, with about 98% of documents retained in the simulation). Not computed on the full shard.
- **Reproducibility:** this simulation and the Wikipedia full-set word counts were computed with ad hoc analysis scripts that are not in the repository. The figures are to be re-derived from the per-filter counts logged by `scripts/prepare_data.py` (§8, §11).

### Reading notes

> Wikipedia: over half of the sample is template-generated stubs (villages, athletes, species) whose text is mostly category lines; full articles are high quality but few; some broken templates with missing words. FineWeb-2: diverse topics and longer complete articles, but a meaningful share of SEO spam, machine-translated text and site navigation; one pornographic document and phone numbers passed the publisher's filters; 'noisy' in my ratings includes most list-like pages; two were rated list.

**Decision:** Arabic Wikipedia (wikimedia/wikipedia, 20231101.ar) as the sole training corpus for v1. FineWeb-2 arb_Arab held in reserve. See docs/adr/0001-training-corpus.md.

## 8. Cleaning pipeline

Applied to every document, in this order. Rules are implemented in `scripts/prepare_data.py` and configured in `configs/data.yaml`. Thresholds marked *provisional* are tuned during inspection.

| Step | Rule | Provisional threshold |
|---|---|---|
| 1. Unicode normalization | Apply NFC normalization so that identical text has identical bytes | — |
| 2. Markup removal | Strip any HTML tags, wiki markup residue, and URLs | — |
| 3. Whitespace normalization | Collapse runs of spaces; collapse 3+ newlines to 2; strip leading/trailing whitespace | — |
| 3a. Wikipedia structure strip *(Wikipedia only)* | Remove the trailing sections of each article, from the first reference-type heading to the end of the document (for example "مراجع", "المراجع", "مصادر", "وصلات خارجية", "روابط خارجية", "انظر أيضا", "اقرأ أيضا", "مواضيع ذات صلة"). In this corpus those sections hold reference, link, and category lines rather than prose. Also drop empty section headings. Runs before steps 4–8, so the length filter counts prose words only | heading list in `configs/data.yaml` |
| 4. Language filter | Drop documents whose Arabic character ratio is below threshold | < 0.80 |
| 5. Length filter | Drop documents shorter than a minimum word count | < 50 words |
| 6. Non-letter filter | Drop documents whose non-letter ratio is above threshold | > 0.30 |
| 7. Boilerplate filter | Drop documents, or lines, matching the boilerplate list | list in `configs/data.yaml` *(web data only)* |
| 8. Line filter | Drop lines with fewer than N words inside otherwise-kept documents (navigation items, list fragments) | < 4 words *(web data only)* |

**Not done here:** diacritic removal, hamza/alef normalization, tatweel removal, and digit normalization. These are tokenizer-level normalization (`04-tokenizer-spec.md`), so that the demo applies the same rules as training.

Every filter logs how many documents it dropped. Those counts go in §11 and in the Model Card.

**Notes from the corpus inspection (§7):**

- **Step 3a** exists because trailing category and reference lines dominate short Wikipedia articles: in the 100-document Wikipedia sample, 32 articles had more than half of their text after the first reference-type heading. The post-cleaning simulation used only the headings "مراجع", "المراجع", "مصادر", "المصادر", "وصلات خارجية", "روابط خارجية", "الوصلات الخارجية", "انظر أيضا" / "انظر أيضاً", and "معرض صور", and did not apply the empty-heading rule, so its figures are approximate.
- **Step 7 is web-only** because on Wikipedia the boilerplate phrases "اقرأ أيضا" and "مواضيع ذات صلة" match ordinary section headings (EXP-003). In the simulation it removed none of the 100 Wikipedia documents.
- **Steps 4–7 do not catch SEO spam, machine-translated text, or site navigation.** In the simulation they removed only 2 of the 27 FineWeb-2 documents rated noisy (both through the boilerplate filter). This matters if FineWeb-2 is ever added: new filters would be needed, and their effect is unknown.

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
| Cleaned Wikipedia yields an estimated 321–535M tokens (≈214M words at 1.5–2.5 tokens per word, provisional ratio): the low end is below the 400M floor of the §3 target | Supports only ≈16–26M parameters at 20 tokens per parameter, with little margin for the upper end of the PRD range (30M) | Choose model size from the token count measured after the tokenizer is trained (`05-model-architecture.md`). Revisit the corpus choice if tokens per word is below 1.5 or the training budget needs more data (`adr/0001-training-corpus.md`). FineWeb-2 is held in reserve |
| Bot-generated template articles survive cleaning (for example US census-place articles such as document 75 of the Wikipedia reading sample: repeated demographic sentences, missing units, numeric artifacts such as `128.93040000000002`) | Model may generate repetitive, template-like text; near-deduplication (§9) may not catch them because the numbers differ | Not quantified: the share of such articles in the corpus is unknown. Watch for it in the pilot run and in the qualitative evaluation (`07-evaluation-plan.md`); add template-aware filtering if it appears |
| Whether the CC BY-SA 3.0 share-alike condition applies to model weights trained on Wikipedia text is unresolved (no legal review; not verified) | Licensing of the released checkpoint | Release the weights under CC BY-SA with attribution to Arabic Wikipedia |

## 14. Related documents

- `02-design-doc.md` §4.1: data pipeline component
- `04-tokenizer-spec.md`: normalization rules and tokenization
- `08-testing-strategy.md`: split integrity test
- `docs/adr/0001-training-corpus.md`: corpus decision (accepted)