"""Build a deterministic, self-contained HTML report from the ranked workbook."""
import argparse
import html
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "output" / "si_domains_ranked.xlsx"
DEFAULT_OUT = ROOT / "output" / "si_domains_ranked.html"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--xlsx", type=Path, default=DEFAULT_SRC, help="source workbook")
parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="generated HTML report")
parser.add_argument("--check", action="store_true", help="compare generated HTML with the existing file")
args = parser.parse_args()
SRC = args.xlsx.resolve()
OUT = args.out.resolve()

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)


def sheet(name):
    rows = list(wb[name].iter_rows(values_only=True))
    return [dict(zip(rows[0], r)) for r in rows[1:] if any(c is not None for c in r)]


def num(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


def coverage(s):
    out = []
    for part in (s or "").split(";"):
        m = re.match(r"(\w+):([a-z_]+)\[(\d+)/(\d+)\]", part.strip())
        if m:
            out.append([m.group(1), m.group(2), int(m.group(3)), int(m.group(4))])
    return out


short = sheet("Shortlist")
all_candidates = sheet("All candidates")
owned_sheet = sheet("Owned")
owned_by_domain = {str(row["domain"]): row for row in owned_sheet}
if len(owned_by_domain) != len(owned_sheet):
    raise ValueError("Owned sheet contains duplicate domains")
if len(owned_by_domain) != 10:
    raise ValueError(f"Expected ten owned domains in the workbook, found {len(owned_by_domain)}")
rows = []
for r in short:
    domain = str(r["domain"])
    owned_row = owned_by_domain.get(domain)
    is_owned = r.get("owned", "") == "yes"
    if is_owned != (owned_row is not None):
        raise ValueError(f"Shortlist owned flag does not match Owned sheet for {domain}")
    purchase_date = str(owned_row["purchase_date"]) if owned_row else ""
    rows.append({
        "r": num(r["rank"]), "d": domain, "t": num(r["total"]), "c": r["category"],
        "owned": is_owned, "owned_status": f"owned by you (bought {purchase_date})" if is_owned else "",
        "s": [num(r[k]) for k in ("brandability", "commercial", "shortness", "hack", "resale", "trademark")],
        "tm": r["trademark_status"], "cov": coverage(r["trademark_coverage"]),
        "why": r["rationale"] or "", "val": r["valuation_rationale"] or "",
        "rdap": [r["rdap_http_status"], r["rdap_timestamp"]], "whois": [r["whois_classification"], r["whois_timestamp"]],
    })

meth = {str(r["Topic"]): str(r["Details"] or "") for r in sheet("Methodology")}
avail = []
for k, v in meth.items():
    if k.startswith("Availability: "):
        p = [x.strip() for x in v.split("|")]
        avail.append({"cat": p[0], "pool": num(p[1]), "eligible": num(p[2]), "final": num(p[3])})
sales = [{k: r[k] for k in ("sold_domain", "amount", "currency", "transaction_date", "venue", "relevance", "source_url")}
         for r in sheet("Valuation evidence")]
cands = len(all_candidates)


def available(candidate):
    if candidate.get("owned") == "yes":
        return True
    return (
        candidate.get("known_rule_class") == "ok"
        and num(candidate.get("latest_rdap_http_status")) == 404
        and candidate.get("latest_rdap_classification") == "potentially_unregistered"
        and candidate.get("latest_whois_classification") == "not_registered"
    )


def unavailable_reason(candidate):
    rule_class = str(candidate.get("known_rule_class") or "ok")
    rdap_class = str(candidate.get("latest_rdap_classification") or "missing")
    whois_class = str(candidate.get("latest_whois_classification") or "missing")
    rdap_time = str(candidate.get("latest_rdap_timestamp") or "")
    whois_time = str(candidate.get("latest_whois_timestamp") or "")
    rule_detail = str(candidate.get("known_rule_explanation") or "")
    if rule_class != "ok":
        if rule_class == "invalid_syntax":
            return "syntax_rule", "Syntax rule", rule_detail, "Local rule", ""
        return f"special:{rule_class}", f"Reserved / special class: {rule_class}", rule_detail, "Local rule", ""
    if rdap_class == "registered":
        return "rdap_registered", "RDAP registered", "", "RDAP", rdap_time
    if rdap_class in {"reserved", "restricted", "premium", "invalid_syntax"}:
        if rdap_class == "invalid_syntax":
            return "syntax_rule", "Syntax rule", "", "RDAP", rdap_time
        return f"special:{rdap_class}", f"RDAP special class: {rdap_class}", "", "RDAP", rdap_time
    if whois_class == "registered":
        return "whois_registered", "WHOIS registered", str(candidate.get("latest_whois_matched_pattern") or ""), "WHOIS", whois_time
    if rdap_class == "unverified" or rdap_class == "missing":
        label = "RDAP unverified" if rdap_class == "unverified" else "RDAP not checked"
        return f"rdap_{rdap_class}", label, str(candidate.get("latest_rdap_error") or ""), "RDAP", rdap_time
    if whois_class in {"unverified", "missing"}:
        label = "WHOIS unverified" if whois_class == "unverified" else "WHOIS not checked"
        return f"whois_{whois_class}", label, str(candidate.get("latest_whois_error") or ""), "WHOIS", whois_time
    return "not_available", str(candidate.get("exclusion_reason") or "Not available"), "", "Registry", rdap_time or whois_time


score_fields = ("brandability", "commercial", "shortness", "hack", "resale", "trademark")
available_rows = []
unavailable_rows = []
for candidate in all_candidates:
    domain = str(candidate["domain"])
    is_owned = candidate.get("owned") == "yes"
    owned_record = owned_by_domain.get(domain)
    base = {
        "d": domain,
        "c": str(candidate["category"]),
        "t": num(candidate.get("score_total")),
        "s": [num(candidate.get(name)) for name in score_fields],
        "r": num(candidate.get("shortlist_rank")),
        "owned": is_owned,
        "owned_status": f"owned by you (bought {owned_record['purchase_date']})" if owned_record else "",
        "why": str(candidate.get("exclusion_reason") or ""),
        "rdap": [str(candidate.get("latest_rdap_http_status") or ""), str(candidate.get("latest_rdap_classification") or ""), str(candidate.get("latest_rdap_timestamp") or "")],
        "whois": [str(candidate.get("latest_whois_classification") or ""), str(candidate.get("latest_whois_timestamp") or "")],
    }
    if available(candidate):
        available_rows.append(base)
    else:
        code, label, detail, source, timestamp = unavailable_reason(candidate)
        base.update({"reason_code": code, "reason": label, "reason_detail": detail,
                     "evidence_source": source, "evidence_time": timestamp})
        unavailable_rows.append(base)

if len(available_rows) + len(unavailable_rows) != cands:
    raise ValueError("Available and unavailable rows do not cover All candidates")
if sum(row["r"] is not None for row in available_rows) != len(short):
    raise ValueError("All available shortlist ranks do not match the Shortlist sheet")

weights = meth.get("Ranking weights", "")
rdap_counts = meth.get("Latest RDAP counts", "")
whois_counts = meth.get("Latest WHOIS counts", "")
tm_range = meth.get("Trademark evidence timestamp range", "")
rdap_range = meth.get("RDAP history timestamp range", "")
whois_range = meth.get("WHOIS history timestamp range", "")

data = json.dumps({"rows": rows, "available": available_rows, "unavailable": unavailable_rows,
                   "avail": avail, "sales": sales}, ensure_ascii=True, separators=(",", ":"))
data = data.replace("</", "<\\/")
E = lambda value: html.escape(str(value)).encode("ascii", errors="xmlcharrefreplace").decode("ascii")
owned_summary = "".join(
    '<li><span class="owned-name">' + E(row["d"]) + '</span><span>Rank <b>' + str(row["r"])
    + '</b></span><span>Score <b>' + str(row["t"]) + "</b></span></li>"
    for row in sorted((row for row in rows if row["owned"]), key=lambda item: item["r"])
)
owned_count = sum(1 for row in rows if row["owned"])

page = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>.si Domain Shortlist</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f6f4ef; --paper:#fffdf9; --ink:#1b1f24; --muted:#5d6670; --faint:#8a929b; --line:#e4dfd5;
  --accent:#0f6b5c; --accent-soft:#e3f1ec; --amber:#a15c07; --amber-soft:#fbefd9; --slate:#4a5866; --slate-soft:#e9edf1;
  --red:#a8322d; --bar:#0f6b5c; --bar-bg:#ebe6dc; --shadow:0 1px 2px rgba(20,20,20,.04),0 8px 24px rgba(20,20,20,.05);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#121417; --paper:#181b1f; --ink:#e8e6e1; --muted:#a3abb4; --faint:#78818b; --line:#2a2f35;
  --accent:#4fbfa8; --accent-soft:#16302b; --amber:#e6a64a; --amber-soft:#33270f; --slate:#a9b6c3; --slate-soft:#232a31;
  --red:#e5736d; --bar:#4fbfa8; --bar-bg:#262b31; --shadow:none;}}
:root[data-theme="dark"]{
  --bg:#121417; --paper:#181b1f; --ink:#e8e6e1; --muted:#a3abb4; --faint:#78818b; --line:#2a2f35;
  --accent:#4fbfa8; --accent-soft:#16302b; --amber:#e6a64a; --amber-soft:#33270f; --slate:#a9b6c3; --slate-soft:#232a31;
  --red:#e5736d; --bar:#4fbfa8; --bar-bg:#262b31; --shadow:none;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
header{padding:56px 0 28px}
.eyebrow{font:600 12px/1 Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
h1{font:650 clamp(34px,5vw,54px)/1.05 Fraunces,Georgia,serif;margin:14px 0 14px;letter-spacing:-.01em}
h1 span{color:var(--accent)}
.lede{max-width:720px;color:var(--muted);font-size:17px;margin:0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:32px 0 0}
.stat{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.stat b{display:block;font:650 28px/1.1 Fraunces,Georgia,serif}
.stat span{color:var(--muted);font-size:13px}
.notice{margin:20px 0 0;padding:14px 16px;border-radius:12px;background:var(--amber-soft);color:var(--ink);font-size:14px;border:1px solid color-mix(in srgb,var(--amber) 25%,transparent)}
.notice strong{color:var(--amber)}
section{margin:40px 0}
h2{font:650 24px/1.2 Fraunces,Georgia,serif;margin:0 0 6px}
.sub{color:var(--muted);margin:0 0 18px;font-size:14px}
.cats{display:flex;flex-wrap:wrap;gap:8px}
.tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:22px 0 18px}
.tab{border:1px solid var(--line);background:var(--paper);color:var(--muted);border-radius:12px;padding:12px 14px;font:600 14px Inter,sans-serif;cursor:pointer;text-align:center}
.tab:hover{color:var(--ink);border-color:var(--accent)}
.tab[aria-selected="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.tab:focus-visible,.chip:focus-visible,.more:focus-visible,.pager button:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.chip{border:1px solid var(--line);background:var(--paper);color:var(--ink);border-radius:999px;padding:7px 13px;font:500 13px Inter,sans-serif;cursor:pointer;display:inline-flex;gap:8px;align-items:center}
.chip i{font-style:normal;color:var(--faint);font-variant-numeric:tabular-nums}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.chip[aria-pressed="true"] i{color:inherit;opacity:.7}
.controls{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 14px;align-items:center}
.controls input,.controls select{font:inherit;font-size:14px;padding:9px 12px;border-radius:10px;border:1px solid var(--line);background:var(--paper);color:var(--ink)}
.controls input{flex:1 1 240px;min-width:0}
.count{color:var(--muted);font-size:13px;margin-left:auto}
.pager{display:flex;align-items:center;justify-content:center;gap:14px;margin:16px auto;color:var(--muted);font-size:13px}
.pager[hidden],.more[hidden],.controls [hidden]{display:none}
.pager button{font:500 14px Inter,sans-serif;padding:9px 14px;border-radius:10px;border:1px solid var(--line);background:var(--paper);color:var(--ink);cursor:pointer}
.pager button:disabled{opacity:.45;cursor:default}
.table{background:var(--paper);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);overflow:hidden}
.row{display:grid;grid-template-columns:52px minmax(150px,1.4fr) 128px 150px minmax(170px,1fr) 150px 24px;gap:14px;align-items:center;padding:12px 18px;border-top:1px solid var(--line);cursor:pointer}
.row:hover{background:color-mix(in srgb,var(--accent-soft) 45%,transparent)}
.row.head{border-top:0;cursor:default;font:600 11px/1 Inter,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);padding-top:14px;padding-bottom:12px}
.row.head:hover{background:none}
.row.head button{all:unset;cursor:pointer}
.row.head button:hover{color:var(--ink)}
.rank{font:600 13px JetBrains Mono,monospace;color:var(--faint)}
.dom{font:600 15px JetBrains Mono,ui-monospace,monospace;letter-spacing:-.01em;overflow-wrap:anywhere}
.dom em{font-style:normal;color:var(--faint)}
.pill{display:inline-block;padding:3px 9px;border-radius:999px;background:var(--slate-soft);color:var(--slate);font-size:12px;font-weight:500;white-space:nowrap}
.total{display:flex;align-items:center;gap:10px}
.total b{font:600 15px JetBrains Mono,monospace;width:38px}
.bar{flex:1;height:6px;border-radius:6px;background:var(--bar-bg);overflow:hidden}
.bar>div{height:100%;background:var(--bar);border-radius:6px}
.minis{display:grid;grid-template-columns:repeat(6,1fr);gap:4px;align-items:end;height:26px}
.minis div{background:var(--bar);opacity:.75;border-radius:2px 2px 0 0;min-height:2px}
.tm{font-size:12px;font-weight:600;padding:4px 9px;border-radius:8px;white-space:nowrap}
.tm.review{background:var(--amber-soft);color:var(--amber)}
.tm.blocked{background:var(--slate-soft);color:var(--slate)}
.tm.none{background:transparent;color:var(--faint);border:1px dashed var(--line)}
.caret{color:var(--faint);transition:transform .15s}
.row[aria-expanded="true"] .caret{transform:rotate(90deg)}
.detail{display:none;padding:4px 18px 20px 84px;border-top:0;background:color-mix(in srgb,var(--accent-soft) 30%,transparent)}
.detail.open{display:block}
.dgrid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:22px}
.dgrid h4{margin:12px 0 8px;font:600 11px Inter,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
.dgrid p{margin:0;font-size:14px}
.sc{display:grid;grid-template-columns:96px 1fr 30px;gap:8px;align-items:center;font-size:13px;margin:4px 0}
.sc span:last-child{font-family:JetBrains Mono,monospace;text-align:right}
.src{display:flex;justify-content:space-between;font-size:13px;padding:5px 0;border-bottom:1px dashed var(--line)}
.src:last-child{border:0}
.ok{color:var(--accent)} .warn{color:var(--amber)} .bad{color:var(--red)} .mute{color:var(--faint)}
.more{display:block;margin:16px auto;font:500 14px Inter,sans-serif;padding:10px 18px;border-radius:10px;border:1px solid var(--line);background:var(--paper);color:var(--ink);cursor:pointer}
.empty{padding:40px;text-align:center;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:var(--shadow)}
.card h3{margin:0 0 6px;font:650 17px Fraunces,Georgia,serif}
.card p{margin:0;color:var(--muted);font-size:14px}
table.plain{width:100%;border-collapse:collapse;font-size:14px;background:var(--paper);border:1px solid var(--line);border-radius:14px;overflow:hidden}
table.plain th{text-align:left;font:600 11px Inter,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);padding:12px 14px;border-bottom:1px solid var(--line)}
table.plain td{padding:10px 14px;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}
table.plain td.n{text-align:right}
.tablebox{overflow-x:auto;border-radius:14px}
.owned-summary{margin:28px 0;padding:20px;background:var(--paper);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow)}
.owned-summary h2{margin-bottom:4px}
.owned-summary .sub{margin-bottom:14px}
.owned-list{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:6px 20px}
.owned-list li{min-width:0;display:grid;grid-template-columns:minmax(0,1fr) 70px 70px;gap:8px;align-items:center;padding:8px 10px;border-top:1px solid var(--line);font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}
.owned-name{min-width:0;color:var(--ink);font:600 13px JetBrains Mono,ui-monospace,monospace;overflow-wrap:anywhere}
.owned-list b{color:var(--ink)}
.owned-badge{display:inline-block;margin-left:7px;padding:2px 7px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font:600 10px/1.5 Inter,sans-serif;letter-spacing:.02em;vertical-align:2px;white-space:nowrap}
.reason-pill{display:inline-block;padding:3px 8px;border-radius:8px;background:var(--slate-soft);color:var(--slate);font-size:12px;line-height:1.4;white-space:normal}
.timestamp{font:12px/1.45 JetBrains Mono,ui-monospace,monospace;color:var(--muted);overflow-wrap:anywhere}
.row.available{grid-template-columns:52px minmax(150px,1.25fr) 128px 145px 150px minmax(165px,1fr) 24px}
.row.unavailable{grid-template-columns:minmax(160px,1.25fr) minmax(120px,.8fr) minmax(165px,1fr) minmax(190px,1.2fr) 24px}
.row.head.unavailable{grid-template-columns:minmax(160px,1.25fr) minmax(120px,.8fr) minmax(165px,1fr) minmax(190px,1.2fr) 24px}
a{color:var(--accent)}
footer{color:var(--faint);font-size:13px;padding:30px 0 60px;border-top:1px solid var(--line);margin-top:50px}
.theme{position:fixed;top:14px;right:14px;z-index:5;border:1px solid var(--line);background:var(--paper);color:var(--ink);border-radius:999px;width:38px;height:38px;cursor:pointer;font-size:16px}
@media (max-width:900px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .tab{padding:10px 6px;font-size:13px}
  .row{grid-template-columns:40px 1fr auto 18px;gap:10px;padding:12px 14px}
  .row .c-cat,.row .c-mini,.row .c-tm{display:none}
  .row.available{grid-template-columns:40px minmax(0,1fr) auto 18px}
  .row.available .rank{grid-column:1;grid-row:1}
  .row.available .dom{grid-column:2;grid-row:1}
  .row.available .c-total{grid-column:3;grid-row:1}
  .row.available .c-cat{display:block;grid-column:2 / 4;grid-row:2}
  .row.available .c-mini{display:none}
  .row.available .c-why{display:block;grid-column:2 / 4;grid-row:3;font-size:12px}
  .row.available .caret{grid-column:4;grid-row:1 / 4;align-self:center}
  .row.head.available .c-cat,.row.head.available .c-mini,.row.head.available .c-why{display:none}
  .row.unavailable{grid-template-columns:minmax(0,1fr) 18px;gap:7px;padding:12px 14px}
  .row.unavailable .c-category,.row.unavailable .c-reason,.row.unavailable .c-stamp{grid-column:1}
  .row.unavailable .caret{grid-column:2;grid-row:1 / 5;align-self:center}
  .row.head.unavailable{grid-template-columns:minmax(0,1fr) auto 18px;gap:8px;padding:12px 14px}
  .row.head.unavailable .c-category,.row.head.unavailable .c-stamp{display:none}
  .row.head .c-total{justify-self:end}
  .total{width:120px}
  .detail{padding:4px 14px 18px}
  .dgrid,.cards{grid-template-columns:1fr}
  .owned-list{grid-template-columns:1fr}
  .owned-list li{grid-template-columns:minmax(0,1fr) 64px 64px;gap:6px;padding:8px 2px}
}
</style>
</head>
<body>
<button class="theme" id="theme" aria-label="Toggle dark mode">&#9681;</button>
<div class="wrap">
<header>
  <div class="eyebrow">Research report / Slovenia ccTLD</div>
  <h1>500 ranked <span>.si</span> domains worth a look</h1>
  <p class="lede">Browse the ranked shortlist, every name that passed both availability checks, and every name that did not. Score details and exclusion reasons come from the workbook; registry observations are a dated snapshot, and domains in Your domains have since been purchased.</p>
  <div class="stats">
    <div class="stat"><b>__CANDS__</b><span>checked</span></div>
    <div class="stat"><b>__AVAILABLE__</b><span>available</span></div>
    <div class="stat"><b>__RANKED__</b><span>top 500 ranked</span></div>
    <div class="stat"><b>__UNAVAILABLE__</b><span>unavailable</span></div>
  </div>
  <div class="notice"><strong>Registry status:</strong> RDAP and WHOIS observations are from 13 Oct 2026 and do not confirm current registrar availability. Owned rows show the purchase date; their registry evidence is pre-purchase history. The owner-requested USPTO screen of profitdesk.si returned zero exact and fuzzy-1 matches; top-100 USPTO coverage remains 100/100, and other outside-top-100 names remain not yet screened. No name is trademark-cleared: EU (TMview) and UK (UKIPO) searches refused automated access. Price estimates are not given because there are not enough comparable .si sales to support them.</div>
