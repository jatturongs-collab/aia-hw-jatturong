"""Dividend Scan: คัดหุ้นทั้งตลาดด้วยด่านปันผล ติดป้ายกลยุทธ์ value ให้คะแนน แล้วสร้าง CSV + HTML

เกณฑ์ทั้งหมดอยู่ใน spec.md หัวข้อ 4 ถ้าแก้เกณฑ์ให้แก้ทั้งสองที่

รัน (WSL):
    python3 tools/dividend_scan.py --db /mnt/c/AI-investor-alpha/db/stocks.db [--top 15]

ได้ไฟล์ output/dividend_scan.csv และ output/dividend_scan.html
"""

import argparse
import csv
import json
import sqlite3
from pathlib import Path

YEARS = [2021, 2022, 2023, 2024, 2025]
MIN_YIELD = 3.0                   # %
PAYOUT_MIN, PAYOUT_MAX = 0.30, 0.80
MAX_DPS_CUTS = 1
S1_CASH_MCAP, S1_MAX_DE = 0.50, 1.0
# น้ำหนักคะแนน (รวม 100) ปรับได้หลังเห็นผลรอบแรก
W_YIELD, W_DPS_CAGR, W_PAYOUT, W_RETURN_UP, W_RETURN_LEVEL, W_BADGE = 30, 25, 15, 15, 5, 5

FIN_ENTITY = {"bank", "insurance", "property fund / REIT"}
FIN_SECTOR = {"BANK", "FIN", "INSUR", "PF&REIT", "Financials"}
# ใช้จาก Jitta แค่ DPS กับ Market Cap เพราะตัวชี้วัดอื่นของ Jitta ปนหน่วยกันตามรอบที่ดึง
# (เช่น ROE ปี 2021 เป็นสัดส่วน ปี 2022–2025 เป็น %) ตัวเลขงบจึงคำนวณจาก SETSMART แทน
JITTA_METRICS = ("dividend_per_share", "market_cap")


def set_url(t):
    return f"https://www.set.or.th/th/market/product/stock/quote/{t}/factsheet"


def jitta_url(t):
    return f"https://www.jitta.com/stock/bkk:{t.lower()}"


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(con):
    q = lambda sql, *p: con.execute(sql, p).fetchall()
    jitta, jitta_date = {}, {}
    marks = ",".join("?" * len(JITTA_METRICS))
    for t, m, p, v, u in q(f"SELECT ticker, metric_name, period, value, updated_at FROM jitta_metrics "
                           f"WHERE period_type='annual' AND period BETWEEN '2021' AND '2025' "
                           f"AND metric_name IN ({marks})", *JITTA_METRICS):
        jitta.setdefault(t, {}).setdefault(m, {})[int(p)] = num(v)
        jitta_date[t] = max(jitta_date.get(t, ""), (u or "")[:10])
    stats = {}
    for t, period, date, close, pe, mcap, dy, payout, upd in q(
            "SELECT ticker, period, date, close_price, pe, market_cap, dividend_yield, "
            "dividend_payout_ratio, updated_at FROM set_trading_stats WHERE period IN ('YTD','2025')"):
        stats.setdefault(t, {})[period] = dict(date=(date or "")[:10], close=num(close), pe=num(pe),
                                               mcap=num(mcap), dy=num(dy), payout=num(payout))
    info = {t: dict(name=n, sector=s, industry=i) for t, n, s, i in
            q("SELECT ticker, name, sector, industry FROM fs_stocks")}
    entity = dict(q("SELECT ticker, entity_type FROM companies"))
    latest_bs = {}
    for t, period, cash, sti, de, re_ in q(
            "SELECT symbol, period, cash, short_term_investments, debt_to_equity, retained_earnings "
            "FROM fundamentals f WHERE period = (SELECT MAX(period) FROM fundamentals g "
            "WHERE g.symbol=f.symbol AND g.total_equity IS NOT NULL)"):
        latest_bs[t] = dict(period=period, cash=(num(cash) or 0) + (num(sti) or 0), de=num(de),
                            retained=num(re_))
    # งบรายปีตามปีบัญชีของบริษัท จาก SETSMART รายไตรมาส (ต้องครบ 4 ไตรมาส)
    annual = {}
    for t, fy, fq, ebit, tax, pbt, rev, np_, ta, cl, cash, sti, roe in q(
            "SELECT symbol, fiscal_year, fiscal_quarter, ebit, income_tax_expense, profit_before_tax, "
            "total_revenue, net_profit_parent, total_assets, total_current_liabilities, cash, "
            "short_term_investments, roe_ttm_pct FROM fundamentals WHERE fiscal_year BETWEEN 2021 AND 2025"):
        a = annual.setdefault(t, {}).setdefault(fy, dict(n=0, ebit=0, tax=0, pbt=0, rev=0, np=0))
        a["n"] += 1
        for k, v in (("ebit", ebit), ("tax", tax), ("pbt", pbt), ("rev", rev), ("np", np_)):
            if v is None:
                a[k] = None
            elif a[k] is not None:
                a[k] += v
        if fq == 4:
            a.update(ta=ta, cl=cl, cash=(cash or 0) + (sti or 0), roe=roe)
    set_dps = {}
    for t, y, d in q("SELECT ticker, substr(xd,1,4), SUM(dividend) FROM set_dividends GROUP BY 1, 2"):
        set_dps.setdefault(t, {})[int(y)] = round(num(d) or 0, 4)
    bond = q("SELECT value, as_of, url FROM bond_yield")[0]
    return jitta, jitta_date, stats, info, entity, latest_bs, annual, set_dps, bond


