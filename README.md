# สื่อการเรียนการสอนโครงการอบรม BOI (99 Industrial Solutions & SNC)

พื้นที่รวมสื่อการสอน ใบงาน Workshop ข้อสอบ ระบบประเมินผล และไฟล์สรุปคะแนน Audit สำหรับวิชา **Enterprise Application Design, Development & Integration (`App`)** พร้อมไฟล์ต้นฉบับอ้างอิงและแม่แบบของโครงการ

## โครงสร้างโฟลเดอร์

```text
BOI_Training_Materials/
├── README.md                                          # คู่มือภาพรวมและดัชนีไฟล์ทั้งหมด
├── User Training-BOI.txt                              # บัญชีเข้าใช้โน้ตบุ๊กสำหรับผู้เรียนในห้องอบรม
│
├── 00_BOI_Template_และตารางฝึกอบรม/
│   ├── BOITemplate.pptx                               # แม่แบบสไลด์มาตรฐาน BOI
│   ├── ตารางฝึกอบรม_7วิชา_19คอร์ส_2026-10-21.xlsx      # ตารางอบรมรวม 7 วิชา (วิชาละ 19 คอร์ส)
│   └── QR_Codes/                                      # รูป QR Code สำหรับเปิดหน้าห้องเรียน / ลงทะเบียน / แบบทดสอบ
│
├── 01_Enterprise_Application/                         # วิชาหลักที่สอน (App: 24 ชม. / 4 วัน, CLO01–CLO08)
│   ├── 01_Slides_สไลด์ประกอบการสอน/                  # สไลด์ (.pptx, .pdf) และเอกสารโครงสร้างหลักสูตร (.pdf)
│   ├── 02_Code_Examples_โค้ดตัวอย่าง/                 # Visual Labs (HTML/CSS, DOM/JS) และโค้ดตัวอย่าง 01–16 + สไลด์ 39–57
│   ├── 03_Workshops_ใบงานและเฉลย/                    # โจทย์, starter/solution Workshop 1–4, Mock API และแบบฟอร์ม UAT/Test Report
│   ├── 04_Exam_ข้อสอบและเกณฑ์วัดผล/                   # ข้อสอบทฤษฎี (PDF / HTML / Google Form), ข้อสอบปฏิบัติ + exam_server.py และ Rubric
│   └── 05_Teaching_Kit_และระบบประเมินผล/              # Teaching Kit (Speaker Notes + Quiz) และระบบประเมิน Google Apps Script
│
├── 02_PLC_Practical_Training/                         # ไฟล์ต้นฉบับอ้างอิงวิชา PLC (เก็บไว้อ้างอิง ไม่ได้สอนเอง)
│   ├── PLC Practical Training_BOI.pptx
│   └── PLC Practical Training_BOI.pdf
│
└── 03_Audit_สรุปคะแนนการสอบ/                         # ศูนย์รวมไฟล์สรุปคะแนนสำหรับ Audit (แยกไฟล์รายรุ่น + แบบฟอร์มเปล่า)
    ├── README.md                                      # คู่มือการใช้งานไฟล์ Audit และโครงสร้างคะแนน
    ├── 00_แบบฟอร์มเปล่า_สรุปคะแนน_วิชา_APP_สำหรับ_Audit.xlsx
    ├── 01_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_01_สำหรับ_Audit.xlsx
    ├── 02_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_02_สำหรับ_Audit.xlsx
    ├── 02_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_02_สำหรับ_Audit.pdf
    ├── 03_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_03_สำหรับ_Audit.xlsx
    ├── 03_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_03.pdf
    ├── 04..08_สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_04..08_สำหรับ_Audit.xlsx
    └── สรุปคะแนนการสอบ_วิชา_APP_รุ่นที่_1-8_พร้อมพิมพ์_PDF.html
```

## คู่มือใช้งานด่วน (วิชา Enterprise Application)