</header>

<section class="owned-summary" id="owned-summary">
  <h2>Your domains</h2>
  <p class="sub">Purchased domains, with their current shortlist rank and score.</p>
  <ul class="owned-list">__OWNED_SUMMARY__</ul>
</section>

<section id="list">
  <div class="tabs" role="tablist" aria-label="Domain views">
    <button class="tab" id="tab-top" role="tab" aria-selected="true" aria-controls="report-panel" tabindex="0" data-mode="top">Top 500</button>
    <button class="tab" id="tab-available" role="tab" aria-selected="false" aria-controls="report-panel" tabindex="-1" data-mode="available">All available</button>
    <button class="tab" id="tab-unavailable" role="tab" aria-selected="false" aria-controls="report-panel" tabindex="-1" data-mode="unavailable">Unavailable</button>
  </div>
  <div id="report-panel" role="tabpanel" aria-labelledby="tab-top" tabindex="0">
  <h2 id="view-title">The shortlist</h2>
  <p class="sub" id="view-sub">Tap a category to filter. Tap any row for the reasoning, score breakdown and evidence.</p>
  <div class="cats" id="cats"><button type="button" class="chip" id="owned-chip" data-owned="true" aria-pressed="false">Owned <i>__OWNED_COUNT__</i></button></div>
  <div class="controls">
    <input id="q" type="search" placeholder="Search domains or reasoning..." aria-label="Search">
    <select id="tmf" aria-label="Trademark status" hidden>
      <option value="">All trademark statuses</option>
      <option value="blocked">Blocked / incomplete screen</option>
      <option value="needs legal review">Needs legal review</option>
      <option value="not yet screened">Not yet screened</option>
    </select>
    <select id="reasonf" aria-label="Unavailable reason" hidden><option value="">All reasons</option></select>
    <select id="len" aria-label="Length">
      <option value="">Any length</option><option value="4"><= 4 letters</option><option value="6"><= 6 letters</option><option value="8"><= 8 letters</option>
    </select>
    <span class="count" id="count"></span>
  </div>
  <div class="table" id="table"></div>
  <button class="more" id="more" hidden>Show more</button>
  <div class="pager" id="pager" hidden><button id="previous-page" type="button">Previous</button><span id="page-label"></span><button id="next-page" type="button">Next</button></div>
  </div>
