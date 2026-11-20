/**
 * ตัวอย่าง System Test อัตโนมัติ: ตรวจว่า API สำรองตอบข้อมูลถูกต้องและรับแจ้งเตือนได้
 * ดัดแปลงจาก module-5-testing-qa/templates/system-test-example.js ของ repo ทีม
 *
 * รัน: node system-test-example.js   (หรือ node system-test-example.js http://192.168.1.10:8000)
 * ต้องเปิด API สำรอง (mock_api.py) ก่อน
 * ใช้ Node.js 18 ขึ้นไป (มี fetch ในตัว)
 */

const API_BASE = process.argv[2] || "http://localhost:8000";

let passed = 0;
let failed = 0;

function check(name, condition) {
  if (condition) {
    console.log("  PASS:", name);
    passed++;
  } else {
    console.log("  FAIL:", name);
    failed++;
  }
}

async function runTests() {
  console.log("System test: API สำรองที่ " + API_BASE + "\n");

  try {
    const res = await fetch(API_BASE + "/api/meter");
    check("GET /api/meter ตอบ 200", res.status === 200);
    const data = await res.json();
    check("มี electric.voltage เป็นตัวเลข", typeof data.electric?.voltage === "number");
    check("มี electric.current เป็นตัวเลข", typeof data.electric?.current === "number");
    check("มี water.flow เป็นตัวเลข", typeof data.water?.flow === "number");
    check("แรงดันอยู่ในช่วงที่เป็นไปได้ (200–260 V)", data.electric.voltage >= 200 && data.electric.voltage <= 260);

    const ok = await fetch(API_BASE + "/api/notify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "System test", message: "ทดสอบจาก system-test-example.js" })
    });
    check("POST /api/notify ที่ถูกต้องตอบ 200", ok.status === 200);

    const bad = await fetch(API_BASE + "/api/notify", { method: "POST", body: "[object Object]" });
    check("POST ที่ไม่ใช่ JSON ตอบ 400", bad.status === 400);

    const missing = await fetch(API_BASE + "/api/nope");
    check("URL ที่ไม่มีอยู่ตอบ 404", missing.status === 404);
  } catch (err) {
    console.log("  FAIL: ติดต่อ API ไม่ได้ เปิด mock_api.py แล้วหรือยัง?", err.message);
    failed++;
  }

  console.log("\nผล: ผ่าน " + passed + " ไม่ผ่าน " + failed);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
