// เงื่อนไข: if, else if, else, switch และ Logical Operator
// สไลด์ 42–46 · รันด้วย: node 06-conditions.js

// ---------------------------------------------------------------- if / else
const temp = 85;

if (temp > 80) {
  console.log('อุณหภูมิสูง');      // → อุณหภูมิสูง
} else {
  console.log('อุณหภูมิปกติ');
}

// ---------------------------------------------------------------- else if
// เช็กจากบนลงล่าง เจอเงื่อนไขแรกที่เป็นจริงแล้วหยุด จึงต้องเรียงจากค่าวิกฤตก่อน
function tempStatus(t) {
  if (t > 90) {
    return 'วิกฤต';
  } else if (t > 80) {
    return 'เตือน';
  } else {
    return 'ปกติ';
  }
}
console.log(tempStatus(95));     // → วิกฤต
console.log(tempStatus(85));     // → เตือน
console.log(tempStatus(70));     // → ปกติ

// กับดัก: เรียงผิดลำดับ ค่า 95 จะได้ 'เตือน' เพราะ t > 80 เป็นจริงก่อน
function tempStatusWrong(t) {
  if (t > 80) return 'เตือน';
  else if (t > 90) return 'วิกฤต';   // ไม่มีทางมาถึงบรรทัดนี้
  return 'ปกติ';
}
console.log(tempStatusWrong(95)); // → เตือน   ✗

// ---------------------------------------------------------------- switch
// เหมาะกับการเช็กตัวแปรเดียวที่มีค่าแน่นอน (เทียบแบบ ===)
function statusColor(status) {
  switch (status) {
    case 'RUNNING':
      return 'green';
    case 'WARNING':
      return 'yellow';
    case 'STOP':
    case 'ALARM':                  // หลาย case ใช้ผลลัพธ์เดียวกันได้
      return 'red';
    default:
      return 'gray';
  }
}
console.log(statusColor('RUNNING')); // → green
console.log(statusColor('ALARM'));   // → red
console.log(statusColor('OFFLINE')); // → gray

// ถ้าไม่ใช้ return ต้องมี break ทุก case ไม่อย่างนั้นจะทำงานต่อไปยัง case ถัดไป
let color = '';
switch ('RUNNING') {
  case 'RUNNING':
    color = 'green';
    break;                         // ลบบรรทัดนี้แล้วลองรัน จะได้ 'red'
  case 'STOP':
    color = 'red';
    break;
}
console.log(color);                // → green

// ---------------------------------------------------------------- Logical Operator
const running = true;
const voltage = 245;

console.log(running && voltage > 240);   // → true   && ต้องจริงทั้งคู่
console.log(running && voltage > 250);   // → false
console.log(!running || voltage > 240);  // → true   || จริงอย่างน้อยหนึ่ง
console.log(!running);                   // → false  ! กลับค่า

if (running && voltage > 240) {
  console.log('แจ้งเตือน: เครื่องทำงานอยู่และแรงดันเกิน');  // → แจ้งเตือน: ...
}

// ---------------------------------------------------------------- ค่าที่นับเป็นเท็จ (falsy)
// false, 0, '', null, undefined, NaN นอกนั้นเป็นจริงหมด รวมถึง '0' และ []
const inputValue = '';
if (!inputValue) {
  console.log('ยังไม่ได้กรอกค่า');   // → ยังไม่ได้กรอกค่า
}

// ---------------------------------------------------------------- เงื่อนไขสั้น (ternary)
const label = voltage > 240 ? 'เกิน' : 'ปกติ';
console.log(label);                // → เกิน