</section>

<section>
  <h2>How the score works</h2>
  <p class="sub">__WEIGHTS__. Each part is 0-100; the total is their weighted average.</p>
  <div class="cards">
    <div class="card"><h3>Brandability / 25%</h3><p>Length, how easy it is to say and spell, letter shape and vowel balance.</p></div>
    <div class="card"><h3>Commercial / 20%</h3><p>Demand for the root words (e.g. <em>data</em>, <em>pay</em>, <em>ai</em>) and how many kinds of buyer they appeal to.</p></div>
    <div class="card"><h3>Shortness / 15%</h3><p>Length, syllables and letter variety; short pronounceable names score highest.</p></div>
    <div class="card"><h3>Domain hack / 15%</h3><p>How well ".si" completes a real word, as in <em>newsagen.si</em> -> "newsagency".</p></div>
    <div class="card"><h3>Resale / 15%</h3><p>A heuristic for memorability, root demand and rarity, not a price estimate.</p></div>
    <div class="card"><h3>Trademark / 10%</h3><p>40 when the US screen found no obvious match or hasn't run yet; 25 when it found a possible conflict.</p></div>
  </div>
</section>

<section>
  <h2>Where the names came from</h2>
  <p class="sub">Candidates per category, eligible in the registry snapshot, and included in the final 500 (each category is capped at 100).</p>
  <div class="tablebox"><table class="plain" id="avail"></table></div>
