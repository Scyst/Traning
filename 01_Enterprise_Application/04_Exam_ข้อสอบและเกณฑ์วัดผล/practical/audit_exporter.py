"""Audit v2 Excel Exporter (30 Theory + 20 Workshop + 50 Practical = 100 + Help Evidence Sheet).

Generates Leelawadee UI-styled Excel workbooks compatible with BOI/Government Audits
without Thai font rendering issues (zero tofu boxes on Windows Export-to-PDF).
"""

import csv
import io
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FONT_NAME = "Leelawadee UI"


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
        (31, "ผลประเมิน\n(>=70)", "D9D9D9", 10),
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
        (22, 27, "สอบปฏิบัติ Final: Electrical Meter Alert (50 คะแนน)", "5 TODO × 10 คะแนน + หัก Help Tiered Cap (Max -15)", "A9D08E", "C6E0B4"),
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
        (20, "หัก Help\nWorkshop", "(-Max 8)", "FCE4D6", 9),
        # V..AA (22..27) Practical
        (22, "TODO 1\nSetup URL", "(10)", "C6E0B4", 8),
        (23, "TODO 2\nDOM Meter", "(10)", "C6E0B4", 8),
        (24, "TODO 3\nCalc Power", "(10)", "C6E0B4", 8),
        (25, "TODO 4\nConditions", "(10)", "C6E0B4", 8),
        (26, "TODO 5\nPOST/Dedup", "(10)", "C6E0B4", 9),
        (27, "หัก Help/Dup\nสอบปฏิบัติ", "(-Max 15)", "FCE4D6", 10),
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

        # Split name heuristics cleanly when only full name given
        full_name = str(rec.get("full_name") or "").strip()
        prefix = str(rec.get("prefix") or "").strip()
        first_name = str(rec.get("first_name") or "").strip()
        last_name = str(rec.get("last_name") or "").strip()
        if full_name and not first_name:
            parts = full_name.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            else:
                first_name = full_name

        ws.cell(r, 1, idx + 1)
        ws.cell(r, 2, rec.get("emp_id", ""))
        ws.cell(r, 3, prefix)
        ws.cell(r, 4, first_name)
        ws.cell(r, 5, last_name)
        ws.cell(r, 6, rec.get("dept", ""))
        if rec.get("pre_20") is not None:
            ws.cell(r, 7, rec.get("pre_20"))
        if rec.get("post_hr_20") is not None:
            ws.cell(r, 8, rec.get("post_hr_20"))

        topics = rec.get("topics") or []
        for t_i in range(6):
            if t_i < len(topics) and topics[t_i] is not None:
                ws.cell(r, 9 + t_i, topics[t_i])

        ws.cell(r, 15, f'=IF(COUNT(I{r}:N{r})=0,"",SUM(I{r}:N{r}))')

        ws_scores = rec.get("workshops") or []
        for w_i in range(4):
            if w_i < len(ws_scores) and ws_scores[w_i] is not None:
                ws.cell(r, 16 + w_i, ws_scores[w_i])
        if rec.get("ws_help_penalty") is not None and rec.get("workshops"):
            ws.cell(r, 20, rec.get("ws_help_penalty"))
        ws.cell(r, 21, f'=IF(COUNT(P{r}:S{r})=0,"",MAX(0,MIN(20,SUM(P{r}:S{r})-SUM(T{r}))))')

        todos = rec.get("practical_todos") or []
        for p_i in range(5):
            if p_i < len(todos) and todos[p_i] is not None:
                ws.cell(r, 22 + p_i, todos[p_i])
        if rec.get("practical_deduct") is not None and rec.get("practical_todos"):
            ws.cell(r, 27, rec.get("practical_deduct"))
        ws.cell(r, 28, f'=IF(COUNT(V{r}:Z{r})=0,"",MAX(0,MIN(50,SUM(V{r}:Z{r})-SUM(AA{r}))))')

        ws.cell(r, 29, f'=IF(COUNT(O{r},U{r},AB{r})=0,"",SUM(O{r},U{r},AB{r}))')
        ws.cell(r, 30, f'=IF(AC{r}="","",IF(AC{r}>=80,"A",IF(AC{r}>=70,"B",IF(AC{r}>=60,"C",IF(AC{r}>=50,"D","F")))))')
        ws.cell(r, 31, f'=IF(AC{r}="","",IF(AC{r}>=70,"ผ่าน","ไม่ผ่าน"))')

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


if __name__ == "__main__":
    import os
    out_tpl = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "03_Audit_สรุปคะแนนการสอบ",
        "00_แบบฟอร์มเปล่า_สรุปคะแนน_วิชา_APP_v2_สำหรับ_Audit.xlsx",
    )
    export_audit_workbook(out_tpl)
    print(f"[OK] Generated v2 Audit Excel template: {out_tpl}")
