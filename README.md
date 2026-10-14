# AI

## Ranked workbook delivery (offline)

The owner-facing guide is [output/README.md](output/README.md), and the generated
workbook is [output/si_domains_ranked.xlsx](output/si_domains_ranked.xlsx). The
guide records the snapshot counts and limits, all source CSVs, and a complete
PowerShell sequence to rebuild research outputs and the workbook from local
snapshots without registry or trademark requests.

For the committed CSV snapshot, export and check the workbook with:

```powershell
python -m si_domains export --out output/si_domains_ranked.xlsx
python scripts/build_html.py
python -m si_domains validate-delivery --workbook output/si_domains_ranked.xlsx
```

The HTML report includes Top 500, All available, and Unavailable views with paged rows and keyboard-operable tabs. Owned domains remain in Top 500 and Your domains, and are excluded from All available.

`data/owned_domains.txt` records domains bought by you and their purchase dates. The workbook and HTML mark those rows as owned; registry evidence is pre-purchase history, and ownership does not change scores or ranks.

`validate-delivery` compares every workbook row and cell to the current sources.
It can report structural delivery PASS while saying research screening BLOCKED;
`python -m si_domains validate-research --candidates data/candidates.csv`
remains separate and exits 2 while required top-100 screening is incomplete:
TMview 0 complete / 100 unverified, UKIPO 0 complete / 100 query-blocked, and
USPTO 100 complete / 0 query-blocked / 0 unverified. TMview is source-wide
refused because the connection closed (`REWORK1-TMVIEW-PROBES`); its per-name
results are unverified. UKIPO is source-wide refused because automated access
was refused (`PKGD-0003`); its per-name results are blocked. Neither command
certifies project completion or owner acceptance.

Add `--completion-mode` to validate that every top-100 name/source pair has a
dated, evidence-backed completed or refused outcome, the summary and scores
reflect conflicts and incomplete sources, and no top-100 opportunity remains
`not yet screened`. This mode checks the record without making network
requests; it does not treat a refusal as a completed search or a clearance.

## Running the verification

Run a small, polite live smoke check and inspect its body-free evidence:

```powershell
python -m si_domains check --input data/candidates.csv --limit 25 --stop-on-unverified
python -m si_domains status --input data/candidates.csv
```

For a longer run, set a wall-clock budget. The command stops between domains,
flushes each evidence row, and preserves input-file order:

```powershell
python -m si_domains check --input data/candidates.csv --max-minutes 30
```

Run the same command again to resume. Recorded results are skipped; pass
`--retry-unverified` to retry previously unverified domains. If the circuit
breaker opens, the runner waits 300 seconds by default, closes it, and resumes.
Set `--cooldown-seconds` to change that wait. Three consecutive cooldown cycles
without a successful registry result end the run with exit code 2 and an
unverified-domain count. A `--max-minutes` budget also covers cooldown time, so
the runner does not wait past the budget before stopping. Progress is printed
every 50 checked domains with a request rate and estimated time remaining.

`check` paces requests at 1.0 second by default. Set `--min-interval` to a
larger number of seconds to slow the run; values below 1.0 are rejected. Each
HTTP 429 raises the effective interval by 1.5 for the rest of that run, up to
5.0 seconds (or a higher configured interval), including retries. Retry-After
and exponential backoff waits are still honoured. The run totals include
requests per minute, HTTP 429 responses, and cooldown cycles.

Evidence is append-only. When `--retry-unverified` checks a domain again, its
new row is appended and becomes that domain's current result for `status` and
resume decisions; earlier evidence rows remain in the CSV.

`python -m si_domains status` reads the candidate CSV and
`output/rdap_evidence.csv` without making network requests. RDAP response bodies
are never saved; the evidence file contains only domain, category, HTTP status,
UTC timestamp, attempt count, classification, and a short error code.

## Second check (WHOIS)

Use the separate WHOIS channel on TCP port 43 to independently check domains
whose latest RDAP evidence is `potentially_unregistered`:

```powershell
python -m si_domains whois-check --input data/candidates.csv --limit 30
python -m si_domains status --input data/candidates.csv
```

The command follows candidate-file order and skips domains already recorded in
`output/whois_evidence.csv`. Run it again to resume a chunk; `--limit` bounds
the number of new checks, `--max-minutes` sets a wall-clock budget, and
`--retry-unverified` retries only domains whose latest WHOIS row is
`unverified`. The default interval is 2 seconds between connection starts and
values below 1 second are rejected. A timeout, connection error, or empty
response is retried in place for the same domain after 10 seconds and then
30 seconds, up to three attempts in one pass. The configured minimum interval
still applies between every connection start. Only the final result is written,
once per domain per pass; a domain whose three attempts fail is recorded as
`unverified` with its final body-free error code.

