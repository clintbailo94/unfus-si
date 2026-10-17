"""FastAPI application serving the .si domain marketplace website."""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import dotenv
dotenv.load_dotenv()

from si_domains.config import DATA_DIR, OUTPUT_DIR
from si_domains.sales import get_verified_completed_sales, load_sales
from . import db
from .checkout import PRICES, create_checkout_session, fulfill_stripe_session
from .db import init_db, record_download, verify_access_token


app = FastAPI(title=".si Domain Marketplace")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
HOSTINGER_AFFILIATE_URL = os.getenv("HOSTINGER_AFFILIATE_URL", "https://www.hostinger.com/uk?REFERRALCODE=Q8QCLINTB2AY").strip()
HOSTINGER_REFERRAL_CODE = os.getenv("HOSTINGER_REFERRAL_CODE", "Q8QCLINTB2AY").strip()

def get_hostinger_url(domain_name: Optional[str] = None) -> str:
    """Build Hostinger affiliate link with referral tracking code."""
    if domain_name:
        return f"https://www.hostinger.com/domain-name-search?domain={domain_name}&REFERRALCODE={HOSTINGER_REFERRAL_CODE}"
    return HOSTINGER_AFFILIATE_URL

templates.env.globals["hostinger_affiliate_url"] = HOSTINGER_AFFILIATE_URL
templates.env.globals["get_hostinger_url"] = get_hostinger_url

# Ensure database tables exist immediately on import
init_db()


@app.on_event("startup")
def on_startup():
    init_db()


def get_snapshot_age_info() -> tuple[str, bool]:
    """Return (last_checked_timestamp, is_stale). Stale if > 8 days."""
    rdap_path = OUTPUT_DIR / "rdap_evidence.csv"
    last_dt: Optional[datetime] = None
    last_str = ""

    if rdap_path.is_file():
        try:
            with rdap_path.open("r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ts = row.get("utc_timestamp", "").strip()
                    if ts:
                        last_str = ts
        except Exception:
            pass

    if last_str:
        try:
            # Parse ISO timestamp
            clean_ts = last_str.replace("Z", "+00:00")
            last_dt = datetime.fromisoformat(clean_ts)
        except Exception:
            pass

    if last_dt is None:
        return ("2026-10-13T09:46:53Z", True)

    now = datetime.now(timezone.utc)
    is_stale = (now - last_dt) > timedelta(days=8)
    return (last_str, is_stale)


def get_owned_domain_set() -> set[str]:
    owned_path = DATA_DIR / "owned_domains.txt"
    if not owned_path.is_file():
        return set()
    with owned_path.open("r", encoding="utf-8") as f:
        return {
            line.split(",")[0].strip().lower()
            for line in f
            if line.strip() and not line.startswith("#")
        }


def load_opportunity_rows() -> list[dict]:
    opp_path = OUTPUT_DIR / "opportunities.csv"
    if not opp_path.is_file():
        # Fall back to shortlist.csv if opportunities.csv is not present
        opp_path = OUTPUT_DIR / "shortlist.csv"
    if not opp_path.is_file():
        return []

    owned = get_owned_domain_set()
    domains: list[dict] = []
    with opp_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = (row.get("domain") or "").strip().lower()
            if not domain or domain in owned:
                continue  # Never include owned domains!
            label = domain.replace(".si", "")
            domains.append({
                "rank": row.get("rank", ""),
                "domain": domain,
                "label": label,
                "length": len(label),
                "category": row.get("category", ""),
                "total": row.get("total", ""),
                "brandability": row.get("brandability", ""),
                "commercial": row.get("commercial", ""),
                "shortness": row.get("shortness", ""),
                "resale": row.get("resale", ""),
                "trademark": row.get("trademark", ""),
                "rationale": row.get("rationale", ""),
                "checked_time": row.get("whois_timestamp") or row.get("rdap_timestamp") or "",
            })
    return domains


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    last_checked, is_stale = get_snapshot_age_info()
    sales = load_sales()  # Includes both verified sales and labeled ask prices
    all_domains = load_opportunity_rows()
    sample_domains = all_domains[:15]

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "sales": sales,
            "sample_domains": sample_domains,
            "last_checked": last_checked,
            "is_stale": is_stale,
        },
    )


