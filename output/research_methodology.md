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

The pool remains **6,204 unique labels**. `data/given_names.txt` is a curated exact-label list grounded in the reviewed proper-name candidates in `data/invented_real_words.txt` and the false-dictionary audit. The 21 audited labels are brena, genal, neral, belal, celal, delal, belami, belona, belova, delina, dorina, genaro, lorina, merina, belara, calami, dorino, elette, karena, larena, marena; they and other curated names carry `given_name` and move to category `invented`. No suffix-only regex is used: endings such as `-ina`, `-ena`, `-ora`, `-aro`, `-ino`, and `-ali` are not sufficient evidence. The source candidate rows and final RDAP/WHOIS evidence remain intact.

`data/scoring_penalties.txt` applies an exact-label 50-point penalty inside brandability, commercial, resale, and hack scoring. The named negative terms `venal`, `melena`, `roguish`, `fidgety`, `jittery`, `naivety`, `raucous`, `gaseous`, and `elitism` are all absent from the final 500. After reviewing the final list, five additional labels were added to the penalty file: `bloodmonitor`, `bloodtrack`, `gynclinic`, `hemoclinic`, and `tumormarker`. The awkward hack forms `floun` and `plian` also remain below the cut because the exact penalty now applies to the hack component. These labels remain in the full candidate pool and score artifact; they were not silently removed.
The complete exact-penalty inventory has 52 labels, all retained in the pool and absent from the final 500: `absorben`, `askance`, `astringen`, `belated`, `biopsylab`, `biopsyscan`, `biopsytrack`, `bloodassay`, `bloodmarker`, `bloodmonitor`, `bloodpulse`, `bloodscan`, `bloodtrack`, `elitism`, `ferven`, `fidgety`, `floun`, `gaseous`, `galium`, `gynclinic`, `gynlab`, `gynscan`, `hemocell`, `hemoclinic`, `hemolab`, `hemoscan`, `indetermina`, `interagen`, `intermitten`, `jittery`, `jugular`, `karaya`, `melena`, `naivete`, `naivety`, `orifice`, `pedslab`, `piquan`, `plian`, `pungen`, `raucous`, `roguish`, `shadowy`, `stringen`, `subtenan`, `tenuous`, `tumorlab`, `tumormarker`, `tumorscan`, `venal`, `walkout`, and `wizened`.

The eight remaining `dictionary` rows are genuine English common words: `stoical` (calm under hardship); `powdery` (fine and dry); `leaning` (inclination); `cowhide` (leather material); `reveler` (event participant); `gyration` (circular motion); `epaulet` (ornamental shoulder piece); `decorous` (proper and restrained). Their meanings are neutral or positive, and narrow words receive a resale penalty. The final 500 also contain these borderline clinical/science product labels: `pharmascan`, `genomelab`, `pharmatrial`, `gerilab`, `genomescan`, `biopsyscope`, `geriscan`, `biopsyassay`, `genomeatlas`, `serumcell`, `physioscan`, `rehabscan`, `pharmaworks`, `helixscan`, `helixcell`, `geneworks`, `genomescope`, `dermascope`, `myelincell`, `sleepatlas`, `plasmacell`, `genomeworks`, `biopsyscreen`, `serumtrial`, `neuroscope`, `cardiopulse`, `biotechworks`, `immunocell`, `stromacell`, `sleeptrack`, `plasmatrial`, `helixassay`, `serumassay`, `genemarker`, `helixatlas`, `rehabtrack`, `neuronatlas`, `helixmarker`, `myelinatlas`, `helixscope`, `serumscope`, `plasmascope`, `retinascope`, `serummarker`, `enzymescope`, `plasmaassay`, `myelinscope`, `biomarkeratlas`, `stromaassay`, `sleepmonitor`, `enzymeassay`, `dermaclinic`, `proteinatlas`, `gericlinic`, `synapsetrial`, `biomarkerassay`, `myelinmarker`, `proteinassay`, `plasmamarker`. These are diagnostic, laboratory, research, monitoring, or care-product descriptions rather than disease names, bodily fluids as standalone labels, insults, or adverse symptoms. The exact negative and awkward terms are penalized.

