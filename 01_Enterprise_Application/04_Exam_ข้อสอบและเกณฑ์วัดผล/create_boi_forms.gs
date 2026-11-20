/**
 * สคริปต์สร้าง Google Forms (Pre-Test + Post-Test/Final ทฤษฎี 26 ข้อ) และสรุปคะแนนลง Google Sheet อัตโนมัติ
 *
 * วิธีใช้งานครั้งแรก:
 *   1. เปิด Google Sheet -> เมนู "ส่วนขยาย (Extensions)" -> "Apps Script"
 *   2. วางโค้ดไฟล์นี้ทั้งหมด -> กดบันทึก -> เลือกฟังก์ชัน "createAllBOIForms" -> กด Run
 *
 * วิธีซ่อมชีตที่ขึ้น "พบชื่อคอลัมน์ที่ซ้ำกัน" และดึงรายชื่อ/คะแนนลง สรุปคะแนน_Audit ทันที:
 *   1. วางโค้ดนี้ทับของเดิมใน Apps Script -> กดบันทึก
 *   2. เลือกฟังก์ชัน "repairLinkedResponseSheets" -> กด Run (หรือกดจากเมนู BOI ระบบสอบ)
 */

const EXAM_DATA = {"title": "แบบทดสอบวัดผลรวม (Post-Test + สอบ Final ภาคทฤษฎี)", "subject": "การออกแบบ พัฒนา และบูรณาการแอปพลิเคชันระดับองค์กร (Enterprise Application)", "minutes": 40, "instructions": ["ข้อสอบฉบับนี้รวม Post-Test และ Final ภาคทฤษฎีไว้ในชุดเดียว รวม 26 ข้อ (50 คะแนน) ใช้เวลาประมาณ 35–40 นาที", "ตอนที่ 1 (ข้อ 1–20): วัดพัฒนาการ Post-Test (ข้อละ 1 คะแนน = 20 คะแนน เทียบคู่กับ Pre-Test)", "ตอนที่ 2 (ข้อ 21–26): ข้อสอบ Final วิเคราะห์สถานการณ์จริงตาม 6 หัวข้ออบรม (ข้อละ 5 คะแนน = 30 คะแนน)"], "preTest": [{"clo": "CLO01", "q": "ข้อใดเป็นระบบ OT (Operational Technology)", "choices": ["ระบบ ERP", "ระบบบัญชี", "อีเมลองค์กร", "PLC และ SCADA"], "answer": 3, "why": "OT คือระบบที่ควบคุมเครื่องจักรและกระบวนการผลิตโดยตรง เช่น PLC, SCADA, HMI ส่วนข้ออื่นเป็นระบบ IT"}, {"clo": "CLO01", "q": "ระบบ OT ให้ความสำคัญกับอะไรเป็นอันดับแรก", "choices": ["ความลับของข้อมูล", "ความสวยงามของหน้าจอ", "ความปลอดภัยและความพร้อมใช้งานของเครื่องจักร", "ราคาถูกที่สุด"], "answer": 2, "why": "OT เน้นความปลอดภัยและความพร้อมใช้งาน เพราะถ้าเครื่องจักรหยุดจะกระทบการผลิตและความปลอดภัยโดยตรง"}, {"clo": "CLO01", "q": "ในสถาปัตยกรรม Client-Server หน้าที่ของ Client คือข้อใด", "choices": ["แสดงผลและรับข้อมูลจากผู้ใช้", "เก็บฐานข้อมูลหลัก", "ประมวลผล Business Logic ทั้งหมด", "ควบคุมเครื่องจักรโดยตรง"], "answer": 0, "why": "Client (เช่น เว็บเบราว์เซอร์) ทำหน้าที่แสดงผลและรับคำสั่งจากผู้ใช้ ส่วน Server ทำหน้าที่ประมวลผลและจัดการข้อมูล"}, {"clo": "CLO02", "q": "JSON ข้อใดเขียนถูกต้อง", "choices": ["{name: 'Line A'}", "{\"name\": \"Line A\"}", "{'name' = 'Line A'}", "[name: \"Line A\"]"], "answer": 1, "why": "ชื่อ key และข้อความใน JSON ต้องครอบด้วยเครื่องหมายคำพูดคู่ (\") และคั่นด้วยเครื่องหมาย :"}, {"clo": "CLO02", "q": "จาก JSON {\"machine\": {\"temp\": 72}} ถ้าเก็บไว้ในตัวแปร data จะอ่านค่า 72 อย่างไร", "choices": ["data.temp", "data[temp]", "data.machine.temp", "machine.temp.data"], "answer": 2, "why": "temp อยู่ภายใน object ชื่อ machine จึงต้องเขียนอ้างอิงทีละชั้นเป็น data.machine.temp"}, {"clo": "CLO02", "q": "จาก {\"sensors\": [10, 20, 30]} ค่า data.sensors[1] คือเท่าไร", "choices": ["10", "20", "30", "undefined"], "answer": 1, "why": "ตำแหน่ง (index) ใน Array เริ่มนับจาก 0 ดังนั้น index 1 คือข้อมูลตัวที่สองซึ่งก็คือ 20"}, {"clo": "CLO02", "q": "ข้อใดคือชนิดข้อมูลทั้ง 6 ชนิดที่ JSON รองรับ", "choices": ["string, number, boolean, null, object, array", "string, number, function, date, object, array", "text, integer, undefined, function, class, list", "string, char, float, undefined, object, map"], "answer": 0, "why": "ตามสไลด์ JSON เก็บข้อมูลได้ 6 ชนิด คือ string, number, boolean, null, object และ array (ไม่เก็บ function หรือ undefined)"}, {"clo": "CLO03", "q": "แท็กใดเป็น Semantic HTML ที่บอกความหมายของโครงสร้างหน้าเว็บ", "choices": ["<header>", "<span>", "<div>", "<b>"], "answer": 0, "why": "<header> บอกความหมายว่าเป็นส่วนหัวของหน้าเว็บ ส่วน <div> และ <span> ไม่ได้บอกความหมายเชิงโครงสร้าง"}, {"clo": "CLO03", "q": "การเขียน CSS แบบใดเหมาะกับเว็บที่มีหลายหน้าและใช้สไตล์ร่วมกัน", "choices": ["Inline Style", "Internal Style", "External Style Sheet (ไฟล์ .css)", "เขียนใน JavaScript ทุกครั้ง"], "answer": 2, "why": "External Style Sheet แยกสไตล์ไว้ในไฟล์ .css กลาง ทุกหน้าเรียกใช้ร่วมกันและแก้ไขจุดเดียวได้ทั้งเว็บ"}, {"clo": "CLO03", "q": "ถ้าต้องการตัวแปรที่เปลี่ยนค่าได้ในภายหลัง ควรประกาศด้วยคำใด", "choices": ["const", "let", "static", "final"], "answer": 1, "why": "let ใช้ประกาศตัวแปรที่เปลี่ยนค่าได้ ส่วน const ใช้กับค่าคงที่ที่ไม่เปลี่ยนค่า"}, {"clo": "CLO03", "q": "ผลลัพธ์ของ '10' + 5 ใน JavaScript คือข้อใด", "choices": ["15", "'15'", "Error", "'105'"], "answer": 3, "why": "เมื่อใช้เครื่องหมาย + กับข้อความ (String) JavaScript จะนำมาต่อข้อความกัน จึงได้ '105'"}, {"clo": "CLO03", "q": "คำสั่งใดเลือก element ที่มี id=\"status\"", "choices": ["document.getElementById('status')", "document.querySelector('status')", "document.getElementsByClassName('status')", "document.select('#status')"], "answer": 0, "why": "getElementById('status') ใช้เลือก element จาก id โดยตรง ถ้าใช้ querySelector ต้องเขียน '#status'"}, {"clo": "CLO03", "q": "ถ้าต้องการให้ฟังก์ชันทำงานเมื่อผู้ใช้คลิกปุ่มบนหน้าเว็บ ต้องใช้ Event ใด", "choices": ["onload", "onclick", "onmouseover", "onkeydown"], "answer": 1, "why": "onclick ทำงานเมื่อผู้ใช้คลิกปุ่ม ส่วน onmouseover เกิดเมื่อนำเมาส์ไปวาง และ onkeydown เกิดเมื่อกดปุ่มคีย์บอร์ด"}, {"clo": "CLO04", "q": "ตามมาตรฐานสีไฟแสดงสถานะ (IEC 60204-1) สีเหลืองหมายถึงอะไร", "choices": ["เตือน / ผิดปกติ ต้องเฝ้าระวัง", "ทำงานปกติ", "หยุดฉุกเฉิน", "ออฟไลน์"], "answer": 0, "why": "ตามมาตรฐานสีอุตสาหกรรม เขียว = ปกติ, เหลือง = เตือน/ผิดปกติ, แดง = ฉุกเฉิน"}, {"clo": "CLO04", "q": "หลัก Visual Hierarchy ในการออกแบบ Dashboard หมายถึงอะไร", "choices": ["การใส่สีสันให้ครบทุกสีในหน้าเดียว", "การจัดลำดับสายตาด้วยขนาด ตำแหน่ง และสี ให้มองเห็นข้อมูลสำคัญได้ทันที", "การใส่ตัวเลขทุกตัวในโรงงานลงในตารางเดียวกัน", "การตั้งค่าให้หน้าเว็บรีเฟรชทุก 1 วินาที"], "answer": 1, "why": "Visual Hierarchy คือการจัดลำดับความสำคัญทางสายตา เพื่อให้ผู้ดูเข้าใจสถานะหลักของระบบได้ทันที"}, {"clo": "CLO05", "q": "HTTP Method ใดใช้สำหรับอ่าน/ดึงข้อมูลจาก API", "choices": ["GET", "POST", "PUT", "DELETE"], "answer": 0, "why": "GET = อ่านข้อมูล, POST = เพิ่ม/ส่งข้อมูลใหม่, PUT = แก้ไขข้อมูลเดิม, DELETE = ลบข้อมูล"}, {"clo": "CLO05", "q": "ข้อใดอธิบายความต่างระหว่างการเรียก API ปกติกับ Webhook ได้ถูกต้อง", "choices": ["API ปกติระบบต้นทางส่งมาหาเราเอง ส่วน Webhook เราต้องไปขอ", "Webhook ใช้ได้เฉพาะกับอีเมล", "ทั้งสองเหมือนกันทุกประการ", "API ปกติเราเป็นฝ่ายไปขอข้อมูล (Pull) ส่วน Webhook ระบบต้นทางส่งมาทันทีเมื่อเกิดเหตุการณ์ (Push)"], "answer": 3, "why": "Webhook ทำงานแบบ Push ส่งข้อมูลมาทันทีเมื่อเกิดเหตุการณ์ ไม่ต้องคอยส่งคำขอไปถามซ้ำ ๆ"}, {"clo": "CLO05", "q": "ในโค้ด async/await คำสั่ง const data = await res.json(); ทำหน้าที่อะไร", "choices": ["ส่งข้อมูลออกไปที่ Server", "แปลงข้อมูล JSON ที่ได้รับจาก API ให้เป็น Object ของ JavaScript", "ลบข้อมูลใน Server", "บันทึกไฟล์ JSON ลงเครื่อง"], "answer": 1, "why": "res.json() ทำหน้าที่อ่านและแปลงข้อมูล JSON จาก Response ให้เป็น Object เพื่อนำไปใช้แสดงผลต่อ และต้องใส่ await รอให้แปลงเสร็จก่อน"}, {"clo": "CLO06", "q": "Test Case ที่ดีต้องมีส่วนใดเพื่อใช้ตัดสินว่า Pass หรือ Fail", "choices": ["ชื่อผู้พัฒนา", "สีของหน้าจอ", "Expected Result (ผลลัพธ์ที่คาดหวัง)", "ราคาของระบบ"], "answer": 2, "why": "ต้องนำผลที่ได้จริง (Actual Result) มาเทียบกับผลที่คาดหวัง (Expected Result) เพื่อตัดสินว่า Pass หรือ Fail"}, {"clo": "CLO06", "q": "UAT (User Acceptance Testing) ทำโดยใคร", "choices": ["นักพัฒนาที่เขียนโค้ด", "เครื่องมือทดสอบอัตโนมัติเท่านั้น", "ผู้ดูแล Server", "ผู้ใช้งานจริงหรือลูกค้า"], "answer": 3, "why": "UAT คือขั้นตอนสุดท้ายที่ให้ผู้ใช้งานจริงทดสอบในสภาพเหมือนจริงก่อนเริ่มใช้งานจริง (Go-Live)"}], "postTest": [{"clo": "CLO01", "q": "ข้อใดเป็นอุปกรณ์หรือระบบฝั่ง OT ทั้งหมด", "choices": ["ERP, CRM และอีเมลองค์กร", "PLC, HMI และเซนเซอร์วัดอุณหภูมิ", "ฐานข้อมูลบัญชี, HMI และ ERP", "เว็บไซต์บริษัท, PLC และอีเมลองค์กร"], "answer": 1, "why": "PLC, HMI และเซนเซอร์เกี่ยวข้องกับเครื่องจักรและสายการผลิตโดยตรง จึงเป็นฝั่ง OT ทั้งหมด"}, {"clo": "CLO01", "q": "ทีม IT ต้องการรีสตาร์ตเครื่องคอมพิวเตอร์ที่คุมเครื่องจักรทันทีระหว่างกะผลิต ข้อกังวลหลักจากมุมมอง OT คือข้อใด", "choices": ["หน้าจออาจเปลี่ยนสี", "ค่าลิขสิทธิ์ซอฟต์แวร์อาจสูงขึ้น", "ข้อมูลอาจถูกส่งออกไปนอกบริษัท", "อาจทำให้เครื่องจักรหยุดชะงัก กระทบการผลิตและความปลอดภัย"], "answer": 3, "why": "ระบบ OT ให้ความสำคัญกับความปลอดภัยและความพร้อมใช้งานของเครื่องจักร การอัปเดตหรือรีสตาร์ตจึงต้องวางแผนล่วงหน้า"}, {"clo": "CLO01", "q": "ในระบบ Web Application แบบ Client-Server หน้าที่ใดทำงานอยู่ฝั่ง Server", "choices": ["รับคำขอ (Request) แล้วประมวลผลหรือส่งข้อมูล JSON กลับให้หน้าเว็บ", "การเปลี่ยนสีตัวอักษรและจัดวางหน้าจอด้วย CSS", "การแสดงค่าตัวเลขลงในหน้าเว็บเมื่อเปิดผ่านเบราว์เซอร์", "การรับเหตุการณ์เมื่อผู้ใช้คลิกปุ่มบนหน้าจอ"], "answer": 0, "why": "Server ทำหน้าที่รับ Request ประมวลผล และส่งข้อมูล JSON กลับ ส่วนการจัดหน้าจอและแสดงผลทำที่ฝั่ง Client (เบราว์เซอร์)"}, {"clo": "CLO02", "q": "JSON ข้อใดเขียนถูกต้องทั้งหมด", "choices": ["{\"line\": \"A\", \"temps\": [72.5, 73.0,]}", "{\"line\": \"A\", \"online\": True}", "{\"line\": \"A\", \"temps\": [72.5, 73.0]}", "{\"line\": \"A\", \"note\": undefined}"], "answer": 2, "why": "JSON ต้องไม่มี comma ตัวสุดท้าย, boolean ต้องเขียน true ตัวเล็กทั้งหมด และไม่มีชนิดข้อมูล undefined"}, {"clo": "CLO02", "q": "จากข้อมูล data = { \"machines\": [ { \"id\": \"M-01\", \"temp\": 72 }, { \"id\": \"M-02\", \"temp\": 65 } ] } ต้องเขียนอย่างไรจึงจะได้ค่า 65", "choices": ["data.machines.temp", "data.machines[0].temp", "data.machines[1].temp", "data.machines[2].temp"], "answer": 2, "why": "machines เป็น Array โดย M-01 อยู่ที่ index 0 และ M-02 อยู่ที่ index 1 จึงเขียนเป็น data.machines[1].temp"}, {"clo": "CLO02", "q": "จาก {\"sensors\": [10, 20, 30, 40]} ค่า data.sensors[data.sensors.length - 2] คือเท่าไร", "choices": ["20", "30", "40", "undefined"], "answer": 1, "why": "length คือ 4 ดังนั้น length - 2 คือ index 2 ซึ่งเป็นตัวที่สาม ได้ 30 (index เริ่มที่ 0)"}, {"clo": "CLO02", "q": "จาก JSON { \"line\": \"A\", \"running\": true, \"alarm\": null } ค่าของ \"running\" และ \"alarm\" เป็นชนิดข้อมูลใดตามลำดับ", "choices": ["string และ number", "boolean และ null", "boolean และ undefined", "object และ array"], "answer": 1, "why": "true เป็นชนิด boolean ส่วน null เป็นค่าว่างของ JSON"}, {"clo": "CLO03", "q": "ต้องการทำแถบเมนูลิงก์ไปหน้าต่าง ๆ ของเว็บ ควรใช้แท็ก Semantic HTML ใดครอบเมนู", "choices": ["<div class=\"menu\">", "<span>", "<footer>", "<nav>"], "answer": 3, "why": "<nav> ใช้สำหรับส่วนนำทาง/เมนูของหน้าเว็บ ส่วน <footer> คือส่วนท้ายของหน้า"}, {"clo": "CLO03", "q": "ไฟล์ style.css กำหนด p { color: blue; } แต่ในหน้าเว็บเขียน <p style=\"color: red\">ข้อความ</p> ข้อความจะเป็นสีอะไร", "choices": ["แดง เพราะ style ที่เขียนในแท็กเจาะจงกว่า", "น้ำเงิน เพราะไฟล์ CSS ภายนอกสำคัญที่สุด", "ดำ เพราะกฎขัดกันจึงใช้ค่าเริ่มต้น", "ม่วง เพราะสีผสมกัน"], "answer": 0, "why": "Inline style ที่เขียนในแท็กมีลำดับความสำคัญสูงกว่า Selector ในไฟล์ CSS ภายนอก"}, {"clo": "CLO03", "q": "โค้ด JavaScript ข้อใดทำงานได้โดยไม่เกิด Error", "choices": ["const max = 240; max = 250;", "const list; list = [];", "let count = 0; count = count + 1;", "let x = 1; let x = 2;"], "answer": 2, "why": "let สามารถกำหนดค่าใหม่ได้ ส่วน const เปลี่ยนค่าไม่ได้และต้องใส่ค่าเริ่มต้นทันที และห้ามประกาศ let ชื่อซ้ำในขอบเขตเดียวกัน"}, {"clo": "CLO03", "q": "จากโค้ด let a = 12; let b = 5; console.log(2 * (a - b)); ผลลัพธ์คือข้อใด", "choices": ["19", "14", "12", "7"], "answer": 1, "why": "คำนวณในวงเล็บก่อน: 12 - 5 ได้ 7 แล้วนำไปคูณ 2 ได้ผลลัพธ์ 14"}, {"clo": "CLO03", "q": "ข้อใดเลือก element เดียวกับ document.getElementById('status')", "choices": ["document.querySelector('.status')", "document.querySelector('status')", "document.getElementsByClassName('status')", "document.querySelector('#status')"], "answer": 3, "why": "querySelector ใช้ CSS Selector จึงต้องใส่เครื่องหมาย # นำหน้าชื่อ id ส่วนเครื่องหมาย . ใช้กับ class"}, {"clo": "CLO03", "q": "เมื่อผู้ใช้นำเมาส์ไปวางบนข้อความหรือกล่องบนหน้าเว็บ (โดยยังไม่ได้กดคลิก) จะเกิด Event ใด", "choices": ["onmouseover", "onmousedown", "onmouseup", "onclick"], "answer": 0, "why": "onmouseover เกิดขึ้นทันทีเมื่อนำเมาส์ไปวางบน element ก่อนที่จะกดคลิก (onmousedown) และปล่อยเมาส์ (onmouseup)"}, {"clo": "CLO04", "q": "ตามมาตรฐาน IEC 60204-1 ไฟแสดงสถานะสีใดหมายถึง \"ต้องให้ผู้ปฏิบัติงานดำเนินการ\"", "choices": ["เขียว", "เหลือง", "น้ำเงิน", "ขาว"], "answer": 2, "why": "ตามมาตรฐาน IEC 60204-1 สีน้ำเงินหมายถึงต้องให้ผู้ปฏิบัติงานดำเนินการ"}, {"clo": "CLO04", "q": "เมื่อพนักงานกดปุ่ม \"ส่งแจ้งเตือน\" หรือ \"ลบข้อมูล\" บนหน้าจอโรงงาน การออกแบบ UI ที่ดีเพื่อป้องกันความผิดพลาดควรทำอย่างไร", "choices": ["ซ่อนปุ่มให้เล็กที่สุดจะได้ไม่เผลอกด", "แสดงกล่องยืนยัน (Confirm) หรือแจ้งผลลัพธ์ชัดเจนและปิดปุ่มชั่วคราวกันกดซ้ำ", "ปล่อยให้กดซ้ำได้ไม่จำกัดโดยไม่ต้องแสดงข้อความใดๆ", "ให้ระบบลบข้อมูลทันทีโดยไม่ต้องตรวจเงื่อนไข"], "answer": 1, "why": "หลัก Error Prevention และ Feedback ต้องมีข้อความยืนยันหรือแจ้งสถานะให้ผู้ใช้เห็นชัดเจนและป้องกันการกดพลาดซ้ำ"}, {"clo": "CLO05", "q": "เมื่อต้องการ \"ส่งข้อมูลใหม่\" หรือส่งข้อความแจ้งเตือนไปยัง Webhook API ของ Server ควรใช้ HTTP Method ใด", "choices": ["GET", "POST", "DELETE", "HEAD"], "answer": 1, "why": "GET ใช้ดึง/อ่านข้อมูล ส่วน POST ใช้ส่งข้อมูลใหม่หรือส่งแจ้งเตือนไปยัง Server"}, {"clo": "CLO05", "q": "หากโรงงานต้องการให้ระบบส่งข้อความแจ้งเตือนทันทีที่เครื่องจักรหยุด โดยหน้าเว็บไม่ต้องคอยเรียก API ถามซ้ำ ๆ ทุก 5 วินาที ควรใช้กลไกใด", "choices": ["Webhook (Push Notification)", "HTML CSS Flexbox", "Local File เปิดผ่าน file://", "Manual Refresh กด F5 เอง"], "answer": 0, "why": "Webhook จะผลัก (Push) ข้อมูลมาทันทีเมื่อเกิดเหตุการณ์สำคัญ โดยไม่ต้องคอยดึงข้อมูลซ้ำ"}, {"clo": "CLO05", "q": "ข้อใดเรียงลำดับการดึงข้อมูลด้วย fetch แบบ async/await ได้ถูกต้อง", "choices": ["await res.json() › เรียก fetch › ตรวจ res.ok › แสดงผล", "เรียก fetch › ตรวจ res.ok › แปลงด้วย await res.json() › แสดงผล", "เรียก fetch › แสดงผล › ตรวจ res.ok", "ตรวจ res.ok › เรียก fetch › await res.json() › แสดงผล"], "answer": 1, "why": "ต้องเรียก fetch เพื่อรับ Response ก่อน จากนั้นเช็ก res.ok แล้วค่อย await res.json() แปลงเป็น Object ก่อนนำไปแสดงผล"}, {"clo": "CLO06", "q": "Test Case ใดเขียนผลลัพธ์ที่คาดหวัง (Expected Result) ได้ชัดเจนและตรวจวัดได้จริงที่สุด", "choices": ["ระบบทำงานถูกต้อง", "หน้าจอแสดงผลสวยงาม", "เมื่อแรงดันเป็น 245 V หน้าจอแสดงคำเตือน \"แรงดันเกิน 240 V\" และเปลี่ยนป้ายเป็นสีแดง", "ไม่พบข้อผิดพลาด"], "answer": 2, "why": "Expected Result ที่ดีต้องระบุผลลัพธ์ที่เห็นและตรวจวัดได้ชัดเจน เพื่อให้ผู้ทดสอบตัดสิน Pass/Fail ได้ตรงกัน"}, {"clo": "CLO06", "q": "จุดประสงค์หลักของการทำ UAT (User Acceptance Testing) คือข้อใด", "choices": ["ให้ผู้เขียนโปรแกรมตรวจ syntax ของโค้ด", "ให้ผู้ใช้งานจริงทดสอบระบบในสภาพเหมือนจริง เพื่อยืนยันว่าใช้งานได้ตรงความต้องการก่อน Go-Live", "ออกแบบสีของหน้าเว็บให้สวยงามก่อนเขียนโค้ด", "ติดตั้งฐานข้อมูลและ Server ใหม่"], "answer": 1, "why": "UAT คือการให้ผู้ใช้งานจริงทดสอบและลงชื่อยอมรับระบบก่อนนำไปใช้งานจริง"}], "finalSection": [{"auditCol": "I", "auditLabel": "สถาปัตยกรรมระบบ OT / IT และ Enterprise App", "clo": "CLO01", "points": 5, "q": "ในระบบตรวจวัดเครื่องจักร (Electrical Meter) ของห้องเรียน ผู้สอนรันโปรแกรม Python (API Server) บนเครื่องผู้สอน ส่วนผู้เรียนเปิดหน้าเว็บ index.html บนเบราว์เซอร์เครื่องตนเอง ข้อใดอธิบายบทบาทของทั้งสองฝั่งได้ถูกต้อง", "choices": ["เบราว์เซอร์ของผู้เรียนทำหน้าที่เป็น Server ส่วนโปรแกรม Python เป็น Client", "โปรแกรม Python ทำหน้าที่เป็น Server คอยจ่ายข้อมูล JSON ผ่าน API ส่วนเบราว์เซอร์ของผู้เรียนเป็น Client ที่ดึงข้อมูลมาคำนวณและแสดงผล", "ทั้งสองฝั่งทำงานในฐานข้อมูลเดียวกันโดยตรงโดยไม่ต้องผ่าน HTTP", "ระบบแบบนี้เป็นฝั่ง OT ทั้งหมดเพราะมีการวัดค่าแรงดันไฟฟ้า"], "answer": 1, "why": "API Server ของผู้สอนคือฝั่ง Server ที่ให้บริการข้อมูล JSON ส่วนหน้าเว็บ HTML/JS ในเบราว์เซอร์ของผู้เรียนคือ Client ที่เรียก fetch ไปดึงข้อมูลมาแสดงผล"}, {"auditCol": "J", "auditLabel": "โครงสร้างหน้าเว็บ HTML5 และการจัดวาง CSS Flexbox", "clo": "CLO03, CLO04", "points": 5, "q": "หน้าจอ Dashboard มีกล่องครอบการ์ด <section class=\"cards\"> ที่มีการ์ด 3 ใบ (Voltage, Current, Water Flow) ต้องการให้การ์ดเรียงเป็นแถวแนวนอน มีช่องว่าง 16px และปัดขึ้นแถวใหม่ได้เมื่อเปิดบนหน้าจอแคบ ควรใช้ CSS ใดกับ .cards", "choices": ["display: block; margin: 16px;", "position: fixed; width: 100%;", "display: flex; flex-wrap: wrap; gap: 16px;", "text-align: center; font-size: 16px;"], "answer": 2, "why": "display: flex จัดเรียงลูกในแนวนอน, flex-wrap: wrap ให้ขึ้นแถวใหม่เมื่อจอแคบ และ gap: 16px กำหนดระยะห่างระหว่างการ์ด"}, {"auditCol": "K", "auditLabel": "การเขียนโปรแกรม JavaScript ฟังก์ชัน และการจัดการ DOM", "clo": "CLO03", "points": 5, "q": "พิจารณาโค้ดต่อไปนี้:\nconst MAX_VOLT = 240;\nfunction checkVolt(v) {\n  if (v > MAX_VOLT) {\n    return 'อันตราย';\n  } else if (v >= 235) {\n    return 'เฝ้าระวัง';\n  } else {\n    return 'ปกติ';\n  }\n}\ndocument.getElementById('status').textContent = checkVolt(240);\nผลลัพธ์ที่แสดงใน #status คือข้อใด", "choices": ["อันตราย", "เฝ้าระวัง", "ปกติ", "เกิด Error"], "answer": 1, "why": "240 > 240 เป็นเท็จ จึงลงมาเช็กเงื่อนไข else if (240 >= 235) ซึ่งเป็นจริง และคืนค่า 'เฝ้าระวัง' ไปแสดงใน #status"}, {"auditCol": "L", "auditLabel": "โครงสร้างข้อมูล JSON และการสื่อสาร REST API", "clo": "CLO02, CLO05", "points": 5, "q": "API ตอบกลับ JSON ดังนี้:\n{ \"line\": \"A\", \"electric\": { \"voltage\": 248.5, \"current\": 16.2 }, \"water\": { \"flow\": 3.1 } }\nหลังแปลงเป็นตัวแปร data ด้วย const data = await res.json(); แล้ว หากต้องการอ่านค่าอัตราการไหลของน้ำ (3.1) ต้องเขียนอย่างไร", "choices": ["data.flow", "data.electric.flow", "data.water.flow", "data[0].water.flow"], "answer": 2, "why": "ไล่ตามโครงสร้าง Object ทีละชั้น: data -> water -> flow จึงเขียนเป็น data.water.flow"}, {"auditCol": "M", "auditLabel": "การรับ-ส่งข้อมูลและระบบแจ้งเตือน Webhook", "clo": "CLO05", "points": 5, "q": "เมื่อตรวจสอบพบว่าค่าแรงดันเกินเกณฑ์ ต้องการส่ง JSON { sender, title, message } ไปแจ้งเตือนที่ Webhook URL ของผู้สอนด้วย fetch ข้อใดตั้งค่าถูกต้องที่สุด", "choices": ["fetch(WEBHOOK_URL, { method: 'GET', body: { sender, title, message } })", "fetch(WEBHOOK_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sender, title, message }) })", "fetch(WEBHOOK_URL, { method: 'POST', body: '{ sender, title, message }' })", "fetch(WEBHOOK_URL, { method: 'PUT', headers: { 'Content-Type': 'text/plain' } })"], "answer": 1, "why": "การส่งข้อมูลเข้า Webhook ต้องใช้ method: 'POST', ระบุ header 'Content-Type': 'application/json' และแปลง Object เป็นข้อความ JSON ด้วย JSON.stringify(...)"}, {"auditCol": "N", "auditLabel": "ความมั่นคงปลอดภัยไซเบอร์ (Security) และการทำ UAT", "clo": "CLO04, CLO06", "points": 5, "q": "ข้อใดปฏิบัติได้ถูกต้องตามหลักความปลอดภัย (ป้องกัน XSS) และการจัดทำ Test Case ก่อนส่งมอบระบบ", "choices": ["ใช้ .innerHTML แสดงข้อความที่ผู้ใช้กรอก เพราะทำงานเร็วกว่า .textContent", "ใช้ .textContent แสดงข้อความจากผู้ใช้ และเขียน Test Case ระบุข้อมูลทดสอบกับผลที่คาดหวัง (Expected Result) ให้ชัดเจน", "เก็บ User และ Password ไว้ในไฟล์ JavaScript ฝั่งหน้าเว็บเพื่อให้ผู้เรียนดูง่าย", "ข้ามขั้นตอน UAT ไปใช้งานจริงทันทีหากเขียนโค้ดเสร็จแล้ว"], "answer": 1, "why": "การแสดงข้อความจากผู้ใช้ต้องใช้ .textContent เพื่อป้องกันการฝังโค้ดอันตราย (XSS) และการทดสอบที่ดีต้องเขียน Test Case ที่มี Expected Result ชัดเจน"}]};
const COHORTS = ["รุ่นที่ 1", "รุ่นที่ 2", "รุ่นที่ 3", "รุ่นที่ 4", "รุ่นที่ 5", "รุ่นที่ 6", "รุ่นที่ 7", "รุ่นที่ 8", "รุ่นที่ 9", "รุ่นที่ 10", "รุ่นที่ 11", "รุ่นที่ 12", "รุ่นที่ 13", "รุ่นที่ 14", "รุ่นที่ 15", "รุ่นที่ 16", "รุ่นที่ 17", "รุ่นที่ 18", "รุ่นที่ 19"];

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("BOI ระบบสอบ")
    .addItem("🔄 อัปเดตสรุปคะแนน Audit", "updateAuditSummary")
    .addItem("🧹 ซ่อมคอลัมน์ซ้ำในชีตคำตอบ + อัปเดต Audit", "repairLinkedResponseSheets")
    .addItem("📝 อัปเดตคำถามในฟอร์มเดิม (ไม่เพิ่มคอลัมน์ซ้ำ)", "updateExistingFormsQuestions")
    .addToUi();
}

