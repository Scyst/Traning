/**
 * ระบบเก็บผลประเมินผู้เรียน: Google Forms + Google Sheets
 *
 * ติดตั้ง: สร้าง Google Sheet ใหม่ › ส่วนขยาย › Apps Script › วางโค้ดทั้งไฟล์นี้
 *          › เลือกฟังก์ชัน setup › กด Run แล้วอนุญาตสิทธิ์
 *
 * ไฟล์นี้สร้างจาก tools/build_assessment.py ห้ามแก้ข้อสอบหรือรายชื่อรุ่นในไฟล์นี้ตรง ๆ
 * ให้แก้ที่ quiz.json (Pre-test), quiz_post.json (Post-test) หรือไฟล์ตารางอบรม แล้ว build ใหม่
 * ข้อสอบสองชุดวัด CLO เดียวกันข้อต่อข้อ ผลราย CLO ก่อนและหลังเรียนจึงเทียบกันได้
 *
 * ฟอร์มคือแหล่งข้อมูลหลัก ทุกครั้งที่มีคนส่งฟอร์ม (หรือกดเมนู "อัปเดตสรุปผล")
 * ระบบจะอ่านคำตอบทั้งหมดจากฟอร์มแล้วสร้างชีตสรุปใหม่ทั้งหมด
 */

