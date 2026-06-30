from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]

HISTOLOGY_PAGE_OFFSET = 23
HISTOLOGY_BODY_BOOK_END = 280
HISTOLOGY_INDEX_BOOK_START = 283
HISTOLOGY_INDEX_BOOK_END = 296

HISTOLOGY_PARTS = [
    {"name": "组织学", "start": 1, "end": 198},
    {"name": "胚胎学", "start": 199, "end": 280},
]

HISTOLOGY_CHAPTERS = [
    {"name": "第1章 组织学绪论", "start": 2, "part": "组织学"},
    {"name": "第2章 上皮组织", "start": 9, "part": "组织学"},
    {"name": "第3章 结缔组织", "start": 20, "part": "组织学"},
    {"name": "第4章 软骨和骨", "start": 29, "part": "组织学"},
    {"name": "第5章 血液", "start": 41, "part": "组织学"},
    {"name": "第6章 肌组织", "start": 52, "part": "组织学"},
    {"name": "第7章 神经组织", "start": 60, "part": "组织学"},
    {"name": "第8章 神经系统", "start": 75, "part": "组织学"},
    {"name": "第9章 循环系统", "start": 83, "part": "组织学"},
    {"name": "第10章 免疫系统", "start": 94, "part": "组织学"},
    {"name": "第11章 皮肤", "start": 106, "part": "组织学"},
    {"name": "第12章 眼与耳", "start": 114, "part": "组织学"},
    {"name": "第13章 内分泌系统", "start": 127, "part": "组织学"},
    {"name": "第14章 消化管", "start": 136, "part": "组织学"},
    {"name": "第15章 消化腺", "start": 151, "part": "组织学"},
    {"name": "第16章 呼吸系统", "start": 161, "part": "组织学"},
    {"name": "第17章 泌尿系统", "start": 170, "part": "组织学"},
    {"name": "第18章 男性生殖系统", "start": 180, "part": "组织学"},
    {"name": "第19章 女性生殖系统", "start": 188, "part": "组织学"},
    {"name": "第20章 胚胎学绪论", "start": 200, "part": "胚胎学"},
    {"name": "第21章 胚胎发生总论", "start": 203, "part": "胚胎学"},
    {"name": "第22章 颜面和四肢的发生", "start": 221, "part": "胚胎学"},
    {"name": "第23章 消化系统和呼吸系统的发生", "start": 229, "part": "胚胎学"},
    {"name": "第24章 泌尿系统和生殖系统的发生", "start": 237, "part": "胚胎学"},
    {"name": "第25章 心血管系统的发生", "start": 247, "part": "胚胎学"},
    {"name": "第26章 神经系统的发生", "start": 259, "part": "胚胎学"},
    {"name": "第27章 眼与耳的发生", "start": 271, "part": "胚胎学"},
    {"name": "第28章 先天畸形概论", "start": 277, "part": "胚胎学"},
]

INDEX_PAGE_RE = re.compile(r"\s(\d{1,3}(?:\s*,\s*\d{1,3})*)\s")
FIG_RE = re.compile(r"图\s*([0-9]+)\s*[-－]\s*([0-9]+)")

STRUCTURE_KEYS = [
    "由",
    "组成",
    "分为",
    "包括",
    "称为",
    "称",
    "是",
    "为",
    "位于",
    "分布",
    "排列",
    "覆盖",
    "衬贴",
    "发生",
    "形成",
    "来源于",
]

FUNCTION_KEYS = [
    "功能",
    "作用",
    "分泌",
    "合成",
    "产生",
    "吸收",
    "排泄",
    "保护",
    "支持",
    "收缩",
    "运输",
    "传导",
    "调节",
    "免疫",
    "屏障",
    "营养",
    "修复",
    "增殖",
    "分化",
]

