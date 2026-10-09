# Tokenizer notes from the data inspection

| | |
|---|---|
| **Purpose** | Observations from the corpus inspection that affect tokenizer design, with measurements and the decisions they force or leave open. Input to `docs/04-tokenizer-spec.md`. |
| **Contains** | Observations, counts, and open questions only. No decisions: those are made in the spec. |
| **Corpus** | Arabic Wikipedia (ADR-0001) |
| **Sample** | The same 50,000 documents as `metrics.md` (seed 42) |
| **Numbers** | `reports/data-inspection/char-stats_wikipedia.json`, produced by `scripts/inspect_data.py --char-stats` |

## 1. How the numbers were produced

```
.venv/Scripts/python.exe scripts/inspect_data.py --char-stats --candidates wikipedia
```

- **Same sample as the quality metrics.** Checked against the existing outputs: total words 11,173,499 equals `metrics.md`; the ids of the first 100 drawn documents equal the ids in `reading_sample_wikipedia.txt`, in order; the pooled diacritics rate (0.717%) equals `metrics.json`. Two independent runs produce byte-identical output. The mode writes only `char-stats_*.json` and never touches the metrics or the rated reading samples.
- **Two views of every measurement.**
  - **Raw:** the 50,000 documents as downloaded, including trailing reference and category sections and stubs.
  - **Cleaned (approximate):** 19,736 documents (39.5%) holding 76.0% of the words. It approximates Data Spec steps 3a to 6: trailing sections cut at the first reference-type heading, then documents dropped for fewer than 50 words (29,858), Arabic ratio below 0.80 (1,061), or non-letter ratio above 0.30 (133); reasons can overlap. It does not apply NFC, markup and URL stripping, whitespace normalization, the empty-heading rule, or the line filter.
  - The tokenizer will see cleaned text, so the cleaned column is the closer guide; the raw column shows what the cleaning removes.
- **Counting.** "Count" is occurrences, "docs" is documents containing at least one. Percentages of documents use 50,000 (raw) or 19,736 (cleaned).
- **Limits.**
  - Fused words, clitics, and orthographic variants are measured with pattern proxies, because no Arabic lexicon is available; the proxies mix real defects with legitimate forms (explained per item).
  - Only Wikipedia was measured. Observations that come from the FineWeb-2 reading sample are listed in section 14 without counts.
  - Examples are Wikipedia article ids from the sample. `W<n>` and `F<n>` mean document n of `reading_sample_wikipedia.txt` and `reading_sample_fineweb2.txt`.

## 2. Summary

| Section | Observation | Headline (cleaned view unless stated) | Decision it forces |
|---|---|---|---|
| 3 | Persian/Urdu-script letters inside Arabic text | Farsi yeh in 185 docs (0.94%); veh, peh, tcheh, gaf also present | Map them to Arabic letters, keep them, or leave them to the vocabulary |
| 4 | Diacritics | 73.2% of docs have some; 37.6% of marks are fathatan; 1.1% of docs are heavily diacritized | Which marks are removed, kept, or mapped |
| 5 | Tatweel | 76.5% of runs are هـ, بـ or لـ; tatweel between two letters is in 3.2% of docs (19.3% of those runs are a one-letter clitic connector) | Remove, keep, or remove only between letters |
| 6 | Digits | Western digits 99.90% of digit characters; Arabic-Indic 0.09% | Map Arabic-Indic and Persian digits or not; how digit strings are split |
| 7 | Alef, hamza, yeh, teh marbuta forms | Bare alef 83.8% of the alef family; ى is 8.3% of ى+ي | Whether any of these forms are collapsed |
| 8 | Fused words and attached numbers or Latin | 6.97% of docs have letter-punctuation-letter with no space | Where pre-tokenization splits; whether any repair is attempted |
| 9 | Latin and other scripts | 36.0% of docs contain Latin letters; 21.3% have a parenthesized Latin phrase | How non-Arabic text is covered by the vocabulary |
| 10 | Punctuation variants and spacing | Arabic comma is 21.2 times the ASCII comma; 38.9% of docs have a space before punctuation | Which variants map together |
| 11 | Invisible characters, Unicode forms | No-break space in 8.9% of docs; NFKC changes 11.9% of docs | Which normalization form; how invisible characters are handled |
| 12 | Markup and template residue | HTML-like tags in 0.64% of docs; empty brackets in 1.06% | Whether the tokenizer sees them depends on §8 step 2 |
| 13 | Character coverage | 2,269 distinct characters; 400 cover 99.99% | The alphabet the vocabulary must cover |

