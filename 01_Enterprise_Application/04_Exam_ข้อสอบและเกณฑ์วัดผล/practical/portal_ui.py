"""HTML UI Templates for BOI Unified Classroom Server v2 (Instructor + Student Portal + PIN Login).

All dynamic templates sanitize user-supplied text via esc() before DOM insertion.
"""

OFFLINE_QR_JS = r"""
const OfflineQR = (function () {
  const GF_EXP = new Uint8Array(512), GF_LOG = new Uint8Array(256);
  let x = 1;
  for (let i = 0; i < 255; i++) { GF_EXP[i] = x; GF_LOG[x] = i; x <<= 1; if (x & 0x100) x ^= 0x11d; }
  for (let i = 255; i < 512; i++) GF_EXP[i] = GF_EXP[i - 255];
  const gfMul = (a, b) => (a === 0 || b === 0) ? 0 : GF_EXP[GF_LOG[a] + GF_LOG[b]];
  const polyMul = (p, q) => {
    const r = new Uint8Array(p.length + q.length - 1);
    for (let i = 0; i < p.length; i++) for (let j = 0; j < q.length; j++) r[i + j] ^= gfMul(p[i], q[j]);
    return r;
  };
  const rsGen = (deg) => { let g = new Uint8Array([1]); for (let i = 0; i < deg; i++) g = polyMul(g, new Uint8Array([1, GF_EXP[i]])); return g; };
  const rsEnc = (data, ec) => {
    const gen = rsGen(ec), buf = new Uint8Array(data.length + ec);
    buf.set(data, 0);
    for (let i = 0; i < data.length; i++) {
      const f = buf[i];
      if (f !== 0) for (let j = 0; j < gen.length; j++) buf[i + j] ^= gfMul(gen[j], f);
    }
    return buf.slice(data.length);
  };
  const SPECS_M = [
    null,
    [1,16,10,1,16,0,0,[]], [2,28,16,1,28,0,0,[6,18]], [3,44,26,1,44,0,0,[6,22]],
    [4,64,18,2,32,0,0,[6,26]], [5,86,24,2,43,0,0,[6,30]], [6,108,16,4,27,0,0,[6,34]],
    [7,124,18,4,31,0,0,[6,22,38]], [8,154,22,2,38,2,39,[6,24,42]],
  ];
  function encodeMatrix(text) {
    const utf8 = new TextEncoder().encode(String(text || ' '));
    let spec = null;
    for (let v = 1; v < SPECS_M.length; v++) {
      if (Math.ceil((utf8.length * 8 + 16) / 8) <= SPECS_M[v][1]) { spec = SPECS_M[v]; break; }
    }
    if (!spec) return null;
    const [ver, totalData, ecB, g1B, g1D, g2B, g2D, alignPos] = spec;
    const bits = [];
    const pushBits = (val, len) => { for (let i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); };
    pushBits(4, 4); pushBits(utf8.length, 8);
    for (const b of utf8) pushBits(b, 8);
    pushBits(0, Math.min(4, totalData * 8 - bits.length));
    while (bits.length % 8 !== 0) bits.push(0);
    let pad = 0;
    while (bits.length < totalData * 8) { pushBits(pad ? 0x11 : 0xec, 8); pad ^= 1; }
    const cw = new Uint8Array(totalData);
    for (let i = 0; i < totalData; i++) { let b = 0; for (let j = 0; j < 8; j++) b = (b << 1) | bits[i * 8 + j]; cw[i] = b; }
    const dBlks = [], eBlks = [];
    let off = 0;
    for (let i = 0; i < g1B; i++) { const s = cw.slice(off, off + g1D); off += g1D; dBlks.push(s); eBlks.push(rsEnc(s, ecB)); }
    for (let i = 0; i < g2B; i++) { const s = cw.slice(off, off + g2D); off += g2D; dBlks.push(s); eBlks.push(rsEnc(s, ecB)); }
    const out = [];
    for (let i = 0; i < Math.max(g1D, g2D); i++) for (const b of dBlks) if (i < b.length) out.push(b[i]);
    for (let i = 0; i < ecB; i++) for (const b of eBlks) out.push(b[i]);
    const size = ver * 4 + 17;
    const mat = Array.from({ length: size }, () => new Int8Array(size).fill(-1));
    const isFunc = Array.from({ length: size }, () => new Uint8Array(size));
    const setF = (r, c, v) => { if (r >= 0 && r < size && c >= 0 && c < size) { mat[r][c] = v ? 1 : 0; isFunc[r][c] = 1; } };
    const finder = (r0, c0) => {
      for (let dr = -1; dr <= 7; dr++) for (let dc = -1; dc <= 7; dc++) {
        const rr = r0 + dr, cc = c0 + dc;
        if (rr < 0 || rr >= size || cc < 0 || cc >= size) continue;
        const ok = dr >= 0 && dr <= 6 && dc >= 0 && dc <= 6;
        setF(rr, cc, ok && (dr === 0 || dr === 6 || dc === 0 || dc === 6 || (dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4)));
      }
    };
    finder(0, 0); finder(0, size - 7); finder(size - 7, 0);
    for (const r of alignPos) for (const c of alignPos) {
      if (isFunc[r][c]) continue;
      for (let dr = -2; dr <= 2; dr++) for (let dc = -2; dc <= 2; dc++) setF(r + dr, c + dc, Math.abs(dr) === 2 || Math.abs(dc) === 2 || (!dr && !dc));
    }
    for (let i = 8; i < size - 8; i++) { if (!isFunc[6][i]) setF(6, i, i % 2 === 0); if (!isFunc[i][6]) setF(i, 6, i % 2 === 0); }
    setF(4 * ver + 9, 8, 1);
    for (let i = 0; i < 9; i++) { if (!isFunc[8][i]) setF(8, i, 0); if (!isFunc[i][8]) setF(i, 8, 0); }
    for (let i = 0; i < 8; i++) { if (!isFunc[8][size - 1 - i]) setF(8, size - 1 - i, 0); if (!isFunc[size - 1 - i][8]) setF(size - 1 - i, 8, 0); }
    if (ver >= 7) {
      let vb = ver << 12;
      for (let i = 5; i >= 0; i--) if ((vb >>> (12 + i)) & 1) vb ^= (0x1f25 << i);
      const vi = (ver << 12) | vb;
      for (let i = 0; i < 18; i++) { const b = (vi >>> i) & 1, p = Math.floor(i / 3), q = size - 11 + (i % 3); setF(p, q, b); setF(q, p, b); }
    }
    let bi = 0, dir = -1;
    for (let col = size - 1; col >= 1; col -= 2) {
      if (col === 6) col--;
      for (let st = 0; st < size; st++) {
        const r = dir === -1 ? (size - 1 - st) : st;
        for (let dc = 0; dc < 2; dc++) {
          const c = col - dc;
          if (!isFunc[r][c]) {
            mat[r][c] = bi < out.length * 8 ? ((out[bi >> 3] >>> (7 - (bi & 7))) & 1) : 0;
            bi++;
          }
        }
      }
      dir = -dir;
    }
    const grid = mat.map((row, r) => row.map((v, c) => (isFunc[r][c] ? v : (((r + c) % 2 === 0) ? (v ^ 1) : v))));
    const fmtBits = 0 ^ 0x5412;
    const fmtBit = (k) => (fmtBits >>> k) & 1;
    const tlH = [0,1,2,3,4,5,7,8], tlV = [7,5,4,3,2,1,0];
    for (let i = 0; i < 8; i++) grid[8][tlH[i]] = fmtBit(14 - i);
    for (let i = 0; i < 7; i++) grid[tlV[i]][8] = fmtBit(6 - i);
    for (let i = 0; i < 7; i++) grid[size - 1 - i][8] = fmtBit(14 - i);
    for (let i = 0; i < 8; i++) grid[8][size - 8 + i] = fmtBit(7 - i);
    return grid;
  }
  function toSvg(text, px = 112) {
    const g = encodeMatrix(text);
    if (!g) return '';
    const n = g.length, t = n + 4;
    let d = '';
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (g[r][c]) d += `M${c + 2},${r + 2}h1v1h-1z`;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${px}" height="${px}" viewBox="0 0 ${t} ${t}" shape-rendering="crispEdges"><rect width="${t}" height="${t}" fill="#fff"/><path d="${d}" fill="#0f172a"/></svg>`;
  }
  return { toSvg };
})();
"""


PIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>เข้าสู่ระบบผู้สอน · BOI Classroom Server</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #0f172a; color: #e2e8f0; font-family: "Leelawadee UI", Tahoma, sans-serif; padding: 20px; }
  .box { width: 100%; max-width: 400px; background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 24px; }
  h1 { margin: 0 0 8px; font-size: 20px; color: #38bdf8; }
  p { margin: 0 0 16px; color: #94a3b8; font-size: 14px; line-height: 1.5; }
  input { width: 100%; min-height: 44px; padding: 10px 12px; border-radius: 8px; border: 1px solid #475569;
    background: #0f172a; color: #f8fafc; font-size: 16px; margin-bottom: 12px; }
  button { width: 100%; min-height: 44px; border: 0; border-radius: 8px; background: #0284c7; color: #fff;
    font: inherit; font-weight: 700; cursor: pointer; font-size: 15px; }
  .err { color: #f87171; font-size: 13px; margin-top: 10px; min-height: 18px; }
  .stu { display: block; text-align: center; margin-top: 14px; color: #93c5fd; font-size: 13px; }
</style>
</head>
<body>
  <div class="box">
    <h1>🔒 เฉพาะผู้สอน (Instructor Dashboard)</h1>
    <p>คุณกำลังเปิดหน้าควบคุมจากเครื่องอื่นบน Wi-Fi กรุณากรอก PIN ผู้สอนที่แสดงบนหน้าจอ Terminal ของเครื่องแม่</p>
    <input id="pin" type="password" placeholder="รหัส PIN ผู้สอน" autofocus onkeydown="if (event.key==='Enter') login()">
    <button onclick="login()">เข้าสู่ระบบ</button>
    <div id="err" class="err"></div>
    <a class="stu" href="/download">➡️ หากเป็นผู้เรียน กดไปหน้าโหลด/ส่งงานที่นี่</a>
  </div>
<script>
async function login() {
  const errEl = document.getElementById('err');
  errEl.textContent = '';
  const pin = document.getElementById('pin').value.trim();
  const res = await fetch('/api/auth', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin })
  });
  const data = await res.json();
  if (res.ok && data.ok) { location.reload(); return; }
  errEl.textContent = data.error || 'PIN ไม่ถูกต้อง';
}
</script>
</body>
</html>
"""


MONITOR_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BOI Classroom Portal v2 · กระดานควบคุมและตรวจผลอัตโนมัติ</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 16px 20px; font-family: "Leelawadee UI", "Sarabun", Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; }
  .top { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 14px; }
  h1 { margin: 0; font-size: 21px; color: #38bdf8; }
  .urls { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; margin-bottom: 14px; }
  .url-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .url-box small { display: block; color: #94a3b8; font-size: 12px; }
  .url-box code { color: #fde047; font-size: 13.5px; font-weight: 700; word-break: break-all; }
  .btn { background: #1e293b; color: #f1f5f9; border: 1px solid #475569; border-radius: 8px; padding: 8px 12px; min-height: 38px; font: inherit; font-weight: 700; cursor: pointer; font-size: 13px; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; }
  .btn:hover { background: #334155; }
  .btn.active { outline: 2px solid #38bdf8; background: #0c4a6e; }
  .btn.green { background: #14532d; border-color: #22c55e; }
  .btn.red { background: #7f1d1d; border-color: #ef4444; }
  .btn.orange { background: #7c2d12; border-color: #f97316; }
  .btn.blue { background: #1e3a8a; border-color: #3b82f6; }
  .btn.amber { background: #78350f; border-color: #f59e0b; }
  .panel { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; }
  .panel h2 { margin: 0 0 10px; font-size: 15.5px; color: #93c5fd; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .live-vals { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; padding: 9px 12px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 14px; }
  .live-vals b { color: #fde047; }
  .grid-2 { display: grid; grid-template-columns: 1.45fr 1fr; gap: 14px; }
  @media (max-width: 1080px) { .grid-2 { grid-template-columns: 1fr; } }
  .tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .tab-btn { padding: 8px 16px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #94a3b8; font: inherit; font-weight: 700; cursor: pointer; }
  .tab-btn.active { background: #0284c7; color: #fff; border-color: #38bdf8; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { border: 1px solid #334155; padding: 7px 8px; text-align: center; }
  th { background: #0f172a; color: #cbd5e1; }
  td.name { text-align: left; font-weight: 700; }
  .ok-cell { background: #064e3b; color: #6ee7b7; font-weight: 700; }
  .wait-cell { color: #64748b; }
  .err-cell { color: #fca5a5; font-weight: 700; }
  .feed { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .feed-item { padding: 9px 11px; border-radius: 8px; background: #0f172a; border-left: 4px solid #22c55e; font-size: 12.5px; }
  .feed-item.bad { border-left-color: #ef4444; background: #2d1216; }
  .feed-item.warn { border-left-color: #f59e0b; background: #2c210e; }
  .help-card { padding: 10px 12px; border-radius: 10px; background: #2a1810; border: 1px solid #f97316; margin-bottom: 8px; }
  .help-card.resolved { background: #0f172a; border-color: #334155; opacity: 0.85; }
  .tag { display: inline-block; padding: 2px 7px; border-radius: 99px; font-size: 11px; font-weight: 700; background: #fde047; color: #0f172a; margin-right: 5px; }
  .roster-box { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
  .roster-box input, .inline-input { flex: 1; min-width: 200px; min-height: 38px; padding: 7px 10px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; font: inherit; }
  .modal-backdrop { display: none; position: fixed; inset: 0; background: rgba(2,6,23,0.82); z-index: 50; padding: 24px; align-items: center; justify-content: center; }
  .modal-backdrop.open { display: flex; }
  .modal-box { width: 100%; max-width: 980px; max-height: 90vh; background: #1e293b; border: 1px solid #475569; border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; }
  .modal-head { padding: 12px 16px; border-bottom: 1px solid #334155; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; }
  .modal-body { margin: 0; padding: 14px 16px; overflow: auto; background: #0b1120; color: #e2e8f0; font-family: Consolas, monospace; font-size: 13px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
</style>
</head>
<body>
  <div class="top">
    <div>
      <h1>🎛️ BOI Classroom Portal v2 · ศูนย์ควบคุมผู้สอน (Workshop 1–4 + สอบปฏิบัติ + คิวช่วย + Auto-Grade)</h1>
      <div style="color:#94a3b8;font-size:13px;">เซิร์ฟเวอร์เดียวใช้ได้ทั้ง 4 วัน · PIN เครื่องอื่น: <b id="pin-hint" style="color:#fde047;">ดูใน Terminal</b></div>
    </div>
    <div class="controls">
      <a class="btn" href="/notifications" target="_blank">🔔 จอแจ้งเตือน</a>
      <a class="btn" href="/prompt" target="_blank">📋 โจทย์ขึ้นจอ</a>
      <a class="btn" href="/theory-exam" target="_blank">📝 ข้อสอบทฤษฎี LAN</a>
      <a class="btn" href="/links" target="_blank">🔗 ลิงก์/QR</a>
      <a class="btn" href="/solution/" target="_blank">👀 เฉลย (เฉพาะผู้สอน)</a>
      <a class="btn" href="/api/submissions.zip">📦 โหลดไฟล์ทั้งหมด (.zip)</a>
      <button class="btn red" onclick="resetProgress()">🗑️ ล้างผลรุ่นนี้</button>
    </div>
  </div>

  <div class="urls">
    <div class="url-box">
      <div><small>1) ลิงก์ผู้เรียน (โหลด/ส่ง Workshop &amp; สอบ &amp; เรียกช่วย)</small><code id="dl-url"></code></div>
      <div style="display:flex;align-items:center;gap:8px;">
        <div id="dl-qr" style="background:#fff;padding:3px;border-radius:6px;line-height:0;"></div>
        <button class="btn" onclick="copyText('dl-url', this)">คัดลอก</button>
      </div>
    </div>
    <div class="url-box">
      <div><small>2) API_URL (ดึงค่ามิเตอร์)</small><code id="api-url"></code></div>
      <button class="btn" onclick="copyText('api-url', this)">คัดลอก</button>
    </div>
    <div class="url-box">
      <div><small>3) WEBHOOK_URL (ส่งแจ้งเตือน)</small><code id="wh-url"></code></div>
      <button class="btn" onclick="copyText('wh-url', this)">คัดลอก</button>
    </div>
  </div>

  <div class="panel">
    <h2>
      <span>📡 ควบคุมสถานการณ์ API มิเตอร์ (GET /api/meter — ปิดคีย์ scenario กันโกงแล้ว)</span>
      <span class="controls">
        <span style="font-size:13px;color:#cbd5e1;">โหมดหน้าเรียน:</span>
        <button class="btn" data-cs="workshop" onclick="setClassStage('workshop')">📚 ช่วง Workshop (W1–W4)</button>
        <button class="btn" data-cs="exam" onclick="setClassStage('exam')">⚡ ช่วงสอบปฏิบัติ Final</button>
      </span>
    </h2>
    <div class="controls">
      <button class="btn green" data-sc="normal" onclick="setScenario('normal')">🟢 ปกติ</button>
      <button class="btn red" data-sc="over_volt" onclick="setScenario('over_volt')">🔴 แรงดันเกิน (&gt;240V)</button>
      <button class="btn orange" data-sc="over_curr" onclick="setScenario('over_curr')">🟠 กระแสเกิน (&gt;20A)</button>
      <button class="btn blue" data-sc="low_water" onclick="setScenario('low_water')">🔵 น้ำต่ำ (&lt;1.5)</button>
      <span style="margin-left:6px;color:#94a3b8;font-size:13px;">การจ่ายค่า:</span>
      <button class="btn" data-mode="manual" onclick="setMode('manual')">✋ กดเอง</button>
      <button class="btn" data-mode="auto_cycle" onclick="setMode('auto_cycle')">🔁 วนทุก 15 วิ</button>
      <button class="btn" data-mode="auto_random" onclick="setMode('auto_random')">🎲 สุ่มทุก 15 วิ</button>
    </div>
    <div class="live-vals" id="live-vals">กำลังเชื่อมต่อเซิร์ฟเวอร์...</div>
  </div>

  <div class="grid-2">
    <div>
      <div class="tabs">
        <button class="tab-btn active" id="tab-exam" onclick="switchTab('exam')">⚡ ผลสอบปฏิบัติ &amp; Auto-Grader (50)</button>
        <button class="tab-btn" id="tab-ws" onclick="switchTab('ws')">📚 ติดตาม Workshop 1–4 (20)</button>
        <button class="tab-btn" id="tab-audit" onclick="switchTab('audit')">📊 รวมคะแนนออก Excel Audit v2 (100)</button>
      </div>

      <div class="panel" id="panel-exam">
        <h2>
          <span>✅ ตารางสอบปฏิบัติ + Auto-Grader (<span id="student-count">0</span> คน)</span>
          <span class="controls">
            <button class="btn blue" onclick="runAutoGradeAll()">🤖 Auto-Grade ทั้งห้อง</button>
            <button class="btn" onclick="exportCSV()">⬇️ Export CSV ปฏิบัติ</button>
          </span>
        </h2>
        <div class="roster-box">
          <input id="roster-input" type="text" placeholder="เพิ่มรายชื่อผู้เรียนล่วงหน้าคั่นด้วยจุลภาค เช่น 01-รุ่งวดี, 02-ณัฐสุภา">
          <button class="btn" onclick="addRoster()">+ เพิ่มรายชื่อ</button>
        </div>
        <div style="overflow-x:auto;">
          <table>
            <thead>
              <tr>
                <th>ผู้เรียน</th><th>V&gt;240</th><th>A&gt;20</th><th>W&lt;1.5</th>
                <th>พลาด</th><th>Help ปฏิบัติ</th><th>ไฟล์ส่ง / โค้ด</th><th>Auto-Grade (50)</th>
              </tr>
            </thead>
            <tbody id="student-tbody"><tr><td colspan="8" style="color:#64748b;">รอข้อมูล...</td></tr></tbody>
          </table>
        </div>
      </div>

      <div class="panel" id="panel-ws" style="display:none;">
        <h2>
          <span>📚 ตารางส่งงาน Workshop 1–4 (<span id="ws-count">0</span> คน)</span>
          <span class="controls">
            <button class="btn blue" onclick="runAutoGradeWorkshops()">🤖 ตรวจโค้ด Workshop 1–4</button>
          </span>
        </h2>
        <div style="overflow-x:auto;">
          <table>
            <thead>
              <tr><th>ผู้เรียน</th><th>W1 (5)</th><th>W2 (5)</th><th>W3 (5)</th><th>W4 (5)</th><th>Help WS</th><th>รวม WS (20)</th></tr>
            </thead>
            <tbody id="ws-tbody"><tr><td colspan="7" style="color:#64748b;">ยังไม่มีข้อมูล Workshop...</td></tr></tbody>
          </table>
        </div>
      </div>

      <div class="panel" id="panel-audit" style="display:none;">
        <h2>
          <span>📊 รวมคะแนนทุกหมวด &amp; ดาวน์โหลด Excel Audit v2 (Leelawadee UI พร้อมทำ PDF)</span>
        </h2>
        <p style="font-size:13px;color:#cbd5e1;margin:0 0 10px;">
          1. แนบไฟล์ <strong>.csv</strong> ที่ดาวน์โหลดจาก Google Sheet แท็บ <code>สรุปคะแนน_Audit</code> (ถ้าสอบทฤษฎีผ่าน LAN ระบบจะรวมให้อัตโนมัติอยู่แล้ว · พบใน LAN: <b id="theory-count">0</b> คน)<br>
          2. ระบุชื่อรุ่น แล้วกดสร้างไฟล์ <strong>.xlsx</strong> (รวม ทฤษฎี 30 + Workshop 20 + ปฏิบัติ 50 = 100 + ชีตหลักฐาน Help Log)
        </p>
        <div class="controls" style="margin-bottom:10px;">
          <input id="audit-cohort" class="inline-input" type="text" value="รุ่นที่ 4" placeholder="ชื่อรุ่น เช่น รุ่นที่ 4">
          <input id="theory-csv-file" type="file" accept=".csv" style="color:#cbd5e1;">
          <button class="btn green" onclick="downloadAuditExcel()">📥 สร้าง &amp; ดาวน์โหลด Excel Audit v2 (.xlsx)</button>
        </div>
        <div id="audit-msg" style="font-size:13px;color:#93c5fd;"></div>
      </div>
    </div>

    <div>
      <div class="panel">
        <h2>
          <span>🙋 คิวขอความช่วยเหลือ (<span id="help-wait-count">0</span> รอดำเนินการ)</span>
          <label style="font-size:12px;color:#cbd5e1;display:inline-flex;align-items:center;gap:5px;cursor:pointer;">
            <input type="checkbox" id="sound-toggle" checked> เสียงเตือน
          </label>
        </h2>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">
          กติกา: 🛠️ เทคนิคฟรี (0) | 💡 ชี้แนะ (WS: 2 ครั้งแรกฟรี ถัดไป -0.5; สอบ: -0.5, -1, -1.5, -0.5...) | 🧑‍💻 แก้โค้ด (-1 WS / -2 สอบ) · เพดานหักสูงสุด WS 5 / สอบ 10 (กันเหลือ >=60%)
        </div>
        <div id="help-box" style="max-height:300px;overflow-y:auto;"></div>
      </div>

      <div class="panel">
        <h2><span>🔔 แจ้งเตือน Webhook สด (<span id="feed-count">0</span>)</span></h2>
        <div class="feed" id="feed-box"></div>
      </div>
    </div>
  </div>

  <div class="modal-backdrop" id="code-modal" onclick="if (event.target === this) closeCodeModal()">
    <div class="modal-box">
      <div class="modal-head">
        <div>
          <strong id="code-modal-title" style="color:#38bdf8;">ไฟล์งานผู้เรียน</strong>
          <div id="code-modal-sub" style="font-size:12px;color:#94a3b8;"></div>
        </div>
        <div class="controls">
          <select id="code-file-select" onchange="loadSelectedSubmission(this.value)" style="display:none;background:#0f172a;color:#f8fafc;border:1px solid #475569;border-radius:8px;padding:7px 10px;font:inherit;"></select>
          <button class="btn" id="code-toggle-btn" onclick="toggleCodeScope()">แสดงทั้งไฟล์</button>
          <a class="btn" id="code-dl-link" href="#">⬇️ ดาวน์โหลด</a>
          <button class="btn red" onclick="closeCodeModal()">ปิด</button>
        </div>
      </div>
      <div id="code-grade-banner" style="padding:8px 16px;background:#0f172a;border-bottom:1px solid #334155;font-size:12.5px;color:#fde047;display:none;"></div>
      <pre class="modal-body" id="code-modal-body"></pre>
    </div>
  </div>

<script>
__OFFLINE_QR_JS__
const LAN_URL_BASE = 'http://__LAN_IP__:__PORT__';
document.getElementById('dl-url').textContent = LAN_URL_BASE + '/download';
document.getElementById('api-url').textContent = LAN_URL_BASE + '/api/meter';
document.getElementById('wh-url').textContent = LAN_URL_BASE + '/api/notify';
document.getElementById('dl-qr').innerHTML = OfflineQR.toSvg(LAN_URL_BASE + '/download', 68);

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function csvCell(v) { return '"' + String(v ?? '').replace(/"/g, '""') + '"'; }

function copyText(id, btn) {
  const txt = document.getElementById(id).textContent;
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(txt);
  else { const t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand('copy'); document.body.removeChild(t); }
  if (btn) { const o = btn.textContent; btn.textContent = 'คัดลอกแล้ว ✓'; setTimeout(() => btn.textContent = o, 1400); }
}

function switchTab(tab) {
  ['exam', 'ws', 'audit'].forEach(t => {
    document.getElementById('panel-' + t).style.display = t === tab ? 'block' : 'none';
    document.getElementById('tab-' + t).classList.toggle('active', t === tab);
  });
}

async function setClassStage(stage) {
  await fetch('/api/control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ class_stage: stage }) });
  refresh();
}
async function setScenario(scenario) {
  await fetch('/api/control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'manual', scenario }) });
  refresh();
}
async function setMode(mode) {
  await fetch('/api/control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode }) });
  refresh();
}
async function addRoster() {
  const raw = document.getElementById('roster-input').value.trim();
  if (!raw) return;
  const names = raw.split(',').map(x => x.trim()).filter(Boolean);
  await fetch('/api/roster', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ names }) });
  document.getElementById('roster-input').value = '';
  refresh();
}
async function resetProgress() {
  if (!confirm('ยืนยันล้างตารางคะแนน ฟีด และคิวช่วยเหลือทั้งหมด? (ไฟล์งานที่ส่งในดิสก์จะไม่ถูกลบ)')) return;
  await fetch('/api/reset', { method: 'POST', body: '{}' });
  refresh();
}
async function resolveHelp(id, resolution) {
  await fetch('/api/help/resolve', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, resolution })
  });
  refresh();
}
async function runAutoGradeAll() {
  const res = await fetch('/api/grade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  const data = await res.json();
  if (!res.ok) { alert(data.error || 'Auto-Grade ไม่สำเร็จ'); return; }
  refresh();
}
async function runAutoGradeWorkshops() {
  const res = await fetch('/api/workshop/grade', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  const data = await res.json();
  if (!res.ok) { alert(data.error || 'ตรวจ Workshop ไม่สำเร็จ'); return; }
  refresh();
}

async function downloadAuditExcel() {
  const msgEl = document.getElementById('audit-msg');
  const cohort = document.getElementById('audit-cohort').value.trim() || 'รุ่นที่ 4';
  const fileEl = document.getElementById('theory-csv-file');
  let theoryCsv = '';
  if (fileEl.files && fileEl.files[0]) {
    theoryCsv = await fileEl.files[0].text();
  }
  msgEl.textContent = 'กำลังตรวจคำนวณล่าสุดและสร้างไฟล์ Excel v2...';
  const res = await fetch('/api/audit/export', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cohort, theory_csv: theoryCsv })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    msgEl.textContent = 'สร้างไฟล์ไม่สำเร็จ: ' + (err.error || res.status);
    return;
  }
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `สรุปคะแนน_Audit_v2_${cohort.replace(/\\s+/g, '_')}.xlsx`;
  a.click();
  msgEl.textContent = 'ดาวน์โหลดไฟล์ Excel v2 (ฟอนต์ Leelawadee UI + สูตรครบ + ชีตหลักฐาน Help) สำเร็จแล้ว ✓';
}

function beepAlert() {
  try {
    if (!document.getElementById('sound-toggle').checked) return;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine'; osc.frequency.value = 780;
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(); osc.stop(ctx.currentTime + 0.25);
  } catch (e) {}
}

let latestData = null, sortedStudents = [], modalFullCode = '', modalScriptOnly = '', modalShowingScriptOnly = true, modalCurrentStudent = null;
let knownWaitingIds = new Set();

function exportCSV() {
  if (!latestData) return;
  const rows = Object.values(latestData.students || {});
  rows.sort((a, b) => a.sender.localeCompare(b.sender, 'th'));
  let csv = '\\uFEFFเลขที่-ชื่อ,เคส1_แรงดันเกิน,เคส2_กระแสเกิน,เคส3_น้ำต่ำ,ส่งพลาดตอนปกติ,หักHelp,คะแนนAutoGrade(50),หมายเหตุ\\n';
  rows.forEach(s => {
    const ag = s.auto_grade || {};
    const score = ag.ok ? ag.final_50 : '';
    const notes = (ag.notes || []).join(' | ');
    csv += [csvCell(s.sender), csvCell(s.over_volt || '-'), csvCell(s.over_curr || '-'), csvCell(s.low_water || '-'),
      s.false_alarm || 0, ag.help_penalty || 0, score, csvCell(notes)].join(',') + '\\n';
  });
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'ผลสอบปฏิบัติ_Electrical_Meter_v2.csv'; a.click();
}

function closeCodeModal() { document.getElementById('code-modal').classList.remove('open'); }
function renderCodeModalBody() {
  const pre = document.getElementById('code-modal-body');
  const btn = document.getElementById('code-toggle-btn');
  if (modalScriptOnly) {
    btn.style.display = 'inline-block';
    pre.textContent = modalShowingScriptOnly ? modalScriptOnly : modalFullCode;
    btn.textContent = modalShowingScriptOnly ? 'แสดงทั้งไฟล์' : 'ดูเฉพาะ <script>';
  } else {
    btn.style.display = 'none';
    pre.textContent = modalFullCode;
  }
}
function toggleCodeScope() { modalShowingScriptOnly = !modalShowingScriptOnly; renderCodeModalBody(); }

async function loadSelectedSubmission(rel) {
  if (!modalCurrentStudent) return;
  const sub = modalCurrentStudent.allSubs.find(x => x.rel === rel);
  if (!sub) return;
  document.getElementById('code-modal-title').textContent = modalCurrentStudent.sender + ' — ' + sub.filename;
  document.getElementById('code-modal-sub').textContent = 'ส่งเวลา ' + sub.time + ' (' + sub.label + ')';
  document.getElementById('code-dl-link').href = '/api/submission/download?rel=' + encodeURIComponent(sub.rel);
  document.getElementById('code-modal-body').textContent = 'กำลังโหลด...';

  const res = await fetch('/api/submission?rel=' + encodeURIComponent(sub.rel), { cache: 'no-store' });
  const data = await res.json();
  if (!data.ok) { modalFullCode = data.error || 'เปิดไม่สำเร็จ'; modalScriptOnly = ''; }
  else if (data.isZip) { modalFullCode = 'ไฟล์ใน ZIP:\\n' + (data.entries || []).join('\\n'); modalScriptOnly = ''; }
  else {
    modalFullCode = data.content || '';
    const lower = modalFullCode.toLowerCase();
    const sIdx = lower.indexOf('<script>');
    const eIdx = sIdx >= 0 ? lower.indexOf('<' + '/script>', sIdx + 8) : -1;
    modalScriptOnly = (sIdx >= 0 && eIdx > sIdx) ? modalFullCode.slice(sIdx + 8, eIdx).trim() : '';
    modalShowingScriptOnly = Boolean(modalScriptOnly);
  }
  renderCodeModalBody();
}

async function openStudentCode(idx, targetRel) {
  const s = sortedStudents[idx];
  if (!s) return;
  const allSubs = [];
  ['w1','w2','w3','w4'].forEach(w => {
    ((s.workshops && s.workshops[w]) || []).forEach(x => allSubs.push({ ...x, label: w.toUpperCase() }));
  });
  (s.submissions || []).forEach(x => allSubs.push({ ...x, label: 'Final Exam' }));
  if (!allSubs.length) return;
  modalCurrentStudent = { sender: s.sender, allSubs };
  const sel = document.getElementById('code-file-select');
  sel.innerHTML = allSubs.slice().reverse().map(x => `<option value="${esc(x.rel)}">[${esc(x.label)}] ${esc(x.filename)} (${esc(x.time)})</option>`).join('');
  sel.style.display = allSubs.length > 1 ? 'inline-block' : 'none';
  const chosen = targetRel || allSubs[allSubs.length - 1].rel;
  sel.value = chosen;

  const banner = document.getElementById('code-grade-banner');
  const ag = s.auto_grade;
  if (ag && ag.ok) {
    banner.style.display = 'block';
    banner.textContent = `Auto-Grade: TODO1=${ag.todo_scores[0]} | TODO2=${ag.todo_scores[1]} | TODO3=${ag.todo_scores[2]} | TODO4=${ag.todo_scores[3]} | TODO5=${ag.todo_scores[4]} | พลาด/ซ้ำ=-${ag.dup_penalty + ag.false_alarm_penalty} | หักHelp=-${ag.help_penalty} => รวม ${ag.final_50}/50 (${(ag.notes||[]).join('; ')})`;
  } else {
    banner.style.display = 'none';
  }
  document.getElementById('code-modal').classList.add('open');
  await loadSelectedSubmission(chosen);
}

async function refresh() {
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    if (res.status === 401) { location.reload(); return; }
    const d = await res.json();
    latestData = d;
    if (d.pin_hint) document.getElementById('pin-hint').textContent = d.pin_hint;

    document.querySelectorAll('[data-sc]').forEach(b => b.classList.toggle('active', b.dataset.sc === d.scenario));
    document.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('active', b.dataset.mode === d.mode));
    document.querySelectorAll('[data-cs]').forEach(b => b.classList.toggle('active', b.dataset.cs === (d.class_stage || 'exam')));

    const r = d.latest_reading;
    document.getElementById('live-vals').innerHTML = `
      <span>สถานะ API: <b>${esc(d.scenario_label)}</b></span>
      <span>V: <b>${r.electric.voltage} V</b></span>
      <span>A: <b>${r.electric.current} A</b></span>
      <span>Flow: <b>${r.water.flow} m³/h</b></span>
      <span>อัปเดต: <b>${esc(r.updatedAt.slice(11, 19))}</b></span>
    `;
    document.getElementById('theory-count').textContent = (d.theory_submissions || []).length;

    const list = Object.values(d.students || {});
    list.sort((a, b) => a.sender.localeCompare(b.sender, 'th'));
    sortedStudents = list;
    document.getElementById('student-count').textContent = list.length;
    document.getElementById('ws-count').textContent = list.length;

    const tbody = document.getElementById('student-tbody');
    const wsBody = document.getElementById('ws-tbody');
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="color:#64748b;">ยังไม่มีข้อมูลผู้เรียน...</td></tr>';
      wsBody.innerHTML = '<tr><td colspan="7" style="color:#64748b;">ยังไม่มีข้อมูล Workshop...</td></tr>';
    } else {
      tbody.innerHTML = list.map((s, idx) => {
        const subs = s.submissions || [];
        const subHtml = subs.length
          ? `<button class="btn" style="padding:3px 9px;min-height:30px;font-size:12px;" onclick="openStudentCode(${idx}, '${esc(subs[subs.length-1].rel)}')">ดูโค้ด (${esc(subs[subs.length-1].time)})</button>`
          : '<span class="wait-cell">ยังไม่ส่ง</span>';
        const ag = s.auto_grade || {};
        const hInfo = s.exam_help_info || {};
        const helpStr = hInfo.total_requests ? `ขอ ${hInfo.total_requests} (-${hInfo.applied_penalty})` : '-';
        let gradeHtml = '<span class="wait-cell">รอตรวจ</span>';
        if (ag.ok) {
          gradeHtml = `<b title="${esc((ag.notes||[]).join(' | '))}">${ag.final_50}</b> <span style="font-size:11px;color:#94a3b8;">(${ag.todo_scores.join('+')})</span>`;
        } else if (ag.error) {
          gradeHtml = `<span class="err-cell" title="${esc(ag.error)}">Err</span>`;
        }
        return `<tr>
          <td class="name">${esc(s.sender)}</td>
          <td class="${s.over_volt ? 'ok-cell' : 'wait-cell'}">${s.over_volt ? '✅ ' + esc(s.over_volt) : '⬜'}</td>
          <td class="${s.over_curr ? 'ok-cell' : 'wait-cell'}">${s.over_curr ? '✅ ' + esc(s.over_curr) : '⬜'}</td>
          <td class="${s.low_water ? 'ok-cell' : 'wait-cell'}">${s.low_water ? '✅ ' + esc(s.low_water) : '⬜'}</td>
          <td class="${s.false_alarm ? 'err-cell' : 'wait-cell'}">${s.false_alarm || 0}</td>
          <td class="${hInfo.applied_penalty ? 'err-cell' : 'wait-cell'}">${esc(helpStr)}</td>
          <td>${subHtml}</td>
          <td>${gradeHtml}</td>
        </tr>`;
      }).join('');

      wsBody.innerHTML = list.map((s, idx) => {
        const ws = s.workshops || {};
        const wsGrades = s.workshop_grades || {};
        const wsHelp = s.workshop_help_info || {};
        let rawSum = 0;
        const cells = ['w1','w2','w3','w4'].map(w => {
          const items = ws[w] || [];
          const g = wsGrades[w];
          if (g && g.ok) rawSum += g.raw_5;
          if (!items.length) return '<td class="wait-cell">⬜</td>';
          const latest = items[items.length - 1];
          const scTxt = (g && g.ok) ? `<b>${g.raw_5}/5</b> ` : '✅ ';
          return `<td class="ok-cell">${scTxt}<button class="btn" style="padding:2px 6px;min-height:24px;font-size:11px;" onclick="openStudentCode(${idx}, '${esc(latest.rel)}')">ดู</button></td>`;
        }).join('');
        const pen = wsHelp.applied_penalty || 0;
        const net = Math.max(0, Math.min(20, Math.round((rawSum - pen) * 10) / 10));
        return `<tr>
          <td class="name">${esc(s.sender)}</td>${cells}
          <td class="${pen ? 'err-cell' : 'wait-cell'}">${wsHelp.total_requests ? `ขอ ${wsHelp.total_requests} (-${pen})` : '-'}</td>
          <td><b>${rawSum > 0 ? net + '/20' : '-'}</b></td>
        </tr>`;
      }).join('');
    }

    // Help Queue
    const helpList = d.help_requests || [];
    const waiting = helpList.filter(h => h.status === 'waiting');
    document.getElementById('help-wait-count').textContent = waiting.length;
    waiting.forEach(h => { if (!knownWaitingIds.has(h.id)) { beepAlert(); } });
    knownWaitingIds = new Set(waiting.map(h => h.id));

    const hbox = document.getElementById('help-box');
    if (helpList.length === 0) {
      hbox.innerHTML = '<div style="color:#64748b;font-size:13px;">ยังไม่มีผู้เรียนกดขอความช่วยเหลือ...</div>';
    } else {
      const waitingFirst = waiting.concat(helpList.filter(h => h.status !== 'waiting').slice(0, 8));
      hbox.innerHTML = waitingFirst.map(h => {
        if (h.status === 'waiting') {
          return `<div class="help-card">
            <div><span class="tag">${esc(h.sender)}</span> <b>[${esc(h.scope === 'workshop' ? 'Workshop' : 'สอบปฏิบัติ')}]</b> ${esc(h.topic)} · <small>${esc(h.time)}</small></div>
            ${h.note ? `<div style="font-size:12.5px;color:#fed7aa;margin-top:4px;">"${esc(h.note)}"</div>` : ''}
            <div class="controls" style="margin-top:8px;">
              <button class="btn green" style="min-height:32px;padding:4px 10px;font-size:12px;" onclick="resolveHelp('${esc(h.id)}','tech_issue')">🛠️ เทคนิค (0)</button>
              <button class="btn amber" style="min-height:32px;padding:4px 10px;font-size:12px;" onclick="resolveHelp('${esc(h.id)}','hint')">💡 ชี้แนะ (Tier)</button>
              <button class="btn red" style="min-height:32px;padding:4px 10px;font-size:12px;" onclick="resolveHelp('${esc(h.id)}','code_fix')">🧑‍💻 แก้โค้ดให้</button>
            </div>
          </div>`;
        }
        const resMap = { tech_issue: '🛠️ เทคนิค (0)', hint: '💡 ชี้แนะ', code_fix: '🧑‍💻 แก้โค้ดให้' };
        return `<div class="help-card resolved">
          <div style="font-size:12px;"><span class="tag">${esc(h.sender)}</span> [${esc(h.scope)}] ${esc(h.topic)} — <b>${esc(resMap[h.resolution] || h.resolution)}</b> (${esc(h.resolved_at || h.time)})</div>
        </div>`;
      }).join('');
    }

    const feed = d.notifications || [];
    document.getElementById('feed-count').textContent = feed.length;
    const fbox = document.getElementById('feed-box');
    fbox.innerHTML = feed.length === 0
      ? '<div style="color:#64748b;font-size:13px;">รอรับแจ้งเตือนจากเครื่องผู้เรียน...</div>'
      : feed.slice(0, 35).map(item => {
          const cls = item.verdict === 'pass' ? '' : (item.verdict === 'false_alarm' ? 'bad' : 'warn');
          return `<div class="feed-item ${cls}">
            <div><span class="tag">${esc(item.sender)}</span> <b>${esc(item.title)}</b> — ${esc(item.message)}</div>
            <div style="margin-top:3px;font-size:11.5px;color:#94a3b8;">${esc(item.time)} (${esc(item.ip)}) · ${esc(item.verdict_text)}</div>
          </div>`;
        }).join('');
  } catch (e) {}
}

setInterval(refresh, 2500);
refresh();
</script>
</body>
</html>
""".replace("__OFFLINE_QR_JS__", OFFLINE_QR_JS)


DOWNLOAD_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>พอร์ทัลผู้เรียน · BOI Enterprise Application</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 20px 16px; font-family: "Leelawadee UI", "Sarabun", Tahoma, sans-serif; background: #0f172a; color: #e2e8f0; }
  .wrap { max-width: 880px; margin: 0 auto; }
  h1 { margin: 0 0 6px; font-size: 24px; color: #38bdf8; }
  .sub { margin: 0 0 16px; color: #94a3b8; font-size: 14px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; }
  .card h2 { margin: 0 0 10px; font-size: 17px; color: #93c5fd; }
  .dl-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .dl-btn { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 10px 18px; border-radius: 10px;
    text-decoration: none; font-weight: 700; font-size: 14.5px; cursor: pointer; border: 1px solid #38bdf8; background: #0284c7; color: #fff; font-family: inherit; }
  .dl-btn:hover { background: #0369a1; }
  .dl-btn.secondary { background: #0f172a; border-color: #475569; color: #cbd5e1; }
  .dl-btn.amber { background: #b45309; border-color: #f59e0b; }
  .dl-btn.green { background: #15803d; border-color: #22c55e; }
  .url-row { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }
  .url-row small { display: block; color: #94a3b8; font-size: 12px; }
  .url-row code { color: #fde047; font-size: 14px; font-weight: 700; user-select: all; word-break: break-all; }
  input[type="text"], input[type="file"], select {
    width: 100%; max-width: 460px; min-height: 44px; padding: 9px 12px; border-radius: 8px;
    border: 1px solid #475569; background: #0f172a; color: #f8fafc; font: inherit;
  }
  .grid-ws { display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr)); gap: 10px; }
  .ws-tile { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 12px; }
  .ws-tile.done { border-color: #22c55e; background: #06281c; }
  .ws-tile h3 { margin: 0 0 6px; font-size: 15px; color: #fde047; }
  .msg { margin-top: 8px; font-size: 13.5px; font-weight: 700; min-height: 18px; }
  .msg.ok { color: #4ade80; }
  .msg.err { color: #f87171; }
  .msg.warn { color: #fbbf24; }
  .help-box { border-color: #f59e0b; background: #1c1917; }
  .fee-rule { font-size: 12.5px; color: #fcd34d; background: #292524; padding: 8px 10px; border-radius: 8px; margin-bottom: 10px; line-height: 1.5; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13.5px; }
  th, td { border: 1px solid #334155; padding: 7px 9px; text-align: left; }
  th { background: #0f172a; color: #cbd5e1; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>🎓 พอร์ทัลผู้เรียน BOI (Workshop 1–4 &amp; สอบปฏิบัติ)</h1>
    <p class="sub">ดาวน์โหลดไฟล์เริ่มต้น คัดลอก URL ส่งงานกลับมาที่เครื่องผู้สอน และขอความช่วยเหลือได้จากหน้านี้หน้าเดียว</p>

    <div class="card">
      <h2>1. ระบุตัวตนผู้เรียน (ใช้ร่วมกันทุกส่วน)</h2>
      <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
        <input id="stu-sender" type="text" placeholder="ระบุเลขที่-ชื่อ เช่น 01-สมชาย" oninput="pollMyStatus()">
        <span id="stu-badge" style="font-size:13px;color:#93c5fd;"></span>
      </div>
    </div>

    <div class="card help-box">
      <h2>🙋 2. ขอความช่วยเหลือผู้สอน (Help Queue)</h2>
      <div class="fee-rule">
        <strong>เกณฑ์อย่างยุติธรรม:</strong><br>
        • ปัญหาเครื่อง / Wi-Fi / Live Server: <strong>ฟรี ไม่หักคะแนน (0)</strong><br>
        • ช่วง Workshop: <strong>2 ครั้งแรกฟรี</strong> (ครั้งที่ 3+ หัก -0.5; แก้โค้ดให้ -1; สูงสุดไม่เกิน 5 จาก 20)<br>
        • ช่วงสอบปฏิบัติ: ชี้แนะ (-0.5, -1, -1.5, ถัดไป -0.5) / แก้โค้ด (-2) · <strong>หักสูงสุดไม่เกิน 10 คะแนน และไม่เกิน 40% ของคะแนนที่ทำได้ (เกณฑ์ผ่าน 60/100)</strong>
      </div>
      <div style="display:grid;gap:8px;max-width:520px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
          <select id="help-scope">
            <option value="workshop">ช่วง Workshop (W1–W4)</option>
            <option value="exam">ช่วงสอบปฏิบัติ Final</option>
          </select>
          <select id="help-topic">
            <option value="เปิด Live Server / เรียก API ไม่ได้">เปิด Live Server / API ไม่ขึ้น</option>
            <option value="เขียนเงื่อนไข / คำนวณ JS">เงื่อนไข / คำนวณ JS</option>
            <option value="ส่ง Webhook POST">ส่ง Webhook POST</option>
            <option value="จัดหน้า HTML/CSS">จัดหน้า HTML/CSS</option>
            <option value="ปัญหาเครื่อง/Wi-Fi">ปัญหาเครื่อง/Wi-Fi</option>
          </select>
        </div>
        <input id="help-note" type="text" placeholder="อธิบายสั้นๆ เช่น ขึ้น Error 400 (ไม่บังคับ)">
        <div class="dl-actions">
          <button class="dl-btn amber" id="help-btn" type="button" onclick="sendHelpRequest()">🙋 กดขอความช่วยเหลือผู้สอน</button>
          <span id="help-status" class="msg" style="margin:0;"></span>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>3. โหมด Workshop 1–4 (ดาวน์โหลดไฟล์เริ่มต้น &amp; ส่งงานระหว่างเรียน)</h2>
      <div class="grid-ws" style="margin-bottom:12px;">
        <div class="ws-tile" id="ws-card-w1"><h3>Workshop 1</h3><small>HTML + CSS Flexbox</small><br><br><a class="dl-btn secondary" href="/download/workshop/w1.zip" style="min-height:36px;padding:6px 10px;font-size:12.5px;">โหลด w1.zip</a><div class="msg" id="ws-stat-w1"></div></div>
        <div class="ws-tile" id="ws-card-w2"><h3>Workshop 2</h3><small>DOM &amp; Events</small><br><br><a class="dl-btn secondary" href="/download/workshop/w2.zip" style="min-height:36px;padding:6px 10px;font-size:12.5px;">โหลด w2.zip</a><div class="msg" id="ws-stat-w2"></div></div>
        <div class="ws-tile" id="ws-card-w3"><h3>Workshop 3</h3><small>API Fetch + Polling</small><br><br><a class="dl-btn secondary" href="/download/workshop/w3.zip" style="min-height:36px;padding:6px 10px;font-size:12.5px;">โหลด w3.zip</a><div class="msg" id="ws-stat-w3"></div></div>
        <div class="ws-tile" id="ws-card-w4"><h3>Workshop 4</h3><small>Webhook POST</small><br><br><a class="dl-btn secondary" href="/download/workshop/w4.zip" style="min-height:36px;padding:6px 10px;font-size:12.5px;">โหลด w4.zip</a><div class="msg" id="ws-stat-w4"></div></div>
      </div>
      <div style="display:grid;gap:8px;max-width:520px;border-top:1px solid #334155;padding-top:12px;">
        <label style="font-size:13px;color:#cbd5e1;">ส่งไฟล์ Workshop ที่ทำเสร็จแล้ว:</label>
        <select id="ws-select">
          <option value="w1">ส่ง Workshop 1 (index.html, style.css)</option>
          <option value="w2">ส่ง Workshop 2 (script.js)</option>
          <option value="w3">ส่ง Workshop 3 (script.js)</option>
          <option value="w4">ส่ง Workshop 4 (script.js)</option>
        </select>
        <input id="ws-files" type="file" accept=".html,.htm,.js,.css,.zip,.txt,.json" multiple>
        <div><button class="dl-btn green" id="ws-submit-btn" type="button" onclick="submitWork('workshop')">ส่งงาน Workshop</button></div>
        <div id="ws-submit-status" class="msg"></div>
      </div>
    </div>

    <div class="card">
      <h2>4. URL เชื่อมต่อระบบ &amp; โหมดสอบปฏิบัติ Final (Electrical Meter Alert)</h2>
      <div class="dl-actions" style="margin-bottom:12px;">
        <a class="dl-btn" href="/download/exam_starter.html">⬇️ ดาวน์โหลด exam_starter.html (ไฟล์เดียวจบ)</a>
        <a class="dl-btn secondary" href="/download/starter.zip">โหลดแบบแยกโฟลเดอร์ (starter.zip)</a>
        <a class="dl-btn secondary" href="/theory-exam" target="_blank">📝 เปิดข้อสอบทฤษฎี LAN (หาก Google Form ล่ม)</a>
      </div>
      <div class="url-row">
        <div><small>API_URL</small><code id="dl-api-url">http://__LAN_IP__:__PORT__/api/meter</code></div>
        <button class="dl-btn secondary" type="button" style="min-height:36px;padding:6px 12px;" onclick="copyUrl('dl-api-url', this)">คัดลอก</button>
      </div>
      <div class="url-row" style="margin-bottom:12px;">
        <div><small>WEBHOOK_URL</small><code id="dl-wh-url">http://__LAN_IP__:__PORT__/api/notify</code></div>
        <button class="dl-btn secondary" type="button" style="min-height:36px;padding:6px 12px;" onclick="copyUrl('dl-wh-url', this)">คัดลอก</button>
      </div>
      <table>
        <thead><tr><th>เงื่อนไข</th><th>ค่าที่ต้องคืนจาก checkCondition()</th><th>การส่ง Webhook</th></tr></thead>
        <tbody>
          <tr><td><code>voltage &gt; 240</code></td><td><code>'over_volt'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td><code>current &gt; 20</code></td><td><code>'over_curr'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td><code>water &lt; 1.5</code></td><td><code>'low_water'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td>อยู่ในเกณฑ์ปกติ</td><td><code>'normal'</code></td><td>ห้ามส่งแจ้งเตือน</td></tr>
        </tbody>
      </table>
      <div style="display:grid;gap:8px;max-width:520px;margin-top:14px;border-top:1px solid #334155;padding-top:12px;">
        <label style="font-size:13px;color:#cbd5e1;">ส่งไฟล์ข้อสอบปฏิบัติที่ทำเสร็จแล้ว (.html, .js, .css, .zip):</label>
        <input id="submit-files" type="file" accept=".html,.htm,.js,.css,.zip,.txt,.json" multiple>
        <div><button class="dl-btn" id="submit-btn" type="button" onclick="submitWork('exam')">ส่งไฟล์ข้อสอบปฏิบัติ Final</button></div>
        <div class="msg" id="submit-status"></div>
      </div>
    </div>
  </div>

<script>
function copyUrl(id, btn) {
  const txt = document.getElementById(id).innerText;
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(txt);
  else { const t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); document.execCommand('copy'); document.body.removeChild(t); }
  const old = btn.innerText; btn.innerText = 'คัดลอกแล้ว ✓'; setTimeout(() => btn.innerText = old, 1400);
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => { const r = String(reader.result || ''); const idx = r.indexOf(','); resolve(idx >= 0 ? r.slice(idx + 1) : r); };
    reader.onerror = () => reject(new Error('อ่านไฟล์ไม่สำเร็จ'));
    reader.readAsDataURL(file);
  });
}

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function submitWork(kind) {
  const sender = document.getElementById('stu-sender').value.trim();
  const statusEl = document.getElementById(kind === 'workshop' ? 'ws-submit-status' : 'submit-status');
  const filesEl = document.getElementById(kind === 'workshop' ? 'ws-files' : 'submit-files');
  const btn = document.getElementById(kind === 'workshop' ? 'ws-submit-btn' : 'submit-btn');

  if (!sender) {
    statusEl.textContent = 'กรุณากรอกเลขที่-ชื่อ ในข้อ 1 ด้านบนก่อนครับ';
    statusEl.className = 'msg err';
    document.getElementById('stu-sender').focus();
    return;
  }
  const fileList = filesEl.files;
  if (!fileList || !fileList.length) {
    statusEl.textContent = 'กรุณาเลือกไฟล์ที่ต้องการส่งอย่างน้อย 1 ไฟล์';
    statusEl.className = 'msg err';
    return;
  }

  btn.disabled = true;
  statusEl.textContent = 'กำลังอัปโหลดไฟล์...';
  statusEl.className = 'msg';
  try {
    const filesPayload = [];
    for (let i = 0; i < fileList.length; i++) {
      filesPayload.push({ filename: fileList[i].name, contentBase64: await readFileAsBase64(fileList[i]) });
    }
    const url = kind === 'workshop' ? '/api/workshop/submit' : '/api/submit';
    const body = kind === 'workshop'
      ? { sender, ws_id: document.getElementById('ws-select').value, files: filesPayload }
      : { sender, files: filesPayload };
    const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
    const names = (data.saved || []).map(x => x.filename).join(', ');
    statusEl.textContent = `ส่งงานสำเร็จ (${names}) เวลา ${data.time} ✓`;
    statusEl.className = 'msg ok';
    pollMyStatus();
  } catch (err) {
    statusEl.textContent = 'ส่งไม่สำเร็จ: ' + err.message;
    statusEl.className = 'msg err';
  } finally {
    btn.disabled = false;
  }
}

async function sendHelpRequest() {
  const sender = document.getElementById('stu-sender').value.trim();
  const statusEl = document.getElementById('help-status');
  if (!sender) {
    statusEl.textContent = 'กรุณากรอกเลขที่-ชื่อในข้อ 1 ก่อน';
    statusEl.className = 'msg err';
    return;
  }
  const res = await fetch('/api/help', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sender,
      scope: document.getElementById('help-scope').value,
      topic: document.getElementById('help-topic').value,
      note: document.getElementById('help-note').value.trim()
    })
  });
  const data = await res.json();
  if (!res.ok) {
    statusEl.textContent = data.error || 'ส่งคำขอไม่สำเร็จ';
    statusEl.className = 'msg err';
    return;
  }
  document.getElementById('help-note').value = '';
  statusEl.textContent = `ส่งคำขอแล้ว! อยู่คิวที่ #${data.queue_position} (รอสักครู่)`;
  statusEl.className = 'msg warn';
  pollMyStatus();
}

let pollTimer = null;
async function pollMyStatus() {
  const sender = document.getElementById('stu-sender').value.trim();
  if (!sender) return;
  try {
    const res = await fetch('/api/student/status?sender=' + encodeURIComponent(sender), { cache: 'no-store' });
    if (!res.ok) return;
    const d = await res.json();
    if (d.class_stage) {
      document.getElementById('help-scope').value = d.class_stage === 'workshop' ? 'workshop' : 'exam';
    }
    const ws = d.workshops || {};
    ['w1','w2','w3','w4'].forEach(w => {
      const card = document.getElementById('ws-card-' + w);
      const stat = document.getElementById('ws-stat-' + w);
      const list = ws[w] || [];
      card.classList.toggle('done', list.length > 0);
      stat.textContent = list.length ? `ส่งแล้ว (${list[list.length - 1].time})` : '';
      stat.className = 'msg ok';
    });
    const badge = document.getElementById('stu-badge');
    const hInfo = d.help_summary || {};
    badge.textContent = `สอบผ่าน Live: ${d.live_cases_passed || 0}/3 เคส` + (hInfo.waiting_pos ? ` | คิวรอช่วย #${hInfo.waiting_pos}` : '');
    const hStatus = document.getElementById('help-status');
    if (hInfo.waiting_pos) {
      hStatus.textContent = `กำลังรอผู้สอน (คิวที่ #${hInfo.waiting_pos})`;
      hStatus.className = 'msg warn';
    }
  } catch (e) {}
}

setInterval(pollMyStatus, 4000);
</script>
</body>
</html>
"""
