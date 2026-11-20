# ระบบข้อสอบและวัดผล v2 (BOI Enterprise Application)

อัปเกรดโครงสร้างการวัดผลเป็น **ทฤษฎีรวม 30 + Workshop ระหว่างเรียน 20 + สอบปฏิบัติ Final 50 = 100 คะแนน** เพื่อลดปัญหาคะแนนทฤษฎีเฟ้อ แยกคะแนนตามหัวข้อให้ละเอียดขึ้น และเก็บหลักฐานงาน Workshop พร้อมประวัติการขอความช่วยเหลือครบถ้วนสำหรับ HR และ Audit

## 1. ข้อสอบภาคทฤษฎีรวม (30 ข้อ · 30 คะแนน) & เครื่องมือซิงก์กลาง

| ไฟล์ | ใช้ทำอะไร |
| --- | --- |
| [combined_exam.json](combined_exam.json) | ฐานข้อมูลข้อสอบหลัก (Single Source of Truth): `preTest` 20 ข้อ + `theoryExam` 30 ข้อ (6 หัวข้อ × 5 ข้อ, แบ่ง 20 ข้อเป็น `isPostCore: true` สำหรับ HR) |
| [build_exam.py](build_exam.py) | สคริปต์ Build กลาง (`python build_exam.py`) ตรวจโครงสร้างและซิงก์ `combined_exam.json` เข้า `create_boi_forms.gs` และ HTML อัตโนมัติ (ตรวจความตรงกันด้วย `--check`) |
| [create_boi_forms.gs](create_boi_forms.gs) | Google Apps Script สร้าง Pre-Test + ทฤษฎีรวม 30 ข้อ และคำนวณ `Post-Test HR (20)` + `หัวข้อ 1..6 (ช่องละ 5 = 30)` เข้าชีต `สรุปคะแนน_Audit` (ยังอ่านชีตเก่า 26 ข้อของรุ่น 1–3 ได้) |
| [ข้อสอบรวม_PostTest_และ_Final_ออนไลน์.html](ข้อสอบรวม_PostTest_และ_Final_ออนไลน์.html) | เว็บสอบสำรอง 30 ข้อบนเบราว์เซอร์ ส่งคะแนนตรงเข้า `exam_server.py` (`/api/theory/submit`) หรือดาวน์โหลด JSON/CSV ได้ |
| [test_platform_v2.py](test_platform_v2.py) | ชุดทดสอบอัตโนมัติ (Build sync, GAS VM runtime, Grading Rules, Node Auto-Grader, Live Server API & Security, Audit Export) |

## 2. พอร์ทัลห้องเรียน, ระบบขอความช่วยเหลือ และ Auto-Grader (`practical/`)

| ไฟล์ | หน้าที่ |
| --- | --- |
| [practical/exam_server.py](practical/exam_server.py) | เซิร์ฟเวอร์กลาง: เสิร์ฟ Starter Workshop `W1–W4`, `/api/meter` (ตัด key `scenario` ออกแล้ว), `/api/notify`, ระบบ Help Queue, Auto-Grade, ส่งออก Audit `.xlsx`, ล็อกสิทธิ์ผู้สอนด้วย loopback + PIN |
| [practical/portal_ui.py](practical/portal_ui.py) | เทมเพลตหน้าจอผู้สอน, หน้าพอร์ทัลผู้เรียน (`/download`), หน้าล็อกอิน PIN สำหรับเครื่องผู้สอนบน Wi-Fi |
| [practical/grading_rules.py](practical/grading_rules.py) | สูตรคำนวณคะแนนกลางและเกณฑ์หัก Help แบบขั้นบันได + เพดานความปลอดภัย |
| [practical/auto_grader.py](practical/auto_grader.py) | ตัวตรวจโค้ดอัตโนมัติใน Node.js VM Sandbox (ตรวจ `W1–W4` + `TODO 1–5`, ค่าขอบ `240/20/1.5`, การส่งซ้ำ, และเช็กการประกาศฟังก์ชันซ้ำ) |
| [practical/audit_exporter.py](practical/audit_exporter.py) | สร้างไฟล์ Excel Audit v2 (`.xlsx` ฟอนต์ `Leelawadee UI` พร้อมชีตหลักฐาน Help) |
| [practical/exam_starter.html](practical/exam_starter.html) | ไฟล์ข้อสอบปฏิบัติ (`TODO 1–5`) มีระบบวินิจฉัย `file://` และปุ่มเรียกผู้สอน `requestExamHelp()` |

## 3. สูตรคะแนน & เกณฑ์หัก "ขอความช่วยเหลือ" (Help Deduction Formula)

1. **Workshop ระหว่างเรียน (`20 คะแนน`: `W1–W4` ชิ้นละ 5 คะแนน)**
   - ปัญหาเทคนิค/เครื่อง (`tech_issue`): **ไม่หัก (`0`)**
   - คำใบ้/ชี้แนะ (`hint`): **2 ครั้งแรกฟรี**, ครั้งที่ 3 เป็นต้นไป หักครั้งละ **`0.5`** คะแนน
   - ผู้สอนลงมือแก้โค้ดให้ (`code_fix`): หักครั้งละ **`1.5`** คะแนน
   - **เพดานหักสูงสุด (Max Cap):** ไม่เกิน **`8.0` คะแนน** และไม่เกิน **50% ของคะแนน Workshop ที่ทำได้**
2. **สอบปฏิบัติ Final (`50 คะแนน`: `TODO 1–5` ข้อละ 10 คะแนน)**
   - ความสะอาดโค้ด/ไลฟ์สด: พบฟังก์ชันซ้ำ `-1`, ส่งพลาดตอนปกติ (`false_alarm`) `-0.5`/ครั้ง (สูงสุด `-2.5`)
   - ปัญหาเทคนิค/เครื่อง (`tech_issue`): **ไม่หัก (`0`)**
   - คำใบ้/ชี้แนะ (`hint`): หักแบบลดแรงกระแทก **`1, 2, 3, 1, 1, ...`** คะแนนตามลำดับครั้ง
   - ผู้สอนแก้โค้ดให้ (`code_fix`): หักครั้งละ **`3.0`** คะแนน
   - **เพดานหักสูงสุด (Max Cap):** ไม่เกิน **`15.0` คะแนน** และไม่มีทางหักเกิน **50% ของคะแนนโค้ดที่ทำได้จริง** (รับประกันว่าจะไม่ถูกหักจนเหลือ `0`)
3. **ผลรวม (`100 คะแนน`):** `ทฤษฎีรวม (30) + Workshop (20) + สอบปฏิบัติ (50)` · ตัดเกรด `A>=80, B>=70, C>=60, D>=50` · เกณฑ์ผ่าน `>= 70`
