# CLAUDE.md

Guidance for Claude Code when working in this repository. Read this fully at the start of every session.

## Project

**mini-arabic-gpt**: a small GPT-style language model built from scratch in PyTorch and trained on Arabic text. It ships with a Gradio demo on Hugging Face Spaces.

- **Purpose:** a portfolio project for applying to AI/ML engineering roles. Correctness, clarity, and documented reasoning matter more than speed or feature count.
- **Approach:** docs-first. Every component is specified in `docs/` before any code is written for it.
- **Timeline:** 3 weeks, started 2026-10-02, target completion 2026-10-23.

## Current phase

**Phase 1: Documentation.** The only code is the corpus inspection tooling: `scripts/inspect_data.py`, with outputs in `reports/data-inspection/` and dependencies in `requirements-dev.txt`. No model, tokenizer, or data-pipeline code exists yet. Do not create other code files, code folders, or configs until the relevant doc is approved and I ask for them.

The code layout (`src/`, `tests/`, `scripts/`, `configs/`, `app/`) is provisional. It gets finalized in `docs/02-design-doc.md`.

## Environment

| Item | Value |
|---|---|
| OS | Windows 11 |
| Python | 3.12.10, in `.venv/` (system Python is 3.14: never use it) |
| PyTorch | 2.14.1+cu130 (CUDA 13.0 build) |
| GPU | NVIDIA GeForce RTX 5050 Laptop GPU, Blackwell, **8 GB dedicated VRAM** |
| System RAM | 16 GB, often half used by other apps |

- **Always call the venv interpreter explicitly:** `.venv/Scripts/python.exe` and `.venv/Scripts/python.exe -m pip`. Your shell may not keep the venv activated between commands, so never rely on activation.
- **VRAM budget is 8 GB.** Task Manager reports ~15.6 GB "GPU memory", but that includes shared system RAM. Plan only against the 8 GB.
- **Never install a CPU-only PyTorch build,** and never install a CUDA build older than 12.8: Blackwell GPUs need CUDA 12.8 or newer.
- **Do not change the PyTorch version** unless I explicitly ask.
- **Hugging Face downloads:** if a download fails with a xet/CAS error, set `HF_HUB_DISABLE_XET=1` and retry.

Verify the GPU works:

```
.venv/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Expected output contains `+cu130`, `True`, and `RTX 5050`.

## How to work with me

I review your reasoning, not just your output. Make your thinking visible.

1. **Plan before acting.** For any non-trivial task, state your plan and the reasoning behind each decision before changing files. Wait for my approval if the task changes design, adds dependencies, or touches more than one component.
2. **Root cause before fix.** For any bug or error, explain the root cause first. If you can't find it, say so. Never apply a speculative fix and present it as solved.
3. **Evidence, not claims.** Never report a task as done without showing the actual command output that proves it. "It should work" is not done.
4. **Stay in scope.** Only create or modify the files the task requires. No unrequested files, refactors, or "improvements". Suggest them instead.
5. **Flag uncertainty.** If a decision depends on something only an experiment can settle (vocab size, learning rate, model size), mark it as an assumption and say how we'll verify it. Don't present it as fact.
6. **Ask, don't guess.** If a requirement is ambiguous, ask one clear question rather than picking an interpretation silently.

## ML correctness rules

Most bugs in this project will not raise errors. Code will run and produce wrong results. Guard against that:

- **Shapes:** annotate tensor shapes in comments for all model code, e.g. `# (B, T, C)`.
- **Causal masking:** the model must never see future tokens. Any attention change requires a test proving this.
- **Overfit first:** before any full training run, confirm the model can overfit a single small batch to near-zero loss.
- **No data leakage:** split train/val/test before training the tokenizer. Train the tokenizer on the train split only. Deduplicate across splits.
- **Comparable metrics:** perplexity is only comparable between runs using the same tokenizer and the same eval set. Never compare across them.
- **Reproducibility:** set and log random seeds. Save the full config with every training run and checkpoint.
- **Memory first:** before proposing a model size or batch size, estimate VRAM usage and show the calculation.
- **Suspicious results are bugs until proven otherwise.** If a loss drops too fast or a metric looks too good, investigate before celebrating.

## Arabic text handling

- **Always pass `encoding="utf-8"`** when opening files. The Windows default encoding is not UTF-8 and will corrupt Arabic text silently.
- **Arabic printed in the terminal may display garbled.** That's a display issue, not data corruption. Verify by writing to a UTF-8 file instead of trusting terminal output.
- **Normalization decisions** (diacritics, hamza forms, tatweel, Arabic-Indic digits) belong in `docs/04-tokenizer-spec.md`. Don't make them ad hoc in code.

## Documentation conventions

- All docs are in **English**, written in **Markdown**, and live in `docs/`.
- Diagrams use **Mermaid**, stored as `.md` files in `docs/diagrams/`.
- **Docs are living documents.** When code and docs disagree, flag the conflict. Don't silently update either one.
- **Every significant decision gets an ADR** in `docs/adr/`, named `NNNN-short-title.md`, covering context, decision, alternatives considered, and consequences.
- **Don't remove or shorten existing doc content** unless I explicitly ask.

## Experiment log

`experiments/experiment-log.md` records every experiment and every mistake caught during development.

When I correct a mistake in your reasoning or code, propose a log entry covering what went wrong, how it was caught, and the fix. **Do not write to the log without my approval.**

## Git

- **Commit messages** use Conventional Commits: `docs:`, `feat:`, `fix:`, `test:`, `refactor:`, `chore:`.
- **Never run `git commit` or `git push`** unless I explicitly ask.
- **Never commit** data, checkpoints, model weights, or secrets. `data/` and `checkpoints/` are git-ignored.
- **Line endings are LF,** enforced by `.gitattributes`.

## Repository layout

```
docs/          Project documentation (01–11), adr/, diagrams/
experiments/   Experiment log
scripts/       Corpus inspection tool (inspect_data.py)
reports/       Data inspection outputs (metrics, reading samples)
requirements-dev.txt  Dev and inspection dependencies
CLAUDE.md      This file
README.md      Project entry point
```

Update this section whenever the layout changes.
