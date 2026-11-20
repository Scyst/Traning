"""เซิร์ฟเวอร์แสดงหน้าเว็บเฉลย (Standalone Solution) + เปิดรับ Webhook API สำหรับห้องสอบปฏิบัติ
รันคำสั่ง: python exam_server.py
"""
import json
import os
import socket
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TZ = timezone(timedelta(hours=7))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.join(BASE_DIR, "solution")
SAMPLES_DIR = os.path.join(BASE_DIR, "starter", "data", "samples")

MODES = {
    "normal": {"file": "normal.json", "label": "🟢 ปกติ (92.0%)"},
    "watch": {"file": "watch.json", "label": "🟡 เฝ้าระวัง (75.0%)"},
    "low": {"file": "low.json", "label": "🔴 ต่ำกว่าเป้า (50.0%)"},
    "b85": {"file": "boundary-85.json", "label": "🟢 ค่าขอบ 85.0%"},
    "b60": {"file": "boundary-60.json", "label": "🟡 ค่าขอบ 60.0%"},
    "off": {"custom": {"line": {"name": "A", "shift": "Day"}, "output": {"target": 0, "actual": 0}, "defect": 0}, "label": "⚪ ไม่มีข้อมูล (target=0)"},
    "err": {"error": True, "label": "⚠️ จำลองโหลดไฟล์ไม่สำเร็จ"},
}

state = {
    "mode": "normal",
    "notifications": [],
}

