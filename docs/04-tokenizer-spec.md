# Tokenizer Spec

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Draft, pending ADR-0002 |
| **Version** | 0.1 |
| **Last updated** | 2026-10-09 |
| **Depends on** | `03-data-spec.md`, `docs/adr/0001-training-corpus.md`, `reports/data-inspection/tokenizer-notes.md` |
| **Feeds** | `05-model-architecture.md` (vocabulary size), `07-evaluation-plan.md` (perplexity comparability), `09-ui-spec.md` (token display) |

## 1. Purpose

This document specifies how text is converted to token IDs and back: the normalization rules, the pre-tokenization boundaries, the subword algorithm, the vocabulary, the special tokens, and the storage format. The same rules apply at training time, at evaluation time, and in the demo, so that the model always sees text in exactly one form.

Every rule below is justified by a measurement in `tokenizer-notes.md` (cited as **TN §n**). Rules marked **provisional** are confirmed or changed after the tokenizer is trained and inspected (§10).

## 2. Requirements

| ID | Requirement | Source |
|---|---|---|
| TR1 | Subword tokenizer trained on the **train split only**. | PRD FR3, Design §4.2 |
| TR2 | Vocabulary size ≤ 65,535, so token IDs fit in `uint16`. | Design §4.2, D2 |
| TR3 | Normalization is part of the tokenizer object, not a separate preprocessing script. | Design §4.2 |
| TR4 | Any input string can be encoded: no character may fail to tokenize. | Design P4 (fail loudly is for bugs, not for user input) |
| TR5 | `decode(encode(text))` equals `normalize(text)` for every text. | Design §8, round-trip test |
| TR6 | Normalization rules live in a configuration table and are versioned with the tokenizer files. | This doc, §9 |
| TR7 | All I/O is UTF-8. | PRD NFR1 |

## 3. Scope: what the tokenizer does and does not do

**Does:** Unicode normalization, character mapping (§4), pre-tokenization (§5), subword segmentation (§6), special tokens (§7).

**Does not:** markup removal, URL removal, whitespace collapsing beyond the defensive N4, or spacing repair around punctuation. Those are Data Spec §8 steps 2 and 3 and happen before text reaches the tokenizer. The tokenizer must still behave sensibly if such residue reaches it (TR4), but it does not try to fix it.

**Does not:** repair fused words (TN §8). No lexicon is available, and the measured patterns mix defects with legitimate compounds. Fused words are tokenized as they are.

## 4. Normalization rules

Applied in this order, to every string, before pre-tokenization. Each rule is a row in `configs/tokenizer.yaml` (§9).

### 4.1 Unicode form

| Rule | Decision | Evidence |
|---|---|---|
| N1 | Apply **NFKC**. | TN §11: NFC changes 1 document in 50,000; NFKC changes 11.9% of cleaned documents, almost all by converting no-break space (U+00A0) to a space, plus superscripts and the ellipsis character. These compatibility forms carry no meaning the model needs. |

**Consequence to verify (§10):** NFKC also decomposes Arabic presentation forms. TN §11 found none except the ornate brackets ﴾ ﴿, which NFKC leaves unchanged. NFKC also turns ½ into 1⁄2 with a fraction slash (U+2044); N14 maps U+2044 to `/`.

### 4.2 Invisible and control characters

| Rule | Decision | Evidence |
|---|---|---|
| N2 | Remove zero-width joiner (U+200D), zero-width space (U+200B), soft hyphen (U+00AD), byte-order mark (U+FEFF), Arabic letter mark (U+061C), and bidirectional marks and isolates (U+200E, U+200F, U+202A–U+202E, U+2066–U+2069). | TN §11: all rare (< 0.2% of documents). They affect display only. |
| N3 | Remove **zero-width non-joiner** (U+200C). | TN §11: 85 cleaned documents; Persian compound names and list markers ("جهان‌آرا"). *Provisional:* removing it merges the two parts visually; keeping it adds a near-invisible token. Removal is simpler. |
| N4 | Map tab to a space. Collapse any run of spaces to one (defensive; Data Spec §8 step 3 should already have done this). Newlines are kept. | TN §10, §11 |

