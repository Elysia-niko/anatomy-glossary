from __future__ import annotations

import csv
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
GLOSSARY_JSON = DATA_DIR / "glossary.json"
GLOSSARY_JS = DATA_DIR / "glossary.js"
GLOSSARY_CSV = DATA_DIR / "glossary.csv"
REPORT_JSON = DATA_DIR / "report.json"

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
LEADING_JUNK_RE = re.compile(r"^[\s)\]）~,，:：;；.。\-—]+")
HAS_CONTENT_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]")


def clean_general_text(value: str) -> str:
    chars: list[str] = []
    for ch in str(value):
        category = unicodedata.category(ch)
        if category in {"Cc", "Cf"}:
            continue
        chars.append(ch)
    return re.sub(r"\s+", " ", "".join(chars)).strip()


def clean_caption(value: str) -> str:
    text = str(value or "")
    match = CONTROL_RE.search(text)
    if match:
        text = text[: match.start()]
    text = clean_general_text(text)
    text = LEADING_JUNK_RE.sub("", text).strip()
    text = re.sub(r"[\u1160-\u11ff]+(?:JOE+|JO)?$", "", text).strip()
    return text if HAS_CONTENT_RE.search(text) else ""


def normalize_for_compare(value: str) -> str:
    text = clean_general_text(value)
    text = re.sub(r"\s+", "", text)
    return text.strip("。；;，,：:、")


def is_duplicate_text(candidate: str, reference: str) -> bool:
    left = normalize_for_compare(candidate)
    right = normalize_for_compare(reference)
    if not left or not right:
        return False
    if left == right:
        return len(left) > 10
    if len(left) <= 20:
        return False
    shorter, longer = sorted((left, right), key=len)
    if len(shorter) > 35 and shorter in longer and len(shorter) / len(longer) >= 0.55:
        return True
    return False


def clean_strings(value: Any) -> Any:
    if isinstance(value, str):
        return clean_general_text(value)
    if isinstance(value, list):
        return [clean_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_strings(item) for key, item in value.items()}
    return value


def clean_figures(course: dict[str, Any]) -> dict[str, int]:
    stats = {"captions_changed": 0, "captions_blank": 0}
    for figure in course.get("figures", []):
        original = figure.get("caption", "")
        cleaned = clean_caption(original)
        if cleaned != original:
            stats["captions_changed"] += 1
            if not cleaned:
                stats["captions_blank"] += 1
            figure["caption"] = cleaned
        if "label" in figure:
            figure["label"] = clean_general_text(figure["label"])
    return stats


def clean_histology_semantics(course: dict[str, Any]) -> dict[str, int]:
    stats = {"structure": 0, "location": 0, "function": 0}
    if course.get("id") != "histology-embryology":
        return stats

    for term in course.get("terms", []):
        definition = term.get("definition", "")
        for field in ("structure", "location", "function"):
            if is_duplicate_text(term.get(field, ""), definition):
                term[field] = ""
                stats[field] += 1

        if is_duplicate_text(term.get("location", ""), term.get("structure", "")):
            term["location"] = ""
            stats["location"] += 1
        if is_duplicate_text(term.get("function", ""), term.get("structure", "")) or is_duplicate_text(
            term.get("function", ""), term.get("location", "")
        ):
            term["function"] = ""
            stats["function"] += 1

    return stats


def write_csv(library: dict[str, Any]) -> None:
    headers = ["课程", "篇", "中文", "English", "分类", "章节", "书页", "PDF页", "解释", "结构/分布", "功能/意义", "相关词条", "关联图", "置信度"]
    rows: list[dict[str, str]] = []
    for course in library.get("courses", []):
        terms_by_id = {term.get("id"): term for term in course.get("terms", [])}
        for term in course.get("terms", []):
            related = [terms_by_id.get(term_id, {}).get("zh", term_id) for term_id in term.get("relatedTerms", [])]
            rows.append(
                {
                    "课程": course.get("title", ""),
                    "篇": term.get("part", ""),
                    "中文": term.get("zh", ""),
                    "English": term.get("en", ""),
                    "分类": term.get("category", ""),
                    "章节": "；".join(term.get("chapters", [])),
                    "书页": "；".join(map(str, term.get("pages", []))),
                    "PDF页": "；".join(map(str, term.get("pdfPages", []))),
                    "解释": term.get("definition", ""),
                    "结构/分布": term.get("structure") or term.get("location", ""),
                    "功能/意义": term.get("function", ""),
                    "相关词条": "；".join(related),
                    "关联图": "；".join(term.get("figures", []) or term.get("pageFigures", [])),
                    "置信度": term.get("confidenceLabel", ""),
                }
            )

    with GLOSSARY_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    library = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    library = clean_strings(library)

    totals: dict[str, Any] = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "figureCaptionChanges": 0,
        "blankFigureCaptions": 0,
        "histologyDuplicateFieldsCleared": {"structure": 0, "location": 0, "function": 0},
    }

    for course in library.get("courses", []):
        figure_stats = clean_figures(course)
        totals["figureCaptionChanges"] += figure_stats["captions_changed"]
        totals["blankFigureCaptions"] += figure_stats["captions_blank"]

        semantic_stats = clean_histology_semantics(course)
        for key, value in semantic_stats.items():
            totals["histologyDuplicateFieldsCleared"][key] += value

    text = json.dumps(library, ensure_ascii=False, indent=2)
    GLOSSARY_JSON.write_text(text + "\n", encoding="utf-8")
    GLOSSARY_JS.write_text("window.MED_GLOSSARY = " + text + ";\n", encoding="utf-8")
    write_csv(library)

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8")) if REPORT_JSON.exists() else {}
    report["cleanedAt"] = totals["generatedAt"]
    report["cleaning"] = totals
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