## 3. Persian/Urdu-script letters inside Arabic text

**Seen.** F37 (FineWeb-2) has Farsi yeh and keheh inside Arabic words ("الیرقات", "کبسولات"). Wikipedia has the same letters in Persian and Kurdish place names (id 2995: "بیجار، مریوان") and mixed with Arabic yeh and kaf in a single sentence (id 16572: "منطقة کردستان یشتمل علی محافظات كرمان"). Veh appears in Arabic-script spellings of the /v/ sound ("نوڤمبر" id 17840, "سوڤيتي" id 28630, "ڤولكسڤاغن" id 4106; also W3). Heh doachashmee stands in for the Hijri marker (id 29056: "١٢٥١ھ").

**Measured.**

| Letter | Raw count / docs | Cleaned count / docs |
|---|---|---|
| U+06CC FARSI YEH ی | 2,130 / 476 | 1,472 / 185 |
| U+06A9 KEHEH ک | 483 / 171 | 329 / 88 |
| U+06AF GAF گ | 634 / 135 | 539 / 112 |
| U+067E PEH پ | 427 / 131 | 365 / 108 |
| U+06A4 VEH ڤ | 416 / 169 | 307 / 112 |
| U+0686 TCHEH چ | 156 / 62 | 109 / 53 |
| U+06BE HEH DOACHASHMEE ھ | 116 / 31 | 111 / 27 |
| other (TTEH, JEH, HEH GOAL, YEH BARREE, HEH WITH YEH ABOVE), docs summed over letters | 48 / up to 35 | 40 / up to 29 |

For scale, Arabic yeh ي occurs 4,434,768 times and Arabic kaf ك 1,174,398 times (raw). Farsi yeh is 0.05% of the yeh-like characters.

**Forces.** Whether Farsi yeh (ی) and keheh (ک) are mapped to Arabic yeh (ي) and kaf (ك) before training. The demo applies the same rule to typed prompts, so the choice also decides how a pasted Persian-keyboard prompt is read.