@app.get("/domains", response_class=HTMLResponse)
async def domains_page(
    request: Request,
    token: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    max_length: Optional[int] = Query(None),
    min_score: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("score_desc"),
):
    last_checked, is_stale = get_snapshot_age_info()
    has_paid = bool(db.verify_access_token(token)) if token else False
    all_domains = load_opportunity_rows()

    # Extract available categories
    categories = sorted({d["category"] for d in all_domains if d["category"]})

    # Apply filters
    filtered = all_domains
    if category:
        filtered = [d for d in filtered if d["category"] == category]
    if max_length:
        filtered = [d for d in filtered if d["length"] <= max_length]
    if min_score:
        filtered = [d for d in filtered if float(d["total"] or 0) >= min_score]

    # Apply sorting
    if sort_by == "length_asc":
        filtered.sort(key=lambda d: (d["length"], -float(d["total"] or 0)))
    else:  # score_desc
        filtered.sort(key=lambda d: (-float(d["total"] or 0), d["length"]))

    # Prepare rows with blur/teaser for unpaid visitors
    view_rows = []
    for idx, d in enumerate(filtered, start=1):
        is_locked = (not has_paid) and (idx > 15)
        teaser_name = f"{d['label'][:2]}***.si" if is_locked else d["domain"]
        view_rows.append({
            **d,
            "is_locked": is_locked,
            "teaser_name": teaser_name,
        })

    return templates.TemplateResponse(
        request=request,
        name="list.html",
        context={
            "domains": view_rows,
            "categories": categories,
            "selected_category": category or "",
            "selected_max_length": max_length,
            "selected_min_score": min_score,
            "sort_by": sort_by,
            "has_paid": has_paid,
            "last_checked": last_checked,
            "is_stale": is_stale,
        },
    )


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    last_checked, is_stale = get_snapshot_age_info()
    return templates.TemplateResponse(
        request=request,
        name="pricing.html",
        context={
            "last_checked": last_checked,
            "is_stale": is_stale,
        },
    )


@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, tier: str = Query("one_off")):
    if tier not in PRICES:
        tier = "one_off"
    last_checked, is_stale = get_snapshot_age_info()
    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={
            "tier": tier,
            "product": PRICES[tier],
            "last_checked": last_checked,
            "is_stale": is_stale,
        },
    )


@app.post("/checkout")
async def process_checkout(
    request: Request,
    tier: str = Form("one_off"),
    email: str = Form(...),
):
    host_url = str(request.base_url).rstrip("/")
    success_url = f"{host_url}/account?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/pricing"

    result = create_checkout_session(
        tier=tier,
        customer_email=email,
        success_url_template=success_url,
        cancel_url=cancel_url,
    )
    return RedirectResponse(url=result["checkout_url"], status_code=303)


@app.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    token: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
):
    last_checked, is_stale = get_snapshot_age_info()
    order = None

    if token:
        order = db.verify_access_token(token)
    elif session_id:
        order = fulfill_stripe_session(session_id)
        if order and not token:
            # Redirect to clean URL with access token
            return RedirectResponse(url=f"/account?token={order['access_token']}", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "order": order,
            "request_url": str(request.url),
            "last_checked": last_checked,
            "is_stale": is_stale,
        },
    )


@app.get("/download/csv")
async def download_csv(
    request: Request,
    token: str = Query(...),
):
    order = db.verify_access_token(token)
    if not order:
        raise HTTPException(status_code=403, detail="Invalid or unpaid access token")

    client_ip = request.client.host if request.client else ""
    db.record_download(order["id"], "csv", ip_address=client_ip)

    # Stream clean CSV without owned domains
    all_domains = load_opportunity_rows()
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["rank", "domain", "category", "total", "brandability", "commercial", "shortness", "resale", "trademark", "rationale", "checked_time"],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in all_domains:
        writer.writerow({
            "rank": row["rank"],
            "domain": row["domain"],
            "category": row["category"],
            "total": row["total"],
            "brandability": row["brandability"],
            "commercial": row["commercial"],
            "shortness": row["shortness"],
            "resale": row["resale"],
            "trademark": row["trademark"],
            "rationale": row["rationale"],
            "checked_time": row["checked_time"],
        })

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="si_available_domains.csv"'},
    )


@app.get("/download/xlsx")
async def download_xlsx(
    request: Request,
    token: str = Query(...),
):
    order = db.verify_access_token(token)
    if not order:
        raise HTTPException(status_code=403, detail="Invalid or unpaid access token")

    xlsx_path = OUTPUT_DIR / "si_domains_ranked.xlsx"
    if not xlsx_path.is_file():
        raise HTTPException(status_code=404, detail="XLSX workbook snapshot not found on server")

    client_ip = request.client.host if request.client else ""
    db.record_download(order["id"], "xlsx", ip_address=client_ip)

    return FileResponse(
        path=str(xlsx_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="si_domains_ranked.xlsx",
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms_page(request: Request):
    last_checked, is_stale = get_snapshot_age_info()
    return templates.TemplateResponse(request=request, name="terms.html", context={"last_checked": last_checked, "is_stale": is_stale})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    last_checked, is_stale = get_snapshot_age_info()
    return templates.TemplateResponse(request=request, name="privacy.html", context={"last_checked": last_checked, "is_stale": is_stale})