DEMO_TOOLBAR_SNIPPET = """
<!-- แถบควบคุมจำลองสถานะสำหรับผู้สอน (ซ่อนได้ ไม่กระทบโค้ดเฉลย) -->
<style>
  #instructor-bar {
    position: fixed; right: 16px; bottom: 16px; z-index: 9999;
    background: rgba(15, 23, 42, 0.96); border: 1px solid #334155;
    border-radius: 12px; padding: 12px 16px; color: #cbd5e1;
    font-family: "Leelawadee UI", Tahoma, sans-serif; font-size: 13px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.6); width: min(620px, 95vw);
  }
  #instructor-bar.minimized { width: auto; }
  #instructor-bar.minimized .ibar-body { display: none; }
  .ibar-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-weight: 700; color: #38bdf8; font-size: 14px; }
  .ibar-toggle { background: #1e293b; border: 1px solid #475569; border-radius: 6px; color: #e2e8f0; cursor: pointer; font-size: 12px; padding: 3px 8px; }
  .ibar-btns { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .ibar-btn {
    background: #1e293b; color: #e2e8f0; border: 1px solid #475569;
    border-radius: 6px; padding: 5px 10px; font-size: 12px; cursor: pointer; font-family: inherit;
  }
  .ibar-btn:hover { background: #334155; }
  .ibar-wh { margin-top: 10px; padding-top: 8px; border-top: 1px solid #334155; font-size: 12px; color: #94a3b8; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }
  .ibar-wh code { color: #fde047; font-weight: 700; font-size: 13px; user-select: all; }
  .ibar-payload-hint { margin-top: 4px; font-size: 12px; color: #cbd5e1; background: #0f172a; padding: 6px 10px; border-radius: 6px; border: 1px dashed #334155; }
  .ibar-payload-hint code { color: #86efac; }
  .ibar-feed { margin-top: 8px; max-height: 180px; overflow-y: auto; font-size: 13px; display: flex; flex-direction: column; gap: 5px; }
  .ibar-item { padding: 6px 10px; background: #064e3b; color: #ecfdf5; border-left: 4px solid #10b981; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .ibar-sender { background: #fde047; color: #0f172a; font-weight: 800; padding: 2px 8px; border-radius: 99px; font-size: 12px; white-space: nowrap; }
  .ibar-meta { color: #a7f3d0; font-size: 11px; white-space: nowrap; }
</style>
<div id="instructor-bar">
  <div class="ibar-head">
    <span>🎛️ แผงจำลองข้อมูล & รายชื่อผู้เรียนที่ยิง Webhook เข้ามา</span>
    <button class="ibar-toggle" onclick="document.getElementById('instructor-bar').classList.toggle('minimized')">ย่อ/ขยาย</button>
  </div>
  <div class="ibar-body">
    <div class="ibar-btns" id="ibar-modes">
      <button class="ibar-btn" onclick="switchMode('normal')">🟢 ปกติ 92%</button>
      <button class="ibar-btn" onclick="switchMode('watch')">🟡 เฝ้าระวัง 75%</button>
      <button class="ibar-btn" onclick="switchMode('low')">🔴 ต่ำกว่าเป้า 50% (กดปุ่มได้)</button>
      <button class="ibar-btn" onclick="switchMode('b85')">85.0%</button>
      <button class="ibar-btn" onclick="switchMode('b60')">60.0%</button>
      <button class="ibar-btn" onclick="switchMode('off')">target=0</button>
      <button class="ibar-btn" onclick="switchMode('err')">⚠️ ไฟล์พัง</button>
    </div>
    <div class="ibar-wh">
      <span>🔗 WEBHOOK_URL: <code id="ibar-url"></code></span>
      <span id="ibar-count" style="color:#34d399;font-weight:700;">แจ้งเตือนเข้า: 0 รายการ</span>
    </div>
    <div class="ibar-payload-hint">
      💡 ให้นักเรียนส่ง JSON: <code>{ "sender": "เลขที่-ชื่อ", "title": "...", "message": "..." }</code>
    </div>
    <div class="ibar-feed" id="ibar-feed"></div>
  </div>
</div>
<script>
  document.getElementById('ibar-url').textContent = 'http://__LAN_IP__:__PORT__/api/notify';
  async function switchMode(mode) {
    await fetch('/api/mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });
    if (typeof loadPerformance === 'function') loadPerformance();
  }
  async function pollWebhookFeed() {
    try {
      const r = await fetch('/api/notifications', { cache: 'no-store' });
      const d = await r.json();
      document.getElementById('ibar-count').textContent = 'แจ้งเตือนเข้า: ' + d.items.length + ' รายการ';
      const feed = document.getElementById('ibar-feed');
      if (d.items.length === 0) {
        feed.innerHTML = '<div style="color:#64748b;font-size:12px;padding:4px 0;">รอรับการแจ้งเตือนจากผู้เรียน...</div>';
        return;
      }
      feed.innerHTML = d.items.slice(0, 12).map(x =>
        `<div class="ibar-item">
          <div><span class="ibar-sender">👤 ${x.sender}</span> <b>${x.title}</b> — ${x.message}</div>
          <span class="ibar-meta">${x.time} (${x.ip})</span>
        </div>`
      ).join('');
    } catch (e) {}
  }
  setInterval(pollWebhookFeed, 1500);
  pollWebhookFeed();
</script>
"""


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def get_current_performance_payload():
    mode_info = MODES.get(state["mode"], MODES["normal"])
    if mode_info.get("error"):
        return None
    if "custom" in mode_info:
        data = dict(mode_info["custom"])
    else:
        sample_path = os.path.join(SAMPLES_DIR, mode_info["file"])
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data["updatedAt"] = datetime.now(TZ).isoformat(timespec="seconds")
    return data


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

    def send_bytes(self, status, content_type, data):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(SOLUTION_DIR, "index.html"), "r", encoding="utf-8") as f:
                html = f.read()
            if "pure=1" not in self.path:
                snippet = DEMO_TOOLBAR_SNIPPET.replace("__LAN_IP__", SERVER_IP).replace("__PORT__", str(SERVER_PORT))
                html = html.replace("</body>", snippet + "\n</body>")
            self.send_bytes(200, "text/html; charset=utf-8", html.encode("utf-8"))
        elif path == "/style.css":
            with open(os.path.join(SOLUTION_DIR, "style.css"), "rb") as f:
                self.send_bytes(200, "text/css; charset=utf-8", f.read())
        elif path == "/script.js":
            with open(os.path.join(SOLUTION_DIR, "script.js"), "rb") as f:
                self.send_bytes(200, "application/javascript; charset=utf-8", f.read())
        elif path in ("/data/performance.json", "/api/performance"):
            payload = get_current_performance_payload()
            if payload is None:
                self.send_json(500, {"error": "จำลองสถานะโหลดข้อมูลไม่สำเร็จ"})
            else:
                self.send_json(200, payload)
        elif path.startswith("/data/samples/"):
            fname = os.path.basename(path)
            fpath = os.path.join(SAMPLES_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    self.send_bytes(200, "application/json; charset=utf-8", f.read())
            else:
                self.send_json(404, {"error": "ไม่พบไฟล์ตัวอย่าง"})
        elif path == "/api/notifications":
            self.send_json(200, {"mode": state["mode"], "items": state["notifications"]})
        elif path == "/api/notify":
            self.send_json(200, {
                "ok": True,
                "info": "Endpoint นี้พร้อมรับ POST JSON {'sender': 'ชื่อผู้ส่ง', 'title': '...', 'message': '...'} สำหรับข้อ 5",
                "total_received": len(state["notifications"]),
            })
        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            self.send_json(400, {"error": "body ไม่ใช่ JSON (ลืม JSON.stringify หรือเปล่า)", "received": raw[:200]})
            return

        if path == "/api/notify":
            fields = body if isinstance(body, dict) else {}
            sender = (fields.get("sender") or fields.get("name") or fields.get("student") or "").strip()
            title = (fields.get("title") or "").strip()
            message = (fields.get("message") or "").strip()
            if not title or not message:
                self.send_json(400, {"error": "ต้องมี sender, title และ message เป็นข้อความ", "received": body})
                return
            if not sender:
                sender = "ไม่ระบุชื่อ"
            stamp = datetime.now(TZ).strftime("%H:%M:%S")
            entry = {
                "time": stamp,
                "ip": self.client_address[0],
                "sender": sender,
                "title": title,
                "message": message,
            }
            state["notifications"].insert(0, entry)
            state["notifications"] = state["notifications"][:100]
            print(f"[แจ้งเตือน {stamp}] ผู้ส่ง: {entry['sender']} ({entry['ip']}) -> {entry['title']} — {entry['message']}", flush=True)
            self.send_json(200, {"ok": True, "received": entry})
        elif path == "/api/mode":
            new_mode = body.get("mode")
            if new_mode in MODES:
                state["mode"] = new_mode
                self.send_json(200, {"ok": True, "mode": state["mode"]})
            else:
                self.send_json(400, {"error": "ไม่รู้จักโหมด " + str(new_mode)})
        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    SERVER_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    SERVER_IP = lan_ip()
    print("=" * 65)
    print("🚀 เปิดระบบแสดงหน้าเว็บสำเร็จ (Solution) + Webhook API เรียบร้อย!")
    print(f"  1) หน้าเว็บสำเร็จ (พร้อมแผงสลับสถานะ): http://localhost:{SERVER_PORT}/")
    print(f"  2) หน้าเว็บสำเร็จแบบเพียวๆ 100%:       http://localhost:{SERVER_PORT}/?pure=1")
    print(f"  3) WEBHOOK_URL ให้นักเรียนเกาะ (ข้อ 5): http://{SERVER_IP}:{SERVER_PORT}/api/notify")
    print("=" * 65, flush=True)
    ThreadingHTTPServer(("0.0.0.0", SERVER_PORT), ExamHandler).serve_forever()
