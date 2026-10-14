"""Check the offline HTML report layout, tabs, keyboard controls, and row paging."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


PAGE_SIZE = 50
MAX_VISIBLE = 150


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def no_horizontal_overflow(page, width: int, mode: str) -> None:
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    expect(not overflow, f"horizontal overflow in {mode} at {width}px")


def rows(page, mode: str) -> int:
    return page.locator(f"#panel-{mode} .row:not(.head)").count()


def check_more_and_window_limit(page, mode: str) -> tuple[int, int, int]:
    start = rows(page, mode)
    expect(start <= PAGE_SIZE + 2, f"{mode} initially rendered {start} rows")
    more = page.locator(f"#panel-{mode} [data-more]")
    expect(more.is_visible(), f"{mode} Show more button is hidden")
    more.click()
    after_more = rows(page, mode)
    expect(after_more > start, f"Show more did not add rows in {mode}")
    expect(after_more == start + PAGE_SIZE, f"Show more did not add one page in {mode}")
    expect(after_more <= PAGE_SIZE * 2 + 2, f"{mode} Show more rendered {after_more} rows")
    more.click()
    expect(rows(page, mode) == MAX_VISIBLE, f"{mode} did not grow to the 150-row window")
    before_shift = page.locator(f"#panel-{mode} [data-page-label]").inner_text()
    more.click()
    capped = rows(page, mode)
    after_shift = page.locator(f"#panel-{mode} [data-page-label]").inner_text()
    expect(capped <= MAX_VISIBLE, f"{mode} rendered {capped} rows past the window limit")
    expect(before_shift != after_shift, f"{mode} did not advance beyond its current row window")
    return start, after_more, capped


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

    summaries: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width in (390, 1440):
                    page = browser.new_page(viewport={"width": width, "height": 1000})
                    page_errors: list[str] = []
                    external_requests: list[str] = []
                    page.on("pageerror", lambda error: page_errors.append(str(error)))
                    page.on(
                        "request",
                        lambda request: external_requests.append(request.url)
                        if request.url.startswith(("http://", "https://"))
                        else None,
                    )
                    page.goto(report.as_uri(), wait_until="domcontentloaded")

                    expect(page.locator('[role="tablist"] [role="tab"]').count() == 3, "expected three tabs")
                    expect(page.locator('[role="tabpanel"]').count() == 3, "expected three tabpanels")
                    for mode in ("top", "available", "unavailable"):
                        expect(
                            page.locator(f"#tab-{mode}").get_attribute("aria-controls") == f"panel-{mode}",
                            f"{mode} tab does not control its tabpanel",
                        )
                        expect(
                            page.locator(f"#panel-{mode}").get_attribute("aria-labelledby") == f"tab-{mode}",
                            f"{mode} tabpanel does not label itself from its tab",
                        )
                    expect(page.locator("#tab-top").get_attribute("aria-selected") == "true", "Top 500 is not selected initially")
                    expect(page.locator("#tab-top").get_attribute("tabindex") == "0", "initial tab does not own keyboard focus")
                    expect(page.locator("#panel-available[hidden] .row:not(.head)").count() == 0, "All available rendered before first open")
                    expect(page.locator("#panel-unavailable[hidden] .row:not(.head)").count() == 0, "Unavailable rendered before first open")
                    expect(page.locator(".stat b").all_inner_texts() == ["6,204", "3,395", "500", "2,809"], "header counts differ")
                    expect(page.locator("#owned-summary .owned-list li").count() == 10, "owned summary does not list ten domains")
                    expect(rows(page, "top") == PAGE_SIZE, "Top 500 did not start with one page")
                    no_horizontal_overflow(page, width, "Top 500")
                    top_counts = check_more_and_window_limit(page, "top")
                    no_horizontal_overflow(page, width, "Top 500 after paging")

                    owned_chip = page.locator("#panel-top .chip[data-owned=true]")
                    expect(owned_chip.locator("i").inner_text().strip() == "10", "Owned filter count is not ten")
                    owned_chip.click()
                    expect(rows(page, "top") == 10, "Owned filter does not show ten rows")
                    expect(page.locator("#panel-top .owned-badge").count() == 10, "owned rows lack badges")
                    page.locator("#panel-top .row:not(.head)").first.click()
                    expect("owned by you (bought 2026-10-14)" in page.locator("#panel-top").inner_text(), "owned availability wording is missing")
                    page.locator("#panel-top .chip[data-c='']").click()

                    page.locator("#tab-top").focus()
                    page.keyboard.press("ArrowRight")
                    expect(page.locator("#tab-available").get_attribute("aria-selected") == "true", "ArrowRight did not activate All available")
                    expect(page.locator("#tab-available").get_attribute("tabindex") == "0", "All available did not receive the roving tabindex")
                    expect(rows(page, "available") == PAGE_SIZE, "All available did not lazily render one page")
                    no_horizontal_overflow(page, width, "All available")
                    available_counts = check_more_and_window_limit(page, "available")

                    data_candidate = page.evaluate(
                        "() => JSON.parse(document.getElementById('data').textContent).a.find(row => row[4] === null)[0]"
                    )
                    page.locator("#panel-available [data-query]").fill(data_candidate)
                    expect(page.locator("#panel-available [data-count]").inner_text() == "1 of 3,395 names", "All available search failed")
                    page.locator("#panel-available [data-query]").fill("")

                    short_count = page.evaluate(
                        "() => JSON.parse(document.getElementById('data').textContent).a.filter(row => row[0].slice(0, -3).length <= 4).length"
                    )
                    page.locator("#panel-available [data-length]").select_option("4")
                    expect(
                        page.locator("#panel-available [data-count]").inner_text() == f"{short_count:,} of 3,395 names",
                        "All available length filter differs from embedded data",
                    )
                    page.locator("#panel-available [data-length]").select_option("")
                    category = page.locator("#panel-available .chip[data-c]").nth(1).get_attribute("data-c")
                    category_count = page.evaluate(
                        "category => JSON.parse(document.getElementById('data').textContent).a.filter(row => row[1] === category).length",
                        category,
                    )
                    page.locator(f"#panel-available .chip[data-c='{category}']").click()
                    expect(
                        page.locator("#panel-available [data-count]").inner_text() == f"{category_count:,} of 3,395 names",
                        "All available category filter differs from embedded data",
                    )
                    page.locator("#panel-available .chip[data-c='']").click()
                    expected_leader = page.evaluate(
                        "() => JSON.parse(document.getElementById('data').textContent).a.slice().sort((a,b) => (b[2] ?? -1) - (a[2] ?? -1) || a[0].localeCompare(b[0]))[0][0]"
                    )
                    page.locator("#panel-available [data-sort='t']").click()
                    expect(
                        page.locator("#panel-available .row:not(.head)").first.get_attribute("data-d") == expected_leader,
                        "All available score sort differs from embedded data",
                    )
                    no_horizontal_overflow(page, width, "All available after filtering and sorting")

                    page.locator("#tab-available").focus()
                    page.keyboard.press("ArrowRight")
                    expect(page.locator("#tab-unavailable").get_attribute("aria-selected") == "true", "ArrowRight did not activate Unavailable")
                    expect(rows(page, "unavailable") == PAGE_SIZE, "Unavailable did not lazily render one page")
                    no_horizontal_overflow(page, width, "Unavailable")
                    unavailable_counts = check_more_and_window_limit(page, "unavailable")
                    reason = page.locator("#panel-unavailable [data-reason]")
                    expect(reason.is_visible(), "Unavailable reason filter is hidden")
                    expect(reason.locator("option[value='rdap_registered']").inner_text() == "RDAP registered (2,803)", "RDAP reason count differs")
                    expect(reason.locator("option[value='whois_registered']").inner_text() == "WHOIS registered (6)", "WHOIS reason count differs")
                    reason.select_option("whois_registered")
                    expect(page.locator("#panel-unavailable [data-count]").inner_text() == "6 of 2,809 names", "Unavailable reason filter failed")
                    unavailable_domain = page.evaluate(
                        "() => JSON.parse(document.getElementById('data').textContent).u.find(row => row[2] === 'whois_registered')[0]"
                    )
                    page.locator("#panel-unavailable [data-query]").fill(unavailable_domain)
                    expect(page.locator("#panel-unavailable [data-count]").inner_text() == "1 of 2,809 names", "Unavailable search failed")
                    no_horizontal_overflow(page, width, "Unavailable after reason filter")

                    page.locator("#tab-unavailable").focus()
                    page.keyboard.press("End")
                    expect(page.locator("#tab-unavailable").get_attribute("aria-selected") == "true", "End did not select the last tab")
                    page.keyboard.press("ArrowLeft")
                    expect(page.locator("#tab-available").get_attribute("aria-selected") == "true", "ArrowLeft did not return to All available")
                    page.keyboard.press("Home")
                    expect(page.locator("#tab-top").get_attribute("aria-selected") == "true", "Home did not select Top 500")
                    focus_outline = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
                    expect(focus_outline != "none", "keyboard focus ring is not visible")
                    expect(not page_errors, f"JavaScript errors: {page_errors}")
                    expect(not external_requests, f"offline page made external requests: {external_requests}")
                    summaries.append(
                        f"{width}px: Top 500 {top_counts[0]}->{top_counts[1]}->{top_counts[2]}, "
                        f"All available {available_counts[0]}->{available_counts[1]}->{available_counts[2]}, "
                        f"Unavailable {unavailable_counts[0]}->{unavailable_counts[1]}->{unavailable_counts[2]}; "
                        "Top 500/All available/Unavailable overflow 0; external requests 0"
                    )
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

    print("HTML layout PASS; " + "; ".join(summaries) + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