## Per-name scoring

Weights remain **brandability 25%, commercial 20%, shortness 15%, hack creativity 15%, resale heuristic 15%, trademark 10%**. Component scores are integers from 0 to 100; the weighted total uses decimal `ROUND_HALF_EVEN` to one decimal.

Brandability combines length (25% of its component), pronunciation (22%), spelling (15%), candidate quality (15%), letter shape (10%), vowel balance (4%), transition balance (3%), distinct letters (3%), and onset/ending clarity (3%). A rootless invented/name-like label has a brandability ceiling of 65, so good phonetics alone do not outweigh a concise commercial root.

Commercial demand uses the reviewed `COMMERCIAL_ROOTS` table in `si_domains/scoring.py`. Tier 1 roots map into 85-100, Tier 2 into 65-85, Tier 3 into 45-65. Without an industry root, a pseudo-name/name-like label is 30-50; a common dictionary word with no industry meaning is 25-45. The unknown-root baseline is modest and label shape, quality, length, phonetic ease, and given-name status vary the result. For a compound, score the strongest listed head/tail root at 88% and the second root at 12%, then add 4 when both are listed commercial roots. Exact roots and buyer breadth are heuristic demand signals, not observed traffic or sales.

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
| ledger | 1 | 85 | 16 | accounting and financial technology |
| market | 1 | 84 | 21 | commerce |
| pay | 1 | 94 | 20 | fintech and payments |
| secure | 1 | 85 | 18 | security and trust |
| security | 1 | 86 | 18 | security and IT |
| software | 1 | 85 | 16 | software |
| trade | 1 | 87 | 20 | commerce and trade |
| travel | 1 | 82 | 20 | travel |
| wallet | 1 | 85 | 14 | payments |
| agent | 2 | 78 | 16 | automation and services |
| auto | 2 | 78 | 16 | automotive |
| business | 2 | 77 | 16 | business services |
| care | 2 | 77 | 14 | care services |
| cash | 2 | 82 | 18 | payments and finance |
| credit | 2 | 79 | 15 | finance |
| crypto | 2 | 78 | 13 | digital finance |
| education | 2 | 76 | 16 | education |
| fintech | 2 | 82 | 16 | financial technology |
| hotel | 2 | 73 | 13 | hospitality |
| med | 2 | 74 | 12 | medical services |
| news | 2 | 76 | 17 | media |
| office | 2 | 72 | 13 | workplace services |
| payload | 2 | 78 | 17 | software data transfer |
| robot | 2 | 77 | 14 | robotics |
| science | 2 | 75 | 14 | science |
| tech | 2 | 77 | 17 | technology |
| bio | 3 | 66 | 11 | biotechnology |
| carbon | 3 | 64 | 11 | climate technology |
| food | 3 | 68 | 15 | food and retail |
| game | 3 | 67 | 13 | games and entertainment |
| genome | 3 | 64 | 10 | genomics |
| law | 3 | 64 | 10 | legal services |
| legal | 3 | 66 | 11 | legal services |
| medical | 3 | 68 | 12 | medical services |
| mobile | 3 | 68 | 15 | mobile technology |
| pharma | 3 | 67 | 10 | pharmaceuticals |
| shop | 3 | 66 | 14 | retail |
| solar | 3 | 68 | 12 | solar energy |
| sport | 3 | 65 | 13 | sports |
| ticket | 3 | 65 | 13 | events and travel |
| web | 3 | 67 | 18 | internet services |

Resale uses per-name length, syllables, phonetic ease, vowel/consonant shape, distinct-letter count, edge clarity, exact-word/commonness, root demand and breadth, buyer-pool breadth, memorability, hack rarity, repeated letters, and ambiguous pairs. Rootless invented/name-like labels cap at 65; this prevents unproven pseudo-names from receiving resale confidence purely for pronunciation. Strong-root compounds and broad-buyer real words can score above 65. Narrow dictionary words, given names, hyphen-like/ambiguous pairs, and repeated letters are penalized. This heuristic is not a price estimate.