const SUBJECT = "App (Application Development & IoT)";
const COHORTS = [
  "คอร์สที่ 1 (2 พฤศจิกายน 2569)",
  "คอร์สที่ 2 (9 พฤศจิกายน 2569)",
  "คอร์สที่ 3 (16 พฤศจิกายน 2569)",
  "คอร์สที่ 4 (23 พฤศจิกายน 2569)",
  "คอร์สที่ 5 (30 พฤศจิกายน 2569)",
  "คอร์สที่ 6 (14 ธันวาคม 2569)",
  "คอร์สที่ 7 (21 ธันวาคม 2569)",
  "คอร์สที่ 8 (4 มกราคม 2570)",
  "คอร์สที่ 9 (11 มกราคม 2570)",
  "คอร์สที่ 10 (18 มกราคม 2570)",
  "คอร์สที่ 11 (25 มกราคม 2570)",
  "คอร์สที่ 12 (1 กุมภาพันธ์ 2570)",
  "คอร์สที่ 13 (8 กุมภาพันธ์ 2570)",
  "คอร์สที่ 14 (15 กุมภาพันธ์ 2570)",
  "คอร์สที่ 15 (1 มีนาคม 2570)",
  "คอร์สที่ 16 (8 มีนาคม 2570)",
  "คอร์สที่ 17 (15 มีนาคม 2570)",
  "คอร์สที่ 18 (22 มีนาคม 2570)",
  "คอร์สที่ 19 (29 มีนาคม 2570)"
];
const QUIZ_PRE = [
  {
    "clo": "CLO01",
    "q": "ข้อใดเป็นระบบ OT (Operational Technology)",
    "choices": [
      "ระบบ ERP",
      "ระบบบัญชี",
      "อีเมลองค์กร",
      "PLC และ SCADA"
    ],
    "answer": 3,
    "why": "OT คือระบบที่ควบคุมเครื่องจักรและกระบวนการผลิตโดยตรง เช่น PLC, SCADA, HMI ส่วนข้ออื่นเป็นระบบ IT (โครงสร้างระดับตาม IEC 62264 / ISA-95: PLC อยู่ระดับ 1, SCADA ระดับ 2, ERP ระดับ 4)"
  },
  {
    "clo": "CLO01",
    "q": "ระบบ OT ให้ความสำคัญกับอะไรเป็นอันดับแรก",
    "choices": [
      "ความลับของข้อมูล",
      "ความสวยงามของหน้าจอ",
      "ความปลอดภัยและความพร้อมใช้งานของเครื่องจักร",
      "ราคาถูกที่สุด"
    ],
    "answer": 2,
    "why": "OT เน้น Safety และ Availability เพราะเครื่องหยุดหมายถึงสูญเสียการผลิต ส่วน IT เน้น Confidentiality ก่อน (อ้างอิง NIST SP 800-82 Rev.3 Guide to OT Security)"
  },
  {
    "clo": "CLO01",
    "q": "ในสถาปัตยกรรม Client-Server หน้าที่ของ Client คือข้อใด",
    "choices": [
      "แสดงผลและรับข้อมูลจากผู้ใช้",
      "เก็บฐานข้อมูลหลัก",
      "ประมวลผล Business Logic ทั้งหมด",
      "ควบคุมเครื่องจักรโดยตรง"
    ],
    "answer": 0,
    "why": "Client (เช่น เบราว์เซอร์) แสดงผลและรับ Input ส่วน Server ประมวลผลและเก็บข้อมูล"
  },
  {
    "clo": "CLO02",
    "q": "JSON ข้อใดเขียนถูกต้อง",
    "choices": [
      "{name: 'Line A'}",
      "{\"name\": \"Line A\"}",
      "{'name' = 'Line A'}",
      "[name: \"Line A\"]"
    ],
    "answer": 1,
    "why": "ตาม RFC 8259 ชื่อ key และข้อความต้องอยู่ในเครื่องหมายคำพูดคู่ (\") และคั่น key กับ value ด้วย :"
  },
  {
    "clo": "CLO02",
    "q": "จาก JSON {\"machine\": {\"temp\": 72}} ถ้าเก็บไว้ในตัวแปร data จะอ่านค่า 72 อย่างไร",
    "choices": [
      "data.temp",
      "data[temp]",
      "data.machine.temp",
      "machine.temp.data"
    ],
    "answer": 2,
    "why": "temp อยู่ใน object ชื่อ machine จึงต้องอ่านไล่ชั้น data.machine.temp"
  },
  {
    "clo": "CLO02",
    "q": "จาก {\"sensors\": [10, 20, 30]} ค่า data.sensors[1] คือเท่าไร",
    "choices": [
      "10",
      "20",
      "30",
      "undefined"
    ],
    "answer": 1,
    "why": "index ของ Array เริ่มที่ 0 ดังนั้น index 1 คือตัวที่สอง ได้ 20"
  },
  {
    "clo": "CLO02",
    "q": "ข้อใดไม่ใช่ชนิดข้อมูลที่ JSON รองรับ",
    "choices": [
      "boolean",
      "null",
      "array",
      "function"
    ],
    "answer": 3,
    "why": "ตาม RFC 8259 ค่าใน JSON มีแค่ string, number, boolean (true/false), null, object และ array ไม่มี function"
  },
  {
    "clo": "CLO03",
    "q": "แท็กใดเป็น Semantic HTML",
    "choices": [
      "<header>",
      "<span>",
      "<div>",
      "<b>"
    ],
    "answer": 0,
    "why": "header บอกความหมายว่าเป็นส่วนหัวของหน้า ส่วน div และ span ไม่บอกความหมาย และ b แค่ทำตัวหนา (อ้างอิง HTML Living Standard ของ WHATWG)"
  },
  {
    "clo": "CLO03",
    "q": "การเขียน CSS แบบใดเหมาะกับเว็บที่มีหลายหน้าและใช้สไตล์ร่วมกัน",
    "choices": [
      "Inline Style",
      "Internal Style",
      "External Style Sheet (ไฟล์ .css)",
      "เขียนใน JavaScript ทุกครั้ง"
    ],
    "answer": 2,
    "why": "External Style Sheet แยกเป็นไฟล์เดียว ทุกหน้าลิงก์ไปใช้ได้ แก้ที่เดียวเปลี่ยนทั้งเว็บ"
  },
  {
    "clo": "CLO03",
    "q": "ถ้าต้องการตัวแปรที่เปลี่ยนค่าได้ ควรประกาศด้วยคำใด",
    "choices": [
      "const",
      "let",
      "static",
      "final"
    ],
    "answer": 1,
    "why": "let ใช้กับค่าที่เปลี่ยนได้ const ใช้กับค่าคงที่ ส่วน static และ final ไม่ใช่คำประกาศตัวแปรของ JavaScript"
  },
  {
    "clo": "CLO03",
    "q": "ผลลัพธ์ของ '10' + 5 ใน JavaScript คือข้อใด",
    "choices": [
      "15",
      "'15'",
      "Error",
      "'105'"
    ],
    "answer": 3,
    "why": "เมื่อมี String อยู่ด้วย เครื่องหมาย + จะต่อข้อความ ได้ '105' ค่าจาก input เป็น String จึงต้องแปลงด้วย Number() ก่อน"
  },
  {
    "clo": "CLO03",
    "q": "คำสั่งใดเลือก element ที่มี id=\"status\"",
    "choices": [
      "document.getElementById('status')",
      "document.querySelector('status')",
      "document.getElementsByClassName('status')",
      "document.select('#status')"
    ],
    "answer": 0,
    "why": "getElementById เลือกด้วย id โดยตรง ถ้าใช้ querySelector ต้องเขียน '#status' มีเครื่องหมาย #"
  },
  {
    "clo": "CLO03",
    "q": "ถ้าต้องการให้โค้ดทำงานเมื่อผู้ใช้กดปุ่ม ต้องใช้ Event ใด",
    "choices": [
      "onload",
      "onclick",
      "onmouseover",
      "onkeydown"
    ],
    "answer": 1,
    "why": "onclick เกิดเมื่อคลิก ส่วน onmouseover เกิดเมื่อเอาเมาส์ชี้ และ onkeydown เกิดเมื่อกดแป้นพิมพ์"
  },
  {
    "clo": "CLO04",
    "q": "ตามมาตรฐานสีไฟแสดงสถานะ (IEC 60204-1) สีเหลืองหมายถึงอะไร",
    "choices": [
      "เตือน ต้องเฝ้าระวัง",
      "ทำงานปกติ",
      "หยุดฉุกเฉิน",
      "ออฟไลน์"
    ],
    "answer": 0,
    "why": "ตาม IEC 60204-1 และ IEC 60073 ไฟแสดงสถานะใช้ เขียว = ปกติ, เหลือง = ผิดปกติ ต้องเฝ้าระวัง, แดง = ฉุกเฉิน/อันตราย, น้ำเงิน = ต้องให้ผู้ปฏิบัติงานดำเนินการ"
  },
  {
    "clo": "CLO04",
    "q": "หลัก 5-Second Rule ในการออกแบบ Dashboard หมายถึงอะไร",
    "choices": [
      "หน้าเว็บต้องโหลดเสร็จใน 5 วินาที",
      "อัปเดตข้อมูลทุก 5 วินาที",
      "ผู้ดูต้องเข้าใจสถานะหลักได้ภายใน 5 วินาที",
      "มีเมนูไม่เกิน 5 เมนู"
    ],
    "answer": 2,
    "why": "Dashboard ที่ดีทำให้คนดูรู้สถานะสำคัญทันที โดยใช้ขนาด ตำแหน่ง และสีช่วย"
  },
  {
    "clo": "CLO05",
    "q": "HTTP Method ใดใช้สำหรับอ่านข้อมูล",
    "choices": [
      "GET",
      "POST",
      "PUT",
      "DELETE"
    ],
    "answer": 0,
    "why": "GET = อ่าน, POST = เพิ่ม, PUT = แก้ไข, DELETE = ลบ ตาม RFC 9110 GET เป็น safe method คืออ่านอย่างเดียว ไม่เปลี่ยนข้อมูลใน Server"
  },
  {
    "clo": "CLO05",
    "q": "ข้อใดอธิบายความต่างระหว่างการเรียก API ปกติกับ Webhook ได้ถูกต้อง",
    "choices": [
      "API ปกติระบบต้นทางส่งมาหาเราเอง ส่วน Webhook เราต้องไปขอ",
      "Webhook ใช้ได้เฉพาะกับอีเมล",
      "ทั้งสองเหมือนกันทุกประการ",
      "API ปกติเราไปขอข้อมูล (Pull) ส่วน Webhook ระบบต้นทางส่งมาทันทีเมื่อเกิดเหตุการณ์ (Push)"
    ],
    "answer": 3,
    "why": "Webhook ทำงานแบบ Push เมื่อเกิด Event จึงไม่ต้องคอยถามซ้ำ ๆ"
  },
  {
    "clo": "CLO05",
    "q": "ในโค้ด fetch(url).then(res => res.json()) คำสั่ง res.json() ทำหน้าที่อะไร",
    "choices": [
      "ส่งข้อมูลไปที่ Server",
      "แปลงข้อมูลที่ได้รับเป็น Object ของ JavaScript",
      "ลบข้อมูลใน Server",
      "บันทึกไฟล์ JSON ลงเครื่อง"
    ],
    "answer": 1,
    "why": "res.json() อ่าน Response แล้วแปลง JSON เป็น Object เพื่อใช้ต่อในโค้ด (อ้างอิง Fetch Living Standard ของ WHATWG)"
  },
  {
    "clo": "CLO06",
    "q": "Test Case ที่ดีต้องมีส่วนใดเพื่อตัดสินว่า Pass หรือ Fail",
    "choices": [
      "ชื่อผู้พัฒนา",
      "สีของหน้าจอ",
      "Expected Result (ผลที่คาดหวัง)",
      "ราคาของระบบ"
    ],
    "answer": 2,
    "why": "นำ Actual Result ไปเทียบกับ Expected Result จึงตัดสินได้ว่าผ่านหรือไม่ ISO/IEC/IEEE 29119-3 กำหนดให้ Test Case ระบุผลที่คาดหวังไว้เสมอ"
  },
  {
    "clo": "CLO06",
    "q": "UAT (User Acceptance Testing) ทำโดยใคร",
    "choices": [
      "นักพัฒนาที่เขียนโค้ด",
      "เครื่องมือทดสอบอัตโนมัติเท่านั้น",
      "ผู้ดูแล Server",
      "ผู้ใช้งานจริงหรือลูกค้า"
    ],
    "answer": 3,
    "why": "UAT คือขั้นสุดท้ายที่ผู้ใช้จริงทดสอบในสภาพเหมือนจริงก่อนยอมรับระบบ (อ้างอิง ISTQB Glossary: acceptance testing)"
  }
];
const QUIZ_POST = [
  {
    "clo": "CLO01",
    "q": "ข้อใดเป็นระบบ OT ทั้งหมด",
    "choices": [
      "ERP, CRM และอีเมลองค์กร",
      "PLC, HMI และเซนเซอร์วัดอุณหภูมิ",
      "ฐานข้อมูลบัญชี, HMI และ ERP",
      "เว็บไซต์บริษัท, PLC และอีเมลองค์กร"
    ],
    "answer": 1,
    "why": "PLC, HMI และเซนเซอร์ควบคุมหรือวัดค่าจากกระบวนการผลิตโดยตรงจึงเป็น OT ทั้งหมด ข้ออื่นมีระบบ IT ปนอยู่ (โครงสร้างระดับตาม IEC 62264 / ISA-95)"
  },
  {
    "clo": "CLO01",
    "q": "ทีม IT ต้องการติดตั้งอัปเดตความปลอดภัยให้คอมพิวเตอร์ที่ควบคุมเครื่องจักรทันทีระหว่างกะผลิต ข้อกังวลหลักจากมุมมอง OT คือข้อใด",
    "choices": [
      "หน้าจออาจเปลี่ยนสี",
      "ค่าลิขสิทธิ์ซอฟต์แวร์อาจสูงขึ้น",
      "ข้อมูลอาจถูกส่งออกไปนอกบริษัท",
      "การรีสตาร์ตอาจทำให้เครื่องจักรหยุด กระทบการผลิตและความปลอดภัย"
    ],
    "answer": 3,
    "why": "OT ให้ความสำคัญกับ Safety และ Availability การอัปเดตจึงต้องวางแผนช่วงหยุดเครื่อง ไม่ทำกลางกะผลิต (อ้างอิง NIST SP 800-82 Rev.3)"
  },
  {
    "clo": "CLO01",
    "q": "ในระบบ Dashboard ค่าน้ำ-ไฟของ Workshop ส่วนใดทำงานอยู่ฝั่ง Server",
    "choices": [
      "การตอบค่าน้ำ-ไฟเป็น JSON ผ่าน /api/meter",
      "การเปลี่ยนสีป้ายสถานะเมื่อกดปุ่ม",
      "การตรวจค่าที่ผู้ใช้พิมพ์ในช่อง input ทันที",
      "การแสดงเวลาอัปเดตล่าสุดบนหน้าจอ"
    ],
    "answer": 0,
    "why": "API ที่ตอบข้อมูลอยู่บน Server ส่วนการแสดงผลและการตรวจค่าที่ผู้ใช้พิมพ์ทำด้วย JavaScript ในเบราว์เซอร์ (Client)"
  },
  {
    "clo": "CLO02",
    "q": "JSON ข้อใดถูกต้องทั้งหมด",
    "choices": [
      "{\"line\": \"A\", \"temps\": [72.5, 73.0,]}",
      "{\"line\": \"A\", \"online\": True}",
      "{\"line\": \"A\", \"temps\": [72.5, 73.0]}",
      "{\"line\": \"A\", \"note\": undefined}"
    ],
    "answer": 2,
    "why": "ตาม RFC 8259 ห้ามมี comma ตัวสุดท้ายแม้อยู่ใน Array ค่า boolean ต้องเป็น true ตัวเล็ก และไม่มีค่า undefined"
  },
  {
    "clo": "CLO02",
    "q": "data = {\"line\": {\"name\": \"A\", \"machines\": [{\"id\": \"M-01\", \"sensors\": {\"temp\": 72}}, {\"id\": \"M-02\", \"sensors\": {\"temp\": 65}}]}}  ต้องเขียนอย่างไรจึงได้ค่า 65",
    "choices": [
      "data.machines[1].sensors.temp",
      "data.line.machines[2].sensors.temp",
      "data.line.machines[1].temp",
      "data.line.machines[1].sensors.temp"
    ],
    "answer": 3,
    "why": "ไล่ทีละชั้น: line เป็น Object › machines เป็น Array ตัวที่สองคือ [1] › sensors เป็น Object › อ่าน temp"
  },
  {
    "clo": "CLO02",
    "q": "จาก {\"sensors\": [10, 20, 30, 40]} ค่า data.sensors[data.sensors.length - 2] คือเท่าไร",
    "choices": [
      "20",
      "30",
      "40",
      "undefined"
    ],
    "answer": 1,
    "why": "length คือ 4 ดังนั้น length - 2 คือ index 2 ซึ่งเป็นตัวที่สาม ได้ 30 (index เริ่มที่ 0)"
  },
  {
    "clo": "CLO02",
    "q": "JSON.stringify({ a: 1, b: undefined, c: null }) ได้ผลลัพธ์ใด",
    "choices": [
      "{\"a\":1,\"c\":null}",
      "{\"a\":1,\"b\":undefined,\"c\":null}",
      "{\"a\":1,\"b\":null,\"c\":null}",
      "{\"a\":1}"
    ],
    "answer": 0,
    "why": "JSON ไม่มีชนิด undefined จึงตัด key b ทิ้ง แต่ null เป็นค่าที่ JSON รองรับจึงยังอยู่ (อ้างอิง RFC 8259 และ ECMA-262)"
  },
  {
    "clo": "CLO03",
    "q": "ต้องการทำเมนูลิงก์ไปหน้าต่าง ๆ ของ Dashboard ควรใช้แท็ก Semantic ใดครอบเมนู",
    "choices": [
      "<div class=\"menu\">",
      "<span>",
      "<footer>",
      "<nav>"
    ],
    "answer": 3,
    "why": "nav ใช้สำหรับกลุ่มลิงก์นำทาง div และ span ไม่บอกความหมาย ส่วน footer คือส่วนท้ายของหน้า (อ้างอิง HTML Living Standard ของ WHATWG)"
  },
  {
    "clo": "CLO03",
    "q": "ไฟล์ style.css กำหนด p { color: blue; } แต่ในหน้าเว็บเขียน <p style=\"color: red\">ข้อความ</p> ข้อความจะเป็นสีอะไร",
    "choices": [
      "แดง เพราะ style ที่เขียนในแท็กเจาะจงกว่า",
      "น้ำเงิน เพราะไฟล์ CSS ภายนอกสำคัญที่สุด",
      "ดำ เพราะกฎขัดกันจึงใช้ค่าเริ่มต้น",
      "ม่วง เพราะสีผสมกัน"
    ],
    "answer": 0,
    "why": "Inline style ในแท็กมีลำดับความสำคัญสูงกว่า Selector ในไฟล์ CSS ภายนอก จึงนิยมใช้ External CSS เป็นหลักแล้วหลีกเลี่ยง Inline"
  },
  {
    "clo": "CLO03",
    "q": "โค้ดใดทำงานได้โดยไม่เกิด error",
    "choices": [
      "const max = 240; max = 250;",
      "const list; list = [];",
      "let count = 0; count = count + 1;",
      "let x = 1; let x = 2;"
    ],
    "answer": 2,
    "why": "let เปลี่ยนค่าได้ ส่วน const กำหนดค่าใหม่ไม่ได้และต้องใส่ค่าตอนประกาศ และประกาศ let ชื่อซ้ำในขอบเขตเดียวกันไม่ได้ (อ้างอิง ECMAScript 2015)"
  },
  {
    "clo": "CLO03",
    "q": "ผลลัพธ์ของ '10' - 5 + '5' ใน JavaScript คือข้อใด",
    "choices": [
      "10",
      "'55'",
      "'105'",
      "NaN"
    ],
    "answer": 1,
    "why": "คำนวณจากซ้ายไปขวา: '10' - 5 แปลงเป็นตัวเลขได้ 5 จากนั้น 5 + '5' มี String จึงต่อข้อความได้ '55'"
  },
  {
    "clo": "CLO03",
    "q": "ข้อใดเลือก element เดียวกับ document.getElementById('status')",
    "choices": [
      "document.querySelector('.status')",
      "document.querySelector('status')",
      "document.getElementsByClassName('status')",
      "document.querySelector('#status')"
    ],
    "answer": 3,
    "why": "querySelector ใช้ CSS Selector ต้องใส่ # นำหน้าเพื่อเลือกด้วย id ส่วน . คือ class และไม่ใส่เครื่องหมายคือชื่อแท็ก"
  },
  {
    "clo": "CLO03",
    "q": "ต้องการตรวจค่าแรงดันทุกครั้งที่ผู้ใช้พิมพ์ในช่อง input ทันทีโดยไม่ต้องกดปุ่ม ควรผูก Event ใด",
    "choices": [
      "input",
      "click",
      "load",
      "submit"
    ],
    "answer": 0,
    "why": "Event input เกิดทุกครั้งที่ค่าในช่องเปลี่ยน ส่วน click ต้องกด และ submit เกิดตอนส่งฟอร์ม"
  },
  {
    "clo": "CLO04",
    "q": "ตามมาตรฐาน IEC 60204-1 ไฟแสดงสถานะสีใดหมายถึง \"ต้องให้ผู้ปฏิบัติงานดำเนินการ\"",
    "choices": [
      "เขียว",
      "เหลือง",
      "น้ำเงิน",
      "ขาว"
    ],
    "answer": 2,
    "why": "ตาม IEC 60204-1 และ IEC 60073 น้ำเงิน = ต้องให้ผู้ปฏิบัติงานดำเนินการ, เขียว = ปกติ, เหลือง = ผิดปกติ, แดง = ฉุกเฉิน, ขาว = ไม่มีความหมายเฉพาะ"
  },
  {
    "clo": "CLO04",
    "q": "Dashboard หน้าหนึ่งแสดงตัวเลข 30 ค่าขนาดเท่ากันหมดและใช้สีต่างกัน 10 สี ข้อใดเป็นการปรับที่ตรงหลักการออกแบบมากที่สุด",
    "choices": [
      "เพิ่มค่าให้ครบทุกค่าที่มีในระบบ",
      "ใช้สีต่างกันทุกค่าเพื่อให้แยกง่าย",
      "ย่อตัวเลขให้เล็กลงเพื่อใส่ได้มากขึ้น",
      "แสดงค่าสำคัญไม่กี่ค่าเป็น KPI ขนาดใหญ่ด้านบน และใช้สีเฉพาะบอกสถานะ"
    ],
    "answer": 3,
    "why": "หลัก 5-Second Rule และ Visual Hierarchy: ค่าสำคัญต้องเด่นและอ่านได้ทันที ใช้สีเพื่อบอกสถานะเท่านั้น (ANSI/ISA-101.01 แนะนำให้ใช้สีสดเฉพาะสถานะผิดปกติ)"
  },
  {
    "clo": "CLO05",
    "q": "HTTP Method ใด ถ้าถูกเรียกซ้ำโดยไม่ตั้งใจ มีโอกาสสร้างข้อมูลหรือแจ้งเตือนซ้ำมากที่สุด",
    "choices": [
      "POST",
      "GET",
      "PUT",
      "DELETE"
    ],
    "answer": 0,
    "why": "ตาม RFC 9110 GET, PUT และ DELETE เป็น idempotent เรียกซ้ำผลเหมือนเรียกครั้งเดียว ส่วน POST ไม่ใช่ จึงต้องกันการกดส่งซ้ำ"
  },
  {
    "clo": "CLO05",
    "q": "Dashboard ถาม Server ทุก 30 วินาที ถ้าเครื่องจักรหยุด 1 วินาทีหลังรอบถามล่าสุด Dashboard จะรู้ช้าสุดประมาณเท่าไร และควรแก้อย่างไร",
    "choices": [
      "ประมาณ 1 วินาที ไม่ต้องแก้",
      "ประมาณ 29 วินาที ควรให้ Server ส่ง Webhook มาทันทีเมื่อเกิดเหตุการณ์",
      "ประมาณ 30 นาที ควรเพิ่มรอบเป็นทุก 1 นาที",
      "รู้ทันที เพราะ Polling เป็นแบบ Push"
    ],
    "answer": 1,
    "why": "Polling ต้องรอรอบถามถัดไป (30 - 1 = 29 วินาที) ส่วน Webhook ทำงานแบบ Push ส่งมาทันทีเมื่อเกิดเหตุการณ์"
  },
  {
    "clo": "CLO05",
    "q": "ข้อใดเรียงลำดับการดึงข้อมูลด้วย fetch ได้ถูกต้อง",
    "choices": [
      "แปลงด้วย res.json() › ส่ง Request › ตรวจ res.ok › แสดงผล",
      "ส่ง Request › ได้ Response › ตรวจ res.ok › แปลงด้วย res.json() › แสดงผล",
      "ส่ง Request › แสดงผล › ได้ Response › ตรวจ res.ok",
      "ตรวจ res.ok › ส่ง Request › แปลงด้วย res.json() › แสดงผล"
    ],
    "answer": 1,
    "why": "ต้องได้ Response ก่อนจึงตรวจสถานะได้ และตรวจ res.ok ก่อนแปลงข้อมูล เพราะ fetch ไม่ reject เมื่อได้ 404 หรือ 500 (อ้างอิง Fetch Living Standard ของ WHATWG)"
  },
  {
    "clo": "CLO06",
    "q": "Test Case ใดเขียนผลที่คาดหวัง (Expected Result) ได้ดีที่สุด",
    "choices": [
      "ระบบทำงานถูกต้อง",
      "หน้าจอแสดงผลสวยงาม",
      "กรอก 245 แล้วแสดง \"Warning: แรงดันเกิน 240 V\" สีแดงภายใน 1 วินาที",
      "ไม่พบข้อผิดพลาด"
    ],
    "answer": 2,
    "why": "ผลที่คาดหวังต้องวัดได้และระบุชัดว่าต้องเห็นอะไร จึงตัดสิน Pass/Fail ได้ตรงกันทุกคน (อ้างอิง ISO/IEC/IEEE 29119-3)"
  },
  {
    "clo": "CLO06",
    "q": "ข้อใดไม่ใช่ลักษณะของ UAT (User Acceptance Testing)",
    "choices": [
      "ผู้ใช้จริงทดสอบตามงานที่ทำจริง",
      "ทดสอบก่อนเริ่มใช้งานจริง (Go-Live)",
      "นักพัฒนาเขียนโค้ดทดสอบฟังก์ชันย่อยทีละฟังก์ชัน",
      "ผู้ใช้ลงชื่อยอมรับหรือไม่ยอมรับระบบ"
    ],
    "answer": 2,
    "why": "การทดสอบฟังก์ชันย่อยโดยนักพัฒนาคือ Unit Testing ส่วน UAT ให้ผู้ใช้จริงทดสอบแล้วยอมรับก่อนใช้งานจริง (อ้างอิง ISTQB Glossary)"
  }
];
const QUIZZES = { "Pre-test": QUIZ_PRE, "Post-test": QUIZ_POST };
const MAX_SEAT = 40;
const CLOS = Array.from(new Set(QUIZ_PRE.map(q => q.clo))).sort();