function addIdentityItems_(form) {
  const seats = Array.from({ length: 20 }, (_, i) => String(i + 1));
  const c = form.addListItem().setTitle("รุ่นที่เข้าอบรม").setChoiceValues(COHORTS).setRequired(true);
  const s = form.addListItem().setTitle("เลขที่ (ตามใบรายชื่อ)").setChoiceValues(seats).setRequired(true);
  const n = form.addTextItem().setTitle("ชื่อ - นามสกุล").setRequired(true);
  const d = form.addTextItem().setTitle("สังกัด / บริษัท").setRequired(false);
  return { cohortId: c.getId(), seatId: s.getId(), nameId: n.getId(), deptId: d.getId() };
}

function findIdentityItems_(form) {
  const ids = {};
  form.getItems().forEach(it => {
    const type = it.getType();
    if (type !== FormApp.ItemType.LIST && type !== FormApp.ItemType.TEXT) return;
    const t = String(it.getTitle() || "");
    if (/^\d+\./.test(t)) return;
    if (!ids.cohortId && t.indexOf("รุ่น") >= 0) ids.cohortId = it.getId();
    else if (!ids.seatId && t.indexOf("เลขที่") >= 0) ids.seatId = it.getId();
    else if (!ids.nameId && t.indexOf("ชื่อ") >= 0) ids.nameId = it.getId();
    else if (!ids.deptId && (t.indexOf("สังกัด") >= 0 || t.indexOf("บริษัท") >= 0)) ids.deptId = it.getId();
  });
  return ids;
}

