# บันทึกขั้นตอน (process log)

> เพิ่ม 1 entry ทุกครั้งก่อน commit ต่อท้ายไฟล์ ห้ามลบของเก่า
> ผู้สอนอ่านไฟล์นี้เพื่อดูวิธีคิดของคุณ ไม่ใช่แค่ผลงานสุดท้าย
> ถ้าใช้ AI ช่วยทำงาน AI จะเขียน entry ให้ตาม AGENTS.md ถ้า commit เอง ให้เขียนเองตามแบบด้านล่าง

---

## รอบ 1 · 2026-10-31

- **ทำอะไร:** clone repo การบ้านลงเครื่อง แล้วร่าง `spec.md` ครั้งแรกจากไอเดีย 3 ข้อ โดยรวมเป็นงานเดียวที่ต่อกันเป็นทอด ๆ: ดึงข้อมูลอัตโนมัติ → Radar คัดหุ้น → Deepdive ยืนยันทีละตัว
- **เครื่องมือ / model:** Claude Desktop (แท็บ Code) · Claude Opus 5.5
- **Prompt ที่ใช้:**

```text
1#Automating the collection of Thai stock market data involves several approaches ranging from direct web scraping libraries in Python to official APIs and low-code tools
2# Deepdive skill for health sector and apply the core skill to other sector
3# Stock radar for price collaps market cap or derate PE but healthly finance performance
```

- **ผลที่ได้:** spec ครบ 5 หัวข้อ: Goal, material questions 5 ข้อ, trust sources (set.or.th, SEC iDisc, IR บริษัท, aioMax), output (สคริปต์ดึงข้อมูล, radar.html + csv, deepdive 2 ตัว) และ success criteria 5 ข้อ ยังไม่ได้ใส่ชื่อเล่นและเลขกลุ่มใน README / owner
- **ตัดสินใจอะไร และเพราะอะไร:**
  - รวม 3 ไอเดียเป็นสายพานเดียว แทนการเลือกทำข้อเดียว เพราะ spec ต้องมี Goal เดียว และทั้ง 3 ข้อส่งต่อกันได้: ข้อ 1 คือที่มาของข้อมูล ข้อ 3 คือการตัดสินใจหลัก ข้อ 2 คือการยืนยันผลที่ Radar คัดได้ (AI เสนอ ผู้เรียนเห็นด้วย)
  - ยืนยันเกณฑ์ Radar ตามที่ AI ร่าง: ราคาต่ำกว่าจุดสูงสุด 52 สัปดาห์ ≥ 30% หรือ PE ต่ำกว่าค่าเฉลี่ย 5 ปี ≥ 30% และแข็งแรงคือ core profit ไม่ลด, ROE ≥ 10%, D/E ≤ 1.5, เงินสดจากการดำเนินงานเป็นบวก ปรับได้หลังเห็นผลรอบแรก
  - ไม่ใช้บทวิเคราะห์โบรก และไม่ commit ข้อมูล SETSMART ดิบ เพราะ repo เป็น Public
  - วาง repo ไว้ที่ `C:\aia-hw-jatturong` ไม่ได้วางใน `homework/` ของ workspace ตามที่ README แนะนำ (ผู้เรียนเลือกเก็บไว้ที่นี่)
- **ขั้นต่อไป:** ใส่ชื่อเล่นและเลขกลุ่มใน README แล้วเริ่มสคริปต์ดึงข้อมูล (ไอเดีย 1)

---

## รอบ 2 · 2026-11-02

- **ทำอะไร:** Phase 1 ของ Dividend Scan คือสร้างฐานข้อมูล SQLite `stocks.db` รวมข้อมูลทุกแหล่งที่มีในเครื่อง เขียนสคริปต์ 3 ตัวใน `tools/`: `build_db.py` (สร้างฐานใหม่ทั้งหมดด้วยคำสั่งเดียว), `fetch_aiomax.py` (เติมปันผลจาก aioMax เฉพาะหุ้นที่แหล่งอื่นไม่มี), `check_db.py` (ตรวจจำนวนแถว เทียบตัวเลขข้ามแหล่ง และสรุปว่าแต่ละแหล่งครอบคลุมกี่หุ้น) เพิ่มลำดับความน่าเชื่อถือของแหล่งข้อมูลใน `spec.md` และเพิ่ม `*.db` ใน `.gitignore`
- **เครื่องมือ / model:** Claude Desktop (แท็บ Code) · Claude Opus 5.5 · รันสคริปต์ด้วย python3 ใน WSL
- **Prompt ที่ใช้:**