STUDY_NOTES = {
    "组织学技术": "复习时把技术名称、观察对象、染色或标记原理和能解决的问题放在一起记。",
    "上皮与腺": "重点抓细胞层数、表层形态、极性、基膜、分布部位和保护/吸收/分泌等功能。",
    "结缔组织": "把细胞、纤维、基质三件事分开记，再回到它们如何支持、连接、营养和防御。",
    "软骨和骨": "复习时按细胞类型、基质特点、组织发生方式和生长改建过程建立框架。",
    "血液与造血": "把血细胞形态、正常比例、寿命、功能和造血谱系连成一条线。",
    "肌组织": "比较骨骼肌、心肌和平滑肌的光镜结构、超微结构、连接方式和收缩特点。",
    "神经组织与系统": "优先记神经元、胶质细胞、纤维、突触和屏障，再联系所在系统功能。",
    "循环系统": "按管壁层次、内皮、平滑肌、弹性成分和血流压力关系来理解结构差异。",
    "免疫系统": "把免疫细胞、淋巴组织和淋巴器官放在抗原进入、识别、应答和迁移路径中复习。",
    "皮肤": "重点区分表皮分层、真皮结构、附属器和屏障/感觉/再生功能。",
    "眼与耳": "把感受细胞、支持结构、透明介质和传导方向对应起来记。",
    "内分泌系统": "按腺体、细胞类型、分泌激素、靶器官和调节轴来整理。",
    "消化系统": "先按黏膜、黏膜下层、肌层、外膜定位，再补细胞类型和分泌吸收功能。",
    "呼吸系统": "沿导气部到呼吸部梳理上皮、软骨/平滑肌、肺泡细胞和气血屏障。",
    "泌尿系统": "以肾单位和集合管为主线，连接滤过、重吸收、分泌和内分泌调节。",
    "生殖系统": "把生殖细胞发生、支持细胞、内分泌细胞和管道/周期变化一起复习。",
    "胚胎发生": "按时间顺序记：受精、卵裂、植入、胚层形成、胚体形成、胎膜和胎盘。",
    "器官发生": "先找胚层来源，再追踪原基、管腔、分隔、旋转、迁移和常见畸形。",
    "先天畸形": "复习时同时看发生时期、关键结构、致畸因素和最终形态改变。",
    "其他": "先定位到篇、章和系统，再补结构特点、功能意义和容易混淆的相关名词。",
}


