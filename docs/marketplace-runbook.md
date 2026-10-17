# .si Domain Marketplace Runbook

This guide explains how to operate the .si domain intelligence marketplace website, run availability refresh sweeps against the registry, install the automated scheduler, and prepare the site for production. Written for non-developers and operators.

---

## 1. Running the Site Locally

The marketplace is built using FastAPI and Python 3.12.

### Start the Server:
Open PowerShell or your command prompt in the project root (`D:\projects\AI`) and run:
```powershell
python -m si_domains serve
```
By default, the server runs at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Available URLs:
- **Home Page**: `http://127.0.0.1:8000/` (Includes recent reported .si sales, features overview, and free 15-name sample)
- **Available Domain Directory**: `http://127.0.0.1:8000/domains` (Search, filter by length/category/score, and view score breakdown. Unpaid visitors see rows after #15 blurred)
- **Pricing & Plans**: `http://127.0.0.1:8000/pricing` (One-off £49 and Subscription £29/mo)
- **Checkout**: `http://127.0.0.1:8000/checkout?tier=one_off` (Runs in test/fake simulator when live keys are absent)
- **Customer Account & Downloads**: `http://127.0.0.1:8000/account` (Enter access token to download CSV / XLSX)
- **Legal Pages**:
  - `http://127.0.0.1:8000/terms` (Terms of service & availability disclaimer)
  - `http://127.0.0.1:8000/privacy` (Privacy policy & data usage)

---

## 2. Refreshing Domain Availability

The repository includes an automated refresh engine that verifies currently unregistered domains against the official registry using RDAP and WHOIS.

### Running a Refresh:
To run an automated refresh:
```powershell
# Bounded test refresh of the first 25 names:
python -m si_domains refresh --limit 25

# Full refresh of candidates:
python -m si_domains refresh --min-interval 1.1
```

### Safety & Rate-Limiting Guarantees:
- **Registry Rate Limit**: Enforces at least 1.1 seconds between consecutive registry requests.
- **Two-Pass Verification**: RDAP is checked first; WHOIS is used strictly to confirm RDAP 404s.
- **Error Backoff & Refusal Halts**: Automatically pauses on network hiccups and terminates immediately upon receiving an upstream rate limit or query block.
- **Pipeline Rebuild**: Automatically rescores candidate opportunities, removes names that have been registered by others, and rebuilds the top shortlist.

---

## 3. Managing the Sales Feed

The marketplace homepage headlines verified, publicly reported .si sales from `data/si_sales.csv`.

### Review Existing Sales:
```powershell
python -m si_domains review-sales
```

### Propose a New Reported Sale:
Before any sale is displayed, it must be verified with an official source URL:
```powershell
python -m si_domains review-sales --domain "brand.si" --amount "15000" --currency "USD" --source-url "https://domainnamewire.com/report-link" --venue "Sedo"
```
*Never record asking prices as completed sales.* Asking prices must be designated with `--type asking_price`.

---

## 4. Scheduling Automated Refreshes (Windows Task Scheduler)

A PowerShell script is provided to define the daily and weekly refresh jobs:
- **Daily Top 500 Refresh**: Runs daily at 03:00 AM UTC.
- **Weekly Full Pool Refresh**: Runs Sundays at 01:00 AM UTC.

### View Schedule Definition:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1
```

### Installing Tasks (Administrator Required):
When you are ready to automate on a server or workstation:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1 -Install
```

### Uninstalling Tasks:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_schedule.ps1 -Uninstall
```

---

## 5. Going Live Checklist

When moving from local testing to a public production deployment:

1. **Production Domain & DNS**:
   - Point your target domain (e.g., `list.si` or `domains.si`) via DNS A/CNAME records to your server.
2. **Reverse Proxy & SSL**:
   - Deploy behind a production web server (Nginx or Caddy) with automated Let's Encrypt SSL certificates.
   - Run FastAPI with Uvicorn behind the proxy: `uvicorn web.main:app --host 127.0.0.1 --port 8000 --workers 4`.
3. **Stripe Production Keys**:
   - Set the environment variables on the production server:
     ```bash
     export STRIPE_SECRET_KEY="sk_live_..."
     export STRIPE_PUBLISHABLE_KEY="pk_live_..."
     ```
   - In Stripe Dashboard, configure the webhook endpoint to point to `https://yourdomain.com/webhook` to handle asynchronous subscription lifecycle events.
4. **Data Freshness**:
   - Run the initial baseline refresh to update the `rdap_evidence.csv` and `whois_evidence.csv` timestamps so the site displays fresh timestamps without a stale-data warning.
