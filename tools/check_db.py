"""ตรวจฐานข้อมูลที่ build_db.py สร้าง: จำนวนแถว, เทียบตัวเลขข้ามแหล่ง, หุ้นที่ไม่ตรงกัน, ตัวอย่างปันผล

รัน (WSL):
    python3 tools/check_db.py --db /mnt/c/AI-investor-alpha/db/stocks.db [--symbol 2S]
"""

import argparse
import sqlite3

EXPECTED = {"fin_raw": 4_162_773, "fundamentals": 18_558, "companies": 911, "yf_info": 852,
            "fs_stocks": 1_103, "set_dividends": 5_731, "set_trading_stats": 2_881,
            "set_financial_statements": 4_770, "jitta_metrics": 1_201_302, "jitta_monthly_prices": 94_187}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--symbol", default="2S")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    q = lambda sql, *p: con.execute(sql, p).fetchall()
    ok = True

    print("== 1. จำนวนแถว")
    for t in ("fin_raw", "fundamentals", "companies", "dictionary", "yf_info", "yf_prices",
              "yf_dividends", "yf_statements", "bond_yield", "fs_stocks", "set_dividends",
              "set_trading_stats", "set_financial_statements", "set_cash_cycles", "jitta_metrics",
              "jitta_monthly_prices", "aiomax_cards", "aiomax_dividends", "source_meta"):
        n = q(f"SELECT COUNT(*) FROM {t}")[0][0]
        exp = EXPECTED.get(t)
        flag = "" if exp is None else (" OK" if n == exp else f" ผิด (ควรเป็น {exp:,})")
        ok &= exp is None or n == exp
        print(f"  {t:15} {n:>10,}{flag}")

    print("== 2. เทียบ fundamentals กับ fin_raw (2S 2021Q1 กำไรส่วนของบริษัทใหญ่)")
    f = q("SELECT net_profit_parent FROM fundamentals WHERE symbol='2S' AND period='2021Q1'")[0][0]
    r = q("SELECT value FROM fin_raw WHERE symbol='2S' AND statement='PL' AND basis='Consolidated' "
          "AND period_end='2021-03-31' AND period_type='standalone_quarter' "
          "AND line_item='Net Profit (Loss) Attributable To : Owners Of The Parent'")
    r = r[0][0] if r else None
    match = r is not None and abs(f * 1000 - r) < 1
    ok &= match
    print(f"  fundamentals = {f} ล้านบาท · fin_raw = {r} พันบาท · {'OK' if match else 'ไม่ตรง'}")

    print("== 3. หุ้นที่มีแหล่งเดียว")
    only_set = [s for (s,) in q("SELECT symbol FROM companies WHERE symbol NOT IN (SELECT symbol FROM yf_info) ORDER BY 1")]
    only_yf = [s for (s,) in q("SELECT symbol FROM yf_info WHERE symbol NOT IN (SELECT symbol FROM companies) ORDER BY 1")]
    print(f"  มีใน SETSMART ไม่มีใน Yahoo ({len(only_set)}): {', '.join(only_set)}")
    print(f"  มีใน Yahoo ไม่มีใน SETSMART ({len(only_yf)}): {', '.join(only_yf)}")

    print(f"== 4. ตัวอย่างปันผล {args.symbol}")
    for row in q("SELECT substr(xd,1,4) y, ROUND(SUM(dps),4), COUNT(*) FROM yf_dividends WHERE symbol=? "
                 "GROUP BY y ORDER BY y DESC LIMIT 6", args.symbol):
        print(f"  ปี {row[0]}: DPS รวม {row[1]} บาท ({row[2]} ครั้ง)")
    last = q("SELECT date, close FROM yf_prices WHERE symbol=? ORDER BY date DESC LIMIT 1", args.symbol)
    src = q("SELECT source_url, retrieved_utc FROM yf_info WHERE symbol=?", args.symbol)
    print(f"  ราคาล่าสุด: {last} · ที่มา: {src}")

    print("== 5. ปันผลรวม (v_dividends) แยกตามแหล่ง: SET → Yahoo → aioMax")
    for row in q("SELECT source, COUNT(DISTINCT symbol), COUNT(*), MIN(xd), MAX(xd) FROM v_dividends GROUP BY source "
                 "ORDER BY CASE source WHEN 'SET' THEN 1 WHEN 'Yahoo' THEN 2 ELSE 3 END"):
        print(f"  {row[0]:7} {row[1]:>4} หุ้น · {row[2]:>6,} งวด · {row[3]} ถึง {row[4]}")
    none = [s for (s,) in q("SELECT symbol FROM companies WHERE symbol NOT IN (SELECT symbol FROM v_dividends) ORDER BY 1")]
    print(f"  หุ้นใน SETSMART ที่ไม่มีปันผลจากแหล่งใดเลย ({len(none)}): {', '.join(none)}")

    print("== 6. เทียบปันผลข้ามแหล่ง (งวด XD เดียวกัน DPS ต่างกันเกิน 0.005 บาท)")
    diff = q("SELECT s.ticker, s.xd, s.dividend, y.dps FROM set_dividends s "
             "JOIN yf_dividends y ON y.symbol = s.ticker AND y.xd = s.xd "
             "WHERE s.dividend IS NOT NULL AND ABS(s.dividend - y.dps) > 0.005")
    same = q("SELECT COUNT(*) FROM set_dividends s JOIN yf_dividends y ON y.symbol = s.ticker AND y.xd = s.xd")[0][0]
    print(f"  SET กับ Yahoo วันเดียวกัน {same:,} งวด · ต่างกัน {len(diff):,} งวด · ตัวอย่าง: {diff[:5]}")

    print("== 7. ที่มาของข้อมูล (source_meta)")
    for row in q("SELECT source_file, table_name, rows, file_mtime_utc, imported_at_utc FROM source_meta"):
        print("  ", row)

    print("\nผลรวม:", "ผ่าน" if ok else "ไม่ผ่าน")


if __name__ == "__main__":
    main()