const SHEET = {
  learners: "ผู้เรียน",
  summary: "สรุปรายคน",
  report: "รายงานรายคน",
  cohorts: "สรุปรายรุ่น",
  attempts: "ผลแบบทดสอบ",
  satisfaction: "ความพึงพอใจ",
  settings: "ตั้งค่า"
};

const LEARNER_HEAD = ["รุ่น", "เลขที่", "ชื่อ-นามสกุล", "หน่วยงาน", "เข้าเรียน (ช่วง)",
  "สอบทฤษฎี (%)", "สอบปฏิบัติ (%)", "นำเสนอ/UAT (%)", "หมายเหตุ"];

const SETTINGS = [
  ["จำนวนช่วงเช็กชื่อทั้งหมด", 8, "4 วัน × เช้า/บ่าย"],
  ["เวลาเรียนขั้นต่ำ (%)", 80, "ค่าเริ่มต้น แก้ให้ตรงเกณฑ์โครงการ"],
  ["น้ำหนักสอบทฤษฎี (%)", 30, "ค่าเริ่มต้น แก้ให้ตรงเกณฑ์โครงการ"],
  ["น้ำหนักสอบปฏิบัติ (%)", 40, "ค่าเริ่มต้น แก้ให้ตรงเกณฑ์โครงการ"],
  ["น้ำหนักนำเสนอ/UAT (%)", 30, "ค่าเริ่มต้น แก้ให้ตรงเกณฑ์โครงการ"],
  ["คะแนนรวมขั้นต่ำที่ผ่าน (%)", 60, "ค่าเริ่มต้น แก้ให้ตรงเกณฑ์โครงการ"]
];

