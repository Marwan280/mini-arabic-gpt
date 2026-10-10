# ADR 0008: Licence of the published weights

| | |
|---|---|
| **Status** | Proposed (provisional). Open to revision if a legal review, or a statement from Wikimedia or Creative Commons about model weights, changes the picture |
| **Date** | 2026-10-10 |
| **Deciders** | Marwan |
| **Related** | `docs/adr/0001-training-corpus.md` (licence consequence); `docs/03-data-spec.md` §13; `docs/10-model-card.md` §6; `docs/09-ui-spec.md` §9; PRD §9 |
| **Evidence** | Sources read on 2026-10-10 (listed below); none is legal advice and no lawyer was consulted |

## Context

The weights may be published on the Hugging Face Hub (model repository only, no Space; optional and after v1). The training text is Arabic Wikipedia. ADR-0001 and the Data Spec §13 recorded that whether the share-alike condition of Wikipedia's licence applies to trained weights is unresolved and proposed releasing the weights under CC BY-SA with attribution. This ADR records the research behind that proposal and the exact licence.

## What the sources say

| Question | Finding | Source |
|---|---|---|
| Which licence covers the training text? | The `wikimedia/wikipedia` dataset card (snapshot 20231101, the one used) lists `cc-by-sa-3.0` and `gfdl` and states that all original textual content is licensed under the GFDL and the Creative Commons Attribution-Share-Alike 3.0 licence, and that some text may be available only under the Creative Commons licence | [dataset card](https://huggingface.co/datasets/wikimedia/wikipedia) |
| And for current contributions? | The Wikimedia Terms of Use say text contributors license it under CC BY-SA 4.0 and the GFDL, and that "reusers may comply with either license or both"; English Wikipedia's copyright policy page names CC BY-SA 4.0 and the GFDL | [Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), [Wikipedia:Copyrights](https://en.wikipedia.org/wiki/Wikipedia:Copyrights) |
| May a CC BY-SA 3.0 work's adaptation be released under 4.0? | CC BY-SA 3.0 §4(b) allows distributing an Adaptation only under (i) this licence, (ii) "a later version of this License with the same License Elements", or (iii) a jurisdiction licence with the same elements. 4.0 is a later version, so it is allowed | [legal code](https://creativecommons.org/licenses/by-sa/3.0/legalcode) |
| Does ShareAlike reach AI models? | Creative Commons' guidance, which it says "assumes the most restrictive legal interpretation for those who wish to take a conservative approach", states: "If AI models or outputs are based on ShareAlike content and they will be shared publicly, following the ShareAlike condition would require AI developers to use the same CC license as the original works." It adds that the attribution and ShareAlike conditions "are triggered only when works or adaptations of works are publicly shared" | [CC: Using CC-licensed works for AI training](https://creativecommons.org/using-cc-licensed-works-for-ai-training-2/) |
| Does the licence apply at all to training? | CC's FAQ: the licences "grant permission for reuse in any situation that requires permission under copyright"; many uses, for example fair uses, need no permission, and then the licence conditions do not matter | [CC FAQ](https://creativecommons.org/faq/) |
| Has Wikimedia said whether weights are adaptations? | **None found.** A search found Wikimedia's general position (credit the sources and use its paid Enterprise access rather than scraping) and a December 2024 law review article reported to say that questions on reproduction, adaptation, attribution, and share-alike remain unresolved; the article itself was not read | web search results, 2026-10-10; [article page](https://publicera.kb.se/siplr/article/view/62457) |
| Is the licence identifier valid on the Hub? | `cc-by-sa-4.0` is in the Hub's list of licence identifiers | [Hub licences](https://huggingface.co/docs/hub/repositories-licenses) |

## Decision

**Provisional (author's choice, 2026-10-10): the published weights and the Model Card are released under CC BY-SA 4.0, with the attribution block of `10-model-card.md` §6; the code stays under the MIT licence of the repository.**

- Nothing is published in v1 unless the author decides to. The licence matters from the moment the weights leave the machine; a purely local demo triggers neither the attribution nor the share-alike condition, on CC's own reading (they apply when works or adaptations are publicly shared).
- CC BY-SA 4.0 satisfies the conservative reading (same licence as the source, a later version of the 3.0 licence) and, if the weights are not an adaptation at all, the author is free to license them as he or she chooses, including under CC BY-SA 4.0. It is not claimed that share-alike applies.
- The weights are not released under the GFDL; the Terms of Use say reusers may comply with either licence.
- The attribution block names the dataset, snapshot, and authors' page, and states that the question is unsettled.

## Alternatives considered

| Alternative | Outcome | Why |
|---|---|---|
| Apache-2.0 or MIT for the weights | Not chosen (author) | Permissive, but if share-alike applies, it would not comply; it reverses the conservative choice the sources support |
| CC BY-SA 3.0 | Not chosen | The same conditions, but 4.0 is the version Wikimedia's Terms of Use now name for new contributions; both identifiers exist on the Hub, and 3.0 §4(b) allows 4.0 |
| A custom or "other" licence | Rejected | Needs its own text in the repository and is less recognizable |
| Do not publish the weights | Always possible | Keeps v1 local; the author may publish later |
| Wait for a legal review | Not available | No lawyer is involved in this project; the decision is a conservative default, not a conclusion |

## Consequences

**Positive**

- A choice that is compliant under the strictest reading found, easy to state, and consistent with ADR-0001's mitigation.
- Downstream users get a clear licence on the Hub (`license: cc-by-sa-4.0`).

**Negative and risks**

- **It restricts reuse of the weights** to those who accept share-alike; a user who wants a permissive licence cannot have it. If it turns out that share-alike does not apply, the choice was more restrictive than needed.
- **Outputs.** The model can reproduce training text (1.9% of 8-token windows for a weak pilot, `07` §5.7); a verbatim output could carry the source's licence. The Model Card says so.
- **The sources are secondary.** The CC guidance is explicitly conservative; no statement by Wikimedia about weights was found; the law review article was not read; the Wikipedia dump's licence note says some text may be CC-only or under other licences.
- **No legal advice** was taken.

**Changes this decision requires**

- The attribution block in `10-model-card.md` §6 and the YAML `license: cc-by-sa-4.0`; a `LICENSE` note in the model repository that the code is MIT and the weights CC BY-SA 4.0 (the repository's `LICENSE` file is unchanged).
- Data Spec §13 and ADR-0001 keep their statements; this ADR supplies the evidence.

**Limits of the evidence**

- The CC pages were read through downloaded text and search results; the full CC legal analysis (a PDF) was not read.
- The licence of each Wikipedia article's individual contributors was not checked.

## Revisit triggers

1. A legal review, or a statement by Wikimedia or Creative Commons, says that weights are, or are not, adaptations.
2. The corpus changes (for example, FineWeb-2 is added): its licence terms (ODC-By and the source sites' terms) would be added to the analysis.
3. The author decides to publish: re-read the Hub's and Wikimedia's current terms.
4. A user or Wikimedia raises a concern about the release.
