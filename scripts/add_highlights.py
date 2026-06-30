from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def normalize_compact(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"[\s\u2000-\u200f\u3000]+", "", value)
    value = re.sub(r"[，,。.;；:：、（）()\[\]【】\-–—_·'\"“”‘’]+", "", value)
    return value


def find_pdf(kind: str) -> Path | None:
    pdfs = sorted((Path.home() / "Desktop").glob("*.pdf"), key=lambda path: path.stat().st_size, reverse=True)
    if kind == "histology":
        for path in pdfs:
            if path.stat().st_size > 100_000_000:
                return path
    if kind == "anatomy":
        for path in pdfs:
            if path.name.startswith("06.") or "系统解剖学" in path.name:
                return path
    return None


def layout_lines(reader: PdfReader, pdf_page: int) -> list[str]:
    try:
        text = reader.pages[pdf_page - 1].extract_text(
            extraction_mode="layout",
            layout_mode_space_vertically=False,
        )
    except Exception:
        text = reader.pages[pdf_page - 1].extract_text() or ""
    lines = []
    for line in (text or "").splitlines():
        if line.strip():
            lines.append(unicodedata.normalize("NFKC", line.rstrip()))
    return lines


def term_targets(term: dict[str, Any]) -> list[tuple[str, int]]:
    targets: list[tuple[str, int]] = []
    zh = normalize_compact(term.get("zh", ""))
    if len(zh) >= 2:
        targets.append((zh, 4))
    for part in re.split(r"[,，;；]", term.get("en", "")):
        compact = normalize_compact(part)
        if len(compact) >= 4:
            targets.append((compact, 5))
    full_en = normalize_compact(term.get("en", ""))
    if len(full_en) >= 4:
        targets.append((full_en, 3))
    seen = set()
    unique = []
    for value, score in targets:
        if value in seen:
            continue
        seen.add(value)
        unique.append((value, score))
    return unique


def line_box(index: int, total: int, raw_line: str) -> dict[str, float]:
    # Layout extraction preserves the visual line order better than the PDF text
    # matrices for these books. The percentages below model the printed text
    # area and intentionally highlight whole lines like a study marker.
    if index == 0:
        y = 12.0
        height = 2.4
    else:
        step = (91.0 - 20.5) / max(1, total - 2)
        y = 20.5 + (index - 1) * step
        height = min(2.4, max(1.4, step * 0.72))
    leading = len(raw_line) - len(raw_line.lstrip(" "))
    x = 7.4 + min(34.0, leading * 0.34)
    width = max(18.0, min(85.0, 92.5 - x))
    return {
        "x": round(x, 2),
        "y": round(max(3.0, min(95.0, y)), 2),
        "w": round(width, 2),
        "h": round(height, 2),
    }


def boxes_for_term_on_page(lines: list[str], term: dict[str, Any], limit: int = 3) -> list[dict[str, float]]:
    targets = term_targets(term)
    if not targets:
        return []

    scored: list[tuple[int, int, dict[str, float]]] = []
    for index, line in enumerate(lines):
        compact_line = normalize_compact(line)
        if not compact_line:
            continue
        score = 0
        for target, target_score in targets:
            if target and target in compact_line:
                score += target_score
        if score <= 0:
            continue
        # Prefer definition-like lines over chapter headers when both match.
        if re.search(r"第\s*\d+\s*章", line):
            score -= 2
        if "。" in line or "，" in line or "(" in line or "（" in line:
            score += 1
        scored.append((-score, index, line_box(index, len(lines), line)))

    scored.sort()
    boxes: list[dict[str, float]] = []
    used_y: list[float] = []
    for _, _, box in scored:
        if any(abs(box["y"] - y) < 0.9 for y in used_y):
            continue
        boxes.append(box)
        used_y.append(box["y"])
        if len(boxes) >= limit:
            break
    boxes.sort(key=lambda item: item["y"])
    return boxes


