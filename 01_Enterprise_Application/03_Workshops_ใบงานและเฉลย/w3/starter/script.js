// Workshop 3: ดึงค่าน้ำ-ไฟจาก API มาแสดงบน Dashboard และอัปเดตอัตโนมัติ
// โค้ดของ Workshop 2 อยู่ด้านบนแล้ว ให้เขียนต่อในส่วน Workshop 3

const API_URL = 'data/meter.json';  // ผู้สอนจะแจ้ง URL ของ API สำรองหรือ API จริง
const MAX_VOLTAGE = 240;
const REFRESH_MS = 5000;

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------- Workshop 2.1: Start / Stop
function setStatus(isRunning) {
  $('status').textContent = isRunning ? 'RUNNING' : 'STOP';
  $('status').className = isRunning ? 'badge run' : 'badge stop';
}

$('start-btn').addEventListener('click', () => setStatus(true));
$('stop-btn').addEventListener('click', () => setStatus(false));

// ---------------------------------------------------------- Workshop 2.2: Simple Meter
function checkVoltage(v) {
  return v > MAX_VOLTAGE ? `Warning: แรงดันเกิน ${MAX_VOLTAGE} V` : '';
}

$('volt-input').addEventListener('input', (event) => {
  const raw = event.target.value;
  $('warning').textContent = raw === '' ? '' : checkVoltage(Number(raw));
});

// ---------------------------------------------------------- Workshop 3
// ข้อมูลจาก API หน้าตาแบบนี้
// {
//   "line": "A",
//   "electric": { "voltage": 231.4, "current": 15.6 },
//   "water": { "flow": 3.2 },
//   "updatedAt": "2026-11-04T11:05:00+07:00"
// }

// TODO ส่วนที่ 1 (ก่อนพักเที่ยง): เขียน loadMeter()
//   1. fetch(API_URL) ด้วย async/await และตรวจ res.ok ถ้าไม่ ok ให้ throw new Error
//   2. แปลงเป็น Object ด้วย await res.json()
//   3. แสดงค่าทศนิยม 1 ตำแหน่ง (toFixed(1)) ใน #voltage, #current, #water
//   4. ถ้าเกิด error ให้แสดง 'โหลดข้อมูลไม่สำเร็จ' ใน #updated และเพิ่ม class 'error'
async function loadMeter() {

}

loadMeter();

// TODO ส่วนที่ 2 (หลังพักเที่ยง)
//   5. โหลดใหม่ทุก REFRESH_MS ด้วย setInterval
//   6. เมื่อโหลดสำเร็จ แสดง 'อัปเดตล่าสุด ' + เวลา ใน #updated และเอา class 'error' ออก
//   7. ใช้ checkVoltage กับแรงดันจาก API แล้วแสดงผลใน #warning
