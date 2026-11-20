// ข้อสอบปฏิบัติ: Electrical Meter Alert (แก้ไขในจุด TODO 1 ถึง TODO 5)

// TODO 1 (10 คะแนน): ใส่ API_URL, WEBHOOK_URL และชื่อผู้สอบ (เช่น '01-สมชาย')
const API_URL = 'data/meter.json';
const WEBHOOK_URL = '';
const STUDENT_NAME = '';

// เกณฑ์มาตรฐานสำหรับตรวจสอบเงื่อนไข
const MAX_VOLTAGE = 240;     // V
const MAX_CURRENT = 20;      // A
const MIN_WATER = 1.5;       // m3/h

let lastSentCondition = '';  // เก็บสถานะล่าสุดที่ส่งแจ้งเตือนแล้ว
let autoTimer = null;

// ฟังก์ชันหลักสำหรับดึงค่าและเรียกตรวจตามลำดับ (ส่วนนี้ไม่ต้องแก้ไข)
async function checkMachine() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) {
      throw new Error('HTTP ' + res.status);
    }
    const data = await res.json();

    // แสดงค่าบนการ์ด (TODO 2 และ TODO 3)
    showMeterValues(data);

    // ตรวจเงื่อนไข (TODO 4) แล้วอัปเดตป้ายสถานะ
    const voltage = data.electric.voltage;
    const current = data.electric.current;
    const water = data.water.flow;
    const condition = checkCondition(voltage, current, water);

    updateStatusBadge(condition);

    // ส่งแจ้งเตือนเมื่อพบค่าผิดปกติ (TODO 5)
    await handleAlert(condition, voltage, current, water);

    const updatedEl = document.getElementById('updated');
    updatedEl.textContent = 'อัปเดตล่าสุด ' + new Date().toLocaleTimeString('th-TH');
    updatedEl.classList.remove('error');
  } catch (err) {
    const updatedEl = document.getElementById('updated');
    updatedEl.textContent = 'โหลดข้อมูลจาก API ไม่สำเร็จ';
    updatedEl.classList.add('error');
    console.error(err);
  }
}

// TODO 3 (10 คะแนน): คำนวณและคืนค่ากำลังไฟฟ้า (หน่วย W)
function calcPower(voltage, current) {
  return 0;
}

// TODO 2 (10 คะแนน): นำค่า voltage, current และ water flow จาก data มาแสดงในหน้าเว็บ
// โครงสร้างข้อมูล API: data.electric.voltage, data.electric.current, data.water.flow
function showMeterValues(data) {

  const power = calcPower(data.electric.voltage, data.electric.current);
  document.getElementById('power').innerText = power.toFixed(0);
}

// TODO 4 (10 คะแนน): ตรวจสอบเงื่อนไขและคืนค่าสถานะ
// ค่าที่ต้องคืน: 'over_volt' (>240V), 'over_curr' (>20A), 'low_water' (<1.5), หรือ 'normal'
function checkCondition(voltage, current, water) {

  return 'normal';
}

function updateStatusBadge(condition) {
  const badge = document.getElementById('status');
  if (condition === 'over_volt') {
    badge.textContent = 'แรงดันเกิน (> 240 V)';
    badge.className = 'badge bad';
  } else if (condition === 'over_curr') {
    badge.textContent = 'กระแสเกิน (> 20 A)';
    badge.className = 'badge warn';
  } else if (condition === 'low_water') {
    badge.textContent = 'น้ำไหลต่ำ (< 1.5)';
    badge.className = 'badge blue';
  } else {
    badge.textContent = 'ปกติ';
    badge.className = 'badge ok';
  }
}

// TODO 5 (10 คะแนน): ส่งแจ้งเตือนแบบ POST ไปที่ WEBHOOK_URL เมื่อสถานะผิดปกติ
// ส่ง JSON { sender, condition, title, message } และเช็ก lastSentCondition เพื่อไม่ให้ส่งซ้ำเมื่อสถานะเดิมค้างอยู่
async function handleAlert(condition, voltage, current, water) {
  const resultEl = document.getElementById('notify-result');
  if (condition === 'normal') {
    lastSentCondition = '';
    resultEl.textContent = 'สถานะปกติ (ไม่ต้องส่งแจ้งเตือน)';
    return;
  }

  // เขียนโค้ดส่งแจ้งเตือนต่อจากตรงนี้

}

// เปิด-ปิดโหมดตรวจสอบอัตโนมัติ (ไม่ต้องแก้ไข)
function toggleAuto(checkbox) {
  if (checkbox.checked) {
    checkMachine();
    autoTimer = setInterval(checkMachine, 5000);
  } else {
    clearInterval(autoTimer);
    autoTimer = null;
  }
}

// เติมชื่อจาก STUDENT_NAME ลงในช่อง input ถ้ามีการกำหนดไว้
const nameInput = document.getElementById('student-name');
if (nameInput && !nameInput.value && STUDENT_NAME) {
  nameInput.value = STUDENT_NAME;
}
