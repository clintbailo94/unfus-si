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
python -m si_domains validate-delivery --workbook output/si_domains_ranked.xlsx
```

`validate-delivery` compares every workbook row and cell to the current sources.
It can report structural delivery PASS while saying research screening BLOCKED;
`python -m si_domains validate-research --candidates data/candidates.csv`
remains separate and exits 2 while the required top-100 trademark query sets
are unresolved. Neither command certifies project completion or owner acceptance.

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
estimate sale prices. Trademark is a fixed placeholder score of 70 with a
"not yet screened" note when no trademark summary is supplied. To inject a
curated summary, pass `--trademark-evidence output/trademark_summary.csv`; the
command also validates its evidence IDs against
`output/trademark_evidence.csv` (override that path with
`--trademark-source-evidence`). Screened rows show their limited, review-needed,
blocked, or unverified state in the rationale. The weighted total is
calculated with decimal arithmetic and rounded once to one decimal using
`ROUND_HALF_EVEN` (ties to even). Commercial keyword bonuses require exact tags,
labels, or recorded seed components. Resale uses curated common-noun and
low-breadth dictionary signals plus reviewed hack-seed adjustments; these are
buyer-breadth heuristics, not valuation evidence.

`python -m si_domains shortlist` combines the candidate CSV, latest RDAP and
WHOIS evidence, and `output/scores.csv`. Only domains with RDAP
`potentially_unregistered` and WHOIS `not_registered` enter
`output/shortlist.csv`; it is capped at 500 domains, with at most 125 per category.
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
```

If rescoring changes membership in the final top 100, complete the newly
entered names' public searches where the specified databases allow them, append
those evidence rows, and repeat summary, score, and shortlist until the target
set is current. The validator checks evidence references, status enums, score
arithmetic, final artifact domain/rank sets, range inputs, and top-100 query
coverage. It cannot establish that a cited source page was read correctly,
that a mark is legally relevant, or that a domain is legally clear; those need
human evidence review.

For the 2026-10-13 research snapshot, TMview has 0/100 completed required-query
sets and 100 unverified domains; UKIPO has 0/100 completed sets and 100 domains
affected by one source-wide HTTP 403; USPTO has 0/100 completed sets and 100
unverified domains. An independent browser-surface check returned `apps=[]`,
`browsers=[]`, and
`Browser is not available: iab` for an in-app browser attempt. No per-domain
search ran. The validator therefore reports structural checks as passed, marks
query coverage BLOCKED, and exits non-zero; a source-wide access attempt never
counts as a completed query.

RDAP and WHOIS outcomes are timestamped observations from the registry's
channels. They are not registrar checkout confirmation and do not guarantee
registration eligibility, registration success, or a non-premium price.
