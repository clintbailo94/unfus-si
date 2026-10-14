# PKG-D ranked `.si` research methodology

Research snapshot: 2026-10-13 UTC. These artifacts supplement the existing
RDAP/WHOIS shortlist. They do not turn the scoring heuristic into a sale-price
valuation, trademark clearance, or registrar checkout result.

`data/owned_domains.txt` records domains bought by you and their purchase dates. The workbook and HTML mark those rows as owned; registry evidence is pre-purchase history, and ownership does not change scores or ranks.

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

The final 500 have **355 distinct** `(brandability, commercial, shortness, hack, resale)` tuples and **500 distinct rationales**. Commercial-score population standard deviation is **16.55**. Mean commercial score for AI, technology, and business/finance rows combined is **59.64** versus **42.48** for invented rows (difference **17.16**); invented resale mean is **59.17**, with each rootless invented/name-like score capped at 65.

### Mean commercial and resale scores by final category

| Category | Rows | Mean commercial | Mean resale |
| --- | ---: | ---: | ---: |
| ai | 100 | 58.97 | 63.85 |
| business_finance | 52 | 56.52 | 62.33 |
| consumer_brands | 90 | 42.92 | 56.82 |
| dictionary | 8 | 38.25 | 77.25 |
| domain_hacks | 3 | 59.00 | 94.33 |
| emerging_industries | 49 | 52.06 | 62.27 |
| health_science | 59 | 45.85 | 56.25 |
| invented | 100 | 42.48 | 59.17 |
| short | 6 | 46.83 | 94.50 |
| technology | 33 | 66.61 | 64.42 |

## Category availability and selection rules

Eligibility means the known local rules pass, latest RDAP is HTTP 404, and latest WHOIS is `not_registered`. Eligible rank is the global order before category and family selection limits. The final 500 category limit is **100 (20%)**. The top-100 limit is **35 per category**, preventing one category from dominating the highest-ranked band. Family caps are a selection rule: at most 6 invented/given-name labels share a final-three-letter ending, at most 6 share a first-four-letter prefix, and at most 10 compound/blend names share a head or tail. Eligible overflow stays visible in All candidates with reason `family cap`; it is never deleted from the pool. The latest selection has **1,353 family-cap exclusions**.

| Category | Pool | Eligible | Final 500 | Median eligible rank | Minimum eligible rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ai | 1,500 | 991 | 100 | 2362 | 6 |
| business_finance | 359 | 288 | 52 | 1946.5 | 4 |
| consumer_brands | 265 | 226 | 90 | 2361.5 | 66 |
| dictionary | 996 | 26 | 8 | 3356.5 | 59 |
| domain_hacks | 135 | 15 | 3 | 3351 | 1 |
| emerging_industries | 289 | 232 | 49 | 2238.5 | 30 |
| health_science | 252 | 221 | 59 | 2541 | 94 |
| invented | 1,454 | 1,247 | 100 | 1403 | 517 |
| short | 700 | 6 | 6 | 17 | 14 |
| technology | 254 | 143 | 33 | 1068 | 5 |

Top-100 categories: ai 35; business_finance 13; consumer_brands 8; dictionary 5; domain_hacks 3; emerging_industries 13; health_science 2; short 6; technology 15. There are **100/100 non-invented keyword, real-word, short, or hack names**; largest category count is 35, at the 35 cap. The six CVCV short names rank 14 fuve.si, 15 guve.si, 16 puve.si, 18 kuzo.si, 19 guza.si, 28 cizo.si. The three hacks rank 1 newsagen.si, 2 unfus.si, 3 tryto.si. Strongest root-bearing compounds include 4 cashops.si (cash), 5 paymentops.si (pay), 6 datafleet.si (data), 7 ledgerhub.si (ledger), 8 payablehub.si (pay), 9 datalearn.si (data), 10 payabledesk.si (pay), 11 payableflow.si (pay), 12 datasolve.si (data), 13 walletlab.si (wallet), 17 chatledger.si (ledger), 20 dataledger.si (data/ledger). The 700-label short category has only 6 eligible rows and all six rank in the final 500, so short availability is the binding limit. Fifteen hacks are eligible; three are selected based on hack/label quality rather than the category cap.

