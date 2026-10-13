# Ranked `.si` workbook delivery

## Snapshot and meaning

Open [si_domains_ranked.xlsx](si_domains_ranked.xlsx) for the ranked workbook. It is a reproducible offline export of the timestamped CSV evidence in this repository. Its **6,204 unique candidates** were checked through the recorded registry channels; **500** names are joined into the ranked opportunity sheet.

The snapshot date is **2026-10-13 UTC**. RDAP history has 6,219 rows timestamped from `2026-10-13T01:11:41Z` through `2026-10-13T05:02:17Z`; the latest-row view covers 6,204 candidates, with 2,803 `registered` and 3,401 `potentially_unregistered`. WHOIS history has 3,401 rows from `2026-10-13T05:12:13Z` through `2026-10-13T10:11:47Z`; latest results are 3,395 `not_registered` and six `registered` conflicts. These are dated registry-channel observations, not a registrar checkout guarantee or assurance that registration will succeed.

Candidate counts by category are: AI 1,500; invented 1,454; dictionary 996; short 700; business and finance 359; emerging industries 289; consumer brands 265; technology 254; health and science 252; domain hacks 135. The pipeline scored 3,401 RDAP-404 rows, excluded 2,809 registered/conflict rows, selected 500 opportunities, and left 2,895 otherwise eligible rows outside the 500-name selection. The review sample contains 30 rows and uses seed 20261013.

The six WHOIS conflicts are **embedengine.si, geve.si, identityhub.si, lanova.si, shallwe.si, and swarmpilot.si**. Each remains excluded and labelled as a conflict in `All candidates`; none is in `Shortlist`.

The score weights remain brandability 25%, commercial demand 20%, shortness 15%, hack creativity 15%, resale heuristic 15%, and trademark 10%. Final data has 358 distinct five-component tuples and 500 distinct rationales. Commercial-score standard deviation is 16.57; mean commercial score for AI/technology/business-finance rows is 60.02 versus 42.48 for invented rows. Rootless invented/name-like resale scores cap at 65. Higher trademark scores indicate lower estimated risk. Ties sort by total descending, label length ascending, then case-folded domain.
Per-category mean commercial and resale components are listed in the [research methodology](research_methodology.md).

The final 500 category limit is **100 per category (20%)**. Selection also limits any top-100 category to 35 names, six invented/given-name labels per final-three-letter ending and per first-four-letter prefix, and ten compound/blend labels per head or tail. There are 1,364 eligible labels marked `family cap`; they stay eligible and visible in `All candidates`.

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

Top-100 category counts: ai: 33; business_finance: 12; consumer_brands: 8; dictionary: 6; domain_hacks: 3; emerging_industries: 14; health_science: 2; short: 6; technology: 16. The largest category contributes 33/100 and there are 100/100 non-invented keyword, common-word, short, or hack names. All six eligible four-letter CVCV shorts are selected at ranks 14 fuve.si, 15 guve.si, 16 puve.si, 18 kuzo.si, 19 guza.si, 28 cizo.si; no three-letter short name was registry-eligible. The three selected hacks rank 1 newsagen.si, 2 unfus.si, 3 tryto.si; 15 hacks were eligible, so hack availability exceeds selection and quality/scoring determines the selected three. Strongest root-bearing compounds include ranks 4 cashops.si, 5 paymentops.si, 6 datafleet.si, 7 ledgerhub.si, 8 payablehub.si, 9 datalearn.si, 10 payabledesk.si, 11 payableflow.si, 12 datasolve.si, 13 walletlab.si, 17 chatledger.si, 20 dataledger.si. Methodology and root-level values are in [research methodology](research_methodology.md).

