"""เซิร์ฟเวอร์ข้อสอบปฏิบัติ (ต่อยอด Workshop 4: Electrical Meter Alert)
รันบนเครื่องผู้สอน:  python exam_server.py

ความสามารถ:
  1) GET  /api/meter      จ่ายค่า Electrical Meter (เลือกเคสเอง / วนอัตโนมัติ / สุ่มอัตโนมัติ)
  2) POST /api/notify     รับแจ้งเตือนจากผู้เรียน + ตรวจว่าตรงเคสปัจจุบันหรือไม่
  3) GET  /               หน้าจอผู้สอน: สลับเคส + ตารางเช็กชื่อผู้เรียนที่ผ่านแต่ละเคส + ฟีดแจ้งเตือนสด
  4) GET  /download       หน้าเว็บให้นักเรียนดึงไฟล์ข้อสอบ + ส่งไฟล์งานที่ทำเสร็จแล้ว
  5) GET  /prompt         หน้าจอโจทย์สอบปฏิบัติ (สำหรับขึ้นโปรเจกเตอร์)
  6) GET  /solution/...   หน้าเว็บเฉลยสำหรับผู้สอนเปิดสาธิต
  7) GET  /starter/...    หน้าเว็บตั้งต้น (สำหรับทดสอบ)
"""
import base64
import io
import json
import os
import random
import re
import socket
import sys
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote

TZ = timezone(timedelta(hours=7))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.join(BASE_DIR, "solution")
STARTER_DIR = os.path.join(BASE_DIR, "starter")
STARTER_HTML_FILE = os.path.join(BASE_DIR, "exam_starter.html")
NOTIFICATIONS_FILE = os.path.join(BASE_DIR, "notifications.html")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
PROGRESS_FILE = os.path.join(BASE_DIR, "exam_progress.json")
PROMPT_FILE = os.path.join(BASE_DIR, "โจทย์สอบปฏิบัติ_แสดงบนจอ.html")
GRACE_SEC = 5.0
ALLOWED_UPLOAD_EXTS = {".html", ".htm", ".js", ".css", ".zip", ".txt", ".json"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_BODY_BYTES = 20 * 1024 * 1024

SCENARIOS = {
    "normal": {
        "label": "🟢 ปกติ (ห้ามส่งแจ้งเตือน)",
        "short": "ปกติ",
        "v_range": (226.0, 234.0),
        "c_range": (14.0, 16.2),
        "w_range": (2.8, 3.6),
    },
    "over_volt": {
        "label": "🔴 เคส 1: แรงดันเกิน (> 240 V)",
        "short": "แรงดันเกิน (>240V)",
        "v_range": (244.5, 258.0),
        "c_range": (14.5, 16.5),
        "w_range": (2.9, 3.5),
    },
    "over_curr": {
        "label": "🟠 เคส 2: กระแสเกิน (> 20 A)",
        "short": "กระแสเกิน (>20A)",
        "v_range": (228.0, 235.0),
        "c_range": (21.5, 25.0),
        "w_range": (2.9, 3.5),
    },
    "low_water": {
        "label": "🔵 เคส 3: น้ำไหลต่ำ (< 1.5 m³/h)",
        "short": "น้ำต่ำ (<1.5)",
        "v_range": (228.0, 234.0),
        "c_range": (14.5, 16.0),
        "w_range": (0.4, 1.1),
    },
}

CYCLE_ORDER = ["normal", "over_volt", "over_curr", "low_water"]

state_lock = threading.Lock()
state = {
    "mode": "manual",          # manual | auto_cycle | auto_random
    "scenario": "normal",
    "prev_scenario": "",
    "cycle_sec": 15,
    "last_switch": time.time(),
    "last_auto_switch": 0.0,
    "last_served_by_ip": {},   # client_ip -> { scenario, ts }
    "latest_reading": {
        "line": "A",
        "electric": {"voltage": 230.4, "current": 15.2},
        "water": {"flow": 3.2},
        "scenario": "normal",
        "updatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
    },
    "students": {},            # sender -> { sender, over_volt, over_curr, low_water, false_alarm, wrong_case, last_seen }
    "notifications": [],       # newest first, max 120
}


def load_saved_progress():
    if not os.path.isfile(PROGRESS_FILE):
        return
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            state["students"] = saved.get("students", {})
            for st in state["students"].values():
                st.setdefault("submissions", [])
            state["notifications"] = saved.get("notifications", [])[:120]
    except Exception as exc:
        print(f"[warn] โหลดไฟล์ความคืบหน้าไม่สำเร็จ: {exc}")


def save_progress():
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"students": state["students"], "notifications": state["notifications"][:120]},
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as exc:
        print(f"[warn] บันทึกไฟล์ความคืบหน้าไม่สำเร็จ: {exc}")


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def maybe_advance_scenario():
    now = time.time()
    mode = state["mode"]
    if mode == "manual":
        return
    if now - state["last_switch"] < state["cycle_sec"]:
        return
    old_sc = state["scenario"]
    state["prev_scenario"] = old_sc
    state["last_switch"] = now
    state["last_auto_switch"] = now
    if mode == "auto_cycle":
        idx = CYCLE_ORDER.index(old_sc) if old_sc in CYCLE_ORDER else 0
        state["scenario"] = CYCLE_ORDER[(idx + 1) % len(CYCLE_ORDER)]
    elif mode == "auto_random":
        choices = [k for k in CYCLE_ORDER if k != old_sc]
        state["scenario"] = random.choice(choices)


def generate_meter_payload(client_ip=""):
    with state_lock:
        maybe_advance_scenario()
        sc = state["scenario"]
        cfg = SCENARIOS.get(sc, SCENARIOS["normal"])
        payload = {
            "line": "A",
            "electric": {
                "voltage": round(random.uniform(*cfg["v_range"]), 1),
                "current": round(random.uniform(*cfg["c_range"]), 1),
            },
            "water": {
                "flow": round(random.uniform(*cfg["w_range"]), 1),
            },
            "scenario": sc,
            "updatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
        }
        state["latest_reading"] = payload
        if client_ip:
            state["last_served_by_ip"][client_ip] = {"scenario": sc, "ts": time.time()}
        return payload


def classify_alert(condition, title, message):
    cond = (condition or "").strip().lower()
    if cond in ("over_volt", "over_curr", "low_water"):
        return cond
    text = f"{cond} {title} {message}".lower()
    if any(k in text for k in ("volt", "240", "แรงดัน", "โวลต์", "ไฟฟ้าเกิน")):
        return "over_volt"
    if any(k in text for k in ("curr", "amp", "20 a", "20a", "กระแส", "แอมป์")):
        return "over_curr"
    if any(k in text for k in ("water", "flow", "1.5", "น้ำ", "ไหลต่ำ", "ไหลน้อย")):
        return "low_water"
    return "unknown"


