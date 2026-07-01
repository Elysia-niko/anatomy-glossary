from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOOK_PAGE_OFFSET = 12

GENERIC_KEYS = {
    "abdomen",
    "angle",
    "apex",
    "arch",
    "arm",
    "artery",
    "base",
    "body",
    "bone",
    "border",
    "brain",
    "canal",
    "cavity",
    "cell",
    "cord",
    "duct",
    "edge",
    "face",
    "fascia",
    "fissure",
    "floor",
    "foot",
    "foramen",
    "fossa",
    "ganglion",
    "gland",
    "groove",
    "hand",
    "head",
    "heart",
    "joint",
    "limb",
    "line",
    "liver",
    "lung",
    "margin",
    "muscle",
    "neck",
    "nerve",
    "plexus",
    "pole",
    "process",
    "region",
    "root",
    "sinus",
    "spine",
    "surface",
    "trunk",
    "vein",
    "wall",
}

CONTEXT_KEYWORDS = {
    "artery",
    "branch",
    "canal",
    "contains",
    "enters",
    "foramen",
    "fossa",
    "innervated",
    "insertion",
    "leaves",
    "ligament",
    "muscle",
    "nerve",
    "origin",
    "passes",
    "process",
    "sensory",
    "supplies",
    "table",
    "through",
    "transmits",
    "vein",
    "vessels",
}


def clean_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value.replace("—", "-").replace("–", "-")


