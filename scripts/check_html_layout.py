"""Check the generated HTML report at narrow and desktop viewport widths."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Playwright is not installed; HTML layout check is unavailable.", file=sys.stderr)
        return 2

    report = Path(__file__).resolve().parents[1] / "output" / "si_domains_ranked.html"
    if not report.is_file():
        print(f"HTML report not found: {report}", file=sys.stderr)
        return 1

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width in (390, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 1000})
                    page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
                    page.route("https://fonts.gstatic.com/**", lambda route: route.abort())
                    page.goto(report.as_uri(), wait_until="domcontentloaded")
                    page.locator("#owned-chip").wait_for()
                    page.locator("#owned-chip").click()
                    assert page.locator("#owned-chip").inner_text().strip().startswith("Owned")
                    assert page.locator("#owned-chip i").inner_text().strip() == "10"
                    assert page.locator("#owned-summary").is_visible()
                    assert page.locator("#owned-summary .owned-list li").count() == 10
                    assert page.locator("#table .row:not(.head)").count() == 10
                    assert page.locator("#table .owned-badge").count() == 10
                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth"
                    )
                    assert not overflow, f"horizontal overflow at {width}px"
                    page.close()
                browser.close()
            except Exception:
                browser.close()
                raise
    except Error as exc:
        print(f"Playwright browser unavailable: {exc}", file=sys.stderr)
        return 2
    except AssertionError as exc:
        print(f"HTML layout check failed: {exc}", file=sys.stderr)
        return 1

    print("HTML layout PASS at 390px and 1440px; 10 owned rows and badges verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