## Public trademark screen and limits

PKG-G continued the T-17 screen on 2026-10-14 after the six-hour cooldown. Its `google` control returned HTTP 200 JSON with 194 hits, followed by 116 sequential candidate-query POSTs at a minimum five-second interval. All 117 requests returned HTTP 200 JSON. The T-18 rework added one `google` control and five candidate queries, sequentially at least five seconds apart. Across both passes, 123 USPTO POSTs (two controls and 121 candidate queries) returned HTTP 200 JSON; there was no new HTTP 403, CAPTCHA, login, non-JSON response, timeout, 5xx, or retry. The earlier T-17 HTTP 403 on `bankingdesk` remains in the evidence history at `REWORK1-USPTO-00259` and `REWORK1-USPTO-SOURCE-STOP`. PKGH then added one google control and exact/fuzzy-1 queries for profitdesk.si on 2026-10-14; all three returned HTTP 200 JSON, the two candidate queries returned zero matches, and request starts were at least five seconds apart.

The 44 previously blocked top-100 labels received exact and near queries. An earlier HTTP 200 response for `powdery [fuzzy-1]` could not be retained because the ASCII writer rejected a non-ASCII mark. `si_domains.uspto` now normalizes distilled text fields to ASCII before evidence writing, retaining diacritics in readable form where possible and escaping other code points. The rework re-queried that label and recorded 10 similar marks from 10 returned results (`RESUME-USPTO-00269` through `RESUME-USPTO-00278`; 2,097 total hits). The `denimwear` exact and fuzzy-1 queries each returned two similar marks (`RESUME-USPTO-00279` through `RESUME-USPTO-00282`). Because `denimwear` left the top 100, `soillab` was screened as the replacement while USPTO remained live: exact returned zero hits; fuzzy-1 returned 10 similar marks from 10 results, 12 total hits (`RESUME-USPTO-00283` through `RESUME-USPTO-00293`). The T-18 control row is `RESUME-USPTO-00268`. Similarity review covers all classes, with classes 9, 35, 36, 38, 41, and 42 noted as higher relevance. No name is legally cleared.

