// Workshop 2: ทำให้หน้า Electrical Meter โต้ตอบได้
// HTML และ CSS เตรียมไว้ให้แล้ว เขียนเฉพาะไฟล์นี้ ห้ามเปลี่ยน id ใน index.html

const MAX_VOLTAGE = 240;
const $ = (id) => document.getElementById(id);   // ย่อ document.getElementById ให้สั้นลง

// ---------------------------------------------------------- Workshop 2.1: Start / Stop
// TODO 1: เขียนฟังก์ชัน setStatus(isRunning)
//   - true  → #status แสดง 'RUNNING' และ className = 'badge run'  (เขียว)
//   - false → #status แสดง 'STOP'    และ className = 'badge stop' (แดง)
function setStatus(isRunning) {

}

// TODO 2: ผูก Event 'click'
//   - #start-btn เรียก setStatus(true)
//   - #stop-btn  เรียก setStatus(false)


// ---------------------------------------------------------- Workshop 2.2: Simple Meter
// TODO 3: เขียนฟังก์ชัน checkVoltage(v)
//   - v มากกว่า MAX_VOLTAGE → คืนข้อความ 'Warning: แรงดันเกิน 240 V'
//   - ไม่เกิน → คืนข้อความว่าง ''
function checkVoltage(v) {

}

// TODO 4: ผูก Event 'input' ที่ #volt-input
//   - อ่านค่าจาก event.target.value (เป็น String) แปลงด้วย Number()
//   - ถ้าช่องว่าง ให้ล้าง #warning
//   - ไม่อย่างนั้นแสดงผลของ checkVoltage ใน #warning
