"""Audit v2 Excel Exporter (30 Theory + 20 Workshop + 50 Practical = 100 + Help Evidence Sheet).

Generates Leelawadee UI-styled Excel workbooks compatible with BOI/Government Audits
without Thai font rendering issues (zero tofu boxes on Windows Export-to-PDF).
"""

import csv
import html as html_lib
import io
import re
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from grading_rules import clamp_score, compute_final_grade

FONT_NAME = "Leelawadee UI"
THAI_PREFIXES = ("นางสาว", "นาง", "นาย", "น.ส.")


def split_thai_name(full_name: str) -> Tuple[str, str, str]:
    """Split 'นางสาวสมหญิง ใจดี' or '01-สมชาย ดีใจ' into (prefix, first_name, last_name)."""
    raw = re.sub(r"^\d+[-_\s]+", "", str(full_name or "").strip()).strip()
    prefix = ""
    for p in THAI_PREFIXES:
        if raw.startswith(p):
            prefix = p
            raw = raw[len(p):].strip()
            break
    parts = raw.split()
    if len(parts) >= 2:
        return prefix, parts[0], " ".join(parts[1:])
    return prefix, raw, ""


def _opt_float(val: Any) -> Optional[float]:
    if val is None or str(val).strip() == "":
        return None
    try:
        return round(float(val), 1)
    except (TypeError, ValueError):
        return None


def _opt_list(vals: Any, length: int) -> List[Optional[float]]:
    src = list(vals) if isinstance(vals, (list, tuple)) else []
    out: List[Optional[float]] = []
    for i in range(length):
        out.append(_opt_float(src[i]) if i < len(src) else None)
    return out