def compact_key(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def word_count(value: str) -> int:
    return len(re.findall(r"[a-z0-9]+", value.lower()))


def candidate_names(term: dict[str, Any]) -> list[str]:
    names = [term.get("en", ""), *(term.get("aliases") or [])]
    seen = set()
    out = []
    for name in names:
        name = clean_text(name)
        key = compact_key(name)
        if not key or key in seen or key in GENERIC_KEYS:
            continue
        if len(key) < 7:
            continue
        if word_count(name) == 1 and len(key) < 9:
            continue
        seen.add(key)
        out.append(name)
    return out


def load_ocr_pages(pages_dir: Path) -> list[dict[str, Any]]:
    pages = []
    for path in sorted(pages_dir.glob("page-*.txt")):
        match = re.search(r"page-(\d+)\.txt$", path.name)
        if not match:
            continue
        pdf_page = int(match.group(1))
        lines = [clean_text(line) for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
        lines = [line for line in lines if line]
        pages.append(
            {
                "pdfPage": pdf_page,
                "bookPage": pdf_page - BOOK_PAGE_OFFSET if pdf_page > BOOK_PAGE_OFFSET else None,
                "lines": lines,
                "compactLines": [compact_key(line) for line in lines],
                "compactText": compact_key(" ".join(lines)),
                "lowerText": clean_text(" ".join(lines)).lower(),
            }
        )
    return pages


def snippet_for_line(lines: list[str], index: int, radius: int = 3) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    text = " ".join(lines[start:end])
    text = re.sub(r"Click here to Visit - www\.thedentalhub\.org\.in", "", text, flags=re.IGNORECASE)
    text = clean_text(text)
    if len(text) > 620:
        text = text[:617].rstrip() + "..."
    return text


def score_hit(name: str, page: dict[str, Any], line_index: int, line: str, snippet: str) -> int:
    key = compact_key(name)
    score = 40 + min(40, len(key) // 2)
    name_lower = name.lower()
    if name_lower in page["lowerText"]:
        score += 35
    if name_lower in line.lower():
        score += 30
    score += sum(8 for word in CONTEXT_KEYWORDS if word in snippet.lower())
    if re.search(r"\b(v[123]|cn|ix|xii|nerve|artery|vein|vessels)\b", snippet.lower()):
        score += 18
    if line_index < 4:
        score -= 15
    return score


def find_hits_for_term(term: dict[str, Any], pages: list[dict[str, Any]], max_hits: int) -> list[dict[str, Any]]:
    names = candidate_names(term)
    if not names:
        return []

    hits_by_page: dict[int, dict[str, Any]] = {}
    for name in names:
        key = compact_key(name)
        for page in pages:
            if key not in page["compactText"]:
                continue
            for index, compact_line in enumerate(page["compactLines"]):
                if key not in compact_line:
                    continue
                snippet = snippet_for_line(page["lines"], index)
                score = score_hit(name, page, index, page["lines"][index], snippet)
                hit = {
                    "pdfPage": page["pdfPage"],
                    "bookPage": page["bookPage"],
                    "matched": name,
                    "line": page["lines"][index],
                    "snippet": snippet,
                    "score": score,
                }
                current = hits_by_page.get(page["pdfPage"])
                if not current or hit["score"] > current["score"]:
                    hits_by_page[page["pdfPage"]] = hit
                break

    hits = sorted(hits_by_page.values(), key=lambda item: (-item["score"], item["pdfPage"]))
    return hits[:max_hits]


def build_book_summary(term: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    page_labels = []
    for hit in hits:
        if hit.get("bookPage"):
            page_labels.append(f"正书第 {hit['bookPage']} 页")
        else:
            page_labels.append(f"PDF 第 {hit['pdfPage']} 页")
    joined = "、".join(page_labels[:3])
    return {
        "zh": f"格氏正书 OCR 在{joined}附近定位到“{term.get('zh') or term.get('en')}”的相关上下文；可展开英文片段核对原书语境。",
        "en": f"Gray's Anatomy for Students OCR located contexts for {term.get('en')} around {', '.join(page_labels[:3])}.",
    }


def update_report(report_path: Path, meta: dict[str, Any]) -> None:
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["grayBookOcrGeneratedAt"] = meta["grayBookOcrGeneratedAt"]
    report["grayBookOcrTerms"] = meta["grayBookOcrTerms"]
    report["grayBookOcrHits"] = meta["grayBookOcrHits"]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_payload(payload: dict[str, Any], out: Path) -> None:
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    data_dir = out / "data"
    (data_dir / "glossary.json").write_text(json_text, encoding="utf-8")
    (data_dir / "glossary.js").write_text(
        "window.MED_GLOSSARY = " + json_text + ";\nwindow.ANATOMY_GLOSSARY = window.MED_GLOSSARY;\n",
        encoding="utf-8",
    )
    update_report(data_dir / "report.json", payload["meta"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach Gray's Anatomy OCR book hits to glossary terms.")
    parser.add_argument("--out", type=Path, default=ROOT)
    parser.add_argument("--ocr-pages", type=Path, default=ROOT / "data" / "gray_ocr" / "pages")
    parser.add_argument("--max-hits", type=int, default=3)
    parser.add_argument("--min-score", type=int, default=78)
    args = parser.parse_args()

    payload_path = args.out / "data" / "glossary.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    anatomy = next(course for course in payload["courses"] if course["id"] == "systematic-anatomy")
    pages = load_ocr_pages(args.ocr_pages)
    if not pages:
        raise FileNotFoundError(f"No OCR page text files found under {args.ocr_pages}")

    term_count = 0
    hit_count = 0
    for term in anatomy["terms"]:
        hits = [hit for hit in find_hits_for_term(term, pages, args.max_hits) if hit["score"] >= args.min_score]
        gray = term.get("gray") or {}
        if hits:
            summary = build_book_summary(term, hits)
            gray["book"] = {
                "zh": summary["zh"],
                "en": summary["en"],
                "hits": hits,
            }
            term["gray"] = gray
            term_count += 1
            hit_count += len(hits)
        elif gray:
            gray.pop("book", None)

    payload["meta"]["grayBookOcrGeneratedAt"] = datetime.now().isoformat(timespec="seconds")
    payload["meta"]["grayBookOcrTerms"] = term_count
    payload["meta"]["grayBookOcrHits"] = hit_count
    payload["meta"]["grayBookOcrPages"] = len(pages)
    write_payload(payload, args.out)
    print(
        json.dumps(
            {
                "ocrPages": len(pages),
                "grayBookOcrTerms": term_count,
                "grayBookOcrHits": hit_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
