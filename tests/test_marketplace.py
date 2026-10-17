"""Tests for marketplace features: paywall, download access, fake/test checkout,

refresh logic with fake registry, stale-data warning, and sales table rendering.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from web.checkout import create_checkout_session, PRICES
from web.db import create_order, init_db, verify_access_token
from web.main import app, get_snapshot_age_info
from si_domains.rdap import Result as RdapResult
from si_domains.refresh import run_refresh
from si_domains.sales import get_verified_completed_sales, load_sales, propose_sale
from si_domains.whois import WhoisResult


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_marketplace.db"
    init_db(test_db)
    monkeypatch.setattr("web.db.DB_PATH", test_db)
    monkeypatch.setattr("web.main.db.DB_PATH", test_db)
    monkeypatch.setattr("web.main.init_db", lambda: None)
    return TestClient(app)


# 1. Paywall enforcement tests
def test_paywall_enforcement_unpaid_visitor(client):
    response = client.get("/domains")
    assert response.status_code == 200
    # Rows after 15 should be blurred/teaser
    assert "***.si" in response.text
    assert "Unlock Remaining Names" in response.text


def test_paywall_enforcement_paid_visitor(client, tmp_path):
    order = create_order("paid_user@example.com", "one_off", 49, status="paid", db_path=tmp_path / "test_marketplace.db")
    token = order["access_token"]

    response = client.get(f"/domains?token={token}")
    assert response.status_code == 200
    assert "My Downloads Portal" in response.text
    # Blur teaser prompt should not appear
    assert "Unlock Remaining Names" not in response.text


# 2. Server-side download access verification
def test_download_access_unauthorized(client):
    res_csv = client.get("/download/csv?token=bad_token")
    assert res_csv.status_code == 403
    assert "Invalid or unpaid" in res_csv.text

    res_xlsx = client.get("/download/xlsx?token=bad_token")
    assert res_xlsx.status_code == 403


def test_download_access_authorized(client, tmp_path):
    order = create_order("downloader@example.com", "one_off", 49, status="paid", db_path=tmp_path / "test_marketplace.db")
    token = order["access_token"]

    res_csv = client.get(f"/download/csv?token={token}")
    assert res_csv.status_code == 200
    assert res_csv.headers["content-type"].startswith("text/csv")
    assert "domain,category,total" in res_csv.text

    # Verify owned domains are NEVER in the download
    assert "datasolve.si" not in res_csv.text
    assert "profitdesk.si" not in res_csv.text
    assert "fuve.si" not in res_csv.text


# 3. Stripe fake / test flow
def test_checkout_fake_simulator_flow(client, monkeypatch):
    import web.checkout as chk
    monkeypatch.setattr(chk, "is_stripe_configured", lambda: False)
    res = client.post("/checkout", data={"tier": "one_off", "email": "testbuyer@example.com"}, follow_redirects=False)
    assert res.status_code == 303
    loc = res.headers["location"]
    assert "token=" in loc

    token = loc.split("token=")[1]
    verified = verify_access_token(token)
    assert verified is not None
    assert verified["email"] == "testbuyer@example.com"
    assert verified["amount_gbp"] == 49


def test_stripe_test_mode_dispatch(monkeypatch):
    import web.checkout as chk
    monkeypatch.setattr(chk, "STRIPE_SECRET_KEY", "sk_test_1234567890")
    monkeypatch.setattr(chk.stripe.checkout.Session, "create", lambda **kwargs: MagicMock(url="https://checkout.stripe.com/test", id="cs_test_123"))

    result = chk.create_checkout_session("one_off", "buyer@example.com", "https://example.com/ok", "https://example.com/cancel")
    assert result["mode"] == "stripe_test"
    assert result["checkout_url"] == "https://checkout.stripe.com/test"


# 4. Refresh logic with fake registry
def test_refresh_with_fake_registry(tmp_path):
    candidates_csv = tmp_path / "cands.csv"
    candidates_csv.write_text("domain_label,category,method,seed,tags,quality_score\nfoo,ai,compound,foo+bar,,80\nbar,technology,compound,bar+baz,,75\n", encoding="utf-8")

    rdap_csv = tmp_path / "rdap.csv"
    whois_csv = tmp_path / "whois.csv"
    scores_csv = tmp_path / "scores.csv"
    shortlist_csv = tmp_path / "shortlist.csv"
    excluded_csv = tmp_path / "excluded.csv"
    sample_csv = tmp_path / "sample.csv"

    def fake_rdap(label, category):
        if label == "foo":
            return RdapResult(domain="foo.si", http_status=404, utc_timestamp="2026-10-17T12:00:00Z", attempts=1, classification="potentially_unregistered")
        return RdapResult(domain="bar.si", http_status=200, utc_timestamp="2026-10-17T12:00:00Z", attempts=1, classification="registered")

    def fake_whois(label, category):
        return WhoisResult(domain=f"{label}.si", classification="not_registered", utc_timestamp="2026-10-17T12:00:05Z", matched_pattern="no_entries_found")

    res = run_refresh(
        candidates_path=candidates_csv,
        rdap_path=rdap_csv,
        whois_path=whois_csv,
        scores_path=scores_csv,
        shortlist_path=shortlist_csv,
        excluded_path=excluded_csv,
        sample_path=sample_csv,
        rdap_check_fn=fake_rdap,
        whois_check_fn=fake_whois,
        min_interval=0.01,
    )

    assert res.checked_rdap == 2
    assert res.rdap_404_count == 1
    assert res.rdap_200_count == 1
    assert res.whois_available_count == 1
    assert shortlist_csv.is_file()
    assert scores_csv.is_file()


# 5. Stale-data warning check
def test_stale_data_warning_triggered(client, monkeypatch):
    # Stale timestamp: 10 days ago
    stale_dt = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(timespec="seconds").replace("+00:00", "Z")
    monkeypatch.setattr("web.main.get_snapshot_age_info", lambda: (stale_dt, True))

    r = client.get("/")
    assert r.status_code == 200
    assert "older than 8 days" in r.text
    assert "stale-warning" in r.text


def test_fresh_data_no_stale_warning(client, monkeypatch):
    # Fresh timestamp: 1 hour ago
    fresh_dt = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds").replace("+00:00", "Z")
    monkeypatch.setattr("web.main.get_snapshot_age_info", lambda: (fresh_dt, False))

    r = client.get("/")
    assert r.status_code == 200
    assert "stale-warning" not in r.text


# 6. Sales table rendering strictly from sourced rows
def test_sales_table_rendering(client):
    res = client.get("/")
    assert res.status_code == 200
    # Verified sales
    assert "ai.si" in res.text
    assert "recursive.si" in res.text
    assert "USD 34,000" in res.text
    assert "USD 20,000" in res.text
    assert "https://www.namepros.com/" in res.text

    # Asking price is labeled as asking price, not sale
    assert "USD 10,000,000" in res.text
    assert "badge-ask" in res.text


def test_sales_proposal_helper(tmp_path):
    test_sales_csv = tmp_path / "test_sales.csv"
    candidate = {
        "domain": "testdom.si",
        "amount": "5000",
        "currency": "USD",
        "source_url": "https://example.com/reported-sale",
        "evidence_type": "completed_sale",
    }
    added = propose_sale(candidate, sales_path=test_sales_csv)
    assert added is True
    assert test_sales_csv.is_file()

    # Reject without URL
    with pytest.raises(ValueError, match="Source URL"):
        propose_sale({"domain": "fail.si", "amount": "100", "source_url": "", "evidence_type": "completed_sale"}, sales_path=test_sales_csv)