const SATISFACTION_ITEMS = [
  "เนื้อหาหลักสูตรสอดคล้องกับลักษณะงานที่ปฏิบัติหรือจะปฏิบัติ",
  "ความรู้และความเข้าใจในเนื้อหาภายหลังการฝึกอบรม",
  "วิทยากรถ่ายทอดความรู้ได้ชัดเจน และตอบข้อซักถามได้ตรงประเด็น",
  "กิจกรรมฝึกปฏิบัติ (Workshop) ช่วยให้สามารถนำความรู้ไปปฏิบัติได้จริง",
  "ระยะเวลาและลำดับของเนื้อหามีความเหมาะสม",
  "สถานที่ เครื่องคอมพิวเตอร์ และอุปกรณ์ประกอบการฝึกอบรมมีความเหมาะสม",
  "สามารถนำความรู้ที่ได้รับไปประยุกต์ใช้ในการปฏิบัติงานได้",
  "ความพึงพอใจโดยรวมต่อการฝึกอบรม"
];

const SATISFACTION_TEXT = {
  title: "แบบประเมินความพึงพอใจต่อการฝึกอบรม · " + SUBJECT,
  description: "แบบประเมินนี้ไม่ต้องระบุชื่อผู้ตอบ ข้อมูลที่ได้รับจะนำไปใช้ปรับปรุงหลักสูตรสำหรับการฝึกอบรมในรุ่นถัดไป\n" +
    "โปรดเลือกระดับความพึงพอใจในแต่ละข้อ โดย 1 หมายถึงน้อยที่สุด และ 5 หมายถึงมากที่สุด",
  confirmation: "ขอขอบคุณที่สละเวลาตอบแบบประเมิน",
  cohort: "รุ่นที่เข้ารับการฝึกอบรม",
  low: "น้อยที่สุด",
  high: "มากที่สุด",
  liked: "ประโยชน์ที่ได้รับจากการฝึกอบรมครั้งนี้",
  improve: "ข้อเสนอแนะเพื่อการปรับปรุงการฝึกอบรม"
};

