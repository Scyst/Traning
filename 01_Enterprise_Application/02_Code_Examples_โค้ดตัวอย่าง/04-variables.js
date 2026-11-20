// ตัวแปร: let, const, var และชนิดข้อมูล
// สไลด์ 39 · รันด้วย: node 04-variables.js

// ---------------------------------------------------------------- let
// ใช้ let เมื่อค่าเปลี่ยนได้ เช่น ค่าที่อ่านจากเครื่องจักร
let voltage = 230;
voltage = 235;
console.log('voltage:', voltage);            // → voltage: 235

// ---------------------------------------------------------------- const
// ใช้ const เมื่อค่าไม่เปลี่ยน เช่น ค่าตั้งของระบบ
const MAX_VOLTAGE = 240;
console.log('MAX_VOLTAGE:', MAX_VOLTAGE);    // → MAX_VOLTAGE: 240

// กำหนดค่าใหม่ให้ const ไม่ได้
try {
  MAX_VOLTAGE = 250;
} catch (err) {
  console.log('const error:', err.message);  // → const error: Assignment to constant variable.
}

// แต่ const ที่เป็น Array หรือ Object ยังแก้ "ข้างใน" ได้
const readings = [230, 231];
readings.push(232);
console.log('readings:', readings);          // → readings: [ 230, 231, 232 ]

// ---------------------------------------------------------------- var (แบบเก่า)
// เจอในโค้ดเก่าให้รู้ว่าคือการประกาศตัวแปร แต่โค้ดใหม่ใช้ let/const แทน
var oldStyle = 'ประกาศแบบเก่า';
console.log(oldStyle);                       // → ประกาศแบบเก่า

// ---------------------------------------------------------------- ชนิดข้อมูล
const machineName = 'Press A';   // String
const temp = 72.5;               // Number (จำนวนเต็มและทศนิยมเป็นชนิดเดียวกัน)
const running = true;            // Boolean
const alarms = ['Door', 'Oil'];  // Array
const machine = { id: 'M-01' };  // Object
let note;                        // ประกาศแต่ยังไม่ใส่ค่า = undefined
const alarm = null;              // ตั้งใจให้ "ไม่มีค่า"

console.log(typeof machineName); // → string
console.log(typeof temp);        // → number
console.log(typeof running);     // → boolean
console.log(typeof alarms);      // → object   (Array ก็เป็น object)
console.log(Array.isArray(alarms)); // → true  (เช็กว่าเป็น Array ให้ใช้แบบนี้)
console.log(typeof machine);     // → object
console.log(typeof note);        // → undefined
console.log(typeof alarm);       // → object   (ข้อผิดพลาดเก่าของภาษา null ควรเป็น null)

// ---------------------------------------------------------------- ตั้งชื่อตัวแปร
// ✓ camelCase สื่อความหมาย: machineName, maxVoltage, isRunning
// ✓ ค่าคงที่ของระบบมักเขียนตัวใหญ่: MAX_VOLTAGE, REFRESH_MS
// ✗ ห้ามขึ้นต้นด้วยตัวเลข ห้ามมีเว้นวรรค: 1st, max voltage
// ✗ ชื่อไม่สื่อ: a, x1, data2
