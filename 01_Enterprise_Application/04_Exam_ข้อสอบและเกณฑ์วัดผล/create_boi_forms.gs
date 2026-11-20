/**
 * สคริปต์สร้าง Google Forms (Pre-Test 20 ข้อ + Post-Test/Final ทฤษฎีรวม 30 ข้อ) และสรุปคะแนนลง Google Sheet อัตโนมัติ (v2)
 *
 * วิธีใช้งานครั้งแรก:
 *   1. เปิด Google Sheet -> เมนู "ส่วนขยาย (Extensions)" -> "Apps Script"
 *   2. วางโค้ดไฟล์นี้ทั้งหมด -> กดบันทึก -> เลือกฟังก์ชัน "createAllBOIForms" -> กด Run
 *
 * วิธีซ่อมชีตที่ขึ้น "พบชื่อคอลัมน์ที่ซ้ำกัน" และดึงรายชื่อ/คะแนนลง สรุปคะแนน_Audit ทันที:
 *   1. วางโค้ดนี้ทับของเดิมใน Apps Script -> กดบันทึก
 *   2. เลือกฟังก์ชัน "repairLinkedResponseSheets" -> กด Run (หรือกดจากเมนู BOI ระบบสอบ)
 *
 * หมายเหตุ: ส่วน EXAM_DATA สร้างอัตโนมัติจาก combined_exam.json ด้วย `python build_exam.py` (ห้ามแก้บรรทัดในบล็อกนี้ด้วยมือ)
 */

