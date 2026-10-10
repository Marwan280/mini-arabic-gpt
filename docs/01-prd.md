# Product Requirements Document (PRD)

| | |
|---|---|
| **Project** | mini-arabic-gpt |
| **Status** | Draft |
| **Version** | 0.1 |
| **Last updated** | 2026-10-10 |

## 1. Overview

mini-arabic-gpt is a small GPT-style language model implemented from scratch in PyTorch and trained on Modern Standard Arabic (MSA) text. Given the beginning of an Arabic sentence, it generates a continuation.

The project shows the full lifecycle of building a language model: data collection and cleaning, tokenizer training, model implementation, training, evaluation, and a local demo. Every stage is documented before it is built, and every significant decision and mistake is recorded.

The goal is not a capable model. The goal is a **correct, well-understood, and well-documented** one.

## 2. Problem statement

Most entry-level ML portfolio projects fine-tune an existing model or call an API. They show that a candidate can use tools, not that they understand what happens inside a language model or can catch it when it silently goes wrong.

This project addresses that gap. Building every component from scratch, and documenting how each one was verified, provides direct evidence of:

- Understanding of the transformer architecture and the language-modeling objective.
- The ability to detect and fix silent failures: bugs that produce wrong results without raising errors.
- Engineering discipline: specifications, decision records, tests, and reproducible experiments.

## 3. Goals

| ID | Goal |
|---|---|
| G1 | Implement a decoder-only transformer (GPT architecture) from scratch in PyTorch. |
| G2 | Train a subword tokenizer on Arabic text, with documented normalization decisions. |
| G3 | Train the model on a single consumer GPU (8 GB VRAM) within the project timeline. |
| G4 | Evaluate the model against a baseline, both quantitatively and qualitatively. |
| G5 | Provide an interactive demo (Gradio) that runs locally on the project machine. Publishing it publicly is an optional step after v1 (`09-ui-spec.md` §9). |
| G6 | Document every component, decision, and caught mistake, to the standard of a professional engineering team. |

## 4. Non-goals

The following are explicitly **out of scope**. Work that drifts toward any of them should be stopped and flagged.

| ID | Non-goal | Reason |
|---|---|---|
| NG1 | Arabic dialects, including Egyptian Arabic | Clean MSA data is far more available. Dialects are a possible future extension. |
| NG2 | Chat, instruction following, or question answering | Requires instruction-tuning data and a far larger model. |
| NG3 | Factual accuracy | A model of this size cannot store reliable knowledge. Generated text may be fluent but false. |
| NG4 | Competing with existing Arabic LLMs | Not achievable at this scale, and not the point of the project. |
| NG5 | Using pretrained weights or pretrained model classes (e.g. Hugging Face `transformers` model implementations) | Defeats the from-scratch objective. |
| NG6 | Multi-GPU or distributed training | Hardware is a single laptop GPU. |
| NG7 | A production API or a custom web frontend (React, FastAPI, etc.) | The demo uses Gradio. A custom stack would consume time needed for the model. |
| NG8 | Content filtering or safety tuning | Out of scope at this scale. Known limitations are disclosed in the Model Card. |

**Definition of "from scratch":** the model architecture, training loop, and generation logic are written by hand in PyTorch. Using libraries for supporting tasks is allowed: downloading datasets, training the tokenizer, numerical computation, and building the demo UI. Each library choice is recorded in an ADR.

## 5. Target audience

| Audience | What they need |
|---|---|
| **Hiring managers and ML engineers** reviewing the portfolio | A clear README with a screen recording of the demo, readable docs, and evidence of sound engineering judgment. They spend minutes, not hours. |
| **Arabic speakers** trying the demo | A simple interface: type an Arabic prompt, get a continuation. |
| **The author** | A deep, hands-on understanding of how language models are built and how they fail. |

## 6. Success metrics

The project succeeds when all of the following are met. Targets marked *provisional* are finalized in `07-evaluation-plan.md`.

| ID | Metric | Target |
|---|---|---|
| M1 | Test-set perplexity vs. an n-gram baseline, using the same tokenizer and the same held-out test set | Model perplexity is lower than the baseline, with the 95% paired-bootstrap interval of the difference in loss per word excluding zero (`07-evaluation-plan.md` §4.6) |
| M2 | Qualitative generation quality on a fixed set of evaluation prompts | Each of two independent blind raters labels at least 70% of the model's 50 continuations acceptable MSA under the written rubric (`07-evaluation-plan.md` §5.3) *(provisional)* |
| M3 | Training cost | One full training run completes in under 6 hours and within 8 GB VRAM |
| M4 | Reproducibility | A training run can be re-executed from its saved config and seed. On the same machine and software the losses are bit-identical (measured over 150 steps); across hardware they agree within run-to-run noise (0.01 to 0.04 nats per word between seeds) |
| M5 | Demo responsiveness | The local demo returns a continuation in under 10 seconds for prompts up to 100 tokens on the project machine |
| M6 | Documentation completeness | All 13 docs and 14 diagrams complete and consistent with the final code (the 14 diagrams are listed in `docs/diagrams/README.md`) |

