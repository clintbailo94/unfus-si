# Ranked `.si` workbook delivery

## Snapshot and meaning

Open [si_domains_ranked.xlsx](si_domains_ranked.xlsx) for the ranked workbook. It is a reproducible offline export of the timestamped CSV evidence in this repository. Its **6,204 unique candidates** were checked through the recorded registry channels; **500** names are joined into the ranked opportunity sheet.

The RDAP/WHOIS snapshot date is **2026-10-13 UTC**; trademark evidence was refreshed on **2026-10-14 UTC**. RDAP history has 6,219 rows timestamped from `2026-10-13T01:11:41Z` through `2026-10-13T05:02:17Z`; the latest-row view covers 6,204 candidates, with 2,803 `registered` and 3,401 `potentially_unregistered`. WHOIS history has 3,401 rows from `2026-10-13T05:12:13Z` through `2026-10-13T10:11:47Z`; latest results are 3,395 `not_registered` and six `registered` conflicts. These are dated registry-channel observations, not a registrar checkout guarantee or assurance that registration will succeed.

Candidate counts by category are: AI 1,500; invented 1,454; dictionary 996; short 700; business and finance 359; emerging industries 289; consumer brands 265; technology 254; health and science 252; domain hacks 135. The pipeline scored 3,401 RDAP-404 rows, excluded 2,809 registered/conflict rows, selected 500 opportunities, and left 2,895 otherwise eligible rows outside the 500-name selection. The review sample contains 30 rows and uses seed 20261013.

The six WHOIS conflicts are **embedengine.si, geve.si, identityhub.si, lanova.si, shallwe.si, and swarmpilot.si**. Each remains excluded and labelled as a conflict in `All candidates`; none is in `Shortlist`.

The score weights remain brandability 25%, commercial demand 20%, shortness 15%, hack creativity 15%, resale heuristic 15%, and trademark 10%. Final data has 356 distinct five-component tuples and 500 distinct rationales. Commercial-score standard deviation is 16.58; mean commercial score for AI/technology/business-finance rows is 60.03 versus 42.48 for invented rows. Rootless invented/name-like resale scores cap at 65. Higher trademark scores indicate lower estimated risk. Ties sort by total descending, label length ascending, then case-folded domain.
Per-category mean commercial and resale components are listed in the [research methodology](research_methodology.md).

The final 500 category limit is **100 per category (20%)**. Selection also limits any top-100 category to 35 names, six invented/given-name labels per final-three-letter ending and per first-four-letter prefix, and ten compound/blend labels per head or tail. There are 1,353 eligible labels marked `family cap`; they stay eligible and visible in `All candidates`.

| Category | Pool | Eligible | Final 500 | Median eligible rank | Minimum eligible rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ai | 1,500 | 991 | 100 | 2362 | 6 |
| business_finance | 359 | 288 | 51 | 1946.5 | 4 |
| consumer_brands | 265 | 226 | 91 | 2361.5 | 66 |
| dictionary | 996 | 26 | 8 | 3356.5 | 59 |
| domain_hacks | 135 | 15 | 3 | 3351 | 1 |
| emerging_industries | 289 | 232 | 50 | 2238.5 | 30 |
| health_science | 252 | 221 | 59 | 2541 | 94 |
| invented | 1,454 | 1,247 | 100 | 1403 | 517 |
| short | 700 | 6 | 6 | 17 | 14 |
| technology | 254 | 143 | 32 | 1068 | 5 |

