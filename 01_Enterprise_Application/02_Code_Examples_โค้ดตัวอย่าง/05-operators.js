// Operator: คำนวณ ต่อข้อความ และเปรียบเทียบ
// สไลด์ 40–42 · รันด้วย: node 05-operators.js

// ---------------------------------------------------------------- คำนวณ
const voltage = 230;
const current = 15.8;

console.log(voltage + 10);       // → 240
console.log(voltage - 10);       // → 220
console.log(voltage * current);  // → 3634
console.log(voltage / 2);        // → 115
console.log(17 % 5);             // → 2   (หารเอาเศษ)
console.log(10 % 2 === 0);       // → true  (ใช้ % เช็กเลขคู่)

// ลำดับการคำนวณ: ในวงเล็บก่อน แล้ว * / ก่อน + -
console.log(2 + 3 * 4);          // → 14
console.log((2 + 3) * 4);        // → 20

// ---------------------------------------------------------------- ต่อข้อความ
console.log('Line ' + 'A');                    // → Line A
console.log('แรงดัน ' + voltage + ' V');        // → แรงดัน 230 V
console.log(`แรงดัน ${voltage} V`);             // → แรงดัน 230 V   (template literal ใช้ backtick)

// ---------------------------------------------------------------- กับดัก: String + Number
// ถ้ามี String อยู่ฝั่งใดฝั่งหนึ่งของ + จะกลายเป็นการต่อข้อความ
console.log('10' + 5);           // → 105
console.log('10' - 5);           // → 5     (เครื่องหมาย - แปลงเป็นตัวเลขให้)
console.log('10' * 2);           // → 20

// ค่าจากช่อง input เป็น String เสมอ ต้องแปลงก่อนคำนวณ
const fromInput = '230';
console.log(fromInput + 10);           // → 23010   ✗
console.log(Number(fromInput) + 10);   // → 240     ✓
console.log(Number(''));               // → 0       ระวัง: ช่องว่างกลายเป็น 0
console.log(Number('12V'));            // → NaN     แปลงไม่ได้ (Not a Number)
console.log(parseFloat('12.5V'));      // → 12.5    อ่านตัวเลขด้านหน้าได้

// ทศนิยมในคอมพิวเตอร์ไม่ตรงเป๊ะ ใช้ toFixed ตอนแสดงผล
console.log(0.1 + 0.2);                // → 0.30000000000000004
console.log((0.1 + 0.2).toFixed(2));   // → 0.30

// ---------------------------------------------------------------- เปรียบเทียบ (ได้ true/false)
console.log(10 > 5);             // → true
console.log(3 < 1);              // → false
console.log(10 >= 10);           // → true
console.log(5 <= 2);             // → false
console.log(5 !== 2);            // → true

// == แปลงชนิดก่อนเทียบ ผลคาดเดายาก ให้ใช้ === เสมอ
console.log('5' == 5);           // → true
console.log('5' === 5);          // → false  ✓ เทียบทั้งค่าและชนิด
console.log(0 == '');            // → true   (ตัวอย่างที่ทำให้สับสน)
