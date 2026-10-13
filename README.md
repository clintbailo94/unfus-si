# AI

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
