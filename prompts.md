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

---

## รอบ 3 · 2026-11-02 (commit 2026-11-04)

- **ทำอะไร:** Phase 2 ตกลงเกณฑ์ Dividend Scan แล้วเขียนเป็นโค้ด เปลี่ยน `spec.md` จาก Stock Radar เป็น Dividend Scan เพิ่ม `tools/dividend_scan.py` (อ่าน `stocks.db` คัดหุ้น ให้คะแนน แล้วส่งออก) และ `tools/dividend_scan_template.html` ได้ผลเป็น `output/dividend_scan.csv` และ `output/dividend_scan.html`
- **เครื่องมือ / model:** Claude Desktop (แท็บ Code) · Claude Opus 5.5 · รันสคริปต์ด้วย python3 ใน WSL · ตรวจหน้า HTML ในบราวเซอร์ของแอป
- **Prompt ที่ใช้:**

```text
เริ่ม Phase 2: คุยเรื่องเกณฑ์และกลยุทธ์ Dividend Scan อ่าน prompts.md รอบ 2 และ PROJECT_MEMORY.md ก่อน ฐานข้อมูลอยู่ที่ /mnt/c/AI-investor-alpha/db/stocks.db
```

```text
A/B/C is good, I have add as following,
(ตามด้วยกลยุทธ์ value S1–S5 ที่ผู้เรียนร่าง: cash fortress, Cash Cycle, PE compression, Triple Crown, Quality growth 2017–2025)
```

```text
ต้องมีปันผลเกิน 3% และมีแน้วโน้วที่ปันผลเพิ่ม มี Payout ratio 30%-80% มี RIOC ประกอบ เพื่อดูแน้วโน้วผมตอบแทน
```

- **ผลที่ได้:**
  - ผลคัดกรอง: หุ้นทั้งหมด 943 ตัว → yield > 3% เหลือ 488 → payout 30–80% เหลือ 223 → DPS มีแนวโน้มเพิ่ม เหลือ 59 → shortlist 15 ตัว ได้แก่ SECURE, TFG, AMARC, PCC, SFLEX, KTB, UVAN, BKD, SISB, AKR, PRM, NSL, LEE, BH, KBANK
  - ป้าย S1 มีแค่ LEE ตัวเดียว ป้าย S3 มี 28 ตัว และ 9 จาก 59 ตัวเป็นกลุ่มการเงิน
  - ใน CSV และ HTML ทุกตัวเลขมีคอลัมน์บอกแหล่งและวันที่ และมีเฉพาะ ratio กับตัวเลขต่อหุ้น ไม่มีงบดิบ SETSMART
  - ตรวจในบราวเซอร์แล้ว: ตาราง ปุ่มกรอง และหน้าต่างรายหุ้นแสดงผลถูก (เช่น CPALL DPS 0.6 → 1.65) ป้าย S3 ของ CPALL ตรงกับรายงานตัวอย่างของผู้เรียน (รายได้ +19.9%, กำไร +112.5%)
  - ยังขาด: ยังไม่ได้สุ่ม 3 ตัวเทียบกับ set.or.th ด้วยมือตาม success criteria ข้อมูลยังเป็นของวันที่ 2026-10-12 ถึง 2026-10-29 และ DPS ปี 2024 ของ SECURE ไม่ตรงกันระหว่างสองแหล่ง (Jitta 0.90, SET รวม XD ปี 2025 ได้ 0.70) ต้องตรวจกับประกาศจริงก่อนเลือกทำ Deepdive
- **ตัดสินใจอะไร และเพราะอะไร:**
  - ใช้ปันผลเป็นด่านแรก แล้วให้กลยุทธ์ value เป็นป้ายเสริม (ผู้เรียนเลือกจากตัวเลือกที่ AI เสนอ)
  - เกณฑ์ด่าน yield > 3%, DPS มีแนวโน้มเพิ่ม, payout 30–80% และใช้ ROIC ประกอบเพื่อดูแนวโน้มผลตอบแทน ผู้เรียนเป็นคนกำหนด
  - นิยาม "DPS มีแนวโน้มเพิ่ม" = ปี 2025 สูงกว่าปี 2021 และลดได้ไม่เกิน 1 ครั้ง AI เสนอ ผู้เรียนอนุมัติในแผน เพราะต้องแปลงคำว่าแนวโน้มเป็นเงื่อนไขที่โค้ดตรวจได้
  - รอบนี้ทำแค่ป้าย S1 กับ S3 ส่วน S2, S4, S5 ไว้รอบถัดไป ใช้ ROE แทน ROIC ในกลุ่มการเงินและ REIT เพราะเงินทุนของธนาคารคือเงินฝากและสินเชื่อ และใช้ Jitta ดูแนวโน้ม DPS โดยแสดงตัวเลขตามประกาศของ SET คู่กัน เรื่องเหล่านี้ผู้เรียนไม่ได้ตอบตอนถาม AI จึงใส่เป็นค่าตั้งต้นในแผน และผู้เรียนอนุมัติแผน
  - เปลี่ยนจากแผน (AI ตัดสินระหว่างทำ ผู้เรียนรับทราบตอนสรุปผล): คำนวณ ROIC, ROE และรายได้/กำไรของ S3 จาก SETSMART แทน Jitta และใช้ yield กับ payout จาก SET อย่างเดียว เพราะตัวชี้วัดรายปีของ Jitta ปนหน่วยกันจนทำให้ ROE ดูพุ่งขึ้นทั้งที่ไม่ได้ขึ้น ผลคือหุ้นที่ไม่มีข้อมูล SET ไม่ผ่านด่าน yield (488 แทน 495)
  - ใช้หน้าตา dashboard ตามตัวอย่าง `stock_valuation_derating_report.html` ที่ผู้เรียนส่งมา
