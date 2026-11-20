"""Sandboxed Node.js & Static Auto-Grader for Practical Exam and Workshops 1-4.

Executes student JS inside an isolated Node `vm` context (no fs/net/child_process access)
with a 3-second timeout and fake DOM + fetch mocks to verify actual runtime behavior.
"""

import json
import os
import re
import shutil
import subprocess
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from grading_rules import calculate_help_penalty, clamp_score


def _extract_inline_scripts(html_text: str) -> str:
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", html_text, flags=re.I | re.S)
    return "\n\n".join(s.strip() for s in scripts if s.strip())


def _find_duplicate_functions(js_code: str) -> List[str]:
    names = re.findall(r"(?m)^\s*(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", js_code)
    seen = set()
    dups = []
    for name in names:
        if name in seen and name not in dups:
            dups.append(name)
        seen.add(name)
    return dups


def _load_submission_bundle(files_paths: List[str]) -> Tuple[str, str, str]:
    """Return (html_text, css_text, js_text) extracted from submitted html/js/css/zip files."""
    html_parts: List[str] = []
    css_parts: List[str] = []
    js_parts: List[str] = []

    for fpath in files_paths:
        if not fpath or not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fpath)[1].lower()
        if ext in (".html", ".htm"):
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
            html_parts.append(txt)
            inline_js = _extract_inline_scripts(txt)
            if inline_js:
                js_parts.append(inline_js)
        elif ext == ".js":
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                js_parts.append(f.read())
        elif ext == ".css":
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                css_parts.append(f.read())
        elif ext == ".zip":
            try:
                with zipfile.ZipFile(fpath, "r") as zf:
                    for name in sorted(zf.namelist()):
                        zext = os.path.splitext(name)[1].lower()
                        if zext not in (".html", ".htm", ".js", ".css"):
                            continue
                        raw = zf.read(name).decode("utf-8", errors="replace")
                        if zext in (".html", ".htm"):
                            html_parts.append(raw)
                            inline_js = _extract_inline_scripts(raw)
                            if inline_js:
                                js_parts.append(inline_js)
                        elif zext == ".js":
                            js_parts.append(raw)
                        elif zext == ".css":
                            css_parts.append(raw)
            except zipfile.BadZipFile:
                pass

    return "\n".join(html_parts), "\n".join(css_parts), "\n".join(js_parts)