def series(j, metric):
    return [j.get(metric, {}).get(y) for y in YEARS]


def full_year(annual, t, y):
    a = annual.get(t, {}).get(y)
    return a if a and a["n"] == 4 and "ta" in a else None


def roic_series(annual, t):
    """ROIC = EBIT × (1 − อัตราภาษี) ÷ (สินทรัพย์รวม − หนี้สินหมุนเวียน − เงินสด) ณ สิ้นปีบัญชี"""
    out = []
    for y in YEARS:
        a = full_year(annual, t, y)
        if not a or None in (a["ebit"], a["ta"], a["cl"]):
            out.append(None)
            continue
        tax_rate = min(max(abs(a["tax"] or 0) / a["pbt"], 0), 1) if a["pbt"] and a["pbt"] > 0 else 0
        ic = a["ta"] - a["cl"] - a["cash"]
        out.append(a["ebit"] * (1 - tax_rate) / ic if ic > 0 else None)
    return out


def roe_series(annual, t):
    return [(full_year(annual, t, y) or {}).get("roe") for y in YEARS]


def scan(con, top):
    jitta, jitta_date, stats, info, entity, latest_bs, annual, set_dps, bond = load(con)
    bond_yield = bond[0]
    universe = sorted(stats)
    funnel = {"universe": len(universe), "yield": 0, "payout": 0, "dps": 0}
    rows = []
    for t in universe:
        j = jitta.get(t, {})
        ytd, s25 = stats[t].get("YTD", {}), stats[t].get("2025", {})
        meta = info.get(t, {})
        is_fin = entity.get(t) in FIN_ENTITY or meta.get("sector") in FIN_SECTOR

        # ด่าน 1: yield (ใช้ SET อย่างเดียว ไม่สำรองด้วย Jitta เพราะ yield ของ Jitta ปนหน่วย % กับสัดส่วน)
        dy, src_dy = ytd.get("dy"), f"SET set_trading_stats YTD {ytd.get('date')}"
        if dy is None or dy <= MIN_YIELD:
            continue
        funnel["yield"] += 1

        # ด่าน 2: payout ปี 2025 (SET อย่างเดียว ด้วยเหตุผลเดียวกัน)
        payout, src_payout = s25.get("payout"), f"SET set_trading_stats 2025 {s25.get('date')}"
        if payout is None or not PAYOUT_MIN <= payout <= PAYOUT_MAX:
            continue
        funnel["payout"] += 1

        # ด่าน 3: DPS เพิ่มขึ้น จ่ายทุกปี 2021–2025 และลดได้ไม่เกิน 1 ครั้ง
        dps = series(j, "dividend_per_share")
        if None in dps or min(dps) <= 0 or dps[-1] <= dps[0]:
            continue
        cuts = sum(1 for a, b in zip(dps, dps[1:]) if b < a)
        if cuts > MAX_DPS_CUTS:
            continue
        funnel["dps"] += 1
        dps_cagr = (dps[-1] / dps[0]) ** (1 / (len(YEARS) - 1)) - 1

        # ตัวชี้วัดประกอบ: ROIC (กลุ่มการเงินใช้ ROE)
        ret = roe_series(annual, t) if is_fin else roic_series(annual, t)
        ret_name = "ROE" if is_fin else "ROIC"
        known = [(y, v) for y, v in zip(YEARS, ret) if v is not None]
        ret_up = len(known) >= 2 and known[-1][1] > known[0][1]
        ret_last = known[-1][1] if known else None

        # ป้าย S1: ป้อมปราการเงินสด (ไม่ใช้กับกลุ่มการเงิน)
        bs = latest_bs.get(t)
        mcap_m = ytd["mcap"] / 1e6 if ytd.get("mcap") else None
        cash_mcap = bs["cash"] / mcap_m if bs and mcap_m else None
        s1 = (not is_fin and cash_mcap is not None and cash_mcap >= S1_CASH_MCAP
              and bs["de"] is not None and bs["de"] < S1_MAX_DE and (bs["retained"] or 0) > 0)

        # ป้าย S3: โตสวนราคา 2022 → 2025 (รายได้ กำไร จาก SETSMART · Market Cap จาก Jitta)
        a22, a25 = full_year(annual, t, 2022) or {}, full_year(annual, t, 2025) or {}
        rev22, rev25, np22, np25 = a22.get("rev"), a25.get("rev"), a22.get("np"), a25.get("np")
        mc22, mc25 = j.get("market_cap", {}).get(2022), j.get("market_cap", {}).get(2025)
        pct = lambda a, b: (b - a) / abs(a) if a not in (None, 0) and b is not None else None
        rev_chg, np_chg, mc_chg = pct(rev22, rev25), pct(np22, np25), pct(mc22, mc25)
        s3 = (rev_chg is not None and np_chg is not None and mc_chg is not None
              and rev_chg > 0 and np_chg > 0 and np25 > 0 and mc_chg <= 0)

        badges = [b for b, ok in (("S1", s1), ("S3", s3)) if ok]
        score = (W_YIELD * min(dy, 8) / 8
                 + W_DPS_CAGR * max(0, min(dps_cagr, 0.20)) / 0.20
                 + W_PAYOUT * max(0, 1 - abs(payout - 0.55) / 0.25)
                 + W_RETURN_UP * ret_up
                 + W_RETURN_LEVEL * (ret_last is not None and ret_last >= 0.10)
                 + W_BADGE * len(badges))

        rows.append(dict(
            ticker=t, name=meta.get("name"), sector=meta.get("sector"), financial=is_fin,
            score=round(score, 1), badges=" ".join(badges),
            price=ytd.get("close"), price_date=ytd.get("date"), pe=ytd.get("pe"),
            yield_pct=round(dy, 2), spread_vs_bond_pct=round(dy - bond_yield, 2), src_yield=src_dy,
            payout_2025=round(payout, 3), src_payout=src_payout,
            dps_cagr_pct=round(dps_cagr * 100, 1), dps_cuts=cuts,
            **{f"dps_{y}": round(v, 4) for y, v in zip(YEARS, dps)},
            src_dps=f"Jitta annual dividend_per_share ({jitta_date.get(t)})",
            return_metric=ret_name,
            **{f"ret_{y}": (round(v, 4) if v is not None else None) for y, v in zip(YEARS, ret)},
            return_up=ret_up,
            src_return="SETSMART fundamentals ปีบัญชี " + ("roe_ttm_pct ณ Q4" if is_fin else "EBIT, ภาษี, งบดุล ณ Q4"),
            cash_mcap=round(cash_mcap, 3) if cash_mcap is not None else None,
            de=round(bs["de"], 2) if bs and bs["de"] is not None else None,
            src_cash_de=f"SETSMART fundamentals {bs['period']} + SET market cap YTD" if bs else None,
            rev_chg_22_25=round(rev_chg, 3) if rev_chg is not None else None,
            np_chg_22_25=round(np_chg, 3) if np_chg is not None else None,
            mcap_chg_22_25=round(mc_chg, 3) if mc_chg is not None else None,
            src_growth=f"SETSMART รายได้/กำไรปีบัญชี · Jitta market_cap ({jitta_date.get(t)})",
            set_dps_by_xd_year=json.dumps(set_dps.get(t, {})),
            src_set_dps="SET set_dividends (ตามประกาศจริง, รวมตามปี XD)",
            url_set=set_url(t), url_jitta=jitta_url(t),
        ))
    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows, 1):
        r["rank"], r["shortlist"] = i, i <= top
    return rows, funnel, dict(value=bond_yield, as_of=bond[1], url=bond[2])