function applyMcqConfig_(mcItem, q, startNo, idx, defaultPoints) {
  const pts = q.points || defaultPoints;
  const titlePrefix = (startNo + idx) + ". ";
  const label = q.auditLabel ? titlePrefix + "[" + q.auditLabel + "]\n" + q.q : titlePrefix + q.q;
  const choices = q.choices.map((c, cIdx) => mcItem.createChoice(c, cIdx === q.answer));
  mcItem.setTitle(label)
    .setChoices(choices)
    .setPoints(pts)
    .setRequired(true);
  if (q.why) {
    const fb = FormApp.createFeedback().setText(q.why).build();
    mcItem.setFeedbackForCorrect(fb);
    mcItem.setFeedbackForIncorrect(fb);
  }
}

function addMcqList_(form, list, startNo, defaultPoints) {
  list.forEach((q, idx) => {
    const item = form.addMultipleChoiceItem();
    applyMcqConfig_(item, q, startNo, idx, defaultPoints);
  });
}

function extractFormIdFromEditUrl_(url) {
  const m = String(url || "").match(/\/forms\/d\/([a-zA-Z0-9_-]+)/);
  if (!m || m[1] === "e") return "";
  return m[1];
}

function getFormsConfig_(ssOpt) {
  const ss = ssOpt || SpreadsheetApp.getActiveSpreadsheet();
  const props = PropertiesService.getScriptProperties();
  const rawCfg = props.getProperty("BOI_FORMS_CFG");
  let cfg = rawCfg ? JSON.parse(rawCfg) : {};
  if (ss) cfg.spreadsheetId = ss.getId();

  const needsPre = !cfg.pre || !cfg.pre.id;
  const needsPost = !cfg.postFinal || !cfg.postFinal.id;
  if ((needsPre || needsPost) && ss) {
    const linkSheet = ss.getSheetByName("ลิงก์ข้อสอบทุกรุ่น");
    if (linkSheet && linkSheet.getLastRow() >= 3) {
      const vals = linkSheet.getRange(2, 1, linkSheet.getLastRow() - 1, 3).getValues();
      vals.forEach(row => {
        const label = String(row[0] || "");
        const editId = extractFormIdFromEditUrl_(row[2]);
        if (!editId) return;
        if (label.indexOf("Pre-Test") >= 0 && (!cfg.pre || !cfg.pre.id)) {
          const f = FormApp.openById(editId);
          cfg.pre = { id: f.getId(), url: f.getPublishedUrl(), edit: f.getEditUrl(), items: findIdentityItems_(f) };
        } else if (label.indexOf("Post-Test") >= 0 && (!cfg.postFinal || !cfg.postFinal.id)) {
          const f = FormApp.openById(editId);
          cfg.postFinal = { id: f.getId(), url: f.getPublishedUrl(), edit: f.getEditUrl(), items: findIdentityItems_(f) };
        }
      });
    }
    if (!cfg.pre || !cfg.pre.id || !cfg.postFinal || !cfg.postFinal.id) {
      ss.getSheets().forEach(sh => {
        const fUrl = sh.getFormUrl();
        if (!fUrl) return;
        try {
          const f = FormApp.openByUrl(fUrl);
          const fTitle = String(f.getTitle() || "");
          const mcCount = f.getItems(FormApp.ItemType.MULTIPLE_CHOICE).length;
          if ((fTitle.indexOf("Pre-Test") >= 0 || mcCount === 20) && (!cfg.pre || !cfg.pre.id)) {
            cfg.pre = { id: f.getId(), url: f.getPublishedUrl(), edit: f.getEditUrl(), items: findIdentityItems_(f) };
          } else if ((fTitle.indexOf("Post-Test") >= 0 || mcCount >= 26) && (!cfg.postFinal || !cfg.postFinal.id)) {
            cfg.postFinal = { id: f.getId(), url: f.getPublishedUrl(), edit: f.getEditUrl(), items: findIdentityItems_(f) };
          }
        } catch (e) {}
      });
    }
    if (cfg.pre && cfg.pre.id && cfg.postFinal && cfg.postFinal.id) {
      props.setProperty("BOI_FORMS_CFG", JSON.stringify(cfg));
    }
  }
  return cfg;
}

