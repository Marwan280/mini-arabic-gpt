"""Corpus inspection tool (Data Spec §5-§6).

Downloads the candidate corpora from the Hugging Face Hub, computes the quality
metrics of Data Spec §6, and exports a random reading sample per candidate.

    .venv/Scripts/python.exe scripts/inspect_data.py

Design notes
- Sampling: row counts come from the Parquet footers; a seeded
  `random.Random(seed).sample(range(total_rows), N)` draws N distinct global row
  indices, uniform without replacement over ALL files of a candidate combined.
  The reading sample is the first `--read-sample-size` entries of that draw.
- Exact duplicates are computed over the FULL data (every row is hashed).
  Near-duplicates are computed on the N-document sample only, so the rate is a
  LOWER BOUND on the true rate (a pair is only found if both copies are drawn).
- Metrics are computed on raw text (no cleaning); we are measuring pre-cleaning
  quality. NFC + whitespace collapsing is applied only inside duplicate hashing.
- The metrics files contain no timestamps or runtimes, so two runs with the same
  seed on the same shards are byte-identical. Runtime is printed to stdout only.
- Manual ratings are protected: if a reading-sample file that would be written
  already contains a filled `Rating:` line, the run is refused before anything is
  downloaded or computed, unless `--force` is passed (the ratings are then lost).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow
import pyarrow.parquet as pq

DEFAULT_SEED = 42

# ---------------------------------------------------------------------------
# Candidates (Data Spec §4). Revisions are pinned to the Hub commit SHA that was
# current when the inspection was written, so the same shards are re-fetched.
# ---------------------------------------------------------------------------
CANDIDATES = {
    "wikipedia": {
        "label": "Arabic Wikipedia",
        "repo": "wikimedia/wikipedia",
        "revision": "b04c8d1ceb2f5cd4588862100d08de323dccfbaa",
        "files": [f"20231101.ar/train-{i:05d}-of-00007.parquet" for i in range(7)],
        "dir": "wikipedia",
    },
    "fineweb2": {
        "label": "FineWeb-2 Arabic",
        "repo": "HuggingFaceFW/fineweb-2",
        "revision": "af9c13333eb981300149d5ca60a8e9d659b276b9",
        "files": ["data/arb_Arab/train/000_00000.parquet"],
        "dir": "fineweb2_arb_Arab",
    },
}

# ---------------------------------------------------------------------------
# Boilerplate phrases (Data Spec §6). Proposal only; per-phrase hit counts are
# reported so the list can be tuned. Matched as substrings on NFC text with
# whitespace collapsed, case-folded (case matters only for the Latin entries).
# Moves to configs/data.yaml when the cleaning pipeline is written.
# ---------------------------------------------------------------------------
BOILERPLATE_PHRASES = (
    "اقرأ أيضا",
    "اقرأ أيضاً",
    "جميع الحقوق محفوظة",
    "حقوق النشر محفوظة",
    "سياسة الخصوصية",
    "ملفات تعريف الارتباط",
    "شروط الاستخدام",
    "اتصل بنا",
    "تابعونا على",
    "اترك تعليقا",
    "مواضيع ذات صلة",
    "قد يعجبك أيضا",
    "اشترك في النشرة البريدية",
    "all rights reserved",
    "privacy policy",
    "cookies",
)

# ---------------------------------------------------------------------------
# Character classes
# ---------------------------------------------------------------------------
# Arabic letter ranges (a character must ALSO have Unicode category L*).
# U+0640 (tatweel, category Lm) falls inside the first range: counts as a letter.
_ARABIC_LETTER_RANGES = (
    (0x0621, 0x064A), (0x066E, 0x066F), (0x0671, 0x06D3), (0x06D5, 0x06D5),
    (0x06FA, 0x06FC), (0x06FF, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
)
# Diacritics (tashkeel and Quranic marks).
_DIACRITIC_RANGES = (
    (0x064B, 0x065F), (0x0670, 0x0670), (0x06D6, 0x06DC), (0x06DF, 0x06E4),
    (0x06E7, 0x06E8), (0x06EA, 0x06ED),
)

# Class ids
C_AR_LETTER, C_OTHER_LETTER, C_DIACRITIC, C_NONLETTER, C_SPACE, C_OTHER = range(6)

_class_cache: dict[str, int] = {}


def _in_ranges(cp: int, ranges) -> bool:
    return any(lo <= cp <= hi for lo, hi in ranges)


def char_class(ch: str) -> int:
    """Classify one character (cached per distinct character)."""
    c = _class_cache.get(ch)
    if c is not None:
        return c
    cp = ord(ch)
    cat = unicodedata.category(ch)
    if ch.isspace():
        c = C_SPACE
    elif _in_ranges(cp, _DIACRITIC_RANGES):
        c = C_DIACRITIC
    elif cat[0] == "L":
        c = C_AR_LETTER if _in_ranges(cp, _ARABIC_LETTER_RANGES) else C_OTHER_LETTER
    elif cat[0] in "NPS":  # digits (incl. Arabic-Indic), punctuation, symbols
        c = C_NONLETTER
    else:  # marks (non-Arabic), controls, format characters, ...
        c = C_OTHER
    _class_cache[ch] = c
    return c


def char_counts(text: str) -> list[int]:
    """Return counts per class id for `text`."""
    counts = [0] * 6
    for ch, n in Counter(text).items():
        counts[char_class(ch)] += n
    return counts


# ---------------------------------------------------------------------------
# Download and file access
# ---------------------------------------------------------------------------
def download_candidate(name: str, data_dir: Path) -> list[Path]:
    from huggingface_hub import hf_hub_download

    cand = CANDIDATES[name]
    local_dir = data_dir / "raw" / cand["dir"]
    local_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for rel in cand["files"]:
        print(f"[download] {cand['repo']}@{cand['revision'][:8]} {rel}", flush=True)
        p = hf_hub_download(
            repo_id=cand["repo"],
            repo_type="dataset",
            filename=rel,
            revision=cand["revision"],
            local_dir=str(local_dir),
        )
        paths.append(Path(p))
    return paths


def footer_rows(paths: list[Path]) -> list[int]:
    return [pq.ParquetFile(p).metadata.num_rows for p in paths]


# ---------------------------------------------------------------------------
# Near-duplicate detection (MinHash + LSH over word 5-grams)
# ---------------------------------------------------------------------------
def make_minhash(tokens: list[str], ngram: int, num_perm: int):
    from datasketch import MinHash

    if len(tokens) >= ngram:
        shingles = [
            " ".join(tokens[i:i + ngram]).encode("utf-8")
            for i in range(len(tokens) - ngram + 1)
        ]
    else:  # fewer than n words: the whole text is the single shingle
        shingles = [" ".join(tokens).encode("utf-8")]
    m = MinHash(num_perm=num_perm)
    m.update_batch(shingles)
    return m


def near_duplicate_stats(sigs: list, threshold: float, num_perm: int) -> dict:
    from datasketch import MinHashLSH

    n = len(sigs)
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    with lsh.insertion_session() as session:
        for i, m in enumerate(sigs):
            session.insert(i, m)

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, m in enumerate(sigs):
        for j in lsh.query(m):
            if j != i and sigs[i].jaccard(sigs[j]) >= threshold:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)

    sizes = Counter(find(i) for i in range(n))
    in_cluster = sum(s for s in sizes.values() if s > 1)
    return {
        "docs_in_clusters": in_cluster,
        "clusters": sum(1 for s in sizes.values() if s > 1),
        "rate": in_cluster / n if n else None,
        "removable": n - len(sizes),
    }


# ---------------------------------------------------------------------------
# Main per-candidate pass
# ---------------------------------------------------------------------------
def pct(a: np.ndarray, q: float) -> float:
    return round(float(np.percentile(a, q)), 4)


def process_candidate(name, paths, n_sample, args, rows_per_file):
    cand = CANDIDATES[name]
    total_rows = sum(rows_per_file)
    rng = random.Random(args.seed)
    draw = rng.sample(range(total_rows), n_sample)  # uniform, without replacement
    selected = {g: pos for pos, g in enumerate(draw)}

    exact_counts: dict[bytes, int] = {}
    # per-sampled-document records
    words, ar_ratio, nonletter_ratio, dia_ratio = [], [], [], []
    zero_letter_docs = zero_nonspace_docs = no_arabic_docs = 0
    ar_letters_total = dia_total = 0
    boiler_hits = Counter()
    boiler_docs = 0
    sigs = []
    reading: dict[int, dict] = {}  # draw position -> record
    phrases = [p.casefold() for p in BOILERPLATE_PHRASES]

    meta_cols = ("id", "url", "title")
    g = 0
    t0 = time.time()
    for path, nrows in zip(paths, rows_per_file):
        pf = pq.ParquetFile(path)
        cols = ["text"] + [c for c in meta_cols if c in pf.schema_arrow.names]
        local_row = 0
        for batch in pf.iter_batches(batch_size=2000, columns=cols):
            texts = batch.column("text").to_pylist()
            metas = {c: batch.column(c).to_pylist() for c in cols[1:]}
            for j, text in enumerate(texts):
                text = text or ""
                nfc = unicodedata.normalize("NFC", text)
                tokens = nfc.split()
                norm = " ".join(tokens)
                h = hashlib.blake2b(norm.encode("utf-8"), digest_size=16).digest()
                exact_counts[h] = exact_counts.get(h, 0) + 1

                pos = selected.get(g)
                if pos is not None:
                    cc = char_counts(text)
                    ar, oth, dia, nonl, space, _ = cc
                    letters = ar + oth
                    nonspace = sum(cc) - space
                    words.append(len(tokens))
                    if letters:
                        ar_ratio.append(ar / letters)
                    else:
                        zero_letter_docs += 1
                    if nonspace:
                        nonletter_ratio.append(nonl / nonspace)
                    else:
                        zero_nonspace_docs += 1
                    if ar + dia:
                        dia_ratio.append(dia / (ar + dia))
                    else:
                        no_arabic_docs += 1
                    ar_letters_total += ar
                    dia_total += dia
                    folded = norm.casefold()
                    hit = [p for p in phrases if p in folded]
                    for p in hit:
                        boiler_hits[p] += 1
                    boiler_docs += bool(hit)
                    sigs.append(make_minhash(tokens, args.ngram, args.num_perm))
                    # keep sample order == draw order: record draw position
                    if pos < args.read_sample_size:
                        reading[pos] = {
                            "file": path.name,
                            "row": local_row + j,
                            "words": len(tokens),
                            "chars": len(text),
                            "text": text[: args.read_max_chars],
                            "meta": {c: metas[c][j] for c in metas},
                        }
                g += 1
            local_row += len(texts)
            if g % 200_000 < 2000:
                print(f"[{name}] {g:,}/{total_rows:,} rows  {time.time() - t0:.0f}s", flush=True)
    assert g == total_rows, f"row count mismatch: read {g}, footers say {total_rows}"

    # ---- aggregate ----
    w = np.array(words, dtype=np.float64)
    a = np.array(ar_ratio, dtype=np.float64)
    nl = np.array(nonletter_ratio, dtype=np.float64)
    d = np.array(dia_ratio, dtype=np.float64)

    dup_docs = sum(c for c in exact_counts.values() if c > 1)
    t1 = time.time()
    print(f"[{name}] near-duplicate detection on {len(sigs):,} sampled docs ...", flush=True)
    near = near_duplicate_stats(sigs, args.threshold, args.num_perm)
    print(f"[{name}] near-dup done in {time.time() - t1:.0f}s", flush=True)

    metrics = {
        "label": cand["label"],
        "source": {
            "repo": cand["repo"],
            "revision": cand["revision"],
            "files": [
                {"path": rel, "bytes": Path(p).stat().st_size, "rows": r}
                for rel, p, r in zip(cand["files"], paths, rows_per_file)
            ],
        },
        "document_count": {"sample": len(words), "full_set": total_rows},
        "word_count_sample": {
            "total": int(w.sum()),
            "mean": round(float(w.mean()), 4),
            "median": pct(w, 50),
            "p5": pct(w, 5),
            "p95": pct(w, 95),
            "share_under_50_words": round(float((w < 50).mean()), 6),
        },
        "arabic_character_ratio": {
            "definition": "Arabic letters / all letters (Unicode L*), per document",
            "mean": round(float(a.mean()), 6),
            "median": round(float(np.median(a)), 6),
            "share_below_0.80": round(float((a < 0.80).mean()), 6),
            "docs_with_zero_letters_excluded": zero_letter_docs,
        },
        "non_letter_ratio_excluding_whitespace": {
            "definition": "(N*+P*+S* chars) / (all non-whitespace chars), per document",
            "mean": round(float(nl.mean()), 6),
            "median": round(float(np.median(nl)), 6),
            "share_above_0.30": round(float((nl > 0.30).mean()), 6),
            "docs_with_zero_nonspace_excluded": zero_nonspace_docs,
        },
        "exact_duplicate_rate": {
            "scope": "FULL set (all rows hashed)",
            "rate": round(dup_docs / total_rows, 6),
            "docs_in_duplicate_groups": dup_docs,
            "removable_docs": total_rows - len(exact_counts),
            "removable_rate": round((total_rows - len(exact_counts)) / total_rows, 6),
        },
        "near_duplicate_rate": {
            "scope": f"SAMPLE only ({len(sigs)} docs): LOWER BOUND on the true rate",
            "method": f"MinHash {args.num_perm} perms, word {args.ngram}-grams, "
                      f"Jaccard >= {args.threshold}, LSH + union-find",
            "rate": round(near["rate"], 6),
            "docs_in_clusters": near["docs_in_clusters"],
            "clusters": near["clusters"],
            "removable_docs": near["removable"],
        },
        "boilerplate_rate": {
            "rate": round(boiler_docs / len(words), 6),
            "docs_with_hit": boiler_docs,
            "per_phrase_docs": {p: boiler_hits[p] for p in sorted(phrases)},
        },
        "diacritics_rate": {
            "definition": "diacritic chars / (Arabic letters + diacritic chars)",
            "pooled": round(dia_total / (ar_letters_total + dia_total), 6)
            if (ar_letters_total + dia_total) else None,
            "per_document_mean": round(float(d.mean()), 6) if len(d) else None,
            "docs_without_arabic_chars_excluded": no_arabic_docs,
        },
        "manual_quality_score": "not computed: manual (rate the reading-sample file)",
    }
    assert len(reading) == min(args.read_sample_size, n_sample)
    return metrics, [reading[k] for k in sorted(reading)]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


# A filled rating is a line that starts with "Rating:" followed by any value.
# Anchored at line start, so the "# ... 'Rating:' line ..." header comment never matches.
# A document line that itself begins with "Rating: ..." would also count; that errs on
# the safe side (the run is refused, and --force overrides it).
_FILLED_RATING = re.compile(r"^Rating:[ \t]*\S")


def reading_sample_path(report_dir: Path, name: str) -> Path:
    return report_dir / f"reading_sample_{name}.txt"


def count_filled_ratings(path: Path) -> int:
    """Number of filled `Rating:` lines in `path` (0 if the file does not exist)."""
    if not path.is_file():
        return 0
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return sum(1 for line in f if _FILLED_RATING.match(line))


def write_reading_sample(path: Path, name: str, docs: list[dict], args, n_sample, total_rows):
    lines = [
        f"# Reading sample: {CANDIDATES[name]['label']}",
        f"# seed={args.seed} sample_size={n_sample} total_rows={total_rows} "
        f"documents={len(docs)} text_cap={args.read_max_chars} chars",
        "# Selection: first documents of a seeded uniform draw over all rows. Rate each "
        "document on the 'Rating:' line: clean | noisy | list | dialect | other",
        "",
    ]
    for i, doc in enumerate(docs, 1):
        meta = " | ".join(f"{k}={v}" for k, v in doc["meta"].items() if v is not None)
        lines.append(
            f"=== [{i:03d}/{len(docs)}] file={doc['file']} | row={doc['row']} | "
            f"words={doc['words']} | chars={doc['chars']}" + (f" | {meta}" if meta else "")
        )
        lines.append(doc["text"])
        if doc["chars"] > len(doc["text"]):
            lines.append(
                f"[truncated: showing first {len(doc['text'])} of {doc['chars']} characters]"
            )
        lines.append("Rating:")
        lines.append("")
    write_text(path, "\n".join(lines))


def fmt_pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.2f}%"


def render_markdown(result: dict) -> str:
    names = list(result["candidates"])
    cols = [result["candidates"][n] for n in names]
    h = result["header"]
    out = [
        "# Data inspection metrics",
        "",
        f"Seed: {h['seed']} | Sample size: {h['sample_size']:,} documents per candidate | "
        f"Generated by `scripts/inspect_data.py`",
        "",
        "Exact duplicates are computed over the full set; near-duplicates over the sample "
        "only (lower bound). Sample statistics are not scaled to the full set.",
        "",
        "| Metric | " + " | ".join(c["label"] for c in cols) + " |",
        "|---|" + "---|" * len(cols),
    ]

    def row(label, fn):
        out.append(f"| {label} | " + " | ".join(fn(c) for c in cols) + " |")

    row("Documents in full set", lambda c: f"{c['document_count']['full_set']:,}")
    row("Sample size (documents)", lambda c: f"{c['document_count']['sample']:,}")
    row("Total words (sample)", lambda c: f"{c['word_count_sample']['total']:,}")
    row("Words per document: mean / median", lambda c: f"{c['word_count_sample']['mean']:.1f} / {c['word_count_sample']['median']:.0f}")
    row("Words per document: p5 / p95", lambda c: f"{c['word_count_sample']['p5']:.0f} / {c['word_count_sample']['p95']:.0f}")
    row("Share of docs under 50 words", lambda c: fmt_pct(c["word_count_sample"]["share_under_50_words"]))
    row("Arabic character ratio (mean)", lambda c: f"{c['arabic_character_ratio']['mean']:.4f}")
    row("Arabic character ratio (median)", lambda c: f"{c['arabic_character_ratio']['median']:.4f}")
    row("Share of docs with Arabic ratio < 0.80", lambda c: fmt_pct(c["arabic_character_ratio"]["share_below_0.80"]))
    row("Non-letter ratio, excluding whitespace (mean)", lambda c: f"{c['non_letter_ratio_excluding_whitespace']['mean']:.4f}")
    row("Share of docs with non-letter ratio > 0.30", lambda c: fmt_pct(c["non_letter_ratio_excluding_whitespace"]["share_above_0.30"]))
    row("Exact duplicate rate (full set)", lambda c: fmt_pct(c["exact_duplicate_rate"]["rate"]))
    row("Exact duplicates removable (full set)", lambda c: f"{c['exact_duplicate_rate']['removable_docs']:,} ({fmt_pct(c['exact_duplicate_rate']['removable_rate'])})")
    row("Near-duplicate rate (sample, lower bound)", lambda c: fmt_pct(c["near_duplicate_rate"]["rate"]))
    row("Boilerplate rate", lambda c: fmt_pct(c["boilerplate_rate"]["rate"]))
    row("Diacritics rate (pooled)", lambda c: fmt_pct(c["diacritics_rate"]["pooled"]))
    row("Manual quality score (clean MSA prose)", lambda c: "not computed: manual")
    out += ["", "## Boilerplate hits per phrase (documents in the sample)", ""]
    phrases = sorted(cols[0]["boilerplate_rate"]["per_phrase_docs"])
    out.append("| Phrase | " + " | ".join(c["label"] for c in cols) + " |")
    out.append("|---|" + "---|" * len(cols))
    for p in phrases:
        out.append(f"| {p} | " + " | ".join(str(c["boilerplate_rate"]["per_phrase_docs"][p]) for c in cols) + " |")
    out += ["", "## Sources", ""]
    for c in cols:
        files = ", ".join(f"`{f['path']}` ({f['bytes'] / 1e6:.0f} MB, {f['rows']:,} rows)" for f in c["source"]["files"])
        out.append(f"- **{c['label']}**: `{c['source']['repo']}` @ `{c['source']['revision']}`: {files}")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Download candidate corpora, compute Data Spec section 6 quality metrics, "
                    "and export a random reading sample per candidate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--seed", type=int, default=DEFAULT_SEED,
                   help="Random seed for the sample draw (printed in the output header).")
    p.add_argument("--sample-size", type=int, default=50_000,
                   help="Documents sampled per candidate for sample-based metrics; capped at "
                        "the smallest candidate's row count so both use the same size.")
    p.add_argument("--candidates", default="wikipedia,fineweb2",
                   help="Comma-separated candidates to inspect: wikipedia, fineweb2.")
    p.add_argument("--data-dir", default="data",
                   help="Directory for raw downloads (Parquet shards go under <data-dir>/raw/).")
    p.add_argument("--report-dir", default="reports/data-inspection",
                   help="Directory for metrics.json, metrics.md and the reading-sample files.")
    p.add_argument("--read-sample-size", type=int, default=100,
                   help="Documents exported per candidate for manual reading.")
    p.add_argument("--read-max-chars", type=int, default=3000,
                   help="Max characters of each document written to the reading sample.")
    p.add_argument("--num-perm", type=int, default=128,
                   help="MinHash permutations for near-duplicate detection.")
    p.add_argument("--ngram", type=int, default=5,
                   help="Word n-gram size for near-duplicate shingles.")
    p.add_argument("--threshold", type=float, default=0.8,
                   help="Jaccard similarity threshold for near-duplicates.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite reading-sample files that already contain filled 'Rating:' "
                        "lines (the manual ratings are lost). Without it, such a run is refused "
                        "before anything is downloaded or written.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    names = [n.strip() for n in args.candidates.split(",") if n.strip()]
    unknown = [n for n in names if n not in CANDIDATES]
    if unknown:
        raise SystemExit(f"unknown candidate(s): {unknown}; choose from {list(CANDIDATES)}")
    data_dir, report_dir = Path(args.data_dir), Path(args.report_dir)

    # Protect manual ratings: check before any download or computation.
    rated = []
    for n in names:
        sample_path = reading_sample_path(report_dir, n)
        filled = count_filled_ratings(sample_path)
        if filled:
            rated.append((sample_path, filled))
    if rated and not args.force:
        for p, k in rated:
            print(f"ERROR: refusing to overwrite {p}: it contains {k} filled 'Rating:' line(s).",
                  file=sys.stderr)
        print("Nothing was downloaded or written. Re-run with --force to overwrite "
              "(the ratings will be lost), or use --report-dir to write elsewhere.",
              file=sys.stderr)
        return 2
    for p, k in rated:
        print(f"WARNING: --force given: {p} will be overwritten and its {k} filled rating(s) "
              f"discarded.", flush=True)

    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"seed={args.seed} sample_size={args.sample_size} candidates={names}", flush=True)
    paths = {n: download_candidate(n, data_dir) for n in names}
    rows = {n: footer_rows(paths[n]) for n in names}
    for n in names:
        print(f"[{n}] {sum(rows[n]):,} rows in {len(paths[n])} file(s)", flush=True)
    n_sample = min([args.sample_size] + [sum(rows[n]) for n in names])
    print(f"effective sample size per candidate: {n_sample:,}", flush=True)

    result = {
        "header": {
            "seed": args.seed,
            "sample_size": n_sample,
            "read_sample_size": args.read_sample_size,
            "read_max_chars": args.read_max_chars,
            "minhash": {"num_perm": args.num_perm, "ngram": args.ngram, "threshold": args.threshold},
            "python": platform.python_version(),
            "pyarrow": pyarrow.__version__,
            "numpy": np.__version__,
        },
        "candidates": {},
    }
    readings = {}
    for n in names:
        metrics, reading = process_candidate(n, paths[n], n_sample, args, rows[n])
        result["candidates"][n] = metrics
        readings[n] = reading

    for n in names:
        write_reading_sample(reading_sample_path(report_dir, n), n, readings[n], args,
                             n_sample, sum(rows[n]))
    write_text(report_dir / "metrics.json",
               json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    write_text(report_dir / "metrics.md", render_markdown(result))
    print(f"wrote outputs to {report_dir}/  (total runtime {time.time() - start:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
