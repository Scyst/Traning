"""BOI Unified Classroom Server v2 (Workshops 1-4 + Practical Exam + Help Queue + Auto-Grader + Audit Export).

Run on instructor laptop:
    python exam_server.py          (default port 8000)
    python exam_server.py 8080     (custom port)

Environment overrides (optional):
    BOI_INSTRUCTOR_PIN=<custom_pin>   (otherwise randomly generated 4-digit PIN on startup)
"""
import base64
import hmac
import io
import json
import os
import random
import re
import secrets
import socket
import sys
import tempfile
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote

from audit_exporter import export_audit_workbook, parse_theory_csv
from auto_grader import grade_practical_submission, grade_workshop_submission
from grading_rules import calculate_help_penalty
from portal_ui import DOWNLOAD_HTML, MONITOR_HTML, PIN_LOGIN_HTML

TZ = timezone(timedelta(hours=7))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_DIR = os.path.dirname(BASE_DIR)
COURSE_DIR = os.path.dirname(EXAM_DIR)
WORKSHOPS_ROOT = os.path.join(COURSE_DIR, "03_Workshops_ใบงานและเฉลย")
LINKS_HTML_FILE = os.path.join(COURSE_DIR, "00_ศูนย์รวมลิงก์และQR_เปิดสอน.html")
FORM_LINKS_FILE = os.path.join(COURSE_DIR, "05_Teaching_Kit_และระบบประเมินผล", "assessment", "form_links.json")
THEORY_HTML_FILE = os.path.join(EXAM_DIR, "ข้อสอบรวม_PostTest_และ_Final_ออนไลน์.html")

SOLUTION_DIR = os.path.join(BASE_DIR, "solution")
STARTER_DIR = os.path.join(BASE_DIR, "starter")
STARTER_HTML_FILE = os.path.join(BASE_DIR, "exam_starter.html")
NOTIFICATIONS_FILE = os.path.join(BASE_DIR, "notifications.html")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
WORKSHOP_SUBMISSIONS_DIR = os.path.join(SUBMISSIONS_DIR, "_workshops")
PROGRESS_FILE = os.path.join(BASE_DIR, "exam_progress.json")
PROMPT_FILE = os.path.join(BASE_DIR, "โจทย์สอบปฏิบัติ_แสดงบนจอ.html")

GRACE_SEC = 5.0
ALLOWED_UPLOAD_EXTS = {".html", ".htm", ".js", ".css", ".zip", ".txt", ".json"}
WORKSHOP_IDS = ("w1", "w2", "w3", "w4")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_BODY_BYTES = 20 * 1024 * 1024
AUTH_MAX_FAILS = 5
AUTH_LOCK_SEC = 60.0

INSTRUCTOR_PIN = os.environ.get("BOI_INSTRUCTOR_PIN") or str(secrets.randbelow(9000) + 1000)
INSTRUCTOR_SESSION_TOKEN = secrets.token_hex(24)

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
auth_failures: Dict[str, List[float]] = {}
state: Dict[str, Any] = {
    "class_stage": "exam",      # workshop | exam
    "mode": "manual",           # manual | auto_cycle | auto_random
    "scenario": "normal",
    "prev_scenario": "",
    "cycle_sec": 15,
    "last_switch": time.time(),
    "last_auto_switch": 0.0,
    "last_served_by_ip": {},
    "latest_reading": {
        "line": "A",
        "electric": {"voltage": 230.4, "current": 15.2},
        "water": {"flow": 3.2},
        "updatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
    },
    "students": {},
    "notifications": [],
    "help_requests": [],        # newest first
    "theory_submissions": [],   # offline / LAN theory submissions
}


def now_hms() -> str:
    return datetime.now(TZ).strftime("%H:%M:%S")


def ensure_student(sender: str) -> Dict[str, Any]:
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
            "workshops": {w: [] for w in WORKSHOP_IDS},
            "workshop_grades": {},
            "auto_grade": None,
            "exam_help_info": {"total_requests": 0, "applied_penalty": 0.0},
            "workshop_help_info": {"total_requests": 0, "applied_penalty": 0.0},
        }
    else:
        st = state["students"][sender]
        st.setdefault("submissions", [])
        st.setdefault("workshops", {w: [] for w in WORKSHOP_IDS})
        for w in WORKSHOP_IDS:
            st["workshops"].setdefault(w, [])
        st.setdefault("workshop_grades", {})
        st.setdefault("auto_grade", None)
        st.setdefault("exam_help_info", {"total_requests": 0, "applied_penalty": 0.0})
        st.setdefault("workshop_help_info", {"total_requests": 0, "applied_penalty": 0.0})
    return state["students"][sender]