Shortness reflects length, syllables, pronunciation/shape, letter variety, and edge clarity. Hack creativity reflects the recorded completion seed and how naturally the `.si` label completes it. All six eligible CVCV short names are selected; the three strongest hacks rank 1-3. Each rationale is ASCII, <=140 characters, and identifies a concrete domain-specific fact: matched root and buyer pool, compound head/tail, common-word sense, hack completion, or label pattern/letter shape.

The final 500 have **358 distinct** `(brandability, commercial, shortness, hack, resale)` tuples and **500 distinct rationales**. Commercial-score population standard deviation is **16.57**. Mean commercial score for AI, technology, and business/finance rows combined is **60.02** versus **42.48** for invented rows (difference **17.54**); invented resale mean is **59.17**, with each rootless invented/name-like score capped at 65.

### Mean commercial and resale scores by final category

| Category | Rows | Mean commercial | Mean resale |
| --- | ---: | ---: | ---: |
| ai | 100 | 59.29 | 64.19 |
| business_finance | 51 | 56.82 | 62.31 |
| consumer_brands | 90 | 42.91 | 56.69 |
| dictionary | 8 | 38.25 | 77.25 |
| domain_hacks | 3 | 59.00 | 94.33 |
| emerging_industries | 51 | 51.16 | 62.16 |
| health_science | 59 | 45.83 | 56.25 |
| invented | 100 | 42.48 | 59.17 |
| short | 6 | 46.83 | 94.50 |
| technology | 32 | 67.38 | 64.09 |

## Category availability and selection rules

Eligibility means the known local rules pass, latest RDAP is HTTP 404, and latest WHOIS is `not_registered`. Eligible rank is the global order before category and family selection limits. The final 500 category limit is **100 (20%)**. The top-100 limit is **35 per category**, preventing one category from dominating the highest-ranked band. Family caps are a selection rule: at most 6 invented/given-name labels share a final-three-letter ending, at most 6 share a first-four-letter prefix, and at most 10 compound/blend names share a head or tail. Eligible overflow stays visible in All candidates with reason `family cap`; it is never deleted from the pool. The latest selection has **1,364 family-cap exclusions**.

| Category | Pool | Eligible | Final 500 | Median eligible rank | Minimum eligible rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ai | 1,500 | 991 | 100 | 2362 | 6 |
| business_finance | 359 | 288 | 51 | 1946.5 | 4 |
| consumer_brands | 265 | 226 | 90 | 2361.5 | 66 |
| dictionary | 996 | 26 | 8 | 3356.5 | 59 |
| domain_hacks | 135 | 15 | 3 | 3351 | 1 |
| emerging_industries | 289 | 232 | 51 | 2238.5 | 30 |
| health_science | 252 | 221 | 59 | 2541 | 94 |
| invented | 1,454 | 1,247 | 100 | 1403 | 517 |
| short | 700 | 6 | 6 | 17 | 14 |
| technology | 254 | 143 | 32 | 1068 | 5 |

Top-100 categories: ai 33; business_finance 12; consumer_brands 8; dictionary 6; domain_hacks 3; emerging_industries 14; health_science 2; short 6; technology 16. There are **100/100 non-invented keyword, real-word, short, or hack names**; largest category count is 33, below the 35 cap. The six CVCV short names rank 14 fuve.si, 15 guve.si, 16 puve.si, 18 kuzo.si, 19 guza.si, 28 cizo.si. The three hacks rank 1 newsagen.si, 2 unfus.si, 3 tryto.si. Strongest root-bearing compounds include 4 cashops.si (cash), 5 paymentops.si (pay), 6 datafleet.si (data), 7 ledgerhub.si (ledger), 8 payablehub.si (pay), 9 datalearn.si (data), 10 payabledesk.si (pay), 11 payableflow.si (pay), 12 datasolve.si (data), 13 walletlab.si (wallet), 17 chatledger.si (ledger), 20 dataledger.si (data/ledger). The 700-label short category has only 6 eligible rows and all six rank in the final 500, so short availability is the binding limit. Fifteen hacks are eligible; three are selected based on hack/label quality rather than the category cap.

