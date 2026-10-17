# Marketplace Product Decisions

This document records architectural, pricing, legal, and design decisions made for turning the .si domain research into a paid, continuously updated domain-list product, per `GOAL-si-list-marketplace.md`.

---

## 1. Pricing Decisions

### Offers and Tiers:
- **One-off Snapshot Download (CSV + XLSX)**: **£49** (one-time payment)
  - **Rationale**: For independent domainers, early-stage startup founders, and agencies looking for a curated collection of available .si names right now. At £49, finding a single valuable name (e.g., comparable to real 4-figure/5-figure sales like `build.si` at $17.4k, `byte.si` at $3.5k, `otherwise.si` at $18.8k) yields an immediate ROI. It lowers friction while valuing the deep verification and scoring methodology.
- **Continuous Access Subscription (Weekly Fresh Lists & Daily Top 500)**: **£29/month**
  - **Rationale**: Domain drops, expirations, and registry changes happen continuously. Serious domain investors and naming consultants require weekly fresh snapshots, newly generated categories, and daily top-500 change tracking before anyone else registers them. £29/month aligns with standard B2B domain/SEO intelligence tooling (e.g., ExpiredDomains pro subscriptions or DomainTools basic tiers), providing recurring cashflow while remaining accessible.

---

## 2. Architecture & File Layout

- **Package & Web Structure**:
  - Web application located in `web/`:
    - `web/main.py`: FastAPI server with clean HTML rendering, authentication via session tokens, Stripe checkout integration (test/fake mode), and secure file download streaming.
    - `web/templates/`: Jinja2 semantic HTML templates (home, list, legal pages, checkout, account/downloads).
    - `web/static/`: Accessible CSS (light/dark theme, responsive at 390px mobile and 1440px desktop) and minimal progressive vanilla JS (filtering, sorting, tab switching).
    - `web/db.py`: SQLite storage for customer orders, licenses, subscriptions, and download audit logs.
  - Core logic retained in `si_domains/`:
    - Candidate generation (`si_domains/candidates/`)
    - Refresh engine (`si_domains/refresh.py`)
    - Sales feed & review helper (`si_domains/sales.py`)
    - CLI entry point extended (`si_domains/cli.py` with `refresh` and `serve` commands)

---

## 3. Data Integrity & Ownership

- **Never Sell Owned Domains**:
  - `data/owned_domains.txt` contains domains acquired by the owner (`datasolve.si`, `profitdesk.si`, `fuve.si`, `guza.si`, `datafleet.si`, `datalearn.si`, `autosearch.si`, `agentlearn.si`, `unfus.si`, `newsagen.si`).
  - These domains are explicitly stripped from any public candidate listing, sample, full download, or paid access view.
- **Availability Disclaimer**:
  - Public listings clearly display "Last checked: <timestamp> UTC" and state that registry availability is based on the snapshot and is not a guaranteed reservation.
  - Stale data older than 8 days displays an automated caution banner.

---

## 4. Sales Evidence Integrity

- **Sourced-Only Policy**:
  - `data/si_sales.csv` is the single source of truth for public sales, derived strictly from verifiable public records (e.g., `output/valuation_evidence.csv` and verified reports).
  - Unverified sales or asking prices are never presented as completed transactions.
  - Asking prices (e.g. `build.si` at $10M or `seed.si` at $8M) are clearly labeled as asking prices for context only, never as sales.
  - New candidate sales from reports require verification before publishing via the helper (`python -m si_domains review-sales`).

---

## 5. Stripe Flow & Test Mode

- **Test Keys and Fallback**:
  - The application reads `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` from the environment.
  - In absence of live/test Stripe keys or in offline testing, an automated "Fake Checkout" simulator allows testing the entire payment -> webhook / fulfillment -> account access -> download lifecycle locally without network dependencies or real transactions.
  - Real transactions and live keys are strictly prohibited in development.

---

## 6. Candidate Expansion Strategy (20,000+ pool)

- Maintain the strict quality, trademark, syntax, and blocklist gates from `si_domains.candidates.quality`.
- Expand vocabulary across key requested themes:
  - SaaS & tech action verbs + prefixes
  - Finance / Fintech terms
  - Health / Wellness / Bio terms
  - Slovenian high-resonance business terms
  - Two-word brandables
  - Pronounceable .si domain hacks (words ending in -si / -sy / -cy sounds)
- Retain existing accepted candidate output while expanding secondary generation tiers to scale to over 20,000 clean candidates.
