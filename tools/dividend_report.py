"""สร้างรายงานผล Dividend Scan เป็น Markdown และ HTML

อ่านข้อมูลที่ฝังอยู่ใน output/dividend_scan.html จึงต้องรัน dividend_scan.py ก่อน ไม่ต้องเปิดฐานข้อมูล
ส่งออก output/dividend_scan_report.md และ output/dividend_scan_report.html

รัน: python3 tools/dividend_report.py
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ผลตรวจมือเมื่อ 2026-11-04 (ดู prompts.md รอบ 4) แก้ที่นี่เมื่อตรวจใหม่
CHECK_DATE = "2026-11-04"
# DPS ปี 2025: Jitta ต่างจาก set_dividends ที่รวมตามงวดผลประกอบการ
DPS_MISMATCH = {"KTB": 2.67, "BH": 11.0, "HUMAN": 0.20, "AMATA": 0.75, "DITTO": 0.25}
# payout แบบ YTD บนหน้า factsheet ณ 2026-11-03 เกินเพดาน ตรวจแค่ SECURE, KTB, CPALL
YTD_PAYOUT = {"SECURE": 0.95, "KTB": 0.88}
SITE_CHECK = [
    # ticker, payout 2025, DPS 2021-2024, DPS 2025, ผล
    ("SECURE", "0.53 ตรง", "ตรง", "1.00 ตรง", "ตรง"),
    ("KTB", "0.58 ตรง", "ตรง", "Jitta 2.07, SET 2.67", "ไม่ตรง"),
    ("CPALL", "0.43 ตรง", "ตรง", "1.65 ตรง", "ตรง"),
]


def load(path):
    m = re.search(r'=\s*(\{"(?:.|\n)*?\})\s*;\s*\n', path.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit(f"ไม่พบข้อมูลใน {path} ให้รัน dividend_scan.py ก่อน")
    return json.loads(m.group(1))


def num(v, digits=2):
    return "-" if v is None else f"{v:,.{digits}f}"


def pct(v, digits=1):
    return "-" if v is None else f"{v * 100:.{digits}f}%"


def flags(r):
    out = []
    t = r["ticker"]
    if t in DPS_MISMATCH:
        out.append(f"DPS 2025 ไม่ตรง SET ({num(DPS_MISMATCH[t])})")
    if t in YTD_PAYOUT:
        out.append(f"payout YTD {YTD_PAYOUT[t]:.2f}")
    return ", ".join(out) or "-"


def table(head, align, rows):
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join(align) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def build_md(d, today):
    rows, f, b, c = d["rows"], d["funnel"], d["bond"], d["criteria"]
    top = [r for r in rows if r["shortlist"]]
    rest = [r for r in rows if not r["shortlist"]]
    dates = sorted({r["price_date"] for r in rows if r["price_date"]})
    s1 = sum("S1" in r["badges"] for r in rows)
    s3 = sum("S3" in r["badges"] for r in rows)
    fin = sum(bool(r["financial"]) for r in rows)
    top_mismatch = [r["ticker"] for r in top if r["ticker"] in DPS_MISMATCH]
    other_mismatch = [t for t in DPS_MISMATCH if t not in top_mismatch]

    funnel = table(
        ["ด่าน", "เงื่อนไข", "เหลือ", "คัดออก"], ["---", "---", "--:", "--:"],
        [["เริ่มต้น", "หุ้นทั้งหมดในฐานข้อมูล", f"{f['universe']:,}", "-"],
         ["Yield", f"มากกว่า {c['min_yield']:.0f}% (YTD)", f["yield"], f["universe"] - f["yield"]],
         ["Payout", f"{c['payout_min'] * 100:.0f}–{c['payout_max'] * 100:.0f}% (ปี 2025)", f["payout"], f["yield"] - f["payout"]],
         ["DPS", f"ปี 2025 สูงกว่าปี 2021 และลดได้ไม่เกิน {c['max_cuts']} ครั้ง", f["dps"], f["payout"] - f["dps"]],
         ["Shortlist", f"คะแนนสูงสุด {len(top)} อันดับ", len(top), f["dps"] - len(top)]])

    shortlist = table(
        ["#", "หุ้น", "กลุ่ม", "คะแนน", "Yield", "Payout 2025", "DPS 2021", "DPS 2025", "DPS โตต่อปี", "ผลตอบแทน 2021 → 2025", "ป้าย", "ต้องตรวจ"],
        ["--:", "---", "---", "--:", "--:", "--:", "--:", "--:", "--:", "---", "---", "---"],
        [[r["rank"], f"[{r['ticker']}]({r['url_set']})", r["sector"], num(r["score"], 1), f"{r['yield_pct']:.2f}%",
          pct(r["payout_2025"], 0), num(r["dps_2021"], 3), num(r["dps_2025"], 3), f"{r['dps_cagr_pct']:.1f}%",
          f"{r['return_metric']} {pct(r['ret_2021'])} → {pct(r['ret_2025'])}", r["badges"] or "-", flags(r)] for r in top])

    appendix = table(
        ["#", "หุ้น", "กลุ่ม", "คะแนน", "Yield", "Payout 2025", "DPS โตต่อปี", "ป้าย", "ต้องตรวจ"],
        ["--:", "---", "---", "--:", "--:", "--:", "--:", "---", "---"],
        [[r["rank"], f"[{r['ticker']}]({r['url_set']})", r["sector"], num(r["score"], 1), f"{r['yield_pct']:.2f}%",
          pct(r["payout_2025"], 0), f"{r['dps_cagr_pct']:.1f}%", r["badges"] or "-", flags(r)] for r in rest])

    check = table(["หุ้น", "Payout 2025", "DPS 2021–2024", "DPS 2025", "ผล"], ["---"] * 5,
                  [list(r) for r in SITE_CHECK])

    sources = sorted({r[k] for r in rows for k in ("src_yield", "src_payout", "src_dps", "src_return") if r.get(k)})
    # วันที่ราคาต่างกันรายหุ้น จึงตัดวันที่ออกจากแหล่ง yield เพื่อไม่ให้รายการยาวซ้ำ
    sources = sorted({re.sub(r" \d{4}-\d{2}-\d{2}$", "", s) for s in sources})

    return f"""# รายงาน Dividend Scan