function ensureSubmitTrigger_(ss) {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === "updateAuditSummary") {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger("updateAuditSummary").forSpreadsheet(ss).onFormSubmit().create();
}

function relinkFormDestinationClean_(form, ss) {
  const pubUrl = form.getPublishedUrl();
  const editUrl = form.getEditUrl();
  const formId = form.getId();
  const stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone() || "Asia/Bangkok", "HHmmss");

  const linkedSheets = ss.getSheets().filter(sh => {
    const fUrl = sh.getFormUrl();
    if (!fUrl) return false;
    return fUrl === pubUrl || fUrl === editUrl || fUrl.indexOf(formId) >= 0;
  });

  try {
    form.removeDestination();
  } catch (e) {}

  linkedSheets.forEach(sh => {
    const backupName = ("สำรอง_" + sh.getName() + "_" + stamp).slice(0, 90);
    sh.setName(backupName);
  });
  SpreadsheetApp.flush();

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
}

function createAllBOIForms() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error("กรุณารันสคริปต์นี้จากภายใน Google Sheet (เมนู ส่วนขยาย -> Apps Script) ครับ");
  }

  // 1. สร้างฟอร์ม Pre-Test (20 ข้อ · 20 คะแนน)
  const preForm = FormApp.create("Pre-Test · วิชา Enterprise Application (BOI)")
    .setDescription("แบบทดสอบก่อนเรียน 20 ข้อ (ข้อละ 1 คะแนน) ใช้เวลาประมาณ 15 นาที\nเลือกรุ่นและเลขที่ให้ตรงกับใบรายชื่อที่ผู้สอนแจก")
    .setIsQuiz(true)
    .setCollectEmail(false)
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage("ส่งคำตอบ Pre-Test เรียบร้อยแล้ว ขอบคุณครับ");
  const preIds = addIdentityItems_(preForm);
  preForm.addPageBreakItem().setTitle("ตอนที่ 1: แบบทดสอบก่อนเรียน (20 ข้อ · 20 คะแนน)");
  addMcqList_(preForm, EXAM_DATA.preTest, 1, 1);

  // 2. สร้างฟอร์ม Post-Test + Final ภาคทฤษฎี ฉบับรวม (26 ข้อ · 50 คะแนน)
  const postFinalForm = FormApp.create("Post-Test + สอบ Final ทฤษฎี (รวม 26 ข้อ) · วิชา Enterprise Application (BOI)")
    .setDescription(EXAM_DATA.instructions.join("\n"))
    .setIsQuiz(true)
    .setCollectEmail(false)
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage("ส่งข้อสอบ Post-Test + Final ทฤษฎี เรียบร้อยแล้วครับ");
  const postIds = addIdentityItems_(postFinalForm);
  postFinalForm.addPageBreakItem()
    .setTitle("ตอนที่ 1: Post-Test วัดพัฒนาการ (20 ข้อ · 20 คะแนน)")
    .setHelpText("ข้อละ 1 คะแนน เทียบพัฒนาการกับ Pre-Test");
  addMcqList_(postFinalForm, EXAM_DATA.postTest, 1, 1);

  postFinalForm.addPageBreakItem()
    .setTitle("ตอนที่ 2: ข้อสอบ Final วิเคราะห์สถานการณ์ 6 หัวข้อ (6 ข้อ · 30 คะแนน)")
    .setHelpText("ข้อละ 5 คะแนน ตรงตาม 6 หัวข้อในใบสรุปคะแนน Audit");
  addMcqList_(postFinalForm, EXAM_DATA.finalSection, 21, 5);

  preForm.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  postFinalForm.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  const cfg = {
    spreadsheetId: ss.getId(),
    pre: { id: preForm.getId(), url: preForm.getPublishedUrl(), edit: preForm.getEditUrl(), items: preIds },
    postFinal: { id: postFinalForm.getId(), url: postFinalForm.getPublishedUrl(), edit: postFinalForm.getEditUrl(), items: postIds }
  };
  PropertiesService.getScriptProperties().setProperty("BOI_FORMS_CFG", JSON.stringify(cfg));

  ensureSubmitTrigger_(ss);

  let linkSheet = ss.getSheetByName("ลิงก์ข้อสอบทุกรุ่น");
  if (!linkSheet) linkSheet = ss.insertSheet("ลิงก์ข้อสอบทุกรุ่น", 0);
  linkSheet.clear();
  const rows = [
    ["รายการ", "ลิงก์สำหรับผู้เรียน (ส่งในห้อง / ทำ QR)", "ลิงก์สำหรับผู้สอนแก้ไข / เปิดดูคะแนนทันที"],
    ["1. Pre-Test (20 ข้อ · 20 คะแนน)", preForm.getPublishedUrl(), preForm.getEditUrl()],
    ["2. Post-Test + Final ทฤษฎี (26 ข้อ · 50 คะแนน)", postFinalForm.getPublishedUrl(), postFinalForm.getEditUrl()]
  ];
  linkSheet.getRange(1, 1, rows.length, 3).setValues(rows);
  linkSheet.getRange(1, 1, 1, 3).setFontWeight("bold");
  linkSheet.setColumnWidth(1, 310);
  linkSheet.setColumnWidth(2, 460);
  linkSheet.setColumnWidth(3, 460);

  updateAuditSummary();

  const resultJson = {
    subject: "App (Application Development & IoT)",
    updatedAt: new Date().toISOString().slice(0, 10),
    forms: [
      {
        key: "pre_test",
        title: "Pre-Test (ก่อนเรียน)",
        when: "วันที่ 1 · 09:15",
        note: "20 ข้อ (20 คะแนน) ประมาณ 15 นาที",
        url: preForm.getPublishedUrl(),
        editUrl: preForm.getEditUrl()
      },
      {
        key: "post_final",
        title: "Post-Test + Final ทฤษฎี (ฉบับรวม)",
        when: "วันที่ 4 · ช่วงสอบทฤษฎี",
        note: "26 ข้อ (ตอน 1: 20 คะแนน + ตอน 2: 30 คะแนน) ประมาณ 35–40 นาที",
        url: postFinalForm.getPublishedUrl(),
        editUrl: postFinalForm.getEditUrl()
      }
    ]
  };

  Logger.log("=== สร้าง Google Forms สำเร็จ! คัดลอก JSON ด้านล่างไปวางใน form_links.json ได้เลย ===");
  Logger.log(JSON.stringify(resultJson, null, 2));
}

