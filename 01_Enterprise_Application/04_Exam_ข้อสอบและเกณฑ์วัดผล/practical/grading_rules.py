"""Scoring and Help-Request Deduction Rules for BOI Training Platform (v2).

Single Source of Truth shared by exam_server.py, auto_grader.py, and audit_exporter.py.

Design goals:
1. Prevent score inflation on Theory (30 pts = 6 topics x 5 pts each) and Practical (50 pts).
2. Incorporate Workshop 1-4 completion/code verification (20 pts = 4 x 5 pts).
3. Support fair self-requested Help / Hint deductions with diminishing decay + hard caps so
   independent learners earn full marks while struggling learners who ask for help are NEVER
   penalized down to zero.
"""

from typing import Any, Dict, List, Optional

EXAM_HELP_HINT_DECAY = (1.0, 2.0, 3.0)  # 1st=1, 2nd=2, 3rd=3, 4th+=1
EXAM_HELP_CODE_FIX_PENALTY = 3.0
EXAM_HELP_MAX_PENALTY = 15.0

WORKSHOP_FREE_HINTS = 2
WORKSHOP_HELP_HINT_PENALTY = 0.5
WORKSHOP_HELP_CODE_FIX_PENALTY = 1.5
WORKSHOP_HELP_MAX_PENALTY = 8.0

DEFAULT_PASS_SCORE = 70.0


def clamp_score(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp numeric score safely to [low, high] rounded to 1 decimal place."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return low
    if num != num:  # NaN guard
        return low
    return round(max(low, min(high, num)), 1)


def _norm_resolution(item: Dict[str, Any]) -> str:
    status = str(item.get("status") or "").strip().lower()
    if status != "resolved":
        return ""
    res = str(item.get("resolution") or "hint").strip().lower()
    if res in ("tech_issue", "tech", "free"):
        return "tech_issue"
    if res in ("code_fix", "fix", "major"):
        return "code_fix"
    return "hint"


def preview_next_exam_hint_cost(resolved_hints_so_far: int) -> float:
    """Return point cost of the NEXT hint in exam mode using tiered diminishing decay."""
    if resolved_hints_so_far < 0:
        resolved_hints_so_far = 0
    if resolved_hints_so_far < len(EXAM_HELP_HINT_DECAY):
        return EXAM_HELP_HINT_DECAY[resolved_hints_so_far]
    return 1.0


def calculate_help_penalty(
    help_requests: List[Dict[str, Any]],
    scope: str = "exam",
    raw_earned: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute diminishing capped help penalty for 'exam' or 'workshop' scope."""
    norm_scope = "workshop" if str(scope).strip().lower() == "workshop" else "exam"
    scoped = [
        req for req in (help_requests or [])
        if str(req.get("scope") or "").strip().lower() == norm_scope
    ]

    hint_count = 0
    code_fix_count = 0
    tech_issue_count = 0
    raw_penalty = 0.0

    for req in scoped:
        res = _norm_resolution(req)
        if not res:
            continue
        if res == "tech_issue":
            tech_issue_count += 1
        elif res == "hint":
            if norm_scope == "exam":
                raw_penalty += preview_next_exam_hint_cost(hint_count)
            else:
                if hint_count >= WORKSHOP_FREE_HINTS:
                    raw_penalty += WORKSHOP_HELP_HINT_PENALTY
            hint_count += 1
        elif res == "code_fix":
            code_fix_count += 1
            raw_penalty += (
                EXAM_HELP_CODE_FIX_PENALTY
                if norm_scope == "exam"
                else WORKSHOP_HELP_CODE_FIX_PENALTY
            )

    scope_cap = EXAM_HELP_MAX_PENALTY if norm_scope == "exam" else WORKSHOP_HELP_MAX_PENALTY
    capped_penalty = min(scope_cap, round(raw_penalty, 1))

    # Floor protection: help requests can never drop a student below 50% of earned raw score
    if raw_earned is not None:
        earned = max(0.0, float(raw_earned))
        floor_cap = round(earned * 0.5, 1)
        applied_penalty = min(capped_penalty, floor_cap)
    else:
        applied_penalty = capped_penalty

    return {
        "scope": norm_scope,
        "total_requests": len(scoped),
        "hint_count": hint_count,
        "code_fix_count": code_fix_count,
        "tech_issue_count": tech_issue_count,
        "uncapped_penalty": round(raw_penalty, 1),
        "max_cap": scope_cap,
        "applied_penalty": round(applied_penalty, 1),
    }


def compute_final_grade(
    theory_30: float,
    workshop_20: float,
    practical_50: float,
    pass_score: float = DEFAULT_PASS_SCORE,
) -> Dict[str, Any]:
    """Compute v2 100-point total, letter grade (A-F), and pass/fail status."""
    t = clamp_score(theory_30, 0.0, 30.0)
    w = clamp_score(workshop_20, 0.0, 20.0)
    p = clamp_score(practical_50, 0.0, 50.0)
    total = round(t + w + p, 1)

    if total >= 80.0:
        grade = "A"
    elif total >= 70.0:
        grade = "B"
    elif total >= 60.0:
        grade = "C"
    elif total >= 50.0:
        grade = "D"
    else:
        grade = "F"

    return {
        "theory_30": t,
        "workshop_20": w,
        "practical_50": p,
        "total_100": total,
        "grade": grade,
        "passed": total >= pass_score,
        "status_th": "ผ่าน" if total >= pass_score else "ไม่ผ่าน",
    }
