"""Check the generated HTML report at narrow and desktop viewport widths."""

from __future__ import annotations

import sys
import traceback
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
                    assert page.locator("#tab-top").get_attribute("aria-selected") == "true"
                    assert page.locator(".stat b").all_inner_texts() == ["6,204", "3,395", "500", "2,809"]
                    assert page.locator(".stat span").all_inner_texts() == [
                        "checked", "available", "top 500 ranked", "unavailable"
                    ]
                    assert page.locator("#table .row:not(.head)").count() == 60
                    assert page.locator("#more").is_visible()
                    assert page.locator("#pager").is_hidden()
                    page.locator("#owned-chip").click()
                    assert page.locator("#owned-chip").inner_text().strip().startswith("Owned")
                    assert page.locator("#owned-chip i").inner_text().strip() == "10"
                    assert page.locator("#owned-summary").is_visible()
                    assert page.locator("#owned-summary .owned-list li").count() == 10
                    assert page.locator("#table .row:not(.head)").count() == 10
                    assert page.locator("#table .owned-badge").count() == 10
                    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                    assert not overflow, f"horizontal overflow on Top 500 at {width}px"

                    page.locator("#tab-top").focus()
                    page.keyboard.press("ArrowRight")
                    assert page.locator("#tab-available").get_attribute("aria-selected") == "true"
                    assert page.locator("#count").inner_text() == "3,395 of 3,395 names"
                    assert page.locator("#owned-chip i").inner_text().strip() == "10"
                    assert page.locator("#table .row:not(.head)").count() == 60
                    assert page.locator("#table .row:not(.head)").first.locator(".c-cat").is_visible()
                    assert page.locator("#table .row:not(.head)").first.locator(".c-why").is_visible()
                    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                    assert not overflow, f"horizontal overflow on All available at {width}px"
                    assert page.locator("#page-label").inner_text().startswith("Rows 1–60 of 3,395")
                    short_length_count = page.evaluate("() => JSON.parse(document.getElementById('data').textContent).available.filter(r => r.d.slice(0,-3).length <= 4).length")
                    page.locator("#len").select_option("4")
                    assert page.locator("#count").inner_text() == f"{short_length_count:,} of 3,395 names"
                    page.locator("#len").select_option("")
                    category = page.locator("#cats .chip[data-c]").nth(1).get_attribute("data-c")
                    category_count = page.evaluate("c => JSON.parse(document.getElementById('data').textContent).available.filter(r => r.c === c).length", category)
                    page.locator(f"#cats .chip[data-c='{category}']").click()
                    assert page.locator("#count").inner_text() == f"{category_count:,} of 3,395 names"
                    page.locator("#cats .chip[data-c='']").click()
                    expected_score_leader = page.evaluate("() => JSON.parse(document.getElementById('data').textContent).available.slice().sort((a,b) => (b.t ?? -1) - (a.t ?? -1) || a.d.localeCompare(b.d))[0].d")
                    page.locator("#table [data-s='t']").click()
                    assert page.locator("#table .row:not(.head)").first.get_attribute("data-d") == expected_score_leader
                    page.locator("#next-page").click()
                    assert page.locator("#page-label").inner_text().startswith("Rows 61–120 of 3,395")
                    assert page.locator("#table .row:not(.head)").count() == 60
                    page.locator("#previous-page").click()
                    page.locator("#q").fill("absorben.si")
                    assert page.locator("#count").inner_text() == "1 of 3,395 names"
                    assert page.locator("#table .row:not(.head)").count() == 1
                    page.locator("#table .row:not(.head)").click()
                    assert "outside_shortlist_cap" in page.locator("#table .detail").inner_text()
                    assert "score breakdown" in page.locator("#table .detail").inner_text().lower()

                    page.locator("#tab-available").focus()
                    page.keyboard.press("ArrowRight")
                    assert page.locator("#tab-unavailable").get_attribute("aria-selected") == "true"
                    assert page.locator("#count").inner_text() == "2,809 of 2,809 names"
                    assert page.locator("#reasonf").is_visible()
                    assert page.locator("#table .row:not(.head)").count() == 60
                    assert page.locator("#table .row:not(.head)").first.locator(".c-category").is_visible()
                    assert page.locator("#table .row:not(.head)").first.locator(".c-stamp").is_visible()
                    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                    assert not overflow, f"horizontal overflow on Unavailable at {width}px"
                    page.locator("#q").fill("abdomen.si")
                    assert page.locator("#count").inner_text() == "1 of 2,809 names"
                    page.locator("#q").fill("")
                    assert page.locator("#reasonf option[value=rdap_registered]").inner_text() == "RDAP registered (2,803)"
                    assert page.locator("#reasonf option[value=whois_registered]").inner_text() == "WHOIS registered (6)"
                    page.locator("#reasonf").select_option("whois_registered")
                    assert page.locator("#count").inner_text() == "6 of 2,809 names"
                    assert page.locator("#table .row:not(.head)").count() == 6

                    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
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
        frame = traceback.extract_tb(exc.__traceback__)[-1]
        print(f"HTML layout check failed at line {frame.lineno}: {exc}", file=sys.stderr)
        return 1

    print("HTML layout PASS at 390px and 1440px; 10 owned rows and badges verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
