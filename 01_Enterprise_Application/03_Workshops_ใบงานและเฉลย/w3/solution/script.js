// เฉลย Workshop 3 (รวมงานจาก Workshop 2)

const API_URL = 'data/meter.json';  // หรือ API สำรองของผู้สอน เช่น http://192.168.1.10:8000/api/meter
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
    $('updated').textContent = 'โหลดข้อมูลไม่สำเร็จ';   // ค่าเดิมบนการ์ดยังอยู่
    $('updated').classList.add('error');
    console.error(err);
  }
}

loadMeter();
setInterval(loadMeter, REFRESH_MS);
