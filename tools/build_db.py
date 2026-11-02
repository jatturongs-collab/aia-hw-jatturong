"""สร้างฐานข้อมูล SQLite จาก SETSMART (CSV + Excel), SET/Jitta factsheet DB, Yahoo backup zip และ cache ของ aioMax

สร้างใหม่ทั้งฐานทุกครั้ง: เขียนลง <db>.tmp ก่อน แล้วค่อย rename ทับ ถ้าล้มกลางทาง ฐานเดิมไม่พัง
ไฟล์นี้ไม่มีข้อมูลใด ๆ อยู่ข้างใน ข้อมูลอยู่นอก repo เท่านั้น (ข้อมูล SETSMART ห้ามเผยแพร่)
ลำดับแหล่งเมื่อซ้ำกัน: SET → Jitta → Yahoo → aioMax (ดู spec.md หัวข้อ Trust sources)

รัน (WSL):
    python3 tools/build_db.py --sources /mnt/c/AI-investor-alpha/sources --db /mnt/c/AI-investor-alpha/db/stocks.db \
        --factsheet /mnt/c/ai/data/factsheet/factsheets_backup.db
"""

import argparse
import glob
import json
import os
import re
import sqlite3
import zipfile
from datetime import datetime, timezone

import pandas as pd

CSV_NAME = "setsmart_financials_clean_2021q1_2026q2.csv"
XLSX_NAME = "setsmart_fundamentals_2021q1_2026q2.xlsx"
ZIP_NAME = "data_backup.zip"
DEFAULT_FACTSHEET = "/mnt/c/ai/data/factsheet/factsheets_backup.db"

# ตารางที่คัดลอกจาก factsheet DB: (ชื่อในต้นทาง, ชื่อใน stocks.db)
# เฉพาะข้อมูลที่ดึงจาก set.or.th และ Jitta ไม่เอา raw JSON snapshot และ change_log
FACTSHEET_TABLES = [
    ("stocks", "fs_stocks"),
    ("set_dividends", "set_dividends"),
    ("set_trading_stats", "set_trading_stats"),
    ("set_financial_statements", "set_financial_statements"),
    ("set_cash_cycles", "set_cash_cycles"),
    ("financial_metrics", "jitta_metrics"),
    ("monthly_prices", "jitta_monthly_prices"),
]

THAI_MONTHS = {"ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6,
               "ก.ค.": 7, "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12}


def thai_date(s):
    """'11 ธ.ค. 2568' -> '2025-12-11' (พ.ศ. - 543); แปลงไม่ได้คืน None"""
    m = re.match(r"(\d{1,2})\s+(\S+)\s+(\d{4})", s or "")
    if not m or m.group(2) not in THAI_MONTHS:
        return None
    return f"{int(m.group(3)) - 543:04d}-{THAI_MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"


def strip_bk(s):
    return s.str.replace(r"\.BK$", "", regex=True)


def file_meta(path):
    st = os.stat(path)
    return st.st_size, datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds")


def load_csv(con, path, meta):
    rows = 0
    for chunk in pd.read_csv(path, chunksize=500_000, dtype={"fiscal_year": "Int64", "fiscal_quarter": "Int64"}):
        chunk.insert(1, "symbol", strip_bk(chunk["ticker"]))
        chunk.to_sql("fin_raw", con, if_exists="append", index=False)
        rows += len(chunk)
        print(f"  fin_raw: {rows:,}", flush=True)
    meta.append((CSV_NAME, "fin_raw", rows, None))


def load_xlsx(con, path, meta):
    sheets = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
    readme = "\n".join("" if pd.isna(v) else str(v) for v in sheets["README"][0])
    for name in ("companies", "fundamentals", "dictionary"):
        df = sheets[name]
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True).infer_objects()
        df.to_sql(name, con, if_exists="replace", index=False)
        print(f"  {name}: {len(df):,}", flush=True)
        meta.append((XLSX_NAME, name, len(df), readme if name == "fundamentals" else None))


