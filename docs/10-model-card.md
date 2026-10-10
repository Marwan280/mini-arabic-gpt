# Model Card (outline)

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Outline only, version 0.1. The card is completed after the main run and the evaluation (task 1 of §7); no result in this file is a result |
| **Version** | 0.1 |
| **Last updated** | 2026-10-10 |
| **Depends on** | `01-prd.md` (G6, NG1 to NG8, deliverable 6), `docs/adr/0001-training-corpus.md` to `docs/adr/0008-model-licence.md`, `03-data-spec.md` §11, §13, `04-tokenizer-spec.md`, `05-model-architecture.md`, `06-training-plan.md`, `07-evaluation-plan.md` §5.6, §12, `09-ui-spec.md` §5.3 |
| **Feeds** | the repository README; the optional Hugging Face model repository (`09-ui-spec.md` §9) |

## 1. Purpose

This file fixes what the final Model Card must contain, where each part comes from, when it can be filled in, and which statements are mandatory because an earlier document promised them. It is an outline: it contains no results, because none exist yet. The final card is written as `README.md` of the model repository (if the weights are published) and linked from the project README either way.

## 2. Format and metadata

A Hugging Face model card is a Markdown file whose YAML section at the top holds metadata ([Model Cards](https://huggingface.co/docs/hub/model-cards)): language, tags, license, datasets, and other fields that support discovery and show the licence. The `library_name` field is recommended for a model that is not a `transformers` model. The licence identifier `cc-by-sa-4.0` is in the Hub's list ([Licenses](https://huggingface.co/docs/hub/repositories-licenses)).

Draft of the metadata (values marked * depend on later decisions):

```yaml
---
license: cc-by-sa-4.0            # * provisional, ADR-0008
language:
  - ar
library_name: pytorch
pipeline_tag: text-generation
tags:
  - arabic
  - modern-standard-arabic
  - causal-lm
  - from-scratch
datasets:
  - wikimedia/wikipedia          # Arabic subset, 20231101.ar
---
```

No `base_model` field: the model is trained from scratch (PRD NG5). Evaluation results are given in a table in the card body; the structured `model-index` format is not planned.

## 3. Section outline

| # | Section | Content | Source | Can be filled when |
|---|---|---|---|---|
| 1 | Summary | what the model is, size, what it does and does not do (it continues text; it does not answer questions) | `01-prd.md` §1, NG2, NG3 | now (text), final numbers after the main run |
| 2 | Model details | architecture (decoder-only, pre-LN, learned positions, tied head), layers, width, heads, context 512, parameter count, vocabulary, tokenizer type, normalization | `05` §3 to §5, `04` | after the vocabulary is confirmed (`04` §10) |
| 3 | Intended use and out of scope | study and demonstration; not for facts, advice, chat, dialects, safety-critical use | PRD NG1 to NG4, NG8 | now |
| 4 | How to use | code to load the weights and tokenizer and generate; the launch command of the local demo | `09` §5, `05` §10 | after the code exists |
| 5 | Training data | Arabic Wikipedia, `wikimedia/wikipedia` `20231101.ar`, 1,219,201 articles; cleaning steps and counts; deduplication; splits (98/1/1); final token and word counts; licence of the text | `03` §8 to §11, ADR-0001 | after the pipeline's final statistics (`03` §11) |
| 6 | Training procedure | seed, optimizer and schedule, batch, epochs, precision, hardware (RTX 5050 Laptop, 8 GB), run time, config hash, tokenizer hash, commit | `06` §4, §6, ADR-0004 | after the main run |
| 7 | Evaluation | the tables of §4 below | `07` §4 to §5.7 | after the evaluation (`07` §7) |
| 8 | Limitations | the list of §5 below | ADR-0001 to ADR-0005, `07` §12 | text now, numbers later |
| 9 | Risks and ethical considerations | unfiltered output; biases of Wikipedia as a source; the probe results in one line each; the policy of not quoting explicit or hateful text | `07` §5.6, PRD NG8 | after the probes are run |
| 10 | Environmental cost | GPU hours of the pilots and the main run on a laptop GPU | `06` §5 (estimate 2.4 h for the main run), run logs | after the runs |
| 11 | Licence and attribution | the block of §6 below | ADR-0008 | now (provisional) |
| 12 | Citation and contact | how to cite; the two authors and their parts (README Contributors) | README | now |
| 13 | Version and reproducibility | model version, config and tokenizer hashes, the commit, how to reproduce | `06` §4.8, `07` §6 | after the main run |

## 4. Evaluation section: what it must report

All of it comes from `reports/eval/<run>/` (`07` §6). Nothing is reported that the protocol of `07` did not produce.

| Item | Content |
|---|---|
| M1 | loss per word, per token, and bits per byte of the model and of the baseline on the test split, under both scoring protocols; the difference with its 95% bootstrap interval; the documents where the model is better; the baseline's order and measured memory |
| M2 | each rater's acceptable rate for the model and for the baseline with Wilson intervals; raw agreement and Cohen's kappa; the breakdown by criterion (G, C, D, S) |
| Diagnostics | distinct-1 and distinct-2, repeated 4-grams, lengths, script shares, `<\|unk\|>` count, verbatim-copy rate |
| Choices | the vocabulary decision and its evidence (`06` §7) and the training budget (2 epochs) |
| Honesty notes | the numbers of the pilot are not results; any provisional value is marked |

## 5. Mandatory limitations (each promised by an earlier document)

| Limitation | Source |
|---|---|
| Trained on Arabic Wikipedia only: encyclopedic register, topic coverage and bias of the source, no dialects, no informal text | ADR-0001, PRD NG1 |
| Does not answer questions, follow instructions, or chat; output may be false | PRD NG2, NG3 |
| Cannot generate diacritics; normalization is lossy (the demo shows normalized text); the tokenizer is frozen | ADR-0002 |
| Small model with a large embedding share (36% of the parameters at V = 16,000); context limited to 512 tokens by learned positions | ADR-0003, `05` §6 |
| Trained for 2 epochs over the data, so some text is seen twice; some generated text may repeat training text (the rehearsal measured 1.9% of 8-token windows for a weak pilot) | ADR-0004, `07` §5.7 |
| The vocabulary was chosen on short-run evidence; hyperparameters were not tuned | ADR-0002 Amendment 1, `06` §9 |
| The two raters of the human evaluation are the authors; 50 prompts cannot distinguish a true rate of 70% from 60%; the baseline may be weakened by memory limits (state the order used) | ADR-0005 |
| Unfiltered: may produce offensive text; the probe results are described in one line each, with no verbatim explicit or hateful text | ADR-0005, PRD NG8 |
| Whether the share-alike condition of the source licence applies to the weights is unsettled; the weights are released under the same licence as a precaution | ADR-0008 |
| Any known defect still open at release (for example the pre-tokenization rule interaction of EXP-005 if `04` has not resolved it) | experiment log |

The short statement that the demo shows (`09` §5.3) is this table in two sentences. Both come from one file, `app/limitations.md`, quoted verbatim in section 8 of the card; a test checks that they match (`09` §8).

## 6. Licence and attribution block (provisional text)

> **Weights and card:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). **Code:** MIT (see `LICENSE` of the repository).
>
> **Training data:** the Arabic Wikipedia text of the `wikimedia/wikipedia` dataset (snapshot `20231101.ar`), written by Wikipedia contributors and made available under the Creative Commons Attribution-ShareAlike 3.0 licence and the GNU Free Documentation License; see <https://dumps.wikimedia.org/legal.html> for the terms and <https://ar.wikipedia.org> for the authors.
>
> **Note:** it is not settled whether the share-alike condition applies to the trained weights; they are released under CC BY-SA as the conservative choice (ADR-0008).

The reasoning, the sources, and the alternatives are in ADR-0008.

## 7. Tasks and open items

| # | Task | Owner / place |
|---|---|---|
| 1 | Complete sections 2, 5 to 10 and 13 from the final results; this is the last documentation task before presentation | `11-roadmap.md` |
| 2 | Review the Arabic texts and the limitations wording with a native speaker | `11-roadmap.md` (task 1 of `09` §10.3) |
| 3 | Decide whether the weights are published on the Hub (model repository only) and, if so, add the YAML metadata of §2 | the author, post-v1 |
| 4 | Keep this outline and ADR-0008 in step: if the licence changes, section 11 and the metadata change | whoever changes the licence |

## 8. Related documents

- `01-prd.md`: deliverable 6, NG1 to NG8
- `03-data-spec.md` §11, §13
- `09-ui-spec.md` §5.3, §9: the shared limitations text, the optional publication
- `07-evaluation-plan.md` §5.6, §12: probe policy, items carried to this card
- `docs/adr/0008-model-licence.md`: the licence decision
