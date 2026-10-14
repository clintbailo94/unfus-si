# Ranked `.si` workbook delivery

## Snapshot and meaning

Open [si_domains_ranked.xlsx](si_domains_ranked.xlsx) for the ranked workbook. It is a reproducible offline export of the timestamped CSV evidence in this repository. Its **6,204 unique candidates** were checked through the recorded registry channels; **500** names are joined into the ranked opportunity sheet.

`data/owned_domains.txt` records domains bought by you and their purchase dates. The workbook and HTML mark those rows as owned; registry evidence is pre-purchase history, and ownership does not change scores or ranks.

The RDAP/WHOIS snapshot date is **2026-10-13 UTC**; trademark evidence was refreshed on **2026-10-14 UTC**. RDAP history has 6,219 rows timestamped from `2026-10-13T01:11:41Z` through `2026-10-13T05:02:17Z`; the latest-row view covers 6,204 candidates, with 2,803 `registered` and 3,401 `potentially_unregistered`. WHOIS history has 3,401 rows from `2026-10-13T05:12:13Z` through `2026-10-13T10:11:47Z`; latest results are 3,395 `not_registered` and six `registered` conflicts. These are dated registry-channel observations, not a registrar checkout guarantee or assurance that registration will succeed.

Candidate counts by category are: AI 1,500; invented 1,454; dictionary 996; short 700; business and finance 359; emerging industries 289; consumer brands 265; technology 254; health and science 252; domain hacks 135. The pipeline scored 3,401 RDAP-404 rows, excluded 2,809 registered/conflict rows, selected 500 opportunities, and left 2,895 otherwise eligible rows outside the 500-name selection. The review sample contains 30 rows and uses seed 20261013.

The six WHOIS conflicts are **embedengine.si, geve.si, identityhub.si, lanova.si, shallwe.si, and swarmpilot.si**. Each remains excluded and labelled as a conflict in `All candidates`; none is in `Shortlist`.

The score weights remain brandability 25%, commercial demand 20%, shortness 15%, hack creativity 15%, resale heuristic 15%, and trademark 10%. Final data has 355 distinct five-component tuples and 500 distinct rationales. Commercial-score standard deviation is 16.55; mean commercial score for AI/technology/business-finance rows is 59.64 versus 42.48 for invented rows. Rootless invented/name-like resale scores cap at 65. Higher trademark scores indicate lower estimated risk. Ties sort by total descending, label length ascending, then case-folded domain.
Per-category mean commercial and resale components are listed in the [research methodology](research_methodology.md).

The final 500 category limit is **100 per category (20%)**. Selection also limits any top-100 category to 35 names, six invented/given-name labels per final-three-letter ending and per first-four-letter prefix, and ten compound/blend labels per head or tail. There are 1,353 eligible labels marked `family cap`; they stay eligible and visible in `All candidates`.

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

Top-100 category counts: ai: 35; business_finance: 13; consumer_brands: 8; dictionary: 5; domain_hacks: 3; emerging_industries: 13; health_science: 2; short: 6; technology: 15. The largest category contributes 35/100 and there are 100/100 non-invented keyword, common-word, short, or hack names. All six eligible four-letter CVCV shorts are selected at ranks 14 fuve.si, 15 guve.si, 16 puve.si, 18 kuzo.si, 19 guza.si, 28 cizo.si; no three-letter short name was registry-eligible. The three selected hacks rank 1 newsagen.si, 2 unfus.si, 3 tryto.si; 15 hacks were eligible, so hack availability exceeds selection and quality/scoring determines the selected three. Strongest root-bearing compounds include ranks 4 cashops.si, 5 paymentops.si, 6 datafleet.si, 7 ledgerhub.si, 8 payablehub.si, 9 datalearn.si, 10 payabledesk.si, 11 payableflow.si, 12 datasolve.si, 13 walletlab.si, 17 chatledger.si, 20 dataledger.si. Methodology and root-level values are in [research methodology](research_methodology.md).