const ATTEMPT_HEAD = ["เวลาส่ง", "รอบ", "รุ่น", "เลขที่", "ชื่อที่กรอก", "คะแนน (เต็ม " + QUIZ_PRE.length + ")"]
  .concat(CLOS.map(c => c + " (ถูก/ทั้งหมด)"));

const SUMMARY_HEAD = ["รหัสรายงาน", "รุ่น", "เลขที่", "ชื่อ-นามสกุล", "หน่วยงาน",
  "Pre-test", "Post-test", "คะแนนเพิ่มขึ้น"]
  .concat(CLOS.map(c => c + " Pre (%)"))
  .concat(CLOS.map(c => c + " Post (%)"))
  .concat(["เข้าเรียน (%)", "สอบทฤษฎี (%)", "สอบปฏิบัติ (%)", "นำเสนอ/UAT (%)",
    "คะแนนรวม (%)", "ผลการประเมิน", "หมายเหตุ"]);

const COHORT_HEAD = ["รุ่น", "ผู้เรียน", "ทำ Pre-test", "ทำ Post-test", "Pre-test เฉลี่ย",
  "Post-test เฉลี่ย", "เพิ่มขึ้นเฉลี่ย", "ผ่าน", "ไม่ผ่าน", "รอข้อมูล",
  "ผู้ตอบแบบประเมิน", "ความพึงพอใจเฉลี่ย (เต็ม 5)"];

const SATISFACTION_HEAD = ["เวลาส่ง", "รุ่น"].concat(SATISFACTION_ITEMS)
  .concat(["เฉลี่ย", "ประโยชน์ที่ได้รับ", "ข้อเสนอแนะ"]);

/* ---------------------------------------------------------------- menu */

function onOpen() {
  SpreadsheetApp.getUi().createMenu("ระบบประเมิน")
    .addItem("อัปเดตสรุปผล", "updateSummary")
    .addItem("อัปเดตข้อความในฟอร์ม", "syncFormText")
    .addItem("สร้างคำถาม Post-test ใหม่ (เมื่อยังไม่มีคำตอบ)", "rebuildPostTest")
    .addToUi();
}

/* --------------------------------------------------------------- setup */