// <EXAM_DATA_START>
const EXAM_DATA = {"version":2,"title":"แบบทดสอบทฤษฎีรวม (Post-Test + Final ภาคทฤษฎี · 30 ข้อ)","subject":"การออกแบบ พัฒนา และบูรณาการแอปพลิเคชันระดับองค์กร (Enterprise Application)","minutes":45,"topics":[{"topicNo":1,"code":"T1","label":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","maxPoints":5},{"topicNo":2,"code":"T2","label":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","maxPoints":5},{"topicNo":3,"code":"T3","label":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","maxPoints":5},{"topicNo":4,"code":"T4","label":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","maxPoints":5},{"topicNo":5,"code":"T5","label":"การส่งแจ้งเตือน Webhook และ Async Polling","maxPoints":5},{"topicNo":6,"code":"T6","label":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","maxPoints":5}],"instructions":["ข้อสอบชุดนี้รวม Post-Test และ Final ภาคทฤษฎีเป็นชุดเดียว จำนวน 30 ข้อ (ข้อละ 1 คะแนน = 30 คะแนน) ใช้เวลาประมาณ 40–45 นาที","ระบบจะแยกคะแนนจาก 20 ข้อแกนหลักส่งต่อเข้าระบบ HR (Post-Test /20 คู่กับ Pre-Test) และสรุปรวม 6 หัวข้อ (หัวข้อละ 5 คะแนน = 30 คะแนน) เข้าใบ Audit อัตโนมัติ","ข้อท้าย ๆ ของแต่ละหัวข้อเน้นการอ่านโค้ด ไล่จุดผิด (Debug) วิเคราะห์ค่าขอบ และความปลอดภัยไซเบอร์"],"preTest":[{"clo":"CLO01","q":"ข้อใดเป็นระบบ OT (Operational Technology)","choices":["ระบบ ERP","ระบบบัญชี","อีเมลองค์กร","PLC และ SCADA"],"answer":3,"why":"OT คือระบบที่ควบคุมเครื่องจักรและกระบวนการผลิตโดยตรง เช่น PLC, SCADA, HMI ส่วนข้ออื่นเป็นระบบ IT"},{"clo":"CLO01","q":"ระบบ OT ให้ความสำคัญกับอะไรเป็นอันดับแรก","choices":["ความลับของข้อมูล","ความสวยงามของหน้าจอ","ความปลอดภัยและความพร้อมใช้งานของเครื่องจักร","ราคาถูกที่สุด"],"answer":2,"why":"OT เน้นความปลอดภัยและความพร้อมใช้งาน เพราะถ้าเครื่องจักรหยุดจะกระทบการผลิตและความปลอดภัยโดยตรง"},{"clo":"CLO01","q":"ในสถาปัตยกรรม Client-Server หน้าที่ของ Client คือข้อใด","choices":["แสดงผลและรับข้อมูลจากผู้ใช้","เก็บฐานข้อมูลหลัก","ประมวลผล Business Logic ทั้งหมด","ควบคุมเครื่องจักรโดยตรง"],"answer":0,"why":"Client (เช่น เว็บเบราว์เซอร์) ทำหน้าที่แสดงผลและรับคำสั่งจากผู้ใช้ ส่วน Server ทำหน้าที่ประมวลผลและจัดการข้อมูล"},{"clo":"CLO02","q":"JSON ข้อใดเขียนถูกต้อง","choices":["{name: 'Line A'}","{\"name\": \"Line A\"}","{'name' = 'Line A'}","[name: \"Line A\"]"],"answer":1,"why":"ชื่อ key และข้อความใน JSON ต้องครอบด้วยเครื่องหมายคำพูดคู่ (\") และคั่นด้วยเครื่องหมาย :"},{"clo":"CLO02","q":"จาก JSON {\"machine\": {\"temp\": 72}} ถ้าเก็บไว้ในตัวแปร data จะอ่านค่า 72 อย่างไร","choices":["data.temp","data[temp]","data.machine.temp","machine.temp.data"],"answer":2,"why":"temp อยู่ภายใน object ชื่อ machine จึงต้องเขียนอ้างอิงทีละชั้นเป็น data.machine.temp"},{"clo":"CLO02","q":"จาก {\"sensors\": [10, 20, 30]} ค่า data.sensors[1] คือเท่าไร","choices":["10","20","30","undefined"],"answer":1,"why":"ตำแหน่ง (index) ใน Array เริ่มนับจาก 0 ดังนั้น index 1 คือข้อมูลตัวที่สองซึ่งก็คือ 20"},{"clo":"CLO02","q":"ข้อใดคือชนิดข้อมูลทั้ง 6 ชนิดที่ JSON รองรับ","choices":["string, number, boolean, null, object, array","string, number, function, date, object, array","text, integer, undefined, function, class, list","string, char, float, undefined, object, map"],"answer":0,"why":"ตามสไลด์ JSON เก็บข้อมูลได้ 6 ชนิด คือ string, number, boolean, null, object และ array (ไม่เก็บ function หรือ undefined)"},{"clo":"CLO03","q":"แท็กใดเป็น Semantic HTML ที่บอกความหมายของโครงสร้างหน้าเว็บ","choices":["<header>","<span>","<div>","<b>"],"answer":0,"why":"<header> บอกความหมายว่าเป็นส่วนหัวของหน้าเว็บ ส่วน <div> และ <span> ไม่ได้บอกความหมายเชิงโครงสร้าง"},{"clo":"CLO03","q":"การเขียน CSS แบบใดเหมาะกับเว็บที่มีหลายหน้าและใช้สไตล์ร่วมกัน","choices":["Inline Style","Internal Style","External Style Sheet (ไฟล์ .css)","เขียนใน JavaScript ทุกครั้ง"],"answer":2,"why":"External Style Sheet แยกสไตล์ไว้ในไฟล์ .css กลาง ทุกหน้าเรียกใช้ร่วมกันและแก้ไขจุดเดียวได้ทั้งเว็บ"},{"clo":"CLO03","q":"ถ้าต้องการตัวแปรที่เปลี่ยนค่าได้ในภายหลัง ควรประกาศด้วยคำใด","choices":["const","let","static","final"],"answer":1,"why":"let ใช้ประกาศตัวแปรที่เปลี่ยนค่าได้ ส่วน const ใช้กับค่าคงที่ที่ไม่เปลี่ยนค่า"},{"clo":"CLO03","q":"ผลลัพธ์ของ '10' + 5 ใน JavaScript คือข้อใด","choices":["15","'15'","Error","'105'"],"answer":3,"why":"เมื่อใช้เครื่องหมาย + กับข้อความ (String) JavaScript จะนำมาต่อข้อความกัน จึงได้ '105'"},{"clo":"CLO03","q":"คำสั่งใดเลือก element ที่มี id=\"status\"","choices":["document.getElementById('status')","document.querySelector('status')","document.getElementsByClassName('status')","document.select('#status')"],"answer":0,"why":"getElementById('status') ใช้เลือก element จาก id โดยตรง ถ้าใช้ querySelector ต้องเขียน '#status'"},{"clo":"CLO03","q":"ถ้าต้องการให้ฟังก์ชันทำงานเมื่อผู้ใช้คลิกปุ่มบนหน้าเว็บ ต้องใช้ Event ใด","choices":["onload","onclick","onmouseover","onkeydown"],"answer":1,"why":"onclick ทำงานเมื่อผู้ใช้คลิกปุ่ม ส่วน onmouseover เกิดเมื่อนำเมาส์ไปวาง และ onkeydown เกิดเมื่อกดปุ่มคีย์บอร์ด"},{"clo":"CLO04","q":"ตามมาตรฐานสีไฟแสดงสถานะ (IEC 60204-1) สีเหลืองหมายถึงอะไร","choices":["เตือน / ผิดปกติ ต้องเฝ้าระวัง","ทำงานปกติ","หยุดฉุกเฉิน","ออฟไลน์"],"answer":0,"why":"ตามมาตรฐานสีอุตสาหกรรม เขียว = ปกติ, เหลือง = เตือน/ผิดปกติ, แดง = ฉุกเฉิน"},{"clo":"CLO04","q":"หลัก Visual Hierarchy ในการออกแบบ Dashboard หมายถึงอะไร","choices":["การใส่สีสันให้ครบทุกสีในหน้าเดียว","การจัดลำดับสายตาด้วยขนาด ตำแหน่ง และสี ให้มองเห็นข้อมูลสำคัญได้ทันที","การใส่ตัวเลขทุกตัวในโรงงานลงในตารางเดียวกัน","การตั้งค่าให้หน้าเว็บรีเฟรชทุก 1 วินาที"],"answer":1,"why":"Visual Hierarchy คือการจัดลำดับความสำคัญทางสายตา เพื่อให้ผู้ดูเข้าใจสถานะหลักของระบบได้ทันที"},{"clo":"CLO05","q":"HTTP Method ใดใช้สำหรับอ่าน/ดึงข้อมูลจาก API","choices":["GET","POST","PUT","DELETE"],"answer":0,"why":"GET = อ่านข้อมูล, POST = เพิ่ม/ส่งข้อมูลใหม่, PUT = แก้ไขข้อมูลเดิม, DELETE = ลบข้อมูล"},{"clo":"CLO05","q":"ข้อใดอธิบายความต่างระหว่างการเรียก API ปกติกับ Webhook ได้ถูกต้อง","choices":["API ปกติระบบต้นทางส่งมาหาเราเอง ส่วน Webhook เราต้องไปขอ","Webhook ใช้ได้เฉพาะกับอีเมล","ทั้งสองเหมือนกันทุกประการ","API ปกติเราเป็นฝ่ายไปขอข้อมูล (Pull) ส่วน Webhook ระบบต้นทางส่งมาทันทีเมื่อเกิดเหตุการณ์ (Push)"],"answer":3,"why":"Webhook ทำงานแบบ Push ส่งข้อมูลมาทันทีเมื่อเกิดเหตุการณ์ ไม่ต้องคอยส่งคำขอไปถามซ้ำ ๆ"},{"clo":"CLO05","q":"ในโค้ด async/await คำสั่ง const data = await res.json(); ทำหน้าที่อะไร","choices":["ส่งข้อมูลออกไปที่ Server","แปลงข้อมูล JSON ที่ได้รับจาก API ให้เป็น Object ของ JavaScript","ลบข้อมูลใน Server","บันทึกไฟล์ JSON ลงเครื่อง"],"answer":1,"why":"res.json() ทำหน้าที่อ่านและแปลงข้อมูล JSON จาก Response ให้เป็น Object เพื่อนำไปใช้แสดงผลต่อ และต้องใส่ await รอให้แปลงเสร็จก่อน"},{"clo":"CLO06","q":"Test Case ที่ดีต้องมีส่วนใดเพื่อใช้ตัดสินว่า Pass หรือ Fail","choices":["ชื่อผู้พัฒนา","สีของหน้าจอ","Expected Result (ผลลัพธ์ที่คาดหวัง)","ราคาของระบบ"],"answer":2,"why":"ต้องนำผลที่ได้จริง (Actual Result) มาเทียบกับผลที่คาดหวัง (Expected Result) เพื่อตัดสินว่า Pass หรือ Fail"},{"clo":"CLO06","q":"UAT (User Acceptance Testing) ทำโดยใคร","choices":["นักพัฒนาที่เขียนโค้ด","เครื่องมือทดสอบอัตโนมัติเท่านั้น","ผู้ดูแล Server","ผู้ใช้งานจริงหรือลูกค้า"],"answer":3,"why":"UAT คือขั้นตอนสุดท้ายที่ให้ผู้ใช้งานจริงทดสอบในสภาพเหมือนจริงก่อนเริ่มใช้งานจริง (Go-Live)"}],"theoryExam":[{"topicNo":1,"topicLabel":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","clo":"CLO01","isPostCore":true,"points":1,"q":"ข้อใดเป็นอุปกรณ์หรือระบบฝั่ง OT ทั้งหมด","choices":["ERP, CRM และอีเมลองค์กร","PLC, HMI และเซนเซอร์วัดอุณหภูมิ","ฐานข้อมูลบัญชี, HMI และ ERP","เว็บไซต์บริษัท, PLC และอีเมลองค์กร"],"answer":1,"why":"PLC, HMI และเซนเซอร์เกี่ยวข้องกับเครื่องจักรและสายการผลิตโดยตรง จึงเป็นฝั่ง OT ทั้งหมด"},{"topicNo":1,"topicLabel":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","clo":"CLO01","isPostCore":true,"points":1,"q":"ทีม IT ต้องการรีสตาร์ตเครื่องคอมพิวเตอร์ที่คุมเครื่องจักรทันทีระหว่างกะผลิต ข้อกังวลหลักจากมุมมอง OT คือข้อใด","choices":["หน้าจออาจเปลี่ยนสี","ค่าลิขสิทธิ์ซอฟต์แวร์อาจสูงขึ้น","ข้อมูลอาจถูกส่งออกไปนอกบริษัท","อาจทำให้เครื่องจักรหยุดชะงัก กระทบการผลิตและความปลอดภัย"],"answer":3,"why":"ระบบ OT ให้ความสำคัญกับความปลอดภัยและความพร้อมใช้งานของเครื่องจักร การอัปเดตหรือรีสตาร์ตจึงต้องวางแผนล่วงหน้า"},{"topicNo":1,"topicLabel":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","clo":"CLO01","isPostCore":true,"points":1,"q":"ในระบบตรวจวัดเครื่องจักร (Electrical Meter) ของห้องเรียน ผู้สอนรันโปรแกรม Python ส่วนผู้เรียนเปิดหน้าเว็บ index.html ข้อใดอธิบายสถาปัตยกรรม Client-Server ได้ถูกต้อง","choices":["เบราว์เซอร์ของผู้เรียนเป็น Server ส่วนโปรแกรม Python เป็น Client","โปรแกรม Python เป็น API Server คอยตอบข้อมูล JSON ส่วนเบราว์เซอร์ผู้เรียนเป็น Client ที่ส่ง HTTP Request ไปขอและแสดงผล","ทั้งสองฝั่งอ่านเขียนไฟล์ลงฮาร์ดดิสก์เดียวกันโดยตรงไม่ผ่าน HTTP","ระบบทั้งหมดทำงานอยู่บน PLC โดยไม่ต้องใช้เบราว์เซอร์"],"answer":1,"why":"Python รอรับ HTTP Request และตอบกลับเป็น JSON จึงเป็นฝั่ง Server ส่วน HTML/JS บนเบราว์เซอร์เป็นฝั่ง Client"},{"topicNo":1,"topicLabel":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","clo":"CLO01","isPostCore":false,"points":1,"q":"ผู้เรียนดับเบิลคลิกเปิดไฟล์ index.html จากโฟลเดอร์ตรง ๆ (ขึ้น URL เป็น file:///...) แล้วโค้ดที่เรียก fetch('data/meter.json') ไม่ทำงาน เกิดจากสาเหตุใดและต้องแก้อย่างไร","choices":["เบราว์เซอร์บล็อกการเรียก fetch บนโปรโตคอล file:// เพื่อความปลอดภัย ต้องเปิดผ่านเว็บเซิร์ฟเวอร์จำลอง เช่น Live Server (http://...)","ต้องเปลี่ยนนามสกุลไฟล์จาก .html เป็น .exe ก่อนเปิด","เบราว์เซอร์ไม่อนุญาตให้ใช้ JavaScript บน Windows ถ้าไม่ได้ต่ออินเทอร์เน็ต","ต้องลบไฟล์ CSS ออกก่อนจึงจะเรียก fetch ได้"],"answer":0,"why":"เมื่อเปิดด้วย file:// Origin จะเป็น null ทำให้ติดนโยบายความปลอดภัยของเบราว์เซอร์ จึงต้องเปิดผ่าน HTTP Server เช่น VS Code Live Server"},{"topicNo":1,"topicLabel":"สถาปัตยกรรมระบบ OT / IT และ Enterprise App","clo":"CLO01","isPostCore":false,"points":1,"q":"เมื่อนำระบบเว็บแจ้งเตือนไปใช้จริงในโรงงาน ทำไมไม่ควรให้โค้ด JavaScript หน้าเว็บถือ Token ลับและยิงเข้า Webhook ภายนอกโดยตรง (เช่น LINE / Discord / MS Teams)","choices":["เพราะ JavaScript ส่ง Method POST ไม่ได้หากอยู่ฝั่ง Frontend","เพราะทุกคนที่เปิด F12 / DevTools สามารถดู Network หรือ Source โค้ดแล้วขโมย Token ลับไปยิงสแปมได้ ควรส่งผ่าน Backend Server แทน","เพราะ Token จะหมดอายุทุก 5 วินาทีเมื่ออยู่ในไฟล์ .html","เพราะ CSS Flexbox ไม่รองรับการส่ง Token"],"answer":1,"why":"โค้ดและ Request ฝั่ง Client เปิดดูได้ทั้งหมดผ่าน DevTools ข้อมูลลับอย่าง API Key / Webhook Token ต้องเก็บไว้ฝั่ง Backend เท่านั้น"},{"topicNo":2,"topicLabel":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","clo":"CLO03","isPostCore":true,"points":1,"q":"ต้องการทำแถบเมนูลิงก์ไปหน้าต่าง ๆ ของเว็บ ควรใช้แท็ก Semantic HTML ใดครอบเมนู","choices":["<div class=\"menu\">","<span>","<footer>","<nav>"],"answer":3,"why":"<nav> ใช้สำหรับส่วนนำทาง/เมนูของหน้าเว็บ ส่วน <footer> คือส่วนท้ายของหน้า"},{"topicNo":2,"topicLabel":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","clo":"CLO03","isPostCore":true,"points":1,"q":"ไฟล์ style.css กำหนด p { color: blue; } แต่ในหน้าเว็บเขียน <p style=\"color: red\">ข้อความ</p> ข้อความจะเป็นสีอะไร","choices":["แดง เพราะ style ที่เขียนในแท็กเจาะจงกว่า","น้ำเงิน เพราะไฟล์ CSS ภายนอกสำคัญที่สุด","ดำ เพราะกฎขัดกันจึงใช้ค่าเริ่มต้น","ม่วง เพราะสีผสมกัน"],"answer":0,"why":"Inline style ที่เขียนในแท็กมีลำดับความสำคัญ (Specificity) สูงกว่า Selector ในไฟล์ CSS ภายนอก"},{"topicNo":2,"topicLabel":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","clo":"CLO04","isPostCore":true,"points":1,"q":"ตามมาตรฐาน IEC 60204-1 ไฟแสดงสถานะสีใดหมายถึง \"ต้องให้ผู้ปฏิบัติงานดำเนินการ (Mandatory action)\"","choices":["เขียว","เหลือง","น้ำเงิน","ขาว"],"answer":2,"why":"ตามมาตรฐาน IEC 60204-1 สีน้ำเงินหมายถึงต้องให้ผู้ปฏิบัติงานดำเนินการ ส่วนเขียว=ปกติ, เหลือง=เตือน, แดง=อันตราย/ฉุกเฉิน"},{"topicNo":2,"topicLabel":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","clo":"CLO04","isPostCore":true,"points":1,"q":"เมื่อพนักงานกดปุ่ม \"ส่งแจ้งเตือน\" หรือ \"ลบข้อมูล\" บนหน้าจอโรงงาน การออกแบบ UI ที่ดีเพื่อป้องกันความผิดพลาดควรทำอย่างไร","choices":["ซ่อนปุ่มให้เล็กที่สุดจะได้ไม่เผลอกด","แสดงกล่องยืนยัน (Confirm) หรือแจ้งผลลัพธ์ชัดเจนและปิดปุ่มชั่วคราวกันกดซ้ำ","ปล่อยให้กดซ้ำได้ไม่จำกัดโดยไม่ต้องแสดงข้อความใด ๆ","ให้ระบบลบข้อมูลทันทีโดยไม่ต้องตรวจเงื่อนไข"],"answer":1,"why":"หลัก Error Prevention และ Feedback ต้องให้ผู้ใช้เห็นสถานะชัดเจน ป้องกันการกดซ้ำระหว่างรอคำตอบ และขนาดปุ่มควรกดง่าย (อย่างน้อย 44x44px)"},{"topicNo":2,"topicLabel":"โครงสร้างหน้าเว็บ HTML5, CSS Flexbox และ UX/UI","clo":"CLO03, CLO04","isPostCore":false,"points":1,"q":"มีโค้ด <section class=\"cards\"> ครอบ <article class=\"card\"> อยู่ 3 ใบ ผู้เรียนเขียน CSS ว่า .card { display: flex; } แต่การ์ดทั้ง 3 ใบยังเรียงลงมาเป็นแนวตั้ง ไม่เรียงข้างกัน ควรแก้อย่างไร","choices":["ย้าย display: flex; ไปใส่ที่ตัวแม่ (.cards) และเพิ่ม flex-wrap: wrap; gap: 16px;","เปลี่ยนจาก <article> เป็น <span> โดยไม่ต้องแก้ CSS","ใส่ color: flex; เพิ่มใน .card","ใส่ position: absolute; ทับทุกการ์ด"],"answer":0,"why":"display: flex ต้องกำหนดที่กล่องแม่ (Flex Container = .cards) เพื่อให้ลูกข้างใน (.card) จัดเรียงในแนวนอน และใช้ flex-wrap: wrap ให้ขึ้นแถวใหม่อัตโนมัติบนจอแคบ"},{"topicNo":3,"topicLabel":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","clo":"CLO03","isPostCore":true,"points":1,"q":"โค้ด JavaScript ข้อใดทำงานได้โดยไม่เกิด Error","choices":["const max = 240; max = 250;","const list; list = [];","let count = 0; count = count + 1;","let x = 1; let x = 2;"],"answer":2,"why":"let เปลี่ยนค่าใหม่ได้ ส่วน const เปลี่ยนค่าไม่ได้และต้องกำหนดค่าทันทีที่ประกาศ รวมถึงห้ามประกาศ let ชื่อซ้ำในขอบเขตเดียวกัน"},{"topicNo":3,"topicLabel":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","clo":"CLO03","isPostCore":true,"points":1,"q":"จากโค้ด let a = 12; let b = 5; console.log(2 * (a - b)); ผลลัพธ์คือข้อใด","choices":["19","14","12","7"],"answer":1,"why":"คำนวณในวงเล็บก่อน: 12 - 5 ได้ 7 แล้วนำไปคูณ 2 ได้ผลลัพธ์ 14"},{"topicNo":3,"topicLabel":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","clo":"CLO03","isPostCore":true,"points":1,"q":"ข้อใดเลือก element เดียวกับ document.getElementById('status')","choices":["document.querySelector('.status')","document.querySelector('status')","document.getElementsByClassName('status')","document.querySelector('#status')"],"answer":3,"why":"querySelector ใช้ CSS Selector จึงต้องใส่เครื่องหมาย # นำหน้าชื่อ id ส่วนเครื่องหมาย . ใช้กับ class"},{"topicNo":3,"topicLabel":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","clo":"CLO03","isPostCore":true,"points":1,"q":"เมื่อผู้ใช้นำเมาส์ไปวางบนข้อความหรือกล่องบนหน้าเว็บ (โดยยังไม่ได้กดคลิก) จะเกิด Event ใด","choices":["onmouseover","onmousedown","onmouseup","onclick"],"answer":0,"why":"onmouseover เกิดขึ้นทันทีเมื่อนำเมาส์ไปชี้บน element ก่อนกดคลิก (onmousedown/onclick)"},{"topicNo":3,"topicLabel":"การเขียนโปรแกรม JavaScript เงื่อนไข และ DOM","clo":"CLO03","isPostCore":false,"points":1,"q":"พิจารณาฟังก์ชันตรวจสอบมิเตอร์:\nfunction checkCondition(v, c, w) {\n  if (v > 240) return 'over_volt';\n  else if (c > 20) return 'over_curr';\n  else if (w < 1.5) return 'low_water';\n  else return 'normal';\n}\nหากค่าจาก API คือ v = 240, c = 20, w = 1.5 ฟังก์ชันจะคืนค่าใด และถ้ามีฟังก์ชันชื่อเดียวกันเขียนซ้ำด้านล่างสุดจะเกิดอะไรขึ้น","choices":["คืน 'over_volt' และฟังก์ชันตัวบนทำงานเสมอ","คืน 'normal' ทั้ง 3 เงื่อนไขยังไม่เกินเกณฑ์ และถ้าเขียน function ชื่อเดียวกันซ้ำด้านล่าง ตัวล่างจะเขียนทับตัวบนทันที","คืน 'over_curr' และเกิด SyntaxError ตอนเปิดหน้าเว็บ","คืน 'low_water' และเบราว์เซอร์จะรวมโค้ดทั้งสองฟังก์ชันเข้าด้วยกัน"],"answer":1,"why":"240 > 240, 20 > 20, 1.5 < 1.5 ต่างเป็นเท็จทั้งหมด จึงตกเข้า else ได้ 'normal' และใน JavaScript การประกาศ function ชื่อซ้ำในขอบเขตเดียวกัน ตัวหลังจะเขียนทับตัวแรกทำให้โค้ดตัวบนไม่ถูกเรียก"},{"topicNo":4,"topicLabel":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","clo":"CLO02","isPostCore":true,"points":1,"q":"JSON ข้อใดเขียนถูกต้องทั้งหมดตามมาตรฐาน RFC 8259","choices":["{\"line\": \"A\", \"temps\": [72.5, 73.0,]}","{\"line\": \"A\", \"online\": True}","{\"line\": \"A\", \"temps\": [72.5, 73.0]}","{\"line\": \"A\", \"note\": undefined}"],"answer":2,"why":"JSON ต้องไม่มี comma ตัวสุดท้าย, boolean ต้องเขียน true ตัวเล็กทั้งหมด และไม่มีชนิดข้อมูล undefined"},{"topicNo":4,"topicLabel":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","clo":"CLO02","isPostCore":true,"points":1,"q":"จากข้อมูล data = { \"machines\": [ { \"id\": \"M-01\", \"temp\": 72 }, { \"id\": \"M-02\", \"temp\": 65 } ] } ต้องเขียนอย่างไรจึงจะได้ค่า 65","choices":["data.machines.temp","data.machines[0].temp","data.machines[1].temp","data.machines[2].temp"],"answer":2,"why":"machines เป็น Array โดย M-01 อยู่ที่ index 0 และ M-02 อยู่ที่ index 1 จึงเขียนเป็น data.machines[1].temp"},{"topicNo":4,"topicLabel":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","clo":"CLO02","isPostCore":true,"points":1,"q":"จาก {\"sensors\": [10, 20, 30, 40]} ค่า data.sensors[data.sensors.length - 2] คือเท่าไร","choices":["20","30","40","undefined"],"answer":1,"why":"length คือ 4 ดังนั้น length - 2 คือ index 2 ซึ่งเป็นตัวที่สาม ได้ 30 (index เริ่มที่ 0)"},{"topicNo":4,"topicLabel":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","clo":"CLO02","isPostCore":true,"points":1,"q":"จาก JSON { \"line\": \"A\", \"running\": true, \"alarm\": null } ค่าของ \"running\" และ \"alarm\" เป็นชนิดข้อมูลใดตามลำดับ","choices":["string และ number","boolean และ null","boolean และ undefined","object และ array"],"answer":1,"why":"true เป็นชนิด boolean ส่วน null เป็นค่าว่างของ JSON"},{"topicNo":4,"topicLabel":"โครงสร้างข้อมูล JSON และการสื่อสาร REST API","clo":"CLO02, CLO05","isPostCore":false,"points":1,"q":"ผู้เรียนพิมพ์ URL ใน fetch() ผิดทำให้ Server ตอบกลับสถานะ 404 เป็นหน้า HTML error แล้วโค้ดที่ไม่ได้ตรวจ if (!res.ok) ไปเรียก await res.json() ต่อ ทันใดนั้น Console ขึ้น Error ว่า \"Unexpected token '<' ... is not valid JSON\" เพราะเหตุใด","choices":["fetch() จะไม่ throw error เองเมื่อเจอสถานะ HTTP 404 หรือ 500 ทำให้โค้ดไหลไปเอาหน้า HTML 404 มาแปลงเป็น JSON จึงพังตอน res.json()","fetch() บังคับให้ทุก Server ต้องส่ง HTML กลับมาเสมอ","คำสั่ง if (!res.ok) ใช้ได้เฉพาะกับ Webhook POST เท่านั้น ใช้กับ GET ไม่ได้","เครื่องหมาย '<' คือข้อมูลชนิดใหม่ของ JSON"],"answer":0,"why":"fetch จะ Promise reject เฉพาะเมื่อเชื่อมต่อเครือข่ายไม่ได้ แต่หาก Server ตอบ HTTP 404/500 Promise ยัง resolve อยู่ ดังนั้นต้องเช็ก if (!res.ok) throw new Error(...) ก่อนเรียก res.json() เสมอ"},{"topicNo":5,"topicLabel":"การส่งแจ้งเตือน Webhook และ Async Polling","clo":"CLO05","isPostCore":true,"points":1,"q":"เมื่อต้องการ \"ส่งข้อมูลใหม่\" หรือส่งข้อความแจ้งเตือนไปยัง Webhook API ของ Server ควรใช้ HTTP Method ใด","choices":["GET","POST","DELETE","HEAD"],"answer":1,"why":"GET ใช้ดึง/อ่านข้อมูล ส่วน POST ใช้ส่งข้อมูลใหม่หรือส่งแจ้งเตือนไปยัง Server"},{"topicNo":5,"topicLabel":"การส่งแจ้งเตือน Webhook และ Async Polling","clo":"CLO05","isPostCore":true,"points":1,"q":"หากโรงงานต้องการให้ระบบส่งข้อความแจ้งเตือนทันทีที่เครื่องจักรหยุด โดยหน้าเว็บไม่ต้องคอยเรียก API ถามซ้ำ ๆ ทุก 5 วินาที ควรใช้กลไกใด","choices":["Webhook (Push Notification)","HTML CSS Flexbox","Local File เปิดผ่าน file://","Manual Refresh กด F5 เอง"],"answer":0,"why":"Webhook จะผลัก (Push) ข้อมูลมาทันทีเมื่อเกิดเหตุการณ์สำคัญ โดยไม่ต้องคอยดึงข้อมูลซ้ำ"},{"topicNo":5,"topicLabel":"การส่งแจ้งเตือน Webhook และ Async Polling","clo":"CLO05","isPostCore":true,"points":1,"q":"ข้อใดเรียงลำดับการดึงข้อมูลด้วย fetch แบบ async/await ได้ถูกต้อง","choices":["await res.json() -> เรียก fetch -> ตรวจ res.ok -> แสดงผล","เรียก fetch -> ตรวจ res.ok -> แปลงด้วย await res.json() -> แสดงผล","เรียก fetch -> แสดงผล -> ตรวจ res.ok","ตรวจ res.ok -> เรียก fetch -> await res.json() -> แสดงผล"],"answer":1,"why":"ต้องเรียก await fetch เพื่อรับ Response ก่อน จากนั้นเช็ก res.ok แล้วค่อย await res.json() แปลงเป็น Object ก่อนนำไปแสดงผล"},{"topicNo":5,"topicLabel":"การส่งแจ้งเตือน Webhook และ Async Polling","clo":"CLO05","isPostCore":false,"points":1,"q":"เมื่อส่งแจ้งเตือนไปที่ Webhook ด้วย fetch แล้วฝั่ง Server แจ้ง Error 400 พร้อมข้อความว่า \"ได้รับ body เป็น [object Object]\" สาเหตุที่ถูกต้องคือข้อใด","choices":["ลืมใส่ Content-Type และลืมแปลง Object ด้วย JSON.stringify(...) ใน body ของ fetch","ลืมใส่ async หน้าปุ่มใน HTML","Server รับข้อมูลได้เฉพาะ method GET เท่านั้น","ตัวแปร payload มีช่องว่างในชื่อ key"],"answer":0,"why":"ถ้าส่ง Object ของ JS ให้ body ของ fetch โดยตรง มันจะถูกแปลงเป็นข้อความ \"[object Object]\" ต้องใช้ JSON.stringify(payload) พร้อม header 'Content-Type': 'application/json'"},{"topicNo":5,"topicLabel":"การส่งแจ้งเตือน Webhook และ Async Polling","clo":"CLO05","isPostCore":false,"points":1,"q":"ในระบบตรวจอัตโนมัติทุก 5 วินาที เราใช้ตัวแปร lastSentCondition กันไม่ให้ส่งแจ้งเตือนซ้ำ แต่พบอาการผิดปกติคือ \"ครั้งแรกที่แรงดันเกิน (over_volt) ส่งแจ้งเตือนได้ แต่พอมิเตอร์กลับเป็นปกติแล้วเกิด over_volt อีกรอบ ระบบกลับไม่ยอมส่งซ้ำให้ใหม่\" น่าจะลืมเขียนโค้ดส่วนใด","choices":["ลืมตั้ง lastSentCondition = ''; เมื่อสถานะกลับมาเป็น 'normal'","ลืมเปลี่ยน clearInterval ในทุกครั้งที่กดปุ่ม","ลืมส่ง condition ซ้ำตอนสถานะ normal ไปที่ Server","ลืมตั้ง MAX_VOLTAGE = 0"],"answer":0,"why":"เมื่อเข้าเคส 'normal' ต้องรีเซ็ต lastSentCondition = '' (หรือ 'normal') ด้วย มิฉะนั้น lastSentCondition จะยังค้างเป็น 'over_volt' ทำให้รอบถัดไปข้ามการส่งแจ้งเตือน"},{"topicNo":6,"topicLabel":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","clo":"CLO06","isPostCore":true,"points":1,"q":"Test Case ใดเขียนผลลัพธ์ที่คาดหวัง (Expected Result) ได้ชัดเจนและตรวจวัดได้จริงที่สุด","choices":["ระบบทำงานถูกต้อง","หน้าจอแสดงผลสวยงาม","เมื่อแรงดันเป็น 245 V หน้าจอแสดงคำเตือน \"แรงดันเกิน 240 V\" และเปลี่ยนป้ายเป็นสีแดง","ไม่พบข้อผิดพลาด"],"answer":2,"why":"Expected Result ที่ดีต้องระบุผลลัพธ์ที่เห็นและตรวจวัดได้ชัดเจน เพื่อให้ผู้ทดสอบตัดสิน Pass/Fail ได้ตรงกัน"},{"topicNo":6,"topicLabel":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","clo":"CLO06","isPostCore":true,"points":1,"q":"จุดประสงค์หลักของการทำ UAT (User Acceptance Testing) คือข้อใด","choices":["ให้ผู้เขียนโปรแกรมตรวจ syntax ของโค้ด","ให้ผู้ใช้งานจริงทดสอบระบบในสภาพเหมือนจริง เพื่อยืนยันว่าใช้งานได้ตรงความต้องการก่อน Go-Live","ออกแบบสีของหน้าเว็บให้สวยงามก่อนเขียนโค้ด","ติดตั้งฐานข้อมูลและ Server ใหม่"],"answer":1,"why":"UAT คือการให้ผู้ใช้งานจริงทดสอบและลงชื่อยอมรับระบบก่อนนำไปใช้งานจริง"},{"topicNo":6,"topicLabel":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","clo":"CLO04, CLO06","isPostCore":false,"points":1,"q":"ข้อใดปฏิบัติได้ถูกต้องตามหลักความปลอดภัยเว็บ (ป้องกัน XSS และความลับรั่วไหล) ในระบบ Dashboard โรงงาน","choices":["ใช้ .innerHTML แสดงชื่อผู้ใช้งานและข้อความจาก API เพื่อให้เบราว์เซอร์ตีความแท็กได้อัตโนมัติ","ใช้ .textContent ในการแสดงข้อความที่ผู้ใช้กรอกเพื่อป้องกันการรันสคริปต์แฝง (XSS) และไม่เก็บรหัสผ่านในไฟล์ JS ฝั่ง Client","บันทึกรหัสผ่านฐานข้อมูลและข้อมูลพนักงานทั้งหมดลงใน localStorage เพื่อโหลดเร็ว","ไม่ต้องตรวจ Input ที่ Server หากหน้าเว็บเช็กให้แล้ว"],"answer":1,"why":".innerHTML อาจถูกฝัง <script> หรือ onerror โจมตีแบบ XSS ได้ จึงควรใช้ .textContent และข้อมูลความลับไม่ควรอยู่ในไฟล์ JS หรือ localStorage"},{"topicNo":6,"topicLabel":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","clo":"CLO06","isPostCore":false,"points":1,"q":"หากเงื่อนไขแจ้งเตือนคือ voltage > 240 และ water < 1.5 การทดสอบค่าขอบ (Boundary Value Analysis) ชุดใดตรวจความแม่นยำของเงื่อนไข (เช่น > เทียบกับ >=) ได้ครอบคลุมที่สุด","choices":["voltage = 200 และ 300; water = 0 และ 10","voltage = 240.0 (ต้องปกติ) กับ 240.1 (ต้องเตือน); water = 1.5 (ต้องปกติ) กับ 1.4 (ต้องเตือน)","voltage = 230 อย่างเดียว 5 รอบ","ทดสอบเฉพาะตอนปิดเซิร์ฟเวอร์"],"answer":1,"why":"การทดสอบค่าขอบ (Boundary Testing) ต้องลองค่าตรงจุดตัดพอดี (240.0, 1.5) เทียบกับค่าที่ข้ามจุดตัดนิดเดียว (240.1, 1.4) เพื่อตรวจว่าเขียน > / >= หรือ < / <= ถูกต้อง"},{"topicNo":6,"topicLabel":"ความมั่นคงปลอดภัยไซเบอร์ (Security) การทดสอบ และ UAT","clo":"CLO06","isPostCore":false,"points":1,"q":"ข้อใดคือความเสี่ยงด้านความปลอดภัยที่ต้องแก้ไขหาก API ฝั่ง Server มีการส่งข้อมูลลับหรือเฉลยปนมากับ Response (เช่น ส่ง field \"scenario\" หรือเปิดสิทธิ์ลบข้อมูลให้ Client ทั่วไปเรียกได้)","choices":["ไม่มีผลอะไร เพราะเบราว์เซอร์ซ่อน JSON จากผู้ใช้","Client สามารถแก้ไขโค้ดฝั่งเบราว์เซอร์หรือยิง Request ตรงเพื่อแอบดูเฉลย/โจมตีได้ จึงต้องย้ายการตรวจสิทธิ์และซ่อนข้อมูลภายในไว้ที่ฝั่ง Server เสมอ","ทำให้สีตัวอักษร CSS เพี้ยน","ทำให้ fetch() เปลี่ยนเป็น GET อัตโนมัติ"],"answer":1,"why":"Security Boundary อยู่ที่ฝั่ง Server เสมอ ห้ามไว้ใจ Client และห้ามส่งข้อมูลภายใน/สิทธิ์ผู้ดูแลไปให้ Client ทั่วไป"}]};
// <EXAM_DATA_END>
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
  const tag = q.topicNo ? "[หัวข้อ " + q.topicNo + ": " + q.topicLabel + "]\n" : "";
  const label = tag + titlePrefix + q.q;
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

function addTheorySections_(form, list) {
  let currentTopic = 0;
  list.forEach((q, idx) => {
    const tNo = Number(q.topicNo || 0);
    if (tNo && tNo !== currentTopic) {
      currentTopic = tNo;
      form.addPageBreakItem()
        .setTitle("หัวข้อที่ " + tNo + ": " + (q.topicLabel || ""))
        .setHelpText("จำนวน 5 ข้อ (ข้อละ 1 คะแนน = 5 คะแนน)");
    }
    const item = form.addMultipleChoiceItem();
    applyMcqConfig_(item, q, 1, idx, 1);
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
        } else if ((label.indexOf("Post-Test") >= 0 || label.indexOf("ทฤษฎีรวม") >= 0) && (!cfg.postFinal || !cfg.postFinal.id)) {
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
          } else if ((fTitle.indexOf("Post-Test") >= 0 || fTitle.indexOf("ทฤษฎี") >= 0 || mcCount >= 26) && (!cfg.postFinal || !cfg.postFinal.id)) {
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
  preForm.addPageBreakItem().setTitle("แบบทดสอบก่อนเรียน (20 ข้อ · 20 คะแนน)");
  addMcqList_(preForm, EXAM_DATA.preTest, 1, 1);

  // 2. สร้างฟอร์มทฤษฎีรวม v2 (Post-Test + Final 6 หัวข้อ = 30 ข้อ · 30 คะแนน)
  const postFinalForm = FormApp.create(EXAM_DATA.title + " · วิชา Enterprise Application (BOI)")
    .setDescription(EXAM_DATA.instructions.join("\n"))
    .setIsQuiz(true)
    .setCollectEmail(false)
    .setProgressBar(true)
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage("ส่งข้อสอบทฤษฎีรวม (30 ข้อ) เรียบร้อยแล้วครับ");
  const postIds = addIdentityItems_(postFinalForm);
  addTheorySections_(postFinalForm, EXAM_DATA.theoryExam);

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
    ["2. ทฤษฎีรวม v2: Post-Test + Final 6 หัวข้อ (30 ข้อ · 30 คะแนน)", postFinalForm.getPublishedUrl(), postFinalForm.getEditUrl()]
  ];
  linkSheet.getRange(1, 1, rows.length, 3).setValues(rows);
  linkSheet.getRange(1, 1, 1, 3).setFontWeight("bold");
  linkSheet.setColumnWidth(1, 340);
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
        title: "ทฤษฎีรวม v2 (Post-Test HR + Final 6 หัวข้อ)",
        when: "วันที่ 4 · ช่วงสอบทฤษฎี",
        note: "30 ข้อ (6 หัวข้อ × 5 ข้อ = 30 คะแนน) แยกคะแนน HR /20 อัตโนมัติ",
        url: postFinalForm.getPublishedUrl(),
        editUrl: postFinalForm.getEditUrl()
      }
    ]
  };

  Logger.log("=== สร้าง Google Forms (v2) สำเร็จ! คัดลอก JSON ด้านล่างไปวางใน form_links.json ได้เลย ===");
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

  function tryUpdateInPlace(form, list, startNo, defaultPoints) {
    const existingIds = findIdentityItems_(form);
    const mcItems = form.getItems(FormApp.ItemType.MULTIPLE_CHOICE);
    if (existingIds.cohortId && existingIds.seatId && existingIds.nameId && mcItems.length === list.length) {
      form.setIsQuiz(true);
      list.forEach((q, idx) => {
        applyMcqConfig_(mcItems[idx].asMultipleChoiceItem(), q, startNo, idx, defaultPoints);
      });
      return existingIds;
    }
    return null;
  }

  const preInPlace = tryUpdateInPlace(preForm, EXAM_DATA.preTest, 1, 1);
  if (preInPlace) {
    cfg.pre.items = preInPlace;
  } else {
    if (preForm.getResponses().length > 0) {
      throw new Error("จำนวนข้อ Pre-Test เปลี่ยนแปลงแต่ยังมีคำตอบค้างอยู่ กรุณาลบคำตอบก่อนครับ");
    }
    clearAllItems(preForm);
    preForm.setIsQuiz(true);
    cfg.pre.items = addIdentityItems_(preForm);
    preForm.addPageBreakItem().setTitle("แบบทดสอบก่อนเรียน (20 ข้อ · 20 คะแนน)");
    addMcqList_(preForm, EXAM_DATA.preTest, 1, 1);
    relinkFormDestinationClean_(preForm, activeSs);
  }

  const postInPlace = tryUpdateInPlace(postForm, EXAM_DATA.theoryExam, 1, 1);
  if (postInPlace) {
    postForm.setDescription(EXAM_DATA.instructions.join("\n"));
    cfg.postFinal.items = postInPlace;
  } else {
    if (postForm.getResponses().length > 0) {
      throw new Error("จำนวนข้อทฤษฎีเปลี่ยนจาก 26 เป็น 30 ข้อแล้ว กรุณารัน createAllBOIForms เพื่อสร้างฟอร์ม v2 ใหม่สำหรับรุ่นถัดไป (หรือลบคำตอบเก่าก่อน)");
    }
    clearAllItems(postForm);
    postForm.setIsQuiz(true);
    postForm.setDescription(EXAM_DATA.instructions.join("\n"));
    cfg.postFinal.items = addIdentityItems_(postForm);
    addTheorySections_(postForm, EXAM_DATA.theoryExam);
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

function parseQuestionNo_(title, fallbackIdx) {
  const m = String(title || "").match(/(?:^|\n)(\d+)\./);
  return m ? Number(m[1]) : (fallbackIdx + 1);
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
      if (/(?:^|\n)\d+\./.test(title)) return;
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
        pre: "", postHr: "", t1: "", t2: "", t3: "", t4: "", t5: "", t6: "", theorySum: ""
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

    const isLegacy26 = gradables.length <= 26;
    let postHr = 0;
    const tScores = [0, 0, 0, 0, 0, 0];

    if (isLegacy26) {
      // รองรับชีตรุ่นที่ 1–3 ที่ยังเป็น 26 ข้อ
      gradables.forEach((ir, idx) => {
        const score = Number(ir.getScore() || 0);
        const qNo = parseQuestionNo_(ir.getItem().getTitle(), idx);
        if (qNo >= 1 && qNo <= 20) postHr += score;
        else if (qNo >= 21 && qNo <= 26) tScores[qNo - 21] = score;
      });
      rec.postHr = postHr;
      rec.t1 = tScores[0]; rec.t2 = tScores[1]; rec.t3 = tScores[2];
      rec.t4 = tScores[3]; rec.t5 = tScores[4]; rec.t6 = tScores[5];
      rec.theorySum = tScores.reduce((a, b) => a + b, 0);
    } else {
      gradables.forEach((ir, idx) => {
        const score = Number(ir.getScore() || 0);
        const qNo = parseQuestionNo_(ir.getItem().getTitle(), idx);
        const meta = EXAM_DATA.theoryExam[qNo - 1];
        if (meta) {
          if (meta.isPostCore) postHr += score;
          if (meta.topicNo >= 1 && meta.topicNo <= 6) {
            tScores[meta.topicNo - 1] += score;
          }
        }
      });
      rec.postHr = postHr;
      rec.t1 = tScores[0]; rec.t2 = tScores[1]; rec.t3 = tScores[2];
      rec.t4 = tScores[3]; rec.t5 = tScores[4]; rec.t6 = tScores[5];
      rec.theorySum = tScores.reduce((a, b) => a + b, 0);
    }
  });

  let outSheet = ss.getSheetByName("สรุปคะแนน_Audit");
  if (!outSheet) outSheet = ss.insertSheet("สรุปคะแนน_Audit", 1);
  outSheet.clear();

  const header = [
    "รุ่น", "เลขที่", "ชื่อ-นามสกุล", "สังกัด",
    "Pre-Test (20)", "Post-Test HR (20)",
    "หัวข้อ 1 (5)", "หัวข้อ 2 (5)", "หัวข้อ 3 (5)", "หัวข้อ 4 (5)", "หัวข้อ 5 (5)", "หัวข้อ 6 (5)",
    "รวมทฤษฎี (30)"
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
      r.pre, r.postHr, r.t1, r.t2, r.t3, r.t4, r.t5, r.t6, r.theorySum
    ]);
  });
  outSheet.getRange(1, 1, rows.length, header.length).setValues(rows);
  outSheet.getRange(1, 1, 1, header.length).setFontWeight("bold");
  outSheet.setFrozenRows(1);
}