The 21 audited false-dictionary labels in `data/given_names.txt` (including brena, genal, neral, belal, celal, delal, belami, belona, belova, delina, dorina, genaro, lorina, merina, belara, calami, dorino, elette, karena, larena, and marena) are category `invented` with `given_name`; the candidate pool is unchanged. The final dictionary labels are stoical, powdery, leaning, cowhide, reveler, gyration, epaulet, and decorous. Five additional exact penalties were added after label review: bloodmonitor, bloodtrack, gynclinic, hemoclinic, and tumormarker. `floun` and `plian` are also below the cut after applying the exact penalty to hack scoring. Full dictionary meanings, clinical borderline keeps, and the existing removed-label history are in the methodology.

## Workbook sheets

- **Shortlist** -- the final 500 joined opportunity records in rank order. It retains every `opportunities.csv` field, numeric rank and scores, exact source timestamps, full rationales, valuation/trademark statuses and evidence IDs, plus current RDAP HTTP/classification and WHOIS classification. Unsupported low/high price cells are blank.
- **All candidates** -- all 6,204 candidate rows and their original metadata, latest RDAP and WHOIS evidence, rule/source, score components where scored, shortlist rank, registry status and exclusion reason. Latest means the last appended evidence row for a domain. Registered, missing, unchecked, unverified and WHOIS conflict states remain distinct.
- **Unverified** -- candidates with missing/unverified latest RDAP or a missing/unverified required WHOIS second check. This snapshot has zero rows; the sheet keeps its headers and the Methodology sheet explains why. Trademark uncertainty is reported separately.
- **Special classes** -- documented alias for `Reserved/Restricted/Invalid/Premium`. Excel forbids `/` in sheet names and limits names to 31 characters. Rows are normalized as `candidate` or `rule_reference`, so the reserved/restricted inventory cannot be mistaken for queried candidates. No invalid or premium candidate example is invented. An empty premium-name inventory does not establish ordinary registrar pricing.
- **Methodology** -- counts, timestamp ranges, ranking and eligibility rules, weights, per-source trademark coverage, limitations, source paths and byte-level SHA-256 hashes.
- **Scores** -- all 3,401 score records.
- **RDAP evidence** and **WHOIS evidence** -- every source CSV row, including append-only history.
- **Valuation evidence** and **Trademark evidence** -- every curated record.

## Source-file map

| File | Role in this delivery |
| --- | --- |
| `data/candidates.csv` | Candidate labels, category membership, and scoring/query metadata. |
| `data/given_names.txt`, `data/reclassify_invented.txt` | Curated exact-name and technical-term reclassification inputs; labels stay in the candidate pool. |
| `data/scoring_penalties.txt` | Exact-label penalties for reviewed negative, medical, pejorative, bodily, and awkward terms. |
| `data/reserved_names.csv`, `data/restricted_names.csv` | Evidence-backed rule inventories used by the special-class sheet. |
| `output/rdap_evidence.csv` | Append-only registry RDAP history; current state uses the last row per domain. |
| `output/whois_evidence.csv` | Append-only WHOIS second-check history; current state uses the last row per domain. |
| `output/scores.csv` | Numeric heuristic components and totals for RDAP-404 candidates. |
| `output/shortlist.csv`, `output/excluded.csv` | Ranked eligible rows and currently ineligible rows; eligible rows outside the cap remain visible in `All candidates`. |
| `output/opportunities.csv` | Joined shortlist, valuation, and trademark fields used by the workbook. |
| `output/valuations.csv`, `output/valuation_evidence.csv` | Per-opportunity valuation state and the distinct sale, asking-price, and unsupported records. |
| `output/trademark_summary.csv`, `output/trademark_evidence.csv` | Per-domain coverage state and the source-wide/domain-query evidence records. |
| `si_domains/uspto.py` | Bounded public USPTO JSON query builder and distilled mark parser; network use was limited to the recorded screen. |
| `output/sample_404_for_review.csv` | The deterministic 30-row review sample counted in Methodology. |
| `output/research_methodology.md`, `output/valuation_sources_notes.md` | Research provenance, coverage rules, valuation limits, and source descriptions. |
| `docs/si_registry_rules.md`, `docs/special_classes.md` | Registry rule sources and the special-sheet schema/known-list limits. |

