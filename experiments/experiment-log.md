# Experiment Log

## Entry template

Copy this block for each new entry. Use the next free ID. Dates are ISO (YYYY-MM-DD).

```
### EXP-NNN: <short title>

- **ID:** EXP-NNN
- **Date:** YYYY-MM-DD
- **Stage:** <pipeline stage, for example data download, tokenizer, training>
- **What happened:**
- **How it was caught:**
- **Root cause:**
- **Fix:**
- **Lesson:**
```

## Entries

### EXP-001: Shard size in the Data Spec was an unverified assumption

- **ID:** EXP-001
- **Date:** 2026-10-05
- **Stage:** Data selection (planning the corpus inspection)
- **What happened:** Data Spec §5 (v0.1) said one Parquet shard per candidate is "hundreds of MB". The FineWeb-2 shard `000_00000` is 4.84 GB (2,693,000 documents), and the 25 train shards range from 1.67 to 4.84 GB.
- **How it was caught:** By Claude while writing the inspection plan, from a read-only listing of file sizes on the Hugging Face Hub, before anything was downloaded.
- **Root cause:** The figure was an unverified assumption. It holds for the Wikipedia shards (65–408 MB), not for FineWeb-2.
- **Fix:** Data Spec §4 and §5 corrected with measured sizes. The plan was changed to download the full 4.84 GB shard, and all 7 Wikipedia shards.
- **Lesson:** Every number in a doc must cite a source or be marked as an estimate.

### EXP-002: FineWeb-2 download failed with a xet/CAS error

- **ID:** EXP-002
- **Date:** 2026-10-05
- **Stage:** Data download (FineWeb-2 shard `000_00000`)
- **What happened:** The first full run of `scripts/inspect_data.py` aborted after about 30 minutes while downloading the 4.84 GB shard, with `RuntimeError: ... CAS Client Error: Format error: I/O error: error decoding response body`. Nothing from the failed attempt was kept in the cache. The Wikipedia shards had downloaded fine.
- **How it was caught:** The script exited with a traceback. The xet log (`~/.cache/huggingface/xet/logs`) showed repeated `s3::get_range` retries with the connection flagged as struggling, then "No more retries; aborting".
- **Root cause:** Not determined. The failure was in the xet transfer path; whether the cause was the local network or the xet backend could not be established from the log.
- **Fix:** Rerun with `HF_HUB_DISABLE_XET=1` (plain HTTPS, about 2.3 MB/s). The download completed.
- **Lesson:** Record environment workarounds in CLAUDE.md and README. (CLAUDE.md updated; README not yet updated.)

### EXP-003: Generic boilerplate list gave false positives on Wikipedia

- **ID:** EXP-003
- **Date:** 2026-10-05
- **Stage:** Data inspection (quality metrics)
- **What happened:** The boilerplate phrase list, written for web text, flagged Wikipedia documents on "اقرأ أيضا" / "اقرأ أيضاً" (250 + 95 documents in the 50,000-document sample) and "مواضيع ذات صلة" (62). These are ordinary Wikipedia section headings, so they inflated Wikipedia's boilerplate rate (0.64%). A later scan of the full Wikipedia set confirmed it: for example, in 2,320 of the 2,331 documents containing "اقرأ أيضاً" the match is a standalone heading line.
- **How it was caught:** Through the per-phrase hit counts printed next to the aggregate rate in `metrics.md`.
- **Root cause:** One generic list was applied to both corpora without checking how it behaves on encyclopedic text.
- **Fix:** The boilerplate filter is web-only in Data Spec §8 (step 7), and those headings are treated as trailing sections to strip in Wikipedia (step 3a). In the post-cleaning simulation the filter removed none of the 100 Wikipedia documents.
- **Lesson:** Calibrate filters per source; always report per-item counts next to aggregate rates.

### EXP-004: Raw volume pointed to FineWeb-2; simulated cleaning reversed it

- **ID:** EXP-004
- **Date:** 2026-10-08
- **Stage:** Corpus selection
- **What happened:** The initial lean was FineWeb-2, based on raw volume and on the raw manual scores (71% clean against 40% for Wikipedia). Rating 200 documents by hand and then applying the Data Spec §8 filters to them reversed the conclusion: among the documents retained after cleaning, 94% were clean for Wikipedia and 72% for FineWeb-2. Wikipedia keeps 35 of the 100 rated documents (40% of articles in the full set) but about 78% of its raw words, and the cleaned corpus (≈214M words) is still large enough.
- **How it was caught:** By running the cleaning filters over the rated documents instead of comparing the raw numbers.
- **Root cause:** The corpora were compared before cleaning. Wikipedia's defects are structural (stubs, trailing category lines) and hid the quality of its articles, while raw size and the raw clean rate favoured FineWeb-2.
- **Fix:** Decision recorded in `docs/adr/0001-training-corpus.md`; the post-cleaning simulation added to Data Spec §7.
- **Lesson:** Raw size is misleading before cleaning; compare corpora after simulated cleaning, not before.

### EXP-005: Pre-tokenization rules P3 and P5 conflict on digits with a one-letter prefix

- **ID:** EXP-005
- **Date:** 2026-10-09
- **Stage:** Tokenizer specification (trial tokenizer for `05-model-architecture.md`)
- **What happened:** Implementing the rules of `docs/04-tokenizer-spec.md` §5 as regular expressions for a trial tokenizer showed that "و2010" becomes the pre-tokens "و2" and "010". P3 (a one-letter prefix is not split from a following digit) plus P5 (digit groups of at most three, counted from the right) attach the prefix to the first, shorter digit group. The check in §10 expects the prefix "as its own piece, not merged into the digits". Related results: "بـ59" stays one pre-token, "791هـ" stays one pre-token, "1920م" becomes "1" and "920م", "29004" becomes "29" and "004".
- **How it was caught:** By running the rules on real text (measurement), not by reading the spec; the spec reads as consistent.
- **Root cause:** Two rules were specified separately and their interaction on the same characters was not tested before writing §10's expected behaviour.
- **Fix:** Not applied. Two options are recorded in `05-model-architecture.md` §13 (item 5): keep the prefix with the digits and reword §10, or make the prefix its own pre-token and reword P3. The decision belongs to `04` (Part D of the spec work). The §10 unit tests must cover prefix plus digits, and the era-marker cases above.
- **Lesson:** Test rule interactions on real strings when the rules are written, not only each rule alone.