def refresh_student_help_summaries() -> None:
    """Recompute cached Workshop and Exam help penalty summaries for every student."""
    by_sender: Dict[str, List[Dict[str, Any]]] = {}
    for req in state["help_requests"]:
        by_sender.setdefault(req.get("sender", ""), []).append(req)
    for sender, st in state["students"].items():
        reqs = by_sender.get(sender, [])
        ag = st.get("auto_grade") or {}
        exam_raw = max(0.0, round(float(ag.get("raw_50") or 0) - float(ag.get("dup_penalty") or 0) - float(ag.get("false_alarm_penalty") or 0), 1)) if ag.get("ok") else None
        ws_grades = st.get("workshop_grades") or {}
        ws_raw = round(sum(float(v.get("raw_5") or 0) for v in ws_grades.values() if v.get("ok")), 1) if ws_grades else None
        st["exam_help_info"] = calculate_help_penalty(reqs, scope="exam", raw_earned=exam_raw)
        st["workshop_help_info"] = calculate_help_penalty(reqs, scope="workshop", raw_earned=ws_raw)


def load_saved_progress() -> None:
    if not os.path.isfile(PROGRESS_FILE):
        return
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            state["students"] = saved.get("students", {})
            for sender in list(state["students"].keys()):
                ensure_student(sender)
            state["notifications"] = saved.get("notifications", [])[:120]
            state["help_requests"] = saved.get("help_requests", [])[:300]
            state["theory_submissions"] = saved.get("theory_submissions", [])[:200]
            state["class_stage"] = saved.get("class_stage", "exam")
            refresh_student_help_summaries()
    except Exception as exc:
        print(f"[warn] โหลดไฟล์ความคืบหน้าไม่สำเร็จ: {exc}")


def save_progress() -> None:
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "class_stage": state["class_stage"],
                    "students": state["students"],
                    "notifications": state["notifications"][:120],
                    "help_requests": state["help_requests"][:300],
                    "theory_submissions": state["theory_submissions"][:200],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
    except Exception as exc:
        print(f"[warn] บันทึกไฟล์ความคืบหน้าไม่สำเร็จ: {exc}")


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def safe_name(value: Any, fallback: str = "item") -> str:
    base = os.path.basename(str(value or "").strip())
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", base).strip(". ")
    if not clean or clean in (".", ".."):
        return fallback
    return clean[:80]


def resolve_submission_path(rel_path: str) -> Optional[str]:
    clean = str(rel_path or "").replace("\\", "/").lstrip("/")
    if not clean:
        return None
    real_base = os.path.realpath(SUBMISSIONS_DIR)
    target = os.path.realpath(os.path.join(real_base, clean))
    if not target.startswith(real_base + os.sep) or not os.path.isfile(target):
        return None
    return target