The 21 audited false-dictionary labels in `data/given_names.txt` (including brena, genal, neral, belal, celal, delal, belami, belona, belova, delina, dorina, genaro, lorina, merina, belara, calami, dorino, elette, karena, larena, and marena) are category `invented` with `given_name`; the candidate pool is unchanged. The final dictionary labels are stoical, powdery, leaning, cowhide, reveler, gyration, epaulet, and decorous. Five additional exact penalties were added after label review: bloodmonitor, bloodtrack, gynclinic, hemoclinic, and tumormarker. `floun` and `plian` are also below the cut after applying the exact penalty to hack scoring. Full dictionary meanings, clinical borderline keeps, and the existing removed-label history are in the methodology.

## Workbook sheets

- **Shortlist** — the final 500 joined opportunity records in rank order. It retains every `opportunities.csv` field, numeric rank and scores, exact source timestamps, full rationales, valuation/trademark statuses and evidence IDs, plus current RDAP HTTP/classification and WHOIS classification. Unsupported low/high price cells are blank.
- **All candidates** — all 6,204 candidate rows and their original metadata, latest RDAP and WHOIS evidence, rule/source, score components where scored, shortlist rank, registry status and exclusion reason. Latest means the last appended evidence row for a domain. Registered, missing, unchecked, unverified and WHOIS conflict states remain distinct.
- **Unverified** — candidates with missing/unverified latest RDAP or a missing/unverified required WHOIS second check. This snapshot has zero rows; the sheet keeps its headers and the Methodology sheet explains why. Trademark uncertainty is reported separately.
- **Special classes** — documented alias for `Reserved/Restricted/Invalid/Premium`. Excel forbids `/` in sheet names and limits names to 31 characters. Rows are normalized as `candidate` or `rule_reference`, so the reserved/restricted inventory cannot be mistaken for queried candidates. No invalid or premium candidate example is invented. An empty premium-name inventory does not establish ordinary registrar pricing.
- **Methodology** — counts, timestamp ranges, ranking and eligibility rules, weights, per-source trademark coverage, limitations, source paths and byte-level SHA-256 hashes.
- **Scores** — all 3,401 score records.
- **RDAP evidence** and **WHOIS evidence** — every source CSV row, including append-only history.
- **Valuation evidence** and **Trademark evidence** — every curated record.

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

The final top 100 have per-source outcome rows. Screening followed the ranking for three rounds: Round 1 processed 100 labels, Round 2 added 3 new entrants, and Round 3 added 9. Names that later left the top 100 keep their evidence. Source refusal rows are blocked or unverified and never count as completed searches.

| Source | Requests and HTTP outcomes | Final top-100 outcome |
| --- | --- | --- |
| TMview | One earlier POST plus three rework API probes (two POST shapes, one GET); all four API connections closed before an HTTP response. The UI shell was readable but did not yield search results. | 0/100 complete; 100 unverified |
| UKIPO | One recorded GET returned HTTP 403 `Service Captcha`; stopped, no retry. | 0/100 complete; 100 blocked |
| USPTO | One earlier UI-shell GET returned HTTP 200 JavaScript HTML without parseable search results; plus 139 JSON API POSTs total: two recorded controls (google = 194 hits; qzxwvk = 0), three initial API/field-shape probes, and 134 candidate attempts. Candidate attempts: 133 HTTP 200 JSON, one HTTP 403 on bankingdesk near query; stopped. The remaining 66 query slots were recorded blocked without requests. | 56/100 complete; 44 query-blocked |

USPTO exact-label queries used an exact phrase, then one near query (fuzziness 1 for labels >=5 characters, whole-word mode for shorter names), paced at no more than one request per second. Results store only distilled serial number, wordmark, live/dead flag, status, classes, result URL, exact URL/query, and UTC timestamp; owner and attorney fields were not copied. Similarity review covers identical marks, whole-word containment, edit distance <=1 for labels >=5 characters, or an identical stem in any class. Classes 9, 35, 36, 38, 41, and 42 are higher relevance; live and dead matches are both flagged. Any uncertainty requires legal review.