def load_zip(con, path, meta):
    info_rows, prices, divs, stmts = [], [], [], []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        fetch_log = z.read("data_backup/fetch_log.json").decode("utf-8")
        for n in names:
            if not (n.startswith("data_backup/yahoo/") and n.endswith(".json")):
                continue
            d = json.loads(z.read(n))
            sym = d["ticker"]
            info = d.get("info") or {}
            info_rows.append({"symbol": sym, "yahoo_symbol": d.get("yahoo_symbol"),
                              "retrieved_utc": d.get("retrieved_utc"), "until": d.get("until"),
                              "source_url": d.get("source_url"), **info})
            prices += [(sym, p["d"], p["c"]) for p in d.get("prices_daily") or []]
            divs += [(sym, x["xd"], x["dps"]) for x in d.get("dividends") or []]
            for st in ("income", "cashflow", "balance"):
                block = d.get(st) or {}
                periods = block.get("periods") or []
                for item, vals in (block.get("rows") or {}).items():
                    stmts += [(sym, st, item, p, v) for p, v in zip(periods, vals)]
        bond = json.loads(z.read("data_backup/thaibma_th10y.json"))

    pd.DataFrame(info_rows).to_sql("yf_info", con, if_exists="replace", index=False)
    con.execute("CREATE TABLE yf_prices (symbol TEXT, date TEXT, close REAL, PRIMARY KEY (symbol, date))")
    con.executemany("INSERT INTO yf_prices VALUES (?,?,?)", prices)
    con.execute("CREATE TABLE yf_dividends (symbol TEXT, xd TEXT, dps REAL)")
    con.executemany("INSERT INTO yf_dividends VALUES (?,?,?)", divs)
    con.execute("CREATE TABLE yf_statements (symbol TEXT, statement TEXT, line_item TEXT, period_end TEXT, value REAL)")
    con.executemany("INSERT INTO yf_statements VALUES (?,?,?,?,?)", stmts)
    pd.DataFrame([bond]).to_sql("bond_yield", con, if_exists="replace", index=False)
    for table, n in (("yf_info", len(info_rows)), ("yf_prices", len(prices)), ("yf_dividends", len(divs)),
                     ("yf_statements", len(stmts)), ("bond_yield", 1)):
        print(f"  {table}: {n:,}", flush=True)
        meta.append((ZIP_NAME, table, n, fetch_log if table == "yf_info" else None))


def load_factsheet(con, path, meta):
    con.execute("ATTACH DATABASE ? AS fs", (f"file:{path}?mode=ro",))
    for src, dst in FACTSHEET_TABLES:
        con.execute(f"CREATE TABLE {dst} AS SELECT * FROM fs.{src}")
        n = con.execute(f"SELECT COUNT(*) FROM {dst}").fetchone()[0]
        print(f"  {dst}: {n:,}", flush=True)
        meta.append((path, dst, n, None))
    con.commit()
    con.execute("DETACH DATABASE fs")
    # วันที่ XD แบบ YYYY-MM-DD ไว้เทียบกับ Yahoo / aioMax
    con.execute("ALTER TABLE set_dividends ADD COLUMN xd TEXT")
    con.execute("UPDATE set_dividends SET xd = substr(xdate, 1, 10)")


def load_aiomax(con, cache_dir, meta):
    """อ่าน cache ที่ fetch_aiomax.py เก็บไว้ (1 ไฟล์ต่อหุ้น) ลงตาราง aiomax_cards / aiomax_dividends"""
    con.execute("DROP TABLE IF EXISTS aiomax_cards")
    con.execute("DROP TABLE IF EXISTS aiomax_dividends")
    con.execute("CREATE TABLE aiomax_cards (symbol TEXT PRIMARY KEY, last_price REAL, yield REAL, dps_12m REAL, "
                "last_xd TEXT, source_url TEXT, fetched_at_utc TEXT)")
    con.execute("CREATE TABLE aiomax_dividends (symbol TEXT, xd TEXT, paid TEXT, dps REAL, type TEXT, "
                "source_url TEXT, fetched_at_utc TEXT)")
    files = sorted(glob.glob(os.path.join(cache_dir, "*.json"))) if cache_dir and os.path.isdir(cache_dir) else []
    n_div = 0
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        card = ((d.get("data") or {}).get("cards") or [{}])[0]
        sym, url, at = d["symbol"], card.get("url"), d["fetched_at_utc"]
        con.execute("INSERT INTO aiomax_cards VALUES (?,?,?,?,?,?,?)",
                    (sym, card.get("last_price"), card.get("yield"), card.get("dps_12m"),
                     thai_date(card.get("last_xd")), url, at))
        seen = set()
        for h in card.get("history") or []:
            key = (thai_date(h.get("xd")), h.get("amt"))
            if key in seen:  # aioMax บางงวดซ้ำ ต่างกันแค่ป้าย "ปันผล" / "เงินปันผล"
                continue
            seen.add(key)
            con.execute("INSERT INTO aiomax_dividends VALUES (?,?,?,?,?,?,?)",
                        (sym, key[0], thai_date(h.get("paid")), h.get("amt"), h.get("type"), url, at))
            n_div += 1
    print(f"  aiomax_cards: {len(files):,} · aiomax_dividends: {n_div:,}", flush=True)
    meta.append(("aiomax cache", "aiomax_dividends", n_div, cache_dir))


