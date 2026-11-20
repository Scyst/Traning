// Array: เก็บหลายค่าในตัวแปรเดียว
// สไลด์ 47–50 · รันด้วย: node 07-array.js

// ---------------------------------------------------------------- สร้างและอ่านค่า
const temps = [70.5, 72.1, 80.3, 68.9];

console.log(temps[0]);                 // → 70.5   index เริ่มที่ 0
console.log(temps[2]);                 // → 80.3
console.log(temps.length);             // → 4
console.log(temps[temps.length - 1]);  // → 68.9   ตัวสุดท้าย = length - 1
console.log(temps[10]);                // → undefined  อ่านเกินไม่ error แต่ได้ undefined

// ---------------------------------------------------------------- แก้ เพิ่ม ลบ
temps[0] = 71.0;                       // แก้ค่าตาม index
temps.push(75.2);                      // เพิ่มต่อท้าย
console.log(temps);                    // → [ 71, 72.1, 80.3, 68.9, 75.2 ]

const last = temps.pop();              // เอาตัวสุดท้ายออก และได้ค่านั้นกลับมา
console.log(last);                     // → 75.2
console.log(temps.length);             // → 4

// เก็บแค่ 5 ค่าล่าสุดสำหรับวาดกราฟ
const history = [];
for (const value of [1, 2, 3, 4, 5, 6, 7]) {
  history.push(value);
  if (history.length > 5) history.shift();   // shift เอาตัวแรกออก
}
console.log(history);                  // → [ 3, 4, 5, 6, 7 ]

// ---------------------------------------------------------------- วนอ่านทุกตัว
// แบบที่ 1: for นับ index
for (let i = 0; i < temps.length; i++) {
  console.log('index', i, '=', temps[i]);
}
// → index 0 = 71 ... index 3 = 68.9

// แบบที่ 2: forEach อ่านง่ายกว่า
temps.forEach((t, i) => {
  console.log(`เครื่องที่ ${i + 1}: ${t} °C`);
});
// → เครื่องที่ 1: 71 °C ... เครื่องที่ 4: 68.9 °C

// ---------------------------------------------------------------- map / filter / find
// map: แปลงทุกตัวได้ Array ใหม่ขนาดเท่าเดิม
const rounded = temps.map(t => Math.round(t));
console.log(rounded);                  // → [ 71, 72, 80, 69 ]

// filter: เลือกเฉพาะตัวที่ตรงเงื่อนไข
const hot = temps.filter(t => t > 72);
console.log(hot);                      // → [ 72.1, 80.3 ]

// find: หาตัวแรกที่ตรงเงื่อนไข
console.log(temps.find(t => t > 80));  // → 80.3

// includes: มีค่านี้ไหม
console.log(['RUNNING', 'STOP'].includes('STOP'));  // → true

// ---------------------------------------------------------------- หาค่าเฉลี่ย สูงสุด ต่ำสุด
const sum = temps.reduce((total, t) => total + t, 0);
console.log((sum / temps.length).toFixed(1));       // → 73.1
console.log(Math.max(...temps));                    // → 80.3
console.log(Math.min(...temps));                    // → 68.9