def find_default_histology_pdf() -> Path:
    pdfs = sorted((Path.home() / "Desktop").glob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in pdfs:
        if "组织学" in path.name and "胚胎学" in path.name:
            return path
    for path in pdfs:
        if "10" in path.name and path.stat().st_size > 100_000_000:
            return path
    raise FileNotFoundError("No histology/embryology PDF found on Desktop. Pass --histology-pdf explicitly.")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\n", " ")
    text = re.sub(r"[\u2000-\u200f\u2028\u2029\ufeff\u3000]+", " ", text)
    fixes = {
        "immunohistoche m istry": "immunohistochemistry",
        "protion": "protein",
        "nature killer cell": "natural killer cell",
        "superfacial cortex": "superficial cortex",
        "complexe": "complex",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_context(text: str, start: int, end: int, limit: int = 280) -> str:
    left = max(text.rfind("。", 0, start), text.rfind("；", 0, start), text.rfind("?", 0, start), text.rfind("!", 0, start))
    right_candidates = [pos for pos in (text.find("。", end), text.find("；", end)) if pos != -1]
    right = min(right_candidates) + 1 if right_candidates else min(len(text), end + limit)
    left = left + 1 if left != -1 else max(0, start - 90)
    value = text[left:right].strip()
    value = re.sub(r"\s+", " ", value)
    if len(value) > limit:
        head = max(0, start - left - 50)
        value = value[head : head + limit].strip()
    return value


def chapter_for_page(book_page: int) -> str:
    chapter = HISTOLOGY_CHAPTERS[0]["name"]
    for item in HISTOLOGY_CHAPTERS:
        if book_page >= item["start"]:
            chapter = item["name"]
        else:
            break
    return chapter


def part_for_page(book_page: int) -> str:
    for part in HISTOLOGY_PARTS:
        if part["start"] <= book_page <= part["end"]:
            return part["name"]
    return "胚胎学" if book_page >= 199 else "组织学"


def chapter_number(chapter: str) -> int:
    match = re.search(r"第(\d+)章", chapter)
    return int(match.group(1)) if match else 0


def clean_index_english(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = value.replace("，", ",")
    value = value.replace("’", "'").replace("ʼ", "'")
    value = re.sub(r"\s*-\s*", "-", value)
    value = re.sub(r"\s*,\s*", ", ", value)
    value = re.sub(r"\b(type)([IVX]+)([A-Za-z])", r"\1 \2 \3", value, flags=re.IGNORECASE)
    value = re.sub(r"\b([BT])cell\b", r"\1 cell", value)
    value = re.sub(r"\b([BT])lymphocyte\b", r"\1 lymphocyte", value)
    return value.strip(" ,，、")


def strip_index_letter(chunk: str) -> str:
    match = re.match(r"^([A-Z])\s+(.+)$", chunk)
    if not match:
        return chunk
    letter, rest = match.groups()
    keep_prefix = (
        (letter in {"B", "T"} and rest.startswith(("细胞", "淋巴细胞")))
        or (letter == "Y" and rest.startswith("染色体"))
        or (letter == "X" and rest.startswith("线"))
        or (letter in {"I", "V"} and rest.startswith("型"))
    )
    return f"{letter}{rest}" if keep_prefix else rest


def parse_index_entries(index_texts: list[str]) -> list[dict[str, Any]]:
    entries = []
    for text in index_texts:
        text = re.sub(r"^\d+\s*中英文名词对照索引\s*", " ", text)
        text = re.sub(r"^中英文名词对照索引\s*\d+\s*", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        cursor = 0
        for match in INDEX_PAGE_RE.finditer(f" {text} "):
            chunk = text[cursor : match.start() - 1].strip()
            cursor = match.end() - 1
            if not chunk:
                continue
            chunk = strip_index_letter(chunk)
            cjk_positions = [idx for idx, char in enumerate(chunk) if "\u4e00" <= char <= "\u9fff"]
            if not cjk_positions:
                continue
            split_at = cjk_positions[-1] + 1
            while split_at < len(chunk) and chunk[split_at] in ")]）":
                split_at += 1
            zh = re.sub(r"\s+", "", chunk[:split_at]).strip(" ,，、")
            zh = re.sub(r"^\d+(?=[\u4e00-\u9fff])", "", zh)
            en = clean_index_english(chunk[split_at:])
            if not zh or not en:
                continue
            if any(noise in zh for noise in ("目录", "索引", "公众号", "推荐阅读")):
                continue
            pages = [int(page) for page in re.findall(r"\d{1,3}", match.group(1))]
            entries.append({"zh": zh, "en": en, "pages": pages})
    return entries


def extract_figures(text: str, book_page: int, pdf_page: int) -> list[dict[str, Any]]:
    figures = []
    for match in FIG_RE.finditer(text):
        chapter, number = match.groups()
        label = f"图{chapter}-{number}"
        tail = text[match.end() : match.end() + 70]
        tail = re.split(r"图\s*[0-9]+\s*[-－]\s*[0-9]+|表\s*[0-9]+|\d{4}/\d{1,2}/\d{1,2}", tail)[0]
        tail = re.split(r"[。；;]", tail)[0]
        caption = re.sub(r"\s+", " ", tail).strip(" :：,，、")
        if len(caption) > 32:
            caption = caption[:32]
        figures.append(
            {
                "label": label,
                "caption": caption,
                "bookPage": book_page,
                "pdfPage": pdf_page,
                "image": f"assets/pages/histology/pdf-{pdf_page:03d}.jpg",
            }
        )
    return figures


def figure_labels_in(text: str) -> list[str]:
    labels = []
    for chapter, number in FIG_RE.findall(text):
        labels.append(f"图{chapter}-{number}")
    return labels


def categorize(zh: str, en: str, first_page: int) -> str:
    chapter = chapter_number(chapter_for_page(first_page))
    if first_page >= 199:
        if chapter == 28:
            return "先天畸形"
        if any(word in zh for word in ("畸形", "闭锁", "缺损", "裂", "疝", "囊肿", "瘘", "隐睾", "异位", "前置")):
            return "先天畸形"
        if chapter in {20, 21} or any(word in zh for word in ("胚", "胎", "受精", "卵裂", "植入", "滋养", "羊膜", "胎盘", "蜕膜")):
            return "胚胎发生"
        return "器官发生"
    if chapter == 1:
        return "组织学技术"
    if chapter == 2:
        return "上皮与腺"
    if chapter == 3:
        return "结缔组织"
    if chapter == 4:
        return "软骨和骨"
    if chapter == 5:
        return "血液与造血"
    if chapter == 6:
        return "肌组织"
    if chapter in {7, 8}:
        return "神经组织与系统"
    if chapter == 9:
        return "循环系统"
    if chapter == 10:
        return "免疫系统"
    if chapter == 11:
        return "皮肤"
    if chapter == 12:
        return "眼与耳"
    if chapter == 13:
        return "内分泌系统"
    if chapter in {14, 15}:
        return "消化系统"
    if chapter == 16:
        return "呼吸系统"
    if chapter == 17:
        return "泌尿系统"
    if chapter in {18, 19}:
        return "生殖系统"
    return "其他"


def confidence_label(score: float) -> str:
    if score >= 0.9:
        return "高"
    if score >= 0.72:
        return "中"
    return "需复核"


def add_context(
    item: dict[str, Any],
    book_page: int,
    pdf_page: int,
    context: str,
    page_figure_labels: list[str],
    explicit_labels: list[str] | None = None,
) -> None:
    item["pages"].add(book_page)
    item["pdfPages"].add(pdf_page)
    item["chapters"].add(chapter_for_page(book_page))
    item["parts"].add(part_for_page(book_page))
    item["pageFigures"].update(page_figure_labels)
    if explicit_labels:
        item["figures"].update(explicit_labels)
    if context and len(item["contexts"]) < 4 and context not in {entry["text"] for entry in item["contexts"]}:
        item["contexts"].append(
            {
                "bookPage": book_page,
                "pdfPage": pdf_page,
                "chapter": chapter_for_page(book_page),
                "part": part_for_page(book_page),
                "text": context,
            }
        )


def find_context_for_term(text: str, zh: str, en: str) -> tuple[str, list[str], int]:
    positions: list[tuple[int, int]] = []
    zh_pos = text.find(zh)
    if zh_pos < 0 and len(zh) <= 14:
        loose = r"\s*".join(re.escape(char) for char in zh)
        loose_match = re.search(loose, text)
        if loose_match:
            zh_pos = loose_match.start()
    if zh_pos >= 0:
        positions.append((zh_pos, zh_pos + len(zh)))

    en_pos = text.lower().find(en.lower())
    if en_pos >= 0:
        positions.append((en_pos, en_pos + len(en)))

    if not positions:
        return "", [], 0
    start, end = min(positions, key=lambda value: value[0])
    count = 0
    if zh:
        count += text.count(zh)
    if en:
        count += text.lower().count(en.lower())
    context = compact_context(text, start, end)
    labels = figure_labels_in(text[max(0, start - 180) : min(len(text), end + 220)])
    return context, labels, max(1, count)


def best_sentence(contexts: list[dict[str, Any]], keys: list[str]) -> str:
    for item in contexts:
        chunks = re.split(r"(?<=[。；;])", item["text"])
        for chunk in chunks:
            if any(key in chunk for key in keys):
                return chunk.strip()[:230]
    return ""


def english_tokens(value: str) -> set[str]:
    stop = {"and", "or", "of", "the", "to", "in", "a", "an", "cell", "tissue", "system"}
    return {token for token in re.findall(r"[a-zA-Z]{3,}", value.lower()) if token not in stop}


def zh_fragments(value: str) -> set[str]:
    compact = re.sub(r"[A-Za-z0-9（）()\-\s,，、]+", "", value)
    if len(compact) < 3:
        return set()
    return {compact[index : index + 2] for index in range(len(compact) - 1)}


def assign_related_terms(terms: list[dict[str, Any]]) -> None:
    helpers = {}
    for term in terms:
        helpers[term["id"]] = {
            "pages": set(term["pages"]),
            "chapters": set(term["chapters"]),
            "tokens": english_tokens(term["en"]),
            "fragments": zh_fragments(term["zh"]),
            "text": " ".join([term["definition"], term["structure"], term["function"], *[c["text"] for c in term["contexts"]]]).lower(),
        }

    for term in terms:
        source = helpers[term["id"]]
        scored: list[tuple[int, int, str]] = []
        for candidate in terms:
            if candidate["id"] == term["id"]:
                continue
            target = helpers[candidate["id"]]
            score = 0
            if term["part"] == candidate["part"]:
                score += 1
            if term["category"] == candidate["category"]:
                score += 3
            if source["chapters"] & target["chapters"]:
                score += 5
            page_overlap = source["pages"] & target["pages"]
            if page_overlap:
                score += 6 + min(3, len(page_overlap))
            if len(term["zh"]) > 1 and len(candidate["zh"]) > 1 and (term["zh"] in candidate["zh"] or candidate["zh"] in term["zh"]):
                score += 4
            shared_fragments = source["fragments"] & target["fragments"]
            if shared_fragments:
                score += min(4, len(shared_fragments))
            shared_tokens = source["tokens"] & target["tokens"]
            if shared_tokens:
                score += min(4, len(shared_tokens) * 2)
            if candidate["zh"] in term["definition"] or candidate["zh"] in term["structure"]:
                score += 5
            if candidate["en"].lower() in source["text"]:
                score += 5
            if score >= 7:
                distance = abs(term["firstPage"] - candidate["firstPage"])
                scored.append((-score, distance, candidate["id"]))
        scored.sort()
        term["relatedTerms"] = [term_id for _, _, term_id in scored[:10]]


def build_histology_course(pdf_path: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    term_map: dict[tuple[str, str], dict[str, Any]] = {}
    figure_map: dict[str, dict[str, Any]] = {}
    page_figures: dict[int, list[str]] = defaultdict(list)
    page_texts: dict[int, str] = {}
    index_texts: list[str] = []

    for pdf_page in range(HISTOLOGY_PAGE_OFFSET + 1, len(reader.pages) + 1):
        book_page = pdf_page - HISTOLOGY_PAGE_OFFSET
        raw_text = reader.pages[pdf_page - 1].extract_text() or ""
        text = normalize_text(raw_text)
        if not text:
            continue
        if book_page <= HISTOLOGY_BODY_BOOK_END:
            page_texts[book_page] = text
            for figure in extract_figures(text, book_page, pdf_page):
                if figure["label"] not in figure_map:
                    figure_map[figure["label"]] = figure
                page_figures[book_page].append(figure["label"])
        if HISTOLOGY_INDEX_BOOK_START <= book_page <= HISTOLOGY_INDEX_BOOK_END:
            index_texts.append(text)

    index_entries = parse_index_entries(index_texts)
    for entry in index_entries:
        valid_pages = [page for page in entry["pages"] if 1 <= page <= HISTOLOGY_BODY_BOOK_END]
        if not valid_pages:
            continue
        first_page = valid_pages[0]
        key = (entry["zh"], entry["en"].lower())
        item = term_map.setdefault(
            key,
            {
                "id": f"he{len(term_map) + 1:04d}",
                "zh": entry["zh"],
                "en": entry["en"],
                "category": categorize(entry["zh"], entry["en"], first_page),
                "pages": set(),
                "pdfPages": set(),
                "chapters": set(),
                "parts": set(),
                "figures": set(),
                "pageFigures": set(),
                "contexts": [],
                "occurrences": 0,
                "confidence": 0.96,
                "sources": {"索引"},
            },
        )
        for book_page in valid_pages:
            pdf_page = book_page + HISTOLOGY_PAGE_OFFSET
            text = page_texts.get(book_page, "")
            context, explicit_labels, count = find_context_for_term(text, entry["zh"], entry["en"])
            item["occurrences"] += count if context else 0
            add_context(item, book_page, pdf_page, context, page_figures.get(book_page, []), explicit_labels)
            if context:
                continue
            for neighbor in (book_page - 1, book_page + 1):
                if neighbor < 1 or neighbor > HISTOLOGY_BODY_BOOK_END:
                    continue
                neighbor_text = page_texts.get(neighbor, "")
                context, explicit_labels, count = find_context_for_term(neighbor_text, entry["zh"], entry["en"])
                if context:
                    item["occurrences"] += count
                    add_context(item, neighbor, neighbor + HISTOLOGY_PAGE_OFFSET, context, page_figures.get(neighbor, []), explicit_labels)
                    break

    chapter_order = {item["name"]: idx for idx, item in enumerate(HISTOLOGY_CHAPTERS)}
    terms = []
    for item in term_map.values():
        pages = sorted(item["pages"])
        pdf_pages = sorted(item["pdfPages"])
        contexts = item["contexts"]
        if not pages:
            continue
        chapters = sorted(item["chapters"], key=lambda name: chapter_order.get(name, 999))
        parts = sorted(item["parts"], key=lambda name: 0 if name == "组织学" else 1)
        category = item["category"]
        figure_labels = sorted(item["figures"], key=lambda value: (figure_map.get(value, {}).get("bookPage", 9999), value))
        page_figure_labels = sorted(item["pageFigures"], key=lambda value: (figure_map.get(value, {}).get("bookPage", 9999), value))
        structure = best_sentence(contexts, STRUCTURE_KEYS)
        function = best_sentence(contexts, FUNCTION_KEYS)
        terms.append(
            {
                "id": item["id"],
                "zh": item["zh"],
                "en": item["en"],
                "part": parts[0] if parts else part_for_page(pages[0]),
                "parts": parts or [part_for_page(pages[0])],
                "category": category,
                "chapters": chapters,
                "pages": pages,
                "pdfPages": pdf_pages,
                "firstPage": pages[0],
                "firstPdfPage": pdf_pages[0],
                "definition": contexts[0]["text"] if contexts else "",
                "structure": structure,
                "location": structure,
                "function": function,
                "studyNote": STUDY_NOTES.get(category, STUDY_NOTES["其他"]),
                "figures": figure_labels,
                "pageFigures": page_figure_labels[:12],
                "pageImages": [f"assets/pages/histology/pdf-{page:03d}.jpg" for page in pdf_pages[:4]],
                "contexts": contexts,
                "occurrences": item["occurrences"],
                "confidence": round(item["confidence"], 2),
                "confidenceLabel": confidence_label(item["confidence"]),
                "sources": sorted(item["sources"]),
                "relatedTerms": [],
            }
        )

    terms.sort(key=lambda value: (value["firstPage"], chapter_order.get(value["chapters"][0], 999), value["zh"], value["en"]))
    assign_related_terms(terms)
    figures = sorted(figure_map.values(), key=lambda value: (value["bookPage"], value["label"]))

    return {
        "id": "histology-embryology",
        "title": "组织学与胚胎学",
        "shortTitle": "组织学与胚胎学",
        "description": "第10版教材词库，按组织学和胚胎学分篇整理。",
        "parts": HISTOLOGY_PARTS,
        "chapters": HISTOLOGY_CHAPTERS,
        "figures": figures,
        "terms": terms,
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "sourcePdf": pdf_path.name,
            "sourcePdfUrl": "",
            "pageOffset": HISTOLOGY_PAGE_OFFSET,
            "totalPdfPages": len(reader.pages),
            "bodyPages": HISTOLOGY_BODY_BOOK_END,
            "indexStartPage": HISTOLOGY_INDEX_BOOK_START,
            "indexEndPage": HISTOLOGY_INDEX_BOOK_END,
            "totalTerms": len(terms),
            "totalFigures": len(figures),
            "indexTerms": len(index_entries),
        },
    }


def load_anatomy_course(root: Path) -> dict[str, Any]:
    payload_path = root / "data" / "glossary.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if "courses" in payload:
        for course in payload["courses"]:
            if course["id"] == "systematic-anatomy":
                return course
        raise ValueError("Combined glossary exists but systematic-anatomy course was not found.")

    terms = payload.get("terms", [])
    for term in terms:
        term.setdefault("part", "系统解剖学")
        term.setdefault("parts", ["系统解剖学"])
        term.setdefault("structure", term.get("location", ""))
        term.setdefault("relatedTerms", [])
    return {
        "id": "systematic-anatomy",
        "title": "系统解剖学",
        "shortTitle": "系统解剖学",
        "description": "系统解剖学教材词库。",
        "parts": [{"name": "系统解剖学", "start": 1, "end": payload.get("meta", {}).get("bodyPages", 0)}],
        "chapters": payload.get("chapters", []),
        "figures": payload.get("figures", []),
        "terms": terms,
        "meta": payload.get("meta", {}),
    }


def prepare_course_terms(course: dict[str, Any]) -> None:
    fallback_part = course.get("parts", [{}])[0].get("name", course.get("title", ""))
    for term in course.get("terms", []):
        term.setdefault("part", fallback_part)
        term.setdefault("parts", [term.get("part", fallback_part)])
        term.setdefault("structure", term.get("location", ""))
        term.setdefault("location", term.get("structure", ""))
        term.setdefault("function", "")
        term.setdefault("definition", "")
        term.setdefault("contexts", [])
        term.setdefault("relatedTerms", [])
    if course.get("terms") and not any(term.get("relatedTerms") for term in course["terms"]):
        assign_related_terms(course["terms"])


def write_outputs(library: dict[str, Any], out_dir: Path) -> None:
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "glossary.json"
    js_path = data_dir / "glossary.js"
    csv_path = data_dir / "glossary.csv"
    report_path = data_dir / "report.json"

    json_text = json.dumps(library, ensure_ascii=False, indent=2)
    json_path.write_text(json_text, encoding="utf-8")
    js_path.write_text("window.MED_GLOSSARY = " + json_text + ";\nwindow.ANATOMY_GLOSSARY = window.MED_GLOSSARY;\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "课程",
                "篇",
                "中文",
                "English",
                "分类",
                "章节",
                "书页",
                "PDF页",
                "解释",
                "结构/分布",
                "功能/意义",
                "相关词条",
                "关联图",
                "置信度",
            ],
        )
        writer.writeheader()
        for course in library["courses"]:
            term_by_id = {term["id"]: term for term in course["terms"]}
            for term in course["terms"]:
                related = [term_by_id[term_id]["zh"] for term_id in term.get("relatedTerms", []) if term_id in term_by_id]
                writer.writerow(
                    {
                        "课程": course["title"],
                        "篇": term.get("part", ""),
                        "中文": term["zh"],
                        "English": term["en"],
                        "分类": term["category"],
                        "章节": " / ".join(term["chapters"]),
                        "书页": ", ".join(map(str, term["pages"])),
                        "PDF页": ", ".join(map(str, term["pdfPages"])),
                        "解释": term.get("definition", ""),
                        "结构/分布": term.get("structure") or term.get("location", ""),
                        "功能/意义": term.get("function", ""),
                        "相关词条": " / ".join(related),
                        "关联图": ", ".join(term.get("figures") or term.get("pageFigures") or []),
                        "置信度": term["confidenceLabel"],
                    }
                )

    report = {
        "generatedAt": library["meta"]["generatedAt"],
        "totalCourses": len(library["courses"]),
        "totalTerms": library["meta"]["totalTerms"],
        "totalFigures": library["meta"]["totalFigures"],
        "courses": {},
    }
    for course in library["courses"]:
        course_report = {
            "totalTerms": len(course["terms"]),
            "totalFigures": len(course.get("figures", [])),
            "categories": {},
            "parts": {},
            "chapters": {},
        }
        for term in course["terms"]:
            course_report["categories"][term["category"]] = course_report["categories"].get(term["category"], 0) + 1
            course_report["parts"][term.get("part", "")] = course_report["parts"].get(term.get("part", ""), 0) + 1
            for chapter in term["chapters"]:
                course_report["chapters"][chapter] = course_report["chapters"].get(chapter, 0) + 1
        report["courses"][course["id"]] = course_report
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def build_library(root: Path, histology_pdf: Path) -> dict[str, Any]:
    anatomy_course = load_anatomy_course(root)
    prepare_course_terms(anatomy_course)
    histology_course = build_histology_course(histology_pdf)
    courses = [anatomy_course, histology_course]
    return {
        "schemaVersion": 2,
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "totalCourses": len(courses),
            "totalTerms": sum(len(course["terms"]) for course in courses),
            "totalFigures": sum(len(course.get("figures", [])) for course in courses),
        },
        "courses": courses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the combined medical glossary for the static site.")
    parser.add_argument("--histology-pdf", type=Path, default=None, help="Path to the Histology and Embryology PDF.")
    parser.add_argument("--out", type=Path, default=ROOT, help="Output project directory.")
    args = parser.parse_args()

    histology_pdf = args.histology_pdf or find_default_histology_pdf()
    library = build_library(args.out, histology_pdf)
    write_outputs(library, args.out)
    print(json.dumps(library["meta"], ensure_ascii=False, indent=2))
    for course in library["courses"]:
        print(json.dumps({"id": course["id"], **course["meta"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