_EXAM_HARNESS_JS = r"""
const vm = require('vm');

let inputBuf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { inputBuf += chunk; });
process.stdin.on('end', async () => {
  try {
    const req = JSON.parse(inputBuf);
    const result = await runExamTests(req.code || '');
    process.stdout.write(JSON.stringify(result));
  } catch (err) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(err && err.message || err) }));
  }
});

function makeDom() {
  const elements = {};
  const ids = [
    'voltage', 'current', 'water', 'power',
    'status', 'updated', 'notify-result', 'student-name',
    'check-btn', 'auto-toggle'
  ];
  for (const id of ids) {
    elements[id] = {
      id,
      _text: '',
      value: '',
      checked: false,
      disabled: false,
      _classes: new Set(),
      className: '',
      classList: {
        add: (...cls) => cls.forEach(c => elements[id]._classes.add(c)),
        remove: (...cls) => cls.forEach(c => elements[id]._classes.delete(c)),
        contains: (c) => elements[id]._classes.has(c) || String(elements[id].className).split(/\s+/).includes(c),
      },
      addEventListener: () => {},
    };
    Object.defineProperty(elements[id], 'textContent', {
      get() { return this._text; },
      set(v) { this._text = String(v ?? ''); },
    });
    Object.defineProperty(elements[id], 'innerText', {
      get() { return this._text; },
      set(v) { this._text = String(v ?? ''); },
    });
  }
  return {
    elements,
    document: {
      getElementById: (id) => elements[id] || null,
      querySelector: (sel) => {
        if (sel && sel.startsWith('#')) return elements[sel.slice(1)] || null;
        return null;
      },
    },
  };
}

async function runExamTests(userCode) {
  const { elements, document } = makeDom();
  const fetchCalls = [];
  let mockMeter = { line: 'A', electric: { voltage: 230.0, current: 15.0 }, water: { flow: 3.2 } };

  const fakeFetch = async (url, opts) => {
    const method = (opts && opts.method ? String(opts.method) : 'GET').toUpperCase();
    const call = { url: String(url || ''), method, headers: (opts && opts.headers) || {}, body: opts ? opts.body : undefined };
    fetchCalls.push(call);
    if (method === 'GET') {
      return {
        ok: true,
        status: 200,
        json: async () => JSON.parse(JSON.stringify(mockMeter)),
        text: async () => JSON.stringify(mockMeter),
      };
    }
    return {
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
      text: async () => JSON.stringify({ ok: true }),
    };
  };

  const sandbox = {
    document,
    fetch: fakeFetch,
    console: { log: () => {}, warn: () => {}, error: () => {} },
    setInterval: () => 1,
    clearInterval: () => {},
    setTimeout: () => 1,
    clearTimeout: () => {},
    window: { location: { protocol: 'http:', origin: 'http://localhost:8000' } },
    Math, Number, String, Boolean, Array, Object, JSON, Date, Error, Promise,
  };
  vm.createContext(sandbox);

  try {
    vm.runInContext(userCode, sandbox, { timeout: 1200 });
  } catch (err) {
    return { ok: false, syntaxOrRuntimeError: String(err && err.message || err) };
  }

  const bindings = vm.runInContext(`({
    api: typeof API_URL !== 'undefined' ? API_URL : '',
    wh: typeof WEBHOOK_URL !== 'undefined' ? WEBHOOK_URL : '',
    name: typeof STUDENT_NAME !== 'undefined' ? STUDENT_NAME : '',
    calcPower: typeof calcPower === 'function' ? calcPower : null,
    showMeterValues: typeof showMeterValues === 'function' ? showMeterValues : null,
    checkCondition: typeof checkCondition === 'function' ? checkCondition : null,
    handleAlert: typeof handleAlert === 'function' ? handleAlert : null,
  })`, sandbox, { timeout: 200 });

  const todo1 = {
    hasApi: Boolean(String(bindings.api).trim() && String(bindings.api).includes('/api/meter')),
    hasWebhook: Boolean(String(bindings.wh).trim() && String(bindings.wh).includes('/api/notify')),
    hasStudentName: Boolean(String(bindings.name).trim() || String(elements['student-name'].value).trim()),
  };

  // TODO 3: calcPower
  let powerTests = { normal: false, overload: false, zero: false };
  if (bindings.calcPower) {
    try {
      powerTests.normal = Math.abs(Number(bindings.calcPower(230, 15)) - 3450) < 0.01;
      powerTests.overload = Math.abs(Number(bindings.calcPower(240, 20.5)) - 4920) < 0.01;
      powerTests.zero = Math.abs(Number(bindings.calcPower(0, 10)) - 0) < 0.01;
    } catch (e) {}
  }

  // TODO 2: showMeterValues
  let domTests = { voltage: false, current: false, water: false, power: false };
  if (bindings.showMeterValues) {
    try {
      bindings.showMeterValues({ line: 'A', electric: { voltage: 231.4, current: 15.6 }, water: { flow: 3.2 } });
      domTests.voltage = elements.voltage._text.includes('231.4');
      domTests.current = elements.current._text.includes('15.6');
      domTests.water = elements.water._text.includes('3.2');
      domTests.power = Number(elements.power._text) >= 3609 && Number(elements.power._text) <= 3610;
    } catch (e) {}
  }

  // TODO 4: checkCondition + exact boundary thresholds
  const condCases = [
    ['normal_mid', [230, 15, 3.2], 'normal'],
    ['volt_boundary_240', [240, 15, 3.2], 'normal'],
    ['volt_over_240_1', [240.1, 15, 3.2], 'over_volt'],
    ['volt_over_250', [250, 15, 3.2], 'over_volt'],
    ['curr_boundary_20', [230, 20, 3.2], 'normal'],
    ['curr_over_20_1', [230, 20.1, 3.2], 'over_curr'],
    ['water_boundary_1_5', [230, 15, 1.5], 'normal'],
    ['water_low_1_4', [230, 15, 1.4], 'low_water'],
  ];
  const condResults = {};
  if (bindings.checkCondition) {
    for (const [label, args, expected] of condCases) {
      try {
        condResults[label] = bindings.checkCondition(...args) === expected;
      } catch (e) {
        condResults[label] = false;
      }
    }
  } else {
    for (const [label] of condCases) condResults[label] = false;
  }

  // TODO 5: Webhook POST, JSON stringify, no normal spam, no duplicate same state, reset after normal
  let alertTests = {
    silentOnNormal: false,
    postsOnOverVolt: false,
    validJsonAndContentType: false,
    hasSender: false,
    dedupSameCondition: false,
    resetsAfterNormal: false,
  };
  if (bindings.handleAlert) {
    if (!elements['student-name'].value.trim() && !String(bindings.name).trim()) {
      elements['student-name'].value = '00-Test';
    }
    try {
      fetchCalls.length = 0;
      await bindings.handleAlert('normal', 230, 15, 3.2);
      const normalPosts = fetchCalls.filter(c => c.method === 'POST').length;
      alertTests.silentOnNormal = normalPosts === 0;

      fetchCalls.length = 0;
      await bindings.handleAlert('over_volt', 250, 15, 3.2);
      const firstPosts = fetchCalls.filter(c => c.method === 'POST');
      alertTests.postsOnOverVolt = firstPosts.length === 1;
      if (firstPosts.length >= 1) {
        const call = firstPosts[0];
        const hdrs = Object.keys(call.headers || {}).reduce((acc, k) => { acc[k.toLowerCase()] = String(call.headers[k]); return acc; }, {});
        const hasCt = (hdrs['content-type'] || '').toLowerCase().includes('application/json');
        try {
          const parsed = typeof call.body === 'string' ? JSON.parse(call.body) : null;
          if (parsed && typeof parsed === 'object') {
            alertTests.validJsonAndContentType = hasCt || Boolean(parsed.title || parsed.message || parsed.condition);
            alertTests.hasSender = Boolean(String(parsed.sender || parsed.name || parsed.student || '').trim()) || (Boolean(parsed.title) && Boolean(parsed.message));
          }
        } catch (e) {}
      }

      fetchCalls.length = 0;
      await bindings.handleAlert('over_volt', 251, 15, 3.2);
      alertTests.dedupSameCondition = fetchCalls.filter(c => c.method === 'POST').length === 0;

      await bindings.handleAlert('normal', 230, 15, 3.2);
      fetchCalls.length = 0;
      await bindings.handleAlert('over_volt', 248, 15, 3.2);
      alertTests.resetsAfterNormal = fetchCalls.filter(c => c.method === 'POST').length === 1;
    } catch (e) {}
  }

  return { ok: true, todo1, powerTests, domTests, condResults, alertTests };
}
"""


