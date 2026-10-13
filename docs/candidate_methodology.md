# Candidate generation methodology (T4)

This stage produces candidate **labels** only. It does not check registration,
availability, premium pricing, trademark status, or legal suitability. No live
RDAP or WHOIS queries were made while building these files. Every result must
be checked against the registry before anyone describes it as available.

The inputs are curated text files under `data/seeds/`, plus the local quality
and blocklist rules. `#` begins a comment. Generators have no network
dependency. Output is stable: labels are deduplicated across categories,
supported singular/plural pairs keep one higher-ranked row, and CSV rows are
sorted by label. T3 categories retain their documented caps. T4 categories
have no target count or ranking cap; their curated pair lists and shared gates
determine the output. The regression suite keeps each category above the
requested approximate 250-row representation floor without adding rows
automatically to reach it. A separate 14-character label ceiling keeps T4
candidates easier to spell and remember.

## CSV and category counts

The CSV columns are `domain_label,category,method,seed,tags,quality_score`.
`category` is the primary category. `tags` is semicolon-separated and can
include both generation reasons (`abbr`, `word`, `cvcv`, `phonotactic`) and
other applicable candidate categories. `quality_score` is a deterministic
0-100 heuristic, not an availability or resale score.

The committed pool contains 6,204 globally unique rows: 4,785 from T3 and
1,419 new T4 primary rows. The hard acceptance minimum of 5,000 is met. The
prior planning range was 2,500-3,500 new T4 rows; this curated pool is 1,081
below its lower end. Four categories land between 252 and 289 rows, while
business_finance has 359. The rework reference was roughly 250-800 per
category. These counts reflect the reviewed names without quota padding.

| Category | Current rows | Prior whitelist rows (`cfa05b5`) | Change | Change vs. 1,200-row baselines | Generation approach |
| --- | ---: | ---: | ---: | ---: | --- |
| `domain_hacks` | 135 | — | — | — | Pronunciation-reviewed `-cy` / `-sy` / `-see` completions plus clear phrases |
| `ai` | 1,500 | — | — | — | Curated AI concept and product compounds, plus selected blends |
| `short` | 700 | — | — | — | Meaningful abbreviations and words, plus pronounceable CVCV labels |
| `dictionary` | 1,050 | — | — | — | Screened common English noun/adjective seeds |
| `invented` | 1,400 | — | — | — | Stem/ending combinations with spelling and repeated-chunk checks |
| `technology` | 254 | 313 | -59 | -946 | Explicit technology root/suffix pairs |
| `business_finance` | 359 | 468 | -109 | -841 | Explicit finance and business root/suffix pairs |
| `health_science` | 252 | 271 | -19 | -948 | Explicit health and science root/suffix pairs |
| `consumer_brands` | 265 | 331 | -66 | -935 | Explicit consumer, travel, education, and retail pairs |
| `emerging_industries` | 289 | 416 | -127 | -911 | Explicit emerging-technology root/suffix pairs |

Both earlier reviewed baselines (`fc0f2b8` and `1696b43`) had 1,200 rows in
each T4 category. Changes against those baselines are shown in the table;
changes against the accepted whitelist output at `cfa05b5` reflect the 14-letter
ceiling, shorter roots, and additional semantic pair pruning. Counts also
reflect global deduplication, supported plural deduplication, shared quality
gates, and cross-category primary-row selection.

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

T4 generation has no per-category quota or rank cap; tests retain the requested
approximate 250-row floor for category representation. Its 14-character
quality-gate limit is a label-length rule, not a way to force a count. The
combined pool clears the hard 5,000 minimum and falls short of the 2,500-row
T4 planning range by 1,081. T3 ceilings and deterministic ranking remain as
before. Neither a length rule nor a score establishes commercial usefulness.

## Quality gate

Every candidate must:

- pass `si_domains.rules.classify(label) == "ok"`;
- use lowercase ASCII letters only, with no hyphens, IDNs, or digits;
- fit the category bounds (short 2-5; AI 3-16; all five T4 categories 3-14;
  dictionary 4-15; domain hacks 2-15; invented 4-9; committed
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

The five sector vocabularies were written for this project and have no external
word-list dependency. Each category has a `*_roots.txt` list of
sector-specific terms, a `*_suffixes.txt` list of product heads, a
`*_standalone.txt` allowlist for roots that work alone, and a
`*_compounds.txt` explicit whitelist with one reviewed `root+suffix` pair per
line. The generator never forms a Cartesian product. It validates all
components, rejects duplicate and unknown pairs, rejects exact generic terms
from `data/blocklist_generic_candidate_terms.txt`, and rejects pairs that
repeat a component inside the other (`workflow+flow`, `footwear+wear`, and
`microgrid+grid`). Generic heads such as `works` and `ops` remain only on
selected roots where that phrase reads naturally; they are not joined to every
root. Only listed compounds, listed standalone roots, and named blends in the
generator modules become candidates. The `seed` column records the source
terms, and the method column distinguishes `root`, `compound`, and `blend`.
Shared spelling, registry, brand, offensive-language, quality, global dedupe,
and plural safeguards still apply afterward.

| Category | Roots | Suffixes | Explicit pairs | Standalone roots | Generated primary rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| `technology` | 64 | 18 | 331 | 12 | 254 |
| `business_finance` | 70 | 16 | 430 | 12 | 359 |
| `health_science` | 67 | 19 | 303 | 12 | 252 |
| `consumer_brands` | 79 | 17 | 325 | 12 | 265 |
| `emerging_industries` | 73 | 20 | 361 | 12 | 289 |

`technology` covers cloud infrastructure, cybersecurity, software delivery,
fintech, blockchain, and connected systems. Its suffix heads include `stack`,
`mesh`, `vault`, `ops`, `grid`, `forge`, `scan`, and `works`; each suffix is
used only on listed compatible roots. Selected blends are `devops`, `netops`,
and `infosec`.

`business_finance` covers investing, trading, banking, insurance, startups,
venture capital, and business services. Its heads include `desk`, `flow`,
`track`, `signal`, `ledger`, `vault`, `quote`, and `launch`. Broad `works`,
`ops`, and `studio` pairings were pruned where they did not name a credible
finance product or service. Selected blends are `fintech`, `insurtech`,
`regtech`, `wealthtech`, and `proptech`.

`health_science` covers healthcare delivery, biotech, diagnostics, longevity,
pharma, and scientific research. Roots include research terms such as `helix`,
`myelin`, `synapse`, `serum`, `plasma`, `cytokine`, `organoid`, `ribosome`,
`chromatin`, and `antigen`. Familiar shorter clinical forms (`cardio`,
`derma`, `gyn`, `hemo`, `immuno`, `nephro`, `physio`, `geri`, and `peds`)
replace long specialty spellings where they preserve meaning and fit the
14-character limit. Heads include `lab`, `scan`, `assay`, `clinic`, `scope`,
`sequence`, `marker`, `atlas`, and `trial`. The whitelist removes tautological
or weak joins such as `tumor+assay`, `rehab+therapy`, `neuron+therapy`,
`dosage+clinic`, and `pharma+therapy`. Selected blends are `biotech`,
`medtech`, `healthtech`, `telehealth`, and `neurotech`.

`consumer_brands` covers fashion, travel, entertainment, lifestyle, education,
and ecommerce. Its heads include `studio`, `shop`, `club`, `house`, `box`,
`craft`, `wear`, `school`, `course`, `booking`, `stay`, and `gear`. Redundant
education joins such as `academy+class`, `academy+school`, `campus+course`, and
`tutoring+course` were removed. Selected blends include `edtech`, `ecommerce`,
`staycation`, and `athleisure`.

`emerging_industries` covers robotics, quantum systems, energy storage,
advanced materials, and autonomous systems. Roots include `cobot`, `lidar`,
`qubit`, `tidal`, `graphene`, `lithium`, `orbit`, and short sector forms `agri`
and `desal`. General computing roots were removed from this category. Heads
include `cell`, `grid`, `dock`, `control`, `mesh`, `engine`, `flight`,
`sensor`, `drive`, and `storage`, with only reviewed compatible pairings
retained. Examples of rejected joins include `propulsion+engine`,
`autopilot+drive`, `aerospace+grid`, `hydro+hub`, and `additive+grid`. Selected
blends include `cleantech`, `greentech`, `climatetech`, `agritech`,
`spacetech`, `foodtech`, and `autotech`.

The seed-1 `docs/candidate_samples.md` file contains 40 candidates from each
of all ten categories. `docs/candidate_review_draws.md` records five
deterministic random draws (seeds 1, 3, 7, 42, and 99), with 40 names from each
new category per seed. My final manual review marked zero names as
non-brandable in each 40-name category draw. Re-review removed long forms and
weak exact pairs including `propulsion+engine`, `tumor+assay`,
`rehab+therapy`, `neuron+therapy`, `bookkeeping+works`, `underwriting+ops`,
`dosage+clinic`, `pharma+therapy`, `antigen+trial`, `tutoring+course`,
`campus+course`, `cruise+stay`, `autopilot+drive`, and `aerospace+grid`.
Shorter forms such as `agri` and `desal` keep useful industry concepts within
the length limit. Earlier reviewed examples with generic filler (`zone`,
`region`, `source`, `care`, `life`, `guide`, `measure`, `home`, `ocean`,
`solar`, and `energy`) remain excluded as exact roots or pairs. These lists
apply to exact components and pairs, not substrings, so neutral health,
technical, identity, religious, and fantasy vocabulary remains eligible where
it passes category and shared quality rules. Review catches obvious spelling
and semantic problems; it is not a trademark, demand, or availability screen.

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

The five T4 sector root/suffix vocabularies and exact pair whitelists were
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