**Note on M1:** perplexity is only comparable between models that share the same tokenizer and the same evaluation set. Any comparison that violates this is invalid.

## 7. Scope and requirements

### 7.1 Functional requirements

| ID | Requirement |
|---|---|
| FR1 | The system downloads, cleans, and deduplicates a public MSA text corpus. |
| FR2 | The corpus is split into train, validation, and test sets **before** the tokenizer is trained. |
| FR3 | A subword tokenizer is trained on the training split only. |
| FR4 | The model takes a sequence of token IDs and predicts the next token at every position, using causal masking. |
| FR5 | The training pipeline saves checkpoints, logs metrics, and stores the full configuration with every run. |
| FR6 | The evaluation pipeline computes test perplexity for the model and the baseline. |
| FR7 | The generation module produces text from a prompt, with configurable temperature and maximum length. |
| FR8 | The demo accepts an Arabic prompt and displays the generated continuation and its tokenization. |

### 7.2 Non-functional requirements

| ID | Requirement |
|---|---|
| NFR1 | All text I/O uses UTF-8 explicitly. |
| NFR2 | Model size is between 10M and 30M parameters (finalized in `05-model-architecture.md`). |
| NFR3 | Peak training memory stays within 8 GB VRAM. |
| NFR4 | Random seeds are set and logged for all training and evaluation runs. |
| NFR5 | Core components are covered by automated tests, including a causal-masking test and a single-batch overfitting test. Every requirement identifier traces to a test or is documentary (`08-testing-strategy.md` §5.3), and the silent-failure safeguards are checked by bug-injection procedures (`08-testing-strategy.md` §6). |

## 8. Deliverables

1. **Source code** in this GitHub repository.
2. **Documentation:** 13 documents in `docs/` and `experiments/`.
3. **Diagrams:** 14 Mermaid diagrams in `docs/diagrams/`.
4. **Trained model checkpoint**. Publishing it on the Hugging Face Hub (model repository only, no Space) is optional.
5. **Local demo** (Gradio), with a short screen recording or GIF in the README. Publishing on Hugging Face Spaces is optional.
6. **Model Card** describing performance, limitations, and risks.
7. **Experiment Log** recording all runs and every mistake caught during development.

## 9. Constraints

| Constraint | Detail |
|---|---|
| **Time** | 3 weeks planned (2026-10-02 to 2026-10-23), ~90 working hours. Moved to 2026-10-26 (`11-roadmap.md` §2.1); 14 planned days and 96 stated hours remain for the build |
| **Hardware** | One NVIDIA RTX 5050 Laptop GPU, 8 GB VRAM; 16 GB system RAM |
| **Environment** | Windows 11, Python 3.12.10, PyTorch 2.14.1+cu130 |
| **Data** | Publicly available text with a license that permits this use |
| **Budget** | No paid compute or paid services |

## 10. Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Silent bugs (masking, leakage, wrong loss) produce misleading results | High | High | Automated tests, single-batch overfitting check, review of all suspicious results |
| Training exceeds 8 GB VRAM | Medium | Medium | Estimate memory before training; start small and scale up |
| Training is slower than estimated | Medium | Medium | Run an end-to-end pipeline on a small model first; scale only after it works |
| Arabic text corrupted by encoding issues on Windows | High | Medium | Explicit UTF-8 everywhere; verify by writing to files, not terminal output |
| Low-quality or duplicated data degrades the model | Medium | Medium | Cleaning and deduplication pipeline, documented in `03-data-spec.md` |
| Documentation phase overruns and squeezes build time | High | Medium | Time-box docs to 4–5 days; treat docs as living and refine them during the build. **The risk materialized:** the documents took 9 days (2026-10-02 to 2026-10-10), see EXP-009 |
| Data license does not permit use | Medium | Low | Verify licenses before downloading; record them in `03-data-spec.md` |

## 11. Open questions

These are resolved in later documents:

| Question | Resolved in | Status |
|---|---|---|
| Which corpus, and how much text? | `03-data-spec.md` | Resolved: cleaned Arabic Wikipedia (ADR-0001, Amendment 1) |
| Which tokenizer algorithm and vocabulary size? Which normalization rules? | `04-tokenizer-spec.md` | Resolved: byte-level BPE, 16,000 entries (ADR-0002, Amendment 1) |
| Exact architecture: layers, heads, embedding size, context length? | `05-model-architecture.md` | Resolved: ADR-0003, `05` §3 |
| Which n-gram baseline, and which evaluation prompts? | `07-evaluation-plan.md` | Resolved: modified Kneser–Ney baseline, 50 prompts (ADR-0005); prompts pending native-speaker approval |
| Demo hosting details and response-time target | `09-ui-spec.md` | Resolved: local demo; response-time target in M5 (ADR-0007) |
| Content filtering if web data is added (conflicts with NG8) | A future ADR, only if FineWeb-2 or other web data is added (see `adr/0001-training-corpus.md`) | Open (conditional) |

## 12. Related documents

- `02-design-doc.md`: technical design
- `07-evaluation-plan.md`: how success metrics are measured
- `11-roadmap.md`: timeline and milestones