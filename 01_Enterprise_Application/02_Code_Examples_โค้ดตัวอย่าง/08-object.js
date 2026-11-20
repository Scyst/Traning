// Object: เก็บข้อมูลของสิ่งหนึ่งเป็นคู่ key กับ value
// สไลด์ 51–54 · รันด้วย: node 08-object.js

// ---------------------------------------------------------------- สร้างและอ่านค่า
const machine = {
  id: 'M-01',
  name: 'Press A',
  status: 'RUNNING',
  temp: 72.5,
  alarm: null
};

console.log(machine.name);             // → Press A
console.log(machine['status']);        // → RUNNING   ใช้ [] เมื่อชื่อ key อยู่ในตัวแปร
const key = 'temp';
console.log(machine[key]);             // → 72.5
console.log(machine.speed);            // → undefined  ไม่มี key นี้

// กับดัก: อ่านต่อจาก undefined อีกชั้นจะ error
try {
  console.log(machine.speed.max);
} catch (err) {
  console.log('error:', err.message);  // → error: Cannot read properties of undefined (reading 'max')
}
console.log(machine.speed?.max);       // → undefined  ?. อ่านได้โดยไม่ error

// ---------------------------------------------------------------- แก้ เพิ่ม ลบ
machine.status = 'STOP';               // แก้
machine.operator = 'สมชาย';            // เพิ่ม key ใหม่
delete machine.alarm;                  // ลบ key
console.log(machine);
// → { id: 'M-01', name: 'Press A', status: 'STOP', temp: 72.5, operator: 'สมชาย' }

// ---------------------------------------------------------------- Object ซ้อน Object
const line = {
  name: 'A',
  power: { voltage: 230, current: 15.8 }
};
console.log(line.power.voltage);       // → 230

// ---------------------------------------------------------------- Array ของ Object (หน้าตาเหมือนข้อมูลจาก API)
const machines = [
  { id: 'M-01', status: 'RUNNING', temp: 72.5 },
  { id: 'M-02', status: 'STOP', temp: 40.1 },
  { id: 'M-03', status: 'RUNNING', temp: 81.0 }
];

console.log(machines[1].id);           // → M-02

machines.forEach(m => {
  console.log(`${m.id} · ${m.status} · ${m.temp} °C`);
});
// → M-01 · RUNNING · 72.5 °C
// → M-02 · STOP · 40.1 °C
// → M-03 · RUNNING · 81 °C

const runningCount = machines.filter(m => m.status === 'RUNNING').length;
console.log('เครื่องที่ทำงาน:', runningCount);       // → เครื่องที่ทำงาน: 2

const ids = machines.map(m => m.id);
console.log(ids);                      // → [ 'M-01', 'M-02', 'M-03' ]

// ---------------------------------------------------------------- ดู key และ value ทั้งหมด
console.log(Object.keys(line.power));    // → [ 'voltage', 'current' ]
console.log(Object.values(line.power));  // → [ 230, 15.8 ]