def write_csv(rows, path):
    cols = ["rank", "shortlist"] + [k for k in rows[0] if k not in ("rank", "shortlist")]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_html(rows, funnel, bond, top, path):
    template = (Path(__file__).parent / "dividend_scan_template.html").read_text(encoding="utf-8")
    data = dict(rows=rows, funnel=funnel, bond=bond, top=top, years=YEARS,
                criteria=dict(min_yield=MIN_YIELD, payout_min=PAYOUT_MIN, payout_max=PAYOUT_MAX,
                              max_cuts=MAX_DPS_CUTS, s1_cash_mcap=S1_CASH_MCAP, s1_max_de=S1_MAX_DE))
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    path.write_text(template.replace("/*__DATA__*/null", payload), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "output"))
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows, funnel, bond = scan(con, args.top)
    out = Path(args.out)
    write_csv(rows, out / "dividend_scan.csv")
    write_html(rows, funnel, bond, args.top, out / "dividend_scan.html")
    print(f"หุ้นทั้งหมด {funnel['universe']} → yield > {MIN_YIELD}% {funnel['yield']} "
          f"→ payout {PAYOUT_MIN:.0%}–{PAYOUT_MAX:.0%} {funnel['payout']} → DPS เพิ่ม {funnel['dps']}")
    print(f"shortlist {min(args.top, len(rows))} ตัว:")
    for r in rows[:args.top]:
        print(f"  {r['rank']:>2}. {r['ticker']:8} score {r['score']:5.1f}  yield {r['yield_pct']:5.2f}%  "
              f"payout {r['payout_2025']:.0%}  DPS CAGR {r['dps_cagr_pct']:5.1f}%  "
              f"{r['return_metric']} {'ขึ้น' if r['return_up'] else 'ลง'}  {r['badges']}")


if __name__ == "__main__":
    main()