def save_uploaded_files(base_dir: str, rel_prefix: str, files_in: List[Any]) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Validate and save uploaded base64 files safely under base_dir; return (saved_items, error_msg)."""
    if not files_in or len(files_in) > 10:
        return None, "ต้องแนบไฟล์อย่างน้อย 1 ไฟล์ และไม่เกิน 10 ไฟล์ต่อครั้ง"

    os.makedirs(base_dir, exist_ok=True)
    real_sub_root = os.path.realpath(SUBMISSIONS_DIR)
    stamp_file = datetime.now(TZ).strftime("%H%M%S")
    stamp_disp = now_hms()
    saved_items: List[Dict[str, Any]] = []

    for item in files_in:
        if not isinstance(item, dict):
            continue
        fname = safe_name(item.get("filename"), "work.html")
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ALLOWED_UPLOAD_EXTS:
            return None, f"ไม่อนุญาตไฟล์นามสกุล {ext or '(ไม่มี)'} — รองรับ .html, .js, .css, .zip"
        b64_data = str(item.get("contentBase64") or "").strip()
        try:
            file_bytes = base64.b64decode(b64_data, validate=True)
        except Exception:
            return None, f"ข้อมูลไฟล์ {fname} ไม่ถูกต้อง"
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            return None, f"ไฟล์ {fname} ใหญ่เกิน 5 MB"

        stored_name = f"{stamp_file}_{fname}"
        target = os.path.realpath(os.path.join(base_dir, stored_name))
        if not target.startswith(real_sub_root + os.sep):
            return None, "ชื่อไฟล์ไม่ถูกต้อง"
        with open(target, "wb") as f:
            f.write(file_bytes)

        saved_items.append({
            "filename": fname,
            "rel": f"{rel_prefix}/{stored_name}",
            "time": stamp_disp,
            "size": len(file_bytes),
        })

    if not saved_items:
        return None, "ไม่พบไฟล์ที่บันทึกได้"
    return saved_items, None


def maybe_advance_scenario() -> None:
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


def generate_meter_payload(client_ip: str = "") -> Dict[str, Any]:
    """Return sensor readings WITHOUT internal 'scenario' key to prevent shortcut cheating."""
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
            "updatedAt": datetime.now(TZ).isoformat(timespec="seconds"),
        }
        state["latest_reading"] = payload
        if client_ip:
            state["last_served_by_ip"][client_ip] = {"scenario": sc, "ts": time.time()}
        return payload


def classify_alert(condition: str, title: str, message: str) -> str:
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


def grade_all_exam_submissions_locked() -> int:
    count = 0
    for sender, st in state["students"].items():
        subs = st.get("submissions") or []
        if not subs:
            continue
        latest_batch_time = subs[-1].get("time")
        batch_paths = [
            p for s in subs if s.get("time") == latest_batch_time
            for p in [resolve_submission_path(s.get("rel", ""))] if p
        ]
        if not batch_paths:
            continue
        reqs = [r for r in state["help_requests"] if r.get("sender") == sender]
        st["auto_grade"] = grade_practical_submission(batch_paths, st, reqs)
        count += 1
    refresh_student_help_summaries()
    return count


def grade_all_workshops_locked() -> int:
    count = 0
    for sender, st in state["students"].items():
        reqs = [r for r in state["help_requests"] if r.get("sender") == sender]
        ws_dict = st.get("workshops") or {}
        st.setdefault("workshop_grades", {})
        for w in WORKSHOP_IDS:
            items = ws_dict.get(w) or []
            if not items:
                continue
            latest_time = items[-1].get("time")
            paths = [
                p for x in items if x.get("time") == latest_time
                for p in [resolve_submission_path(x.get("rel", ""))] if p
            ]
            if paths:
                st["workshop_grades"][w] = grade_workshop_submission(w, paths, reqs)
                count += 1
    refresh_student_help_summaries()
    return count


def zip_directory_bytes(folder: str, archive_root: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, _, files in os.walk(folder):
            for fn in files:
                full = os.path.join(root_dir, fn)
                rel = os.path.relpath(full, folder)
                zf.write(full, os.path.join(archive_root, rel))
    return buf.getvalue()


SERVER_IP = "127.0.0.1"
SERVER_PORT = 8000


class ExamHandler(BaseHTTPRequestHandler):
    def cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")

    def is_instructor(self) -> bool:
        ip = self.client_address[0]
        if ip in ("127.0.0.1", "::1"):
            return True
        raw_cookie = self.headers.get("Cookie") or ""
        c = SimpleCookie()
        try:
            c.load(raw_cookie)
        except Exception:
            return False
        morsel = c.get("boi_inst")
        if not morsel:
            return False
        return hmac.compare_digest(str(morsel.value), INSTRUCTOR_SESSION_TOKEN)

    def send_json(self, status: int, body: Any, extra_headers: Optional[Dict[str, str]] = None) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_bytes(status, "application/json; charset=utf-8", data, extra_headers)

    def send_bytes(self, status: int, content_type: str, data: bytes, extra_headers: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for key, val in extra_headers.items():
                self.send_header(key, val)
        self.cors()
        self.end_headers()
        self.wfile.write(data)

    def serve_static_file(self, file_path: str, content_type: str = "text/html; charset=utf-8", extra_headers: Optional[Dict[str, str]] = None) -> None:
        if not os.path.isfile(file_path):
            self.send_json(404, {"error": f"ไม่พบไฟล์ {os.path.basename(file_path)}"})
            return
        with open(file_path, "rb") as f:
            self.send_bytes(200, content_type, f.read(), extra_headers)

    def serve_static_dir(self, base_dir: str, rel_path: str) -> None:
        rel = rel_path.lstrip("/") or "index.html"
        real_base = os.path.realpath(base_dir)
        target = os.path.realpath(os.path.join(real_base, rel))
        if (target != real_base and not target.startswith(real_base + os.sep)) or not os.path.isfile(target):
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

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self) -> None:
        raw_path = self.path.split("?")[0]
        path = raw_path.rstrip("/") or "/"
        qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")

        # Instructor-only routes
        instructor_routes = {"/", "/monitor", "/api/status", "/api/submission", "/api/submission/download", "/api/submissions.zip"}
        if path in instructor_routes or raw_path == "/solution" or raw_path.startswith("/solution/"):
            if not self.is_instructor():
                if path in ("/", "/monitor"):
                    self.send_bytes(401, "text/html; charset=utf-8", PIN_LOGIN_HTML.encode("utf-8"))
                else:
                    self.send_json(401, {"error": "เฉพาะผู้สอนเท่านั้น (กรุณายืนยันตัวตนด้วย PIN)"})
                return

        if path in ("/", "/monitor"):
            html = MONITOR_HTML.replace("__LAN_IP__", SERVER_IP).replace("__PORT__", str(SERVER_PORT))
            self.send_bytes(200, "text/html; charset=utf-8", html.encode("utf-8"))
        elif path in ("/download", "/get", "/submit", "/workshop"):
            html = DOWNLOAD_HTML.replace("__LAN_IP__", SERVER_IP).replace("__PORT__", str(SERVER_PORT))
            self.send_bytes(200, "text/html; charset=utf-8", html.encode("utf-8"))
        elif path == "/theory-exam":
            self.serve_static_file(THEORY_HTML_FILE)
        elif path == "/links":
            self.serve_static_file(LINKS_HTML_FILE)
        elif path == "/05_Teaching_Kit_และระบบประเมินผล/assessment/form_links.json" or path == "/form_links.json":
            self.serve_static_file(FORM_LINKS_FILE, "application/json; charset=utf-8")
        elif path == "/download/exam_starter.html":
            self.serve_static_file(
                STARTER_HTML_FILE,
                "text/html; charset=utf-8",
                {"Content-Disposition": 'attachment; filename="exam_starter.html"'},
            )
        elif path == "/download/starter.zip":
            if not os.path.isdir(STARTER_DIR):
                self.send_json(404, {"error": "ไม่พบโฟลเดอร์ starter"})
                return
            self.send_bytes(
                200,
                "application/zip",
                zip_directory_bytes(STARTER_DIR, "exam_starter"),
                {"Content-Disposition": 'attachment; filename="exam_starter.zip"'},
            )
        elif path.startswith("/download/workshop/") and path.endswith(".zip"):
            ws_id = path[len("/download/workshop/"):-len(".zip")].lower()
            if ws_id not in WORKSHOP_IDS:
                self.send_json(404, {"error": "ไม่พบชุด Workshop ที่ระบุ"})
                return
            ws_starter = os.path.join(WORKSHOPS_ROOT, ws_id, "starter")
            if not os.path.isdir(ws_starter):
                self.send_json(404, {"error": f"ไม่พบโฟลเดอร์ {ws_id}/starter"})
                return
            self.send_bytes(
                200,
                "application/zip",
                zip_directory_bytes(ws_starter, f"{ws_id}_starter"),
                {"Content-Disposition": f'attachment; filename="{ws_id}_starter.zip"'},
            )
        elif path == "/prompt":
            self.serve_static_file(PROMPT_FILE)
        elif path == "/notifications":
            self.serve_static_file(NOTIFICATIONS_FILE)
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
        elif path == "/api/notify":
            self.send_json(200, {"ok": True, "info": "พร้อมรับ POST JSON { sender, condition, title, message }"})
        elif path == "/api/student/status":
            sender = (qs.get("sender") or [""])[0].strip()
            with state_lock:
                st = state["students"].get(sender, {})
                ws = st.get("workshops") or {}
                live_count = sum(1 for k in ("over_volt", "over_curr", "low_water") if st.get(k))
                waiting = [h for h in state["help_requests"] if h.get("status") == "waiting"]
                # Oldest waiting first for fair queue numbering
                waiting_oldest = list(reversed(waiting))
                waiting_pos = 0
                for idx, h in enumerate(waiting_oldest, 1):
                    if h.get("sender") == sender:
                        waiting_pos = idx
                        break
                body = {
                    "class_stage": state["class_stage"],
                    "workshops": ws,
                    "live_cases_passed": live_count,
                    "help_summary": {"waiting_pos": waiting_pos},
                }
            self.send_json(200, body)
        elif path == "/api/status":
            with state_lock:
                maybe_advance_scenario()
                sc = state["scenario"]
                body = {
                    "class_stage": state["class_stage"],
                    "mode": state["mode"],
                    "scenario": sc,
                    "scenario_label": SCENARIOS.get(sc, SCENARIOS["normal"])["label"],
                    "latest_reading": state["latest_reading"],
                    "students": state["students"],
                    "notifications": state["notifications"],
                    "help_requests": state["help_requests"],
                    "theory_submissions": state["theory_submissions"],
                    "pin_hint": INSTRUCTOR_PIN,
                }
            self.send_json(200, body)
        elif path == "/api/submission":
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
                    self.send_json(200, {"ok": True, "isZip": False, "content": f.read()})
        elif path == "/api/submission/download":
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
            raw_zip = zip_directory_bytes(SUBMISSIONS_DIR, "submissions")
            self.send_bytes(
                200,
                "application/zip",
                raw_zip,
                {"Content-Disposition": 'attachment; filename="student_submissions.zip"'},
            )
        elif raw_path == "/solution" or raw_path.startswith("/solution/"):
            self.serve_static_dir(SOLUTION_DIR, raw_path[len("/solution"):])
        elif raw_path == "/starter" or raw_path.startswith("/starter/"):
            self.serve_static_dir(STARTER_DIR, raw_path[len("/starter"):])
        else:
            self.send_json(404, {"error": "ไม่พบ " + path})

    def _read_json_body(self) -> Tuple[Optional[Any], bool]:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "ขนาดข้อมูลรวมใหญ่เกินกำหนด (สูงสุด 20 MB)"})
            return None, False
        raw = self.rfile.read(length).decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
            return body, True
        except ValueError:
            self.send_json(400, {"error": "body ไม่ใช่ JSON (ลืม JSON.stringify หรือเปล่า)", "received": raw[:200]})
            return None, False

    def do_POST(self) -> None:
        raw_path = self.path.split("?")[0]
        path = raw_path.rstrip("/") or "/"
        body, ok = self._read_json_body()
        if not ok:
            return
        fields = body if isinstance(body, dict) else {}

        if path == "/api/auth":
            ip = self.client_address[0]
            now = time.time()
            fails = [ts for ts in auth_failures.get(ip, []) if now - ts <= AUTH_LOCK_SEC]
            auth_failures[ip] = fails
            if len(fails) >= AUTH_MAX_FAILS:
                self.send_json(429, {"error": "กรอก PIN ผิดเกินกำหนด กรุณารอ 1 นาที"})
                return
            pin = str(fields.get("pin") or "").strip()
            if hmac.compare_digest(pin, INSTRUCTOR_PIN):
                auth_failures.pop(ip, None)
                self.send_json(
                    200,
                    {"ok": True},
                    {"Set-Cookie": f"boi_inst={INSTRUCTOR_SESSION_TOKEN}; Path=/; HttpOnly; SameSite=Lax"},
                )
                return
            fails.append(now)
            auth_failures[ip] = fails
            self.send_json(401, {"error": "รหัส PIN ไม่ถูกต้อง"})
            return

        # Instructor-only POST routes
        if path in ("/api/control", "/api/roster", "/api/reset", "/api/help/resolve", "/api/grade", "/api/workshop/grade", "/api/audit/export"):
            if not self.is_instructor():
                self.send_json(401, {"error": "เฉพาะผู้สอนเท่านั้น (กรุณายืนยันตัวตนด้วย PIN)"})
                return

        if path == "/api/submit":
            sender = str(fields.get("sender") or "").strip()
            files_in = fields.get("files") if isinstance(fields.get("files"), list) else []
            if not sender:
                self.send_json(400, {"error": "กรุณาระบุชื่อผู้ส่ง (sender)"})
                return
            safe_sender = safe_name(sender, "student")
            saved_items, err = save_uploaded_files(os.path.join(SUBMISSIONS_DIR, safe_sender), safe_sender, files_in)
            if err or not saved_items:
                self.send_json(400, {"error": err})
                return
            with state_lock:
                st = ensure_student(sender)
                st["submissions"].extend(saved_items)
                st["last_seen"] = now_hms()
                save_progress()
            print(f"[{now_hms()}] [ส่งไฟล์สอบ] {sender} -> {', '.join(x['filename'] for x in saved_items)}", flush=True)
            self.send_json(200, {"ok": True, "sender": sender, "saved": saved_items, "time": now_hms()})
            return

        if path == "/api/workshop/submit":
            sender = str(fields.get("sender") or "").strip()
            ws_id = str(fields.get("ws_id") or "").strip().lower()
            files_in = fields.get("files") if isinstance(fields.get("files"), list) else []
            if not sender:
                self.send_json(400, {"error": "กรุณาระบุชื่อผู้ส่ง (sender)"})
                return
            if ws_id not in WORKSHOP_IDS:
                self.send_json(400, {"error": "กรุณาเลือก Workshop ที่ต้องการส่ง (w1–w4)"})
                return
            safe_sender = safe_name(sender, "student")
            target_dir = os.path.join(WORKSHOP_SUBMISSIONS_DIR, ws_id, safe_sender)
            rel_prefix = f"_workshops/{ws_id}/{safe_sender}"
            saved_items, err = save_uploaded_files(target_dir, rel_prefix, files_in)
            if err or not saved_items:
                self.send_json(400, {"error": err})
                return
            with state_lock:
                st = ensure_student(sender)
                st["workshops"][ws_id].extend(saved_items)
                st["last_seen"] = now_hms()
                save_progress()
            print(f"[{now_hms()}] [ส่ง {ws_id.upper()}] {sender} -> {', '.join(x['filename'] for x in saved_items)}", flush=True)
            self.send_json(200, {"ok": True, "ws_id": ws_id, "sender": sender, "saved": saved_items, "time": now_hms()})
            return

        if path == "/api/help":
            sender = str(fields.get("sender") or "").strip()
            scope = "workshop" if str(fields.get("scope") or "").strip().lower() == "workshop" else "exam"
            topic = str(fields.get("topic") or "ขอความช่วยเหลือ").strip()[:100]
            note = str(fields.get("note") or "").strip()[:240]
            if not sender:
                self.send_json(400, {"error": "กรุณาระบุเลขที่-ชื่อผู้เรียนก่อนกดขอความช่วยเหลือ"})
                return
            with state_lock:
                ensure_student(sender)
                # Prevent duplicate active requests in the same scope while waiting
                waiting_oldest = list(reversed([h for h in state["help_requests"] if h.get("status") == "waiting"]))
                for idx, h in enumerate(waiting_oldest, 1):
                    if h.get("sender") == sender and h.get("scope") == scope:
                        self.send_json(200, {"ok": True, "already_waiting": True, "id": h["id"], "queue_position": idx})
                        return
                req_id = f"h_{int(time.time() * 1000)}_{secrets.token_hex(2)}"
                entry = {
                    "id": req_id,
                    "time": now_hms(),
                    "ip": self.client_address[0],
                    "sender": sender,
                    "scope": scope,
                    "topic": topic,
                    "note": note,
                    "status": "waiting",
                    "resolution": "",
                    "instructor_note": "",
                    "resolved_at": "",
                }
                state["help_requests"].insert(0, entry)
                state["help_requests"] = state["help_requests"][:300]
                waiting_count = sum(1 for h in state["help_requests"] if h.get("status") == "waiting")
                save_progress()
            print(f"[{now_hms()}] [HELP {scope}] {sender}: {topic} {note}", flush=True)
            self.send_json(200, {"ok": True, "id": req_id, "queue_position": waiting_count})
            return

        if path == "/api/help/resolve":
            req_id = str(fields.get("id") or "").strip()
            res_type = str(fields.get("resolution") or "hint").strip().lower()
            if res_type not in ("tech_issue", "hint", "code_fix"):
                self.send_json(400, {"error": "ประเภทการช่วยเหลือไม่ถูกต้อง"})
                return
            note = str(fields.get("instructor_note") or "").strip()[:200]
            with state_lock:
                found = None
                for h in state["help_requests"]:
                    if h.get("id") == req_id:
                        h["status"] = "resolved"
                        h["resolution"] = res_type
                        h["instructor_note"] = note
                        h["resolved_at"] = now_hms()
                        found = h
                        break
                if not found:
                    self.send_json(404, {"error": "ไม่พบคำขอความช่วยเหลือนี้"})
                    return
                refresh_student_help_summaries()
                save_progress()
            self.send_json(200, {"ok": True, "resolved": found})
            return

        if path == "/api/theory/submit":
            student_name = str(fields.get("studentName") or "").strip()
            if not student_name:
                self.send_json(400, {"error": "กรุณาระบุชื่อ-นามสกุล"})
                return
            record = {
                "time": now_hms(),
                "cohort": str(fields.get("cohort") or "").strip(),
                "seatNo": str(fields.get("seatNo") or "").strip(),
                "studentName": student_name,
                "department": str(fields.get("department") or "").strip(),
                "postHr20": float(fields.get("postHr20") or 0),
                "topicScores": [float(x) for x in (fields.get("topicScores") or [0]*6)[:6]],
                "theory30": float(fields.get("theory30") or 0),
            }
            with state_lock:
                state["theory_submissions"] = [
                    r for r in state["theory_submissions"]
                    if not (r.get("studentName") == student_name and r.get("seatNo") == record["seatNo"])
                ]
                state["theory_submissions"].append(record)
                save_progress()
            print(f"[{now_hms()}] [Theory LAN] {record['seatNo']}-{student_name}: {record['theory30']}/30 (HR {record['postHr20']}/20)", flush=True)
            self.send_json(200, {"ok": True, "time": now_hms()})
            return

        if path == "/api/grade":
            with state_lock:
                cnt = grade_all_exam_submissions_locked()
                save_progress()
            self.send_json(200, {"ok": True, "graded": cnt})
            return

        if path == "/api/workshop/grade":
            with state_lock:
                cnt = grade_all_workshops_locked()
                save_progress()
            self.send_json(200, {"ok": True, "graded": cnt})
            return

        if path == "/api/audit/export":
            cohort = str(fields.get("cohort") or "รุ่นที่ 4").strip()
            theory_csv = str(fields.get("theory_csv") or "").strip()
            parsed_csv = parse_theory_csv(theory_csv) if theory_csv else {}

            with state_lock:
                grade_all_exam_submissions_locked()
                grade_all_workshops_locked()

                # Merge theory lookup from CSV + LAN theory_submissions
                theory_lookup: Dict[str, Dict[str, Any]] = dict(parsed_csv)
                for ts in state["theory_submissions"]:
                    t_rec = {
                        "name": ts.get("studentName", ""),
                        "seat": ts.get("seatNo", ""),
                        "dept": ts.get("department", ""),
                        "pre_20": None,
                        "post_hr_20": ts.get("postHr20"),
                        "topics": ts.get("topicScores") or [0]*6,
                    }
                    if t_rec["name"]:
                        theory_lookup[t_rec["name"]] = t_rec
                    if t_rec["seat"]:
                        theory_lookup[f"seat:{str(t_rec['seat']).zfill(2)}"] = t_rec

                students = sorted(state["students"].values(), key=lambda x: x.get("sender", ""))
                rows_data: List[Dict[str, Any]] = []
                for s in students:
                    sender = s.get("sender", "")
                    seat_m = re.match(r"^(\d+)[-_\s]*(.+)$", sender)
                    seat_key = f"seat:{seat_m.group(1).zfill(2)}" if seat_m else ""
                    name_part = seat_m.group(2).strip() if seat_m else sender
                    t_rec = theory_lookup.get(sender) or theory_lookup.get(name_part) or (theory_lookup.get(seat_key) if seat_key else None) or {}

                    ws_grades = s.get("workshop_grades") or {}
                    ws_scores = [ws_grades[w]["raw_5"] if w in ws_grades and ws_grades[w].get("ok") else 0.0 for w in WORKSHOP_IDS]
                    has_any_ws = any(w in ws_grades for w in WORKSHOP_IDS)

                    ag = s.get("auto_grade") or {}
                    todos = ag.get("todo_scores") if ag.get("ok") else []
                    prac_deduct = round(float(ag.get("dup_penalty") or 0) + float(ag.get("false_alarm_penalty") or 0) + float(ag.get("help_penalty") or 0), 1)

                    note_bits = []
                    if ag.get("live_bonus_info"):
                        note_bits.append(ag["live_bonus_info"])
                    if ag.get("notes"):
                        note_bits.extend(ag["notes"])

                    rows_data.append({
                        "full_name": t_rec.get("name") or name_part,
                        "dept": t_rec.get("dept") or "",
                        "pre_20": t_rec.get("pre_20"),
                        "post_hr_20": t_rec.get("post_hr_20"),
                        "topics": t_rec.get("topics") or [],
                        "workshops": ws_scores if has_any_ws else [],
                        "ws_help_penalty": (s.get("workshop_help_info") or {}).get("applied_penalty", 0.0),
                        "practical_todos": todos or [],
                        "practical_deduct": prac_deduct if todos else None,
                        "audit_note": " | ".join(note_bits),
                    })

                help_snapshot = list(reversed(state["help_requests"]))
                save_progress()

            fd, tmp_xlsx = tempfile.mkstemp(suffix=".xlsx")
            os.close(fd)
            try:
                export_audit_workbook(
                    tmp_xlsx,
                    cohort_title=f"หลักสูตร การออกแบบ พัฒนา และบูรณาการแอปพลิเคชันระดับองค์กร (Enterprise Application) {cohort}",
                    date_subtitle=f"สรุปผลอัตโนมัติจากระบบ BOI Classroom Portal v2 · ส่งออกวันที่ {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}",
                    rows_data=rows_data,
                    help_requests=help_snapshot,
                    blank_rows=max(12, len(rows_data)),
                )
                with open(tmp_xlsx, "rb") as f:
                    xlsx_bytes = f.read()
            finally:
                if os.path.isfile(tmp_xlsx):
                    os.remove(tmp_xlsx)

            self.send_bytes(
                200,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                xlsx_bytes,
                {"Content-Disposition": f'attachment; filename="BOI_Audit_v2.xlsx"'},
            )
            return

        if path == "/api/notify":
            sender = str(fields.get("sender") or fields.get("name") or fields.get("student") or "").strip()
            title = str(fields.get("title") or "").strip()
            message = str(fields.get("message") or "").strip()
            condition = str(fields.get("condition") or "").strip()
            effective_title = title

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
                self.send_json(400, {"error": "ยังไม่ได้ส่งชื่อผู้ส่ง (sender)", "received": body})
                return
            if not effective_title and not message:
                self.send_json(400, {"error": "ต้องส่งหัวข้อหรือข้อความแจ้งเตือน (title หรือ message)", "received": body})
                return

            detected = classify_alert(condition, effective_title, message)
            stamp = now_hms()
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
            print(f"[{stamp}] {sender} ({client_ip}) -> {verdict_text}", flush=True)
            self.send_json(200, {"ok": True, "sender": sender, "verdict": verdict, "verdict_text": verdict_text})
            return

        if path == "/api/control":
            with state_lock:
                if "class_stage" in fields and fields["class_stage"] in ("workshop", "exam"):
                    state["class_stage"] = fields["class_stage"]
                if "mode" in fields and fields["mode"] in ("manual", "auto_cycle", "auto_random"):
                    state["mode"] = fields["mode"]
                    state["last_switch"] = time.time()
                if "scenario" in fields and fields["scenario"] in SCENARIOS:
                    state["scenario"] = fields["scenario"]
                    state["prev_scenario"] = ""
                    state["last_auto_switch"] = 0.0
                    state["last_switch"] = time.time()
                save_progress()
                resp = {"ok": True, "class_stage": state["class_stage"], "mode": state["mode"], "scenario": state["scenario"]}
            self.send_json(200, resp)
            return

        if path == "/api/roster":
            names = fields.get("names") or []
            with state_lock:
                for n in names:
                    clean = str(n).strip()
                    if clean:
                        ensure_student(clean)
                save_progress()
            self.send_json(200, {"ok": True})
            return

        if path == "/api/reset":
            with state_lock:
                state["students"] = {}
                state["notifications"] = []
                state["help_requests"] = []
                state["theory_submissions"] = []
                state["last_served_by_ip"] = {}
                save_progress()
            self.send_json(200, {"ok": True})
            return

        self.send_json(404, {"error": "ไม่พบ " + path})

    def log_message(self, fmt: str, *args: Any) -> None:
        pass


def create_server(host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
    global SERVER_IP, SERVER_PORT
    SERVER_IP = lan_ip()
    load_saved_progress()
    srv = ThreadingHTTPServer((host, port), ExamHandler)
    SERVER_PORT = srv.server_address[1]
    return srv


if __name__ == "__main__":
    req_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = create_server("0.0.0.0", req_port)
    print("=" * 72)
    print("🚀 เปิดระบบ BOI Classroom Portal v2 เรียบร้อย!")
    print(f"  1) กระดานผู้สอน (localhost เข้าทันที / LAN PIN = {INSTRUCTOR_PIN}): http://localhost:{SERVER_PORT}/")
    print(f"  2) พอร์ทัลผู้เรียน (Workshop + สอบ + Help Queue):      http://{SERVER_IP}:{SERVER_PORT}/download")
    print(f"  3) ข้อสอบทฤษฎีสำรอง (LAN 30 ข้อ):                     http://{SERVER_IP}:{SERVER_PORT}/theory-exam")
    print(f"  4) ศูนย์รวมลิงก์ & QR (HTTP Mode):                    http://localhost:{SERVER_PORT}/links")
    print(f"  5) จอแจ้งเตือน (Lockscreen) / โจทย์ / เฉลย:            http://localhost:{SERVER_PORT}/notifications")
    print(f"  6) API_URL สำหรับผู้เรียน:     http://{SERVER_IP}:{SERVER_PORT}/api/meter")
    print(f"  7) WEBHOOK_URL สำหรับผู้เรียน: http://{SERVER_IP}:{SERVER_PORT}/api/notify")
    print("=" * 72, flush=True)
    server.serve_forever()
