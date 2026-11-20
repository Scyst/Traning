// JSON: รูปแบบข้อความที่ระบบใช้รับส่งข้อมูลกัน
// สไลด์ 73–74, 78 · รันด้วย: node 13-json.js

// ---------------------------------------------------------------- JSON คือ "ข้อความ"
// ข้อมูลที่ได้จาก API มาเป็นข้อความแบบนี้ (สังเกต key อยู่ในเครื่องหมายคำพูดคู่เสมอ)
const text = `{
  "line": "A",
  "updatedAt": "2026-11-02T09:15:00",
  "online": true,
  "alarm": null,
  "machines": [
    { "id": "M-01", "status": "RUNNING", "temp": 72.5 },
    { "id": "M-02", "status": "STOP", "temp": 40.1 }
  ],
  "power": { "voltage": 230, "current": 15.8 }
}`;

console.log(typeof text);              // → string  ยังเป็นข้อความ อ่านทีละ key ไม่ได้

// ---------------------------------------------------------------- JSON.parse: ข้อความ → Object
const data = JSON.parse(text);
console.log(typeof data);              // → object

// อ่านค่าไล่ทีละชั้น: Object ใช้ .key ส่วน Array ใช้ [ตัวเลข]
console.log(data.line);                     // → A
console.log(data.power.voltage);            // → 230
console.log(data.machines[0].temp);         // → 72.5
console.log(data.machines[1].status);       // → STOP
console.log(data.machines.length);          // → 2
console.log(data.alarm);                    // → null

// ---------------------------------------------------------------- JSON.stringify: Object → ข้อความ
// ใช้ตอนส่ง body ไปให้ API
const payload = { title: 'Machine started', message: 'M-01 RUNNING' };
console.log(JSON.stringify(payload));
// → {"title":"Machine started","message":"M-01 RUNNING"}

console.log(JSON.stringify(data.power, null, 2));   // จัดย่อหน้าให้อ่านง่าย
// → {
//     "voltage": 230,
//     "current": 15.8
//   }

// ---------------------------------------------------------------- ชนิดข้อมูลที่ JSON เก็บได้
// string, number, boolean, null, object, array เท่านั้น
// undefined และ function จะหายไปตอน stringify
console.log(JSON.stringify({ a: 1, b: undefined, c: () => 1 }));  // → {"a":1}

// ---------------------------------------------------------------- JSON ที่ผิดรูปแบบ
const badExamples = [
  "{'line': 'A'}",          // ใช้ ' แทน "
  '{"line": "A",}',         // มี comma ตัวสุดท้าย
  '{line: "A"}',            // key ไม่มีเครื่องหมายคำพูด
  '<!DOCTYPE html>'         // ได้หน้า HTML (เช่น 404) แทน JSON
];
badExamples.forEach(bad => {
  try {
    JSON.parse(bad);
  } catch (err) {
    console.log('ผิดรูปแบบ:', bad);
  }
});
// → ผิดรูปแบบ: ... (ทั้ง 4 แบบ)
