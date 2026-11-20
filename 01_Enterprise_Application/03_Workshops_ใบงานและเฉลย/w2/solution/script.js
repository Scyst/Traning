// เฉลย Workshop 2

const MAX_VOLTAGE = 240;
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
  const raw = event.target.value;            // ค่าจาก input เป็น String เสมอ
  $('warning').textContent = raw === '' ? '' : checkVoltage(Number(raw));
});
