# Workshop 1–4

Workshop ทั้ง 4 ข้อต่อยอดเป็นงานชิ้นเดียว คือหน้า Electrical Meter ทุกข้อมีโฟลเดอร์ `starter` ให้ผู้เรียนเริ่ม และ `solution` เป็นเฉลยสำหรับผู้สอน starter ของข้อถัดไปคือเฉลยของข้อก่อนหน้า บวกส่วนที่ต้องใช้ในข้อใหม่ ผู้เรียนที่ทำข้อก่อนหน้าไม่ทันจึงเริ่มต่อได้ทันที

| Workshop | หัวข้อ | เวลา | ผู้เรียนแก้ไฟล์ |
| --- | --- | --- | --- |
| `w1` | Electrical Meter (HTML + CSS, Flexbox) | วันที่ 1 · 14:00–15:45 | `index.html`, `style.css` |
| `w2` | Start / Stop และ Simple Meter (DOM, Event) | วันที่ 2 · 14:30–16:00 | `script.js` |
| `w3` | ดึงค่าน้ำ-ไฟจาก API (fetch, setInterval) | วันที่ 3 · 11:00–12:00, 13:00–13:45 | `script.js` |
| `w4` | แจ้งเตือนผ่าน Webhook เมื่อกด Start (POST) | วันที่ 3 · 14:15–15:00 | `script.js` |

- `โจทย์ Workshop.pdf`: เอกสารแจกผู้เรียน 1 หน้าต่อ Workshop มีขั้นตอน เช็กลิสต์ "ทำเสร็จเมื่อ" งานเสริมสำหรับคนที่เสร็จก่อน และปัญหาที่เจอบ่อย
- `mock-api/mock_api.py`: API สำรองสำหรับ Workshop 3–4
- ใช้เช็กลิสต์ "ทำเสร็จเมื่อ" ในเอกสารตรวจงานของผู้เรียนได้เลย Workshop ไม่มีคะแนน

## แบบฟอร์มทดสอบ (`templates/`)

ดัดแปลงจากเทมเพลตใน repo ทีม (`snc-boi-stemplus/enterprise-app-workshop`) ให้เป็นภาษาไทยและตรงกับ Electrical Meter Dashboard

- `แบบฟอร์ม Test Report และ UAT.pdf`: พิมพ์แจกผู้เรียน Test Report ใช้ท้ายวันที่ 3 แบบตรวจรับ UAT ใช้ตอน UAT Showcase บ่ายวันที่ 4
- `test-report.md`, `uat-checklist.md`: ฉบับ Markdown สำหรับกรอกในคอมพิวเตอร์
- `system-test-example.js`: ตัวอย่าง System Test อัตโนมัติที่ตรวจ API สำรอง รันด้วย `node templates/system-test-example.js http://<IP ผู้สอน>:8000`

แก้เนื้อหาแบบฟอร์มได้ที่สคริปต์ build ภายนอก (`tools/build_testing_forms.py` ไม่ได้รวมอยู่ในชุดสื่อนี้):

```bash
python tools/build_testing_forms.py "01_Enterprise_Application/03_Workshops_ใบงานและเฉลย/templates"
```

## ก่อนเริ่มรุ่น

1. คัดลอกโฟลเดอร์ `w1/starter` ถึง `w4/starter` ลงทุกเครื่อง ห้ามคัดลอกโฟลเดอร์ `solution`
2. ติดตั้ง VS Code และส่วนขยาย Live Server ทุกเครื่อง ตั้งแต่ Workshop 3 ต้องเปิดผ่าน Live Server เพราะ fetch ใช้กับ `file://` ไม่ได้
3. พิมพ์ `โจทย์ Workshop.pdf` หรือส่งไฟล์ให้ผู้เรียน

## API สำรอง (Workshop 3–4)

ใช้เมื่อ API ค่าน้ำ-ไฟของบริษัทหรือช่องแจ้งเตือนใช้ไม่ได้ หรือใช้แทนตั้งแต่แรกก็ได้ เพราะค่าเปลี่ยนเองและไม่กระทบระบบจริง เปิดบนเครื่องผู้สอนที่ต่อ Wi-Fi วงเดียวกับผู้เรียน:

```bash
python "01_Enterprise_Application/03_Workshops_ใบงานและเฉลย/mock-api/mock_api.py"
```

โปรแกรมจะพิมพ์ URL ให้เขียนบนกระดาน:

- Workshop 3: `API_URL = 'http://<IP ผู้สอน>:8000/api/meter'` ค่าเปลี่ยนทุกครั้งที่เรียก และในวินาทีที่ 0–9 ของทุกนาทีแรงดันจะเกิน 240 V เพื่อให้เห็นคำเตือน
- Workshop 4: `WEBHOOK_URL = 'http://<IP ผู้สอน>:8000/api/notify'` แจ้งเตือนของผู้เรียนจะขึ้นบนหน้าจอผู้สอน พร้อม IP ของเครื่องที่ส่ง ถ้าส่ง body ผิดรูปแบบ API จะตอบ 400 พร้อมบอกสาเหตุ

ถ้า Windows ถามเรื่อง Firewall ให้อนุญาตเฉพาะ Private network ถ้าผู้เรียนเรียกไม่ได้ ให้ลองเปิด `http://<IP ผู้สอน>:8000/api/meter` ในเบราว์เซอร์ของผู้เรียนก่อน

ถ้าทุกอย่างล่ม ผู้เรียนยังใช้ `API_URL = 'data/meter.json'` ที่อยู่ใน starter ได้ แต่ค่าจะไม่เปลี่ยน

### ใช้ API จริงของบริษัท

รูปแบบข้อมูลใน starter, เฉลย และ API สำรองเป็นแบบนี้:

```json
{ "line": "A", "electric": { "voltage": 231.4, "current": 15.6 }, "water": { "flow": 3.2 }, "updatedAt": "..." }
```

ถ้า API จริงส่งข้อมูลหน้าตาไม่เหมือนนี้ ให้บอกผู้เรียนว่า path ที่ต้องใช้คืออะไร เช่น `data.voltage` แทน `data.electric.voltage` และต้องตรวจก่อนว่า API นั้นอนุญาต CORS ให้เรียกจากหน้าเว็บได้

ช่องแจ้งเตือนจริงในสไลด์ 89 รับ `{"title", "message"}` เหมือน API สำรอง ถ้าจะใช้ ให้ใช้ช่องสำหรับห้องเรียนเท่านั้น ห้ามใช้ช่องแจ้งเตือนจริงของโรงงาน

## แก้โจทย์

เนื้อหาโจทย์อยู่ใน `workshops.json` (หากมีสคริปต์ build ภายนอก `tools/build_workshop_pdf.py` สามารถสร้าง PDF ใหม่ได้):

```bash
python tools/build_workshop_pdf.py "01_Enterprise_Application/03_Workshops_ใบงานและเฉลย"
```

ถ้าแก้โค้ดใน `solution` ของข้อใด ให้คัดลอก `index.html`, `style.css` และ `data/` ไปที่ starter ของข้อถัดไปด้วย starter จะได้ยังต่อจากเฉลยได้