### 4.3 Script variants

| Rule | Decision | Evidence |
|---|---|---|
| N5 | Map Farsi yeh ی (U+06CC) → Arabic yeh ي (U+064A). Map keheh ک (U+06A9) → Arabic kaf ك (U+0643). | TN §3: these are script variants of Arabic letters; in Wikipedia they occur mostly in Persian and Kurdish words. They are present in 0.94% and 0.45% of cleaned documents. Mapping also makes the demo robust to Persian-layout keyboards. |
| N6 | **Keep** gaf گ, peh پ, tcheh چ, veh ڤ, heh doachashmee ھ, and other extended letters as they are. | TN §3: they represent sounds Arabic letters do not ("نوڤمبر", "ڤولكسڤاغن"). Mapping would change spelling. They are rare and will be covered by the vocabulary or byte fallback (§6). |

### 4.4 Diacritics (tashkeel)

| Rule | Decision | Evidence |
|---|---|---|
| N7 | **Remove all Arabic diacritics**: fathatan, dammatan, kasratan, fatha, damma, kasra, shadda, sukun, maddah and hamza marks (all of U+064B–U+065F), superscript alef (U+0670), and the Quranic annotation marks (U+06D6–U+06ED). | TN §4: 0.86% of Arabic letters plus marks (0.66% of all characters) in cleaned text; 73% of documents contain a mark, but 38% of all marks are fathatan (e.g. أيضاً). Only 1.1% of documents are heavily diacritized. Standard MSA prose is written without diacritics. |

**Consequences:**
- The model cannot generate diacritics. Accepted under PRD goals; disclosed in the Model Card.
- "أيضاً" and "أيضا" become identical, which merges a spelling variant rather than losing information.
- The ~22 heavily diacritized cleaned documents (TN §4) become ordinary text.

### 4.5 Tatweel (kashida)

| Rule | Decision | Evidence |
|---|---|---|
| N8 | Remove tatweel (U+0640) **only when it is between two Arabic letters**. Keep it otherwise. | TN §5: 76.5% of tatweel runs are the connector in the Hijri marker هـ and the prefixes بـ, لـ. Removing tatweel everywhere would rewrite "1313 هـ" as "1313 ه". Tatweel between two Arabic letters is in 3.2% of documents: 19.3% of such runs are a one-letter clitic joined to the next word (بـعملية), 80.7% are inside a longer word. |

**Consequence:** هـ, بـ, لـ remain distinct tokens from ه, ب, ل wherever the tatweel is kept. This is intended. A clitic joined to a following letter loses its tatweel: بـعملية becomes بعملية; accepted.

### 4.6 Digits

| Rule | Decision | Evidence |
|---|---|---|
| N9 | Map Arabic-Indic digits ٠–٩ (U+0660–U+0669) and Persian digits ۰–۹ (U+06F0–U+06F9) → ASCII 0–9. | TN §6: ASCII digits are 99.90% of digit characters. One digit form simplifies the vocabulary and number handling. |
| N10 | Map Arabic decimal separator ٫ (U+066B) → `.` and Arabic thousands separator ٬ (U+066C) → `,`. | TN §6: rare (< 0.2% of documents); consistent with N9. |

### 4.7 Punctuation

| Rule | Decision | Evidence |
|---|---|---|
| N11 | Map ASCII `,` → Arabic comma `،`; `;` → `؛`; `?` → `؟`. | TN §10: Arabic forms dominate 21:1, 16:1, 12:1 in cleaned text. One form per mark. |
| N12 | Map Arabic percent ٪ (U+066A) → `%`. | TN §10: ASCII % dominates 16:1. |
| N13 | Map curly double quotes “ ” and ASCII `"` → the guillemets « » **is not done**. Quotes are kept as they are. | TN §10: guillemets are the Wikipedia style, but ASCII quotes may mark different usage; not measured. Collapsing them is a guess; leaving them costs a few vocabulary entries. *Provisional.* |
| N14 | Map en dash – and em dash — → hyphen-minus `-`. Map minus sign − → `-`. Map the ellipsis character … (after NFKC it is already `...`). Map the fraction slash ⁄ (U+2044), which NFKC produces from ½, to `/`. | TN §10: dash variants carry no meaning difference the model needs. TN §11: NFKC turns ½ (77 raw occurrences) into 1⁄2. |

