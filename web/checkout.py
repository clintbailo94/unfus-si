"""Stripe integration with test-mode handling and local fake-checkout simulator."""

from __future__ import annotations

import os
import secrets
from typing import Optional

import stripe
from . import db
from .db import create_order


STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

PRICES = {
    "one_off": {
        "amount_gbp": 49,
        "name": "Full Available .si Domain List (Instant Download)",
        "description": "One-off download of all verified available .si domain opportunities (CSV + Excel XLSX).",
    },
    "subscription": {
        "amount_gbp": 29,
        "name": "Continuous .si Intelligence (Weekly Updates + Top 500 Daily)",
        "description": "Continuous access to weekly fresh available domain snapshots and newly discovered drops.",
    },
}


def is_stripe_configured() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_SECRET_KEY.startswith("sk_test_"))


def create_checkout_session(
    tier: str,
    customer_email: str,
    success_url_template: str,
    cancel_url: str,
    db_path: Optional[str] = None,
) -> dict:
    """Create a checkout flow.
    
    If Stripe test keys are present in env, creates a real Stripe Checkout Session in test mode.
    Otherwise, returns a fake checkout session URL for local automated testing.
    """
    if tier not in PRICES:
        raise ValueError(f"Unknown tier: {tier}")

    product = PRICES[tier]
    amount = product["amount_gbp"]

    if is_stripe_configured():
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=customer_email,
            line_items=[
                {
                    "price_data": {
                        "currency": "gbp",
                        "product_data": {
                            "name": product["name"],
                            "description": product["description"],
                        },
                        "unit_amount": amount * 100,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment" if tier == "one_off" else "subscription",
            success_url=success_url_template.replace("{CHECKOUT_SESSION_ID}", "{CHECKOUT_SESSION_ID}"),
            cancel_url=cancel_url,
        )
        return {
            "mode": "stripe_test",
            "checkout_url": session.url,
            "session_id": session.id,
        }

    # Fake checkout for local testing
    fake_token = secrets.token_hex(16)
    order = db.create_order(
        email=customer_email,
        tier=tier,
        amount_gbp=amount,
        stripe_session_id=f"fake_{fake_token}",
        status="paid",
        db_path=db_path,
    )
    success_url = success_url_template.replace("{CHECKOUT_SESSION_ID}", f"fake_{fake_token}")
    if "?" in success_url:
        redirect_url = f"{success_url}&token={order['access_token']}"
    else:
        redirect_url = f"{success_url}?token={order['access_token']}"

    return {
        "mode": "fake_local",
        "checkout_url": redirect_url,
        "session_id": f"fake_{fake_token}",
        "access_token": order["access_token"],
    }