Three PKG-G entrant rounds added 9, 4, and 1 names. The T-18 rework used one further round for `soillab`; the updated ranking then settled within the two-round limit. TMview and UKIPO received no requests. TMview source-wide refused: connection closed (evidence `REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified because of that refusal. UKIPO source-wide refused: automated access refused (evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked because of that refusal. Their per-name `soillab` rows cite those existing refusal records. Profitdesk.si is the sole outside-top-100 USPTO screen, requested by the owner; the other names outside the top 100 remain not yet screened by USPTO (`RESUME-TMVIEW-00031`/`00032`, `RESUME-UKIPO-00031`/`00032`). Except for profitdesk.si, screened at the owner's request, names ranked 101-500 remain not yet screened by USPTO.

Relative to the pre-rework PKG-G top 100, `soillab` entered and `denimwear` exited. Relative to T-17, final top-100 membership changed by seven entries and seven exits.

| Entered | Exited |
| --- | --- |
| `examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `biomasshub`, `roboticflow`, `biomasslab` | `robotsystem`, `gyration`, `crophub`, `croplab`, `agrihub`, `cryptoworks`, `parcelshop` |

| Source | Final top-100 coverage | PKG-G and T-18 rework outcomes |
| --- | --- | --- |
| TMview | 0/100 complete; 0 query-blocked; 100 unverified | No request. TMview source-wide refused: connection closed (evidence `REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified because of that refusal. |
| UKIPO | 0/100 complete; 100 query-blocked; 0 unverified | No request. UKIPO source-wide refused: automated access refused (evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked because of that refusal. |
| USPTO | 100/100 complete; 0 query-blocked; 0 unverified | 2 `google` controls plus 121 candidate requests; 123 HTTP 200 JSON total; no new 403 or retry. |

USPTO's earlier source-stop remains in the evidence history: one HTTP 403 on the `bankingdesk` near query at 2026-10-13T18:05:11Z (`REWORK1-USPTO-00259`; source-stop row `REWORK1-USPTO-SOURCE-STOP`). The T-17 history also includes the earlier UI-shell GET and 139 JSON POSTs; PKG-G does not overwrite those records.

The similarity rule flags identical word marks, whole-word containment, edit distance <=1, or an identical stem in any class. Classes 9, 35, 36, 38, 41, and 42 are higher relevance; live and dead marks both trigger review. Uncertain results are never treated as clear. Thirty-seven final-top-100 names need legal review, up from 24. Thirteen newly flagged names are `autokernel`, `autonetwork`, `autostream`, `carboncell`, `cashops`, `jewelshop`, `keyscan`, `pharmascan`, `powdery`, `reveler`, `robotspark`, `soilhub`, and `soillab`. The full current list is `autobeacon`, `autokernel`, `autonetwork`, `autosearch`, `autostream`, `autoswitch`, `bankinghub`, `carboncell`, `carbonhub`, `cashledger`, `cashops`, `cizo`, `cowhide`, `creditdesk`, `datafleet`, `datalearn`, `dataledger`, `datasolve`, `dataswitch`, `jewelshop`, `keyscan`, `leaning`, `ledgerlink`, `loanledger`, `newsagen`, `paymentops`, `pharmascan`, `powdery`, `reveler`, `robotloop`, `robotspark`, `soilhub`, `soillab`, `stoical`, `tryto`, `unfus`, and `walletlink`. `denimwear` also has possible-conflict evidence but is outside the final top 100.

Trademark component values use one mapping in `si_domains/scoring.py` and `si_domains/trademarks.py`: all three sources complete with no obvious match = 85; any possible conflict = 25; incomplete, blocked, unverified, or not yet screened = 40. The 40 score is below clear and above conflict, without weight renormalization. These limited queries imply no clearance.

`validate-research` in strict mode exits **2** because coverage remains incomplete: TMview 0 complete / 0 query-blocked / 100 unverified; UKIPO 0 complete / 100 query-blocked / 0 unverified; USPTO 100 complete / 0 query-blocked / 0 unverified. `validate-delivery` is a separate structural check and can pass while research remains blocked. Screening is not comprehensive phonetic, class, national-office, or worldwide clearance.

### Manual trademark checks the owner can do

Official search pages: [TMview](https://www.tmdn.org/tmview/), [UKIPO](https://trademarks.ipo.gov.uk/ipo-tmtext), and [USPTO](https://tmsearch.uspto.gov/). TMview source-wide refused: connection closed (evidence `REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified because of that refusal. UKIPO source-wide refused: automated access refused (evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked because of that refusal. No further TMview or UKIPO requests were made. USPTO's earlier HTTP 403 remains in history at `REWORK1-USPTO-00259` / `REWORK1-USPTO-SOURCE-STOP`; PKG-G and the T-18 rework made 123 POSTs, all HTTP 200 JSON, with no new 403 or retry. USPTO coverage is 100/100 complete. PKGH screened profitdesk.si at the owner's request; it is the only outside-top-100 USPTO screen, and all other outside-top-100 names remain not yet screened by USPTO. No result is a trademark clearance.

`validate-research --completion-mode` checks that every top-100 name/source pair has a completed exact and near query, or dated blocked/unverified records with an official source URL and an evidence-backed reason. Accepted incomplete reasons include an HTTP refusal, CAPTCHA, connection closure, cited source-stop row, a local evidence-write failure after a response, or the documented three-round screening limit. Missing pairs fail. It checks record completeness and score/status consistency without network requests; strict mode still exits 2 while searches remain incomplete.

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
