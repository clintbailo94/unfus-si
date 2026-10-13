# Ranked `.si` workbook delivery

## Snapshot and meaning

Open [si_domains_ranked.xlsx](si_domains_ranked.xlsx) for the ranked workbook. It is a reproducible offline export of the timestamped CSV evidence in this repository. Its **6,204 unique candidates** were checked through the recorded registry channels; **500** names are joined into the ranked opportunity sheet.

The snapshot date is **2026-10-13 UTC**. RDAP history has 6,219 rows timestamped from `2026-10-13T01:11:41Z` through `2026-10-13T05:02:17Z`; the latest-row view covers 6,204 candidates, with 2,803 `registered` and 3,401 `potentially_unregistered`. WHOIS history has 3,401 rows from `2026-10-13T05:12:13Z` through `2026-10-13T10:11:47Z`; latest results are 3,395 `not_registered` and six `registered` conflicts. These are dated registry-channel observations, not a registrar checkout guarantee or assurance that registration will succeed.

Candidate counts by category are: AI 1,500; invented 1,454; dictionary 996; short 700; business and finance 359; emerging industries 289; consumer brands 265; technology 254; health and science 252; domain hacks 135. The pipeline scored 3,401 RDAP-404 rows, excluded 2,809 registered/conflict rows, selected 500 opportunities, and left 2,895 otherwise eligible rows outside the workbook's 500-name/100-per-category selection cap. The review sample contains 30 rows and uses seed 20261013.

The six WHOIS conflicts are **embedengine.si, geve.si, identityhub.si, lanova.si, shallwe.si, and swarmpilot.si**. Each remains excluded and labelled as a conflict in `All candidates`; none is in `Shortlist`.

Ranking uses brandability 25%, commercial relevance 20%, shortness 15%, domain-hack creativity 15%, resale heuristic 15%, and trademark risk 10%. Per-name root and shape factors create 356 distinct five-component tuples among the final 500. The weighted total is out of 100; higher trademark scores mean lower estimated risk. Rows sort by total descending, label length ascending, then case-folded domain ascending. Selection is capped at 500 overall and 100 per category (20%).

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

All six eligible four-letter CVCV short labels are selected; there was no eligible three-letter short label. The three high-quality eligible hacks rank 1–3; the other 12 eligible hacks are awkward, weak, or narrow-seed labels and were penalized below the cut. The 100-per-category cap preserves diversity. Scores are heuristics, not evidence of demand, market value, availability, or legal safety.

Commercial demand is rooted in the tiered table in [research methodology](research_methodology.md). Example scores:

| Tier | Example roots (demand score) | Treatment |
| --- | --- | --- |
| 1 | ai 96; pay 94; cloud 92; data 92; health 90; bank 89; trade 87 | High-demand roots |
| 2 | fintech 82; agent 78; credit 79; robot 77; tech 77; news 76 | Mid-demand roots |
| 3 | food 68; ledger 68; pharma 67; genome 64; carbon 64 | Niche roots |
| Unknown | base demand 48; buyer breadth 4 | Label shape and length still differentiate |

Compounds score their head and tail separately and gain six points when both parts are commercial roots. Resale also uses length, syllables, commonness, phonetic ease, buyer breadth, hack rarity, and ambiguous-letter penalties. The workbook Methodology sheet lists every root and value.

The `given_name` list in `data/given_names.txt` moves curated false-dictionary names to `invented` without dropping candidate labels. Exact negative, medical, bodily, pejorative, and awkward-label penalties are in `data/scoring_penalties.txt`. The final dictionary-category names are common English words: stoical, leaning, cowhide, powdery, reveler, gyration, epaulet, and decorous. See [the research methodology](research_methodology.md) for the list of prior-shortlist removals and borderline keeps.

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
| `output/sample_404_for_review.csv` | The deterministic 30-row review sample counted in Methodology. |
| `output/research_methodology.md`, `output/valuation_sources_notes.md` | Research provenance, coverage rules, valuation limits, and source descriptions. |
| `docs/si_registry_rules.md`, `docs/special_classes.md` | Registry rule sources and the special-sheet schema/known-list limits. |

