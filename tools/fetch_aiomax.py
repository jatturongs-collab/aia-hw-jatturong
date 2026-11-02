"""ดึงปันผลจาก aioMax เฉพาะหุ้นที่ SET และ Yahoo ไม่มีข้อมูลปันผล แล้วเก็บเป็น cache + อัปเดต stocks.db

aioMax อยู่ลำดับสุดท้ายของ trust sources (SET → Jitta → Yahoo → aioMax) จึงใช้เติมช่องว่างเท่านั้น
ใช้ client ของผู้เรียนที่ /mnt/c/ai/script/aiomax (ครั้งแรกต้อง login ผ่าน browser, token เก็บไว้ข้าง client ไม่อยู่ใน repo)
cache เก็บที่ <db dir>/aiomax_cache/<SYMBOL>.json เพื่อให้ build_db.py สร้างฐานใหม่ได้โดยไม่ต้องเรียกซ้ำ

รัน (WSL):
    source ~/portfolio-venv/bin/activate
    python tools/fetch_aiomax.py --db /mnt/c/AI-investor-alpha/db/stocks.db [--symbols COLOR,KKC] [--force]
"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_db import load_aiomax  # noqa: E402

CLIENT_DIR = "/mnt/c/ai/script/aiomax"

MISSING_SQL = """
SELECT symbol FROM companies
WHERE symbol NOT IN (SELECT ticker FROM set_dividends)
  AND symbol NOT IN (SELECT symbol FROM yf_dividends)
ORDER BY symbol
"""


async def fetch(symbols, cache_dir, force):
    sys.path.insert(0, CLIENT_DIR)
    from aiomax_client import AioMax

    async with AioMax() as ax:
        for sym in symbols:
            path = os.path.join(cache_dir, f"{sym}.json")
            if os.path.exists(path) and not force:
                print(f"  {sym}: มี cache แล้ว ข้าม")
                continue
            for attempt in range(3):
                try:
                    _, data = await ax.call("get_dividend", symbol=sym)
                    break
                except RuntimeError as e:  # aioMax จำกัด 30 ครั้ง/นาที
                    if "rate limit" not in str(e) or attempt == 2:
                        raise
                    print("  ติด rate limit รอ 65 วินาที", flush=True)
                    await asyncio.sleep(65)
            await asyncio.sleep(2.1)
            out = {"symbol": sym, "tool": "get_dividend",
                   "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "data": data}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
            n = len(((data or {}).get("cards") or [{}])[0].get("history") or [])
            print(f"  {sym}: {n} งวด")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--symbols", help="คั่นด้วยจุลภาค ถ้าไม่ใส่ จะใช้หุ้นที่ SET และ Yahoo ไม่มีปันผล")
    ap.add_argument("--force", action="store_true", help="ดึงใหม่แม้มี cache แล้ว")
    args = ap.parse_args()

    cache_dir = os.path.join(os.path.dirname(os.path.abspath(args.db)), "aiomax_cache")
    os.makedirs(cache_dir, exist_ok=True)
    con = sqlite3.connect(args.db)
    symbols = args.symbols.split(",") if args.symbols else [s for (s,) in con.execute(MISSING_SQL)]
    print(f"เรียก aioMax {len(symbols)} หุ้น: {', '.join(symbols)}")
    asyncio.run(fetch(symbols, cache_dir, args.force))

    meta = []
    load_aiomax(con, cache_dir, meta)
    con.execute("CREATE INDEX IF NOT EXISTS ix_aiomax_dividends ON aiomax_dividends (symbol, xd)")
    con.execute("DELETE FROM source_meta WHERE source_file = 'aiomax cache'")
    con.execute("INSERT INTO source_meta VALUES (?,?,?,?,?,?,?)",
                ("aiomax cache", "aiomax_dividends", meta[0][2], None, None,
                 datetime.now(timezone.utc).isoformat(timespec="seconds"), cache_dir))
    con.commit()
    print("อัปเดต stocks.db แล้ว")


if __name__ == "__main__":
    main()