def candidate_pages(term: dict[str, Any]) -> list[tuple[int, int]]:
    pages: list[tuple[int, int]] = []
    seen = set()
    for context in term.get("contexts", [])[:3]:
        pdf_page = context.get("pdfPage")
        book_page = context.get("bookPage")
        if pdf_page and pdf_page not in seen:
            pages.append((int(pdf_page), int(book_page or 0)))
            seen.add(pdf_page)
    for pdf_page, book_page in zip(term.get("pdfPages", [])[:3], term.get("pages", [])[:3]):
        if pdf_page and pdf_page not in seen:
            pages.append((int(pdf_page), int(book_page or 0)))
            seen.add(pdf_page)
    return pages[:3]


def add_course_highlights(course: dict[str, Any], reader: PdfReader | None) -> tuple[int, int]:
    if reader is None:
        return 0, 0
    line_cache: dict[int, list[str]] = {}
    highlighted_terms = 0
    total_boxes = 0

    for term in course.get("terms", []):
        highlights = []
        for pdf_page, book_page in candidate_pages(term):
            if pdf_page < 1 or pdf_page > len(reader.pages):
                continue
            if pdf_page not in line_cache:
                line_cache[pdf_page] = layout_lines(reader, pdf_page)
            boxes = boxes_for_term_on_page(line_cache[pdf_page], term)
            if boxes:
                highlights.append({"pdfPage": pdf_page, "bookPage": book_page, "boxes": boxes})
        term["highlights"] = highlights
        if highlights:
            highlighted_terms += 1
            total_boxes += sum(len(item["boxes"]) for item in highlights)
    return highlighted_terms, total_boxes


def write_payload(payload: dict[str, Any], out_dir: Path, highlight_report: dict[str, Any]) -> None:
    data_dir = out_dir / "data"
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    (data_dir / "glossary.json").write_text(json_text, encoding="utf-8")
    (data_dir / "glossary.js").write_text(
        "window.MED_GLOSSARY = " + json_text + ";\nwindow.ANATOMY_GLOSSARY = window.MED_GLOSSARY;\n",
        encoding="utf-8",
    )
    report_path = data_dir / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["highlightGeneratedAt"] = highlight_report["generatedAt"]
        report["highlightedTerms"] = sum(item["highlightedTerms"] for item in highlight_report["courses"].values())
        report["highlightBoxes"] = sum(item["highlightBoxes"] for item in highlight_report["courses"].values())
        for course_id, course_report in highlight_report["courses"].items():
            report.setdefault("courses", {}).setdefault(course_id, {}).update(course_report)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add line-level highlighter boxes to glossary terms.")
    parser.add_argument("--out", type=Path, default=ROOT, help="Project directory containing data/glossary.json.")
    parser.add_argument("--anatomy-pdf", type=Path, default=None)
    parser.add_argument("--histology-pdf", type=Path, default=None)
    args = parser.parse_args()

    payload_path = args.out / "data" / "glossary.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    anatomy_pdf = args.anatomy_pdf or find_pdf("anatomy")
    histology_pdf = args.histology_pdf or find_pdf("histology")
    readers = {
        "systematic-anatomy": PdfReader(str(anatomy_pdf)) if anatomy_pdf and anatomy_pdf.exists() else None,
        "histology-embryology": PdfReader(str(histology_pdf)) if histology_pdf and histology_pdf.exists() else None,
    }

    report: dict[str, Any] = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "courses": {},
    }
    for course in payload.get("courses", []):
        highlighted_terms, total_boxes = add_course_highlights(course, readers.get(course.get("id", "")))
        report["courses"][course.get("id", "")] = {
            "highlightedTerms": highlighted_terms,
            "highlightBoxes": total_boxes,
        }

    payload.setdefault("meta", {})["highlightGeneratedAt"] = report["generatedAt"]
    payload["meta"]["highlightedTerms"] = sum(item["highlightedTerms"] for item in report["courses"].values())
    payload["meta"]["highlightBoxes"] = sum(item["highlightBoxes"] for item in report["courses"].values())
    write_payload(payload, args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