_WORKSHOP_HARNESS_JS = r"""
const vm = require('vm');

let inputBuf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { inputBuf += chunk; });
process.stdin.on('end', async () => {
  try {
    const req = JSON.parse(inputBuf);
    const result = await testWorkshop(req.wsId, req.code || '');
    process.stdout.write(JSON.stringify(result));
  } catch (err) {
    process.stdout.write(JSON.stringify({ ok: false, error: String(err && err.message || err) }));
  }
});

function makeWsDom() {
  const listeners = {};
  const els = {};
  const ids = ['voltage', 'current', 'water', 'power', 'status', 'start-btn', 'stop-btn', 'volt-input', 'warning', 'updated', 'notify-result'];
  for (const id of ids) {
    els[id] = {
      id,
      _text: '',
      value: '',
      disabled: false,
      className: '',
      _classes: new Set(),
      classList: {
        add: (...c) => c.forEach(x => els[id]._classes.add(x)),
        remove: (...c) => c.forEach(x => els[id]._classes.delete(x)),
        contains: (x) => els[id]._classes.has(x) || String(els[id].className).split(/\s+/).includes(x),
      },
      addEventListener: (ev, fn) => {
        listeners[id + ':' + ev] = listeners[id + ':' + ev] || [];
        listeners[id + ':' + ev].push(fn);
      },
    };
    Object.defineProperty(els[id], 'textContent', { get() { return this._text; }, set(v) { this._text = String(v ?? ''); } });
    Object.defineProperty(els[id], 'innerText', { get() { return this._text; }, set(v) { this._text = String(v ?? ''); } });
  }
  return {
    els,
    listeners,
    document: {
      getElementById: (id) => els[id] || null,
      querySelector: (sel) => (sel && sel.startsWith('#') ? els[sel.slice(1)] || null : null),
    },
  };
}

async function testWorkshop(wsId, userCode) {
  const { els, listeners, document } = makeWsDom();
  const fetchCalls = [];
  const intervalCalls = [];
  const fakeMeter = { line: 'A', electric: { voltage: 245.5, current: 16.2 }, water: { flow: 3.1 } };

  const sandbox = {
    document,
    console: { log: () => {}, warn: () => {}, error: () => {} },
    setInterval: (fn, ms) => { intervalCalls.push(ms); return 1; },
    clearInterval: () => {},
    setTimeout: () => 1,
    fetch: async (url, opts) => {
      const method = (opts && opts.method ? String(opts.method) : 'GET').toUpperCase();
      fetchCalls.push({ url: String(url || ''), method, headers: (opts && opts.headers) || {}, body: opts ? opts.body : undefined });
      return { ok: true, status: 200, json: async () => fakeMeter, text: async () => JSON.stringify(fakeMeter) };
    },
    window: { location: { protocol: 'http:' } },
    Math, Number, String, Boolean, Array, Object, JSON, Date, Error, Promise,
  };
  vm.createContext(sandbox);
  try {
    vm.runInContext(userCode, sandbox, { timeout: 1200 });
  } catch (err) {
    return { ok: false, error: String(err && err.message || err) };
  }

  if (wsId === 'w2') {
    let statusRun = false, statusStop = false, warnHigh = false, warnBoundary = false;
    try {
      if (typeof sandbox.setStatus === 'function') {
        sandbox.setStatus(true);
        statusRun = els.status._text.toUpperCase().includes('RUN') && els.status.className.includes('run');
        sandbox.setStatus(false);
        statusStop = els.status._text.toUpperCase().includes('STOP') && els.status.className.includes('stop');
      }
      if (typeof sandbox.checkVoltage === 'function') {
        warnHigh = Boolean(sandbox.checkVoltage(245));
        warnBoundary = sandbox.checkVoltage(240) === '';
      }
    } catch (e) {}
    const hasEvents = (listeners['start-btn:click'] || []).length > 0 && (listeners['volt-input:input'] || []).length > 0;
    return { ok: true, checks: { statusRun, statusStop, warnHigh, warnBoundary, hasEvents } };
  }

  if (wsId === 'w3') {
    let fetched = false, domUpdated = false, warnShown = false;
    try {
      if (typeof sandbox.loadMeter === 'function') {
        await sandbox.loadMeter();
        fetched = fetchCalls.some(c => c.method === 'GET');
        domUpdated = els.voltage._text.includes('245.5') && els.current._text.includes('16.2') && els.water._text.includes('3.1');
        warnShown = Boolean(els.warning._text.trim());
      }
    } catch (e) {}
    const hasPolling = intervalCalls.some(ms => ms >= 1000);
    return { ok: true, checks: { fetched, domUpdated, warnShown, hasPolling } };
  }

  if (wsId === 'w4') {
    let postOk = false, validJsonBody = false, startTrigger = false;
    try {
      if (typeof sandbox.notify === 'function') {
        fetchCalls.length = 0;
        await sandbox.notify('Machine started', 'Line A test');
        const p = fetchCalls.find(c => c.method === 'POST');
        postOk = Boolean(p);
        if (p && typeof p.body === 'string') {
          const obj = JSON.parse(p.body);
          validJsonBody = Boolean(obj.title && obj.message);
        }
      }
      if ((listeners['start-btn:click'] || []).length > 0) {
        fetchCalls.length = 0;
        if (typeof sandbox.setStatus === 'function') sandbox.setStatus(false);
        await listeners['start-btn:click'][0]();
        startTrigger = fetchCalls.some(c => c.method === 'POST');
      }
    } catch (e) {}
    return { ok: true, checks: { postOk, validJsonBody, startTrigger } };
  }

  return { ok: true, checks: {} };
}
"""


