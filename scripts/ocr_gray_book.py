from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from PIL import Image
from PIL import ImageOps
from rapidocr_onnxruntime import RapidOCR


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "Grays Anatomy For Students, 3rd Edition"


@dataclass
class OcrLine:
    text: str
    score: float
    left: float
    top: float
    right: float
    bottom: float


def find_default_pdf() -> Path:
    base = Path.home() / "Documents" / "xwechat_files"
    matches = sorted(base.rglob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in matches:
        if DEFAULT_NAME.lower() in path.name.lower():
            return path
    raise FileNotFoundError("Gray's Anatomy for Students PDF was not found in xwechat_files.")


def parse_pages(values: list[str], page_count: int) -> list[int]:
    pages: set[int] = set()
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = [int(piece) for piece in part.split("-", 1)]
                pages.update(range(start, end + 1))
            else:
                pages.add(int(part))
    selected = sorted(page for page in pages if 1 <= page <= page_count)
    if not selected:
        raise ValueError("No valid PDF pages were selected.")
    return selected


def pixmap_to_array(pix: fitz.Pixmap) -> np.ndarray:
    mode = "RGB" if pix.n < 4 else "RGBA"
    image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.asarray(image)


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = value.replace("—", "-").replace("–", "-")
    return value


def result_to_lines(result: list[Any] | None) -> list[OcrLine]:
    lines: list[OcrLine] = []
    for item in result or []:
        if len(item) < 2:
            continue
        box = item[0]
        text = normalize_text(str(item[1]))
        score = float(item[2]) if len(item) > 2 else 0.0
        if not text:
            continue
        xs = [float(point[0]) for point in box]
        ys = [float(point[1]) for point in box]
        lines.append(OcrLine(text, score, min(xs), min(ys), max(xs), max(ys)))
    return lines


def sort_reading_order(lines: list[OcrLine], width: int) -> list[OcrLine]:
    if len(lines) < 12:
        return sorted(lines, key=lambda line: (line.top, line.left))

    center = width / 2
    left = [line for line in lines if line.right < center + width * 0.04]
    right = [line for line in lines if line.left > center - width * 0.04]
    crossing = [line for line in lines if line not in left and line not in right]

    has_two_columns = len(left) >= 5 and len(right) >= 5
    if not has_two_columns:
        return sorted(lines, key=lambda line: (line.top, line.left))

    header = [line for line in crossing if line.top < min((item.top for item in left + right), default=0) + 80]
    middle = [line for line in crossing if line not in header]
    ordered = sorted(header, key=lambda line: (line.top, line.left))
    ordered += sorted(left, key=lambda line: (line.top, line.left))
    ordered += sorted(right, key=lambda line: (line.top, line.left))
    ordered += sorted(middle, key=lambda line: (line.top, line.left))
    return ordered


def line_to_json(line: OcrLine) -> dict[str, Any]:
    return {
        "text": line.text,
        "score": round(line.score, 4),
        "box": [round(line.left, 1), round(line.top, 1), round(line.right, 1), round(line.bottom, 1)],
    }


def ocr_page(doc: fitz.Document, page_number: int, ocr: RapidOCR, scale: float) -> tuple[list[OcrLine], float]:
    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = pixmap_to_array(pix)
    start = time.time()
    result, _ = ocr(image)
    lines = sort_reading_order(result_to_lines(result), pix.width)
    return lines, time.time() - start


def find_tesseract(path: Path | None = None) -> Path:
    if path and path.exists():
        return path
    command = shutil.which("tesseract")
    if command:
        return Path(command)
    default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if default.exists():
        return default
    raise FileNotFoundError("tesseract.exe was not found.")


def ocr_page_tesseract(
    doc: fitz.Document,
    page_number: int,
    scale: float,
    tesseract: Path,
    psm: int,
) -> tuple[list[OcrLine], float]:
    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
    image = ImageOps.autocontrast(image)

    with tempfile.TemporaryDirectory(prefix="gray_tess_") as temp_dir:
        image_path = Path(temp_dir) / f"page-{page_number:04d}.png"
        image.save(image_path)
        start = time.time()
        result = subprocess.run(
            [str(tesseract), str(image_path), "stdout", "-l", "eng", "--psm", str(psm)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        seconds = time.time() - start
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Tesseract failed on page {page_number}")

    lines = []
    for index, line in enumerate(result.stdout.splitlines()):
        text = normalize_text(line)
        if text:
            lines.append(OcrLine(text=text, score=0.0, left=0, top=index, right=0, bottom=index))
    return lines, seconds


def write_page_outputs(output_dir: Path, page_number: int, lines: list[OcrLine]) -> None:
    pages_dir = output_dir / "pages"
    json_dir = output_dir / "json"
    pages_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    text = "\n".join(line.text for line in lines).strip() + "\n"
    (pages_dir / f"page-{page_number:04d}.txt").write_text(text, encoding="utf-8")
    (json_dir / f"page-{page_number:04d}.json").write_text(
        json.dumps([line_to_json(line) for line in lines], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_combined(output_dir: Path, pages: list[int], name: str) -> None:
    chunks = ["# Gray's Anatomy for Students OCR\n"]
    for page in pages:
        page_path = output_dir / "pages" / f"page-{page:04d}.txt"
        if not page_path.exists():
            continue
        chunks.append(f"\n## PDF page {page}\n")
        chunks.append(page_path.read_text(encoding="utf-8").strip())
        chunks.append("\n")
    (output_dir / name).write_text("\n".join(chunks), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR selected pages from Gray's Anatomy for Students.")
    parser.add_argument("--pdf", type=Path, default=None, help="Path to the Gray's Anatomy PDF.")
    parser.add_argument("--pages", nargs="+", default=[], help="PDF pages or ranges, for example: 868 994-996.")
    parser.add_argument("--all", action="store_true", help="OCR every page in the PDF.")
    parser.add_argument("--scale", type=float, default=2.0, help="Rendering scale. 2.0 is a good quality/speed balance.")
    parser.add_argument("--engine", choices=["rapidocr", "tesseract"], default="tesseract")
    parser.add_argument("--tesseract", type=Path, default=None, help="Path to tesseract.exe.")
    parser.add_argument("--psm", type=int, default=3, help="Tesseract page segmentation mode.")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "gray_ocr")
    parser.add_argument("--combined", default="gray_book_ocr_selected.md")
    parser.add_argument("--force", action="store_true", help="Re-OCR pages even if cached text already exists.")
    args = parser.parse_args()

    pdf = args.pdf or find_default_pdf()
    output_dir = args.out
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf)
    if args.all:
        pages = list(range(1, doc.page_count + 1))
    else:
        pages = parse_pages(args.pages, doc.page_count)

    ocr = RapidOCR() if args.engine == "rapidocr" else None
    tesseract = find_tesseract(args.tesseract) if args.engine == "tesseract" else None
    summary = {
        "pdf": str(pdf),
        "pageCount": doc.page_count,
        "selectedPages": pages,
        "scale": args.scale,
        "engine": args.engine,
        "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pages": [],
    }

    for index, page_number in enumerate(pages, start=1):
        text_path = output_dir / "pages" / f"page-{page_number:04d}.txt"
        if text_path.exists() and not args.force:
            print(f"[{index}/{len(pages)}] page {page_number}: cached")
            continue
        if args.engine == "tesseract":
            lines, seconds = ocr_page_tesseract(doc, page_number, args.scale, tesseract, args.psm)
        else:
            lines, seconds = ocr_page(doc, page_number, ocr, args.scale)
        write_page_outputs(output_dir, page_number, lines)
        summary["pages"].append({"page": page_number, "lines": len(lines), "seconds": round(seconds, 2)})
        print(f"[{index}/{len(pages)}] page {page_number}: {len(lines)} lines, {seconds:.2f}s")

    build_combined(output_dir, pages, args.combined)
    summary["finishedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (output_dir / "last_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"combined: {output_dir / args.combined}")


if __name__ == "__main__":
    main()
