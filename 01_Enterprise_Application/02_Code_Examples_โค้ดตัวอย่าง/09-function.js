// Function: รวมชุดคำสั่งไว้เรียกใช้ซ้ำ
// สไลด์ 55–57 · รันด้วย: node 09-function.js

// ---------------------------------------------------------------- function แบบปกติ
// v และ a คือ parameter ส่วนค่าที่ส่งเข้าไปตอนเรียกคือ argument
function power(v, a) {
  return v * a;                        // return ส่งค่ากลับ และจบการทำงานทันที
}
console.log(power(230, 15.8));         // → 3634

// ---------------------------------------------------------------- Arrow function (ES6)
const powerArrow = (v, a) => v * a;    // บรรทัดเดียว return ให้อัตโนมัติ
console.log(powerArrow(230, 10));      // → 2300

const describe = (name, temp) => {     // หลายบรรทัดต้องเขียน return เอง
  const text = `${name}: ${temp} °C`;
  return text;
};
console.log(describe('Press A', 72.5)); // → Press A: 72.5 °C

// ---------------------------------------------------------------- ตัวอย่างในสไลด์: ตัดเกรด
function calculateGrade(score) {
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  if (score >= 50) return 'D';
  return 'F';
}
console.log(calculateGrade(85));       // → A
console.log(calculateGrade(55));       // → D

// ---------------------------------------------------------------- ตัวอย่างงานโรงงาน: เช็กแรงดัน
const MAX_VOLTAGE = 240;

function checkVoltage(v) {
  if (v > MAX_VOLTAGE) return 'เตือน';
  return 'ปกติ';
}
console.log(checkVoltage(230));        // → ปกติ
console.log(checkVoltage(240));        // → ปกติ   (240 ยังไม่เกิน)
console.log(checkVoltage(240.1));      // → เตือน

// ---------------------------------------------------------------- ค่าเริ่มต้นของ parameter
function formatTemp(temp, unit = '°C') {
  return temp.toFixed(1) + ' ' + unit;
}
console.log(formatTemp(72.456));       // → 72.5 °C
console.log(formatTemp(162.5, '°F'));  // → 162.5 °F

// ---------------------------------------------------------------- กับดัก
// ลืม return: ได้ undefined
function powerNoReturn(v, a) {
  v * a;
}
console.log(powerNoReturn(230, 10));   // → undefined

// ส่ง argument ไม่ครบ: parameter ที่ขาดเป็น undefined
console.log(power(230));               // → NaN  (230 * undefined)

// ---------------------------------------------------------------- ฟังก์ชันเป็นค่า ส่งให้ฟังก์ชันอื่นได้
// ใช้แบบนี้กับ forEach, map, addEventListener, setInterval
const readings = [230, 238, 245];
const statuses = readings.map(checkVoltage);
console.log(statuses);                 // → [ 'ปกติ', 'ปกติ', 'เตือน' ]
