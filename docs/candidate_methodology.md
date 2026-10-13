# Candidate generation methodology (T4)

This stage produces candidate **labels** only. It does not check registration,
availability, premium pricing, trademark status, or legal suitability. No live
RDAP or WHOIS queries were made while building these files. Every result must
be checked against the registry before anyone describes it as available.

The inputs are curated text files under `data/seeds/`, plus the local quality
and blocklist rules. `#` begins a comment. Generators have no network
dependency. Output is stable: labels are deduplicated across categories,
supported singular/plural pairs keep one higher-ranked row, and CSV rows are
sorted by label. T3 categories retain their documented caps; T4 categories are
not capped, so their counts reflect reviewed pair lists and shared gates.

## CSV and category counts

The CSV columns are `domain_label,category,method,seed,tags,quality_score`.
`category` is the primary category. `tags` is semicolon-separated and can
include both generation reasons (`abbr`, `word`, `cvcv`, `phonotactic`) and
other applicable candidate categories. `quality_score` is a deterministic
0-100 heuristic, not an availability or resale score.

The committed pool contains 7,323 globally unique rows: 4,785 from T3 and
2,538 new T4 primary rows. The hard acceptance minimum of 5,000 is met. The
rework planning target was about 600-900 rows per T4 category and about
8,000-9,300 rows overall. Four categories are 52-187 rows below the 600-row
lower bound; consumer_brands is within range. The pool is 677 below the lower
combined planning target. No rows were added to meet a quota.

| Category | Rows | Brief target | Generation approach |
| --- | ---: | ---: | --- |
| `domain_hacks` | 135 | 700 | Pronunciation-reviewed `-cy` / `-sy` / `-see` completions plus clear phrases |
| `ai` | 1,500 | 1,300 | Curated AI concept and product compounds, plus selected blends |
| `short` | 700 | 500 | Meaningful abbreviations and words, plus pronounceable CVCV labels |
| `dictionary` | 1,050 | 800 | Screened common English noun/adjective seeds |
| `invented` | 1,400 | 1,200 | Stem/ending combinations with spelling and repeated-chunk checks |
| `technology` | 413 | 600-900 | Explicit cloud, security, software, data, hardware, and fintech pairs |
| `business_finance` | 548 | 600-900 | Explicit investing, banking, insurance, venture, and operations pairs |
| `health_science` | 426 | 600-900 | Explicit clinical, diagnostic, biotech, pharma, and research pairs |
| `consumer_brands` | 604 | 600-900 | Explicit fashion, travel, media, education, retail, and lifestyle pairs |
| `emerging_industries` | 547 | 600-900 | Explicit robotics, quantum, energy, materials, climate, and aerospace pairs |

The `domain_hacks` count is below its target. The original SCOWL v2 size 60
suffix set supplied 293 source words. Semantic and pronunciation review left
146 curated seeds, including the named audit `-sy` examples so tests can
prove they are rejected. The generator emits 120 suffix completions and 15
clear phrase completions; the shared gate and global deduplication leave 135
rows. `lunacy` is excluded as an unsuitable hack source; the exact source guard
in `data/blocklist_domain_hack_sources.txt` prevents reintroduction while
leaving `luna` available for consideration in other categories. Expanding to
size 85 exceeded 700, but its
review sample contained many rare specialist or derived forms. Those were left
out to honor the brief's no-filler requirement. Non-natural splits such as
`heresy`, `papacy`, `lacy`,
`racy`, `juicy`, `citrusy`, `geodesy`, and `primacy` are pruned only from this
category's seed file; their resulting labels are not globally blocked. The
regression test pins the reviewed count at 135
rather than treating the 700 target as met; additions should pass the same
human quality review.

The T4 categories have no per-category quota or cap. The target shortfalls are
187 rows for technology, 52 for business_finance, 174 for health_science, and
53 for emerging_industries; consumer_brands is within its target range. These
shortfalls are deliberate: the exact-pair vocabularies and semantic review
take precedence over count. T3 ceilings and deterministic ranking remain as
before. Neither a cap nor a score establishes commercial usefulness.

## Quality gate

Every candidate must:

- pass `si_domains.rules.classify(label) == "ok"`;
- use lowercase ASCII letters only, with no hyphens, IDNs, or digits;
- fit the category bounds (short 2-5; AI and all five T4 compound categories
  3-16; dictionary 4-15; domain hacks 2-15; invented 4-9; committed
  dictionary seeds are 6-9 characters);
