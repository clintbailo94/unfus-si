import json
import re
from html.parser import HTMLParser
from pathlib import Path


REPORT = Path(__file__).resolve().parents[1] / "output" / "si_domains_ranked.html"


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_summary = False
        self.in_owned_name = False
        self.in_owned_list_item = False
        self.in_data_script = False
        self.in_script = False
        self.in_owned_chip = False
        self.owned_names = []
        self.owned_items = []
        self.current_item = []
        self.data_json = ""
        self.script_text = []
        self.owned_chip_count = ""
        self.has_owned_chip = False
        self.in_owned_chip_count = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = values.get("class", "").split()
        if tag == "section" and values.get("id") == "owned-summary":
            self.in_summary = True
        if tag == "li" and self.in_summary:
            self.in_owned_list_item = True
            self.current_item = []
        if tag == "span" and self.in_summary and "owned-name" in classes:
            self.in_owned_name = True
        if tag == "script":
            self.in_script = True
            self.in_data_script = values.get("id") == "data"
        if tag == "button" and values.get("id") == "owned-chip":
            self.has_owned_chip = True
            self.in_owned_chip = True
        if tag == "i" and self.in_owned_chip:
            self.in_owned_chip_count = True

    def handle_data(self, data):
        if self.in_owned_name:
            self.owned_names.append(data.strip())
        if self.in_owned_list_item:
            self.current_item.append(data.strip())
        if self.in_data_script:
            self.data_json += data
        if self.in_script:
            self.script_text.append(data)
        if self.in_owned_chip_count:
            self.owned_chip_count += data.strip()

    def handle_endtag(self, tag):
        if tag == "span" and self.in_owned_name:
            self.in_owned_name = False
        if tag == "li" and self.in_owned_list_item:
            self.owned_items.append(" ".join(filter(None, self.current_item)))
            self.in_owned_list_item = False
        if tag == "section" and self.in_summary:
            self.in_summary = False
        if tag == "script":
            self.in_script = False
            self.in_data_script = False
        if tag == "button" and self.in_owned_chip:
            self.in_owned_chip = False
        if tag == "i" and self.in_owned_chip_count:
            self.in_owned_chip_count = False


def test_report_contains_owned_chip_summary_badges_and_purchase_wording():
    parser = ReportParser()
    source = REPORT.read_text(encoding="ascii")
    parser.feed(source)

    assert parser.has_owned_chip
    assert parser.owned_chip_count == "10"
    assert len(parser.owned_items) == 10
    assert len(parser.owned_names) == 10
    assert all("Rank" in item and "Score" in item for item in parser.owned_items)
    assert "owned-badge" in "".join(parser.script_text)

    data = json.loads(parser.data_json)
    owned = [row for row in data["rows"] if row["owned"]]
    assert len(owned) == 10
    assert {row["d"] for row in owned} == set(parser.owned_names)
    assert all(row["owned_status"] == "owned by you (bought 2026-10-14)" for row in owned)

    assert 'role="tablist"' in source
    assert all(f'>{label}</button>' in source for label in ("Top 500", "All available", "Unavailable"))
    stats = re.findall(r'<div class="stat"><b>(.*?)</b><span>(.*?)</span>', source)
    assert ('6,204', 'checked') in stats
    assert ('3,395', 'available') in stats
    assert ('500', 'top 500 ranked') in stats
    assert ('2,809', 'unavailable') in stats
    assert len(data["available"]) == 3395
    assert len(data["unavailable"]) == 2809
    assert sum(row["r"] is not None for row in data["available"]) == 500
    assert all(row["owned"] or (row["rdap"][0] == "404" and row["rdap"][1] == "potentially_unregistered"
                                and row["whois"][0] == "not_registered") for row in data["available"])
    assert all(row["r"] is not None or row["why"] for row in data["available"])
    assert all(not row["owned"] and row["reason"] and (row["evidence_time"] or row["evidence_source"] == "Local rule")
               for row in data["unavailable"])
    assert "const PAGE_SIZE = 60" in "".join(parser.script_text)
