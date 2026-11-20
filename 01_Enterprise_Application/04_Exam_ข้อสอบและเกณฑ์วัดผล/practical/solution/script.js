// เฉลยสอบปฏิบัติ: Electrical Meter Alert (ใช้เฉพาะคำสั่งพื้นฐานที่สอนในห้อง)

let API_URL = 'data/meter.json';
let WEBHOOK_URL = '';
const STUDENT_NAME = '00-เฉลยอาจารย์';
if (window.location.protocol.startsWith('http')) {
  API_URL = '/api/meter';
  WEBHOOK_URL = '/api/notify';
}

const MAX_VOLTAGE = 240;
const MAX_CURRENT = 20;
const MIN_WATER = 1.5;

let lastSentCondition = '';
let autoTimer = null;

async function checkMachine() {
  const updatedEl = document.getElementById('updated');
  try {
    const res = await fetch(API_URL);
    if (!res.ok) {
      throw new Error('HTTP ' + res.status);
    }
    const data = await res.json();

    showMeterValues(data);

    const voltage = data.electric.voltage;
    const current = data.electric.current;
    const water = data.water.flow;
    const condition = checkCondition(voltage, current, water);

    updateStatusBadge(condition);
    await handleAlert(condition, voltage, current, water);

    updatedEl.textContent = 'อัปเดตล่าสุด ' + new Date().toLocaleTimeString('th-TH');
    updatedEl.classList.remove('error');
  } catch (err) {
    updatedEl.textContent = 'โหลดข้อมูลจาก API ไม่สำเร็จ';
    updatedEl.classList.add('error');
    console.error(err);
  }
}

function calcPower(voltage, current) {
  return voltage * current;
}

function showMeterValues(data) {
  document.getElementById('voltage').textContent = data.electric.voltage.toFixed(1);
  document.getElementById('current').textContent = data.electric.current.toFixed(1);
  document.getElementById('water').textContent = data.water.flow.toFixed(1);

  const power = calcPower(data.electric.voltage, data.electric.current);
  document.getElementById('power').textContent = power.toFixed(0);
}

function checkCondition(voltage, current, water) {
  if (voltage > MAX_VOLTAGE) {
    return 'over_volt';
  } else if (current > MAX_CURRENT) {
    return 'over_curr';
  } else if (water < MIN_WATER) {
    return 'low_water';
  } else {
    return 'normal';
  }
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

async function handleAlert(condition, voltage, current, water) {
  const resultEl = document.getElementById('notify-result');
  if (condition === 'normal') {
    lastSentCondition = '';
    resultEl.textContent = 'สถานะปกติ (ไม่ต้องส่งแจ้งเตือน)';
    resultEl.classList.remove('error');
    return;
  }

  if (condition === lastSentCondition) {
    return;
  }

  let sender = document.getElementById('student-name').value.trim();
  if (!sender) {
    sender = STUDENT_NAME.trim();
  }
  if (!sender) {
    resultEl.textContent = 'กรุณากรอกเลขที่-ชื่อก่อนส่งแจ้งเตือน';
    resultEl.classList.add('error');
    return;
  }

  if (!WEBHOOK_URL) {
    resultEl.textContent = 'ยังไม่ได้ตั้งค่า WEBHOOK_URL';
    return;
  }

  let titleText = 'แจ้งเตือนความผิดปกติ';
  if (condition === 'over_volt') {
    titleText = 'แรงดันไฟฟ้าเกิน 240 V';
  } else if (condition === 'over_curr') {
    titleText = 'กระแสไฟฟ้าเกิน 20 A';
  } else if (condition === 'low_water') {
    titleText = 'อัตราการไหลน้ำต่ำกว่า 1.5 m³/h';
  }

  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender: sender,
        condition: condition,
        title: titleText,
        message: 'V=' + voltage + ' V, A=' + current + ' A, Flow=' + water + ' m³/h'
      })
    });
    if (!res.ok) {
      throw new Error('HTTP ' + res.status);
    }
    lastSentCondition = condition;
    resultEl.textContent = 'ส่งแจ้งเตือนสำเร็จ (' + titleText + ')';
    resultEl.classList.remove('error');
  } catch (err) {
    resultEl.textContent = 'ส่งแจ้งเตือนไม่สำเร็จ';
    resultEl.classList.add('error');
    console.error(err);
  }
}

function toggleAuto(checkbox) {
  if (checkbox.checked) {
    checkMachine();
    autoTimer = setInterval(checkMachine, 5000);
  } else {
    clearInterval(autoTimer);
    autoTimer = null;
  }
}

const nameInput = document.getElementById('student-name');
if (nameInput && !nameInput.value && STUDENT_NAME) {
  nameInput.value = STUDENT_NAME;
}