</section>

<section>
  <h2>Comparable .si sales</h2>
  <p class="sub">The public sales found. All are weak analogies, which is why no name gets a price estimate.</p>
  <div class="tablebox"><table class="plain" id="sales"></table></div>
</section>

<footer>
  Source: <code>si_domains_ranked.xlsx</code> (Shortlist, Methodology and evidence sheets).
  RDAP checks __RDAPR__ / WHOIS checks __WHOISR__ / trademark evidence __TMR__.<br>
  RDAP results: __RDAPC__. WHOIS results: __WHOISC__. Research data only: not legal or investment advice.
</footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
const CAT = {ai:'AI',invented:'Invented',consumer_brands:'Consumer brands',health_science:'Health & science',
  business_finance:'Business & finance',emerging_industries:'Emerging industries',technology:'Technology',
  dictionary:'Dictionary words',short:'Short',domain_hacks:'Domain hacks'};
const TM = {'needs legal review':['review','Needs legal review'],'blocked':['blocked','Blocked / incomplete screen'],'not yet screened':['none','Not yet screened']};
const PARTS = ['Brandability','Commercial','Shortness','Hack','Resale','Trademark'];
const COV = {complete:['ok','clear'],no_obvious_match:['ok','no obvious match'],possible_conflict:['warn','possible conflict'],
  unverified:['mute','unchecked (refused access)'],blocked:['mute','unchecked (blocked)']};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $ = id => document.getElementById(id);