def ensure_student(sender):
    if sender not in state["students"]:
        state["students"][sender] = {
            "sender": sender,
            "over_volt": "",
            "over_curr": "",
            "low_water": "",
            "false_alarm": 0,
            "wrong_case": 0,
            "last_seen": "",
            "submissions": [],
        }
    else:
        state["students"][sender].setdefault("submissions", [])
    return state["students"][sender]


def safe_name(value, fallback="item"):
    base = os.path.basename(str(value or "").strip())
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", base).strip(". ")
    if not clean or clean in (".", ".."):
        return fallback
    return clean[:80]


def resolve_submission_path(rel_path):
    clean = str(rel_path or "").replace("\\", "/").lstrip("/")
    if not clean:
        return None
    real_base = os.path.realpath(SUBMISSIONS_DIR)
    target = os.path.realpath(os.path.join(real_base, clean))
    if not target.startswith(real_base + os.sep) or not os.path.isfile(target):
        return None
    return target


MONITOR_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>กระดานควบคุมและตรวจผลสอบปฏิบัติ · BOI Exam Server</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 18px 22px;
    font-family: "Leelawadee UI", "Sarabun", Tahoma, sans-serif;
    background: #0f172a; color: #e2e8f0;
  }
  .top {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;
    margin-bottom: 16px;
  }
  h1 { margin: 0; font-size: 22px; color: #38bdf8; }
  .urls {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 10px; margin-bottom: 16px;
  }
  .url-box {
    background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 10px 14px;
    display: flex; justify-content: space-between; align-items: center; gap: 10px;
  }
  .url-box small { display: block; color: #94a3b8; font-size: 12px; }
  .url-box code { color: #fde047; font-size: 14px; font-weight: 700; word-break: break-all; }
  .btn {
    background: #1e293b; color: #f1f5f9; border: 1px solid #475569; border-radius: 8px;
    padding: 8px 13px; font: inherit; font-weight: 700; cursor: pointer; font-size: 13px;
  }
  .btn:hover { background: #334155; }
  .btn.active { outline: 3px solid #38bdf8; background: #0c4a6e; }
  .btn.green { background: #14532d; border-color: #22c55e; }
  .btn.red { background: #7f1d1d; border-color: #ef4444; }
  .btn.orange { background: #7c2d12; border-color: #f97316; }
  .btn.blue { background: #1e3a8a; border-color: #3b82f6; }
  .panel {
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 14px 18px; margin-bottom: 16px;
  }
  .panel h2 { margin: 0 0 10px; font-size: 16px; color: #93c5fd; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .live-vals {
    display: flex; flex-wrap: wrap; gap: 16px; margin-top: 12px;
    padding: 10px 14px; background: #0f172a; border-radius: 8px; border: 1px solid #334155;
    font-size: 15px;
  }
  .live-vals b { color: #fde047; }
  .grid-2 {
    display: grid; grid-template-columns: 1.35fr 1fr; gap: 16px;
  }
  @media (max-width: 980px) { .grid-2 { grid-template-columns: 1fr; } }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th, td { border: 1px solid #334155; padding: 8px 10px; text-align: center; }
  th { background: #0f172a; color: #cbd5e1; }
  td.name { text-align: left; font-weight: 700; }
  .ok-cell { background: #064e3b; color: #6ee7b7; font-weight: 700; }
  .wait-cell { color: #64748b; }
  .err-cell { color: #fca5a5; font-weight: 700; }
  .feed { max-height: 440px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  .feed-item {
    padding: 9px 12px; border-radius: 8px; background: #0f172a;
    border-left: 4px solid #22c55e; font-size: 13px;
  }
  .feed-item.bad { border-left-color: #ef4444; background: #2d1216; }
  .feed-item.warn { border-left-color: #f59e0b; background: #2c210e; }
  .tag {
    display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 11.5px; font-weight: 700;
    background: #fde047; color: #0f172a; margin-right: 6px;
  }
  .roster-box { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
  .roster-box input {
    flex: 1; min-width: 220px; padding: 8px 10px; border-radius: 8px;
    border: 1px solid #475569; background: #0f172a; color: #f8fafc; font: inherit;
  }
  .modal-backdrop {
    display: none; position: fixed; inset: 0; background: rgba(2, 6, 23, 0.82);
    z-index: 50; padding: 24px; align-items: center; justify-content: center;
  }
  .modal-backdrop.open { display: flex; }
  .modal-box {
    width: 100%; max-width: 980px; max-height: 90vh; background: #1e293b;
    border: 1px solid #475569; border-radius: 12px; display: flex; flex-direction: column;
    overflow: hidden;
  }
  .modal-head {
    padding: 12px 16px; border-bottom: 1px solid #334155;
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;
  }
  .modal-body {
    margin: 0; padding: 14px 16px; overflow: auto; background: #0b1120;
    color: #e2e8f0; font-family: Consolas, monospace; font-size: 13px; line-height: 1.5;
    white-space: pre-wrap; word-break: break-word;
  }
</style>
</head>
<body>
  <div class="top">
    <div>
      <h1>🎛️ Exam Server &amp; ตารางตรวจผลสอบปฏิบัติ (ต่อยอด Workshop 4)</h1>
      <div style="color:#94a3b8;font-size:13px;">จ่ายข้อมูล API แบบสลับเคส/วนอัตโนมัติ และบันทึกเคสที่ผู้เรียนแต่ละคนส่งแจ้งเตือนผ่าน</div>
    </div>
    <div class="controls">
      <a class="btn" href="/notifications" target="_blank" style="text-decoration:none;">🔔 เปิดจอแจ้งเตือน</a>
      <a class="btn" href="/prompt" target="_blank" style="text-decoration:none;">📋 เปิดโจทย์ขึ้นจอ</a>
      <a class="btn" href="/solution/" target="_blank" style="text-decoration:none;">👀 เปิดหน้าเว็บเฉลย</a>
      <a class="btn" href="/api/submissions.zip" style="text-decoration:none;">📦 โหลดไฟล์ที่ส่ง (.zip)</a>
      <button class="btn" onclick="exportCSV()">⬇️ Export CSV</button>
      <button class="btn red" onclick="resetProgress()">🗑️ ล้างผลบันทึก</button>
    </div>
  </div>

  <div class="urls">
    <div class="url-box">
      <div><small>1) ลิงก์ให้นักเรียนเปิดโหลดไฟล์ข้อสอบ</small><code id="dl-url"></code></div>
      <div class="controls">
        <button class="btn" onclick="copyText('dl-url', this)">คัดลอก</button>
        <a class="btn" href="/download" target="_blank" style="text-decoration:none;">เปิด</a>
      </div>
    </div>
    <div class="url-box">
      <div><small>2) API_URL (ให้ผู้เรียนวางในโค้ด)</small><code id="api-url"></code></div>
      <button class="btn" onclick="copyText('api-url', this)">คัดลอก</button>
    </div>
    <div class="url-box">
      <div><small>3) WEBHOOK_URL (ให้ผู้เรียนวางในโค้ด)</small><code id="wh-url"></code></div>
      <button class="btn" onclick="copyText('wh-url', this)">คัดลอก</button>
    </div>
  </div>

  <div class="panel">
    <h2>📡 ควบคุมค่าที่ API ส่งออกไปให้ผู้เรียน (GET /api/meter)</h2>
    <div class="controls" id="scenario-btns">
      <button class="btn green" data-sc="normal" onclick="setScenario('normal')">🟢 ปกติ (ห้ามส่งแจ้งเตือน)</button>
      <button class="btn red" data-sc="over_volt" onclick="setScenario('over_volt')">🔴 เคส 1: แรงดันเกิน (&gt;240V)</button>
      <button class="btn orange" data-sc="over_curr" onclick="setScenario('over_curr')">🟠 เคส 2: กระแสเกิน (&gt;20A)</button>
      <button class="btn blue" data-sc="low_water" onclick="setScenario('low_water')">🔵 เคส 3: น้ำต่ำ (&lt;1.5)</button>
      <span style="margin-left:8px;color:#94a3b8;">โหมดจ่ายค่า:</span>
      <button class="btn" data-mode="manual" onclick="setMode('manual')">✋ กดเลือกเอง</button>
      <button class="btn" data-mode="auto_cycle" onclick="setMode('auto_cycle')">🔁 วนอัตโนมัติ (15 วิ)</button>
      <button class="btn" data-mode="auto_random" onclick="setMode('auto_random')">🎲 สุ่มอัตโนมัติ (15 วิ)</button>
    </div>
    <div class="live-vals" id="live-vals">กำลังโหลดค่า...</div>
  </div>

  <div class="grid-2">
    <div class="panel">
      <h2>✅ ตารางสรุปผู้เรียนที่ส่งแจ้งเตือนผ่านแต่ละเคส (<span id="student-count">0</span> คน)</h2>
      <div class="roster-box">
        <input id="roster-input" type="text" placeholder="เพิ่มชื่อผู้เรียนล่วงหน้าคั่นด้วยจุลภาค เช่น 01-รุ่งวดี, 02-ณัฐสุภา">
        <button class="btn" onclick="addRoster()">+ เพิ่มรายชื่อ</button>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>เลขที่-ชื่อ</th>
              <th>เคส 1<br>แรงดันเกิน</th>
              <th>เคส 2<br>กระแสเกิน</th>
              <th>เคส 3<br>น้ำต่ำ</th>
              <th>ส่งพลาด<br>ตอนปกติ</th>
              <th>ไฟล์งานที่ส่ง</th>
              <th>สรุป</th>
            </tr>
          </thead>
          <tbody id="student-tbody">
            <tr><td colspan="7" style="color:#64748b;">ยังไม่มีข้อมูลผู้เรียน...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <h2>🔔 แจ้งเตือนที่ส่งเข้ามาล่าสุด (<span id="feed-count">0</span>)</h2>
      <div class="feed" id="feed-box">
        <div style="color:#64748b;font-size:13px;">รอรับแจ้งเตือนจากเครื่องผู้เรียน...</div>
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
          <a class="btn" id="code-dl-link" href="#" style="text-decoration:none;">⬇️ ดาวน์โหลดไฟล์</a>
          <button class="btn red" onclick="closeCodeModal()">ปิด</button>
        </div>
      </div>
      <pre class="modal-body" id="code-modal-body"></pre>
    </div>
  </div>

<script>
const LAN_URL_BASE = 'http://__LAN_IP__:__PORT__';
document.getElementById('dl-url').textContent = LAN_URL_BASE + '/download';
document.getElementById('api-url').textContent = LAN_URL_BASE + '/api/meter';
document.getElementById('wh-url').textContent = LAN_URL_BASE + '/api/notify';

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function copyText(id, btn) {
  const txt = document.getElementById(id).textContent;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(txt);
  } else {
    const temp = document.createElement('textarea');
    temp.value = txt;
    document.body.appendChild(temp);
    temp.select();
    document.execCommand('copy');
    document.body.removeChild(temp);
  }
  if (btn) {
    const oldTxt = btn.textContent;
    btn.textContent = 'คัดลอกแล้ว ✓';
    setTimeout(function () { btn.textContent = oldTxt; }, 1400);
  }
}

async function setScenario(scenario) {
  await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: 'manual', scenario })
  });
  refresh();
}

async function setMode(mode) {
  await fetch('/api/control', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode })
  });
  refresh();
}

async function addRoster() {
  const raw = document.getElementById('roster-input').value.trim();
  if (!raw) return;
  const names = raw.split(',').map(x => x.trim()).filter(Boolean);
  await fetch('/api/roster', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ names })
  });
  document.getElementById('roster-input').value = '';
  refresh();
}

async function resetProgress() {
  if (!confirm('ยืนยันล้างตารางคะแนนและฟีดแจ้งเตือนทั้งหมด?')) return;
  await fetch('/api/reset', { method: 'POST' });
  refresh();
}

let latestData = null;

function exportCSV() {
  if (!latestData) return;
  const rows = Object.values(latestData.students || {});
  rows.sort((a, b) => a.sender.localeCompare(b.sender, 'th'));
  let csv = '\\uFEFFเลขที่-ชื่อ,เคส1_แรงดันเกิน,เคส2_กระแสเกิน,เคส3_น้ำต่ำ,ส่งพลาดตอนปกติ,รวมเคสที่ผ่าน\\n';
  rows.forEach(s => {
    const passCount = [s.over_volt, s.over_curr, s.low_water].filter(Boolean).length;
    csv += `"${s.sender}","${s.over_volt || '-'}","${s.over_curr || '-'}","${s.low_water || '-'}",${s.false_alarm || 0},${passCount}/3\\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'ผลสอบปฏิบัติ_Electrical_Meter.csv';
  a.click();
}

let sortedStudents = [];
let modalFullCode = '';
let modalScriptOnly = '';
let modalShowingScriptOnly = true;

function closeCodeModal() {
  document.getElementById('code-modal').classList.remove('open');
}

function renderCodeModalBody() {
  const pre = document.getElementById('code-modal-body');
  const btn = document.getElementById('code-toggle-btn');
  if (modalScriptOnly) {
    btn.style.display = 'inline-block';
    pre.textContent = modalShowingScriptOnly ? modalScriptOnly : modalFullCode;
    btn.textContent = modalShowingScriptOnly ? 'แสดงทั้งไฟล์' : 'ดูเฉพาะส่วน <script>';
  } else {
    btn.style.display = 'none';
    pre.textContent = modalFullCode;
  }
}

function toggleCodeScope() {
  modalShowingScriptOnly = !modalShowingScriptOnly;
  renderCodeModalBody();
}

let modalCurrentStudent = null;

async function loadSelectedSubmission(rel) {
  if (!modalCurrentStudent) return;
  const sub = modalCurrentStudent.submissions.find(x => x.rel === rel);
  if (!sub) return;
  document.getElementById('code-modal-title').textContent = modalCurrentStudent.sender + ' — ' + sub.filename;
  document.getElementById('code-modal-sub').textContent = 'ส่งเวลา ' + sub.time + ' (รวม ' + modalCurrentStudent.submissions.length + ' ไฟล์)';
  document.getElementById('code-dl-link').href = '/api/submission/download?rel=' + encodeURIComponent(sub.rel);
  document.getElementById('code-modal-body').textContent = 'กำลังโหลดไฟล์...';

  const res = await fetch('/api/submission?rel=' + encodeURIComponent(sub.rel), { cache: 'no-store' });
  const data = await res.json();
  if (!data.ok) {
    modalFullCode = data.error || 'เปิดไฟล์ไม่สำเร็จ';
    modalScriptOnly = '';
  } else if (data.isZip) {
    modalFullCode = 'ไฟล์ภายใน ZIP:\\n' + (data.entries || []).join('\\n');
    modalScriptOnly = '';
  } else {
    modalFullCode = data.content || '';
    const lower = modalFullCode.toLowerCase();
    const startTag = '<script>';
    const endTag = '<' + '/script>';
    const sIdx = lower.indexOf(startTag);
    const eIdx = sIdx >= 0 ? lower.indexOf(endTag, sIdx + startTag.length) : -1;
    modalScriptOnly = (sIdx >= 0 && eIdx > sIdx) ? modalFullCode.slice(sIdx + startTag.length, eIdx).trim() : '';
    modalShowingScriptOnly = Boolean(modalScriptOnly);
  }
  renderCodeModalBody();
}

async function openLatestCode(idx) {
  const s = sortedStudents[idx];
  if (!s || !s.submissions || !s.submissions.length) return;
  modalCurrentStudent = s;
  const sel = document.getElementById('code-file-select');
  if (s.submissions.length > 1) {
    sel.innerHTML = s.submissions.slice().reverse().map(x => `<option value="${esc(x.rel)}">${esc(x.filename)} (${esc(x.time)})</option>`).join('');
    sel.style.display = 'inline-block';
  } else {
    sel.style.display = 'none';
  }
  const latest = s.submissions[s.submissions.length - 1];
  document.getElementById('code-modal').classList.add('open');
  await loadSelectedSubmission(latest.rel);
}

async function refresh() {
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    const d = await res.json();
    latestData = d;

    document.querySelectorAll('[data-sc]').forEach(b => b.classList.toggle('active', b.dataset.sc === d.scenario));
    document.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('active', b.dataset.mode === d.mode));

    const r = d.latest_reading;
    document.getElementById('live-vals').innerHTML = `
      <span>สถานะที่กำลังจ่าย: <b>${esc(d.scenario_label)}</b></span>
      <span>Voltage: <b>${r.electric.voltage} V</b></span>
      <span>Current: <b>${r.electric.current} A</b></span>
      <span>Water Flow: <b>${r.water.flow} m³/h</b></span>
      <span>เวลา: <b>${esc(r.updatedAt.slice(11, 19))}</b></span>
    `;

    const list = Object.values(d.students || {});
    list.sort((a, b) => a.sender.localeCompare(b.sender, 'th'));
    sortedStudents = list;
    document.getElementById('student-count').textContent = list.length;
    const tbody = document.getElementById('student-tbody');
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="color:#64748b;">ยังไม่มีข้อมูลผู้เรียน...</td></tr>';
    } else {
      tbody.innerHTML = list.map((s, idx) => {
        const count = [s.over_volt, s.over_curr, s.low_water].filter(Boolean).length;
        const subs = s.submissions || [];
        let subHtml = '<span class="wait-cell">ยังไม่ส่ง</span>';
        if (subs.length > 0) {
          const latest = subs[subs.length - 1];
          subHtml = `<button class="btn" style="padding:4px 10px;font-size:12px;" onclick="openLatestCode(${idx})">ดูโค้ด (${esc(latest.time)})</button>`;
        }
        return `<tr>
          <td class="name">${esc(s.sender)}</td>
          <td class="${s.over_volt ? 'ok-cell' : 'wait-cell'}">${s.over_volt ? '✅ ' + esc(s.over_volt) : '⬜ รอ'}</td>
          <td class="${s.over_curr ? 'ok-cell' : 'wait-cell'}">${s.over_curr ? '✅ ' + esc(s.over_curr) : '⬜ รอ'}</td>
          <td class="${s.low_water ? 'ok-cell' : 'wait-cell'}">${s.low_water ? '✅ ' + esc(s.low_water) : '⬜ รอ'}</td>
          <td class="${s.false_alarm ? 'err-cell' : 'wait-cell'}">${s.false_alarm || 0}</td>
          <td>${subHtml}</td>
          <td><b>${count}/3</b></td>
        </tr>`;
      }).join('');
    }

    const feed = d.notifications || [];
    document.getElementById('feed-count').textContent = feed.length;
    const fbox = document.getElementById('feed-box');
    if (feed.length === 0) {
      fbox.innerHTML = '<div style="color:#64748b;font-size:13px;">รอรับแจ้งเตือนจากเครื่องผู้เรียน...</div>';
    } else {
      fbox.innerHTML = feed.slice(0, 40).map(item => {
        const cls = item.verdict === 'pass' ? '' : (item.verdict === 'false_alarm' ? 'bad' : 'warn');
        return `<div class="feed-item ${cls}">
          <div><span class="tag">${esc(item.sender)}</span> <b>${esc(item.title)}</b> — ${esc(item.message)}</div>
          <div style="margin-top:4px;font-size:12px;color:#94a3b8;">
            ${esc(item.time)} (${esc(item.ip)}) · เคสที่ส่ง: ${esc(item.detected)} · <b>${esc(item.verdict_text)}</b>
          </div>
        </div>`;
      }).join('');
    }
  } catch (e) {}
}

setInterval(refresh, 2000);
refresh();
</script>
</body>
</html>
"""

DOWNLOAD_HTML = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ดาวน์โหลดไฟล์สอบปฏิบัติ · Electrical Meter Alert</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 18px;
    font-family: "Leelawadee UI", "Sarabun", Tahoma, sans-serif;
    background: #0f172a; color: #e2e8f0;
  }
  .wrap { max-width: 820px; margin: 0 auto; }
  h1 { margin: 0 0 6px; font-size: 26px; color: #38bdf8; }
  .sub { margin: 0 0 18px; color: #94a3b8; font-size: 14px; }
  .card {
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 18px 20px; margin-bottom: 16px;
  }
  .card h2 { margin: 0 0 12px; font-size: 17px; color: #93c5fd; }
  .dl-actions { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
  .dl-btn {
    display: inline-flex; align-items: center; justify-content: center;
    min-height: 48px; padding: 12px 22px; border-radius: 10px;
    text-decoration: none; font-weight: 700; font-size: 16px; cursor: pointer;
    border: 1px solid #38bdf8; background: #0284c7; color: #ffffff;
  }
  .dl-btn:hover { background: #0369a1; }
  .dl-btn.secondary {
    background: #0f172a; border-color: #475569; color: #cbd5e1; font-size: 14px;
  }
  .dl-btn.secondary:hover { background: #334155; }
  .url-row {
    display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
    gap: 10px; background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 10px;
  }
  .url-row small { display: block; color: #94a3b8; font-size: 12px; margin-bottom: 2px; }
  .url-row code { color: #fde047; font-size: 15px; font-weight: 700; user-select: all; word-break: break-all; }
  .copy-btn {
    min-height: 40px; padding: 8px 14px; border-radius: 8px;
    border: 1px solid #475569; background: #1e293b; color: #f8fafc;
    font: inherit; font-weight: 700; cursor: pointer;
  }
  .copy-btn:hover { background: #334155; }
  ol { margin: 8px 0 0; padding-left: 22px; line-height: 1.75; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }
  th, td { border: 1px solid #334155; padding: 8px 10px; text-align: left; }
  th { background: #0f172a; color: #cbd5e1; }
  .submit-row { display: grid; gap: 10px; margin-top: 8px; }
  .submit-row input[type="text"], .submit-row input[type="file"] {
    width: 100%; max-width: 440px; min-height: 44px; padding: 9px 12px;
    border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; font: inherit;
  }
  .submit-msg { margin-top: 10px; font-size: 14px; font-weight: 700; }
  .submit-msg.ok { color: #4ade80; }
  .submit-msg.err { color: #f87171; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>ข้อสอบปฏิบัติ: Electrical Meter Alert</h1>
    <p class="sub">ดาวน์โหลดไฟล์เริ่มต้นและคัดลอก URL ไปใช้งานในโค้ด</p>

    <div class="card">
      <h2>1. ดาวน์โหลดไฟล์เริ่มต้น</h2>
      <div class="dl-actions">
        <a class="dl-btn" href="/download/exam_starter.html">ดาวน์โหลด exam_starter.html</a>
        <a class="dl-btn secondary" href="/download/starter.zip">ดาวน์โหลดแบบแยกโฟลเดอร์ (starter.zip)</a>
      </div>
    </div>

    <div class="card">
      <h2>2. URL สำหรับเชื่อมต่อระบบ</h2>
      <div class="url-row">
        <div>
          <small>API_URL (ดึงค่ามิเตอร์)</small>
          <code id="dl-api-url">http://__LAN_IP__:__PORT__/api/meter</code>
        </div>
        <button class="copy-btn" type="button" onclick="copyUrl('dl-api-url', this)">คัดลอก API_URL</button>
      </div>
      <div class="url-row" style="margin-bottom:0;">
        <div>
          <small>WEBHOOK_URL (ส่งแจ้งเตือน)</small>
          <code id="dl-wh-url">http://__LAN_IP__:__PORT__/api/notify</code>
        </div>
        <button class="copy-btn" type="button" onclick="copyUrl('dl-wh-url', this)">คัดลอก WEBHOOK_URL</button>
      </div>
    </div>

    <div class="card">
      <h2>3. ขั้นตอนการทำข้อสอบและเกณฑ์เงื่อนไข</h2>
      <ol>
        <li>เปิดไฟล์ <code>exam_starter.html</code> ในโฟลเดอร์ <code>Downloads</code> ด้วย VS Code</li>
        <li>แก้ไขเฉพาะส่วน <code>TODO 1</code> ถึง <code>TODO 5</code> (ระบุ URL และชื่อผู้สอบใน <code>STUDENT_NAME</code> เช่น <code>01-สมชาย</code>)</li>
        <li>เปิดหน้าเว็บผ่าน Live Server แล้วทดสอบกดปุ่มตรวจสอบและโหมดตรวจอัตโนมัติ</li>
      </ol>
      <table>
        <thead>
          <tr><th>เงื่อนไข</th><th>สถานะที่คืน</th><th>การแจ้งเตือน</th></tr>
        </thead>
        <tbody>
          <tr><td><code>voltage &gt; 240</code></td><td><code>'over_volt'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td><code>current &gt; 20</code></td><td><code>'over_curr'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td><code>water &lt; 1.5</code></td><td><code>'low_water'</code></td><td>ส่งแจ้งเตือน</td></tr>
          <tr><td>อยู่ในเกณฑ์ปกติ</td><td><code>'normal'</code></td><td>ไม่ต้องส่งแจ้งเตือน</td></tr>
        </tbody>
      </table>
    </div>

    <div class="card" id="submit-section">
      <h2>4. ส่งไฟล์งานที่ทำเสร็จแล้วกลับมาที่เครื่องผู้สอน</h2>
      <div class="submit-row">
        <div>
          <label for="submit-sender" style="display:block;font-size:13px;color:#cbd5e1;margin-bottom:4px;">ชื่อผู้ส่ง (ระบุให้ตรงกับที่ส่งแจ้งเตือน เช่น 01-สมชาย)</label>
          <input id="submit-sender" type="text" placeholder="เลขที่-ชื่อ เช่น 01-สมชาย">
        </div>
        <div>
          <label for="submit-files" style="display:block;font-size:13px;color:#cbd5e1;margin-bottom:4px;">เลือกไฟล์ที่แก้ไขเสร็จแล้ว (.html, .js, .css หรือ .zip ได้สูงสุดครั้งละ 10 ไฟล์)</label>
          <input id="submit-files" type="file" accept=".html,.htm,.js,.css,.zip,.txt,.json" multiple>
        </div>
        <div>
          <button class="dl-btn" id="submit-btn" type="button" onclick="submitWork()">ส่งไฟล์งาน</button>
        </div>
      </div>
      <div class="submit-msg" id="submit-status"></div>
    </div>
  </div>

  <script>
    function copyUrl(id, btn) {
      const txt = document.getElementById(id).innerText;
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(txt);
      } else {
        const temp = document.createElement('textarea');
        temp.value = txt;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
      }
      if (btn) {
        const oldTxt = btn.innerText;
        btn.innerText = 'คัดลอกแล้ว ✓';
        setTimeout(function () { btn.innerText = oldTxt; }, 1400);
      }
    }

    function readFileAsBase64(file) {
      return new Promise(function (resolve, reject) {
        const reader = new FileReader();
        reader.onload = function () {
          const result = String(reader.result || '');
          const idx = result.indexOf(',');
          resolve(idx >= 0 ? result.slice(idx + 1) : result);
        };
        reader.onerror = function () { reject(new Error('อ่านไฟล์ไม่สำเร็จ')); };
        reader.readAsDataURL(file);
      });
    }

    async function submitWork() {
      const senderEl = document.getElementById('submit-sender');
      const filesEl = document.getElementById('submit-files');
      const statusEl = document.getElementById('submit-status');
      const btn = document.getElementById('submit-btn');

      const sender = senderEl.value.trim();
      const fileList = filesEl.files;
      if (!sender) {
        statusEl.innerText = 'กรุณากรอกเลขที่-ชื่อผู้ส่งก่อน';
        statusEl.className = 'submit-msg err';
        return;
      }
      if (!fileList || fileList.length === 0) {
        statusEl.innerText = 'กรุณาเลือกไฟล์ที่ต้องการส่งอย่างน้อย 1 ไฟล์';
        statusEl.className = 'submit-msg err';
        return;
      }

      btn.disabled = true;
      statusEl.innerText = 'กำลังส่งไฟล์...';
      statusEl.className = 'submit-msg';
      try {
        const filesPayload = [];
        for (let i = 0; i < fileList.length; i++) {
          const f = fileList[i];
          const b64 = await readFileAsBase64(f);
          filesPayload.push({ filename: f.name, contentBase64: b64 });
        }
        const res = await fetch('/api/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sender: sender, files: filesPayload })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || ('HTTP ' + res.status));
        }
        const names = (data.saved || []).map(function (x) { return x.filename; }).join(', ');
        statusEl.innerText = 'ส่งไฟล์เรียบร้อยแล้ว (' + names + ') เวลา ' + data.time;
        statusEl.className = 'submit-msg ok';
      } catch (err) {
        statusEl.innerText = 'ส่งไฟล์ไม่สำเร็จ: ' + err.message;
        statusEl.className = 'submit-msg err';
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""


class ExamHandler(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.cors()
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, status, content_type, data, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for key, val in extra_headers.items():
                self.send_header(key, val)
        self.cors()
        self.end_headers()
        self.wfile.write(data)

    def serve_static_dir(self, base_dir, rel_path):
        rel = rel_path.lstrip("/") or "index.html"
        target = os.path.normpath(os.path.join(base_dir, rel))
        if not target.startswith(os.path.normpath(base_dir)) or not os.path.isfile(target):
            self.send_json(404, {"error": "ไม่พบไฟล์ " + rel})
            return
        ext = os.path.splitext(target)[1].lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }.get(ext, "application/octet-stream")
        with open(target, "rb") as f:
            self.send_bytes(200, ctype, f.read())

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        raw_path = self.path.split("?")[0]
        path = raw_path.rstrip("/") or "/"
        if path in ("/", "/monitor"):
            html = MONITOR_HTML.replace("__LAN_IP__", SERVER_IP).replace("__PORT__", str(SERVER_PORT))
            self.send_bytes(200, "text/html; charset=utf-8", html.encode("utf-8"))
        elif path in ("/download", "/get", "/submit"):
            html = DOWNLOAD_HTML.replace("__LAN_IP__", SERVER_IP).replace("__PORT__", str(SERVER_PORT))
            self.send_bytes(200, "text/html; charset=utf-8", html.encode("utf-8"))
        elif path == "/api/submission":
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            rel = (qs.get("rel") or [""])[0]
            target = resolve_submission_path(rel)
            if not target:
                self.send_json(404, {"ok": False, "error": "ไม่พบไฟล์ที่ระบุ"})
                return
            ext = os.path.splitext(target)[1].lower()
            if ext == ".zip":
                try:
                    with zipfile.ZipFile(target, "r") as zf:
                        entries = zf.namelist()
                    self.send_json(200, {"ok": True, "isZip": True, "entries": entries})
                except zipfile.BadZipFile:
                    self.send_json(200, {"ok": False, "error": "ไฟล์ ZIP เสียหายหรือไม่ใช่ ZIP มาตรฐาน"})
            else:
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.send_json(200, {"ok": True, "isZip": False, "content": content})
        elif path == "/api/submission/download":
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            rel = (qs.get("rel") or [""])[0]
            target = resolve_submission_path(rel)
            if not target:
                self.send_json(404, {"error": "ไม่พบไฟล์ที่ระบุ"})
                return
            fname = os.path.basename(target)
            with open(target, "rb") as f:
                self.send_bytes(
                    200,
                    "application/octet-stream",
                    f.read(),
                    {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}"},
                )
        elif path == "/api/submissions.zip":
            if not os.path.isdir(SUBMISSIONS_DIR):
                self.send_json(404, {"error": "ยังไม่มีไฟล์งานที่ส่งเข้ามา"})
                return
            buf = io.BytesIO()
            count = 0
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for root_dir, _, files in os.walk(SUBMISSIONS_DIR):
                    for fn in files:
                        full = os.path.join(root_dir, fn)
                        rel = os.path.relpath(full, SUBMISSIONS_DIR)
                        zf.write(full, os.path.join("submissions", rel))
                        count += 1
            if count == 0:
                self.send_json(404, {"error": "ยังไม่มีไฟล์งานที่ส่งเข้ามา"})
                return
            self.send_bytes(
                200,
                "application/zip",
                buf.getvalue(),
                {"Content-Disposition": 'attachment; filename="student_submissions.zip"'},
            )
        elif path == "/download/exam_starter.html":
            if os.path.isfile(STARTER_HTML_FILE):
                with open(STARTER_HTML_FILE, "rb") as f:
                    self.send_bytes(
                        200,
                        "text/html; charset=utf-8",
                        f.read(),
                        {"Content-Disposition": 'attachment; filename="exam_starter.html"'},
                    )
            else:
                self.send_json(404, {"error": "ไม่พบไฟล์ exam_starter.html"})
        elif path == "/download/starter.zip":
            if os.path.isdir(STARTER_DIR):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root_dir, _, files in os.walk(STARTER_DIR):
                        for fn in files:
                            full = os.path.join(root_dir, fn)
                            rel = os.path.relpath(full, STARTER_DIR)
                            zf.write(full, os.path.join("exam_starter", rel))
                self.send_bytes(
                    200,
                    "application/zip",
                    buf.getvalue(),
                    {"Content-Disposition": 'attachment; filename="exam_starter.zip"'},
                )
            else:
                self.send_json(404, {"error": "ไม่พบโฟลเดอร์ starter"})
        elif path == "/prompt":
            if os.path.isfile(PROMPT_FILE):
                with open(PROMPT_FILE, "rb") as f:
                    self.send_bytes(200, "text/html; charset=utf-8", f.read())
            else:
                self.send_json(404, {"error": "ไม่พบไฟล์โจทย์ขึ้นจอ"})
        elif path == "/notifications":
            if os.path.isfile(NOTIFICATIONS_FILE):
                with open(NOTIFICATIONS_FILE, "rb") as f:
                    self.send_bytes(200, "text/html; charset=utf-8", f.read())
            else:
                self.send_json(404, {"error": "ไม่พบไฟล์ notifications.html"})
        elif path == "/api/notifications":
            with state_lock:
                items = []
                for it in state["notifications"][:50]:
                    raw_title = it.get("title") or ""
                    sender_name = it.get("sender") or ""
                    disp_title = sender_name if raw_title == "(ส่งแบบ Workshop)" else f"[{sender_name}] {raw_title}"
                    msg_text = it.get("message") or ""
                    verdict_txt = it.get("verdict_text") or ""
                    disp_msg = f"{msg_text} · {verdict_txt}".strip(" ·")
                    items.append({
                        "time": it.get("time", ""),
                        "from": it.get("ip", ""),
                        "title": disp_title,
                        "message": disp_msg,
                    })
            self.send_json(200, {"you": self.client_address[0], "items": items})
        elif path == "/api/meter":
            self.send_json(200, generate_meter_payload(self.client_address[0]))
        elif path == "/api/status":
            with state_lock:
                maybe_advance_scenario()
                sc = state["scenario"]
                body = {
                    "mode": state["mode"],
                    "scenario": sc,
                    "scenario_label": SCENARIOS.get(sc, SCENARIOS["normal"])["label"],
                    "latest_reading": state["latest_reading"],
                    "students": state["students"],
                    "notifications": state["notifications"],
                }
            self.send_json(200, body)
        elif path == "/api/notify":
            self.send_json(200, {
                "ok": True,
                "info": "พร้อมรับ POST JSON { sender, condition, title, message }",
            })
        elif raw_path == "/solution" or raw_path.startswith("/solution/"):
            rel = raw_path[len("/solution"):]
            self.serve_static_dir(SOLUTION_DIR, rel)
        elif raw_path == "/starter" or raw_path.startswith("/starter/"):
            rel = raw_path[len("/starter"):]
            self.serve_static_dir(STARTER_DIR, rel)
        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def do_POST(self):
        raw_path = self.path.split("?")[0]
        path = raw_path.rstrip("/") or "/"
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "ขนาดไฟล์รวมใหญ่เกินกำหนด (สูงสุด 20 MB)"})
            return
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            self.send_json(400, {"error": "body ไม่ใช่ JSON (ลืม JSON.stringify หรือเปล่า)", "received": raw[:200]})
            return

        if path == "/api/submit":
            fields = body if isinstance(body, dict) else {}
            sender = str(fields.get("sender") or "").strip()
            files_in = fields.get("files") if isinstance(fields.get("files"), list) else []
            if not sender:
                self.send_json(400, {"error": "กรุณาระบุชื่อผู้ส่ง (sender)"})
                return
            if not files_in or len(files_in) > 10:
                self.send_json(400, {"error": "ต้องแนบไฟล์อย่างน้อย 1 ไฟล์ และไม่เกิน 10 ไฟล์ต่อครั้ง"})
                return

            safe_sender = safe_name(sender, "student")
            student_dir = os.path.join(SUBMISSIONS_DIR, safe_sender)
            os.makedirs(student_dir, exist_ok=True)
            real_base = os.path.realpath(SUBMISSIONS_DIR)

            stamp_file = datetime.now(TZ).strftime("%H%M%S")
            stamp_disp = datetime.now(TZ).strftime("%H:%M:%S")
            saved_items = []
            for item in files_in:
                if not isinstance(item, dict):
                    continue
                fname = safe_name(item.get("filename"), "exam.html")
                ext = os.path.splitext(fname)[1].lower()
                if ext not in ALLOWED_UPLOAD_EXTS:
                    self.send_json(400, {"error": f"ไม่อนุญาตไฟล์นามสกุล {ext or '(ไม่มี)'} — รองรับ .html, .js, .css, .zip"})
                    return
                b64_data = str(item.get("contentBase64") or "").strip()
                try:
                    file_bytes = base64.b64decode(b64_data, validate=True)
                except Exception:
                    self.send_json(400, {"error": f"ข้อมูลไฟล์ {fname} ไม่ถูกต้อง"})
                    return
                if len(file_bytes) > MAX_UPLOAD_BYTES:
                    self.send_json(400, {"error": f"ไฟล์ {fname} ใหญ่เกิน 5 MB"})
                    return

                stored_name = f"{stamp_file}_{fname}"
                target = os.path.realpath(os.path.join(student_dir, stored_name))
                if not target.startswith(real_base + os.sep):
                    self.send_json(400, {"error": "ชื่อไฟล์ไม่ถูกต้อง"})
                    return
                with open(target, "wb") as f:
                    f.write(file_bytes)

                rel_posix = f"{safe_sender}/{stored_name}"
                saved_items.append({
                    "filename": fname,
                    "rel": rel_posix,
                    "time": stamp_disp,
                    "size": len(file_bytes),
                })

            if not saved_items:
                self.send_json(400, {"error": "ไม่พบไฟล์ที่บันทึกได้"})
                return

            with state_lock:
                st = ensure_student(sender)
                st["submissions"].extend(saved_items)
                st["last_seen"] = stamp_disp
                save_progress()
            names_log = ", ".join(x["filename"] for x in saved_items)
            print(f"[{stamp_disp}] [ส่งไฟล์] {sender} ({self.client_address[0]}) -> {names_log}", flush=True)
            self.send_json(200, {"ok": True, "sender": sender, "saved": saved_items, "time": stamp_disp})
            return

        if path == "/api/notify":
            fields = body if isinstance(body, dict) else {}
            sender = str(fields.get("sender") or fields.get("name") or fields.get("student") or "").strip()
            title = str(fields.get("title") or "").strip()
            message = str(fields.get("message") or "").strip()
            condition = str(fields.get("condition") or "").strip()
            effective_title = title

            # รองรับรูปแบบ workshop2.html: ส่งชื่อมาใน title และข้อความอาการมาใน message
            alert_header_words = (
                "แจ้งเตือน", "alert", "warning", "error",
                "over_volt", "over_curr", "low_water",
                "แรงดันเกิน", "กระแสเกิน", "น้ำไหล", "น้ำต่ำ",
                "over volt", "over curr", "low water",
            )
            if not sender and title and message and not any(w in title.lower() for w in alert_header_words):
                sender = title
                effective_title = ""

            if not sender:
                self.send_json(400, {"error": "ยังไม่ได้ส่งชื่อผู้ส่ง (sender หรือ title แบบ Workshop) — ตรวจว่ากรอกชื่อและส่งมาใน JSON", "received": body})
                return
            if not effective_title and not message:
                self.send_json(400, {"error": "ต้องส่งหัวข้อหรือข้อความแจ้งเตือน (title หรือ message) อย่างน้อย 1 อย่าง", "received": body})
                return

            detected = classify_alert(condition, effective_title, message)
            stamp = datetime.now(TZ).strftime("%H:%M:%S")
            now = time.time()
            client_ip = self.client_address[0]
            with state_lock:
                maybe_advance_scenario()
                current_sc = state["scenario"]
                expected_sc = current_sc
                grace_note = ""
                if (current_sc == "normal" or detected != current_sc) and detected in ("over_volt", "over_curr", "low_water"):
                    served = state["last_served_by_ip"].get(client_ip)
                    auto_recent = state["prev_scenario"] and (now - state["last_auto_switch"] <= GRACE_SEC)
                    if served and (now - served["ts"] <= GRACE_SEC) and served["scenario"] == detected:
                        expected_sc = served["scenario"]
                        grace_note = " (ช่วงเปลี่ยนเคส)"
                    elif auto_recent and state["prev_scenario"] == detected:
                        expected_sc = state["prev_scenario"]
                        grace_note = " (ช่วงเปลี่ยนเคสอัตโนมัติ)"

                st = ensure_student(sender)
                st["last_seen"] = stamp

                if expected_sc == "normal":
                    verdict = "false_alarm"
                    verdict_text = "❌ ส่งแจ้งเตือนขณะสถานะปกติ"
                    st["false_alarm"] += 1
                elif detected == expected_sc:
                    verdict = "pass"
                    verdict_text = f"✅ ผ่านเคส {SCENARIOS[expected_sc]['short']}{grace_note}"
                    if not st[expected_sc]:
                        st[expected_sc] = stamp
                else:
                    verdict = "wrong_case"
                    verdict_text = f"⚠️ เคสปัจจุบันคือ {SCENARIOS[expected_sc]['short']} (ที่ส่งมา: {detected})"
                    st["wrong_case"] += 1

                entry = {
                    "time": stamp,
                    "ip": client_ip,
                    "sender": sender,
                    "title": effective_title or "(ส่งแบบ Workshop)",
                    "message": message,
                    "detected": detected,
                    "server_scenario": expected_sc,
                    "verdict": verdict,
                    "verdict_text": verdict_text,
                }
                state["notifications"].insert(0, entry)
                state["notifications"] = state["notifications"][:120]
                save_progress()
            print(f"[{stamp}] {sender} ({client_ip}) -> {verdict_text} | {effective_title or 'Workshop'} - {message}", flush=True)
            self.send_json(200, {"ok": True, "sender": sender, "verdict": verdict, "verdict_text": verdict_text})

        elif path == "/api/control":
            with state_lock:
                if "mode" in body and body["mode"] in ("manual", "auto_cycle", "auto_random"):
                    state["mode"] = body["mode"]
                    state["last_switch"] = time.time()
                if "scenario" in body and body["scenario"] in SCENARIOS:
                    state["scenario"] = body["scenario"]
                    state["prev_scenario"] = ""
                    state["last_auto_switch"] = 0.0
                    state["last_switch"] = time.time()
                sc = state["scenario"]
                mode = state["mode"]
            self.send_json(200, {"ok": True, "mode": mode, "scenario": sc})

        elif path == "/api/roster":
            names = body.get("names") if isinstance(body, dict) else []
            with state_lock:
                for n in (names or []):
                    clean = str(n).strip()
                    if clean:
                        ensure_student(clean)
                save_progress()
            self.send_json(200, {"ok": True})

        elif path == "/api/reset":
            with state_lock:
                state["students"] = {}
                state["notifications"] = []
                state["last_served_by_ip"] = {}
                save_progress()
            self.send_json(200, {"ok": True})

        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    SERVER_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    SERVER_IP = lan_ip()
    load_saved_progress()
    print("=" * 68)
    print("🚀 เปิดระบบ Exam Server (Electrical Meter Alert) เรียบร้อย!")
    print(f"  1) กระดานผู้สอน (ควบคุมเคส + ตารางผู้ผ่าน): http://localhost:{SERVER_PORT}/")
    print(f"  2) หน้าให้นักเรียนดาวน์โหลดและส่งไฟล์งาน:   http://{SERVER_IP}:{SERVER_PORT}/download")
    print(f"  3) หน้าจอแจ้งเตือน (Lockscreen):           http://localhost:{SERVER_PORT}/notifications")
    print(f"  4) โจทย์สอบปฏิบัติ (สำหรับขึ้นจอโปรเจกเตอร์): http://localhost:{SERVER_PORT}/prompt")
    print(f"  5) หน้าเว็บเฉลย (Solution):                 http://localhost:{SERVER_PORT}/solution/")
    print(f"  6) API_URL สำหรับผู้เรียน:     http://{SERVER_IP}:{SERVER_PORT}/api/meter")
    print(f"  7) WEBHOOK_URL สำหรับผู้เรียน: http://{SERVER_IP}:{SERVER_PORT}/api/notify")
    print("=" * 68, flush=True)
    ThreadingHTTPServer(("0.0.0.0", SERVER_PORT), ExamHandler).serve_forever()