The RDAP and WHOIS channels are separate checks run against the same `.si` registry; WHOIS is not a different operator or registrar. Public registrar confirmation, registrar retail pricing, and premium availability/pricing remain unknown.

## Trademark and valuation limits

The T-17 USPTO screen stopped after an HTTP 403 on `bankingdesk` at 2026-10-13T18:05:11Z. PKG-G resumed on 2026-10-14 after the cooldown. Its control returned HTTP 200 JSON with 194 `google` hits, followed by 116 sequential candidate-query POSTs at a minimum five-second interval; all 117 requests returned HTTP 200 JSON. The T-18 rework added one `google` control and five sequential candidate queries, each at least five seconds from the preceding request start. Across PKG-G and the rework, 123 POSTs (two controls and 121 candidate queries) returned HTTP 200 JSON. There was no new 403, CAPTCHA, login, non-JSON response, timeout, 5xx, or retry. No TMview, UKIPO, RDAP, or WHOIS requests were made.

The prior `powdery [fuzzy-1]` HTTP 200 response had been parsed but not retained because an ASCII evidence writer rejected a non-ASCII wordmark. The parser now sanitizes distilled evidence text as ASCII, and the rework retained this query's outcome. It returned 2,097 hits overall, with 10 returned and 10 similar. `denimwear` exact and fuzzy-1 each returned two results, both similar. Its USPTO result is now `possible_conflict`, and it left the top 100. The replacement `soillab` exact query returned zero hits; its fuzzy-1 query returned 12 overall, with 10 returned and 10 similar. `soillab` entered the top 100 and was screened while USPTO remained live. These candidate outcomes are recorded at `RESUME-USPTO-00269` through `RESUME-USPTO-00293`; the new control is `RESUME-USPTO-00268`.

