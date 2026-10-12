# Candidate generation methodology (T3)

This stage produces candidate **labels** only. It does not check registration,
availability, premium pricing, trademark status, or legal suitability. No live
RDAP or WHOIS queries were made while building these files. Every result must
be checked against the registry before anyone describes it as available.

The inputs are curated text files under `data/seeds/`, plus the local quality
and blocklist rules. A seed line is one term; `#` begins a comment. Generators
have no network dependency. Output is stable: labels are deduplicated across
categories, near-identical singular/plural pairs keep one higher-ranked row,
and CSV rows are sorted by label. Equal-score candidates are selected with a
stable SHA-256 tie-break when a category limit applies.

## CSV and category counts

The CSV columns are `domain_label,category,method,seed,tags,quality_score`.
`category` is the primary category. `tags` is semicolon-separated and can
include both generation reasons (`abbr`, `word`, `cvcv`, `phonotactic`) and
other applicable candidate categories. `quality_score` is a deterministic
0-100 heuristic, not an availability or resale score.

The committed T3 pool contains 4,915 unique rows:

| Category | Rows | Brief target | Generation approach |
| --- | ---: | ---: | --- |
| `domain_hacks` | 265 | 700 | Pronunciation-safe `-cy` / `-sy` / `-see` completions plus a small set of clear phrases |
| `ai` | 1,500 | 1,300 | Curated AI concept and product compounds, plus selected blends |
| `short` | 700 | 500 | Meaningful abbreviations and words, plus pronounceable CVCV labels |
| `dictionary` | 1,050 | 800 | Screened common English noun/adjective seeds |
| `invented` | 1,400 | 1,200 | Stem/ending combinations with spelling and repeated-chunk checks |

The `domain_hacks` count is below its target. SCOWL v2 size 60 supplied 293
possible ending words; after sound exceptions, blocklists, registry checks and
deduplication, 265 remain. Expanding to size 85 exceeded 700, but a review
sample contained many rare specialist or derived forms. Those were left out to
honor the brief's no-filler requirement. The automated test records a smaller
minimum for this category so future seed additions can improve the count
without legitimizing weak candidates.

Category ceilings keep this phase focused on the overall 10,000-12,000 name
pool planned across T3 and T4. When a generator produces more than its ceiling,
the highest quality scores are kept and ties are resolved deterministically;
for `short`, the explicitly curated words and abbreviations are retained
before filling the remaining slots with CVCV candidates.

## Quality gate

Every candidate must:

- pass `si_domains.rules.classify(label) == "ok"`;
- use lowercase ASCII letters only, with no hyphens, IDNs, or digits;
- fit the category length (2-5 for short, up to 16 for AI, up to 15 for other
  categories; dictionary words are 4-9 characters in the committed seeds);
- avoid known reserved labels, triple repeated letters, and consonant runs
  longer than three;
- include a vowel, except a short label explicitly tagged as a meaningful
  abbreviation;
- avoid the brand, offensive-language, and low-quality terms in `data/`.
- receive a quality score of at least 50.

Brand entries of five or more letters are blocked as substrings. Shorter marks
are blocked as exact labels or when present as a generator seed component.
Offensive entries of four or more letters are blocked as substrings; shorter
entries require a whole-token match. The offensive list is a conservative
starter screen across English, German, French, Spanish, Italian, and Slovenian
ASCII spellings, not a complete translation or trademark search.

The score combines length fit (30%), vowel ratio (25%), consonant-cluster
comfort (25%), and seed quality (20%). These weights only help rank candidates;
they do not override a rejection rule. The current implementation is in
`si_domains/candidates/quality.py`.

## Category generation

### `domain_hacks`

`data/seeds/domain_hacks.txt` contains English source words from SCOWL v2 size
60. For final `-cy`, the generator replaces those letters with `.si`; it does
the same for `-sy` only when the suffix is pronounced with an unvoiced /s/.
Words where the ending is /zee/ (such as *easy* or *daisy*) are excluded. Final
`-see` and `-si` are handled only for accepted source spellings. A short
curated phrase list covers clear reads such as “go see” and “wait and see”.
The domain label must still pass the shared gate.

### `ai`

The generator crosses curated concepts in `ai.txt` with product and
infrastructure terms in `ai_products.txt`. A second pass uses reviewed clipped
stems for pronounceable blends. The result is ranked and capped at 1,500.
`data/blocklist_brands.txt` blocks well-known AI marks and major product/company
names, including the names called out in the brief.

### `dictionary`

`data/seeds/dictionary.txt` contains 1,450 selected 6-9 letter US English
noun/adjective entries from SCOWL v2 size 35. Selection favors a seven-letter
length, a comfortable vowel ratio, and simple consonant transitions. The
shared gate and `blocklist_low_quality.txt` remove known weak, negative, or
unsuitable standalone terms. The committed output is ranked and capped at
1,050.

### `short`

`short_abbr.txt` holds selected 2-5 letter abbreviations; `short_words.txt`
holds compact English words. `short_onsets.txt` and `short_endings.txt` define
the CVCV combinations. Rows are tagged with `abbr`, `word`, or `cvcv` to show
why they qualify. The ranked output ceiling is 700.

### `invented`

`invented_stems.txt` crosses with `affixes.txt`, which contains vowel endings
and short brandable morphemes. Matching boundary letters are merged, and the
quality gate rejects spelling clusters, repeated letters, and repeated
two/three-letter chunks. The ranked output ceiling is 1,400.

## Word-list source and license

Dictionary and suffix seeds were derived from the English Speller Database
(ESDB, formerly SCOWL v2), using its US English word-list view and the size and
variant filters described above. Source snapshot:
[en-wl/wordlist at commit `1e5b7d3a72f47a71da5d28686c1dd4b397178485`](https://github.com/en-wl/wordlist/tree/1e5b7d3a72f47a71da5d28686c1dd4b397178485).
The upstream project describes the combined database and generated word lists
as available under its MIT-like permission; see the
[upstream copyright file](https://github.com/en-wl/wordlist/blob/1e5b7d3a72f47a71da5d28686c1dd4b397178485/Copyright).

The required upstream notice for the derived seed lists is reproduced here:

> Copyright 2000-2026 by Kevin Atkinson
>
> Permission to use, copy, modify, distribute, and sell any part of the English
> Speller Database (ESDB, previously known as SCOWLv2), or word lists created
> from it, is hereby granted without fee, provided that the above copyright
> notice appears in all copies and that both that copyright notice and this
> notice appear in supporting documentation. Kevin Atkinson makes no
> representations about the suitability of this database for any purpose. It
> is provided "as is" without express or implied warranty.

## Registry syntax note

The output deliberately uses ASCII letters only even though `.si` accepts
published Latin IDN characters. This project sends ASCII-only labels to its
RDAP client; candidate generation therefore excludes IDNs and all digits.