**Exception to N11:** a comma, semicolon, or question mark that appears **inside a run of Latin letters or digits** (e.g. "1,234", "e.g., ") is left unchanged. *Provisional*: implemented as a context rule; confirmed in §10.

### 4.8 What is deliberately not normalized

| Item | Decision | Evidence and reason |
|---|---|---|
| Alef forms (ا أ إ آ) | **Kept distinct.** | TN §7: Wikipedia spelling is standard. Collapsing loses meaning (أمل/إمل, أن/إن). |
| Alef maksura vs yeh (ى / ي) | **Kept distinct.** | TN §7: ى is 8.3% of the pair; على/علي differ in meaning. |
| Teh marbuta vs heh (ة / ه) | **Kept distinct.** | TN §7: grammatically different. |
| Hamza on waw/yeh (ؤ ئ) | Kept. | Standard orthography. |
| Latin letters and other scripts | Kept, case preserved. | TN §9: 21.3% of documents have a parenthesized Latin phrase; 36% have any Latin. Removing it would damage sentences. |

**Revisit trigger:** if FineWeb-2 is added to the corpus (ADR-0001 revisit), the alef/yeh/teh-marbuta decisions are reopened, because web text has far more non-standard spelling (TN §14: hamza-less "اقامت", "الشركه"). See §11.

## 5. Pre-tokenization

Pre-tokenization decides where a word boundary can never be crossed by a subword piece.

| Rule | Decision | Evidence |
|---|---|---|
| P1 | Split on whitespace. Each space is attached to the **following** word as a prefix marker (the standard "metaspace" convention), so that word starts are distinguishable. | Standard practice; needed for correct detokenization. |
| P2 | Split between an Arabic letter and a Latin letter in both directions. | TN §8: 629 cleaned documents have Arabic directly against Latin ("الCASS", "وIBM"). The Arabic part is a prefix; separating it lets the prefix be shared. |
| P3 | Split between a digit and an Arabic letter in both directions, **except**: do not split a **single** Arabic letter in {و, ب, ل, ف, ك} that precedes a digit, and do not split the era markers م, هـ and ھ (heh doachashmee) that follow a digit. The tatweel in بـ59 is kept by N8 (it is not between two Arabic letters), and the pre-token is بـ. | TN §8: 75% of letter→digit contacts are these one-letter prefixes; 83% of digit→letter contacts are era markers. Splitting them would detach a prefix from its number. TN §3: ھ stands in for the Hijri marker in some articles (111 occurrences in 27 cleaned documents). *Provisional*: the exception list is confirmed in §10. |
| P4 | Punctuation characters are their own pre-tokens (each punctuation character separated from letters on both sides). | TN §8: 7% of cleaned documents have letter-punctuation-letter with no space ("الوقت.وتقول"). Isolating punctuation stops a subword from spanning a sentence boundary. |
| P5 | Digit strings are split into runs of at most 3 digits, from the right. | Standard for small models: "29004" → "29", "004". Keeps the number vocabulary small and the model's arithmetic-adjacent behaviour consistent. *Provisional.* |

## 6. Subword algorithm and vocabulary

