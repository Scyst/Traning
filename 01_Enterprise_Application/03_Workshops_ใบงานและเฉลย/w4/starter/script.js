// Workshop 4: กด Start แล้วส่งแจ้งเตือนผ่าน Webhook (Trigger-based Notification)
// โค้ดของ Workshop 2–3 อยู่ด้านบนแล้ว ให้เขียนต่อในส่วน Workshop 4

const API_URL = 'data/meter.json';  // ใช้ URL เดิมจาก Workshop 3
const WEBHOOK_URL = '';             // ผู้สอนจะแจ้ง URL ช่องแจ้งเตือนของห้องเรียน
const MAX_VOLTAGE = 240;
const REFRESH_MS = 5000;

const $ = (id) => document.getElementById(id);
let running = false;

// ---------------------------------------------------------- Workshop 2.1: Start / Stop
function setStatus(isRunning) {
  running = isRunning;
  $('status').textContent = isRunning ? 'RUNNING' : 'STOP';
  $('status').className = isRunning ? 'badge run' : 'badge stop';
}

// TODO 3: ปุ่ม Start ต้องส่งแจ้งเตือนด้วย (แก้ตามข้อ 3 ด้านล่าง)
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

// ---------------------------------------------------------- Workshop 3: ดึงค่าน้ำ-ไฟจาก API
async function loadMeter() {
  try {
    const res = await fetch(API_URL, { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    $('voltage').textContent = data.electric.voltage.toFixed(1);
    $('current').textContent = data.electric.current.toFixed(1);
    $('water').textContent = data.water.flow.toFixed(1);
    $('warning').textContent = checkVoltage(data.electric.voltage);
    $('updated').textContent = 'อัปเดตล่าสุด ' + new Date().toLocaleTimeString('th-TH');
    $('updated').classList.remove('error');
  } catch (err) {
    $('updated').textContent = 'โหลดข้อมูลไม่สำเร็จ';
    $('updated').classList.add('error');
    console.error(err);
  }
}

loadMeter();
setInterval(loadMeter, REFRESH_MS);

// ---------------------------------------------------------- Workshop 4
// TODO 1: เขียน notify(title, message)
//   - fetch(WEBHOOK_URL) แบบ method: 'POST'
//   - headers: { 'Content-Type': 'application/json' }
//   - body: JSON.stringify({ title, message })
//   - ถ้า res.ok เป็น false ให้ throw new Error
async function notify(title, message) {

}

// TODO 2: ทดลองเรียก notify ใน Console ก่อน เช่น
//   notify('ทดสอบ', 'ข้อความทดสอบจากเลขที่ ...')

// TODO 3: แก้ปุ่ม Start ด้านบน ให้ทำตามลำดับนี้
//   1. ถ้า running เป็น true อยู่แล้ว ให้ return ทันที (ไม่ส่งซ้ำ)
//   2. setStatus(true)
//   3. ปิดปุ่ม (disabled = true) และแสดง 'กำลังส่งแจ้งเตือน…' ใน #notify-result
//   4. await notify('Machine started', 'Line A · เครื่องเริ่มทำงานเวลา ' + เวลาปัจจุบัน)
//   5. สำเร็จแสดง 'ส่งแจ้งเตือนแล้ว' ไม่สำเร็จแสดง 'ส่งแจ้งเตือนไม่สำเร็จ'
//   6. เปิดปุ่มกลับ (ใช้ finally)
