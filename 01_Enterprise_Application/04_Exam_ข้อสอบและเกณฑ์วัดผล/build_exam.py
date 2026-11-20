"""Central Exam Sync Builder (Single Source of Truth -> Google Apps Script + HTML Exam).

Usage:
    python build_exam.py          # Sync combined_exam.json -> create_boi_forms.gs & HTML exam
    python build_exam.py --check  # Verify all files match combined_exam.json (exit non-zero if stale)
"""
import argparse
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAM_JSON_PATH = os.path.join(BASE_DIR, "combined_exam.json")
GAS_PATH = os.path.join(BASE_DIR, "create_boi_forms.gs")
HTML_PATH = os.path.join(BASE_DIR, "ข้อสอบรวม_PostTest_และ_Final_ออนไลน์.html")

START_MARKER = "// <EXAM_DATA_START>"
END_MARKER = "// <EXAM_DATA_END>"


def load_and_validate_exam(path: str) -> dict:
    """Load combined_exam.json and validate counts, topic distribution, and HR Post-Test parity."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pre = data.get("preTest")
    theory = data.get("theoryExam")
    topics = data.get("topics")
    if not isinstance(pre, list) or len(pre) != 20:
        raise ValueError(f"preTest must have exactly 20 questions, found {len(pre or [])}")
    if not isinstance(theory, list) or len(theory) != 30:
        raise ValueError(f"theoryExam must have exactly 30 questions, found {len(theory or [])}")
    if not isinstance(topics, list) or len(topics) != 6:
        raise ValueError(f"topics must have exactly 6 definitions, found {len(topics or [])}")

    post_core_count = sum(1 for q in theory if q.get("isPostCore") is True)
    if post_core_count != 20:
        raise ValueError(f"theoryExam must have exactly 20 isPostCore questions for HR, found {post_core_count}")

    topic_counts = {t["topicNo"]: 0 for t in topics}
    for idx, q in enumerate(pre + theory, 1):
        choices = q.get("choices") or []
        ans = q.get("answer")
        if len(choices) != 4 or not isinstance(ans, int) or not (0 <= ans < 4):
            raise ValueError(f"Question index {idx} has invalid choices or answer: {q.get('q')}")
        if not q.get("why"):
            raise ValueError(f"Question index {idx} is missing 'why' explanation")

    for q in theory:
        t_no = q.get("topicNo")
        if t_no not in topic_counts:
            raise ValueError(f"Invalid topicNo {t_no} in theoryExam question: {q.get('q')}")
        topic_counts[t_no] += 1
        if q.get("points", 1) != 1:
            raise ValueError(f"All theoryExam questions must have 1 point each in v2: {q.get('q')}")

    bad_topics = {k: v for k, v in topic_counts.items() if v != 5}
    if bad_topics:
        raise ValueError(f"Each of the 6 topics must have exactly 5 questions, mismatch: {bad_topics}")

    return data


def build_payload_dict(data: dict) -> dict:
    """Return compact dict embedded into create_boi_forms.gs and offline HTML exam."""
    return {
        "version": data.get("version", 2),
        "title": data["title"],
        "subject": data["subject"],
        "minutes": data["minutes"],
        "topics": data["topics"],
        "instructions": data["instructions"],
        "preTest": data["preTest"],
        "theoryExam": data["theoryExam"],
    }


def replace_marked_block(content: str, const_name: str, payload_json: str) -> str:
    """Replace the block between START_MARKER and END_MARKER cleanly."""
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.DOTALL,
    )
    replacement = f"{START_MARKER}\nconst {const_name} = {payload_json};\n{END_MARKER}"
    updated, count = pattern.subn(lambda _: replacement, content, count=1)
    if count != 1:
        raise ValueError(f"Could not find unique {START_MARKER}..{END_MARKER} block")
    return updated


def sync_file(file_path: str, const_name: str, payload_json: str, check_only: bool) -> bool:
    """Write updated constant block to target file or compare in --check mode."""
    with open(file_path, "r", encoding="utf-8") as f:
        original = f.read()
    updated = replace_marked_block(original, const_name, payload_json)
    if original == updated:
        return True
    if check_only:
        return False
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync combined_exam.json to GAS & HTML exam.")
    parser.add_argument("--check", action="store_true", help="Verify files are up to date without modifying them.")
    args = parser.parse_args()

    data = load_and_validate_exam(EXAM_JSON_PATH)
    payload_json = json.dumps(build_payload_dict(data), ensure_ascii=False, separators=(",", ":"))
    # Escape HTML script-closing tags safely inside inline JS strings
    payload_for_html = payload_json.replace("</", "<\\/")

    targets = [
        (GAS_PATH, "EXAM_DATA", payload_json),
        (HTML_PATH, "EXAM", payload_for_html),
    ]

    stale = []
    for path, const_name, payload in targets:
        ok = sync_file(path, const_name, payload, args.check)
        if not ok:
            stale.append(os.path.basename(path))

    if args.check and stale:
        print(f"OUT OF SYNC: {', '.join(stale)}. Run `python build_exam.py`.", file=sys.stderr)
        return 1

    action = "Checked" if args.check else "Synced"
    print(f"[OK] {action} v2 exam bank (preTest=20, theoryExam=30, isPostCore=20, 6 topics x 5) -> create_boi_forms.gs & HTML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
