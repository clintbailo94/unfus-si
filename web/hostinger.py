"""Hostinger API client for managing DNS records for unfus.si."""

from __future__ import annotations

import os
import requests
from typing import Optional


HOSTINGER_API_BASE = "https://api.hostinger.com/v1"


def get_hostinger_token() -> str:
    return os.getenv("HOSTINGER_API_TOKEN", "").strip()


def is_hostinger_configured() -> bool:
    return bool(get_hostinger_token())


def get_dns_records(domain: str = "unfus.si") -> list[dict]:
    """Retrieve DNS zone records from Hostinger API."""
    token = get_hostinger_token()
    if not token:
        raise ValueError("HOSTINGER_API_TOKEN is not set in .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    url = f"{HOSTINGER_API_BASE}/dns/zones/{domain}"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Hostinger API returned HTTP {resp.status_code}: {resp.text}")
    return resp.json().get("records", [])


def update_a_record(domain: str, ip_address: str, host: str = "@", ttl: int = 3600) -> dict:
    """Update or create an A record in Hostinger DNS zone."""
    token = get_hostinger_token()
    if not token:
        raise ValueError("HOSTINGER_API_TOKEN is not set in .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    url = f"{HOSTINGER_API_BASE}/dns/zones/{domain}"
    payload = {
        "records": [
            {
                "type": "A",
                "name": host,
                "content": ip_address,
                "ttl": ttl,
            }
        ]
    }
    resp = requests.put(url, json=payload, headers=headers, timeout=15)
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(f"Failed to update Hostinger DNS (HTTP {resp.status_code}): {resp.text}")
    return {"status": "success", "domain": domain, "ip": ip_address}
