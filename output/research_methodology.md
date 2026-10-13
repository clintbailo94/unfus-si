# PKG-D ranked `.si` research methodology

Research snapshot: 2026-10-13 UTC. These artifacts supplement the existing
RDAP/WHOIS shortlist. They do not turn the scoring heuristic into a sale-price
valuation, trademark clearance, or registrar checkout result.

## Comparable-sale evidence and valuation rule

`valuation_evidence.csv` contains 15 curated evidence items: 10 reported
completed sales, two asking prices, and three NameBio individual-sale-page
access failures. The completed-sale records retain the original reported USD
amounts and link to NameBio-authored daily reports on NamePros or Domain Name
Wire reporting. For example, NameBio's report lists [`ai.si` at USD 34,000](https://www.namepros.com/threads/housr-com-sold-for-40-000-ai-si-for-34-000.1352464/),
[`recursive.si` at USD 20,000](https://www.namepros.com/threads/reply-ai-sold-for-77-000-recursive-si-for-20-000.1387881/),
and [`build.si` at USD 17,435](https://www.namepros.com/threads/archon-tech-sold-for-35-000-build-si-for-17-435.1388779/).
Domain Name Wire reports the buyer context for [Recursive.si and Military.si](https://domainnamewire.com/2026/06/11/who-is-buying-si-domain-names/).
September's reports include [`models.si` at USD 5,458 and `stack.si` at USD 3,988](https://www.namepros.com/threads/avive-com-sold-for-210-000-mytickets-com-for-25-000.1399851/).

The sales provide market context, but none was curated as a direct comparable
for a shortlisted name. `ai.si` is an exceptionally scarce two-character
abbreviation; the word and technology sales have semantics unlike the current
brandables and compounds; the reported end-user deals include buyer-specific
names; and the reported September activity was unusually high. No public sale
in this pass matched the shortlist's label-plus-`.si` completed-seed phrase
hacks or its random four-letter pronounceables. The evidence records explain
each row's relevance and limits.

The two asking-price records are separate from sale evidence:
[`build.si` displayed USD 10,000,000](https://build.si/) and
[`seed.si` displayed USD 8,000,000](https://seed.si/) on the access date. Those
are asks, not transactions; `build.si` also has a separately reported sale.
NameBio's public individual-sale pages for `hollywood.si`, `otherwise.si`, and
`pocket.si` returned HTTP 403. The single attempts were recorded as
`unsupported`; no access restriction was bypassed.

The offline valuation builder emits a numeric speculative range only if at
least two distinct `.si` domains are curated as `completed_sale` and
`direct_comparable`, share the target category and currency, and have label
lengths within two characters. Only original GBP or USD records can support a
range; there is no currency conversion. Asking prices, unrelated items, other
extensions, and unsupported source attempts cannot support numbers. The
current result is **0 supported ranges and 500 `insufficiently supported`**.
This is an evidence limit, not a conclusion that the domains have no value.
Extension liquidity and buyer pools differ; `.com` prices are never converted
mechanically to `.si`.

## Candidate classification and quality review

The candidate pool remains **6,204 unique labels**. The curated exact-label
list in `data/given_names.txt` moves known given names and pseudo-names out of
`dictionary` into `invented`, adds the `given_name` tag, and records the
reclassification method. The list is based on reviewed proper-name examples
and the PKG-D false-dictionary audit. No suffix-only name regex is used;
`-ina`, `-ena`, `-ora`, `-aro`, `-ino`, and `-ali` are not sufficient evidence
on their own. Exact technical/niche exceptions such as `galium` and `karaya`
are tagged `technical_term` and are not presented as common dictionary words.
Candidate labels and registry evidence were not removed or changed.

`data/scoring_penalties.txt` supplies exact-label penalties of 50 points to
brandability, commercial demand, and resale for negative, bodily, medical,
pejorative, or awkward truncated labels. The additional shortlist removals
from the previous 500 were: `absorben`, `askance`, `astringen`, `biopsylab`,
`elitism`, `ferven`, `fidgety`, `floun`, `galium`, `gaseous`, `gynlab`,
`gynscan`, `hemocell`, `hemolab`, `hemoscan`, `indetermina`, `interagen`,
`intermitten`, `jittery`, `karaya`, `melena`, `naivete`, `naivety`, `pedslab`,
`piquan`, `plian`, `pungen`, `raucous`, `roguish`, `shadowy`, `stringen`,
`subtenan`, `tenuous`, `tumorlab`, `venal`, and `walkout`. The named nine
negative terms (`venal`, `melena`, `roguish`, `fidgety`, `jittery`, `naivety`,
`raucous`, `gaseous`, `elitism`) all have this penalty and none is in the final
500.

The final 500 labels were reviewed one by one. Remaining `dictionary` entries
are all common English words: `stoical`, `leaning`, `cowhide`, `powdery`,
`reveler`, `gyration`, `epaulet`, and `decorous`. Borderline dictionary keeps
are `stoical` (positive resilience), `leaning` (neutral inclination),
`cowhide` (commercial material), `powdery` (neutral product texture),
`reveler` (event/consumer), `gyration` (neutral motion/technical), `epaulet`
(niche fashion), and `decorous` (positive, uncommon). Borderline clinical keeps
include `myelinlab`, `serumlab`, `pharmascan`, `cardiolab`, `physioscan`,
`rehabscan`, `sleepscan`, `genomelab`, `nephrolab`, `nephroscan`, `retinalab`,
`retinascan`, `dosagelab`, `dosagescan`, `immunolab`, and `antigenlab`; these
describe diagnostic, research, or care products rather than a disease name or
bodily function. Exact negative, disease, bodily-fluid, pejorative, and awkward
truncated examples were penalized.

## Per-name scoring

The weights remain **brandability 25%, commercial 20%, shortness 15%, hack
creativity 15%, resale heuristic 15%, and trademark 10%**. Component scores
are integers from 0 to 100; the weighted total uses decimal arithmetic with
`ROUND_HALF_EVEN` to one decimal.

Brandability combines length (25% of that component), pronounceability (22%),
spelling clarity (15%), candidate quality (15%), letter shape (10%), vowel
balance (4%), vowel/consonant transitions (3%), distinct letters (3%), and
onset/ending clarity (3%). Reviewed phrase-hack adjustments and exact-label
quality penalties are applied within the component.

Commercial demand uses `COMMERCIAL_ROOTS` in `si_domains/scoring.py`: each
entry has a tier, relative demand score, buyer-pool breadth, and buyer summary.
These are ranking inputs, not measured traffic or sales data. Tier 1 contains
high-demand roots such as `ai`, `pay`, `cloud`, `data`, `health`, `bank`, and
`trade`; Tier 2 contains mid-demand roots such as `agent`, `credit`, `fintech`,
`news`, `robot`, and `tech`; Tier 3 contains more niche roots such as `bio`,
`carbon`, `ledger`, `pharma`, and `genome`. The complete root table and values
are reproduced row-by-row in the workbook Methodology sheet. Compounds average
the recorded head and tail demand and gain six points when both parts are
commercial roots. Unknown roots start at demand 48 and breadth 4. Label shape,
length, given-name status, and exact negative-label penalties adjust the result.
Invented/name-like labels without a commercial signal therefore start lower,
but still vary by their own shape.

The demand-root table below is the complete per-name lookup used by the score.
Demand and breadth are heuristic scales, not observed searches or buyer counts.

| Root | Tier | Demand | Buyer breadth | Buyer pool |
| --- | ---: | ---: | ---: | --- |
| ai | 1 | 96 | 24 | software and automation |
| bank | 1 | 89 | 18 | finance |
| cloud | 1 | 92 | 22 | software and hosting |
| data | 1 | 92 | 25 | cross-industry analytics |
| energy | 1 | 84 | 18 | energy |
| finance | 1 | 89 | 17 | financial services |
| health | 1 | 90 | 18 | health technology |
| insurance | 1 | 85 | 15 | insurance |
| invest | 1 | 86 | 17 | investment |
| market | 1 | 84 | 21 | commerce |
| pay | 1 | 94 | 20 | fintech and payments |
| security | 1 | 86 | 18 | security and IT |
| software | 1 | 85 | 16 | software |
| trade | 1 | 87 | 20 | commerce and trade |
| travel | 1 | 82 | 20 | travel |
| wallet | 1 | 85 | 14 | payments |
| agent | 2 | 78 | 16 | automation and services |
| auto | 2 | 78 | 16 | automotive |
| business | 2 | 77 | 16 | business services |
| care | 2 | 77 | 14 | care services |
| credit | 2 | 79 | 15 | finance |
| crypto | 2 | 78 | 13 | digital finance |
| education | 2 | 76 | 16 | education |
| fintech | 2 | 82 | 16 | financial technology |
| hotel | 2 | 73 | 13 | hospitality |
| med | 2 | 74 | 12 | medical services |
| news | 2 | 76 | 17 | media |
| office | 2 | 72 | 13 | workplace services |
| robot | 2 | 77 | 14 | robotics |
| science | 2 | 75 | 14 | science |
| tech | 2 | 77 | 17 | technology |
| bio | 3 | 66 | 11 | biotechnology |
| carbon | 3 | 64 | 11 | climate technology |
| food | 3 | 68 | 15 | food and retail |
| game | 3 | 67 | 13 | games and entertainment |
| genome | 3 | 64 | 10 | genomics |
| law | 3 | 64 | 10 | legal services |
| ledger | 3 | 68 | 12 | accounting and finance |
| legal | 3 | 66 | 11 | legal services |
| medical | 3 | 68 | 12 | medical services |
| mobile | 3 | 68 | 15 | mobile technology |
| pharma | 3 | 67 | 10 | pharmaceuticals |
| shop | 3 | 66 | 14 | retail |
| solar | 3 | 68 | 12 | solar energy |
| sport | 3 | 65 | 13 | sports |
| ticket | 3 | 65 | 13 | events and travel |
| web | 3 | 67 | 18 | internet services |

Shortness uses label length, syllable estimate, vowel/consonant shape, distinct
letters, and edge clarity. Hack creativity combines the recorded seed's
quality with label pronunciation. Resale is a heuristic from label length,
syllables, phonetic ease, root demand and buyer breadth, exact-word/commonness,
memorability shape, and hack rarity. Repeated letters and ambiguous pairs such
as `rn`, `cl`, `vv`, `ii`, `0o`, and `1l` reduce resale; given names and
reviewed low-breadth dictionary words receive specific penalties. It is not a
price estimate. The final 500 contain **356 distinct** five-component tuples
(brandability/commercial/shortness/hack/resale); the six eligible `short`
labels have distinct tuples.

## Category availability and selection cap

Eligibility means the known local rules pass, latest RDAP is HTTP 404, and
latest WHOIS is `not_registered`. Eligible rank is the global rank among all
eligible labels before the 500-row/category selection cap. The category cap is
**100 (20% of the shortlist)** to prevent one family dominating the list.
All six eligible four-letter CVCV short labels are selected; no three-letter
short label was eligible. Of 15 eligible domain hacks, the three stronger
entries rank 1–3 and are selected. The other 12 eligible hacks are awkward,
weak, or narrow-seed labels and were penalized below the cut. Short-name
availability is the constraint; hack selection is quality/scoring constrained,
not category-cap constrained.

| Category | Pool | Eligible | Final 500 | Median eligible rank | Minimum eligible rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ai | 1,500 | 991 | 100 | 2,194 | 88 |
| business_finance | 359 | 288 | 71 | 2,436.5 | 458 |
| consumer_brands | 265 | 226 | 48 | 2,546 | 460 |
| dictionary | 996 | 26 | 8 | 3,360.5 | 4 |
| domain_hacks | 135 | 15 | 3 | 3,346 | 1 |
| emerging_industries | 289 | 232 | 69 | 2,529 | 159 |
| health_science | 252 | 221 | 47 | 2,586 | 1,240 |
| invented | 1,454 | 1,247 | 100 | 657 | 5 |
| short | 700 | 6 | 6 | 31 | 13 |
| technology | 254 | 143 | 48 | 2,170 | 57 |

The workbook Methodology sheet contains the same category availability fields.
The low dictionary/short/hack pool counts reflect the fixed candidate and
registry evidence, not dropped candidate labels. All 3,395 eligible rows are
ranked; 2,895 remain visible outside the 500-row selection.

## Public trademark search attempt and limits

After the offline Parts 1–4 ranking, Round 1 targeted the top 100 exact labels
with one source probe per host. Those probes showed that per-name search was
not safely available, so the source was stopped and no mark result was
invented. The outcome was recorded for every name/source pair in
`trademark_evidence.csv`; each row explicitly distinguishes source-wide
coverage from an actual per-domain request.

| Source | Probe | HTTP outcome | Requests made | Completed per-name searches | Final top-100 outcomes |
| --- | --- | --- | ---: | ---: | --- |
| TMview | POST `https://www.tmdn.org/tmview/api/search/results` with `newsagen` | Remote connection closed before an HTTP response; not retried | 1 | 0 | 100 unverified |
| UKIPO | GET `https://trademarks.ipo.gov.uk/ipo-tmtext/page/Results?text=newsagen` | HTTP 403, Service Captcha; stopped | 1 | 0 | 100 blocked |
| USPTO | GET `https://tmsearch.uspto.gov/search/search-results?query=newsagen` | HTTP 200 JavaScript application shell; no parseable results; stopped | 1 | 0 | 100 unverified |

No browser workaround, account, paid source, login, or search-engine substitute
was used. Exact per-name queries were not sent after the source-wide outcomes.
Round 2 added coverage records for **6 new entrants** after the scoring
penalties removed awkward labels; each record carries the existing source-wide
outcome, not a new request or search result. The final top 100 had records for
all three sources and no further membership change. **Two ranking rounds** ran;
Round 3 was unnecessary. No name was flagged for legal review because no mark
data was returned. Names ranked 101–500 have no summary row, remain
`not yet screened`, and score 40.

Coverage rows with `blocked` or `unverified` never count as completed searches.
`validate-research` exits **2** because the top-100 requirements are unresolved:
TMview 0/100 complete (100 unverified), UKIPO 0/100 (100 blocked), and USPTO
0/100 (100 unverified). `validate-delivery` can still pass because it checks
the consistency of the local workbook and CSVs, not screening completion.

For any future accessible result, flag legal review for an identical word
mark, whole-word containment of or by the label, edit distance at most one for
labels of at least five characters, or an identical stem, in any class. Classes
9, 35, 36, 38, 41, and 42 have higher relevance. Anything uncertain is a legal
review case, never a no-obvious-match result. Store only distilled hit facts:
mark number, name, status, classes, and result URL. Do not bulk-copy trademark
database content. This bounded method is not comprehensive phonetic, class,
national-office, or worldwide clearance.

Trademark component values come from one mapping in
`si_domains/scoring.py`: `limited_screen_no_obvious_match` = 85; `needs legal
review` = 25; `blocked`, `unverified`, and `not yet screened` = 40. The
incomplete-screen rationale is `unverified (no clearance implied)`. The
40-point value is documented, lower than a clear screen and higher
than a conflict; weights are not renormalized. Unknown risk is penalized
relative to a clean screen, while a conflict receives the largest penalty. A
clear screen can add up to 4.5 weighted points over an unscreened name, so a
future workflow must screen replacement top-100 entrants in later rounds.
None of these scores implies clearance.

## Offline build and validation

After updating the curated evidence CSVs with actual sourced records, rebuild
in this order. The first three commands create a summary for the current top
100, inject its scores, and regenerate the shortlist. The next three refresh
the summary for the re-ranked top 100. Compare membership after each scoring
pass; if a new name enters, research it where access permits, append the result,
and repeat until the summary covers the final membership. A blocked source does
not become complete through repetition.

```powershell
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
python -m si_domains valuations --shortlist output/shortlist.csv --evidence output/valuation_evidence.csv --out output/valuations.csv
python -m si_domains opportunities --shortlist output/shortlist.csv --scores output/scores.csv --valuations output/valuations.csv --trademark-summary output/trademark_summary.csv --out output/opportunities.csv
python -m si_domains validate-research --candidates data/candidates.csv
```

Do not fill a blocked source with a synthetic completed result. Existing
per-name blocked/unverified coverage rows may record why a required query was
not completed, but they do not satisfy coverage.

The validator checks CSV schemas, duplicate IDs/domains, candidate-to-score
relationships, exact Decimal weighted totals and injected trademark scores,
shortlist score/length/domain order and caps, all copied opportunity fields,
valuation range citations, trademark summary mappings, required label/seed
queries, and query proof references. It reports source-wide access failures
separately from complete per-domain query sets and exits unsuccessfully when
required coverage remains unresolved. These structural checks cannot confirm
that a cited sale is genuinely comparable or that a mark result is legally
relevant; a reviewer must inspect the cited pages and proof files.

RDAP `potentially_unregistered` and WHOIS `not_registered` are timestamped
observations from two registry channels. They are not registrar checkout
confirmation, registration eligibility, a guarantee that registration will
succeed, or a guarantee of a non-premium price. Existing candidate, RDAP, and
WHOIS evidence was not changed by this research step.
