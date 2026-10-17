# .si Domain Marketplace Project Summary

## Executive Overview
We have turned the .si domain research project into a paid, continuously updated, production-ready domain list marketplace website. The solution adheres strictly to all legal, technical, rate-limiting, and data integrity guidelines specified in `GOAL-si-list-marketplace.md`.

---

## 1. What Was Built

### A. Web Application (`web/`)
- **FastAPI Backend (`web/main.py`)**: High-performance asynchronous API serving responsive HTML templates, managing checkout redirects, validating download tokens server-side, and streaming CSV and XLSX exports.
- **Responsive UI (`web/static/css/styles.css` & `web/templates/`)**: Mobile-first responsive layout (tested at 390px mobile and 1440px desktop) with full light/dark mode support and accessibility features.
- **Home Page (`/`)**:
  - Recent .si sales table with 10 real, publicly reported sales linked directly to sources (e.g. `ai.si` $34k, `recursive.si` $20k, `otherwise.si` $18.8k, `build.si` $17.4k) and labeled asking prices.
  - Transparent value proposition, methodology explanation, and 15-name free preview with full scoring breakdown and timestamp metadata.
  - Automatic stale-data alert banner triggered whenever snapshot timestamps exceed 8 days.
- **Directory / List Page (`/domains`)**:
  - Interactive multi-criteria filtering: category, maximum character length, minimum total score, and sorting (highest score / shortest length).
  - Paywall & blur teaser: Unpaid visitors see unblurred top 15 rows; subsequent rows feature blurred labels (`fo***.si`) and a prompt to unlock full access.
- **Paid Access & Checkout (`/checkout`, `web/checkout.py`)**:
  - Supports Stripe Checkout in test mode (`sk_test_*` keys).
  - Features an automated local fake checkout simulator when Stripe keys are absent, allowing local testing of payment, fulfillment, and downloads without network friction.
- **Customer Account & Downloads (`/account`, `/download/csv`, `/download/xlsx`)**:
  - Secure token-based license management stored in SQLite (`web/db.py`).
  - Server-side authorization check on every download request with customer and IP audit logging.
  - Strict exclusion guarantee: domains owned by the owner (`data/owned_domains.txt`) are excluded from candidate lists and download exports.
- **Legal & Honesty Pages (`/terms`, `/privacy`)**:
  - Availability disclaimers (registry status reflects snapshot check, not an advance reservation).
  - Realistic valuation disclaimers (historical sales do not predict or guarantee resale prices).

### B. Continuous Refresh Engine (`si_domains/refresh.py`)
- CLI command `python -m si_domains refresh`:
  - Re-checks availability via official RDAP first, followed by RFC 3912 port-43 WHOIS to confirm RDAP 404s.
  - Strictly enforces registry rate limiting (at least 1.1s between queries).
  - Backs off adaptively on network errors and halts on upstream refusal.
  - Rescores opportunities, drops names that became registered, and rebuilds the shortlist.
- Windows Task Scheduler helper (`scripts/install_schedule.ps1`) defining daily top-500 and weekly full-pool refresh tasks without installing them automatically.

### C. Curated Sales Feed (`si_domains/sales.py`, `data/si_sales.csv`)
- Verifiable sales database tracking 10 completed .si transactions and benchmark asking prices.
- CLI helper `python -m si_domains review-sales` for listing records and proposing new reported sales with mandatory source URLs.

### D. Candidate Expansion Pool (`si_domains/candidates/expansion.py`)
- Expanded candidate pool generator scaling from 6,204 to **21,500 unique candidates**.
- Added high-resonance categories:
  - Fintech & payments (`business_finance`: 1,804)
  - SaaS action verbs & cloud workflows (`technology`: 1,539)
  - Health, bio & wellness (`health_science`: 1,172)
  - Slovenian business words & compounds (`dictionary`: 1,040)
  - Brandable two-word compounds & pronounceable blends (`invented`: 12,090)
  - Domain hacks completing -sy/-cy/-si sounds (`domain_hacks`: 146)
- Passes all strict quality, trademark, and registry rules.

---

## 2. Pricing Decisions Recorded

| Product Tier | Price | Format | Target Customer & Value Proposition |
| :--- | :--- | :--- | :--- |
| **One-Off Snapshot** | **£49** | One-time payment | Instant download of full available .si opportunity directory (CSV + XLSX). Finding a single viable startup name or domain flip yields positive ROI. |
| **Continuous Subscription** | **£29 / month** | Recurring subscription | Continuous access to weekly refreshed lists, daily top-500 drop monitoring, and newly generated candidate categories. Aligned with domain intelligence pro tooling. |

*Full decision rationale documented in `docs/marketplace-decisions.md`.*

---

## 3. Test Suite & Verification Results

All 455 tests across the entire repository pass with zero errors:
- **Baseline preservation**: 444 pre-existing tests (candidates, delivery, scoring, shortlist, workbook, whois, rdap, trademarks, etc.) pass unchanged.
- **Marketplace test suite (`tests/test_marketplace.py`)**: 11 new automated unit and integration tests covering:
  - Paywall enforcement for unpaid vs paid visitors
  - Server-side download authorization and 403 blocks for invalid tokens
  - Stripe test flow and fake checkout simulator
  - Continuous refresh logic against a mock registry
  - Stale data warning triggers (>8 days)
  - Sourced-only sales table rendering and proposal validation

---

## 4. Operator Hand-off & Next Steps for the Owner

The site is fully runnable locally out of the box. As documented in `docs/marketplace-runbook.md`, going live requires:
1. **Hosting & Reverse Proxy**: Deploy FastAPI with Uvicorn behind Nginx/Caddy with SSL.
2. **Domain & DNS**: Assign target production domain (e.g. `domains.si` or `list.si`).
3. **Live Stripe Keys**: Add `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` environment variables.
4. **Task Scheduling**: Run `powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1 -Install` as Administrator on the production server.