| Item | Decision | Reason |
|---|---|---|
| **Algorithm** | **Byte-level BPE** (byte-pair encoding over UTF-8 bytes). | Any input is encodable (TR4): characters outside the vocabulary fall back to byte tokens. TN §13 shows 2,269 distinct characters with a long tail of singletons; byte fallback covers the tail without reserving entries for it. BPE is the GPT-family standard and is well supported by the chosen library. |
| **Vocabulary size** | **32,000** (including special tokens). | Below the `uint16` limit (TR2) with margin. Typical for models in the 10–30M parameter range: the embedding and output matrices are `vocab × d_model`, and at 32k they already dominate parameter count at small `d_model` (see `05-model-architecture.md`). *Provisional*: 16k and 48k are compared in §10 by tokens-per-word on the validation split. |
| **Library** | **Hugging Face `tokenizers`** (Rust core, Python API). | Byte-level BPE, custom normalizer and pre-tokenizer pipelines, one-file serialization (`tokenizer.json`), fast batch encoding, and the same object is loaded in training, evaluation, and the Gradio demo. SentencePiece was considered (see ADR-0002): its Unigram model is a reasonable alternative, but its normalization is a fixed charmap, which fits TR6 less well. |
| **Training data** | `data/clean/train.txt` only (TR1). The full split, not a sample, unless training time exceeds 30 minutes, in which case a seeded uniform sample of documents is used and the sample size recorded. | Data Spec §10 |
| **Byte fallback** | Enabled: the 256 byte tokens are always in the vocabulary. | TR4 |
| **Case** | Preserved. | Latin is a small share; lowercasing would lose proper-noun information for no vocabulary benefit. |

**Allowed under the PRD's "from scratch" definition:** training the tokenizer with a library is explicitly permitted (PRD §4, definition). The model and training loop remain hand-written.

## 7. Special tokens

| Token | ID | Use |
|---|---|---|
| `<|endoftext|>` | 0 | Inserted between documents in the token stream (Data Spec §12). The model learns document boundaries. Also the stop token for generation. |
| `<|pad|>` | 1 | Padding for batched inference in the demo. Never appears in training data. |
| `<|unk|>` | 2 | Reserved; with byte fallback it should never be produced. Its presence in any encoded text is a test failure. |

IDs 3–258 are the 256 byte tokens. Learned merges start at 259.

## 8. Storage format

| File | Content |
|---|---|
| `artifacts/tokenizer/tokenizer.json` | The complete tokenizer: normalizer, pre-tokenizer, vocabulary, merges, special tokens. One file, loaded by `Tokenizer.from_file`. Tracked in git. |
| `artifacts/tokenizer/tokenizer_config.yaml` | Copy of the config used to train it (§9), the train-split manifest hash, the training date, the library version, and the measured statistics from §10. Tracked in git. |
| `artifacts/tokenizer/CHANGELOG.md` | One entry per tokenizer version (§11). |
| `data/tokens/{train,val,test}.bin` | Encoded splits, `uint16`, little-endian, flat; documents separated by `<|endoftext|>`. Git-ignored. |
| `data/tokens/{train,val,test}.meta.json` | Token count, document count, tokenizer file hash, source split hash. Git-ignored. |

**Encoder assertion (Design §4.2):** before writing any `.bin`, assert `max(ids) < 65536` and that the tokenizer hash matches `tokenizer_config.yaml`.

## 9. Configuration

`configs/tokenizer.yaml` declares every rule in §4–§6 as data. Sketch:

```yaml
version: 1
normalization:
  unicode_form: NFKC
  remove: [U+200D, U+200B, U+00AD, U+FEFF, U+061C, U+200E, U+200F, U+202A-U+202E, U+2066-U+2069, U+200C]
  map:
    "ی": "ي"
    "ک": "ك"
    "٠-٩": "0-9"
    "۰-۹": "0-9"
    "٫": "."
    "٬": ","
    ",": "،"
    ";": "؛"
    "?": "؟"
    "٪": "%"
    "–": "-"
    "—": "-"
    "−": "-"
    "⁄": "/"
  remove_diacritics: true
  tatweel: between_letters_only
  punctuation_context_exception: latin_or_digit_run
pretokenization:
  split_arabic_latin: true
  split_digit_letter: true
  digit_letter_exceptions:
    prefix_letters: ["و", "ب", "ل", "ف", "ك"]
    era_suffixes: ["م", "هـ", "ھ"]
  isolate_punctuation: true
  digit_group_size: 3
model:
  type: byte_level_bpe
  vocab_size: 32000
  byte_fallback: true
special_tokens: ["<|endoftext|>", "<|pad|>", "<|unk|>"]
```