```text
Let discuss with my objective to setup the Divident Scan stock from financial.
There are 3 Phase that I would like to discuss before execute project.
Phase 1# I would need to setup the source data for you first. ...
would you be able to create new database and import all those data into database.
```

```text
Hold Phase 2# let fix phase 1# first.
regarding to missing data , I have 2 solution.
1# I have existing data base that I have fetch data from public. ... factsheets_backup.db
2# you can try this ... python aiomax_client.py call get_dividend '{"symbol": "PTT"}'
```

```text
here is priority of trust source SET,Jitta and yahoo.
And if it missing then call aioMax but it will need my login from browser one time.
If you think we don't need jitta then excludng.
```

- **ผลที่ได้:**
  - `stocks.db` (~1 GB) อยู่ที่ `C:\AI-investor-alpha\db\` นอก repo มี SETSMART (งบ 4.16 ล้านแถว, fundamentals 18,558 แถว, 911 หุ้น), Yahoo (ราคารายวัน, ปันผล 852 หุ้น), SET factsheet (ปันผล 817 หุ้น, สถิติซื้อขาย, งบย่อ), Jitta (ตัวชี้วัดรายปี 2016–2026, ราคารายเดือน) และ aioMax (40 หุ้น) ทุกตารางบันทึกที่มาและวันที่ใน `source_meta`
  - view `v_dividends` รวมปันผลตามลำดับ SET → Yahoo → aioMax ครอบคลุม 899 จาก 911 หุ้น เหลือ 12 หุ้นที่ไม่มีปันผลจากแหล่งใดเลย (ส่วนใหญ่น่าจะไม่จ่ายหรือถูกพักการซื้อขาย)
  - `check_db.py` ผ่านทุกข้อ: จำนวนแถวตรงกับต้นทาง และกำไร 2S 2021Q1 ตรงกันระหว่าง fundamentals กับงบดิบ
  - ยังขาด: ข้อมูล factsheet เป็นของวันที่ 2026-10-14 และ Yahoo จบที่ 2026-10-29 ยังไม่ได้อัปเดตให้เป็นปัจจุบัน
- **ตัดสินใจอะไร และเพราะอะไร:**
  - เก็บฐานข้อมูลนอก repo (`C:\AI-investor-alpha\db\`) เพราะมีข้อมูล SETSMART ที่ซื้อมา และ repo นี้เป็น Public (ผู้เรียนเลือก)
  - นำข้อมูล Yahoo จาก `data_backup.zip` เข้าด้วย เพราะ SETSMART ไม่มีราคาและ DPS ต่อหุ้น ซึ่งต้องใช้คิด dividend yield (ผู้เรียนเลือก)
  - รันใน WSL เพราะใน WSL มี pandas และ openpyxl อยู่แล้ว และผู้เรียนใช้ SQLite ใน WSL อยู่ (ผู้เรียนเลือก)
  - Yahoo ขาดไป 59 หุ้น รวมตัวใหญ่อย่าง AOT, BANPU, BTS ผู้เรียนจึงเสนอให้ใช้ factsheet DB ที่ตัวเองดึงไว้ และใช้ aioMax เติม
  - ลำดับความน่าเชื่อถือ SET → Jitta → Yahoo → aioMax ผู้เรียนเป็นคนกำหนด และใช้ aioMax เฉพาะหุ้นที่แหล่งอื่นไม่มี
  - นำ Jitta เข้าด้วย (ผู้เรียนให้ AI ตัดสิน) เพราะ Jitta มี DPS, payout ratio และ yield รายปีย้อนไปถึง 2016 ส่วน SET factsheet มีปันผลแค่ตั้งแต่ 2021 ถ้าจะดูว่าบริษัทจ่ายปันผลสม่ำเสมอไหม ต้องใช้ข้อมูลย้อนหลังยาว
  - ไม่นำเข้า raw JSON snapshot และ change_log จาก factsheet DB เพราะไม่ได้ใช้คำนวณ และทำให้ฐานใหญ่ขึ้นโดยไม่จำเป็น
- **ขั้นต่อไป:** Phase 2 คุยเรื่องเกณฑ์และกลยุทธ์ Dividend Scan รวมถึงแก้ `spec.md` จากโจทย์ Stock Radar ให้เป็น Dividend Scan และตัดสินใจว่าจะยึด DPS ฐานไหน (ตัวเลขตามประกาศจริงแบบ SET หรือแบบที่ปรับตามการแตกพาร์แบบ Yahoo)