A rate-limit notice starts a cooldown immediately. Other `unverified` outcomes
start a cooldown only after three consecutive domains finish unverified. The
default cooldown is 300 seconds; three consecutive cooldown cycles without a
successful WHOIS classification stop the run with exit code 2. A rate-limit
notice or consecutive unverified results increase the interval by 1.5 up to
6 seconds. It decreases by 1.5 after each 50 consecutive successful checks,
down to the configured interval.

WHOIS response text is discarded after classification and is never written to
disk. The six evidence columns contain the domain, category, UTC timestamp,
classification, recognized pattern identifier, and a short error code; no
registrant or contact fields are retained. `status` reads both evidence files
without making network requests and reports confirmations, conflicts, and
pending WHOIS checks for RDAP 404s.

## Scoring and shortlist

`python -m si_domains score` reads `data/candidates.csv` and the latest rows in
`output/rdap_evidence.csv`, then writes deterministic heuristic scores for
RDAP-404 candidates to `output/scores.csv`. The score uses candidate category,
method, tags, quality score, and label. Its six weights are brandability 25%,
commercial relevance 20%, shortness 15%, domain-hack creativity 15%, resale
potential 15%, and trademark risk 10%. Scores do not use network access or
estimate sale prices. Unscreened candidates score 40 for trademark status and
carry a "not yet screened" note when no summary is supplied. To inject a
curated summary, pass `--trademark-evidence output/trademark_summary.csv`; the
command also validates its evidence IDs against
`output/trademark_evidence.csv` (override that path with
`--trademark-source-evidence`). Trademark maps to 85 for a complete limited
screen with no obvious match, 25 when a mark needs legal review, and 40 for
blocked, unverified, incomplete, or not-yet-screened states. Unknown risk is
penalized without renormalizing the weights. The weighted total is calculated
with decimal arithmetic and rounded once to one decimal using
`ROUND_HALF_EVEN` (ties to even). Commercial roots use per-name demand tiers
and buyer breadth; compounds combine head and tail. Length, syllables,
pronounceability, word/commonness, ambiguity, and root breadth differentiate
resale scores. These are buyer-breadth heuristics, not valuation evidence.

`python -m si_domains shortlist` combines the candidate CSV, latest RDAP and
WHOIS evidence, and `output/scores.csv`. Only domains with RDAP
`potentially_unregistered` and WHOIS `not_registered` enter
`output/shortlist.csv`; it is capped at 500 domains, with at most 100 per category
(20% of the shortlist).
Other candidates, including rule-based special classes and evidence conflicts,
are written to `output/excluded.csv` with a reason. A seeded sample of up to 30
RDAP-404 domains, including available WHOIS status groups, is written to
`output/sample_404_for_review.csv`; set `--seed` to reproduce another sample.

## PKG-B research artifacts and offline rebuild

Curated source records live in `output/valuation_evidence.csv` and
`output/trademark_evidence.csv`. The first records attributable completed-sale
reports, asking prices, and unavailable source pages separately. The second
records exact per-domain public database queries or a source-wide access
failure; a source-wide row says that no per-domain query ran. Candidate
metadata supplies the required normalized label query and, for domain hacks,
the completed seed phrase (for example, `tryto + see` normalizes to `try to see`).
A homepage URL with only a cosmetic parameter or fragment does not
prove a query. A query row may instead cite an existing screenshot or official
export using `proof_kind` (`screenshot` or `official_export`) and `proof_path`,
a relative path under `output/`; both optional columns remain backward
compatible with older evidence CSVs. Evidence stays linked to its row's exact
domain, source, and query. Human review is still required to inspect proof
contents. Do not turn an access attempt into a no-match result.
`output/valuation_sources_notes.md` records the sales research and
`output/research_methodology.md` explains the screening limits and validator
checks.

Use these commands to rebuild the research outputs without registry or
trademark network calls:

```powershell
# Build the initial screen, then re-score and rebuild the shortlist.
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
# Refresh the summary for the re-ranked top 100; repeat these three steps if
# the top-100 membership changes and newly entered names receive evidence.
python -m si_domains trademark-summary --shortlist output/shortlist.csv --candidates data/candidates.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
python -m si_domains valuations --shortlist output/shortlist.csv --evidence output/valuation_evidence.csv --out output/valuations.csv
python -m si_domains opportunities --shortlist output/shortlist.csv --scores output/scores.csv --valuations output/valuations.csv --trademark-summary output/trademark_summary.csv --out output/opportunities.csv
python -m si_domains validate-research --candidates data/candidates.csv
python -m si_domains validate-research --candidates data/candidates.csv --completion-mode
python -m si_domains export --out output/si_domains_ranked.xlsx
python scripts/build_html.py
```