function setup() {
  const props = PropertiesService.getScriptProperties();
  if (props.getProperty("config")) {
    notify_("ไฟล์นี้ตั้งค่าไปแล้ว ถ้าต้องการชุดใหม่ ให้สร้าง Google Sheet ไฟล์ใหม่แล้ววางโค้ดอีกครั้ง");
    return;
  }
  const ss = SpreadsheetApp.getActive();
  ss.rename("ผลประเมินผู้เรียน · " + SUBJECT);
  buildSheets_(ss);

  const config = {
    spreadsheetId: ss.getId(),
    pre: createQuizForm_("Pre-test"),
    post: createQuizForm_("Post-test"),
    sat: createSatisfactionForm_()
  };
  props.setProperty("config", JSON.stringify(config));

  [config.pre.id, config.post.id, config.sat.id].forEach(id =>
    ScriptApp.newTrigger("onAnySubmit").forForm(FormApp.openById(id)).onFormSubmit().create());

  const s = ss.getSheetByName(SHEET.settings);
  const links = [
    ["ลิงก์สำหรับผู้เรียน", "", ""],
    ["Pre-test", config.pre.url, "แจกวันที่ 1 เวลา 09:15"],
    ["Post-test", config.post.url, "แจกวันที่ 4 เวลา 15:00"],
    ["แบบประเมินความพึงพอใจ", config.sat.url, "แจกวันที่ 4 ก่อนปิดคอร์ส"],
    ["", "", ""],
    ["ลิงก์แก้ไขฟอร์ม (เฉพาะผู้สอน)", "", ""],
    ["แก้ไข Pre-test", config.pre.edit, ""],
    ["แก้ไข Post-test", config.post.edit, ""],
    ["แก้ไขแบบประเมิน", config.sat.edit, ""]
  ];
  s.getRange(SETTINGS.length + 3, 1, links.length, 3).setValues(links);
  s.getRange(SETTINGS.length + 3, 1).setFontWeight("bold");
  s.getRange(SETTINGS.length + 8, 1).setFontWeight("bold");

  updateSummary();
  ss.setActiveSheet(s);
  notify_("ตั้งค่าเสร็จแล้ว ลิงก์ฟอร์มทั้งหมดอยู่ในชีต \"ตั้งค่า\"");
}

function buildSheets_(ss) {
  const first = ss.getSheets()[0];
  const order = [SHEET.learners, SHEET.summary, SHEET.report, SHEET.cohorts,
    SHEET.attempts, SHEET.satisfaction, SHEET.settings];
  order.forEach((name, i) => {
    const sh = i === 0 ? first.setName(name) : ss.insertSheet(name);
    sh.setFrozenRows(1);
  });

  const learners = ss.getSheetByName(SHEET.learners);
  learners.getRange(1, 1, 1, LEARNER_HEAD.length).setValues([LEARNER_HEAD]).setFontWeight("bold");
  learners.getRange("A2:A").setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(COHORTS, true).build());
  learners.getRange("B2:B").setDataValidation(
    SpreadsheetApp.newDataValidation().requireNumberBetween(1, MAX_SEAT).build());
  learners.getRange("E2:H").setDataValidation(
    SpreadsheetApp.newDataValidation().requireNumberBetween(0, 100).build());
  learners.setColumnWidth(1, 220);
  learners.setColumnWidth(3, 200);

  const settings = ss.getSheetByName(SHEET.settings);
  settings.getRange(1, 1, 1, 3).setValues([["รายการ", "ค่า", "หมายเหตุ"]]).setFontWeight("bold");
  settings.getRange(2, 1, SETTINGS.length, 3).setValues(SETTINGS);
  settings.setColumnWidth(1, 240);
  settings.setColumnWidth(2, 360);

  const summary = ss.getSheetByName(SHEET.summary);
  summary.getRange(1, 1, 1, SUMMARY_HEAD.length).setValues([SUMMARY_HEAD]).setFontWeight("bold");

  const report = ss.getSheetByName(SHEET.report);
  report.getRange("A1").setValue("รายงานผลผู้เรียน · " + SUBJECT).setFontWeight("bold").setFontSize(14);
  report.getRange("A2").setValue("เลือกผู้เรียน").setFontWeight("bold");
  report.getRange("B2").setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInRange(summary.getRange("A2:A"), true).build());
  const rows = SUMMARY_HEAD.slice(1).map((label, i) => [label,
    '=IF($B$2="","",IFERROR(VLOOKUP($B$2,\'' + SHEET.summary + '\'!$A:$BZ,' + (i + 2) + ',FALSE),""))']);
  report.getRange(4, 1, rows.length, 2).setValues(rows);
  report.getRange(4, 1, rows.length, 1).setFontWeight("bold");
  report.setColumnWidth(1, 200);
  report.setColumnWidth(2, 320);
  report.setFrozenRows(2);
}

function createQuizForm_(round) {
  const quiz = QUIZZES[round];
  const form = FormApp.create(round + " · " + SUBJECT)
    .setDescription("แบบทดสอบ " + quiz.length + " ข้อ ข้อละ 1 คะแนน ใช้เวลาประมาณ 15 นาที\n" +
      "เลือกรุ่นและเลขที่ให้ตรงกับใบรายชื่อที่ผู้สอนแจก ส่งแล้วกดดูคะแนนได้ทันที")
    .setIsQuiz(true)
    .setCollectEmail(false)
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage("ส่งคำตอบแล้ว ขอบคุณครับ");

  const items = identityItems_(form);
  form.addPageBreakItem().setTitle("แบบทดสอบ");
  const questions = addQuizItems_(form, quiz);
  return { id: form.getId(), url: form.getPublishedUrl(), edit: form.getEditUrl(), items: items, questions: questions };
}

function addQuizItems_(form, quiz) {
  return quiz.map((q, i) => {
    const item = form.addMultipleChoiceItem();
    item.setTitle((i + 1) + ". " + q.q)
      .setChoices(q.choices.map((c, j) => item.createChoice(c, j === q.answer)))
      .setPoints(1)
      .setRequired(true)
      .setFeedbackForCorrect(FormApp.createFeedback().setText(q.why).build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText(q.why).build());
    return item.getId();
  });
}

/**
 * แทนคำถามทั้งหมดในฟอร์ม Post-test ที่ติดตั้งแล้วด้วยข้อสอบ Post-test ชุดปัจจุบัน
 * ลิงก์และ QR code เดิมใช้ต่อได้ ทำได้เฉพาะเมื่อฟอร์มยังไม่มีคำตอบ (ลบคำตอบทดสอบก่อน)
 */
function rebuildPostTest() {
  const props = PropertiesService.getScriptProperties();
  const config = JSON.parse(props.getProperty("config"));
  const form = FormApp.openById(config.post.id);
  const responses = form.getResponses().length;
  if (responses > 0) {
    throw new Error("ฟอร์ม Post-test มีคำตอบแล้ว " + responses + " รายการ ลบคำตอบในแท็บ Responses ก่อน แล้วรันใหม่");
  }
  config.post.questions.forEach(id => form.deleteItem(form.getItemById(id)));
  config.post.questions = addQuizItems_(form, QUIZ_POST);
  props.setProperty("config", JSON.stringify(config));
  updateSummary();
  notify_("สร้างคำถาม Post-test ชุดใหม่แล้ว " + QUIZ_POST.length + " ข้อ ลิงก์เดิมใช้ต่อได้");
}

function identityItems_(form) {
  const seats = [];
  for (let i = 1; i <= MAX_SEAT; i++) seats.push(String(i));
  const cohort = form.addListItem().setTitle("รุ่น").setChoiceValues(COHORTS).setRequired(true);
  const seat = form.addListItem().setTitle("เลขที่").setHelpText("เลขที่ตามใบรายชื่อที่ผู้สอนแจก")
    .setChoiceValues(seats).setRequired(true);
  const name = form.addTextItem().setTitle("ชื่อ-นามสกุล").setRequired(true);
  return { cohort: cohort.getId(), seat: seat.getId(), name: name.getId() };
}