**Open.** What happens to gaf, peh, tcheh, and veh, which have no Arabic-alphabet equivalent and are used for loan phonemes (kept as they are, mapped, or left to the vocabulary's fallback). Whether the mapping is applied in documents only or also at inference.

## 4. Diacritics (tashkeel)

**Seen.** W3 is a fully diacritized stub; F48 is a fully diacritized classical text of 39,782 characters; F67 and F77 are partly diacritized. In ordinary Wikipedia prose the commonest mark is fathatan (as in "أيضاً", "جداً"), not the short vowels.

**Measured.**

| | Raw | Cleaned |
|---|---|---|
| Pooled rate, marks ÷ (Arabic letters + marks) | 0.717% | 0.862% |
| Docs with at least one mark | 23,282 (46.6%) | 14,438 (73.2%) |
| Docs where marks are at least 5% of letters + marks | 303 (0.61%) | 212 (1.07%) |
| Docs where marks are at least 20% | 70 (0.14%) | 22 (0.11%) |

Marks by type (raw count, docs): fathatan 138,003 (18,855); damma 63,880 (10,410); shadda 57,734 (8,408); fatha 57,618 (5,098); kasra 27,478 (3,776); sukun 10,938 (1,139); kasratan 6,830 (1,696); dammatan 2,613 (980); superscript alef 38 (15); maddah and hamza marks 13. Fathatan is 37.8% of all marks (37.6% cleaned). Quranic annotation marks (U+06D6 to U+06ED): 40 occurrences of 7 distinct marks. The ornate Quranic brackets ﴿ ﴾ occur 113 times (15 docs).

**Forces.** Which marks are removed, kept, or mapped, before tokenizer training and at inference. The Data Spec §8 defers diacritic removal to the tokenizer stage.

**Open.** Whether fathatan is treated like the short vowels or like an ordinary spelling element; whether shadda is treated separately; what happens to the 22 heavily diacritized cleaned documents (70 raw) if marks are kept; whether the Quranic marks and ornate brackets get their own handling.

## 5. Tatweel (kashida)

**Seen.** In FineWeb-2, tatweel also appears inside obfuscated spellings ("الحـ .ـريق", F43; not measured, section 14). In Wikipedia it is mostly not decorative: it is the connector of the one-letter forms هـ (Hijri-year marker, id 1911: "1313 هــ"), بـ and لـ ("بـ59", id 2386 "بـعملية", W51 "الـحركي"). Decorative elongation inside a word is rare (id 9605: "طــياراً").

**Measured.**

| | Raw | Cleaned |
|---|---|---|
| Tatweel characters / docs | 24,773 / 9,050 (18.1%) | 18,387 / 4,626 (23.4%) |
| Runs of tatweel | 23,226 | 16,860 |
| Run preceded by ه / ب / ل | 7,890 / 6,806 / 4,236 | 4,999 / 4,024 / 3,867 |
| Those three together | 18,932 runs (81.5%) | 12,890 runs (76.5%) |
| Run followed by space / Arabic letter / punctuation / digit / newline | 11,488 / 3,686 / 3,205 / 1,639 / 2,508 | 8,118 / 3,502 / 3,063 / 1,591 / 152 |
| Between two Arabic letters: runs / docs | 3,482 / 759 (1.5%) | 3,310 / 627 (3.2%) |
| of which a one-letter clitic (و ب ل ف ك) at the start of a word, joined to the next word (as in "بـعملية") | 721 / 464 | 639 / 387 |
| of which inside a longer word (decorative elongation, as in "طــياراً") | 2,761 / 360 (0.7%) | 2,671 / 303 (1.5%) |
| Runs of two or more tatweels: occurrences / docs | 827 / 178 | 808 / 163 |

**Forces.** Whether tatweel is removed everywhere, kept, or removed only between two letters. With the measured contexts, removing it everywhere rewrites the Hijri marker هـ to ه and the prefixes بـ and لـ to the bare letters ب and ل, which then read as ordinary letters and prepositions. Removing it only between two letters also removes the one-letter connector before a following letter (19.3% of the between-letters runs in the cleaned view), but leaves it before spaces, digits, punctuation and Latin letters.

**Open.** Whether هـ and the other connector forms are protected or rewritten; whether the choice applies to runs of two or more differently from single tatweels.

## 6. Digits and number formats

**Seen.** W36 has Arabic-Indic digits ("٢٠ إلى ١٠٠"); F9, F14 and F20 do too. Wikipedia ids 17848, 29056, 34184, 44637 show the same, including Hijri/Gregorian pairs ("١٢٥١ھ/١٨٣٥م"). Persian-form digits are almost absent.

**Measured.**

| | Raw | Cleaned |
|---|---|---|
| Digit characters, share of all characters | 1,794,708 (2.66%) | 1,116,679 (2.19%) |
| Western (ASCII) digits: occurrences / docs | 1,793,560 / 44,474 (88.9%) | 1,115,618 / 17,907 (90.7%) |
| Arabic-Indic digits ٠-٩ | 1,102 / 87 docs (0.17%) | 1,033 / 76 docs (0.39%) |
| Persian-form digits ۰-۹ | 35 / 5 docs | 19 / 4 docs |
| Digit strings that mix digit scripts | 0 | 0 |
| Digit strings: Western / Arabic-Indic / Persian | 652,987 / 376 / 16 | 429,813 / 353 / 12 |
| Digit strings of 8 or more digits: occurrences / docs | 564 / 317 | 203 / 88 |
| Western thousands separator, as in 29,004: occurrences / docs | 13,768 / 3,306 | 12,946 / 2,659 |
| Western decimal point, as in 2.61: occurrences / docs | 53,516 / 4,654 | 51,348 / 4,021 |
| Arabic decimal separator ٫ / thousands separator ٬ | 82 (32 docs) / 226 (81 docs) | 31 (8 docs) / 138 (30 docs) |

**Forces.** Whether Arabic-Indic and Persian-form digits are mapped to Western digits, kept, or left to the vocabulary (together they are 0.06% of digit characters raw, 0.09% cleaned). How digit strings are split into pieces, since digits are 2.2% of the characters the tokenizer will see.

**Open.** Whether the Arabic decimal and thousands separators are mapped to . and , ; whether very long digit strings (identifiers, coordinates) are treated differently from short numbers.

## 7. Alef, hamza, yeh, and teh marbuta forms

**Seen.** In the FineWeb-2 reading sample, several web pages spell hamza-less ("اقامت", "الى") or write ه for ة ("الشركه", "الماليه") (F23, F39, F68, F74). The Wikipedia text is mostly in standard spelling. Spelling variation cannot be counted without a lexicon, so only the inventory of forms is measured.

**Measured** (raw count; cleaned count in brackets).

| Form | Count | Form | Count |
|---|---|---|---|
| ا alef | 7,242,707 (5,661,191) | ى alef maksura | 328,160 (291,472) |
| أ alef with hamza above | 1,006,748 (759,275) | ي Arabic yeh | 4,434,768 (3,205,805) |
| إ alef with hamza below | 360,773 (291,772) | ة teh marbuta | 1,785,170 (1,351,157) |
| آ alef with madda | 49,587 (39,978) | ه heh | 922,319 (797,206) |
| ٱ alef wasla | 39 (37) | ك Arabic kaf | 1,174,398 (858,474) |
| ء hamza | 141,734 (114,418) | ؤ / ئ | 40,465 (35,672) / 204,200 (165,529) |

In the alef family, bare alef is 83.6% (83.8% cleaned), hamza above 11.6%, hamza below 4.2%, madda 0.57%. ى is 6.9% of ى+ي (8.3% cleaned).

**Forces.** Whether alef forms, ى and ي, or ة and ه are collapsed. The Data Spec §8 lists hamza and alef normalization as a tokenizer-stage decision.

**Open.** What a collapse would cost: no measurement here shows how often two distinct words differ only by these forms.

## 8. Fused words and attached numbers or Latin

**Seen.** Words run together in the extracted text: W83 ("الإضرابفي", "الثانييناير"), id 221940 ("الترميميوالاكاديميون"), id 387243 ("البكتريّالـجنتومايسين"); F1, F22 and F52 show the same in web text ("2013عادت", "منذالصباح"). Sentences are joined with no space after the period ("الوقت.وتقول" id 1461, "هكتار.وتغطي" id 1626). Numbers and Latin names are attached to Arabic: single-letter prefixes before numbers ("ب1240", "و2010"), era markers after years ("1920م", "791هـ"), units ("400مم" id 2995), and other cases of text stuck to a number ("12مليار" id 6592, a footnote number in "1يعد" id 6961, "الCASS" id 3862, "وIBM" id 6985).

**Measured.** These are proxies: they find a pattern, not whether it is a defect.

| Pattern | Raw: occurrences / docs | Cleaned: occurrences / docs |
|---|---|---|
| Run of 15 or more Arabic letters | 978 / 541 (1.08%) | 859 / 466 (2.36%) |
| Run of 20 or more | 31 / 22 | 29 / 20 |
| Run of 25 or more | 6 / 5 | 5 / 4 |
| Letter-punctuation-letter with no space (2+ letters each side) | 3,424 / 1,601 (3.20%) | 3,090 / 1,376 (6.97%) |
| Digit directly followed by an Arabic letter | 11,137 / 2,914 | 10,502 / 2,624 |
| of which era marker م or هـ | 9,271 (83.2%) | 8,760 (83.4%) |
| of which other (units, conjunction و, footnote numbers) | 1,866 | 1,742 |
| Arabic letter directly followed by a digit | 16,677 / 5,213 | 15,667 / 4,437 |
| of which a single-letter prefix (و ب ل ف ك) before a digit | 12,193 (73.1%) | 11,753 (75.0%) |
| Arabic letter directly next to a Latin letter | 1,705 / 702 | 1,582 / 629 |

Long runs mix real fusions (ids 221940, 387243) with legitimate compound terms (id 138938 "الديكستروأمفيتامينات", id 1128555 "الهيدروكلوروفلوروكربونات"). The no-space punctuation pattern also matches web addresses and names (id 1563 "إسلام أون لاين.نت"). Moderate fusions of ordinary words ("الإضرابفي") fall below every run threshold and are not counted.

**Forces.** Where pre-tokenization splits: at digit-letter, Arabic-Latin, and letter-punctuation boundaries, or not. In the measured sample most digit-letter contacts are era markers and most letter-digit contacts are single-letter prefixes (table above), which a split at every such boundary would separate from their numbers.

**Open.** Whether any repair of fused words is attempted (no lexicon is available, and the proxies cannot separate defects from compounds); how large the fused-word problem is, since only the extreme tail is measurable here.

## 9. Latin text and other scripts

**Seen.** Latin appears in parenthesized transliteration pairs (W3: "(بالأَلمانِيَّة: Gemeinde Ahorntal)"; id 1626 "(بالإنجليزية: Ibero-Maurusian)"), in names and acronyms attached to Arabic prefixes, in lists (W57, a cast list that is mostly Latin), and in bilingual passages (W51, French lyrics with an Arabic gloss). Other scripts appear as isolated glosses: Chinese (W33), Korean and Chinese (W89), Turkish verse written in Arabic script (W62), Cyrillic, Greek, Hebrew, Armenian, and others.

**Measured.**

| | Raw | Cleaned |
|---|---|---|
| Latin letters, share of all letters | 1,343,065 (2.59%) | 416,843 (1.06%) |
| Docs with any Latin letter | 12,126 (24.3%) | 7,099 (36.0%) |
| Docs where Latin is at least 5% of letters | 4,535 (9.1%) | 1,320 (6.7%) |
| Docs where Latin is at least 20% of letters | 1,013 (2.0%) | 0 (removed by the Arabic-ratio filter) |
| Latin words of 2+ letters: occurrences / docs | 233,540 / 11,804 | 76,067 / 6,799 |
| Parenthesized phrase containing a Latin word of 3+ letters: occurrences / docs | 17,162 / 5,917 (11.8%) | 12,160 / 4,209 (21.3%) |
| Letters in scripts other than Arabic and Latin (15 largest scripts) | 19,533 (0.04%) | 10,847 (0.03%) |

Largest other scripts, raw letters / docs: Cyrillic 8,129 / 184; Greek 2,810 / 324; CJK ideographs 2,498 / 352; Hangul 1,768 / 81; Hebrew 1,201 / 72; Hiragana 950 / 153; Armenian 804 / 27; Devanagari 464 / 36; Katakana 425 / 51. Characters outside the Basic Multilingual Plane: 79 occurrences of 33 distinct characters.

**Forces.** How much non-Arabic text the vocabulary must cover, and how characters outside the covered set are represented. The Data Spec §8 language filter (Arabic ratio at least 0.80) already removes the documents where Latin is 20% or more of the letters.

**Open.** Whether Latin words get their own pieces or are covered at the character or byte level; whether parenthesized Latin glosses are kept, which affects 21.3% of cleaned documents.

## 10. Punctuation variants and spacing

**Seen.** Wikipedia mixes Arabic-specific marks with ASCII ones and uses several quotation styles. Spaces before punctuation come from machine-translated text and from stripped templates (W17: "أكينفيف ، من مواليد"; F8: "تعال ، حدد").

**Measured** (raw count / docs; cleaned count / docs).

| Pair | Arabic form | Other form |
|---|---|---|
| Comma | ، 443,670 / 39,945; 398,793 / 18,469 | , 39,455 / 5,545; 18,812 / 3,908 |
| Semicolon | ؛ 10,521 / 4,745; 9,326 / 3,696 | ; 2,849 / 398; 572 / 192 |
| Question mark | ؟ 1,447 / 642; 1,345 / 586 | ? 357 / 192; 113 / 53 |
| Percent | ٪ 2,361 / 574; 2,304 / 563 | % 37,234 / 1,951; 36,461 / 1,911 |
| Double quotation | « » 39,430 and 39,418 / 7,350 docs; 37,487 and 37,472 / 6,330 | ASCII " 22,410 / 2,708; 13,924 / 2,231. Curly “ ” 765 and 1,025 (268 docs for ”); 668 and 935 |

Arabic comma to ASCII comma: 11.2 to 1 raw, 21.2 to 1 cleaned. Apostrophes (raw): ASCII ' 4,151 / 1,253 docs; right single quote ’ 308 / 132; left single quote ‘ 116 / 39. Dashes (raw): hyphen-minus 65,236 / 13,239 docs; en dash 17,314 / 4,340; em dash 4,519 / 204 (337 / 126 cleaned); minus sign 184. Ellipsis character: 110. Bullet: 1,427 / 107. Space or tab before , ، ؛ : ؟ ? ! or . : 44,253 occurrences in 12,283 docs (24.6%) raw, 35,698 in 7,672 (38.9%) cleaned. Runs of two or more whitespace characters (other than newline) inside a line: 64,352 in 29,400 docs (58.8%) raw, 29,606 in 9,890 (50.1%) cleaned; Data Spec step 3 collapses these.

**Forces.** Which punctuation variants map to one form (Arabic and ASCII comma, semicolon, question mark, percent; quote styles; dash types), and whether a space before punctuation is normalized in §8 step 3 or left to the tokenizer.

**Open.** Whether the mapping is symmetric; whether quote and bracket pairs are kept distinct from each other.

## 11. Invisible characters, spaces, and Unicode normalization forms

**Measured** (raw count / docs; cleaned count / docs).

| Character | Raw | Cleaned |
|---|---|---|
| U+00A0 no-break space | 15,087 / 2,436 (4.9%) | 12,113 / 1,762 (8.9%) |
| Tab | 3,814 / 285 | 2,632 / 137 |
| U+200C zero-width non-joiner | 520 / 266 | 317 / 85 |
| U+200D zero-width joiner | 71 / 41 | 64 / 34 |
| U+061C Arabic letter mark | 19 / 5 | 19 / 5 |
| Other spaces and marks, counts only: thin space 15 (6 cleaned), narrow no-break 7, em space 10, en space 1, zero-width space 5, soft hyphen 4, left-to-right mark 2, byte-order mark 3 (0 cleaned) | 47 | 35 |

Zero-width non-joiner appears in compound names (id 55946 "جهان‌آرا") and list markers (id 10678 "أ‌-"). Right-to-left marks and the directional embeddings and isolates (U+202A to U+202E, U+2066 to U+2068): none; U+2069: 2.

| Normalization | Raw | Cleaned |
|---|---|---|
| Docs not already in NFC | 1 (1 character changed) | 0 |
| Docs that NFKC would change | 3,318 (6.6%) | 2,356 (11.9%) |
| Characters NFKC changes beyond NFC | 16,399 | 12,982 |

NFKC changes are mostly no-break space (15,087 raw) to a space, then superscript ² (868), the ellipsis character (110), ½ (77), № (24), ³ (23), ″ (23), thin space (15), and fullwidth tilde (15). The Arabic Presentation Forms-A range holds 113 occurrences of only two characters, the ornate brackets ﴾ ﴿ (U+FD3E, U+FD3F); no presentation-form letters or ligatures occur. Presentation Forms-B holds only a byte-order mark (3 occurrences).

**Forces.** Which normalization form is applied (NFC as in §8 step 1, NFKC, or a custom mapping), and what happens to no-break space, zero-width characters, and the other items above. NFC changes almost nothing in this corpus; NFKC changes about one cleaned document in eight.

**Open.** Whether zero-width non-joiner is kept (it separates letters inside names) or removed; whether NFKC's changes to superscripts and the ellipsis are wanted.

## 12. Markup and template residue

**Seen.** HTML and wiki syntax survive in the text: `</span>` (id 1569), `<ol start=5>` and a wiki table (id 3886), `<blockquote>` (id 5331), `<div class="ltr">` (id 6961), `<ref>` (id 18750), `</onlyinclude>` (id 20384), and `</div id="France v Italy" >` (W78). Stripped templates leave empty brackets ("( )" id 5076, "()" id 14586; W28 "(و. )") and broken sentences (W29 "يلعب ك."). The census-place template prints numeric artifacts ("435.86400000000003" id 8352260; W75).

**Measured.**

| Pattern | Raw: occurrences / docs | Cleaned: occurrences / docs |
|---|---|---|
| HTML-like tag | 830 / 203 (0.41%) | 342 / 126 (0.64%) |
| Vertical bar \| (table and template syntax) | 78,375 / 370 | 3,889 / 208 |
| Left brace { | 465 / 235 | 325 / 163 |
| URL | 1,015 / 528 (1.06%) | 157 / 85 (0.43%) |
| Empty brackets ( ), [ ], « » | 570 / 286 (0.57%) | 440 / 209 (1.06%) |
| Decimal number with 8 or more decimals | 33 / 33 | 32 / 32 |
| Run of 4 or more of the same Arabic letter | 2 / 2 | 2 / 2 |

**Forces.** What the tokenizer is trained on depends on how much of this residue §8 step 2 (markup, wiki residue, URL removal) strips before training; residue left in the training text can enter the vocabulary as pieces.

**Open.** Whether empty brackets and numeric artifacts count as markup residue for step 2 or stay in the text.

## 13. Character coverage of the alphabet

**Measured.**

| | Raw | Cleaned |
|---|---|---|
| Distinct characters | 2,636 | 2,269 |
| Characters occurring exactly once | 935 | 875 |
| Distinct characters covering 99% of all characters | 77 | 65 |
| 99.9% | 126 | 118 |
| 99.99% | 483 | 400 |
| 99.999% | 1,961 | 1,760 |
| 100% | 2,636 | 2,269 |

**Forces.** The character coverage the vocabulary is built to guarantee, and how any uncovered character is represented. The rows above give the number of distinct characters needed for each coverage level.

**Open.** Where to cut the tail. Beyond the 99.99% level there are 2,153 raw characters (1,869 cleaned), of which 935 (875 cleaned) occur exactly once; their scripts were not tabulated (section 9 lists the other scripts by letter count).

## 14. Observations from FineWeb-2 that were not measured

FineWeb-2 is held in reserve (ADR-0001). These observations come from the 100-document reading sample only and have no counts. They become tokenizer questions only if FineWeb-2 is added; measuring them is `inspect_data.py --char-stats --candidates fineweb2` (same sample as `metrics.md`; not run).

- **Letter hiding with tatweel, spaces, and dots** ("الحـ .ـريق", F43).
- **Persian-script letters inside Arabic words** (F37), as in section 3.
- **Missing spaces from extraction** ("منذالصباح", F22; "ويركزمعهد بحوثالعامة", F52; "2013عادت", F1), as in section 8.
- **Machine-translated spacing** (" ، " and " . " before punctuation, F8, F31, F72, F94), as in section 10.
- **Hamza-less spellings and ه for ة** (F23, F39, F68, F74), as in section 7.
- **Arabic-Indic digits in news text** (F9, F14, F20), as in section 6.
- **A fully diacritized long document** (F48), as in section 4.
- **Dialect words in otherwise standard text** (F10, F69). No document was rated dialect in either sample.
- **Repeated-letter elongation** is absent from Wikipedia (2 runs in 2 documents) and is not measured on web text.