def normalize_audit_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize arbitrary/partial student record into full editable Audit v2 row with computed totals."""
    prefix = str(rec.get("prefix") or "").strip()
    first_name = str(rec.get("first_name") or "").strip()
    last_name = str(rec.get("last_name") or "").strip()
    full_name = str(rec.get("full_name") or rec.get("name") or "").strip()
    if not first_name and full_name:
        p, fn, ln = split_thai_name(full_name)
        prefix = prefix or p
        first_name = fn
        last_name = last_name or ln

    topics = _opt_list(rec.get("topics"), 6)
    workshops = _opt_list(rec.get("workshops"), 4)
    ws_pen = _opt_float(rec.get("ws_help_penalty")) or 0.0
    todos = _opt_list(rec.get("practical_todos"), 5)
    prac_pen = _opt_float(rec.get("practical_deduct")) or 0.0

    has_t = any(x is not None for x in topics)
    has_w = any(x is not None for x in workshops)
    has_p = any(x is not None for x in todos)

    t_sum = clamp_score(sum(x or 0.0 for x in topics), 0.0, 30.0) if has_t else None
    w_sum = clamp_score(sum(x or 0.0 for x in workshops) - ws_pen, 0.0, 20.0) if has_w else None
    p_sum = clamp_score(sum(x or 0.0 for x in todos) - prac_pen, 0.0, 50.0) if has_p else None

    if has_t or has_w or has_p:
        graded = compute_final_grade(t_sum or 0.0, w_sum or 0.0, p_sum or 0.0)
        total_100: Optional[float] = graded["total_100"]
        grade = graded["grade"]
        status_th = graded["status_th"]
    else:
        total_100 = None
        grade = ""
        status_th = ""

    return {
        "sender": str(rec.get("sender") or "").strip(),
        "emp_id": str(rec.get("emp_id") or "").strip(),
        "prefix": prefix,
        "first_name": first_name,
        "last_name": last_name,
        "dept": str(rec.get("dept") or "").strip(),
        "pre_20": _opt_float(rec.get("pre_20")),
        "post_hr_20": _opt_float(rec.get("post_hr_20")),
        "topics": topics,
        "theory_30": t_sum,
        "workshops": workshops,
        "ws_help_penalty": ws_pen,
        "workshop_20": w_sum,
        "practical_todos": todos,
        "practical_deduct": prac_pen,
        "practical_50": p_sum,
        "total_100": total_100,
        "grade": grade,
        "status_th": status_th,
        "audit_note": str(rec.get("audit_note") or "").strip(),
    }


def _font(size: int = 10, bold: bool = False, color: str = "000000") -> Font:
    return Font(name=FONT_NAME, size=size, bold=bold, color=color)


def _fill(hex_color: str) -> PatternFill:
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


def _border(left: str = "thin", right: str = "thin", top: str = "thin", bottom: str = "thin") -> Border:
    return Border(
        left=Side(style=left, color="000000"),
        right=Side(style=right, color="000000"),
        top=Side(style=top, color="000000"),
        bottom=Side(style=bottom, color="000000"),
    )


def parse_theory_csv(csv_text: str) -> Dict[str, Dict[str, Any]]:
    """Parse Google Sheet 'สรุปคะแนน_Audit' or offline HTML CSV export keyed by normalized student name/seat."""
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    records: Dict[str, Dict[str, Any]] = {}
    for row in reader:
        name = str(row.get("ชื่อ-นามสกุล") or row.get("studentName") or "").strip()
        seat = str(row.get("เลขที่") or row.get("seatNo") or "").strip()
        if not name and not seat:
            continue

        def _num(col_candidates: List[str]) -> Optional[float]:
            for key in col_candidates:
                if key in row and str(row[key]).strip() != "":
                    try:
                        return float(row[key])
                    except ValueError:
                        return None
            return None

        parsed = {
            "cohort": str(row.get("รุ่น") or "").strip(),
            "seat": seat,
            "name": name,
            "dept": str(row.get("สังกัด") or "").strip(),
            "pre_20": _num(["Pre-Test (20)", "pre_20"]),
            "post_hr_20": _num(["Post-Test HR (20)", "Post-Test_HR(20)", "Post-Test (20)", "post_hr_20"]),
            "topics": [
                _num([f"หัวข้อ {i} (5)", f"หัวข้อ{i}(5)", f"หัวข้อ {i}"])
                for i in range(1, 7)
            ],
        }
        if name:
            records[name] = parsed
        if seat:
            seat_pad = seat.zfill(2) if seat.isdigit() else seat
            records[f"seat:{seat_pad}"] = parsed
    return records


def export_audit_workbook(
    output_path: str,
    cohort_title: str = "หลักสูตร การออกแบบ พัฒนา และบูรณาการแอปพลิเคชันระดับองค์กร (Enterprise Application) รุ่นที่ ___",
    date_subtitle: str = "วันที่ .............................. (โครงสร้างเกณฑ์ v2: ทฤษฎี 30 + Workshop 20 + ปฏิบัติ 50 = 100)",
    rows_data: Optional[List[Dict[str, Any]]] = None,
    help_requests: Optional[List[Dict[str, Any]]] = None,
    blank_rows: int = 15,
) -> str:
    """Write a complete Audit v2 workbook with formulas, formatting, and Help Log tab."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "สรุปคะแนนการสอบ_v2"

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    total_cols = 31  # A..AE

    # Title Banner Rows 1-3
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    ws.cell(1, 1, "สรุปคะแนนการสอบและการปฏิบัติงานระหว่างเรียน (v2 · Audit & HR)").font = _font(14, True)
    ws.cell(1, 1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(1, 1).fill = _fill("FCE4D6")

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols)
    ws.cell(2, 1, cohort_title).font = _font(11, True)
    ws.cell(2, 1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(2, 1).fill = _fill("F8CBAD")

    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=total_cols)
    ws.cell(3, 1, date_subtitle).font = _font(10, False)
    ws.cell(3, 1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(3, 1).fill = _fill("FCE4D6")
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 22
    ws.row_dimensions[3].height = 20

    # Header Rows 5-8
    single_headers = [
        (1, "ลำดับ", "8EA9DB", 6),
        (2, "รหัส\nพนักงาน", "8EA9DB", 11),
        (3, "คำนำ\nหน้า", "8EA9DB", 7),
        (4, "ชื่อ", "8EA9DB", 15),
        (5, "นามสกุล", "8EA9DB", 16),
        (6, "สังกัด /\nบริษัท", "8EA9DB", 12),
        (7, "Pre-Test\nHR (20)\n(ไม่รวม 100)", "F4B084", 10),
        (8, "Post-Test\nHR (20)\n(ไม่รวมซ้ำ)", "ED7D31", 10),
        (15, "รวมทฤษฎี\n(30)", "DDEBF7", 9),
        (21, "รวม\nWorkshop\n(20)", "FFF2CC", 9),
        (28, "รวมปฏิบัติ\nFinal (50)", "F8CBAD", 10),
        (29, "คะแนนรวม\n(100)", "C6E0B4", 10),
        (30, "เกรด", "FFFFFF", 7),
        (31, "ผลประเมิน\n(>=60)", "D9D9D9", 10),
    ]
    for col, text, color, width in single_headers:
        ws.merge_cells(start_row=5, start_column=col, end_row=8, end_column=col)
        cell = ws.cell(5, col, text)
        cell.font = _font(9, True)
        cell.fill = _fill(color)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = width
        for r in range(5, 9):
            ws.cell(r, col).border = _border("medium", "medium", "medium" if r == 5 else "thin", "medium" if r == 8 else "thin")
            ws.cell(r, col).fill = _fill(color)

    # Group Headers in Row 5-6
    groups = [
        (9, 14, "ทฤษฎีรวม 6 หัวข้อ (Post-Test + Final แนววิเคราะห์ & Debug · หัวข้อละ 5 ข้อ = 30 คะแนน)", "6 หัวข้ออบรม Enterprise App (ไม่กระจุกคะแนนข้อละ 5)", "9BC2E6", "BDD7EE"),
        (16, 20, "Workshop ระหว่างเรียน (20 คะแนน)", "ส่งงานจริง W1–W4 ผ่านระบบ + หักตาม Help Tiered Cap", "FFE699", "FFF2CC"),
        (22, 27, "สอบปฏิบัติ Final: Electrical Meter Alert (50 คะแนน)", "5 TODO × 10 คะแนน + หัก Help Tiered Cap (Max -10)", "A9D08E", "C6E0B4"),
    ]
    for c1, c2, top_txt, sub_txt, top_col, sub_col in groups:
        ws.merge_cells(start_row=5, start_column=c1, end_row=5, end_column=c2)
        c_top = ws.cell(5, c1, top_txt)
        c_top.font = _font(10, True)
        c_top.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.merge_cells(start_row=6, start_column=c1, end_row=6, end_column=c2)
        c_sub = ws.cell(6, c1, sub_txt)
        c_sub.font = _font(9, False)
        c_sub.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for c in range(c1, c2 + 1):
            ws.cell(5, c).fill = _fill(top_col)
            ws.cell(6, c).fill = _fill(sub_col)
            ws.cell(5, c).border = _border("thin", "thin", "medium", "thin")
            ws.cell(6, c).border = _border("thin", "thin", "thin", "thin")

    sub_cols = [
        # I..N (9..14) Theory 6 topics
        (9, "1. OT/IT &\nApp Arch", "(5)", "BDD7EE", 10),
        (10, "2. HTML5,\nCSS & UI", "(5)", "BDD7EE", 10),
        (11, "3. JS Logic\n& DOM", "(5)", "BDD7EE", 10),
        (12, "4. JSON &\nREST API", "(5)", "BDD7EE", 10),
        (13, "5. Webhook\n& Polling", "(5)", "BDD7EE", 10),
        (14, "6. Security\n& Testing", "(5)", "BDD7EE", 10),
        # P..T (16..20) Workshops
        (16, "W1\nHTML/CSS", "(5)", "FFF2CC", 8),
        (17, "W2\nDOM/Event", "(5)", "FFF2CC", 8),
        (18, "W3\nAPI Fetch", "(5)", "FFF2CC", 8),
        (19, "W4\nWebhook", "(5)", "FFF2CC", 8),
        (20, "หัก Help\nWorkshop", "(-Max 5)", "FCE4D6", 9),
        # V..AA (22..27) Practical
        (22, "TODO 1\nSetup URL", "(10)", "C6E0B4", 8),
        (23, "TODO 2\nDOM Meter", "(10)", "C6E0B4", 8),
        (24, "TODO 3\nCalc Power", "(10)", "C6E0B4", 8),
        (25, "TODO 4\nConditions", "(10)", "C6E0B4", 8),
        (26, "TODO 5\nPOST/Dedup", "(10)", "C6E0B4", 9),
        (27, "หัก Help/Dup\nสอบปฏิบัติ", "(-Max 10)", "FCE4D6", 10),
    ]
    for col, title, wt, bg, width in sub_cols:
        c7 = ws.cell(7, col, title)
        c7.font = _font(9, True)
        c7.fill = _fill(bg)
        c7.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c7.border = _border("thin", "thin", "thin", "thin")

        c8 = ws.cell(8, col, wt)
        c8.font = _font(9, True, "C00000")
        c8.fill = _fill("FCE4D6")
        c8.alignment = Alignment(horizontal="center", vertical="center")
        c8.border = _border("thin", "thin", "thin", "medium")
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.row_dimensions[5].height = 24
    ws.row_dimensions[6].height = 20
    ws.row_dimensions[7].height = 36
    ws.row_dimensions[8].height = 18

    records = rows_data or []
    num_rows = max(len(records), blank_rows)
    start_row = 9

    for idx in range(num_rows):
        r = start_row + idx
        ws.row_dimensions[r].height = 20
        rec = records[idx] if idx < len(records) else {}
        norm = normalize_audit_row(rec)

        ws.cell(r, 1, idx + 1)
        ws.cell(r, 2, norm["emp_id"])
        ws.cell(r, 3, norm["prefix"])
        ws.cell(r, 4, norm["first_name"])
        ws.cell(r, 5, norm["last_name"])
        ws.cell(r, 6, norm["dept"])
        if norm["pre_20"] is not None:
            ws.cell(r, 7, norm["pre_20"])
        if norm["post_hr_20"] is not None:
            ws.cell(r, 8, norm["post_hr_20"])

        for t_i, val in enumerate(norm["topics"]):
            if val is not None:
                ws.cell(r, 9 + t_i, val)

        ws.cell(r, 15, f'=IF(COUNT(I{r}:N{r})=0,"",SUM(I{r}:N{r}))')

        has_ws = any(v is not None for v in norm["workshops"])
        for w_i, val in enumerate(norm["workshops"]):
            if val is not None:
                ws.cell(r, 16 + w_i, val)
        if has_ws and norm["ws_help_penalty"]:
            ws.cell(r, 20, norm["ws_help_penalty"])
        ws.cell(r, 21, f'=IF(COUNT(P{r}:S{r})=0,"",MAX(0,MIN(20,SUM(P{r}:S{r})-SUM(T{r}))))')

        has_prac = any(v is not None for v in norm["practical_todos"])
        for p_i, val in enumerate(norm["practical_todos"]):
            if val is not None:
                ws.cell(r, 22 + p_i, val)
        if has_prac and norm["practical_deduct"]:
            ws.cell(r, 27, norm["practical_deduct"])
        ws.cell(r, 28, f'=IF(COUNT(V{r}:Z{r})=0,"",MAX(0,MIN(50,SUM(V{r}:Z{r})-SUM(AA{r}))))')

        ws.cell(r, 29, f'=IF(COUNT(O{r},U{r},AB{r})=0,"",SUM(O{r},U{r},AB{r}))')
        ws.cell(r, 30, f'=IF(AC{r}="","",IF(AC{r}>=80,"A",IF(AC{r}>=70,"B",IF(AC{r}>=60,"C",IF(AC{r}>=50,"D","F")))))')
        ws.cell(r, 31, f'=IF(AC{r}="","",IF(AC{r}>=60,"ผ่าน","ไม่ผ่าน"))')

        # Style row cells cleanly
        row_fills = {
            15: "DDEBF7",
            20: "FCE4D6",
            21: "FFF2CC",
            27: "FCE4D6",
            28: "FCE4D6",
            29: "C6E0B4",
            31: "D9D9D9",
        }
        for c in range(1, total_cols + 1):
            cell = ws.cell(r, c)
            cell.font = _font(10, c in (15, 21, 28, 29, 30, 31))
            cell.border = _border()
            if c in (4, 5):
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            if c in row_fills:
                cell.fill = _fill(row_fills[c])
            if c in (15, 21, 28, 29) and c <= total_cols:
                cell.number_format = "0.0"

    # Footer Summary Row
    avg_r = start_row + num_rows
    ws.row_dimensions[avg_r].height = 22
    ws.merge_cells(start_row=avg_r, start_column=1, end_row=avg_r, end_column=6)
    ws.cell(avg_r, 1, "ค่าเฉลี่ยทั้งรุ่น (Average)").font = _font(10, True)
    ws.cell(avg_r, 1).alignment = Alignment(horizontal="right", vertical="center")
    for c in range(7, 30):
        col_l = get_column_letter(c)
        c_cell = ws.cell(avg_r, c, f'=IF(COUNT({col_l}{start_row}:{col_l}{avg_r-1})=0,"",ROUND(AVERAGE({col_l}{start_row}:{col_l}{avg_r-1}),1))')
        c_cell.font = _font(10, True)
        c_cell.alignment = Alignment(horizontal="center", vertical="center")
    for c in range(1, total_cols + 1):
        ws.cell(avg_r, c).fill = _fill("F2F4F8")
        ws.cell(avg_r, c).border = _border("thin", "thin", "medium", "medium")

    # Sheet 2: Help & AutoGrade Audit Evidence
    ws_log = wb.create_sheet("หลักฐาน_Help_และ_AutoGrade")
    ws_log.page_setup.orientation = ws_log.ORIENTATION_LANDSCAPE
    ws_log.sheet_properties.pageSetUpPr.fitToPage = True
    ws_log.page_setup.fitToWidth = 1

    log_headers = ["เวลาที่ขอ", "ช่วงงาน (Workshop/Exam)", "ผู้เรียน", "หัวข้อ/อาการที่แจ้ง", "สถานะ", "ระดับการช่วยของครู", "หมายเหตุผู้สอน", "Auto-Grade / Live Summary"]
    for c_idx, h_txt in enumerate(log_headers, 1):
        hc = ws_log.cell(1, c_idx, h_txt)
        hc.font = _font(10, True, "FFFFFF")
        hc.fill = _fill("1E293B")
        hc.alignment = Alignment(horizontal="center", vertical="center")
        hc.border = _border()
        ws_log.column_dimensions[get_column_letter(c_idx)].width = 18 if c_idx in (1, 2, 5, 6) else 28

    r_idx = 2
    for req in (help_requests or []):
        vals = [
            req.get("time", ""),
            req.get("scope", ""),
            req.get("sender", ""),
            req.get("topic", "") + (" — " + req.get("note", "") if req.get("note") else ""),
            req.get("status", ""),
            req.get("resolution", ""),
            req.get("instructor_note", ""),
            "",
        ]
        for c_i, val in enumerate(vals, 1):
            lc = ws_log.cell(r_idx, c_i, val)
            lc.font = _font(10)
            lc.border = _border()
            lc.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        r_idx += 1

    for rec in records:
        if rec.get("audit_note"):
            vals = ["Auto-Grader", "Summary", rec.get("full_name", rec.get("first_name", "")), "", "evaluated", "", "", rec["audit_note"]]
            for c_i, val in enumerate(vals, 1):
                lc = ws_log.cell(r_idx, c_i, val)
                lc.font = _font(10)
                lc.border = _border()
                lc.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            r_idx += 1

    if r_idx == 2:
        ws_log.cell(2, 1, "ยังไม่มีบันทึกการขอความช่วยเหลือ (เมื่อใช้ระบบผ่าน BOI Classroom Portal ข้อมูลจะมาปรากฏที่นี่อัตโนมัติ)").font = _font(10, False, "64748B")

    wb.save(output_path)
    return output_path


def _fmt_num(val: Optional[float], one_dec: bool = False) -> str:
    if val is None:
        return ""
    if one_dec or (val % 1 != 0):
        return f"{val:.1f}"
    return str(int(val))


def render_audit_print_html(
    cohort_title: str,
    date_subtitle: str,
    rows_data: Optional[List[Dict[str, Any]]] = None,
    help_requests: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Render an A4-landscape Print-to-PDF HTML sheet styled to match official BOI Audit forms."""
    e = html_lib.escape
    norm_rows = [normalize_audit_row(r) for r in (rows_data or [])]
    body_rows = []
    for idx, r in enumerate(norm_rows, 1):
        t_cells = "".join(f"<td>{e(_fmt_num(v))}</td>" for v in r["topics"])
        w_cells = "".join(f"<td>{e(_fmt_num(v))}</td>" for v in r["workshops"])
        p_cells = "".join(f"<td>{e(_fmt_num(v))}</td>" for v in r["practical_todos"])
        w_pen = e(_fmt_num(r["ws_help_penalty"])) if any(x is not None for x in r["workshops"]) else ""
        p_pen = e(_fmt_num(r["practical_deduct"])) if any(x is not None for x in r["practical_todos"]) else ""
        status_cls = "pass" if r["status_th"] == "ผ่าน" else ("fail" if r["status_th"] == "ไม่ผ่าน" else "")
        body_rows.append(
            f"<tr>"
            f"<td>{idx}</td><td>{e(r['emp_id'])}</td>"
            f"<td class='name-p'>{e(r['prefix'])}</td><td class='name-f'>{e(r['first_name'])}</td><td class='name-l'>{e(r['last_name'])}</td>"
            f"<td>{e(r['dept'])}</td>"
            f"<td class='orange'>{e(_fmt_num(r['pre_20']))}</td>"
            f"<td class='orange'>{e(_fmt_num(r['post_hr_20']))}</td>"
            f"{t_cells}<td class='fsum'><b>{e(_fmt_num(r['theory_30'], True))}</b></td>"
            f"{w_cells}<td class='pen'>{w_pen}</td><td class='wsum'><b>{e(_fmt_num(r['workshop_20'], True))}</b></td>"
            f"{p_cells}<td class='pen'>{p_pen}</td><td class='psum'><b>{e(_fmt_num(r['practical_50'], True))}</b></td>"
            f"<td class='tot'><b>{e(_fmt_num(r['total_100'], True))}</b></td>"
            f"<td><b>{e(r['grade'])}</b></td>"
            f"<td class='{status_cls}'><b>{e(r['status_th'])}</b></td>"
            f"</tr>"
        )

    def _avg(vals: List[Optional[float]]) -> str:
        nums = [v for v in vals if v is not None]
        return f"{sum(nums) / len(nums):.1f}" if nums else ""

    avg_row = (
        f"<tr class='avg-row'><td colspan='6' style='text-align:right;font-weight:700;'>ค่าเฉลี่ยทั้งรุ่น</td>"
        f"<td>{_avg([r['pre_20'] for r in norm_rows])}</td>"
        f"<td>{_avg([r['post_hr_20'] for r in norm_rows])}</td>"
        f"<td colspan='6'></td><td>{_avg([r['theory_30'] for r in norm_rows])}</td>"
        f"<td colspan='5'></td><td>{_avg([r['workshop_20'] for r in norm_rows])}</td>"
        f"<td colspan='6'></td><td>{_avg([r['practical_50'] for r in norm_rows])}</td>"
        f"<td>{_avg([r['total_100'] for r in norm_rows])}</td><td colspan='2'></td></tr>"
    )

    ev_rows = []
    for req in (help_requests or []):
        msg = f"{req.get('topic', '')}{' — ' + req.get('note', '') if req.get('note') else ''}"
        ev_rows.append(
            f"<tr><td>{e(str(req.get('time', '')))}</td><td>{e(str(req.get('scope', '')))}</td>"
            f"<td>{e(str(req.get('sender', '')))}</td><td>{e(msg)}</td>"
            f"<td>{e(str(req.get('status', '')))}</td><td>{e(str(req.get('resolution', '')))}</td></tr>"
        )
    for r in norm_rows:
        if r["audit_note"]:
            full = f"{r['prefix']}{r['first_name']} {r['last_name']}".strip()
            ev_rows.append(
                f"<tr><td>Auto-Grader</td><td>Summary</td><td>{e(full or r['sender'])}</td>"
                f"<td colspan='3'>{e(r['audit_note'])}</td></tr>"
            )
    ev_section = ""
    if ev_rows:
        ev_section = (
            "<div class='page page-break'>"
            "<div class='b1'>หลักฐานการขอความช่วยเหลือผู้สอน &amp; ผลการตรวจโค้ดอัตโนมัติ (Help &amp; Auto-Grade Log)</div>"
            "<table class='ev-table'><thead><tr>"
            "<th style='width:80px;'>เวลา</th><th style='width:85px;'>ช่วงงาน</th><th style='width:160px;'>ผู้เรียน</th>"
            "<th>อาการ / รายละเอียด / ผลตรวจ Auto-Grader</th><th style='width:85px;'>สถานะ</th><th style='width:95px;'>การช่วยเหลือ</th>"
            "</tr></thead><tbody>" + "".join(ev_rows) + "</tbody></table></div>"
        )

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>พิมพ์สรุปคะแนน Audit v2</title>
<style>
  @page {{ size: A4 landscape; margin: 7mm; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
  body {{ margin: 0; padding: 16px; background: #e2e8f0; color: #000; font-family: "Leelawadee UI", "Sarabun", Tahoma, sans-serif; }}
  .toolbar {{ position: sticky; top: 0; z-index: 20; background: #0f172a; color: #fff; padding: 10px 18px; border-radius: 10px;
    margin: 0 auto 14px; max-width: 283mm; display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
  .toolbar button, .toolbar a {{ padding: 8px 16px; border-radius: 8px; border: 0; font: inherit; font-weight: 700; cursor: pointer; text-decoration: none; }}
  .toolbar .print-btn {{ background: #2563eb; color: #fff; }}
  .toolbar .back-btn {{ background: #334155; color: #fff; }}
  .page {{ background: #fff; width: 283mm; margin: 0 auto 16px; padding: 6mm; box-shadow: 0 3px 14px rgba(0,0,0,0.12); }}
  .page-break {{ page-break-before: always; }}
  .b1, .b2, .b3 {{ text-align: center; padding: 4px; font-weight: 700; }}
  .b1 {{ background: #FCE4D6; font-size: 14px; }}
  .b2 {{ background: #F8CBAD; font-size: 12.5px; }}
  .b3 {{ background: #FCE4D6; font-size: 11px; font-weight: 400; margin-bottom: 6px; }}
  table {{ width: 100%; border-collapse: collapse; border: 2px solid #000; font-size: 10px; }}
  th, td {{ border: 1px solid #000; padding: 3px 2px; text-align: center; vertical-align: middle; }}
  .blue-h {{ background: #8EA9DB; font-weight: 700; }}
  .pre-h {{ background: #F4B084; font-weight: 700; }}
  .post-h {{ background: #ED7D31; font-weight: 700; }}
  .th-top {{ background: #9BC2E6; font-weight: 700; }}
  .th-sub {{ background: #BDD7EE; font-weight: 700; font-size: 9px; }}
  .ws-top {{ background: #FFE699; font-weight: 700; }}
  .ws-sub {{ background: #FFF2CC; font-weight: 700; font-size: 9px; }}
  .pr-top {{ background: #A9D08E; font-weight: 700; }}
  .pr-sub {{ background: #C6E0B4; font-weight: 700; font-size: 9px; }}
  .wt {{ background: #FCE4D6; color: #C00000; font-weight: 700; font-size: 9px; }}
  .fsum {{ background: #DDEBF7; }}
  .wsum {{ background: #FFF2CC; }}
  .psum {{ background: #FCE4D6; }}
  .pen {{ background: #FCE4D6; color: #991B1B; }}
  .tot {{ background: #C6E0B4; }}
  .orange {{ color: #C65911; font-weight: 700; }}
  .pass {{ background: #DCFCE7; color: #166534; }}
  .fail {{ background: #FEE2E2; color: #991B1B; }}
  .name-p {{ border-right: none !important; text-align: left !important; padding-left: 3px !important; }}
  .name-f {{ border-left: none !important; border-right: none !important; text-align: left !important; }}
  .name-l {{ border-left: none !important; text-align: left !important; padding-right: 3px !important; }}
  .avg-row {{ background: #F1F5F9; font-weight: 700; }}
  .ev-table th {{ background: #1E293B; color: #fff; padding: 5px; font-size: 11px; }}
  .ev-table td {{ text-align: left; padding: 4px 6px; font-size: 10.5px; }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .page {{ box-shadow: none; width: 100%; margin: 0; padding: 0; }}
  }}
</style>
</head>
<body>
  <div class="toolbar">
    <span>🖨️ หน้าพร้อมพิมพ์ใบคะแนน Audit v2 (A4 แนวนอน · เลือก Printer: <b>Save as PDF</b>)</span>
    <div style="display:flex;gap:8px;">
      <button class="print-btn" onclick="window.print()">🖨️ พิมพ์ / Save as PDF</button>
      <a class="back-btn" href="/">← กลับกระดานผู้สอน</a>
    </div>
  </div>
  <div class="page">
    <div class="b1">สรุปคะแนนการสอบและการปฏิบัติงานระหว่างเรียน (v2 · Audit &amp; HR)</div>
    <div class="b2">{e(cohort_title)}</div>
    <div class="b3">{e(date_subtitle)}</div>
    <table>
      <thead>
        <tr>
          <th rowspan="3" class="blue-h" style="width:26px;">ที่</th>
          <th rowspan="3" class="blue-h" style="width:52px;">รหัส</th>
          <th rowspan="3" colspan="3" class="blue-h">ชื่อ - นามสกุล</th>
          <th rowspan="3" class="blue-h" style="width:44px;">สังกัด</th>
          <th rowspan="3" class="pre-h" style="width:34px;">Pre<br>(20)</th>
          <th rowspan="3" class="post-h" style="width:36px;">Post<br>HR(20)</th>
          <th colspan="6" class="th-top">ทฤษฎี 6 หัวข้อ (30)</th>
          <th rowspan="3" class="fsum" style="width:36px;">รวม<br>ทฤษฎี<br>(30)</th>
          <th colspan="5" class="ws-top">Workshop (20)</th>
          <th rowspan="3" class="wsum" style="width:36px;">รวม<br>WS<br>(20)</th>
          <th colspan="6" class="pr-top">สอบปฏิบัติ Final (50)</th>
          <th rowspan="3" class="psum" style="width:36px;">รวม<br>ปฏิบัติ<br>(50)</th>
          <th rowspan="3" class="tot" style="width:38px;">รวม<br>(100)</th>
          <th rowspan="3" style="width:26px;">เกรด</th>
          <th rowspan="3" style="background:#D9D9D9;width:44px;">ผล<br>(&gt;=60)</th>
        </tr>
        <tr>
          <th class="th-sub">H1<br>OT/IT</th><th class="th-sub">H2<br>UI/CSS</th><th class="th-sub">H3<br>JS/DOM</th>
          <th class="th-sub">H4<br>JSON</th><th class="th-sub">H5<br>Hook</th><th class="th-sub">H6<br>Sec/QA</th>
          <th class="ws-sub">W1</th><th class="ws-sub">W2</th><th class="ws-sub">W3</th><th class="ws-sub">W4</th><th class="wt">หัก<br>Help</th>
          <th class="pr-sub">T1</th><th class="pr-sub">T2</th><th class="pr-sub">T3</th><th class="pr-sub">T4</th><th class="pr-sub">T5</th><th class="wt">หัก<br>Help</th>
        </tr>
        <tr>
          <th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th>
          <th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">(5)</th><th class="wt">-5max</th>
          <th class="wt">(10)</th><th class="wt">(10)</th><th class="wt">(10)</th><th class="wt">(10)</th><th class="wt">(10)</th><th class="wt">-10max</th>
        </tr>
      </thead>
      <tbody>{"".join(body_rows) if body_rows else "<tr><td colspan='31'>ยังไม่มีข้อมูลผู้เรียน</td></tr>"}{avg_row}</tbody>
    </table>
  </div>
  {ev_section}
</body>
</html>"""


if __name__ == "__main__":
    import os
    out_tpl = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "03_Audit_สรุปคะแนนการสอบ",
        "00_แบบฟอร์มเปล่า_สรุปคะแนน_วิชา_APP_v2_สำหรับ_Audit.xlsx",
    )
    export_audit_workbook(out_tpl)
    print(f"[OK] Generated v2 Audit Excel template: {out_tpl}")
