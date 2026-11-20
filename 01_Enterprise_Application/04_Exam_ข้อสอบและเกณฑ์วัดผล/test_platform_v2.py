"""Comprehensive verification suite for BOI Training Platform v2.

Covers:
1. Central exam builder sync (`build_exam.py --check`) and schema invariants.
2. Google Apps Script (`create_boi_forms.gs`) syntax + mocked runtime verification.
3. Scoring & Help-Penalty edge cases (`grading_rules.py`).
4. Sandboxed Node.js Auto-Grader (`auto_grader.py`) on practical & W1..W4 files.
5. Embedded UI HTML/JS syntax + ISO-18004 Offline QR encoder reverse-decoding.
6. Live `exam_server.py` HTTP server integration test (isolated temp data dir).
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile

import openpyxl

EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
COURSE_DIR = os.path.dirname(EXAM_DIR)
PRACTICAL_DIR = os.path.join(EXAM_DIR, "practical")
if PRACTICAL_DIR not in sys.path:
    sys.path.insert(0, PRACTICAL_DIR)

import auto_grader  # noqa: E402
import exam_server  # noqa: E402
import grading_rules  # noqa: E402
import portal_ui  # noqa: E402


class TestExamBankAndGAS(unittest.TestCase):
    def test_build_exam_check(self) -> None:
        proc = subprocess.run(
            [sys.executable, os.path.join(EXAM_DIR, "build_exam.py"), "--check"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_gas_syntax_and_mock_execution(self) -> None:
        gas_path = os.path.join(EXAM_DIR, "create_boi_forms.gs")
        with open(gas_path, "r", encoding="utf-8") as f:
            gas_code = f.read()

        syn = subprocess.run(["node", "--check", "-"], input=gas_code, text=True, capture_output=True)
        self.assertEqual(syn.returncode, 0, syn.stderr)

        harness = r"""
const fs = require('fs');
const vm = require('vm');
const gasCode = fs.readFileSync(process.argv[1], 'utf8');

let sheetsStore = [];
let formsStore = {};
let propsStore = {};
let triggersStore = [];
let idSeq = 1;

function makeSheet(name) {
  const sh = {
    _name: name,
    _rows: [],
    _formUrl: null,
    getName: () => sh._name,
    setName: (n) => { sh._name = n; },
    clear: () => { sh._rows = []; },
    getLastRow: () => sh._rows.length,
    getFormUrl: () => sh._formUrl,
    setColumnWidth: () => sh,
    setFrozenRows: () => sh,
    getRange: (r, c, nr, nc) => ({
      getValues: () => {
        const out = [];
        for (let i = 0; i < nr; i++) {
          const row = sh._rows[r - 1 + i] || [];
          out.push(row.slice(c - 1, c - 1 + nc));
        }
        return out;
      },
      setValues: (vals) => {
        vals.forEach((row, idx) => { sh._rows[r - 1 + idx] = row.slice(); });
      },
      setFontWeight: () => {},
    }),
  };
  return sh;
}

const activeSs = {
  _id: 'ss_v2_mock',
  getId: () => 'ss_v2_mock',
  getSheets: () => sheetsStore,
  getSheetByName: (n) => sheetsStore.find(s => s._name === n) || null,
  insertSheet: (n, idx) => { const s = makeSheet(n); sheetsStore.push(s); return s; },
};

