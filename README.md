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

`python -m si_domains status` reads the candidate CSV and
`output/rdap_evidence.csv` without making network requests. RDAP response bodies
are never saved; the evidence file contains only domain, category, HTTP status,
UTC timestamp, attempt count, classification, and a short error code.
