# โค้ดตัวอย่างสำหรับสอน

ไฟล์ละ 1 เรื่อง เรียงตามลำดับสไลด์ ใช้เปิดดูระหว่างสอน หรือพิมพ์ตามสดให้ผู้เรียนดู ทุกบรรทัดที่มี `// →` คือผลลัพธ์ที่ได้จริง ตรวจด้วยการรันแล้ว

| ไฟล์ | เรื่อง | สไลด์ | เปิดด้วย |
| --- | --- | --- | --- |
| `00-html-css-visual-lab.html` | สื่อการสอน Visual Lab: แท็ก, กล่องซ้อนกล่อง, Box Model, Selector, Flexbox & X-Ray | 25–34 | เบราว์เซอร์ |
| `00-dom-js-visual-lab.html` | สื่อการสอน Visual Lab: JavaScript DOM, Selector, Event และอัปเดตหน้าเว็บแบบเห็นภาพ | 58–70 | เบราว์เซอร์ |
| `01-html-structure.html` | โครง HTML, head/body, Semantic, ตาราง, รายการ, ฟอร์ม | 25–27 | เบราว์เซอร์ |
| `02-css-basics.html` + `02-style.css` | 3 วิธีเขียน CSS, Selector, ตัวอักษร, Box Model, ลำดับความสำคัญ | 28–33 | เบราว์เซอร์ |
| `03-css-flexbox.html` | Flexbox จัดการ์ดเรียงแถว (หน้า Workshop 1) | 34 | เบราว์เซอร์ |
| `04-variables.js` | let, const, var, ชนิดข้อมูล, typeof, การตั้งชื่อ | 39 | Node |
| `05-operators.js` | คำนวณ, ต่อข้อความ, `'10' + 5`, `Number()`, `===` | 40–42 | Node |
| `06-conditions.js` | if / else if / else, switch, `&&` `\|\|` `!`, falsy, ternary | 41–45 | Node |
| `07-array.js` | index, push/pop, for, forEach, map, filter, find | 47–50 | Node |
| `08-object.js` | key/value, อ่าน/แก้/เพิ่ม/ลบ, Object ซ้อน, Array ของ Object | 51–54 | Node |
| `09-function.js` | function, arrow function, parameter, return, ตัดเกรด, checkVoltage | 55–57 | Node |
| `10-dom-select.html` | getElementById, getElementsByClassName, querySelector(All) | 58–62 | เบราว์เซอร์ + Console |
| `11-dom-events.html` | click, input, keydown, mouse, event.target (แนว Workshop 2) | 63–66, 70 | เบราว์เซอร์ |
| `12-dom-content.html` | textContent, innerText, innerHTML, XSS, สร้าง element | 67–69 | เบราว์เซอร์ |
| `13-json.js` | JSON.parse, JSON.stringify, อ่าน path, JSON ที่ผิดรูปแบบ | 73–74, 78 | Node |
| `14-fetch.html` + `data/meter.json` | fetch แบบ then และ async/await, res.ok, error, Polling (แนว Workshop 3) | 81–85 | Live Server |
| `15-webhook-post.html` | POST JSON ไป Webhook, กันกดซ้ำ, preflight (แนว Workshop 4) | 86–90 | Live Server |
| `16-testing.js` | Test Case, ค่าขอบ, รันตรวจอัตโนมัติ, ระดับการทดสอบ | 91–97 | Node |
| `slides_39_to_57_function.js` | สรุปโค้ดสอนสดต่อเนื่องตั้งแต่ Variable ถึง Function ตามลำดับสไลด์ 39–57 | 39–57 | Node |

## วิธีเปิด

ไฟล์ `.js` รันใน Terminal ของ VS Code จากโฟลเดอร์หลักโปรเจ็ค:

```bash
node "01_Enterprise_Application/02_Code_Examples_โค้ดตัวอย่าง/07-array.js"
```

ไฟล์ `.html` ส่วนใหญ่ดับเบิลคลิกเปิดได้เลย ยกเว้น `14-fetch.html` และ `15-webhook-post.html` ต้องเปิดผ่าน Live Server เพราะ fetch ใช้กับ `file://` ไม่ได้ กด F12 เพื่อดู Console และ Network ประกอบการสอน

`15-webhook-post.html` ไม่ได้ใส่ URL ไว้ ให้กรอก URL ช่องแจ้งเตือนของห้องเรียนเองตอนสาธิต ห้ามใช้ช่องแจ้งเตือนจริงของโรงงาน