function makeForm(title) {
  const id = 'form_' + (idSeq++);
  const items = [];
  const form = {
    _id: id,
    _title: title,
    _responses: [],
    getId: () => id,
    getTitle: () => form._title,
    getPublishedUrl: () => `https://docs.google.com/forms/d/e/${id}/viewform`,
    getEditUrl: () => `https://docs.google.com/forms/d/${id}/edit`,
    setDescription: () => form,
    setIsQuiz: () => form,
    setCollectEmail: () => form,
    setProgressBar: () => form,
    setAllowResponseEdits: () => form,
    setShowLinkToRespondAgain: () => form,
    setConfirmationMessage: () => form,
    setDestination: (type, ssId) => {
      const sh = makeSheet('Form_Responses_' + id);
      sh._formUrl = form.getPublishedUrl();
      sheetsStore.push(sh);
    },
    removeDestination: () => {
      sheetsStore.forEach(s => { if (s._formUrl === form.getPublishedUrl()) s._formUrl = null; });
    },
    getItems: (typeFilter) => typeFilter ? items.filter(i => i._type === typeFilter) : items.slice(),
    deleteItem: (it) => { const idx = items.indexOf(it); if (idx >= 0) items.splice(idx, 1); },
    getResponses: () => form._responses,
    addListItem: () => {
      const it = { _id: idSeq++, _type: 'LIST', _title: '', setTitle(t){this._title=t;return it;}, setChoiceValues(){return it;}, setRequired(){return it;}, getId(){return this._id;}, getType(){return this._type;}, getTitle(){return this._title;} };
      items.push(it); return it;
    },
    addTextItem: () => {
      const it = { _id: idSeq++, _type: 'TEXT', _title: '', setTitle(t){this._title=t;return it;}, setRequired(){return it;}, getId(){return this._id;}, getType(){return this._type;}, getTitle(){return this._title;} };
      items.push(it); return it;
    },
    addPageBreakItem: () => {
      const it = { _id: idSeq++, _type: 'PAGE', _title: '', setTitle(t){this._title=t;return it;}, setHelpText(){return it;}, getId(){return this._id;}, getType(){return this._type;}, getTitle(){return this._title;} };
      items.push(it); return it;
    },
    addMultipleChoiceItem: () => {
      const it = {
        _id: idSeq++, _type: 'MCQ', _title: '', _points: 1,
        setTitle(t){this._title=t;return it;}, setChoices(c){this._choices=c;return it;},
        setPoints(p){this._points=p;return it;}, setRequired(){return it;},
        setFeedbackForCorrect(){return it;}, setFeedbackForIncorrect(){return it;},
        createChoice(txt, ok){return {txt, ok};},
        asMultipleChoiceItem(){return it;},
        getId(){return this._id;}, getType(){return this._type;}, getTitle(){return this._title;}
      };
      items.push(it); return it;
    },
  };
  formsStore[id] = form;
  return form;
}

const sandbox = {
  Logger: { log: () => {} },
  Utilities: { formatDate: () => '101500' },
  Session: { getScriptTimeZone: () => 'Asia/Bangkok' },
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => propsStore[k] || null, setProperty: (k,v) => { propsStore[k] = v; } }) },
  SpreadsheetApp: {
    getActiveSpreadsheet: () => activeSs,
    openById: () => activeSs,
    flush: () => {},
    getUi: () => ({ alert: () => {}, createMenu: () => ({ addItem(){return this;}, addToUi(){} }) }),
  },
  FormApp: {
    ItemType: { LIST: 'LIST', TEXT: 'TEXT', MULTIPLE_CHOICE: 'MCQ' },
    DestinationType: { SPREADSHEET: 'SS' },
    create: (t) => makeForm(t),
    openById: (id) => formsStore[id],
    openByUrl: (u) => Object.values(formsStore).find(f => f.getPublishedUrl() === u || f.getEditUrl() === u),
    createFeedback: () => ({ setText(){return this;}, build(){return {};} }),
  },
  ScriptApp: {
    getProjectTriggers: () => triggersStore,
    deleteTrigger: (t) => { triggersStore = triggersStore.filter(x => x !== t); },
    newTrigger: (fn) => ({ forSpreadsheet(){return this;}, onFormSubmit(){return this;}, create(){ triggersStore.push({ getHandlerFunction: () => fn }); } }),
  },
};
vm.createContext(sandbox);
vm.runInContext(gasCode, sandbox);
sandbox.createAllBOIForms();

// Simulate 1 student completing Pre (20/20) and Theory v2 (30 items: misses #4 topic1 non-core & #28 topic6 non-core => HR=20/20, Theory=28/30)
const cfg = JSON.parse(propsStore.BOI_FORMS_CFG);
const preForm = formsStore[cfg.pre.id];
const theoryForm = formsStore[cfg.postFinal.id];
const preMcq = preForm.getItems('MCQ');
const thMcq = theoryForm.getItems('MCQ');