Top-100 category counts: ai: 35; business_finance: 13; consumer_brands: 9; dictionary: 5; domain_hacks: 3; emerging_industries: 12; health_science: 2; short: 6; technology: 15. The largest category contributes 35/100 and there are 100/100 non-invented keyword, common-word, short, or hack names. All six eligible four-letter CVCV shorts are selected at ranks 14 fuve.si, 15 guve.si, 16 puve.si, 18 kuzo.si, 19 guza.si, 28 cizo.si; no three-letter short name was registry-eligible. The three selected hacks rank 1 newsagen.si, 2 unfus.si, 3 tryto.si; 15 hacks were eligible, so hack availability exceeds selection and quality/scoring determines the selected three. Strongest root-bearing compounds include ranks 4 cashops.si, 5 paymentops.si, 6 datafleet.si, 7 ledgerhub.si, 8 payablehub.si, 9 datalearn.si, 10 payabledesk.si, 11 payableflow.si, 12 datasolve.si, 13 walletlab.si, 17 chatledger.si, 20 dataledger.si. Methodology and root-level values are in [research methodology](research_methodology.md).

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

The T-17 USPTO screen stopped after an HTTP 403 on `bankingdesk` at 2026-10-13T18:05:11Z. PKG-G resumed on 2026-10-14 after the cooldown. Before any candidate request, one `google` control returned HTTP 200 JSON with 194 hits. The pass made 116 sequential candidate-query POSTs at a minimum five-second interval. Including the control, all 117 POSTs returned HTTP 200 JSON. There was no new 403, CAPTCHA, login, non-JSON response, timeout, 5xx, or retry. Two additional requests repeated the `soilhub` exact and near pair after it re-entered the top 100; latest evidence wins.

One `powdery` near-query response was received and parsed, but its evidence could not be retained after the local ASCII writer rejected a non-ASCII wordmark. That query is recorded `unverified`, and no retry was made. The source was not stopped. The final top-100 USPTO coverage is 98 complete, 0 query-blocked, and 2 unverified. The two unverified names are `powdery` and `denimwear`; `denimwear` entered after the third entrant round and received unverified USPTO outcome rows without requests because the three-round cap had been reached.

| Source | PKG-G requests and outcomes | Final top-100 coverage |
| --- | --- | --- |
| TMview | No requests. Existing probes closed before an HTTP response; new entrant rows cite `REWORK1-TMVIEW-PROBES` at 2026-10-13T18:02:42Z. | 0/100 complete; 0 query-blocked; 100 unverified |
| UKIPO | No requests. Existing search GET returned HTTP 403 Service Captcha; new entrant rows cite `PKGD-0003` at 2026-10-13T17:09:52Z. | 0/100 complete; 100 query-blocked; 0 unverified |
| USPTO | 1 `google` control plus 116 candidate requests; all 117 HTTP 200 JSON; 0 new 403; no retries. | 98/100 complete; 0 query-blocked; 2 unverified |

The original 44 blocked final-top-100 labels each received exact and near queries. Forty-three now have both query outcomes retained; `powdery` exact is a possible conflict and its near query is unverified after the local evidence-write failure. The existing 2026-10-13 source-stop row `REWORK1-USPTO-SOURCE-STOP` remains in history. The earlier 139 JSON POSTs and UI-shell GET are also retained; PKG-G adds new evidence rather than replacing that history.