function updateExistingFormsQuestions() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const cfg = getFormsConfig_(ss);
  if (!cfg.pre || !cfg.pre.id || !cfg.postFinal || !cfg.postFinal.id) {
    throw new Error("ยังไม่พบการตั้งค่าเดิม กรุณารัน createAllBOIForms ก่อนครับ");
  }
  const activeSs = ss || SpreadsheetApp.openById(cfg.spreadsheetId);
  const preForm = FormApp.openById(cfg.pre.id);
  const postForm = FormApp.openById(cfg.postFinal.id);

  function clearAllItems(form) {
    const items = form.getItems();
    for (let i = items.length - 1; i >= 0; i--) {
      form.deleteItem(items[i]);
    }
  }

  function tryUpdateInPlace(form, specs) {
    const existingIds = findIdentityItems_(form);
    const mcItems = form.getItems(FormApp.ItemType.MULTIPLE_CHOICE);
    const totalExpected = specs.reduce((acc, s) => acc + s.list.length, 0);
    if (existingIds.cohortId && existingIds.seatId && existingIds.nameId && mcItems.length === totalExpected) {
      form.setIsQuiz(true);
      let cursor = 0;
      specs.forEach(s => {
        s.list.forEach((q, idx) => {
          applyMcqConfig_(mcItems[cursor].asMultipleChoiceItem(), q, s.startNo, idx, s.defaultPoints);
          cursor++;
        });
      });
      return existingIds;
    }
    return null;
  }

  const preInPlace = tryUpdateInPlace(preForm, [{ list: EXAM_DATA.preTest, startNo: 1, defaultPoints: 1 }]);
  if (preInPlace) {
    cfg.pre.items = preInPlace;
  } else {
    if (preForm.getResponses().length > 0) {
      throw new Error("จำนวนข้อ Pre-Test เปลี่ยนแปลงแต่ยังมีคำตอบค้างอยู่ กรุณาลบคำตอบก่อนครับ");
    }
    clearAllItems(preForm);
    preForm.setIsQuiz(true);
    cfg.pre.items = addIdentityItems_(preForm);
    preForm.addPageBreakItem().setTitle("ตอนที่ 1: แบบทดสอบก่อนเรียน (20 ข้อ · 20 คะแนน)");
    addMcqList_(preForm, EXAM_DATA.preTest, 1, 1);
    relinkFormDestinationClean_(preForm, activeSs);
  }

  const postInPlace = tryUpdateInPlace(postForm, [
    { list: EXAM_DATA.postTest, startNo: 1, defaultPoints: 1 },
    { list: EXAM_DATA.finalSection, startNo: 21, defaultPoints: 5 }
  ]);
  if (postInPlace) {
    postForm.setDescription(EXAM_DATA.instructions.join("\n"));
    cfg.postFinal.items = postInPlace;
  } else {
    if (postForm.getResponses().length > 0) {
      throw new Error("จำนวนข้อ Post+Final เปลี่ยนแปลงแต่ยังมีคำตอบค้างอยู่ กรุณาลบคำตอบก่อนครับ");
    }
    clearAllItems(postForm);
    postForm.setIsQuiz(true);
    postForm.setDescription(EXAM_DATA.instructions.join("\n"));
    cfg.postFinal.items = addIdentityItems_(postForm);
    postForm.addPageBreakItem()
      .setTitle("ตอนที่ 1: Post-Test วัดพัฒนาการ (20 ข้อ · 20 คะแนน)")
      .setHelpText("ข้อละ 1 คะแนน เทียบพัฒนาการกับ Pre-Test");
    addMcqList_(postForm, EXAM_DATA.postTest, 1, 1);
    postForm.addPageBreakItem()
      .setTitle("ตอนที่ 2: ข้อสอบ Final วิเคราะห์สถานการณ์ 6 หัวข้อ (6 ข้อ · 30 คะแนน)")
      .setHelpText("ข้อละ 5 คะแนน ตรงตาม 6 หัวข้อในใบสรุปคะแนน Audit");
    addMcqList_(postForm, EXAM_DATA.finalSection, 21, 5);
    relinkFormDestinationClean_(postForm, activeSs);
  }

  PropertiesService.getScriptProperties().setProperty("BOI_FORMS_CFG", JSON.stringify(cfg));
  ensureSubmitTrigger_(activeSs);
  updateAuditSummary();
  Logger.log("อัปเดตคำถามลงใน Google Forms เดิมสำเร็จแล้ว (ไม่สร้างคอลัมน์ซ้ำ!)");
}

function repairLinkedResponseSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const cfg = getFormsConfig_(ss);
  if (!cfg.pre || !cfg.pre.id || !cfg.postFinal || !cfg.postFinal.id) {
    throw new Error("ไม่พบลิงก์ Google Forms ในชีต ลิงก์ข้อสอบทุกรุ่น หรือ ScriptProperties");
  }
  const activeSs = ss || SpreadsheetApp.openById(cfg.spreadsheetId);
  const preForm = FormApp.openById(cfg.pre.id);
  const postForm = FormApp.openById(cfg.postFinal.id);

  relinkFormDestinationClean_(preForm, activeSs);
  relinkFormDestinationClean_(postForm, activeSs);

  cfg.pre.items = findIdentityItems_(preForm);
  cfg.postFinal.items = findIdentityItems_(postForm);
  PropertiesService.getScriptProperties().setProperty("BOI_FORMS_CFG", JSON.stringify(cfg));

  ensureSubmitTrigger_(activeSs);
  updateAuditSummary();

  const msg = "ซ่อมชีตคำตอบทั้ง 2 ฟอร์มเรียบร้อย (ชีตเดิมถูกเก็บเป็นชีตสำรองไว้ให้แล้ว) และดึงข้อมูลเข้า สรุปคะแนน_Audit ครบแล้วครับ";
  Logger.log(msg);
  try {
    SpreadsheetApp.getUi().alert(msg);
  } catch (e) {}
}