Final top-100 USPTO coverage is 100 complete, 0 query-blocked, and 0 unverified. Relative to the pre-rework PKG-G top 100, `soillab` entered and `denimwear` exited. Relative to T-17, entries are `examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `biomasshub`, `roboticflow`, and `biomasslab`; exits are `robotsystem`, `gyration`, `croplab`, `crophub`, `agrihub`, `cryptoworks`, and `parcelshop`. Names leaving the top 100 retain their evidence. On 2026-10-14, the owner-requested PKGH screen added exact and fuzzy-1 USPTO queries for profitdesk.si; both returned HTTP 200 JSON with zero matches. Top-100 USPTO coverage remains 100/100; profitdesk is the sole outside-top-100 USPTO screen, and all other names outside the top 100 remain not yet screened by USPTO. Except for profitdesk.si, screened at the owner's request, names ranked 101-500 remain not yet screened by USPTO.

| Source | PKG-G and T-18 rework requests and outcomes | Final top-100 coverage |
| --- | --- | --- |
| TMview | No requests. TMview source-wide refused: connection closed (evidence `REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified because of that refusal. | 0/100 complete; 0 query-blocked; 100 unverified |
| UKIPO | No requests. UKIPO source-wide refused: automated access refused (evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked because of that refusal. | 0/100 complete; 100 query-blocked; 0 unverified |
| USPTO | 2 `google` controls plus 121 candidate requests; all 123 HTTP 200 JSON; 0 new 403; no retries. | 100/100 complete; 0 query-blocked; 0 unverified |

The 44 originally blocked final-top-100 labels have exact and near USPTO outcomes; rework resolved the two remaining incomplete labels, `powdery` and `denimwear`, and one replacement entrant, `soillab`, was screened. The existing 2026-10-13 source-stop row `REWORK1-USPTO-SOURCE-STOP` remains in history. The earlier 139 JSON POSTs and UI-shell GET are also retained; PKG-G and T-18 append new evidence rather than replacing that history.

The three PKG-G entrant rounds processed while USPTO remained live added 9 (`examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `memolab`, `biomasshub`, `pharmatrial`, `epaulet`, `trekgear`), 4 (`roboticflow`, `gerilab`, `soilhub`, `biomasslab`), and 1 (`credittrack`). In the T-18 rework, `denimwear` left the top 100 after possible-conflict results, and `soillab` was screened as its replacement. TMview and UKIPO were not contacted. Names leaving the top 100 keep their evidence. Relative to T-17, final entries are `examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `biomasshub`, `roboticflow`, and `biomasslab`; exits are `robotsystem`, `gyration`, `crophub`, `croplab`, `agrihub`, `cryptoworks`, and `parcelshop`. Except for profitdesk.si, screened at the owner's request, names ranked 101-500 remain not yet screened by USPTO.

There are 37 final-top-100 names flagged for legal review, up from 24. Thirteen newly flagged names are `autokernel`, `autonetwork`, `autostream`, `carboncell`, `cashops`, `jewelshop`, `keyscan`, `pharmascan`, `powdery`, `reveler`, `robotspark`, `soilhub`, and `soillab`. The complete current list is `autobeacon`, `autokernel`, `autonetwork`, `autosearch`, `autostream`, `autoswitch`, `bankinghub`, `carboncell`, `carbonhub`, `cashledger`, `cashops`, `cizo`, `cowhide`, `creditdesk`, `datafleet`, `datalearn`, `dataledger`, `datasolve`, `dataswitch`, `jewelshop`, `keyscan`, `leaning`, `ledgerlink`, `loanledger`, `newsagen`, `paymentops`, `pharmascan`, `powdery`, `reveler`, `robotloop`, `robotspark`, `soilhub`, `soillab`, `stoical`, `tryto`, `unfus`, and `walletlink`. `denimwear` also has possible-conflict evidence but is outside the final top 100.

USPTO exact-label queries use an exact phrase and one near query: fuzziness 1 for labels at least five characters, or whole-word mode for shorter labels. Results retain only distilled serial number, wordmark, live/dead flag, status, classes, result URL, query and UTC timestamp; owner and attorney fields were not copied. Similarity review covers identical marks, whole-word containment, edit distance <=1, and identical stems in any class. Classes 9, 35, 36, 38, 41, and 42 are higher relevance. Live and dead marks both trigger review. A possible conflict in any source scores 25; all three sources must complete without a match to score 85; incomplete or refused sources score 40. These limited queries imply no clearance.

`validate-research` exits **2** because coverage is incomplete: TMview 0 completed / 0 query-blocked / 100 unverified; UKIPO 0 completed / 100 query-blocked / 0 unverified; USPTO 100 completed / 0 query-blocked / 0 unverified. `validate-delivery` is a separate structural check and can pass while research remains blocked. Screening is not comprehensive phonetic, class, national-office, or worldwide clearance.

### Manual trademark checks the owner can do

Official search pages: [TMview](https://www.tmdn.org/tmview/), [UKIPO](https://trademarks.ipo.gov.uk/ipo-tmtext), and [USPTO](https://tmsearch.uspto.gov/). TMview source-wide refused: connection closed (evidence `REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified because of that refusal. UKIPO source-wide refused: automated access refused (evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked because of that refusal. No further TMview or UKIPO attempts were made. USPTO's earlier HTTP 403 remains at `REWORK1-USPTO-00259` / `REWORK1-USPTO-SOURCE-STOP`. PKG-G and T-18 rework made 123 USPTO POSTs on 2026-10-14 (two controls and 121 candidate queries); all returned HTTP 200 JSON with no new 403 or retry. PKGH added one google control and exact/fuzzy-1 queries for profitdesk, all HTTP 200 JSON at least five seconds apart; neither candidate query returned a match. Final USPTO top-100 coverage is 100/100 complete. No name is cleared.

`validate-research --completion-mode` requires a recorded outcome for every top-100 name/source pair. A pair needs completed exact and near queries or dated blocked/unverified rows with an official source URL and an evidence-backed reason. Accepted incomplete reasons include an HTTP refusal, CAPTCHA, connection closure, cited source-stop row, a local evidence-write failure after a response, or the documented three-round screening limit. Missing pairs fail. The mode checks evidence completeness and score/status consistency without network requests; strict validation still exits 2 while required searches remain incomplete.

All **500 valuations** are literally `insufficiently supported`; currency, low, and high are blank. The evidence file separately records ten reported completed sales, two asking prices, and three unsupported source attempts. None qualified as a direct comparable for a current shortlist name. Asking prices are not sales, and the unsupported source attempts did not become market evidence. These entries are not appraisals.

## Rebuild from the recorded source snapshot (offline)

Prerequisites: Python 3.12 or compatible Python 3, with the packages in the repository's `requirements.txt` (`requests` and `openpyxl`); pytest is needed only to run tests. Install prerequisites if they are not already present:

```powershell
python --version
python -m pip install -r requirements.txt
```

The following PowerShell sequence regenerates candidate CSVs from curated inputs and rebuilds research artifacts under ignored `output/rebuild/`, leaving committed source snapshots untouched. Commands in this section are offline: they do not recheck RDAP/WHOIS, TMview, USPTO, UKIPO, or sales sources. The current trademark evidence can only represent the recorded results; it cannot complete blocked sources.

After exporting the committed workbook, run `python scripts/build_html.py` from the repository root to rebuild the committed HTML report. The isolated rebuild below writes its HTML beside the temporary workbook.

The report has **Top 500**, **All available** (3,395 names), and **Unavailable** (2,809 names) tabs for this 6,204-name snapshot. The long views render 60 rows per page; tabs support arrow-key navigation.

```powershell
$Build = 'output/rebuild'
$Source = "$Build/source"
New-Item -ItemType Directory -Force -Path $Build, $Source | Out-Null
python -m si_domains candidates --all
python -m si_domains candidates --all --out data/candidates.csv
Copy-Item data/candidates.csv, data/reserved_names.csv, data/restricted_names.csv, output/rdap_evidence.csv, output/whois_evidence.csv, output/shortlist.csv, output/valuation_evidence.csv, output/trademark_evidence.csv, output/sample_404_for_review.csv -Destination $Source -Force

# Seed the first top-100 summary from the committed ranked list, then rebuild scores and shortlist.
python -m si_domains trademark-summary --shortlist "$Source/shortlist.csv" --candidates "$Source/candidates.csv" --evidence "$Source/trademark_evidence.csv" --out "$Build/trademark_summary_1.csv" --top-n 100
python -m si_domains score --input "$Source/candidates.csv" --rdap-evidence "$Source/rdap_evidence.csv" --out "$Build/scores_1.csv" --trademark-evidence "$Build/trademark_summary_1.csv" --trademark-source-evidence "$Source/trademark_evidence.csv"
python -m si_domains shortlist --input "$Source/candidates.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores_1.csv" --out "$Build/shortlist_1.csv" --excluded "$Build/excluded_1.csv" --sample-out "$Build/sample_1.csv"

# Refresh the top-100 summary for the rebuilt rank order, then create final research artifacts.
python -m si_domains trademark-summary --shortlist "$Build/shortlist_1.csv" --candidates "$Source/candidates.csv" --evidence "$Source/trademark_evidence.csv" --out "$Build/trademark_summary_2.csv" --top-n 100
python -m si_domains score --input "$Source/candidates.csv" --rdap-evidence "$Source/rdap_evidence.csv" --out "$Build/scores.csv" --trademark-evidence "$Build/trademark_summary_2.csv" --trademark-source-evidence "$Source/trademark_evidence.csv"
python -m si_domains shortlist --input "$Source/candidates.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores.csv" --out "$Build/shortlist.csv" --excluded "$Build/excluded.csv" --sample-out "$Build/sample_404_for_review.csv"
python -m si_domains valuations --shortlist "$Build/shortlist.csv" --evidence "$Source/valuation_evidence.csv" --out "$Build/valuations.csv"
python -m si_domains opportunities --shortlist "$Build/shortlist.csv" --scores "$Build/scores.csv" --valuations "$Build/valuations.csv" --trademark-summary "$Build/trademark_summary_2.csv" --out "$Build/opportunities.csv"

# This is expected to exit 2 for the recorded snapshot because top-100 screening is unresolved.
python -m si_domains validate-research --shortlist "$Build/shortlist.csv" --scores "$Build/scores.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-evidence "$Source/trademark_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --opportunities "$Build/opportunities.csv" --candidates "$Source/candidates.csv"
$ResearchExit = $LASTEXITCODE
if ($ResearchExit -ne 2) { throw "Expected validate-research exit 2 for unresolved trademark coverage; got $ResearchExit" }

# This checks that the same incomplete research is recorded honestly, without network access.
python -m si_domains validate-research --shortlist "$Build/shortlist.csv" --scores "$Build/scores.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-evidence "$Source/trademark_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --opportunities "$Build/opportunities.csv" --candidates "$Source/candidates.csv" --completion-mode
if ($LASTEXITCODE -ne 0) { throw "Expected completion-mode validation to pass; got $LASTEXITCODE" }

# Export and structurally validate the rebuilt workbook. Validation is read-only.
python -m si_domains export --out "$Build/si_domains_ranked.xlsx" --candidates "$Source/candidates.csv" --reserved-names "$Source/reserved_names.csv" --restricted-names "$Source/restricted_names.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores.csv" --shortlist "$Build/shortlist.csv" --excluded "$Build/excluded.csv" --opportunities "$Build/opportunities.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --trademark-evidence "$Source/trademark_evidence.csv" --sample "$Source/sample_404_for_review.csv"
python scripts/build_html.py --xlsx "$Build/si_domains_ranked.xlsx" --out "$Build/si_domains_ranked.html"
python -m si_domains validate-delivery --workbook "$Build/si_domains_ranked.xlsx" --candidates "$Source/candidates.csv" --reserved-names "$Source/reserved_names.csv" --restricted-names "$Source/restricted_names.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores.csv" --shortlist "$Build/shortlist.csv" --excluded "$Build/excluded.csv" --opportunities "$Build/opportunities.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --trademark-evidence "$Source/trademark_evidence.csv" --sample "$Source/sample_404_for_review.csv"
```

The summary preserves prior evidence for names that leave the top 100 and records incomplete results for new entrants. A refusal never becomes a completed query. Do not run beyond three screening rounds without a new authorization. `validate-delivery` checks workbook and CSV consistency and may exit 0 while reporting **Research screening BLOCKED**; strict `validate-research` remains the coverage check and exits 2 on the current snapshot, while `--completion-mode` checks that recorded outcomes and resulting statuses are complete and honest.

## Optional fresh live verification

These commands are outside the offline rebuild above and were **not run for this package**. They contact the public registry and WHOIS service. Keep the built-in pacing (RDAP at least one second between request starts; WHOIS at least one second, two seconds by default), honor retry/cooldown behavior, stop on unverified/refused access, and do not bypass rate limits, CAPTCHAs, or anti-bot controls. Never describe an RDAP 404 as guaranteed availability.

```powershell
python -m si_domains check --input data/candidates.csv --limit 25 --stop-on-unverified
python -m si_domains whois-check --input data/candidates.csv --limit 30
```

The workbook and this README report the evidence available for the dated snapshot. They do not claim the project completion gate has passed. The unresolved trademark-screen criterion remains explicit; only the configured independent review and owner gate can certify completion.
