// สอบปฏิบัติ: The Performance Update
// อ่านโจทย์ในเอกสารสอบ แล้วเขียนโค้ดตาม TODO ห้ามเปลี่ยนชื่อฟังก์ชันและ id ใน index.html

const DATA_URL = 'data/performance.json';
const WEBHOOK_URL = '';   // ใส่ URL ที่ผู้สอนเขียนไว้บนกระดาน
const REFRESH_MS = 10000;

const $ = (id) => document.getElementById(id);
let current = null;       // เก็บข้อมูลล่าสุดที่โหลดสำเร็จ

// T3: คืนค่า Performance (%) ปัดทศนิยม 1 ตำแหน่ง ถ้า target <= 0 ให้คืน null
function calcPerformance(actual, target) {
  // TODO
}

// T3: คืน { key, text } ตามตารางในโจทย์
// key: 'ok' | 'warn' | 'bad' | 'off'
function statusOf(p) {
  // TODO
}

// T2 + T3: แสดงข้อมูลลงใน #line, #actual, #target, #defect, #performance, #status, #updated
function render(data) {
  // TODO
}

// T2: ดึงข้อมูลจาก DATA_URL ด้วย fetch แล้วเรียก render
// ถ้าผิดพลาดให้แสดง 'โหลดข้อมูลไม่สำเร็จ' ใน #message
async function loadPerformance() {
  // TODO
}

// T5: ส่ง POST แจ้งหัวหน้างานไปที่ WEBHOOK_URL พร้อมแนบชื่อผู้แจ้ง { sender, title, message }
async function sendAlert() {
  // TODO
}

// T4: โหลดข้อมูลครั้งแรก และโหลดใหม่ทุก REFRESH_MS
// TODO