const PAGE_SIZE = 60;
const st = {mode:'top', cat:'', owned:false, q:'', tm:'', reason:'', len:'', sort:'r', dir:1, shown:60, page:0};

// theme toggle
try { const t = localStorage.getItem('si-theme'); if (t) document.documentElement.dataset.theme = t; } catch(e) {}
$('theme').onclick = () => {
  const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark'
    : matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark ? 'light' : 'dark';
  try { localStorage.setItem('si-theme', document.documentElement.dataset.theme); } catch(e) {}
};

function sourceRows(){ return st.mode === 'top' ? D.rows : st.mode === 'available' ? D.available : D.unavailable; }
function resetPaging(){ st.shown = PAGE_SIZE; st.page = 0; }
function drawCategories(){
  const source = sourceRows(), counts = {};
  source.forEach(r => counts[r.c] = (counts[r.c] || 0) + 1);
  const cats = [['', 'All', source.length], ...Object.entries(counts).sort((a,b) => b[1]-a[1]).map(([k,n]) => [k, CAT[k] || k, n])];
  const chips = cats.map(([k,l,n]) => `<button type="button" class="chip" data-c="${esc(k)}" aria-pressed="${k === st.cat && !st.owned}">${esc(l)} <i>${n.toLocaleString()}</i></button>`).join('');
  const owned = st.mode === 'unavailable' ? '' : `<button type="button" class="chip" id="owned-chip" data-owned="true" aria-pressed="${st.owned}">Owned <i>${source.filter(r => r.owned).length}</i></button>`;
  $('cats').innerHTML = chips + owned;
}
function drawReasonFilter(){
  const counts = {};
  D.unavailable.forEach(r => { if (!counts[r.reason_code]) counts[r.reason_code] = {label:r.reason,count:0}; counts[r.reason_code].count++; });
  const options = Object.entries(counts).sort((a,b) => b[1].count-a[1].count)
    .map(([code,v]) => `<option value="${esc(code)}">${esc(v.label)} (${v.count.toLocaleString()})</option>`).join('');
  $('reasonf').innerHTML = '<option value="">All reasons</option>' + options;
}
function updateControls(){
  $('tmf').hidden = st.mode !== 'top'; $('reasonf').hidden = st.mode !== 'unavailable';
  $('view-title').textContent = st.mode === 'top' ? 'The shortlist' : st.mode === 'available' ? 'All available' : 'Unavailable';
  $('view-sub').textContent = st.mode === 'top'
    ? 'Tap a category to filter. Tap any row for the reasoning, score breakdown and evidence.'
    : st.mode === 'available'
      ? 'Every name with RDAP 404, WHOIS not_registered and known rules passing. Ranked names include their shortlist rank; other exclusion reasons come from the workbook.'
      : 'Names that failed an availability check or a known rule. Search by domain and filter by the recorded reason; timestamps are from the evidence.';
}
function selectMode(mode, focusTab){
  st.mode = mode; st.cat = ''; st.owned = false; st.tm = ''; st.reason = ''; st.len = ''; st.q = '';
  st.sort = mode === 'unavailable' ? 'd' : 'r'; st.dir = 1; resetPaging();
  $('q').value = ''; $('tmf').value = ''; $('reasonf').value = ''; $('len').value = '';
  document.querySelectorAll('[role="tab"]').forEach(tab => {
    const selected = tab.dataset.mode === mode;
    tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1;
    if (selected) { $('report-panel').setAttribute('aria-labelledby', tab.id); if (focusTab) tab.focus(); }
  });
  updateControls(); drawCategories(); render();
}
function filtered(){
  const rs = sourceRows().filter(r => (!st.cat || r.c === st.cat) && (!st.owned || r.owned)
    && (!st.tm || r.tm === st.tm) && (!st.reason || r.reason_code === st.reason)
    && (!st.len || r.d.slice(0, -3).length <= +st.len)
    && (!st.q || [r.d,r.c,r.why,r.reason,r.reason_detail].filter(Boolean).join(' ').toLowerCase().includes(st.q)));
  const cmp = (a,b) => a > b ? 1 : a < b ? -1 : 0;
  return rs.sort((a,b) => {
    let result = 0;
    if (st.sort === 'd') result = cmp(a.d,b.d);
    else if (st.sort === 't') {
      if (a.t == null || b.t == null) result = a.t == null ? (b.t == null ? cmp(a.d,b.d) : 1) : -1;
      else result = cmp(b.t,a.t) || cmp(a.d,b.d);
    } else {
      if (a.r == null || b.r == null) result = a.r == null ? (b.r == null ? cmp(a.d,b.d) : 1) : -1;
      else result = cmp(a.r,b.r);
    }
    return result * st.dir;
  });
}
function shortRow(r){
  const [cls, label] = TM[r.tm] || ['none', r.tm];
  const label_ = r.d.slice(0, -3);
  return `<div class="row" role="button" tabindex="0" aria-expanded="false" data-d="${esc(r.d)}">
    <span class="rank">${r.r}</span>
    <span class="dom">${esc(label_)}<em>.si</em>${r.owned ? '<span class="owned-badge">Owned</span>' : ''}</span>
    <span class="c-cat"><span class="pill">${esc(CAT[r.c] || r.c)}</span></span>
    <span class="c-total total"><b>${r.t}</b><span class="bar"><div style="width:${r.t}%"></div></span></span>
    <span class="c-mini minis" title="${PARTS.map((p,i) => p + ' ' + r.s[i]).join(' / ')}">${r.s.map(v => `<div style="height:${Math.max(8, v)}%"></div>`).join('')}</span>
    <span class="c-tm"><span class="tm ${cls}">${label}</span></span>
    <span class="caret">></span></div>
  <div class="detail">${shortDetail(r)}</div>`;
}
function shortDetail(r){
  const availability = r.owned
    ? `<p><b>${esc(r.owned_status)}</b></p><p>Registry evidence is pre-purchase history (${esc(r.rdap[1])}; ${esc(r.whois[1])}).</p>`
    : `<p>RDAP <b>${esc(r.rdap[0])}</b> (not found) at ${esc(r.rdap[1])}<br>WHOIS <b>${esc(String(r.whois[0]).replace('_',' '))}</b> at ${esc(r.whois[1])}</p>`;
  const cov = r.cov.length ? r.cov.map(([s,status,n,m]) => { const [c,l] = COV[status] || ['mute', status];
      return `<div class="src"><span>${esc(s)}</span><span class="${c}">${esc(l)}</span></div>`; }).join('')
    : '<p class="mute">Profitdesk.si was screened at the owner request; other names outside the top 100 have not been screened by USPTO.</p>';
  return `<div class="dgrid">
    <div><h4>Why it ranks here</h4><p>${esc(r.why)}</p>
      <h4>Availability evidence</h4>${availability}</div>
    <div><h4>Score breakdown</h4>${PARTS.map((p,i) => `<div class="sc"><span>${p}</span><span class="bar"><div style="width:${r.s[i]}%"></div></span><span>${r.s[i]}</span></div>`).join('')}</div>
    <div><h4>Trademark screen</h4>${cov}<h4>Valuation</h4><p class="mute">${esc(r.val)}</p></div></div>`;
}
function scoreBars(r){
  if (r.t == null || !r.s || r.s.some(v => v == null)) return '<span class="mute">No score</span>';
  return `<span class="c-mini minis" title="${PARTS.map((p,i) => p + ' ' + r.s[i]).join(' / ')}">${r.s.map(v => `<div style="height:${Math.max(8, v)}%"></div>`).join('')}</span>`;
}
function availableRow(r){
  const label_ = r.d.slice(0, -3);
  const reason = r.r == null ? (r.why || 'No exclusion reason recorded') : 'In Top 500';
  return `<div class="row available" role="button" tabindex="0" aria-expanded="false" data-d="${esc(r.d)}">
    <span class="rank">${r.r == null ? '\u2014' : r.r}</span>
    <span class="dom">${esc(label_)}<em>.si</em>${r.owned ? '<span class="owned-badge">Owned</span>' : ''}</span>
    <span class="c-cat"><span class="pill">${esc(CAT[r.c] || r.c)}</span></span>
    <span class="c-total total"><b>${r.t == null ? '\u2014' : r.t}</b>${r.t == null ? '' : `<span class="bar"><div style="width:${r.t}%"></div></span>`}</span>
    ${scoreBars(r)}<span class="c-why"><span class="reason-pill">${esc(reason)}</span></span><span class="caret">></span></div>
  <div class="detail">${availableDetail(r)}</div>`;
}
function availableDetail(r){
  const score = r.t == null || !r.s || r.s.some(v => v == null)
    ? '<p class="mute">No score is recorded for this name.</p>'
    : PARTS.map((p,i) => `<div class="sc"><span>${p}</span><span class="bar"><div style="width:${r.s[i]}%"></div></span><span>${r.s[i]}</span></div>`).join('');
  const why = r.r == null ? `<p>${esc(r.why || 'No exclusion reason recorded in the workbook.')}</p>` : `<p>Shortlist rank <b>${r.r}</b>.</p>`;
  const evidence = r.owned
    ? `<p><b>${esc(r.owned_status)}</b></p><p>Registry observations are pre-purchase history (${esc(r.rdap[2])}; ${esc(r.whois[1])}).</p>`
    : `<p>RDAP <b>${esc(r.rdap[0])}</b> (${esc(r.rdap[1])}) at ${esc(r.rdap[2])}<br>WHOIS <b>${esc(r.whois[0])}</b> at ${esc(r.whois[1])}</p>`;
  return `<div class="dgrid"><div><h4>Why it is outside the 500</h4>${why}<h4>Availability evidence</h4>${evidence}</div><div><h4>Score breakdown</h4>${score}</div><div><h4>Category</h4><p>${esc(CAT[r.c] || r.c)}</p></div></div>`;
}
function unavailableRow(r){
  const label_ = r.d.slice(0, -3);
  const timestamp = r.evidence_time ? `${r.evidence_source} \u00b7 ${r.evidence_time}` : 'Local rule \u00b7 no registry timestamp';
  return `<div class="row unavailable" role="button" tabindex="0" aria-expanded="false" data-d="${esc(r.d)}">
    <span class="dom">${esc(label_)}<em>.si</em></span>
    <span class="c-category"><span class="pill">${esc(CAT[r.c] || r.c)}</span></span>
    <span class="c-reason"><span class="reason-pill">${esc(r.reason)}</span></span>
    <span class="c-stamp timestamp">${esc(timestamp)}</span><span class="caret">></span></div>
  <div class="detail">${unavailableDetail(r)}</div>`;
}
function unavailableDetail(r){
  const why = r.reason_detail ? `<p>${esc(r.reason_detail)}</p>` : '';
  const evidence = r.evidence_time
    ? `<p>${esc(r.evidence_source)} evidence timestamp: <b>${esc(r.evidence_time)}</b></p>`
    : '<p>This is a local known-rule classification; the workbook has no registry timestamp for the rule itself.</p>';
  return `<div class="dgrid"><div><h4>Why unavailable</h4><p><b>${esc(r.reason)}</b></p>${why}</div><div><h4>Evidence timestamp</h4>${evidence}</div><div><h4>Category</h4><p>${esc(CAT[r.c] || r.c)}</p></div></div>`;
}
function head(){
  const arrow = k => st.sort === k ? (st.dir > 0 ? ' ^' : ' v') : '';
  if (st.mode === 'unavailable') return `<div class="row head unavailable"><button data-s="d">Domain${arrow('d')}</button><span class="c-category">Category</span><span>Reason</span><span class="c-stamp">Evidence timestamp</span><span></span></div>`;
  if (st.mode === 'available') return `<div class="row head available"><button data-s="r">Rank${arrow('r')}</button><button data-s="d">Domain${arrow('d')}</button>
    <span class="c-cat">Category</span><button class="c-total" data-s="t">Total score${arrow('t')}</button>
    <span class="c-mini">Breakdown</span><span class="c-why">Why outside 500</span><span></span></div>`;
  return `<div class="row head"><button data-s="r">#${arrow('r')}</button><button data-s="d">Domain${arrow('d')}</button>
    <span class="c-cat">Category</span><button class="c-total" data-s="t">Score${arrow('t')}</button>
    <span class="c-mini" title="Brandability, commercial, shortness, hack, resale, trademark">Breakdown</span><span class="c-tm">Trademark</span><span></span></div>`;
}
function render(){
  const rs = filtered();
  const source = sourceRows();
  $('count').textContent = `${rs.length.toLocaleString()} of ${source.length.toLocaleString()} names`;
  const start = st.mode === 'top' ? 0 : st.page * PAGE_SIZE;
  const visible = st.mode === 'top' ? rs.slice(0, st.shown) : rs.slice(start, start + PAGE_SIZE);
  const drawRow = st.mode === 'top' ? shortRow : st.mode === 'available' ? availableRow : unavailableRow;
  $('table').innerHTML = head() + (visible.length ? visible.map(drawRow).join('') : '<div class="empty">No names match these filters.</div>');
  $('more').hidden = rs.length <= st.shown;
  $('more').textContent = `Show more (${rs.length - st.shown} left)`;
  $('pager').hidden = st.mode === 'top';
  const pageCount = Math.max(1, Math.ceil(rs.length / PAGE_SIZE));
  const from = rs.length ? start + 1 : 0;
  const to = Math.min(start + PAGE_SIZE, rs.length);
  $('page-label').textContent = `Rows ${from.toLocaleString()}\u2013${to.toLocaleString()} of ${rs.length.toLocaleString()} \u00b7 page ${st.page + 1} of ${pageCount}`;
  $('previous-page').disabled = st.page === 0;
  $('next-page').disabled = st.page + 1 >= pageCount;
}
$('table').addEventListener('click', e => {
  const s = e.target.closest('[data-s]');
  if (s) { st.dir = st.sort === s.dataset.s ? -st.dir : 1; st.sort = s.dataset.s; resetPaging(); render(); return; }
  const r = e.target.closest('.row:not(.head)'); if (!r) return;
  const open = r.getAttribute('aria-expanded') !== 'true';
  r.setAttribute('aria-expanded', open); r.nextElementSibling.classList.toggle('open', open);
});
$('table').addEventListener('keydown', e => { if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('row')) { e.preventDefault(); e.target.click(); } });
$('cats').addEventListener('click', e => {
  const b = e.target.closest('.chip'); if (!b) return;
  st.owned = b.dataset.owned === 'true'; st.cat = st.owned ? '' : b.dataset.c;
  resetPaging(); drawCategories(); render();
});
$('q').oninput = e => { st.q = e.target.value.trim().toLowerCase(); resetPaging(); render(); };
$('tmf').onchange = e => { st.tm = e.target.value; resetPaging(); render(); };
$('reasonf').onchange = e => { st.reason = e.target.value; resetPaging(); render(); };
$('len').onchange = e => { st.len = e.target.value; resetPaging(); render(); };
$('more').onclick = () => { st.shown += 100; render(); };
$('previous-page').onclick = () => { st.page = Math.max(0, st.page - 1); render(); };
$('next-page').onclick = () => { st.page++; render(); };
$('list').addEventListener('click', e => { const tab = e.target.closest('[role="tab"]'); if (tab) selectMode(tab.dataset.mode, false); });
$('list').addEventListener('keydown', e => {
  const tab = e.target.closest('[role="tab"]'); if (!tab) return;
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  let next = tabs.indexOf(tab);
  if (e.key === 'ArrowRight') next = (next + 1) % tabs.length;
  else if (e.key === 'ArrowLeft') next = (next - 1 + tabs.length) % tabs.length;
  else if (e.key === 'Home') next = 0;
  else if (e.key === 'End') next = tabs.length - 1;
  else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectMode(tab.dataset.mode, false); return; }
  else return;
  e.preventDefault(); selectMode(tabs[next].dataset.mode, true);
});
drawReasonFilter(); updateControls(); drawCategories(); render();