def _run_node_harness(harness_js: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    node_bin = shutil.which("node")
    if not node_bin:
        return {"ok": False, "error": "Node.js not found in PATH"}
    proc = subprocess.run(
        [node_bin, "-e", harness_js],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        timeout=4,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr.strip() or f"exit {proc.returncode}"}
    try:
        return json.loads(proc.stdout.strip() or "{}")
    except ValueError as exc:
        return {"ok": False, "error": f"Invalid grader output: {exc}"}


def grade_practical_submission(
    files_paths: List[str],
    live_student_record: Optional[Dict[str, Any]] = None,
    help_requests: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Grade practical exam HTML/JS/ZIP submission -> breakdown of TODO 1..5 + live/help adjustments."""
    _, _, js_code = _load_submission_bundle(files_paths)
    if not js_code.strip():
        return {
            "ok": False,
            "error": "ไม่พบโค้ด JavaScript ในไฟล์ที่ส่ง",
            "todo_scores": [0.0, 0.0, 0.0, 0.0, 0.0],
            "raw_50": 0.0,
            "help_penalty": 0.0,
            "false_alarm_penalty": 0.0,
            "final_50": 0.0,
            "notes": ["ไม่พบโค้ด <script> หรือ .js"],
        }

    dups = _find_duplicate_functions(js_code)
    sim = _run_node_harness(_EXAM_HARNESS_JS, {"code": js_code})
    if not sim.get("ok"):
        return {
            "ok": False,
            "error": sim.get("syntaxOrRuntimeError") or sim.get("error") or "รันตรวจโค้ดไม่สำเร็จ",
            "todo_scores": [0.0, 0.0, 0.0, 0.0, 0.0],
            "raw_50": 0.0,
            "help_penalty": 0.0,
            "false_alarm_penalty": 0.0,
            "final_50": 0.0,
            "duplicates": dups,
            "notes": [f"Syntax/Runtime error: {sim.get('syntaxOrRuntimeError') or sim.get('error')}"],
        }

    notes: List[str] = []

    # TODO 1 (10 pts): API_URL (4) + WEBHOOK_URL (4) + STUDENT_NAME (2)
    t1_info = sim.get("todo1", {})
    t1 = (4.0 if t1_info.get("hasApi") else 0.0) + (4.0 if t1_info.get("hasWebhook") else 0.0) + (2.0 if t1_info.get("hasStudentName") else 0.0)
    if t1 < 10:
        notes.append(f"TODO1 ขาดการตั้งค่า: api={t1_info.get('hasApi')}, wh={t1_info.get('hasWebhook')}, name={t1_info.get('hasStudentName')}")

    # TODO 2 (10 pts): voltage (3), current (3), water (3), power DOM update (1)
    dom = sim.get("domTests", {})
    t2 = (3.0 if dom.get("voltage") else 0.0) + (3.0 if dom.get("current") else 0.0) + (3.0 if dom.get("water") else 0.0) + (1.0 if dom.get("power") else 0.0)
    if t2 < 10:
        notes.append(f"TODO2 DOM: V={dom.get('voltage')}, A={dom.get('current')}, W={dom.get('water')}, Power={dom.get('power')}")

    # TODO 3 (10 pts): only award zero case if non-zero cases compute properly (prevents stub `return 0;` free points)
    pwr = sim.get("powerTests", {})
    has_power_calc = bool(pwr.get("normal") or pwr.get("overload"))
    t3 = (5.0 if pwr.get("normal") else 0.0) + (3.0 if pwr.get("overload") else 0.0) + (2.0 if (has_power_calc and pwr.get("zero")) else 0.0)
    if t3 < 10:
        notes.append(f"TODO3 calcPower failed some test cases: {pwr}")

    # TODO 4 (10 pts): require at least one abnormal case handled before scoring normal boundaries
    cond = sim.get("condResults", {})
    abnormal_keys = ("volt_over_250", "curr_over_20_1", "water_low_1_4", "volt_over_240_1")
    has_abnormal = any(cond.get(k) for k in abnormal_keys)
    core_keys = ("normal_mid", "volt_over_250", "curr_over_20_1", "water_low_1_4")
    edge_keys = ("volt_boundary_240", "volt_over_240_1", "curr_boundary_20", "water_boundary_1_5")
    if has_abnormal:
        core_pass = sum(1 for k in core_keys if cond.get(k))
        edge_pass = sum(1 for k in edge_keys if cond.get(k))
        t4 = round((core_pass / len(core_keys)) * 7.0 + (edge_pass / len(edge_keys)) * 3.0, 1)
    else:
        core_pass, edge_pass, t4 = 0, 0, 0.0
    if t4 < 10:
        notes.append(f"TODO4 เงื่อนไขผ่าน core {core_pass}/4, boundary {edge_pass}/4")

    # TODO 5 (10 pts): require POST on over_volt before awarding silent/dedup marks
    al = sim.get("alertTests", {})
    if al.get("postsOnOverVolt"):
        t5 = (
            (2.0 if al.get("silentOnNormal") else 0.0)
            + 3.0
            + (2.0 if al.get("validJsonAndContentType") else 0.0)
            + (1.0 if al.get("hasSender") else 0.0)
            + (1.0 if al.get("dedupSameCondition") else 0.0)
            + (1.0 if al.get("resetsAfterNormal") else 0.0)
        )
    else:
        t5 = 0.0
    if t5 < 10:
        missing = [k for k, v in al.items() if not v]
        notes.append(f"TODO5 ไม่ผ่าน: {', '.join(missing)}")

    raw_50 = round(t1 + t2 + t3 + t4 + t5, 1)

    dup_penalty = 1.0 if dups else 0.0
    if dups:
        notes.append(f"พบการประกาศฟังก์ชันซ้ำในไฟล์ (-1): {', '.join(dups)}")

    live_rec = live_student_record or {}
    false_alarms = int(live_rec.get("false_alarm") or 0)
    false_alarm_penalty = min(1.5, round(false_alarms * 0.5, 1))
    if false_alarm_penalty > 0:
        notes.append(f"ส่งแจ้งเตือนพลาดขณะสถานะปกติ {false_alarms} ครั้ง (-{false_alarm_penalty})")

    # Reward verifying all 3 live cases if recorded cleanly; slight deduction (-1 per missing live case) only if server recorded submissions
    live_cases = [bool(live_rec.get(k)) for k in ("over_volt", "over_curr", "low_water")]
    live_bonus_info = f"ส่งผ่าน Live {sum(live_cases)}/3 เคส"

    earned_after_hygiene = max(0.0, round(raw_50 - dup_penalty - false_alarm_penalty, 1))
    help_info = calculate_help_penalty(help_requests or [], scope="exam", raw_earned=earned_after_hygiene)
    help_penalty = help_info["applied_penalty"]
    if help_penalty > 0:
        notes.append(
            f"หักคะแนนขอความช่วยเหลือสอบ: -{help_penalty} "
            f"(ชี้แนะ {help_info['hint_count']}, แก้โค้ดให้ {help_info['code_fix_count']}, เทคนิคฟรี {help_info['tech_issue_count']})"
        )

    final_50 = clamp_score(earned_after_hygiene - help_penalty, 0.0, 50.0)
    return {
        "ok": True,
        "todo_scores": [round(t1, 1), round(t2, 1), round(t3, 1), round(t4, 1), round(t5, 1)],
        "raw_50": raw_50,
        "duplicates": dups,
        "dup_penalty": dup_penalty,
        "false_alarms": false_alarms,
        "false_alarm_penalty": false_alarm_penalty,
        "live_cases_passed": sum(live_cases),
        "live_bonus_info": live_bonus_info,
        "help_info": help_info,
        "help_penalty": help_penalty,
        "final_50": final_50,
        "notes": notes or ["โค้ดผ่านเกณฑ์ครบทุกจุด"],
    }


def grade_workshop_submission(
    ws_id: str,
    files_paths: List[str],
    help_requests: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Grade one Workshop (w1..w4 -> 0..5 raw pts). Help penalty applies across all workshops cleanly."""
    ws = str(ws_id).strip().lower()
    html_text, css_text, js_code = _load_submission_bundle(files_paths)
    score = 0.0
    notes: List[str] = []

    if ws == "w1":
        if not html_text.strip():
            return {"ok": False, "ws_id": ws, "raw_5": 0.0, "notes": ["ไม่พบไฟล์ index.html"]}
        hl = html_text.lower()
        cl = (css_text + "\n" + html_text).lower()
        checks = {
            "semantic_tags": all(tag in hl for tag in ("<header", "<main", "<section", "<article")),
            "css_link": "style.css" in hl,
            "ids": 'id="voltage"' in hl and 'id="current"' in hl,
            "flexbox": "display: flex" in cl or "display:flex" in cl,
            "theme_colors": "#111827" in cl,
        }
        score = float(sum(1 for v in checks.values() if v))
        missing = [k for k, v in checks.items() if not v]
        if missing:
            notes.append("W1 ยังขาด: " + ", ".join(missing))
    elif ws in ("w2", "w3", "w4"):
        if not js_code.strip():
            return {"ok": False, "ws_id": ws, "raw_5": 0.0, "notes": [f"ไม่พบไฟล์โค้ด JavaScript ใน {ws}"]}
        sim = _run_node_harness(_WORKSHOP_HARNESS_JS, {"wsId": ws, "code": js_code})
        if not sim.get("ok"):
            return {"ok": False, "ws_id": ws, "raw_5": 0.0, "notes": [f"{ws} error: {sim.get('error')}"]}
        checks = sim.get("checks") or {}
        if checks:
            passed = sum(1 for v in checks.values() if v)
            score = round((passed / len(checks)) * 5.0, 1)
            missing = [k for k, v in checks.items() if not v]
            if missing:
                notes.append(f"{ws} ยังไม่ผ่าน: {', '.join(missing)}")
    else:
        return {"ok": False, "ws_id": ws, "raw_5": 0.0, "notes": ["ไม่รู้จักรหัส Workshop"]}

    return {
        "ok": True,
        "ws_id": ws,
        "raw_5": clamp_score(score, 0.0, 5.0),
        "notes": notes or [f"{ws} ผ่านครบถ้วน"],
    }
