# PKG-B research methodology

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

## Public trademark search attempt and limits

The target was the pre-rescoring top 100, then the final top 100 after
re-scoring. The member sets were identical, so there were no newly entered
names to search. The available browser inventory was empty and the in-app
browser was unavailable. The official-page fetches did not expose a usable
search UI, so **no exact label or completed seed phrase was queried for any
domain**. No mark match or no-match result was invented.

The source-wide access evidence records:

- **TMview:** official page fetches returned HTML with zero extractable text
  lines. Status is `unverified`; no per-domain query ran.
- **UKIPO:** the first fetch returned **HTTP 403 Forbidden**. It was not retried.
  The tool transcript did not retain the original request-time timestamp; the
  evidence timestamp records when that outcome was captured, and the limitation
  is stated in the row. No per-domain query ran.
- **USPTO Trademark Search:** official page fetches returned a page title but
  zero extractable text lines. Status is `unverified`; no per-domain query ran.

Each source-wide record is linked by ID from the 100 affected summary rows, but
is not counted as a completed query. Current top-100 per-source counts are:

| Source | Completed per-domain queries | Blocked top-100 domains | Unverified top-100 domains |
| --- | ---: | ---: | ---: |
| TMview | 0 | 0 | 100 |
| UKIPO | 0 | 100 | 0 |
| USPTO | 0 | 0 | 100 |

These are domain coverage counts, not counts of attempted per-domain requests.
For example, UKIPO's 100 blocked domains are affected by one source-wide 403
record; no 100 individual requests were made.

All 100 summary rows therefore remain `unverified` at the conservative score
of 70. The other 400 shortlist names have no summary row and remain explicitly
`not yet screened` in `opportunities.csv`; the scoring rationale retains the
baseline placeholder note for those names. No domain received an 80-point
no-obvious-match increase. The exact-word query, similar marks, status,
classes, and sector relevance cannot be assessed until a public UI query is
completed. A later `possible_conflict` requires professional legal review;
expired marks are contextual, and this pipeline never declares a name legally
safe or cleared.

The screening rubric is limited to exact labels and recorded seed phrases,
plus similarity checks exposed by the public UI when available. It does not
claim comprehensive phonetic, class, national-office, or worldwide coverage.
Trademark scores are ranking heuristics, not legal probabilities or legal
advice.

## Offline build and validation

After updating the curated evidence CSVs with actual sourced records, rebuild
in this order:

```powershell
python -m si_domains trademark-summary --shortlist output/shortlist.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
python -m si_domains trademark-summary --shortlist output/shortlist.csv --evidence output/trademark_evidence.csv --out output/trademark_summary.csv --top-n 100
python -m si_domains score --trademark-evidence output/trademark_summary.csv --trademark-source-evidence output/trademark_evidence.csv
python -m si_domains shortlist
python -m si_domains valuations --shortlist output/shortlist.csv --evidence output/valuation_evidence.csv --out output/valuations.csv
python -m si_domains opportunities --shortlist output/shortlist.csv --scores output/scores.csv --valuations output/valuations.csv --trademark-summary output/trademark_summary.csv --out output/opportunities.csv
python -m si_domains validate-research
```

After each re-score, compare the final top-100 domain set to the summary. Search
new entrants where an official source permits a query, add per-domain evidence,
and repeat until membership is current. Do not fill a blocked source with
synthetic result rows.

The validator checks CSV schemas, duplicate IDs/domains, score arithmetic with
the exact configured weights, shortlist/valuation/opportunity domain and rank
sets, numeric range currencies and eligible completed-sale references,
trademark statuses and evidence mappings, and query coverage of the final top
100. It reports source-wide access failures separately from completed queries
and exits unsuccessfully when required coverage remains unresolved. These are
structural checks: a reviewer must still inspect the cited public pages and
decide whether a sale is genuinely comparable or a mark is relevant and
current.

RDAP `potentially_unregistered` and WHOIS `not_registered` are timestamped
observations from two registry channels. They are not registrar checkout
confirmation, registration eligibility, a guarantee that registration will
succeed, or a guarantee of a non-premium price. Existing candidate, RDAP, and
WHOIS evidence was not changed by this research step.