| งานที่ต้องใช้ | ไฟล์ / คำสั่ง |
| --- | --- |
| **ศูนย์รวมลิงก์ & QR เปิดสอน (เริ่มรุ่นใหม่เปิดไฟล์นี้ก่อน)** | `01_Enterprise_Application/00_ศูนย์รวมลิงก์และQR_เปิดสอน.html` |
| เปิด Visual Lab สอนสด | `01_Enterprise_Application/02_Code_Examples_โค้ดตัวอย่าง/00-html-css-visual-lab.html` และ `00-dom-js-visual-lab.html` |
| รัน Mock API (Workshop 3–4) | `python "01_Enterprise_Application/03_Workshops_ใบงานและเฉลย/mock-api/mock_api.py"` |
| เปิดข้อสอบรวม Post-Test + Final (26 ข้อ) | `01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/ข้อสอบรวม_PostTest_และ_Final_ออนไลน์.html` |
| รันเซิร์ฟเวอร์สอบปฏิบัติ + ตารางผู้ผ่านแต่ละเคส | `python "01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/practical/exam_server.py"` |
| แสดงโจทย์สอบปฏิบัติขึ้นจอ | `01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/practical/โจทย์สอบปฏิบัติ_แสดงบนจอ.html` |
| กรอกคะแนนและออกไฟล์ Audit รายรุ่น | โฟลเดอร์ `03_Audit_สรุปคะแนนการสอบ/` (ดูรายละเอียดใน `03_Audit_สรุปคะแนนการสอบ/README.md`) |

## คู่มือรับช่วงต่อสำหรับผู้สอนรุ่นที่ 4 เป็นต้นไป

1. **เปิดลิงก์ข้อสอบ Pre-Test / Post-Test:** เปิด [01_Enterprise_Application/00_ศูนย์รวมลิงก์และQR_เปิดสอน.html](01_Enterprise_Application/00_ศูนย์รวมลิงก์และQR_เปิดสอน.html) ได้ลิงก์และ QR Code สำหรับผู้เรียนทันที (ใน Google Form มีช่องให้เลือก `รุ่นที่เข้าอบรม`) ส่วนสคริปต์จัดการฟอร์ม/ซ่อมชีตคำตอบอยู่ที่ [create_boi_forms.gs](01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/create_boi_forms.gs)
2. **วันสอน Workshop 3–4:** รัน `python "01_Enterprise_Application/03_Workshops_ใบงานและเฉลย/mock-api/mock_api.py"` (หรือ `python "01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/practical/exam_server.py"` แล้วเปิด `http://localhost:8000/notifications` เพื่อแสดงหน้าจอแจ้งเตือน Lockscreen)
3. **วันสอบปฏิบัติ (วันที่ 4):**
   - รัน `python "01_Enterprise_Application/04_Exam_ข้อสอบและเกณฑ์วัดผล/practical/exam_server.py"` บนเครื่องผู้สอน
   - เปิด `http://localhost:8000/` (หน้าคุมเคส + ดูโค้ด), กด **`🗑️ ล้างผลบันทึก`** 1 ครั้งก่อนเริ่มรุ่นใหม่เพื่อล้างตารางของรุ่นที่ 3 (ไม่ลบไฟล์ที่เก็บไว้ใน `practical/submissions/`)
   - หน้าจอเสริมสำหรับผู้สอน: `http://localhost:8000/notifications` (จอแจ้งเตือน), `http://localhost:8000/prompt` (โจทย์ขึ้นจอ), `http://localhost:8000/solution/` (เฉลยโชว์การทำงาน)
   - ให้ผู้เรียนเข้า **`http://<IP_เครื่องผู้สอน>:8000/download`** เพื่อดาวน์โหลดไฟล์ `exam_starter.html`, คัดลอก `API_URL`/`WEBHOOK_URL`, และส่งไฟล์งานกลับเมื่อทำเสร็จ
4. **สรุปคะแนน Audit:** ใช้ไฟล์รุ่นที่ `04..08` หรือคัดลอก [00_แบบฟอร์มเปล่า_สรุปคะแนน_วิชา_APP_สำหรับ_Audit.xlsx](03_Audit_สรุปคะแนนการสอบ/00_แบบฟอร์มเปล่า_สรุปคะแนน_วิชา_APP_สำหรับ_Audit.xlsx) — แนะนำตั้งฟอนต์เป็น `Leelawadee UI` ตามรุ่นที่ 3 ก่อน Export PDF เพื่อป้องกันสระ/วรรณยุกต์เป็นสี่เหลี่ยม (`□`) บน Windows