## Public trademark screen and limits

The final top 100 were processed in three ranking rounds: Round 1 covered 100 labels, Round 2 added 3 entrants, and Round 3 added 9. After each round, available results were applied before looking for new top-100 entrants. The final top 100 has a per-source query outcome record; names that exited the top 100 retain their evidence. No query was sent to a stopped source after its access refusal.

USPTO's public JSON API was used at `https://tmsearch.uspto.gov/prod-stage-v1-0-0/tmsearch` with an honest project User-Agent and one-second pacing. Two controls were recorded: exact `google` returned HTTP 200 JSON with 194 total hits, and `qzxwvk` returned HTTP 200 JSON with zero hits. Candidate screening made 134 requests (133 HTTP 200 JSON, one HTTP 403 during the `bankingdesk` near query); the source stopped after that 403. The 66 remaining query slots were recorded blocked without requests. Including three initial API/field-shape probes and the two controls, **139 JSON POSTs** were made. One earlier UI-shell GET returned HTTP 200 JavaScript HTML without parseable search results, making 140 USPTO requests across the task. There were no retries after the refusal. Exact phrase was followed by one fuzzy query (fuzziness 1 for labels at least five characters; whole-word mode for shorter labels). Only distilled serial number, wordmark, live/dead flag, status, classes, and result URL were retained. Owner and attorney fields were not copied.

TMview's earlier single POST probe plus three new official-endpoint probe shapes (two POST forms and one GET) all closed before an HTTP response; the official UI shell itself was readable but yielded no search data. The exact three new probes and outcomes are recorded in `trademark_evidence.csv`: `/tmview/api/search/results` POST, the same endpoint with `translate=true` and query parameters, and GET on the same query URL. The source then stopped. UKIPO's one recorded search-page GET returned HTTP 403 Service Captcha and was stopped. No CAPTCHA, login, bot wall, proxy, or alternate identity was used.

| Source | Final top-100 coverage | Per-source outcome counts |
| --- | --- | --- |
| TMview | 0/100 complete | 0 query-blocked | 100 unverified/missing |
| UKIPO | 0/100 complete | 100 query-blocked | 0 unverified/missing |
| USPTO | 56/100 complete | 44 query-blocked | 0 unverified/missing |

The similarity rule flags an identical word mark, whole-word containment of or by the label, a near match with edit distance <=1 for labels of at least five characters, or an identical stem in any class. Classes 9, 35, 36, 38, 41, and 42 are noted as higher relevance. Live and dead marks both trigger review. Any uncertain match is `possible_conflict`, never clear. **24 names** have a USPTO possible conflict and are `needs legal review` at score 25: `newsagen`, `unfus`, `tryto`, `paymentops`, `datafleet`, `datalearn`, `datasolve`, `dataledger`, `loanledger`, `cashledger`, `robotloop`, `cizo`, `ledgerlink`, `walletlink`, `bankinghub`, `stoical`, `dataswitch`, `creditdesk`, `leaning`, `carbonhub`, `autoswitch`, `autobeacon`, `autosearch`, `cowhide`. A conflict in any source takes precedence over other incomplete sources.

Trademark component values use one mapping in `si_domains/scoring.py` and `si_domains/trademarks.py`: all three sources complete with no obvious match = 85; any possible conflict = 25; incomplete, blocked, unverified, or not yet screened = 40. The 40 score is explicitly below clear and above conflict, without weight renormalization: unknown risk is penalized relative to a clean screen, and a conflict is penalized most. A screened-clear name could gain up to 4.5 weighted points over an unscreened name, so new top-100 entrants are checked in subsequent rounds. None of these scores is legal clearance.

`validate-research` in strict mode exits **2** on this snapshot. Source counts are: TMview: 0 complete, 0 query-blocked, 100 unverified/missing; UKIPO: 0 complete, 100 query-blocked, 0 unverified/missing; USPTO: 56 complete, 44 query-blocked, 0 unverified/missing. TMview and UKIPO are incomplete; USPTO is also partial. `validate-delivery` is a separate structural check and can pass while research remains blocked. This is not comprehensive phonetic, class, national-office, or worldwide clearance.

