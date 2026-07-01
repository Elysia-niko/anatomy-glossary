from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_JSON = ROOT / "data" / "glossary.json"
OUTPUT_DIR = ROOT / "assets" / "pages" / "organic"


def find_organic_pdf() -> Path:
    desktop = Path.home() / "Desktop"
    candidates = [path for path in desktop.glob("*.pdf") if path.name.startswith("04.")]
    if not candidates:
        candidates = [path for path in desktop.glob("*.pdf") if "有机" in path.name]
    if not candidates:
        raise FileNotFoundError("No organic chemistry PDF found on Desktop.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def organic_pdf_pages() -> list[int]:
    payload = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    course = next(course for course in payload["courses"] if course["id"] == "organic-chemistry")
    pages = {int(page) for term in course["terms"] for page in term.get("pdfPages", [])}
    return sorted(pages)


def find_pdftoppm() -> str:
    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "native"
        / "poppler"
        / "Library"
        / "bin"
        / "pdftoppm.exe"
    )
    if bundled.exists():
        return str(bundled)
    found = shutil.which("pdftoppm") or shutil.which("pdftoppm.exe")
    if not found:
        raise RuntimeError("pdftoppm was not found")
    return found


def main() -> None:
    pdf = find_organic_pdf()
    pdftoppm = find_pdftoppm()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.gettempdir()) / "codex-organic-render"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_pdf = temp_dir / "organic.pdf"
    if not temp_pdf.exists() or temp_pdf.stat().st_size != pdf.stat().st_size:
        shutil.copyfile(pdf, temp_pdf)

    rendered = 0
    for pdf_page in organic_pdf_pages():
        target = OUTPUT_DIR / f"pdf-{pdf_page:03d}.jpg"
        if target.exists():
            continue
        prefix = temp_dir / f"page-{pdf_page:03d}"
        subprocess.run(
            [
                pdftoppm,
                "-jpeg",
                "-r",
                "130",
                "-f",
                str(pdf_page),
                "-l",
                str(pdf_page),
                "-singlefile",
                str(temp_pdf),
                str(prefix),
            ],
            check=True,
        )
        temp = prefix.with_suffix(".jpg")
        shutil.move(str(temp), target)
        rendered += 1

    print(f"rendered {rendered} organic page images into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