- **ขั้นต่อไป:** สุ่ม 3 ตัวเทียบกับ set.or.th ทบทวนเกณฑ์ที่อาจต้องปรับ (เช่น S1 ที่เหลือตัวเดียว) แล้วเลือกหุ้นทำ Deepdive

---

## รอบ 4 · 2026-11-04

- **ทำอะไร:** เทียบผล Dividend Scan กับหน้า factsheet ของ set.or.th 3 ตัว (SECURE, KTB, CPALL ข้อมูล ณ 3 พ.ย. 2569) แล้วเทียบ DPS ของ Jitta กับ `set_dividends` ที่รวมตามงวดผลประกอบการ ครบทั้ง 59 หุ้นที่ผ่านด่าน รอบนี้ไม่ได้แก้สคริปต์
- **เครื่องมือ / model:** Claude Desktop (แท็บ Code) · Claude Opus 5.5 · บราวเซอร์ของแอป · python3 ใน WSL (อ่านฐานข้อมูลอย่างเดียว)
- **Prompt ที่ใช้:**

```text
proceed
```

```text
note and proceed
```

```text
will do it later in seperate session , please save and commit
```

- **ผลที่ได้:**
  - แหล่งที่เทียบ: `https://www.set.or.th/th/market/product/stock/quote/<TICKER>/factsheet` ดึงเมื่อ 2026-11-04 หุ้น 3 ตัวนี้ AI เลือกเอง ไม่ได้สุ่มจริง: SECURE เพราะมีข้อสงสัยเรื่อง DPS, KTB เพราะเป็นกลุ่มการเงิน และ CPALL เพราะเทียบกับรายงานตัวอย่างของผู้เรียนได้
  - Payout ปี 2025 และ DPS ปี 2021–2024 ตรงทั้ง 3 ตัว Yield และ P/E ตรงเมื่อคำนวณใหม่ด้วยราคาวันที่ของข้อมูลใน scan (9–12 ต.ค. 2569) DPS ปี 2025 ตรงกับ SECURE และ CPALL แต่ KTB ไม่ตรง (Jitta 2.07, SET 0.43 + 2.24 = 2.67) success criteria ข้อนี้จึงยังไม่ผ่าน
  - **แก้ข้อความในรอบ 3:** ที่เขียนว่า DPS ปี 2024 ของ SECURE ไม่ตรงกันนั้นผิด ปันผลงวดนั้นคือ 0.20 + 0.70 = 0.90 บาท ตรงกับ Jitta แต่ 0.20 มีวัน XD ในปี 2024 จึงไม่อยู่ในยอด XD ปี 2025
  - เทียบ DPS ทั้ง 59 ตัวได้ 229 จุด ไม่ตรง 14 จุดใน 8 หุ้น (เกณฑ์: ต่างเกิน 0.02 บาทและเกิน 3%) อีก 66 จุดเทียบไม่ได้เพราะไม่มีข้อมูลงวด ใน shortlist มี KTB ปี 2025 และ BH ปี 2025 (Jitta 5.00, SET 11.00) นอก shortlist มี HUMAN, AMATA, DITTO, SO, BIZ, MTI และ AEONTS
  - ยังไม่รู้สาเหตุของจุดที่ไม่ตรง มีแค่ MTI ที่ต่างกันพอดี 10 เท่าจึงน่าจะมาจากการแตกพาร์ และยังไม่ได้ตรวจหุ้นที่ตกด่าน DPS ไปแล้ว
  - payout แบบ YTD บนเว็บของ SECURE คือ 0.95 และ KTB คือ 0.88 เกินเพดาน 80% แต่ผ่านด่านเพราะเกณฑ์ใช้ปี 2025 กำไรครึ่งแรกปี 2569 ของ SECURE ลดลง 21.82%
- **ตัดสินใจอะไร และเพราะอะไร:**
  - ยังไม่เพิ่มการตรวจ DPS เทียบ SET ลงในสคริปต์ ผู้เรียนสั่ง "ยังไม่ต้อง" โดยยังไม่ได้บอกเหตุผล
  - เก็บข้อความเดิมในรอบ 3 ไว้ แล้วแก้ไว้ในรอบนี้ เพราะกติกาของไฟล์นี้ห้ามลบของเก่า
  - ยังไม่เริ่ม Deepdive ผู้เรียนจะทำใน session แยกภายหลัง AI เสนอ BH เป็นตัวแรก แต่ผู้เรียนยังไม่ได้ยืนยัน
- **ขั้นต่อไป:** เริ่ม Deepdive ใน session ใหม่ โดยเลือกหุ้นตัวแรกก่อน ที่ค้างอยู่คือ DPS ที่ไม่ตรงกับ SET และการตัดสินใจว่าจะดู payout แบบ YTD ด้วยหรือไม่