- avoid known reserved labels, triple repeated letters, and consonant runs
  longer than three;
- include a vowel, except a short label explicitly tagged as a meaningful
  abbreviation;
- avoid the brand, offensive-language, and low-quality terms in `data/`, plus
  the exact dictionary and domain-hack source exclusions.
- receive a quality score of at least 50.

Low-quality entries are exact standalone-word and source-seed exclusions, not
substring matches. This avoids rejecting sound words such as `dynasty` because
they happen to contain a negative fragment such as `nasty`. Review removed the
named negative dictionary terms (`bestial`, `bigoted`, `bigotry`, `bribery`,
`carnage`, `carrion`, `boorish`, `buffoon`, and `anguish`) plus similarly
derogatory, criminal, harmful, death-related, or weak standalone words. Neutral
health and technical vocabulary with credible use remains eligible, including
`insulin`, `vaccine`, `therapy`, `neutron`, and `quantum`. A few weak general
dictionary seeds (`dealing`, `fatigue`, and `rumored`) were pruned only from
that category's seed file rather than globally blocked. A further semantic
pass removed `accuser`, `desolate`, `evasion`, `evasive`, `futility`, `jealous`,
`tirade`, and `polygamy` from the premium dictionary seeds. These exact terms
are also in `data/blocklist_dictionary.txt`, which applies only to the
dictionary category and protects against accidental seed reintroduction.
The short label `muka` is excluded after manual Slovenian review; the
[Fran/SSKJ² entry](https://fran.si/iskanje/SSKJ%C2%B2/trpeti?AllNoHeadword=trpeti&FilteredDictionaryIds=133&Query=trpeti&View=1)
uses it for suffering and torment. The exact-word rule avoids blocking
unrelated labels that share only part of its spelling.

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

`data/seeds/domain_hacks.txt` contains reviewed English ending-word sources
from SCOWL v2 size 60. The generator replaces final `-cy` with `.si`; it
replaces `-sy` only when the spelling and pronunciation produce a natural
read. The audit examples `posy`, `newsy`, `tansy`, `teensy`, `outdoorsy`, and
`woodsy` are retained as regression fixtures and never emitted. Five have
voiced endings supported by the pronunciation entries for [*posy*](https://www.merriam-webster.com/dictionary/posy),
[*newsy*](https://www.merriam-webster.com/dictionary/newsy),
[*tansy*](https://www.merriam-webster.com/dictionary/tansy),
[*outdoorsy*](https://www.merriam-webster.com/dictionary/outdoorsy), and
[*woodsy*](https://www.merriam-webster.com/dictionary/woodsy). [*Teensy*](https://www.collinsdictionary.com/us/dictionary/english/teensy)
is accent-sensitive: Collins records an American /s/ and British /z/
pronunciation, so it is rejected for an unreliable read. [*Pansy*](https://www.merriam-webster.com/dictionary/pansy)
and [*quinsy*](https://www.merriam-webster.com/dictionary/quinsy) are also
excluded for semantic reasons. The source review removed weak, negative, and
obscure forms such as `idiocy`, `contumacy`, `plangency`, `regeneracy`,
`mendicancy`, `lunacy`, `baronetcy`, `inefficacy`, and `inexpediency`; disease
names with awkward suffix splits and rare ecclesiastical or military titles
were removed only from this category's seeds. Pronunciation and split
exclusions never globally block an otherwise
valid label in another category. Final `-see` and `-si` use the same
natural-read check. The small phrase
list covers clear reads such as “go see”, “wait and see”, and “come and see”.
Every resulting label must pass the shared gate.

### `ai`

The generator combines curated concepts in `ai.txt` with product and
infrastructure heads in `ai_products.txt`; a second pass uses reviewed clipped
stems for pronounceable blends. Sample review removed generic heads that
produced weak AI joins, including `base`, `field`, `garden`, `harbor`, and
`path`. The result is ranked and capped at 1,500. `data/blocklist_brands.txt`
blocks well-known AI marks and major product/company names, including the
names called out in the brief.

### T4 sector categories

The five T4 concept and product vocabularies were written for this project.
Concept files contain distinctive sector roots. Product files contain a
compact set of suffix heads such as `hub`, `lab`, `works`, `stack`, `scan`,
`desk`, `grid`, and `forge`. The consumer vocabulary was reduced from 78 to 31
reviewed heads to keep its broader set of subsectors manageable. Each category
also has a `*_pairs.txt` file with
lines of the form `concept|suffix,suffix`. The shared loader validates every
root and suffix against its source vocabulary, rejects malformed or duplicate
pairs, and emits only the exact listed combinations. It never infers
compatibility from matching groups or crosses whole vocabularies. Each row
records its two source terms in `seed`; selected natural blends keep their
named source and `blend` method. Substring-redundant joins are dropped before
the shared spelling, registry, brand, offensive-language, and quality gates.

- `technology`: cloud platforms, security, software delivery, data compute,
  connected hardware, and fintech infrastructure. Pair choices use heads such
  as `stack`, `mesh`, `vault`, `ops`, `grid`, and `forge`. Natural shorthand
  includes `devops`, `netops`, and `infosec`.
- `business_finance`: investment markets, banking and payments, insurance,
  startup and venture tools, business operations, and professional services.
  Pairs use finance tools such as `desk`, `flow`, `ledger`, `vault`, and
  `quote`. Selected blends are `fintech`, `insurtech`, `regtech`, `wealthtech`,
  and `proptech`.
- `health_science`: care delivery, diagnostics and imaging, biotech and
  genomics, pharma trials, longevity and wellness, and research. Clinical
  heads include `lab`, `scan`, `assay`, `clinic`, `atlas`, and `track`. Selected
  blends include `biotech`, `medtech`, `healthtech`, `telehealth`, and
  `neurotech`.
- `consumer_brands`: fashion and beauty, travel and hospitality, media and
  entertainment, education, retail and ecommerce, and lifestyle communities.
  Its 31 reusable product heads include `studio`, `shop`, `house`, `club`,
  `booking`, `box`, `craft`, `school`, and `gear`; exact root/head pairs are
  listed individually. Selected blends include `edtech`, `ecommerce`,
  `staycation`, and `athleisure`.
- `emerging_industries`: robotics and autonomy, quantum computing, energy
  storage, advanced materials, climate and agriculture, and aerospace. Pairs
  name products or infrastructure such as `cell`, `grid`, `plant`, `storage`,
  `flight`, and `control`. Selected blends include `cleantech`, `greentech`,
  `climatetech`, `agritech`, `spacetech`, `foodtech`, and `autotech`.

All ten seed-1 sample sections were regenerated and read by hand. Fresh random
draws of 100 candidates per category also used seeds 1, 7, and 42. The three
T4 review passes initially rejected 7, 2, and 3 names, respectively, across
the five categories. They led to exact whitelist edits; final T4 draws
produced no further rejections. The corresponding T3 and AI draws produced no
additional seed changes after the AI head cleanup described above. Examples
removed include same-class or redundant pairs (`exam+quiz`, `basket+cart`,
`festival+show`, `genome+omics`, `soil+plant`), verb or adjective joins
(`underwrite+works`, `insure+quote`), and weak/mismatched pairs
(`aquaponic+cell`, `microbiome+cell`, `trial+therapy`, `music+live`,
`decarbon+plant`, and `additive+cell`). The review also excluded the weak
examples named in the task such as `region+harbor`, `healthy+care`,
`water+market`, and `alloy+carbon`. Pair exclusions are category-scoped; words
are not globally banned. CSV rows and review samples are regenerated from
inputs, never hand-edited. Review checks spelling and obvious semantic fit; it
is not a trademark, demand, or availability screen.

### `dictionary`

`data/seeds/dictionary.txt` contains 1,184 retained 6-9 letter US English
noun/adjective entries from an initial 1,450 SCOWL v2 size 35 selections.
Selection favors a seven-letter length, a comfortable vowel ratio, and simple
consonant transitions. A full semantic pass removed 266 weak, derogatory,
criminal, harmful, disease-related, or unsuitable standalone words from the
seeds, including the eight exact terms listed above; the category-scoped
exact-word gate also protects future additions.
The output retains neutral specialist words such as `insulin`, `vaccine`,
`therapy`, `neutron`, and `quantum`. The committed output is ranked and capped
at 1,050.

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

The five T4 sector concept/product vocabularies and exact pair whitelists were
authored and reviewed locally for this project. They were not downloaded from
an external word list, so the ESDB-derived seed notice below applies to the
earlier dictionary and domain-hack inputs, not to these T4 files.

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