The RDAP and WHOIS channels are separate checks run against the same `.si` registry; WHOIS is not a different operator or registrar. Public registrar confirmation, registrar retail pricing, and premium availability/pricing remain unknown.

## Trademark and valuation limits

The final top 100 each have a per-source coverage record, but **zero required-query sets were completed**. One source probe was made per host: TMview closed the connection before an HTTP response (100 unverified final names); UKIPO returned HTTP 403 `Service Captcha` (100 blocked names); USPTO returned HTTP 200 with a JavaScript shell but no parseable results (100 unverified names). No per-domain request was sent after those outcomes. Six new entrants were added as Round 2 coverage records from the existing source-wide outcomes; no additional requests ran. The final top 100 then stabilized. No name was flagged for legal review because no mark data was returned. The other 400 opportunities say `not yet screened`.

Trademark scores map to 85 for a complete limited screen with no obvious match, 25 when a similar/identical mark needs legal review, and 40 for incomplete, blocked, unverified, or not-yet-screened states. The 40 value is explicitly below a clean screen and above a conflict; weights are not renormalized. A clean screen can add up to 4.5 weighted points over an unscreened candidate, so new final-top-100 entrants must be screened in subsequent ranking rounds when sources allow. `validate-research` exits 2 because TMview is 0/100 complete, UKIPO is 0/100, and USPTO is 0/100. These scores do not imply legal safety or clearance. The method is not comprehensive phonetic, class, national-office, or worldwide legal clearance; possible conflicts need qualified legal review.

The review rule flags an identical word mark, whole-word containment of or by the label, an edit distance of at most one for labels of five or more characters, or an identical stem in any class. Classes 9, 35, 36, 38, 41, and 42 have higher relevance. Anything uncertain requires legal review; it is never treated as clear.

All **500 valuations** are literally `insufficiently supported`; currency, low, and high are blank. The evidence file separately records ten reported completed sales, two asking prices, and three unsupported source attempts. None qualified as a direct comparable for a current shortlist name. Asking prices are not sales, and the unsupported source attempts did not become market evidence. These entries are not appraisals.

See [research methodology](research_methodology.md), [valuation source notes](valuation_sources_notes.md), [registry rules](../docs/si_registry_rules.md), and [special class schema](../docs/special_classes.md). The 2026-10-13 research notes record the access outcomes and the fact that no per-domain trademark search ran; they are historical observations, not permanent statements about current browser or source access.

## Rebuild from the recorded source snapshot (offline)

Prerequisites: Python 3.12 or compatible Python 3, with the packages in the repository's `requirements.txt` (`requests` and `openpyxl`); pytest is needed only to run tests. Install prerequisites if they are not already present:

```powershell
python --version
python -m pip install -r requirements.txt
```

The following PowerShell sequence regenerates candidate CSVs from the curated candidate inputs and copies the committed candidate, registry, rule, curated-research, and review-sample snapshots into `output/rebuild/source/`. It rebuilds research files in `output/rebuild/`, leaving the committed source CSVs untouched. All commands in this section are offline. They do not recheck the registry, WHOIS, trademark databases, or sales sources.

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

For this snapshot the second summary is built only from the existing evidence. It cannot add completed searches. If ranked membership changes later, rerun the offline aggregation to expose the new names' unverified/source-wide state, then acquire actual permitted public-query evidence separately before claiming screening coverage. `validate-delivery` checks every workbook cell against the named CSVs and may exit 0 while reporting **Research screening BLOCKED**; it is not the separate `validate-research` completion check.

## Optional fresh live verification

These commands are outside the offline rebuild above and were **not run for this package**. They contact the public registry and WHOIS service. Keep the built-in pacing (RDAP at least one second between request starts; WHOIS at least one second, two seconds by default), honor retry/cooldown behavior, stop on unverified/refused access, and do not bypass rate limits, CAPTCHAs, or anti-bot controls. Never describe an RDAP 404 as guaranteed availability.

```powershell
python -m si_domains check --input data/candidates.csv --limit 25 --stop-on-unverified
python -m si_domains whois-check --input data/candidates.csv --limit 30
```

The workbook and this README report the evidence available for the dated snapshot. They do not claim the project completion gate has passed. The unresolved trademark-screen criterion remains explicit; only the configured independent review and owner gate can certify completion.
