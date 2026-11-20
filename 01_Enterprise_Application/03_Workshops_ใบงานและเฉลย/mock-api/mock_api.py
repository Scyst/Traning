"""API สำรองสำหรับ Workshop 3–4 (ใช้ Python มาตรฐาน ไม่ต้องติดตั้งอะไรเพิ่ม)

  GET  /api/meter    ค่าน้ำ-ไฟที่เปลี่ยนทุกครั้งที่เรียก
                     ทุกนาที วินาทีที่ 0–9 แรงดันจะเกิน 240 V ให้เห็นคำเตือน
  POST /api/notify   รับแจ้งเตือน {"title": "...", "message": "..."} แล้วพิมพ์บนหน้าจอผู้สอน

รันบนเครื่องผู้สอน:  python mock_api.py   (หรือ python mock_api.py 8001 เพื่อเปลี่ยน port)
แล้วให้ผู้เรียนใช้ URL ที่โปรแกรมพิมพ์ออกมา เช่น http://192.168.1.10:8000/api/meter
ถ้า Windows ถามเรื่อง Firewall ให้อนุญาตเฉพาะ Private network
"""
import json
import random
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TZ = timezone(timedelta(hours=7))
state = {"voltage": 230.0, "current": 15.6, "flow": 3.2}


def drift(value, step, low, high):
    return min(high, max(low, value + random.uniform(-step, step)))


def read_meter():
    state["voltage"] = drift(state["voltage"], 1.5, 224, 238)
    state["current"] = drift(state["current"], 0.3, 14, 17.5)
    state["flow"] = drift(state["flow"], 0.2, 2.5, 4.0)
    voltage = state["voltage"]
    if datetime.now(TZ).second < 10:      # ช่วงทดสอบคำเตือน
        voltage += random.uniform(6, 12)
    return {
        "line": "A",
        "electric": {"voltage": round(voltage, 1), "current": round(state["current"], 1)},
        "water": {"flow": round(state["flow"], 1)},
        "updatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.cors()
        self.end_headers()
        self.wfile.write(data)

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):                 # preflight ของ POST แบบ JSON
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/meter":
            self.send_json(200, read_meter())
        elif path == "/":
            self.send_json(200, {"endpoints": ["GET /api/meter", "POST /api/notify"]})
        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def do_POST(self):
        if self.path.split("?")[0] != "/api/notify":
            self.send_json(404, {"error": "ไม่พบ " + self.path})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except ValueError:
            self.send_json(400, {"error": "body ไม่ใช่ JSON (ลืม JSON.stringify หรือเปล่า)", "received": raw[:200]})
            return
        fields = body if isinstance(body, dict) else {}
        title, message = fields.get("title"), fields.get("message")
        if not isinstance(title, str) or not isinstance(message, str) or not title or not message:
            self.send_json(400, {"error": "ต้องมี title และ message เป็นข้อความ", "received": body})
            return
        stamp = datetime.now(TZ).strftime("%H:%M:%S")
        print(f"[แจ้งเตือน {stamp}] จาก {self.client_address[0]}: {title} — {message}", flush=True)
        self.send_json(200, {"ok": True})

    def log_message(self, fmt, *args):    # ไม่พิมพ์ทุก request ให้เห็นเฉพาะแจ้งเตือน
        pass


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))   # ไม่ได้ส่งข้อมูลจริง ใช้หา IP ของการ์ดเครือข่าย
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    ip = lan_ip()
    print("API สำรองพร้อมใช้งาน ให้ผู้เรียนใช้ URL นี้")
    print(f"  Workshop 3  API_URL     = 'http://{ip}:{port}/api/meter'")
    print(f"  Workshop 4  WEBHOOK_URL = 'http://{ip}:{port}/api/notify'")
    print("กด Ctrl+C เพื่อหยุด\n", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