สร้างเมื่อ {today} · ราคาและ yield ของแต่ละหุ้นเป็นข้อมูลวันที่ {dates[0]} ถึง {dates[-1]} · เพื่อการศึกษา ไม่ใช่คำแนะนำซื้อขาย

## สรุป

- จากหุ้น {f['universe']:,} ตัว มี {f['dps']} ตัวที่ผ่านด่านปันผลครบ และเลือก {len(top)} ตัวที่คะแนนสูงสุดเป็น shortlist สำหรับศึกษาต่อ
- อันดับแรกคือ {', '.join(r['ticker'] for r in top[:3])} รายชื่อทั้งหมดอยู่ในตาราง shortlist
- **ผลนี้ยังตรวจไม่ครบ:** DPS ปี 2025 ของ {' และ '.join(top_mismatch)} ใน shortlist ไม่ตรงกับ SET ต้องตรวจกับเอกสารของบริษัทก่อนใช้ตัวเลข
- ใน {f['dps']} ตัวมีป้าย S1 {s1} ตัว ป้าย S3 {s3} ตัว และเป็นกลุ่มการเงินหรือ REIT {fin} ตัว
- Yield ของพันธบัตรรัฐบาล 10 ปีอยู่ที่ {b['value']:.2f}% ณ {b['as_of']} ([ThaiBMA]({b['url']}))

## ผลคัดกรองแต่ละด่าน

{funnel}

## Shortlist {len(top)} ตัว

DPS เป็นบาทต่อหุ้นตามปีผลประกอบการ จาก Jitta ผลตอบแทนคือ ROIC ส่วนกลุ่มการเงินและ REIT ใช้ ROE คำนวณจาก SETSMART ชื่อหุ้นลิงก์ไปหน้า factsheet ของ SET เครื่องหมาย - คือไม่มีข้อมูลหรือไม่มีเรื่องต้องตรวจ

{shortlist}

## เรื่องที่ต้องตรวจก่อนใช้ผล

- **DPS ของ Jitta ไม่ตรงกับ SET บางจุด:** เทียบได้ 229 จุด ไม่ตรง 14 จุดใน 9 หุ้น และเทียบไม่ได้อีก 66 จุดเพราะไม่มีข้อมูลงวด ยังไม่รู้สาเหตุทุกจุด
- **อาจผ่านด่านเกินจริง:** {', '.join(t for t in other_mismatch if t != 'KTB')} มี DPS ปี 2025 จาก Jitta สูงกว่า SET ถ้าใช้ตัวเลข SET ผลอาจเปลี่ยน
- **อาจตกด่านผิด:** ยังไม่ได้ตรวจหุ้นที่ตกด่าน DPS ไปแล้ว ซึ่งอาจตกเพราะตัวเลข Jitta ผิด
- **Payout ปีล่าสุดอาจดูดีเกินจริง:** เกณฑ์ใช้ปี 2025 แต่ payout แบบ YTD ของ SECURE คือ 0.95 และ KTB คือ 0.88 เกินเพดาน 80% ทั้งคู่ และกำไรครึ่งแรกปี 2569 ของ SECURE ลดลง 21.82%
- **DPS โตต่อปีบางตัวสูงเพราะฐานต่ำ:** ปี 2021 เป็นฐานต่ำของหลายบริษัท คะแนนจึงจำกัดส่วนนี้ไว้ที่ 20% ต่อปี แต่ตารางแสดงค่าจริง

## ผลเทียบกับ set.or.th

เทียบเมื่อ {CHECK_DATE} กับหน้า factsheet ข้อมูล ณ 3 พ.ย. 2569 หุ้น 3 ตัวนี้เลือกเอง ไม่ได้สุ่ม Yield และ P/E ตรงเมื่อคำนวณใหม่ด้วยราคาวันที่ของข้อมูลใน scan เกณฑ์ "เทียบแล้วตรงกัน" ใน `spec.md` จึงยังไม่ผ่าน