# ปันผลรวมทุกแหล่งตามลำดับ SET → Yahoo → aioMax
# SET factsheet มีเฉพาะตั้งแต่ 2021: ใช้ Yahoo เติมงวดก่อนหน้าที่ SET ไม่มี, aioMax ใช้เฉพาะหุ้นที่ไม่มีทั้ง 2 แหล่ง
# (Jitta ไม่มีปันผลราย XD จึงไม่อยู่ใน view นี้)
VIEWS = ["""
CREATE VIEW v_dividends AS
WITH s AS (SELECT ticker AS symbol, xd, payment_date, dividend AS dps, dividend_type AS type
           FROM set_dividends WHERE dividend IS NOT NULL),
     s_first AS (SELECT symbol, MIN(xd) AS first_xd FROM s GROUP BY symbol)
SELECT symbol, xd, substr(payment_date, 1, 10) AS paid, dps, type, 'SET' AS source FROM s
UNION ALL
SELECT y.symbol, y.xd, NULL, y.dps, NULL, 'Yahoo' FROM yf_dividends y
LEFT JOIN s_first f ON f.symbol = y.symbol
WHERE f.symbol IS NULL OR y.xd < f.first_xd
UNION ALL
SELECT a.symbol, a.xd, a.paid, a.dps, a.type, 'aioMax' FROM aiomax_dividends a
WHERE a.symbol NOT IN (SELECT symbol FROM s) AND a.symbol NOT IN (SELECT symbol FROM yf_dividends)
"""]


INDEXES = [
    "CREATE INDEX ix_fin_raw_key ON fin_raw (symbol, statement, basis, period_end)",
    "CREATE INDEX ix_fin_raw_item ON fin_raw (line_item)",
    "CREATE UNIQUE INDEX ux_fundamentals ON fundamentals (symbol, period)",
    "CREATE UNIQUE INDEX ux_companies ON companies (symbol)",
    "CREATE UNIQUE INDEX ux_dictionary ON dictionary (\"column\")",
    "CREATE UNIQUE INDEX ux_yf_info ON yf_info (symbol)",
    "CREATE INDEX ix_yf_dividends ON yf_dividends (symbol, xd)",
    "CREATE INDEX ix_yf_statements ON yf_statements (symbol, statement, line_item, period_end)",
    "CREATE INDEX ix_set_dividends ON set_dividends (ticker, xd)",
    "CREATE INDEX ix_jitta_metrics ON jitta_metrics (ticker, metric_name, period_type, period)",
    "CREATE INDEX ix_jitta_monthly ON jitta_monthly_prices (ticker, year, month)",
    "CREATE INDEX ix_aiomax_dividends ON aiomax_dividends (symbol, xd)",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--factsheet", default=DEFAULT_FACTSHEET)
    ap.add_argument("--aiomax-cache", help="โฟลเดอร์ cache ของ fetch_aiomax.py (ค่าเริ่มต้น: <db dir>/aiomax_cache)")
    args = ap.parse_args()

    db_dir = os.path.dirname(os.path.abspath(args.db))
    os.makedirs(db_dir, exist_ok=True)
    cache_dir = args.aiomax_cache or os.path.join(db_dir, "aiomax_cache")
    tmp = args.db + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)

    con = sqlite3.connect(f"file:{tmp}", uri=True)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    meta = []

    print("[1/5] CSV", flush=True)
    load_csv(con, os.path.join(args.sources, CSV_NAME), meta)
    print("[2/5] Excel", flush=True)
    load_xlsx(con, os.path.join(args.sources, XLSX_NAME), meta)
    print("[3/5] Yahoo zip", flush=True)
    load_zip(con, os.path.join(args.sources, ZIP_NAME), meta)
    print("[4/5] SET/Jitta factsheet", flush=True)
    load_factsheet(con, args.factsheet, meta)
    print("[5/5] aioMax cache", flush=True)
    load_aiomax(con, cache_dir, meta)

    print("indexes + views", flush=True)
    for sql in INDEXES + VIEWS:
        con.execute(sql)

    imported_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute("CREATE TABLE source_meta (source_file TEXT, table_name TEXT, rows INTEGER, "
                "file_size INTEGER, file_mtime_utc TEXT, imported_at_utc TEXT, note TEXT)")
    for src, table, n, note in meta:
        path = src if os.path.isabs(src) else os.path.join(args.sources, src)
        size, mtime = file_meta(path) if os.path.exists(path) else (None, None)
        con.execute("INSERT INTO source_meta VALUES (?,?,?,?,?,?,?)", (src, table, n, size, mtime, imported_at, note))
    con.commit()
    con.close()

    os.replace(tmp, args.db)
    print(f"done: {args.db}")


if __name__ == "__main__":
    main()
