from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "Grays Anatomy For Students, 3rd Edition"


def find_default_pdf() -> Path:
    base = Path.home() / "Documents" / "xwechat_files"
    matches = sorted(base.rglob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in matches:
        if DEFAULT_NAME.lower() in path.name.lower():
            return path
    raise FileNotFoundError("Gray's Anatomy for Students PDF was not found in xwechat_files.")


def referenced_pages(glossary_path: Path) -> list[int]:
    payload = json.loads(glossary_path.read_text(encoding="utf-8"))
    pages = {
        int(hit["pdfPage"])
        for course in payload.get("courses", [])
        for term in course.get("terms", [])
        for hit in term.get("gray", {}).get("book", {}).get("hits", [])
        if hit.get("pdfPage")
    }
    return sorted(pages)


def render_page(doc: fitz.Document, page_number: int, output_path: Path, scale: float, quality: int) -> None:
    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Gray's Anatomy book pages referenced by OCR hits.")
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--glossary", type=Path, default=ROOT / "data" / "glossary.json")
    parser.add_argument("--out", type=Path, default=ROOT / "assets" / "pages" / "gray-book")
    parser.add_argument("--scale", type=float, default=1.55)
    parser.add_argument("--quality", type=int, default=74)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pages = referenced_pages(args.glossary)
    pdf = args.pdf or find_default_pdf()
    doc = fitz.open(pdf)

    rendered = 0
    skipped = 0
    for index, page_number in enumerate(pages, start=1):
        target = args.out / f"pdf-{page_number:04d}.jpg"
        if target.exists() and target.stat().st_size > 0 and not args.force:
            skipped += 1
            continue
        render_page(doc, page_number, target, args.scale, args.quality)
        rendered += 1
        if rendered % 50 == 0:
            print(f"rendered {rendered}/{len(pages)} last=PDF {page_number}")

    total_bytes = sum(path.stat().st_size for path in args.out.glob("*.jpg"))
    print(
        json.dumps(
            {
                "referencedPages": len(pages),
                "rendered": rendered,
                "skipped": skipped,
                "output": str(args.out),
                "totalJpgBytes": total_bytes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