{check}

## วิธีให้คะแนน

คะแนนรวม 100: yield 30 (เต็มที่ 8%), DPS โตต่อปี 25 (เต็มที่ 20%), payout ใกล้ 55% ได้ 15, ผลตอบแทนขาขึ้น 15, ผลตอบแทนปีล่าสุดตั้งแต่ 10% ได้ 5 และป้ายละ 5 คะแนน น้ำหนักนี้ AI เสนอและผู้เรียนอนุมัติในแผน ยังไม่ได้ทดสอบว่าน้ำหนักอื่นให้ผลต่างกันแค่ไหน

- **S1 ป้อมปราการเงินสด:** เงินสดและเงินลงทุนระยะสั้นตั้งแต่ {c['s1_cash_mcap'] * 100:.0f}% ของ Market Cap, D/E ต่ำกว่า {c['s1_max_de']:.1f} และกำไรสะสมเป็นบวก ไม่ใช้กับกลุ่มการเงิน
- **S3 โตสวนราคา:** รายได้และกำไรสุทธิปี 2025 สูงกว่าปี 2022 แต่ Market Cap ปี 2025 ไม่สูงกว่าปี 2022

## แหล่งข้อมูล

{chr(10).join('- ' + s for s in sources)}

ตัวเลขรายหุ้นพร้อมแหล่งและวันที่อยู่ใน `dividend_scan.csv` และดูกราฟรายปีได้ใน `dividend_scan.html`

## ภาคผนวก: หุ้นที่ผ่านด่านแต่ไม่อยู่ใน shortlist

{appendix}
"""


def inline(text):
    parts = re.split(r"(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`)", text)
    out = []
    for p in parts:
        if m := re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", p):
            out.append(f'<a href="{html.escape(m[2])}">{html.escape(m[1])}</a>')
        elif p.startswith("**") and p.endswith("**") and len(p) > 4:
            out.append(f"<strong>{html.escape(p[2:-2])}</strong>")
        elif p.startswith("`") and p.endswith("`") and len(p) > 2:
            out.append(f"<code>{html.escape(p[1:-1])}</code>")
        else:
            out.append(html.escape(p))
    return "".join(out)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_to_html(md):
    body, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("# "):
            body.append(f"<h1>{inline(line[2:])}</h1>")
            i += 1
        elif line.startswith("## "):
            body.append(f"<h2>{inline(line[3:])}</h2>")
            i += 1
        elif line.startswith("|"):
            head, align = cells(line), cells(lines[i + 1])
            cls = ["num" if a.endswith(":") else "" for a in align]
            th = "".join(f'<th class="{k}">{inline(c)}</th>' for c, k in zip(head, cls))
            i += 2
            trs = []
            while i < len(lines) and lines[i].startswith("|"):
                trs.append("<tr>" + "".join(f'<td class="{k}">{inline(c)}</td>' for c, k in zip(cells(lines[i]), cls)) + "</tr>")
                i += 1
            body.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>')
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            body.append(f"<ul>{''.join(items)}</ul>")
        else:
            body.append(f"<p>{inline(line)}</p>")
            i += 1
    return HTML_PAGE.replace("<!--BODY-->", "\n".join(body))


HTML_PAGE = """<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>รายงาน Dividend Scan</title>
<style>
  :root { --bg:#0b1120; --card:#131c31; --line:#24314f; --text:#e2e8f0; --muted:#94a3b8; --blue:#60a5fa; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font:16px/1.65 "Sarabun","Segoe UI",sans-serif; }
  .wrap { max-width:1200px; margin:0 auto; padding:32px 16px 56px; }
  h1 { font-size:28px; margin:0 0 6px; } h2 { font-size:20px; margin:36px 0 12px; }
  h1 + p { color:var(--muted); margin-top:0; }
  p, ul { max-width:820px; } li { margin:6px 0; } ul { padding-left:22px; }
  a { color:var(--blue); }
  code { background:var(--card); padding:1px 5px; border-radius:4px; font-size:14px; }
  .tbl { overflow-x:auto; border:1px solid var(--line); border-radius:12px; margin:12px 0; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th, td { padding:9px 10px; text-align:left; white-space:nowrap; border-bottom:1px solid var(--line); }
  tbody tr:last-child td { border-bottom:0; }
  th { background:#0f172a; color:var(--muted); font-weight:600; }
  .num { text-align:right; font-variant-numeric:tabular-nums; }
</style>
</head>
<body>
<div class="wrap">
<!--BODY-->
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--date", default=CHECK_DATE, help="วันที่สร้างรายงาน")
    args = ap.parse_args()
    out = Path(args.out)
    md = build_md(load(out / "dividend_scan.html"), args.date)
    (out / "dividend_scan_report.md").write_text(md, encoding="utf-8")
    (out / "dividend_scan_report.html").write_text(md_to_html(md), encoding="utf-8")
    print(f"เขียน {out / 'dividend_scan_report.md'} และ .html แล้ว")


if __name__ == "__main__":
    main()