function updateAuditSummary() {
  const ssOpt = SpreadsheetApp.getActiveSpreadsheet();
  const cfg = getFormsConfig_(ssOpt);
  if (!cfg || !cfg.pre || !cfg.pre.id || !cfg.postFinal || !cfg.postFinal.id) return;
  const ss = ssOpt || SpreadsheetApp.openById(cfg.spreadsheetId);

  const records = {};
  function normalizeSeatKey_(seat) {
    const raw = String(seat || "").trim();
    const num = Number(raw);
    return !isNaN(num) && raw !== "" ? String(num).padStart(2, "0") : raw;
  }

  function readIdentity_(resp, savedItems) {
    const all = resp.getItemResponses();
    const byId = {};
    const byKind = { cohort: "", seat: "", name: "", dept: "" };
    all.forEach(r => {
      const it = r.getItem();
      const val = r.getResponse();
      byId[it.getId()] = val;
      const type = it.getType();
      if (type !== FormApp.ItemType.LIST && type !== FormApp.ItemType.TEXT) return;
      const title = String(it.getTitle() || "");
      if (/^\d+\./.test(title)) return;
      if (!byKind.cohort && title.indexOf("รุ่น") >= 0) byKind.cohort = val;
      else if (!byKind.seat && title.indexOf("เลขที่") >= 0) byKind.seat = val;
      else if (!byKind.name && title.indexOf("ชื่อ") >= 0) byKind.name = val;
      else if (!byKind.dept && (title.indexOf("สังกัด") >= 0 || title.indexOf("บริษัท") >= 0)) byKind.dept = val;
    });

    const ids = savedItems || {};
    const cohort = String(byId[ids.cohortId] || byKind.cohort || "").trim();
    const seat = String(byId[ids.seatId] || byKind.seat || "").trim();
    const name = String(byId[ids.nameId] || byKind.name || "").trim();
    const dept = String(byId[ids.deptId] || byKind.dept || "").trim();
    if (!cohort && !seat && !name) return null;

    const seatKey = normalizeSeatKey_(seat);
    const key = (cohort || "-") + "|" + (seatKey || name);
    if (!records[key]) {
      records[key] = {
        cohort: cohort,
        seat: Number(seat) || seat,
        name: name,
        dept: dept,
        pre: "", post: "", f1: "", f2: "", f3: "", f4: "", f5: "", f6: "", finalSum: ""
      };
    }
    if (name) records[key].name = name;
    if (dept) records[key].dept = dept;
    return records[key];
  }

  const preResponses = FormApp.openById(cfg.pre.id).getResponses()
    .slice()
    .sort((a, b) => a.getTimestamp() - b.getTimestamp());
  preResponses.forEach(resp => {
    const gradables = resp.getGradableItemResponses();
    if (gradables.length === 0) return;
    const rec = readIdentity_(resp, cfg.pre.items);
    if (!rec) return;
    let sum = 0;
    gradables.forEach(ir => { sum += Number(ir.getScore() || 0); });
    rec.pre = sum;
  });

  const postResponses = FormApp.openById(cfg.postFinal.id).getResponses()
    .slice()
    .sort((a, b) => a.getTimestamp() - b.getTimestamp());
  postResponses.forEach(resp => {
    const gradables = resp.getGradableItemResponses();
    if (gradables.length === 0) return;
    const rec = readIdentity_(resp, cfg.postFinal.items);
    if (!rec) return;

    let postSum = 0;
    const fScores = [0, 0, 0, 0, 0, 0];
    gradables.forEach((ir, idx) => {
      const score = Number(ir.getScore() || 0);
      const m = String(ir.getItem().getTitle() || "").match(/^(\d+)\./);
      const qNo = m ? Number(m[1]) : (idx + 1);
      if (qNo >= 1 && qNo <= 20) {
        postSum += score;
      } else if (qNo >= 21 && qNo <= 26) {
        fScores[qNo - 21] = score;
      }
    });

    rec.post = postSum;
    rec.f1 = fScores[0]; rec.f2 = fScores[1]; rec.f3 = fScores[2];
    rec.f4 = fScores[3]; rec.f5 = fScores[4]; rec.f6 = fScores[5];
    rec.finalSum = fScores.reduce((a, b) => a + b, 0);
  });

  let outSheet = ss.getSheetByName("สรุปคะแนน_Audit");
  if (!outSheet) outSheet = ss.insertSheet("สรุปคะแนน_Audit", 1);
  outSheet.clear();

  const header = [
    "รุ่น", "เลขที่", "ชื่อ-นามสกุล", "สังกัด",
    "Pre-Test (20)", "Post-Test (20)",
    "หัวข้อ 1 (5)", "หัวข้อ 2 (5)", "หัวข้อ 3 (5)", "หัวข้อ 4 (5)", "หัวข้อ 5 (5)", "หัวข้อ 6 (5)",
    "รวม Final (30)"
  ];
  const rows = [header];
  const sortedKeys = Object.keys(records).sort((a, b) => {
    const ra = records[a];
    const rb = records[b];
    const ca = Number(String(ra.cohort).replace(/\D+/g, "")) || 999;
    const cb = Number(String(rb.cohort).replace(/\D+/g, "")) || 999;
    if (ca !== cb) return ca - cb;
    const sa = Number(ra.seat) || 999;
    const sb = Number(rb.seat) || 999;
    if (sa !== sb) return sa - sb;
    return String(ra.name).localeCompare(String(rb.name), "th");
  });
  sortedKeys.forEach(k => {
    const r = records[k];
    rows.push([
      r.cohort, r.seat, r.name, r.dept,
      r.pre, r.post, r.f1, r.f2, r.f3, r.f4, r.f5, r.f6, r.finalSum
    ]);
  });
  outSheet.getRange(1, 1, rows.length, header.length).setValues(rows);
  outSheet.getRange(1, 1, 1, header.length).setFontWeight("bold");
  outSheet.setFrozenRows(1);
}