The YAML is loaded into a typed dataclass (Design §7). Unknown keys are an error. The Hugging Face normalizer and pre-tokenizer pipelines are **built from this config** by `src/mini_arabic_gpt/tokenizer.py`; no rule is hard-coded.

## 10. Verification after training

The tokenizer is accepted only when all of the following are recorded in `tokenizer_config.yaml`:

| Check | Pass condition |
|---|---|
| **Round trip** | `decode(encode(t)) == normalize(t)` on every document of the validation split and on a fixed list of adversarial strings (mixed scripts, all special characters from TN §11, empty string, one emoji, a 10,000-character line). |
| **No `<|unk|>`** | Zero occurrences across all three encoded splits. |
| **Vocabulary bound** | `max id < 65536`. |
| **Tokens per word** | Measured on the validation split. Replaces the provisional 1.5–2.5 assumption in Data Spec §3. If outside 1.5–2.5, the Data Spec token budget and ADR-0001 trigger 1 are re-evaluated. |
| **Vocabulary size comparison** | Tokens per word at 16k, 32k, 48k on the same validation sample, recorded in a table. 32k stays unless 16k is within 5% of it (then 16k, smaller embedding) or 48k improves by more than 15% (then reconsider). |
| **Top-200 inspection** | The 200 most frequent learned pieces are listed and read by hand. Fail if more than 10 are markup residue, template artifacts (TN §12), or merged punctuation sequences. |
| **Rule spot-checks** | For each normalization rule N1–N14 and pre-tokenization rule P1–P5, a unit test with one input and the expected output (`tests/test_tokenizer.py`). |
| **Era-marker and prefix check (P3)** | "1313 هـ", "791هـ", "1920م", "بـ59", "و2010" tokenize with the marker or prefix as its own piece, not merged into the digits. |
| **Diacritics check (N7)** | A fully diacritized sentence and its undiacritized form encode identically. |

## 11. Versioning and the FineWeb-2 contingency

- The tokenizer is **frozen** once accepted (§10). Any change to the config is a new version, a new `tokenizer.json`, a `CHANGELOG.md` entry, and **re-encoding of all splits**.
- Perplexity is comparable only between runs using the same tokenizer version (Design §9). The evaluation code refuses to compare across versions.
- **If FineWeb-2 is added to the corpus** (ADR-0001 revisit triggers), the tokenizer **must be retrained** on the new train split, because its vocabulary was learned from Wikipedia text alone. That is a new tokenizer version, which in turn means the model is retrained from scratch. The cost of adding FineWeb-2 therefore includes a full tokenizer-plus-model retraining, not a fine-tune. The alef/yeh/teh-marbuta decisions in §4.8 are reopened at the same time. This is recorded as a consequence in ADR-0002.

## 12. Open questions

| Question | Resolved by |
|---|---|
| Final vocabulary size (16k / 32k / 48k) | §10 comparison |
| Keep or remove zero-width non-joiner (N3) | §10 top-200 inspection and round-trip on Persian names |
| Quote normalization (N13) | §10 top-200 inspection: if quote variants fragment the vocabulary, revisit |
| Exact exception list for P3 | §10 era-marker and prefix check |
| Digit grouping (P5) | §10 tokens-per-word; `05-model-architecture.md` if context length is tight |

## 13. Related documents

- `03-data-spec.md` §8 and §12: what reaches the tokenizer and the document separator
- `reports/data-inspection/tokenizer-notes.md`: the measurements behind every rule
- `docs/adr/0002-tokenizer.md`: algorithm, library and vocabulary decision record (proposed)
- `05-model-architecture.md`: consumes the vocabulary size
- `08-testing-strategy.md`: tokenizer tests