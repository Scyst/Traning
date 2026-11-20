// เฉลยสอบปฏิบัติ: The Performance Update (สำหรับผู้สอนเท่านั้น)

const DATA_URL = 'data/performance.json';
const WEBHOOK_URL = 'http://10.1.9.112:8000/api/notify';   // URL ของช่องแจ้งเตือนห้องเรียน
const REFRESH_MS = 10000;

const $ = (id) => document.getElementById(id);
let current = null;       // ข้อมูลล่าสุดที่โหลดสำเร็จ
let alertSent = false;    // ส่งแจ้งเตือนรอบนี้ไปแล้วหรือยัง

// T3: Performance (%) = ผลิตได้ ÷ เป้าหมาย × 100 ปัดทศนิยม 1 ตำแหน่ง
function calcPerformance(actual, target) {
  if (!(target > 0)) return null;
  return Math.round((actual / target) * 1000) / 10;
}

// T3: ใช้ค่าที่ปัดแล้วตัดสินสถานะ
function statusOf(p) {
  if (p === null) return { key: 'off', text: 'ไม่มีข้อมูล' };
  if (p >= 85) return { key: 'ok', text: 'ปกติ' };
  if (p >= 60) return { key: 'warn', text: 'เฝ้าระวัง' };
  return { key: 'bad', text: 'ต่ำกว่าเป้า' };
}

function render(data) {
  const p = calcPerformance(data.output.actual, data.output.target);
  const status = statusOf(p);

  $('line').textContent = `Line ${data.line.name} · กะ ${data.line.shift}`;
  $('actual').textContent = data.output.actual.toLocaleString('th-TH');
  $('target').textContent = data.output.target.toLocaleString('th-TH');
  $('defect').textContent = data.defect;
  $('performance').textContent = p === null ? '–' : p.toFixed(1) + '%';
  $('status').textContent = status.text;
  $('status').className = 'status ' + status.key;
  $('updated').textContent = 'อัปเดตล่าสุด ' + new Date().toLocaleTimeString('th-TH');

  // T5: เมื่อกลับมาไม่ต่ำกว่าเป้า ให้แจ้งเตือนได้ใหม่ในครั้งถัดไป
  if (status.key !== 'bad') {
    alertSent = false;
    $('alert-result').textContent = '';
  }
  $('alert-btn').disabled = status.key !== 'bad' || alertSent;
}

// T2 + T4
async function loadPerformance() {
  try {
    const res = await fetch(DATA_URL, { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    current = await res.json();
    render(current);
    $('message').textContent = '';
  } catch (err) {
    $('message').textContent = 'โหลดข้อมูลไม่สำเร็จ';
    console.error(err);
  }
}

// T5
async function sendAlert() {
  if (!current) return;
  const senderInput = $('sender');
  const sender = senderInput ? senderInput.value.trim() : '';
  if (!sender) {
    $('alert-result').textContent = 'กรุณาระบุชื่อผู้แจ้งก่อนส่ง';
    if (senderInput) senderInput.focus();
    return;
  }
  const btn = $('alert-btn');
  btn.disabled = true;
  const { actual, target } = current.output;
  const p = calcPerformance(actual, target);
  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: sender,
        title: `Line ${current.line.name} ต่ำกว่าเป้า`,
        message: `Performance ${p.toFixed(1)}% (ผลิตได้ ${actual} จากเป้า ${target} ชิ้น)`
      })
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    alertSent = true;
    $('alert-result').textContent = `ส่งแจ้งเตือนแล้ว (โดย ${sender})`;
  } catch (err) {
    btn.disabled = false;
    $('alert-result').textContent = 'ส่งแจ้งเตือนไม่สำเร็จ';
    console.error(err);
  }
}

$('alert-btn').addEventListener('click', sendAlert);
loadPerformance();
setInterval(loadPerformance, REFRESH_MS);