If rescoring changes membership in the final top 100, complete the newly
entered names' public searches where the specified databases allow them, append
those evidence rows, and repeat summary, score, and shortlist until the target
set is current. The validator checks evidence references, status enums, score
arithmetic, final artifact domain/rank sets, range inputs, and top-100 query
coverage. It cannot establish that a cited source page was read correctly,
that a mark is legally relevant, or that a domain is legally clear; those need
human evidence review.

The 2026-10-13 T-17 screen stopped USPTO after HTTP 403 on `bankingdesk`.
PKG-G resumed after the cooldown with 117 sequential POSTs (one `google`
control and 116 candidate queries), all HTTP 200 JSON. The T-18 rework added
six requests (one control and five candidate queries), also all HTTP 200 JSON,
at least five seconds apart. Across both passes, 123 requests returned HTTP
200 JSON; there was no new 403, CAPTCHA, login, non-JSON response, timeout,
5xx, or retry. An earlier `powdery [fuzzy-1]` response had failed local ASCII
evidence writing; the parser now sanitizes distilled text as ASCII and the
query was re-run with its facts retained.

Final USPTO top-100 coverage is 100 complete, 0 query-blocked, and 0
unverified. The T-18 rework found possible conflicts for `powdery [fuzzy-1]`,
`denimwear` exact and fuzzy queries, and `soillab [fuzzy-1]`; `soillab` was
screened as the replacement entrant after `denimwear` left the top 100. The
new top-100 entrant/exiter versus the prior PKG-G set are `soillab` and
`denimwear`. Relative to T-17, entries are `examhub`, `bankingvault`,
`roboticlink`, `roboticloop`, `biomasshub`, `roboticflow`, and `biomasslab`;
exits are `robotsystem`, `gyration`, `crophub`, `croplab`, `agrihub`,
`cryptoworks`, and `parcelshop`.

The final top 100 flags 37 names for legal review, up from 24; the 13 newly
flagged names are `autokernel`, `autonetwork`, `autostream`, `carboncell`,
`cashops`, `jewelshop`, `keyscan`, `pharmascan`, `powdery`, `reveler`,
`robotspark`, `soilhub`, and `soillab`. `denimwear` also has possible-conflict
evidence but is outside the final top 100. The query records are limited
screening evidence; no name is cleared. Except for profitdesk.si, screened at the owner's request, names ranked 101-500 remain not yet screened by USPTO. The full final-top-100 flagged list is `autobeacon`, `autokernel`,
`autonetwork`, `autosearch`, `autostream`, `autoswitch`, `bankinghub`,
`carboncell`, `carbonhub`, `cashledger`, `cashops`, `cizo`, `cowhide`,
`creditdesk`, `datafleet`, `datalearn`, `dataledger`, `datasolve`,
`dataswitch`, `jewelshop`, `keyscan`, `leaning`, `ledgerlink`, `loanledger`,
`newsagen`, `paymentops`, `pharmascan`, `powdery`, `reveler`, `robotloop`,
`robotspark`, `soilhub`, `soillab`, `stoical`, `tryto`, `unfus`, and
`walletlink`.

RDAP and WHOIS outcomes are timestamped observations from the registry's
channels. They are not registrar checkout confirmation and do not guarantee
registration eligibility, registration success, or a non-premium price.

## Manual trademark checks the owner can do

The official search pages are [TMview](https://www.tmdn.org/tmview/),
[UKIPO](https://trademarks.ipo.gov.uk/ipo-tmtext), and
[USPTO](https://tmsearch.uspto.gov/). TMview source-wide refused: connection closed (evidence
`REWORK1-TMVIEW-PROBES`, 2026-10-13T18:02:42Z); per-name results are unverified
because of that refusal. UKIPO source-wide refused: automated access refused
(evidence `PKGD-0003`, 2026-10-13T17:09:52Z); per-name results are blocked
because of that refusal. No further TMview or UKIPO
attempts were made. USPTO screening stopped after one HTTP 403 at
2026-10-13T18:05:11Z (`REWORK1-USPTO-00259`, source-stop record
`REWORK1-USPTO-SOURCE-STOP`). PKG-G and the T-18 rework made 123 USPTO POSTs
across two controls and 121 candidate queries; all returned HTTP 200 JSON,
with no new 403 or retry. Final USPTO coverage is 100/100 complete. PKGH added one google control and exact/fuzzy-1 queries for profitdesk.si on 2026-10-14; all three returned HTTP 200 JSON at least five seconds apart, and both candidate queries returned zero matches. Profitdesk was screened at the owner's request and is the sole outside-top-100 USPTO screen; all other outside-top-100 names remain not yet screened by USPTO. No result is a trademark clearance.
