// ============================================================================
// โค้ดประกอบการสอนตามลำดับสไลด์ที่ 39 ถึง 57 (Variable -> Function)
// วิธีรัน: node "slides_39_to_57_function.js"
// ============================================================================

// --- [สไลด์ 39] Variable (ตัวแปร) ---
let number = 2;
let number2 = 2.4;
let firstname = 'mike';
let isCheck = false;

isCheck = true;
firstname = 'newmike';
console.log('Slide 39:', { number, number2, firstname, isCheck });

// --- [สไลด์ 40] Operator (คำนวณตัวเลข) ---
let num1 = 12;
let num2 = 5;

let num3 = num1 + num2;
console.log('บวก:', num3); // 17

let num4 = num1 - num2;
console.log('ลบ:', num4);  // 7

console.log('คูณ:', num1 * num2); // 60
console.log('หาร:', num1 / num2); // 2.4
console.log('หารเอาเศษ (%):', num1 % num2); // 2

// --- [สไลด์ 41] Operator กับ String และลำดับวงเล็บ () ---
let fname = '99is';
let lname = 'test';
let fullName = fname + ' ' + lname;
console.log('name =', fullName); // 99is test

let str1 = '1';
let str2 = '2';
let combinedStr = str1 + str2;
console.log('String + String:', combinedStr); // '12'

let calc1 = 12;
let calc2 = 2 * (calc1 - 5) / 2; // 2 * (7) / 2 = 7
console.log('ลำดับการคำนวณวงเล็บ:', calc2); // 7

// --- [สไลด์ 43-44] If / Else / Else If ---
let scoreCheck = 75;
if (scoreCheck >= 80) {
  console.log('ดีมาก');
} else if (scoreCheck >= 50) {
  console.log('ผ่านเกณฑ์');
} else {
  console.log('ไม่ผ่าน');
}

// --- [สไลด์ 45] Switch Case ---
let machineStatus = 'RUNNING';
switch (machineStatus) {
  case 'RUNNING':
    console.log('เครื่องกำลังทำงาน');
    break;
  case 'STOP':
    console.log('เครื่องหยุดทำงาน');
    break;
  default:
    console.log('ไม่ทราบสถานะ');
}

// --- [สไลด์ 46] Logical Operators (&&, ||, !) ---
let a = 5;
let b = 10;

if (a > 0 && b > 0) {
  console.log('Both a and b are positive.');
} else {
  console.log('Either a or b is not positive.');
}

a = -5;
b = 10;
if (a > 0 || b > 0) {
  console.log('Either a or b is positive.');
} else {
  console.log('Both a and b are not positive.');
}

// --- [สไลด์ 47-48] Array และการเข้าถึงด้วย Index ---
let numbers = [1, 2, 3];
let names = ['99is', 'test', 'unit'];
let datas = [1, '99is', false];

console.log(names[0]); // 99is
console.log(names[1]); // test
console.log(names[2]); // unit

// --- [สไลด์ 49] Array กับ for loop และ forEach ---
for (let i = 0; i < names.length; i++) {
  console.log(i, names[i]);
}

names.forEach((name, i) => {
  console.log(i, name);
});

// --- [สไลด์ 50] Array push / pop ---
let memberList = ['anuwut', 'test'];
memberList.push('tani');
console.log('หลัง push:', memberList); // ['anuwut', 'test', 'tani']

memberList.pop();
console.log('หลัง pop:', memberList);  // ['anuwut', 'test']

// --- [สไลด์ 51-53] Object ---
let person = {
  firstname: 'John',
  lastname: 'Doe',
  age: 25
};

console.log(person.firstname); // John
console.log(person.lastname);  // Doe
console.log(person.age);       // 25

// --- [สไลด์ 54] Object + Array ---
let persons = [
  { name: '99IS', age: 24 },
  { name: 'SNC', age: 30 }
];

for (let i = 0; i < persons.length; i++) {
  console.log(persons[i].name);
  console.log(persons[i].age);
}

persons.forEach(p => {
  console.log(p.name);
  console.log(p.age);
});

// --- [สไลด์ 55-57] Function & Arrow Function (ตัวอย่างตัดเกรด) ---
function regularFunc() {
  // รูปแบบ Function ปกติ
}

const arrowFunc = () => {
  // รูปแบบ Arrow Function (ES6)
};

const calculateGrade = (score) => {
  if (score >= 90) return 'Your grade is A.';
  else if (score >= 80) return 'Your grade is B.';
  else if (score >= 70) return 'Your grade is C.';
  else if (score >= 60) return 'Your grade is D.';
  else return 'Your grade is F.';
};

let score = 85;
console.log(calculateGrade(score)); // Your grade is B.