Three entrant rounds were processed while USPTO remained live: Round 1 added 9 (`examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `memolab`, `biomasshub`, `pharmatrial`, `epaulet`, `trekgear`); Round 2 added 4 (`roboticflow`, `gerilab`, `soilhub`, `biomasslab`); Round 3 added `credittrack`. TMview and UKIPO were not contacted. Names leaving the top 100 keep their evidence. Final top-100 entries versus T-17 are `examhub`, `bankingvault`, `roboticlink`, `roboticloop`, `biomasshub`, `roboticflow`, `biomasslab`, and `denimwear`. Exits are `robotsystem`, `soillab`, `gyration`, `crophub`, `croplab`, `agrihub`, `cryptoworks`, and `parcelshop`. Names ranked 101-500 remain not yet screened.

There are 36 final-top-100 names flagged for legal review, up from 24. Twelve newly flagged names are `autokernel`, `autonetwork`, `autostream`, `carboncell`, `cashops`, `jewelshop`, `keyscan`, `pharmascan`, `powdery`, `reveler`, `robotspark`, and `soilhub`. The complete current list is `autobeacon`, `autokernel`, `autonetwork`, `autosearch`, `autostream`, `autoswitch`, `bankinghub`, `carboncell`, `carbonhub`, `cashledger`, `cashops`, `cizo`, `cowhide`, `creditdesk`, `datafleet`, `datalearn`, `dataledger`, `datasolve`, `dataswitch`, `jewelshop`, `keyscan`, `leaning`, `ledgerlink`, `loanledger`, `newsagen`, `paymentops`, `pharmascan`, `powdery`, `reveler`, `robotloop`, `robotspark`, `soilhub`, `stoical`, `tryto`, `unfus`, and `walletlink`.

USPTO exact-label queries use an exact phrase and one near query: fuzziness 1 for labels at least five characters, or whole-word mode for shorter labels. Results retain only distilled serial number, wordmark, live/dead flag, status, classes, result URL, query and UTC timestamp; owner and attorney fields were not copied. Similarity review covers identical marks, whole-word containment, edit distance <=1, and identical stems in any class. Classes 9, 35, 36, 38, 41, and 42 are higher relevance. Live and dead marks both trigger review. A possible conflict in any source scores 25; all three sources must complete without a match to score 85; incomplete or refused sources score 40. These limited queries imply no clearance.

`validate-research` exits **2** because coverage is incomplete: TMview 0 completed / 0 query-blocked / 100 unverified; UKIPO 0 completed / 100 query-blocked / 0 unverified; USPTO 98 completed / 0 query-blocked / 2 unverified. `validate-delivery` is a separate structural check and can pass while research remains blocked. Screening is not comprehensive phonetic, class, national-office, or worldwide clearance.

### Manual trademark checks the owner can do

Official search pages: [TMview](https://www.tmdn.org/tmview/), [UKIPO](https://trademarks.ipo.gov.uk/ipo-tmtext), and [USPTO](https://tmsearch.uspto.gov/). TMview and UKIPO remain inaccessible to automated screening based on their recorded source-wide refusal evidence; no further attempts were made. USPTO's earlier HTTP 403 remains at `REWORK1-USPTO-00259` / `REWORK1-USPTO-SOURCE-STOP`. PKG-G made one cooled-down control and 116 candidate requests on 2026-10-14; all 117 returned HTTP 200 JSON with no new 403. No name is cleared.

`validate-research --completion-mode` requires a recorded outcome for every top-100 name/source pair. A pair needs completed exact and near queries or dated blocked/unverified rows with an official source URL and an evidence-backed reason. Accepted incomplete reasons include an HTTP refusal, CAPTCHA, connection closure, cited source-stop row, a local evidence-write failure after a response, or the documented three-round screening limit. Missing pairs fail. The mode checks evidence completeness and score/status consistency without network requests; strict validation still exits 2 while required searches remain incomplete.

All **500 valuations** are literally `insufficiently supported`; currency, low, and high are blank. The evidence file separately records ten reported completed sales, two asking prices, and three unsupported source attempts. None qualified as a direct comparable for a current shortlist name. Asking prices are not sales, and the unsupported source attempts did not become market evidence. These entries are not appraisals.

## Rebuild from the recorded source snapshot (offline)

Prerequisites: Python 3.12 or compatible Python 3, with the packages in the repository's `requirements.txt` (`requests` and `openpyxl`); pytest is needed only to run tests. Install prerequisites if they are not already present:

```powershell
python --version
python -m pip install -r requirements.txt
```

The following PowerShell sequence regenerates candidate CSVs from curated inputs and rebuilds research artifacts under ignored `output/rebuild/`, leaving committed source snapshots untouched. Commands in this section are offline: they do not recheck RDAP/WHOIS, TMview, USPTO, UKIPO, or sales sources. The current trademark evidence can only represent the recorded results; it cannot complete blocked sources.

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