function createSatisfactionForm_() {
  const t = SATISFACTION_TEXT;
  const form = FormApp.create(t.title)
    .setDescription(t.description)
    .setCollectEmail(false)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage(t.confirmation);
  const cohort = form.addListItem().setTitle(t.cohort).setChoiceValues(COHORTS).setRequired(true);
  const scales = SATISFACTION_ITEMS.map(s => form.addScaleItem().setTitle(s)
    .setBounds(1, 5).setLabels(t.low, t.high).setRequired(true).getId());
  const liked = form.addParagraphTextItem().setTitle(t.liked).getId();
  const improve = form.addParagraphTextItem().setTitle(t.improve).getId();
  return { id: form.getId(), url: form.getPublishedUrl(), edit: form.getEditUrl(),
    cohort: cohort.getId(), scales: scales, liked: liked, improve: improve };
}

/**
 * แก้ข้อความในฟอร์มที่ติดตั้งแล้วให้ตรงกับไฟล์นี้ คำตอบเดิมยังอยู่ครบ
 * - Pre/Post-test: ชื่อคำถามและคำอธิบายเฉลย (ตัวเลือกและคำตอบที่ถูกต้องเหมือนเดิม ไม่อย่างนั้นต้องติดตั้งใหม่)
 * - แบบประเมินความพึงพอใจ: ชื่อฟอร์ม คำชี้แจง ข้อความหลังส่ง และข้อความของแต่ละข้อ
 */
function syncFormText() {
  const config = JSON.parse(PropertiesService.getScriptProperties().getProperty("config"));
  const sat = FormApp.openById(config.sat.id);
  if (config.sat.scales.length !== SATISFACTION_ITEMS.length) {
    throw new Error("จำนวนข้อในแบบประเมินความพึงพอใจไม่ตรงกับไฟล์นี้ ต้องติดตั้งใหม่");
  }
  const forms = [[config.pre, QUIZ_PRE], [config.post, QUIZ_POST]]
    .map(([f, quiz]) => ({ form: FormApp.openById(f.id), ids: f.questions, quiz: quiz }));

  // ตรวจทั้งสองฟอร์มก่อน แก้เฉพาะเมื่อทุกข้อตรงกัน จะได้ไม่แก้ไปครึ่งเดียว
  forms.forEach(({ form, ids, quiz }) => ids.forEach((id, i) => {
    const choices = form.getItemById(id).asMultipleChoiceItem().getChoices();
    const values = choices.map(c => c.getValue());
    const correct = choices.findIndex(c => c.isCorrectAnswer());
    if (values.join("\n") !== quiz[i].choices.join("\n") || correct !== quiz[i].answer) {
      throw new Error("ข้อ " + (i + 1) + " ในฟอร์ม \"" + form.getTitle() + "\" มีตัวเลือกหรือคำตอบไม่ตรงกับไฟล์นี้ " +
        "ถ้าเป็น Post-test ให้รัน rebuildPostTest ก่อน");
    }
  }));

  let titles = 0;
  forms.forEach(({ form, ids, quiz }) => ids.forEach((id, i) => {
    const item = form.getItemById(id).asMultipleChoiceItem();
    const title = (i + 1) + ". " + quiz[i].q;
    if (item.getTitle() !== title) {
      item.setTitle(title);
      titles++;
    }
    item.setFeedbackForCorrect(FormApp.createFeedback().setText(quiz[i].why).build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText(quiz[i].why).build());
  }));

  const t = SATISFACTION_TEXT;
  sat.setTitle(t.title).setDescription(t.description).setConfirmationMessage(t.confirmation);
  sat.getItemById(config.sat.cohort).setTitle(t.cohort);
  config.sat.scales.forEach((id, i) => {
    sat.getItemById(id).asScaleItem().setTitle(SATISFACTION_ITEMS[i]).setLabels(t.low, t.high);
  });
  sat.getItemById(config.sat.liked).setTitle(t.liked);
  sat.getItemById(config.sat.improve).setTitle(t.improve);

  updateSummary();   // หัวตารางในชีตความพึงพอใจใช้ข้อความชุดใหม่
  notify_("อัปเดตฟอร์มแล้ว: Pre/Post-test แก้ชื่อคำถาม " + titles + " จุดและคำอธิบายเฉลยครบทุกข้อ " +
    "และแบบประเมินความพึงพอใจใช้ข้อความชุดใหม่ทั้งฟอร์ม");
}

/* -------------------------------------------------------------- update */

function onAnySubmit() {
  updateSummary();
}

function updateSummary() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(60000)) return; // another run is rebuilding; it reads every response anyway
  try {
    const config = JSON.parse(PropertiesService.getScriptProperties().getProperty("config"));
    const ss = SpreadsheetApp.openById(config.spreadsheetId);
    const attempts = readQuiz_(config.pre, "Pre-test").concat(readQuiz_(config.post, "Post-test"))
      .sort((a, b) => a.time - b.time);
    const sat = readSatisfaction_(config.sat);
    const result = computeSummary(readLearners_(ss), attempts, sat, readSettings_(ss));

    writeTable_(ss.getSheetByName(SHEET.attempts), ATTEMPT_HEAD, attempts.map(attemptRow));
    writeTable_(ss.getSheetByName(SHEET.summary), SUMMARY_HEAD, result.rows);
    writeTable_(ss.getSheetByName(SHEET.cohorts), COHORT_HEAD, result.cohorts);
    writeTable_(ss.getSheetByName(SHEET.satisfaction), SATISFACTION_HEAD, sat.map(satisfactionRow));
  } finally {
    lock.releaseLock();
  }
}

function readQuiz_(f, round) {
  return FormApp.openById(f.id).getResponses().map(r => {
    const byId = responsesById_(r);
    return gradeAttempt({
      time: r.getTimestamp(),
      round: round,
      cohort: String(byId[f.items.cohort] || ""),
      seat: Number(byId[f.items.seat]) || "",
      name: String(byId[f.items.name] || "").trim(),
      answers: f.questions.map(id => byId[id] == null ? "" : String(byId[id]))
    });
  });
}

function readSatisfaction_(f) {
  return FormApp.openById(f.id).getResponses().map(r => {
    const byId = responsesById_(r);
    return {
      time: r.getTimestamp(),
      cohort: String(byId[f.cohort] || ""),
      scores: f.scales.map(id => Number(byId[id]) || ""),
      liked: String(byId[f.liked] || ""),
      improve: String(byId[f.improve] || "")
    };
  });
}

function responsesById_(r) {
  const byId = {};
  r.getItemResponses().forEach(ir => { byId[ir.getItem().getId()] = ir.getResponse(); });
  return byId;
}

function readLearners_(ss) {
  const values = ss.getSheetByName(SHEET.learners).getDataRange().getValues().slice(1);
  return values
    .filter(v => String(v[0]).trim() && num(v[1]) !== "")
    .map(v => ({
      cohort: String(v[0]).trim(), seat: num(v[1]), name: String(v[2]).trim(), org: String(v[3]).trim(),
      sessions: num(v[4]), theory: num(v[5]), practical: num(v[6]), present: num(v[7]), note: String(v[8]).trim()
    }));
}

