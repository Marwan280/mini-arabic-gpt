# ADR 0002: Tokenizer

| | |
|---|---|
| **Status** | Proposed. Becomes Accepted when the verification in `docs/04-tokenizer-spec.md` §10 passes and its results are recorded in `artifacts/tokenizer/tokenizer_config.yaml` |
| **Date** | 2026-10-09 |
| **Deciders** | Marwan |
| **Related** | `docs/04-tokenizer-spec.md`; `docs/03-data-spec.md` §8, §12; `docs/adr/0001-training-corpus.md`; PRD FR3, G2, NFR2; Design Doc §4.2 |
| **Evidence** | `reports/data-inspection/tokenizer-notes.md`, `char-stats_wikipedia.json` |

## Context

The model needs a tokenizer that turns Arabic text into token IDs and back. The spec (`04-tokenizer-spec.md` §2) sets these requirements:

- **TR1:** trained on the train split only.
- **TR2:** vocabulary of at most 65,535 entries, so IDs fit in `uint16`.
- **TR3:** normalization is part of the tokenizer object, not a separate script.
- **TR4:** any input string can be encoded; no character may fail.
- **TR5:** `decode(encode(text))` equals `normalize(text)`.
- **TR6:** normalization rules live in a configuration table, versioned with the tokenizer.

The corpus is cleaned Arabic Wikipedia (ADR-0001). The character-level measurements in the tokenizer notes (50,000-document sample, cleaned view) show what the tokenizer has to handle:

| Measurement | Value |
|---|---|
| Distinct characters / those occurring once | 2,269 / 875 |
| Distinct characters covering 99% / 99.99% of all characters | 65 / 400 |
| Characters per word, spaces included (50,959,907 over 8,491,335 words) | 6.0 |
| Documents containing a diacritic / fathatan's share of all marks | 73.2% / 37.6% |
| Documents containing Farsi yeh / keheh | 0.94% / 0.45% |
| Tatweel runs that are هـ, بـ or لـ | 76.5% |
| Western digits' share of digit characters | 99.90% |
| Documents containing Latin letters | 36.0% |
| Documents changed by NFC / by NFKC | 0 / 11.9% |
| Arabic comma to ASCII comma | 21.2 to 1 |