preForm._responses.push({
  getTimestamp: () => 1000,
  getItemResponses: () => [
    { getItem: () => preForm.getItems('LIST')[0], getResponse: () => 'รุ่นที่ 4' },
    { getItem: () => preForm.getItems('LIST')[1], getResponse: () => '7' },
    { getItem: () => preForm.getItems('TEXT')[0], getResponse: () => '07-ทดสอบ' },
    { getItem: () => preForm.getItems('TEXT')[1], getResponse: () => 'SNC' },
  ],
  getGradableItemResponses: () => preMcq.map(it => ({ getItem: () => it, getScore: () => 1 })),
});

theoryForm._responses.push({
  getTimestamp: () => 2000,
  getItemResponses: () => [
    { getItem: () => theoryForm.getItems('LIST')[0], getResponse: () => 'รุ่นที่ 4' },
    { getItem: () => theoryForm.getItems('LIST')[1], getResponse: () => '7' },
    { getItem: () => theoryForm.getItems('TEXT')[0], getResponse: () => '07-ทดสอบ' },
    { getItem: () => theoryForm.getItems('TEXT')[1], getResponse: () => 'SNC' },
  ],
  getGradableItemResponses: () => thMcq.map((it, i) => ({
    getItem: () => it,
    getScore: () => (i === 3 || i === 27) ? 0 : 1,
  })),
});