function readSettings_(ss) {
  const v = ss.getSheetByName(SHEET.settings).getRange(2, 2, SETTINGS.length, 1).getValues().map(r => Number(r[0]));
  return { sessions: v[0], minAttend: v[1], wTheory: v[2], wPractical: v[3], wPresent: v[4], pass: v[5] };
}

function writeTable_(sheet, head, rows) {
  sheet.clearContents();
  sheet.getRange(1, 1, 1, head.length).setValues([head]).setFontWeight("bold");
  if (rows.length) sheet.getRange(2, 1, rows.length, head.length).setValues(rows);
}

function notify_(msg) {
  try { SpreadsheetApp.getUi().alert(msg); } catch (e) { Logger.log(msg); }
}

/* ------------------------------------------- pure logic (tested in Node) */

function num(v) {
  if (v === "" || v == null) return "";
  const n = Number(v);
  return isNaN(n) ? "" : n;
}

function round1(x) {
  return Math.round(x * 10) / 10;
}

function keyOf(cohort, seat) {
  return cohort + "|" + Number(seat);
}

function cohortNo(label) {
  const m = String(label).match(/(\d+)/);
  return m ? Number(m[1]) : 9999;
}

function sameName(a, b) {
  const norm = s => String(s).replace(/\s+/g, "").toLowerCase();
  return norm(a) === norm(b);
}

function gradeAttempt(a) {
  const quiz = QUIZZES[a.round] || QUIZ_PRE;
  const clo = {};
  CLOS.forEach(c => { clo[c] = { ok: 0, all: 0 }; });
  let score = 0;
  quiz.forEach((q, i) => {
    const ok = a.answers[i] === q.choices[q.answer];
    clo[q.clo].all++;
    if (ok) { clo[q.clo].ok++; score++; }
  });
  return Object.assign({}, a, { score: score, clo: clo });
}

function attemptRow(a) {
  return [a.time, a.round, a.cohort, a.seat, a.name, a.score]
    .concat(CLOS.map(c => a.clo[c].ok + "/" + a.clo[c].all));
}

function satisfactionRow(s) {
  const given = s.scores.filter(x => x !== "");
  const avg = given.length ? round1(given.reduce((a, b) => a + b, 0) / given.length) : "";
  return [s.time, s.cohort].concat(s.scores).concat([avg, s.liked, s.improve]);
}

function judge(l, settings) {
  const attend = l.sessions === "" ? "" : round1(l.sessions / settings.sessions * 100);
  const parts = [l.theory, l.practical, l.present];
  const weights = [settings.wTheory, settings.wPractical, settings.wPresent];
  const total = parts.some(p => p === "") ? "" :
    round1(parts.reduce((s, p, i) => s + p * weights[i], 0) / weights.reduce((a, b) => a + b, 0));
  let status;
  if (attend !== "" && attend < settings.minAttend) status = "ไม่ผ่าน (เวลาเรียนไม่ถึง)";
  else if (total === "") status = "รอคะแนน";
  else if (attend === "") status = "รอข้อมูลเวลาเรียน";
  else status = total >= settings.pass ? "ผ่าน" : "ไม่ผ่าน (คะแนนไม่ถึง)";
  return { attend: attend, total: total, status: status };
}

/**
 * learners: rows from the roster sheet; attempts: graded quiz attempts sorted by time;
 * sat: satisfaction responses; settings: values from the settings sheet.
 * The first attempt per round counts; later attempts stay visible in ผลแบบทดสอบ.
 */
function computeSummary(learners, attempts, sat, settings) {
  const first = {};
  attempts.forEach(a => {
    const k = a.round + "#" + keyOf(a.cohort, a.seat);
    if (!first[k]) first[k] = a;
  });

  const people = learners.map(l => Object.assign({ registered: true }, l));
  const known = new Set(people.map(l => keyOf(l.cohort, l.seat)));
  attempts.forEach(a => {
    const k = keyOf(a.cohort, a.seat);
    if (a.cohort && a.seat !== "" && !known.has(k)) {
      known.add(k);
      people.push({ registered: false, cohort: a.cohort, seat: a.seat, name: a.name, org: "",
        sessions: "", theory: "", practical: "", present: "", note: "" });
    }
  });
  people.sort((a, b) => cohortNo(a.cohort) - cohortNo(b.cohort) || a.seat - b.seat);

  const pct = (a, c) => a ? round1(a.clo[c].ok / a.clo[c].all * 100) : "";
  const rows = people.map(l => {
    const k = keyOf(l.cohort, l.seat);
    const pre = first["Pre-test#" + k], post = first["Post-test#" + k];
    const j = judge(l, settings);
    const notes = [];
    if (!l.registered) notes.push("ไม่มีในชีตผู้เรียน");
    [pre, post].forEach(a => {
      if (a && l.registered && l.name && !sameName(a.name, l.name)) notes.push(a.round + " กรอกชื่อ: " + a.name);
    });
    if (l.note) notes.push(l.note);
    return [
      l.cohort + " · " + String(l.seat).padStart(2, "0") + " · " + (l.name || "(ไม่ระบุชื่อ)"),
      l.cohort, l.seat, l.name, l.org,
      pre ? pre.score : "", post ? post.score : "", pre && post ? post.score - pre.score : ""
    ]
      .concat(CLOS.map(c => pct(pre, c)))
      .concat(CLOS.map(c => pct(post, c)))
      .concat([j.attend, l.theory, l.practical, l.present, j.total, j.status, notes.join(" · ")]);
  });

  const col = name => SUMMARY_HEAD.indexOf(name);
  const avg = xs => xs.length ? round1(xs.reduce((a, b) => a + b, 0) / xs.length) : "";
  const groups = {};
  rows.forEach(r => { (groups[r[1]] = groups[r[1]] || []).push(r); });
  sat.forEach(s => { if (s.cohort && !groups[s.cohort]) groups[s.cohort] = []; });
  const cohorts = Object.keys(groups).sort((a, b) => cohortNo(a) - cohortNo(b)).map(c => {
    const rs = groups[c];
    const pre = rs.map(r => r[col("Pre-test")]).filter(x => x !== "");
    const post = rs.map(r => r[col("Post-test")]).filter(x => x !== "");
    const gain = rs.map(r => r[col("คะแนนเพิ่มขึ้น")]).filter(x => x !== "");
    const status = rs.map(r => r[col("ผลการประเมิน")]);
    const sats = sat.filter(s => s.cohort === c).map(s => satisfactionRow(s)[2 + SATISFACTION_ITEMS.length])
      .filter(x => x !== "");
    return [c, rs.length, pre.length, post.length, avg(pre), avg(post), avg(gain),
      status.filter(s => s === "ผ่าน").length,
      status.filter(s => s.indexOf("ไม่ผ่าน") === 0).length,
      status.filter(s => s.indexOf("รอ") === 0).length,
      sats.length, avg(sats)];
  });

  return { rows: rows, cohorts: cohorts };
}