$('avail').innerHTML = '<tr><th>Category</th><th style="text-align:right">Candidates</th><th style="text-align:right">Eligible (snapshot)</th><th style="text-align:right">In the 500</th></tr>'
  + D.avail.sort((a,b) => b.final - a.final).map(a => `<tr><td>${esc(CAT[a.cat] || a.cat)}</td><td class="n">${a.pool.toLocaleString()}</td><td class="n">${a.eligible.toLocaleString()}</td><td class="n"><b>${a.final}</b></td></tr>`).join('');
$('sales').innerHTML = '<tr><th>Domain sold</th><th style="text-align:right">Price</th><th>Date</th><th>Venue</th><th>Source</th></tr>'
  + D.sales.sort((a,b) => b.amount - a.amount).map(s => `<tr><td><b>${esc(s.sold_domain)}</b></td><td class="n">${esc(s.currency)} ${Number(s.amount).toLocaleString()}</td><td>${esc(s.transaction_date)}</td><td>${esc(s.venue)}</td><td><a href="${esc(s.source_url)}" target="_blank" rel="noopener">link</a></td></tr>`).join('');
})();
</script>
</body>
</html>
"""

screened = sum(1 for r in rows if r["cov"])
page = (page.replace("__DATA__", data).replace("__CANDS__", f"{cands:,}")
        .replace("__AVAILABLE__", f"{len(available_rows):,}").replace("__RANKED__", f"{len(short):,}")
        .replace("__UNAVAILABLE__", f"{len(unavailable_rows):,}").replace("__SCREENED__", str(screened))
        .replace("__WEIGHTS__", E(weights[0].upper() + weights[1:] if weights else ""))
        .replace("__RDAPR__", E(rdap_range)).replace("__WHOISR__", E(whois_range)).replace("__TMR__", E(tm_range))
        .replace("__RDAPC__", E(rdap_counts)).replace("__WHOISC__", E(whois_counts))
        .replace("__OWNED_SUMMARY__", owned_summary).replace("__OWNED_COUNT__", str(owned_count)))
wb.close()
rendered = page.encode("ascii")
if args.check:
    if not OUT.is_file() or OUT.read_bytes() != rendered:
        print(f"HTML report differs from {OUT}", file=sys.stderr)
        sys.exit(1)
    print(f"HTML report matches {OUT}")
else:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(rendered)
    print(OUT, f"{len(rendered) / 1024:.0f} KB", "rows", len(rows), "owned", owned_count, "screened", screened, "sales", len(sales), "categories", len(avail))