sandbox.updateExistingFormsQuestions();
const auditSheet = activeSs.getSheetByName('สรุปคะแนน_Audit');
process.stdout.write(JSON.stringify({
  preCount: preMcq.length,
  theoryCount: thMcq.length,
  rows: auditSheet._rows,
}));
"""
        res = subprocess.run(["node", "-e", harness, gas_path], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        self.assertEqual(out["preCount"], 20)
        self.assertEqual(out["theoryCount"], 30)
        # Row 0 header, Row 1 student: Pre=20, HR=20, T1=4, T2=5, T3=5, T4=5, T5=5, T6=4, Total=28
        row = out["rows"][1]
        self.assertEqual(row[4], 20)   # Pre
        self.assertEqual(row[5], 20)   # Post-Test HR (20 core items all right!)
        self.assertEqual(row[6:12], [4, 5, 5, 5, 5, 4])
        self.assertEqual(row[12], 28)  # Theory total /30


class TestGradingRules(unittest.TestCase):
    def test_exam_help_decay_and_cap(self) -> None:
        reqs = [
            {"scope": "exam", "status": "resolved", "resolution": "tech_issue"},  # 0
            {"scope": "exam", "status": "resolved", "resolution": "hint"},        # -1
            {"scope": "exam", "status": "resolved", "resolution": "hint"},        # -2
            {"scope": "exam", "status": "resolved", "resolution": "hint"},        # -3
            {"scope": "exam", "status": "resolved", "resolution": "hint"},        # -1 (total -7)
            {"scope": "exam", "status": "waiting", "resolution": ""},             # ignored
        ]
        res = grading_rules.calculate_help_penalty(reqs, scope="exam", raw_earned=45.0)
        self.assertEqual(res["tech_issue_count"], 1)
        self.assertEqual(res["hint_count"], 4)
        self.assertEqual(res["applied_penalty"], 7.0)

        # Extreme help spam should NEVER exceed max cap (15) or drop >50% of earned score
        spam = [{"scope": "exam", "status": "resolved", "resolution": "code_fix"} for _ in range(10)]
        capped = grading_rules.calculate_help_penalty(spam, scope="exam", raw_earned=50.0)
        self.assertEqual(capped["applied_penalty"], 15.0)

        floor_protected = grading_rules.calculate_help_penalty(spam, scope="exam", raw_earned=20.0)
        self.assertEqual(floor_protected["applied_penalty"], 10.0)  # Never drops earned 20 below 10!

        zero_earned = grading_rules.calculate_help_penalty(spam, scope="exam", raw_earned=0.0)
        self.assertEqual(zero_earned["applied_penalty"], 0.0)

    def test_workshop_help_and_boundaries(self) -> None:
        ws_reqs = [
            {"scope": "workshop", "status": "resolved", "resolution": "hint"},     # free #1
            {"scope": "workshop", "status": "resolved", "resolution": "hint"},     # free #2
            {"scope": "workshop", "status": "resolved", "resolution": "hint"},     # -0.5
            {"scope": "workshop", "status": "resolved", "resolution": "code_fix"}, # -1.5 => -2.0
        ]
        ws_res = grading_rules.calculate_help_penalty(ws_reqs, scope="workshop", raw_earned=20.0)
        self.assertEqual(ws_res["applied_penalty"], 2.0)

        self.assertEqual(grading_rules.compute_final_grade(25, 19, 36)["grade"], "A")
        self.assertEqual(grading_rules.compute_final_grade(25, 19, 35.9)["grade"], "B")
        self.assertFalse(grading_rules.compute_final_grade(20, 15, 34)["passed"])
        self.assertEqual(grading_rules.clamp_score(float("nan")), 0.0)
        self.assertEqual(grading_rules.clamp_score(-5.0), 0.0)
        self.assertEqual(grading_rules.clamp_score(120.0), 100.0)


class TestAutoGrader(unittest.TestCase):
    def test_practical_and_workshop_graders(self) -> None:
        sol_res = auto_grader.grade_practical_submission([
            os.path.join(PRACTICAL_DIR, "solution", "index.html"),
            os.path.join(PRACTICAL_DIR, "solution", "script.js"),
        ])
        self.assertTrue(sol_res["ok"])
        self.assertEqual(sol_res["final_50"], 50.0)

        starter_res = auto_grader.grade_practical_submission([
            os.path.join(PRACTICAL_DIR, "exam_starter.html"),
        ])
        self.assertEqual(starter_res["final_50"], 0.0)

        bulaporn_res = auto_grader.grade_practical_submission([
            os.path.join(PRACTICAL_DIR, "submissions", "03_Bulaporn", "114857_03_Bulaporn.html"),
        ])
        self.assertEqual(bulaporn_res["duplicates"], ["showMeterValues"])
        self.assertEqual(bulaporn_res["final_50"], 48.0)

        for ws in ("w1", "w2", "w3", "w4"):
            ws_dir = os.path.join(COURSE_DIR, "03_Workshops_ใบงานและเฉลย", ws, "solution")
            files = [os.path.join(ws_dir, fn) for fn in os.listdir(ws_dir) if os.path.isfile(os.path.join(ws_dir, fn))]
            w_res = auto_grader.grade_workshop_submission(ws, files)
            self.assertEqual(w_res["raw_5"], 5.0, f"{ws} failed: {w_res}")


class TestPortalAndServerIntegration(unittest.TestCase):
    def test_ui_templates_syntax(self) -> None:
        for html_txt in (portal_ui.MONITOR_HTML, portal_ui.DOWNLOAD_HTML, portal_ui.PIN_LOGIN_HTML):
            m = re.search(r"<script>([\s\S]*)</script>", html_txt)
            self.assertIsNotNone(m)
            chk = subprocess.run(["node", "--check", "-"], input=m.group(1), text=True, capture_output=True)
            self.assertEqual(chk.returncode, 0, chk.stderr)

        with open(os.path.join(PRACTICAL_DIR, "exam_starter.html"), encoding="utf-8") as f:
            starter_html = f.read()
        m_st = re.search(r"<script>([\s\S]*)</script>", starter_html)
        chk_st = subprocess.run(["node", "--check", "-"], input=m_st.group(1), text=True, capture_output=True)
        self.assertEqual(chk_st.returncode, 0, chk_st.stderr)

        with open(os.path.join(COURSE_DIR, "00_ศูนย์รวมลิงก์และQR_เปิดสอน.html"), encoding="utf-8") as f:
            links_html = f.read()
        m_lk = re.search(r"<script>([\s\S]*)</script>", links_html)
        chk_lk = subprocess.run(["node", "--check", "-"], input=m_lk.group(1), text=True, capture_output=True)
        self.assertEqual(chk_lk.returncode, 0, chk_lk.stderr)

    def test_theory_csv_import_parsing(self) -> None:
        from audit_exporter import parse_theory_csv
        csv_txt = "\ufeffรุ่น,เลขที่,ชื่อ-นามสกุล,สังกัด,Pre-Test (20),Post-Test HR (20),หัวข้อ 1 (5),หัวข้อ 2 (5),หัวข้อ 3 (5),หัวข้อ 4 (5),หัวข้อ 5 (5),หัวข้อ 6 (5),รวมทฤษฎี (30)\n"
        csv_txt += '"รุ่นที่ 4","3","นางสาว ทดสอบ ระบบ","IPC",12,18,4,5,4,5,4,4,26\n'
        parsed = parse_theory_csv(csv_txt)
        rec = parsed.get("seat:03")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["pre_20"], 12.0)
        self.assertEqual(rec["post_hr_20"], 18.0)
        self.assertEqual(rec["topics"], [4.0, 5.0, 4.0, 5.0, 4.0, 4.0])

    def test_live_server_workflows_and_security(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            orig_sub = exam_server.SUBMISSIONS_DIR
            orig_ws_sub = exam_server.WORKSHOP_SUBMISSIONS_DIR
            orig_prog = exam_server.PROGRESS_FILE
            orig_pin = exam_server.INSTRUCTOR_PIN
            try:
                exam_server.SUBMISSIONS_DIR = os.path.join(tmp, "submissions")
                exam_server.WORKSHOP_SUBMISSIONS_DIR = os.path.join(exam_server.SUBMISSIONS_DIR, "_workshops")
                exam_server.PROGRESS_FILE = os.path.join(tmp, "progress.json")
                exam_server.INSTRUCTOR_PIN = "4321"
                exam_server.state["students"] = {}
                exam_server.state["notifications"] = []
                exam_server.state["help_requests"] = []
                exam_server.state["theory_submissions"] = []
                exam_server.state["scenario"] = "over_volt"
                exam_server.state["mode"] = "manual"

                srv = exam_server.create_server("0.0.0.0", 0)
                port = srv.server_address[1]
                th = threading.Thread(target=srv.serve_forever, daemon=True)
                th.start()

                try:
                    lan = exam_server.SERVER_IP
                    base_local = f"http://127.0.0.1:{port}"
                    base_lan = f"http://{lan}:{port}"

                    # 1) /api/meter MUST NOT contain 'scenario'
                    with urllib.request.urlopen(base_local + "/api/meter") as r:
                        meter = json.loads(r.read().decode("utf-8"))
                    self.assertNotIn("scenario", meter)
                    self.assertGreater(meter["electric"]["voltage"], 240.0)

                    # 2) Workshop W1..W4 starter downloads work
                    with urllib.request.urlopen(base_local + "/download/workshop/w1.zip") as r:
                        with zipfile.ZipFile(io.BytesIO(r.read())) as zf:
                            self.assertTrue(any("index.html" in n for n in zf.namelist()))

                    # 3) LAN IP (when different from 127.0.0.1) blocks unauthenticated instructor routes
                    if lan != "127.0.0.1":
                        for restricted in ("/api/status", "/solution/index.html"):
                            with self.assertRaises(urllib.error.HTTPError) as ctx:
                                urllib.request.urlopen(base_lan + restricted)
                            self.assertEqual(ctx.exception.code, 401)

                        # Authenticate via PIN cookie
                        auth_req = urllib.request.Request(
                            base_lan + "/api/auth",
                            data=json.dumps({"pin": "4321"}).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(auth_req) as r:
                            cookie = r.headers.get("Set-Cookie", "").split(";")[0]
                            self.assertIn("boi_inst=", cookie)

                        ok_req = urllib.request.Request(base_lan + "/api/status", headers={"Cookie": cookie})
                        with urllib.request.urlopen(ok_req) as r:
                            self.assertEqual(r.status, 200)

                    # 4) Student submits Workshop W1, Final Exam solution, Theory LAN backup, and Help Request
                    import base64
                    with open(os.path.join(COURSE_DIR, "03_Workshops_ใบงานและเฉลย/w1/solution/index.html"), "rb") as f:
                        w1_html = f.read()
                    with open(os.path.join(COURSE_DIR, "03_Workshops_ใบงานและเฉลย/w1/solution/style.css"), "rb") as f:
                        w1_css = f.read()
                    ws_req = urllib.request.Request(
                        base_local + "/api/workshop/submit",
                        data=json.dumps({
                            "sender": "01-Tester",
                            "ws_id": "w1",
                            "files": [
                                {"filename": "index.html", "contentBase64": base64.b64encode(w1_html).decode()},
                                {"filename": "style.css", "contentBase64": base64.b64encode(w1_css).decode()},
                            ],
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(ws_req) as r:
                        self.assertEqual(r.status, 200)

                    with open(os.path.join(PRACTICAL_DIR, "solution", "index.html"), "rb") as f:
                        sol_html = f.read()
                    with open(os.path.join(PRACTICAL_DIR, "solution", "script.js"), "rb") as f:
                        sol_js = f.read()
                    ex_req = urllib.request.Request(
                        base_local + "/api/submit",
                        data=json.dumps({
                            "sender": "01-Tester",
                            "files": [
                                {"filename": "index.html", "contentBase64": base64.b64encode(sol_html).decode()},
                                {"filename": "script.js", "contentBase64": base64.b64encode(sol_js).decode()},
                            ],
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(ex_req) as r:
                        self.assertEqual(r.status, 200)

                    # Help request + duplicate protection while waiting
                    help_req = urllib.request.Request(
                        base_local + "/api/help",
                        data=json.dumps({"sender": "01-Tester", "scope": "exam", "topic": "ติด TODO 4", "note": "border"}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(help_req) as r:
                        h1 = json.loads(r.read().decode("utf-8"))
                        self.assertEqual(h1["queue_position"], 1)
                    with urllib.request.urlopen(help_req) as r:
                        h2 = json.loads(r.read().decode("utf-8"))
                        self.assertTrue(h2.get("already_waiting"))

                    # Resolve help as hint (-1 in exam)
                    res_req = urllib.request.Request(
                        base_local + "/api/help/resolve",
                        data=json.dumps({"id": h1["id"], "resolution": "hint"}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(res_req) as r:
                        self.assertEqual(r.status, 200)

                    # Theory LAN submit
                    th_req = urllib.request.Request(
                        base_local + "/api/theory/submit",
                        data=json.dumps({
                            "cohort": "รุ่นที่ 4",
                            "seatNo": "1",
                            "studentName": "01-Tester",
                            "department": "SNC",
                            "postHr20": 18,
                            "topicScores": [4, 5, 4, 4, 5, 4],
                            "theory30": 26,
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(th_req) as r:
                        self.assertEqual(r.status, 200)

                    # Export Audit v2 XLSX (triggers auto-grade on practical + workshops + merges theory!)
                    exp_req = urllib.request.Request(
                        base_local + "/api/audit/export",
                        data=json.dumps({"cohort": "รุ่นที่ 4", "theory_csv": ""}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(exp_req) as r:
                        wb = openpyxl.load_workbook(io.BytesIO(r.read()), data_only=False)
                        ws = wb["สรุปคะแนนการสอบ_v2"]
                        # Verify Theory topic 1..6 populated, W1=5, Practical TODO1..5=10 each, Help deduct=1
                        self.assertEqual([ws.cell(9, c).value for c in range(9, 15)], [4, 5, 4, 4, 5, 4])
                        self.assertEqual(ws.cell(9, 16).value, 5.0)
                        self.assertEqual([ws.cell(9, c).value for c in range(22, 27)], [10.0, 10.0, 10.0, 10.0, 10.0])
                        self.assertEqual(ws.cell(9, 27).value, 1.0)
                        ws_log = wb["หลักฐาน_Help_และ_AutoGrade"]
                        self.assertEqual(ws_log.cell(2, 3).value, "01-Tester")

                    # Path traversal guard
                    with self.assertRaises(urllib.error.HTTPError) as ctx2:
                        urllib.request.urlopen(base_local + "/api/submission?rel=../../README.md")
                    self.assertEqual(ctx2.exception.code, 404)
                finally:
                    srv.shutdown()
                    srv.server_close()
            finally:
                exam_server.SUBMISSIONS_DIR = orig_sub
                exam_server.WORKSHOP_SUBMISSIONS_DIR = orig_ws_sub
                exam_server.PROGRESS_FILE = orig_prog
                exam_server.INSTRUCTOR_PIN = orig_pin


if __name__ == "__main__":
    unittest.main(verbosity=2)
