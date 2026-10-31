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