**24 names** were flagged for USPTO legal review: newsagen, unfus, tryto, paymentops, datafleet, datalearn, datasolve, dataledger, loanledger, cashledger, robotloop, cizo, ledgerlink, walletlink, bankinghub, stoical, dataswitch, creditdesk, leaning, carbonhub, autoswitch, autobeacon, autosearch, cowhide. A possible conflict in any source scores 25 even when the others are blocked. Trademark scores map to 85 only when all three sources complete with no obvious similar mark, 25 for a possible conflict, and 40 for incomplete, blocked, unverified, or not-yet-screened status. The 40 is explicitly lower than clear and higher than a conflict; weights are not renormalized. Unknown risk is penalized relative to a clean screen, and a conflict is penalized most. A screened-clear name could gain up to 4.5 weighted points over an unscreened name, so new top-100 entrants are screened in later rounds when access permits. These limited queries imply no clearance.

`validate-research` exits **2** because required coverage is incomplete: TMview 0 completed, 0 query-blocked, 100 unverified; UKIPO 0 completed, 100 query-blocked, 0 unverified; USPTO 56 completed, 44 query-blocked, 0 unverified. In particular TMview and UKIPO were inaccessible and USPTO stopped after an HTTP 403 with 44 top-100 labels still incomplete. Its output separates those exact states. The final top 100 are not legally cleared; the screen is not comprehensive phonetic, class, national-office, or worldwide clearance.

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

# Export and structurally validate the rebuilt workbook. Validation is read-only.
python -m si_domains export --out "$Build/si_domains_ranked.xlsx" --candidates "$Source/candidates.csv" --reserved-names "$Source/reserved_names.csv" --restricted-names "$Source/restricted_names.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores.csv" --shortlist "$Build/shortlist.csv" --excluded "$Build/excluded.csv" --opportunities "$Build/opportunities.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --trademark-evidence "$Source/trademark_evidence.csv" --sample "$Source/sample_404_for_review.csv"
python -m si_domains validate-delivery --workbook "$Build/si_domains_ranked.xlsx" --candidates "$Source/candidates.csv" --reserved-names "$Source/reserved_names.csv" --restricted-names "$Source/restricted_names.csv" --rdap-evidence "$Source/rdap_evidence.csv" --whois-evidence "$Source/whois_evidence.csv" --scores "$Build/scores.csv" --shortlist "$Build/shortlist.csv" --excluded "$Build/excluded.csv" --opportunities "$Build/opportunities.csv" --valuations "$Build/valuations.csv" --valuation-evidence "$Source/valuation_evidence.csv" --trademark-summary "$Build/trademark_summary_2.csv" --trademark-evidence "$Source/trademark_evidence.csv" --sample "$Source/sample_404_for_review.csv"
```

The summary preserves prior evidence for names that leave the top 100 and records incomplete results for new entrants. A refusal never becomes a completed query. Do not run beyond three screening rounds without a new authorization. `validate-delivery` checks workbook and CSV consistency and may exit 0 while reporting **Research screening BLOCKED**; `validate-research` is the separate coverage check and exits 2 on the current snapshot.

## Optional fresh live verification

These commands are outside the offline rebuild above and were **not run for this package**. They contact the public registry and WHOIS service. Keep the built-in pacing (RDAP at least one second between request starts; WHOIS at least one second, two seconds by default), honor retry/cooldown behavior, stop on unverified/refused access, and do not bypass rate limits, CAPTCHAs, or anti-bot controls. Never describe an RDAP 404 as guaranteed availability.

```powershell
python -m si_domains check --input data/candidates.csv --limit 25 --stop-on-unverified
python -m si_domains whois-check --input data/candidates.csv --limit 30
```

The workbook and this README report the evidence available for the dated snapshot. They do not claim the project completion gate has passed. The unresolved trademark-screen criterion remains explicit; only the configured independent review and owner gate can certify completion.