### Manual trademark checks the owner can do

Official search pages: [TMview](https://www.tmdn.org/tmview/),
[UKIPO](https://trademarks.ipo.gov.uk/ipo-tmtext), and
[USPTO](https://tmsearch.uspto.gov/). TMview automated access is documented as
unavailable after its probes closed before an HTTP response at
2026-10-13T18:02:42Z (`REWORK1-TMVIEW-PROBES`; earlier `PKGD-0002` at
2026-10-13T17:09:22Z). UKIPO returned HTTP 403 Service Captcha at
2026-10-13T17:09:52Z (`PKGD-0003`). No further TMview or UKIPO attempts were
made. USPTO screening stopped after one HTTP 403 at 2026-10-13T18:05:11Z
(`REWORK1-USPTO-00259`; source-stop record `REWORK1-USPTO-SOURCE-STOP`). No
USPTO resume was attempted here; a later cooled-down pass belongs to the
separate PKG-G package. No result is a clearance.

`validate-research --completion-mode` runs the same structural checks and then
requires every top-100 name/source pair to have a recorded outcome. A pair
must have completed exact and near searches, or dated blocked/unverified
records with an official source URL and a note naming the refusal (HTTP status,
CAPTCHA, connection closed, or a source-stop evidence ID). Missing pairs fail.
Only three completed no-match sources may score 85; any possible conflict
must score 25; incomplete or refused sources score 40 unless a conflict takes
precedence. Every top-100 opportunity must have a trademark status other than
`not yet screened`. The command prints per-source completed, refused-by-reason,
and missing counts plus the needs-legal-review total. It makes no network
requests and does not change strict mode, which still exits 2 until required
query sets are complete.

## Offline rebuild and validation

All rebuild commands below use the checked-in candidate, RDAP, WHOIS, valuation, and trademark-evidence files; they do not contact registries or trademark sources. If top-100 membership changes, first aggregate the recorded evidence, apply scores, and regenerate selection. Screen new entrants only where the public source remains accessible and within the three-round limit. Never invent a completed result from a refusal.

```powershell
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --input data/candidates.csv --rdap-evidence output/rdap_evidence.csv --out output/scores.csv --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist --input data/candidates.csv --rdap-evidence output/rdap_evidence.csv --whois-evidence output/whois_evidence.csv --scores output/scores.csv --out output/shortlist.csv --excluded output/excluded.csv --sample-out output/sample_404_for_review.csv --seed 20261013
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --input data/candidates.csv --rdap-evidence output/rdap_evidence.csv --out output/scores.csv --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist --input data/candidates.csv --rdap-evidence output/rdap_evidence.csv --whois-evidence output/whois_evidence.csv --scores output/scores.csv --out output/shortlist.csv --excluded output/excluded.csv --sample-out output/sample_404_for_review.csv --seed 20261013
python -m si_domains valuations --shortlist output/shortlist.csv --evidence output/valuation_evidence.csv --out output/valuations.csv
python -m si_domains opportunities --shortlist output/shortlist.csv --scores output/scores.csv --valuations output/valuations.csv --trademark-summary output/trademark_summary.csv --out output/opportunities.csv
python -m si_domains export --out output/si_domains_ranked.xlsx
python -m si_domains validate-delivery --workbook output/si_domains_ranked.xlsx --candidates data/candidates.csv
python -m si_domains validate-research --candidates data/candidates.csv
python -m si_domains validate-research --candidates data/candidates.csv --completion-mode
```

The strict research validator requires a real exact and near-query result per required source for each final top-100 label; blocked and unverified rows never complete coverage. Completion mode checks outcome-record presence and the consistency of statuses and scores; it does not count refusals as searches or establish trademark clearance. Structural delivery checks compare workbook cells and evidence joins with current CSV snapshots. They do not establish comparable-sale validity, registrar pricing, or successful registration. The score and rationale are ranking heuristics only.