**Not yet measured:** tokens per word (the Data Spec's 1.5 to 2.5 is an assumption), compression, vocabulary quality, and everything else that needs a trained tokenizer. Those are the §10 checks.

## Decision

**A byte-level BPE tokenizer with a 32,000-entry vocabulary, trained with Hugging Face `tokenizers`. Normalization and pre-tokenization are declared as a versioned configuration table (`configs/tokenizer.yaml`), and the library's normalizer and pre-tokenizer are built from that table.**

In outline (the rules themselves are in the spec):

- **Algorithm:** byte-level BPE. The 256 byte tokens are always in the vocabulary; three special tokens (`<|endoftext|>` = 0, `<|pad|>` = 1, `<|unk|>` = 2); learned merges start at ID 259.
- **Vocabulary:** 32,000 entries including special tokens. Provisional: 16k and 48k are compared on the validation split in §10 (16k wins if within 5% of 32k; 48k reopens the question if it improves by more than 15%).
- **Library:** Hugging Face `tokenizers`. One `tokenizer.json` holds normalizer, pre-tokenizer, vocabulary, merges, and special tokens, and the same object is loaded in training, evaluation, and the demo.
- **Normalization (spec §4, rules N1 to N14):** NFKC; removal of invisible characters; Farsi yeh and keheh mapped to Arabic yeh and kaf; removal of all Arabic diacritics; tatweel removed only between two Arabic letters; Arabic-Indic and Persian digits mapped to ASCII; Arabic and ASCII punctuation unified for the comma, semicolon, question mark, percent, and dashes. Alef forms, alef maksura versus yeh, and teh marbuta versus heh are deliberately kept distinct.
- **Pre-tokenization (spec §5, rules P1 to P5):** whitespace, Arabic-Latin and digit-letter boundaries (with exceptions for one-letter prefixes and era markers), isolated punctuation, and digit groups of at most three.

Reasons:

1. **Every input is encodable (TR4).** The character inventory has a long tail: 875 of 2,269 characters occur once in the sample. Byte-level BPE covers that tail without reserving vocabulary entries, and `<|unk|>` should never be produced.
2. **One object, one config (TR3, TR6).** Several rules depend on context: tatweel only between two letters, a comma left alone inside a digit run, one-letter prefixes kept with their numbers. A library that builds its normalizer and pre-tokenizer from a table lets the rules live in one versioned file inside the tokenizer file.
3. **It matches the model family.** Byte-level BPE is the GPT-family standard and is supported directly by the chosen library.
4. **The vocabulary fits the budget.** 32,000 is well below the `uint16` limit and is a common size for models of this scale. The cost is the embedding matrix (see Consequences).
5. **The normalization choices rest on measurements.** Each rule in the spec cites a section of the tokenizer notes; the exceptions are listed under "Limits of the evidence".

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| SentencePiece Unigram | Rejected | Reasonable as an algorithm. The spec's objection (§6) is its normalization, a fixed character map; the context-dependent rules above would have to move into a separate preprocessing step outside the tokenizer object, against TR3 and TR6. BPE and Unigram were not compared by training both, so this choice is not an empirical result. |
| Character-level | Rejected | No unknown characters and a small vocabulary (2,269 characters in the sample). But text is about 6.0 tokens per word, against a provisional 1.5 to 2.5 for BPE, so sequences are roughly 2.4 to 4.0 times longer. For a fixed context length the model sees that much less text per sequence, and attention cost grows with the square of sequence length. |
| WordPiece | Rejected | Has no byte-level mode: a character outside the vocabulary becomes `[UNK]`, which conflicts with TR4 and with the rule that `<|unk|>` is never produced. The 875 single-occurrence characters in the sample alone show the tail is real. Its `##` continuation convention and training are designed for BERT-style encoders, and no benefit for a decoder-only model was identified. |
| Vocabulary of 16k or 48k | Deferred to §10 | The size is provisional; the comparison and its decision thresholds are part of the verification. |

## Consequences

**Positive**

- Any text can be encoded, and every rule is a table row with a unit test (spec §10).
- Training, evaluation, and the demo load the same file, so text is processed in exactly one way.
- Normalization is versioned with the tokenizer and cannot drift from the code.

**Negative and risks**

- **The tokenizer is frozen after acceptance.** Any change to the config is a new tokenizer version: a new `tokenizer.json`, a `CHANGELOG.md` entry, and re-encoding of all splits. A trained model is tied to one tokenizer version; changing it means retraining. Perplexity is comparable only within one version, and the evaluation code refuses to compare across versions.
- **Adding FineWeb-2 requires retraining both the tokenizer and the model.** The vocabulary is learned from Wikipedia text alone, so a new corpus means a new train split, a new tokenizer version, and training the model again from scratch, not fine-tuning. The alef, yeh, and teh marbuta decisions (spec §4.8) are reopened at the same time, and ADR-0001's revisit conditions for FineWeb-2 (content filtering, PRD NG8) still apply.
- **Diacritics cannot be generated.** Rule N7 removes all Arabic diacritics before training, so the model never sees one and cannot produce one. "أيضاً" and "أيضا" become identical, and about 22 heavily diacritized documents in the cleaned sample lose theirs. Disclosed in the Model Card.
- **Normalization is lossy.** `decode(encode(text))` equals the normalized text, not the original. The demo shows normalized text; Persian-script yeh and kaf are mapped (which also changes the spelling of Persian words), zero-width non-joiner is removed, and digits and punctuation are unified.
- **The embedding matrix is large for a small model.** It has 32,000 times `d_model` entries. As an illustration (`05-model-architecture.md` is not written yet): 8.2M parameters at `d_model` = 256 and 12.3M at 384, a large share of a 10 to 30M parameter model, even if the input and output matrices are tied.
- **Several rules are provisional** (zero-width non-joiner removal, quote handling, the prefix and era-marker exceptions, digit grouping, the vocabulary size), to be confirmed or changed after training in §10.

**Changes this decision requires**

- `configs/tokenizer.yaml` (the config table) and `src/mini_arabic_gpt/tokenizer.py` (builds the normalizer and pre-tokenizer from it).
- `artifacts/tokenizer/` with `tokenizer.json`, `tokenizer_config.yaml`, and `CHANGELOG.md`; `tests/test_tokenizer.py` with one test per rule.
- `05-model-architecture.md` takes the vocabulary size as an input.

**Limits of the evidence**

- All measurements come from one 50,000-document Wikipedia sample, and the cleaned view only approximates the Data Spec §8 cleaning.
- Fused words, clitic attachment, and spelling variants are measured with pattern proxies, because no Arabic lexicon was available.
- Some statements in the spec's rationale go beyond what the notes measured. For example, the notes show the Farsi-yeh and keheh occurrences in Wikipedia are mostly in Persian and Kurdish words, so mapping them (rule N5) is a design choice, not a measured need. Such cases are listed with the spec's review notes.
- Nothing about tokens per word, compression, or merge quality is known until the tokenizer is trained.
- BPE and Unigram were not compared empirically, and the character-level cost is arithmetic from characters per word before normalization, not a measurement.

## Revisit triggers

Reopen this decision if any of the following occurs:

1. **A §10 check fails:** the round trip, any `<|unk|>` in the encoded splits, more than 10 residue pieces among the 200 most frequent, or the vocabulary-size comparison favouring 16k or 48k.
2. **FineWeb-2 is added to the corpus** (ADR-0001 revisit): the tokenizer and the model are retrained and the §4.8 decisions are reopened.
3. **Measured tokens per word falls outside 1.5 to 2.5:** the Data Spec token budget and ADR-0001's first revisit trigger are re-evaluated.

## Amendment 1 (2026-10-09): vocabulary size 16,000

*The text above is unchanged (it still names 32,000 and the 5% tokens-per-word rule). This section records the vocabulary decision; the status stays Proposed until `docs/04-tokenizer-spec.md` §10 passes.*

| | |
|---|---|
| **Decided by** | Marwan |
| **Evidence** | `docs/06-training-plan.md` §7 and Appendix A (preliminary: scratchpad code, trial tokenizers, not the production pipeline) |

**Decision: the vocabulary has 16,000 entries (including the three special tokens), not 32,000.** The algorithm, library, normalization table, and special-token IDs are unchanged. The byte tokens occupy IDs 3 to 258 and learned merges start at 259, so 15,741 merges are learned.

**Why.** The decision rule changed from tokens per word to validation loss per word, so that vocabularies are compared on modelling the same text. Matched short runs of the `base` model (one pass over the same 18.7M words, two seeds each, trial tokenizers) gave:

| | 32,000 | 16,000 |
|---|---|---|
| Final validation loss per word, mean of 2 seeds (nats) | 7.4037 | **7.3150** |
| Seed-to-seed spread | 0.013 | 0.039 |
| Parameters | 23,111,424 | 16,967,424 |
| Tokens per word (held-out, preliminary) | 1.4755 | 1.6073 (+8.9%) |

The 16k model is lower by 0.089 nats per word (8.5% lower perplexity per word), in both seed pairs, against a larger spread of 0.039. The 5% tokens-per-word rule of `04` §10 would have kept 32k, because 16k needs 8.9% more tokens for the same text; the new rule weighs that against the 26.6% smaller model, 1.54 GiB less memory at micro-batch 16, and 23% higher throughput with the real loader, 74.6k against 60.7k tokens/s (`06` §5).

**Consequences.**

- Embedding matrix: 16,000 × `d_model` = 6.1M parameters at `d_model` = 384, 36.2% of `base` (53.2% at 32,000). The embedding-cost bullet of the Consequences above should be read with these numbers.
- Token supply rises to about 328.0M train tokens (preliminary), so 2 epochs are 38.7 tokens per parameter.
- Sequences are longer in tokens: 512 tokens cover about 318 words instead of 347.
- Changes to `04-tokenizer-spec.md` §6, §9, §10, and `05-model-architecture.md` are listed as proposed edits in `06-training-plan.md` §11 (items 1 to 3 and 10).

**Limits of the evidence.**

- The pilot trains at 1.2 to 1.8 tokens per parameter, a regime that favours the smaller model; it does not show the outcome at 2 epochs on 300M tokens. A longer matched comparison was considered and not scheduled.
- Two seeds per vocabulary; no significance test. The 32k model leads for the first half of the pass and 16k overtakes at 4/6.
- Trial tokenizers trained on 8.7% of the corpus's words with approximated normalization.

**Re-confirmation.** The comparison is repeated on the production tokenizer and splits (`04` §10, proposed rule). If 32,000 then has lower mean validation loss per word by more than the seed spread, this decision is reopened.
