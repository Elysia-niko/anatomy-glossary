import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
COURSES_DIR = DATA_DIR / "courses"
GLOSSARY_JSON = DATA_DIR / "glossary.json"
TOPICS_JS = DATA_DIR / "topics.js"
REPORT_JSON = DATA_DIR / "text_cleanup_report.json"
DATA_VERSION = "textclean-20260707"

TEXT_FIELDS = ("definition", "structure", "location", "function", "studyNote", "mnemonic")
FIGURE_TEXT_FIELDS = ("caption",)
GRAY_TEXT_FIELDS = ("zh",)
GRAY_BOOK_TEXT_FIELDS = ("zh",)
GRAY_HIT_TEXT_FIELDS = ("matched", "snippet", "line")

CN = r"\u3400-\u4dbf\u4e00-\u9fff"
CN_RE = re.compile(f"[{CN}]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b\u200c\u200d\ufeff]")
PROTECTED_TOKEN_RE = re.compile(r"\b(?:[A-Z]{1,6}\d*|pH|sp[23]|Ig[A-Z]?|mRNA|tRNA|rRNA|DNA|RNA)\s+(?=[\u3400-\u4dbf\u4e00-\u9fff])")
KNOWN_JOIN_WORDS = set()


def has_cn(text):
    return bool(CN_RE.search(text or ""))


def clean_text(value):
    if not isinstance(value, str) or not value:
        return value
    if not has_cn(value):
        return normalize_non_cn_text(value)

    text = CONTROL_RE.sub("", value)
    text = text.replace("\u3000", " ")
    text = text.replace("（ ", "（").replace(" ）", "）")
    text = re.sub(r"[ \t\r\n]+", " ", text).strip()

    # Common OCR splits inside Chinese words and numbering phrases.
    text = re.sub(f"([{CN}])\\s+([{CN}])", r"\1\2", text)
    text = normalize_numeric_spacing(text)
    text = re.sub(r"\b(sp)\s+([23])\b", r"\1\2", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=\b\d)\s+([spdf])\s*(?=[轨層层能])", r"\1", text, flags=re.IGNORECASE)
    text = repair_split_english_terms(text)
    text = normalize_organic_ocr_tokens(text)

    # Keep full English terms readable, but attach short biomedical abbreviations to Chinese.
    text = PROTECTED_TOKEN_RE.sub(lambda match: match.group(0).replace(" ", ""), text)
    text = re.sub(r"(?<=[" + CN + r"]) +([A-Z]{1,6}\d*|pH|sp[23]|Ig[A-Z]?|DNA|RNA|mRNA|tRNA|rRNA)(?=[" + CN + r"])", r"\1", text)

    # Normalize spaces around punctuation that belongs to Chinese prose.
    text = re.sub(r"\s+([，。；：！？、])", r"\1", text)
    text = re.sub(r"([，。；：！？、])\s+", r"\1", text)
    text = re.sub(r"\s+([,.;:!?])(?=\s*[" + CN + r"])", r"\1", text)
    text = re.sub(r"([" + CN + r"])\s+([,.;:!?])", r"\1\2", text)

    # Convert halfwidth punctuation when it is adjacent to Chinese prose.
    replacements = {
        ",": "，",
        ";": "；",
        ":": "：",
        "?": "？",
        "!": "！",
    }
    for half, full in replacements.items():
        text = re.sub(f"([{CN}]){re.escape(half)}(?=\\s*([{CN}A-Za-z0-9]))", rf"\1{full}", text)
        text = re.sub(f"([{CN}]){re.escape(half)}(?=\\s*[（(])", rf"\1{full}", text)
        text = re.sub(f"([A-Za-z0-9]){re.escape(half)}(?=\\s*([{CN}]))", rf"\1{full}", text)
        text = re.sub(f"([%）°′]){re.escape(half)}(?=\\s*([{CN}]))", rf"\1{full}", text)
        text = re.sub(f"([{CN}]){re.escape(half)}$", rf"\1{full}", text)

    # A period after Chinese prose should be a Chinese full stop, but list markers like "1. 长骨" stay as-is.
    text = re.sub(f"([{CN}])\\.(?=\\s*([{CN}]|$))", r"\1。", text)

    # Repair OCR spaces inside compact organic-chemistry bond labels without touching molecular formulas.
    text = re.sub(
        r"\b([CHONSP])\s+([CHONSP])\s+([CHONSP])(?=\s*键角)",
        r"\1-\2-\3",
        text,
    )
    text = re.sub(
        r"\b(C|N|O|S|P|H)\s+(H|C|N|O|S|Cl|Br|I|F)(?=\s*(?:键|键能|键长|键角|伸缩|弯曲|吸收|断裂))",
        r"\1-\2",
        text,
    )
    text = re.sub(r"(?<=[（(])\b(C|N|O|S|P|H)\s+(H|C|N|O|S|Cl|Br|I|F)(?=[）)])", r"\1-\2", text)
    text = re.sub(r"\bC\s+(F|Cl|Br|I)(?=\s*(?:[、，,<>]|键|键能|键长|断裂))", r"C-\1", text)

    # Remove punctuation spacing introduced before conversion.
    text = re.sub(r"\s+([，。；：！？、])", r"\1", text)
    text = re.sub(r"([，。；：！？、])\s+", r"\1", text)

    # Normalize alphanumeric chemical hyphen spacing without touching minus signs in prose.
    text = re.sub(r"(?<=[A-Za-z0-9])\s*-\s*(?=[A-Za-z0-9])", "-", text)
    text = re.sub(r"(?<=[" + CN + r"])\s*-\s*(?=[" + CN + r"])", "-", text)

    # Attach common compact notations to Chinese units/words.
    text = re.sub(r"\b([A-Z]{1,6}\d*|pH|sp[23]|Ig[A-Z]?|DNA|RNA|mRNA|tRNA|rRNA)\s+(?=[" + CN + r"])", r"\1", text)
    text = normalize_numeric_spacing(text)

    # Clean duplicated punctuation and final whitespace.
    text = re.sub(r"([，。；：！？、])\1+", r"\1", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def normalize_numeric_spacing(text):
    compact_units = (
        "个|块|根|条|支|对|层|种|类|型|部|面|端|侧|章|节|页|例|岁|年|月|日|次|"
        "处|孔|束|段|区|份|期|周|天|小时|分钟|秒|倍|度|号|卷|篇|列|排|行|组|"
        "颈椎|胸椎|腰椎|骶椎|尾椎|椎|肋骨|肋|mm|cm|mL|mol|pm|nm|kJ|°C|°|%"
    )
    text = re.sub(r"(第|图|表|式)\s+(\d)", r"\1\2", text)
    text = re.sub(f"([{CN}])\\s+(?=\\d+(?:{compact_units}))", r"\1", text)
    text = re.sub(r"(\d)\s+(?=(?:" + compact_units + r"))", r"\1", text)
    text = re.sub(r"(?<=\d)\s+(?=至|到|~|～)", "", text)
    text = re.sub(r"(?<=[至到~～])\s+(?=第?\d)", "", text)
    text = re.sub(r"(\d)\s+\.\s+(?=[A-Za-z])", r"\1. ", text)
    return text


def normalize_organic_ocr_tokens(text):
    text = re.sub(r"亲\s*N\s*核", "亲核", text)
    text = re.sub(r"亲核性\s*N\s*N?\s*(?=越强|越弱|强|弱)", "亲核性", text)
    text = re.sub(r"反应速\s*N\s*率", "反应速率", text)
    text = re.sub(r"速\s*N\s*率", "速率", text)
    text = re.sub(r"离去倾\s*N\s*N?\s*向", "离去倾向", text)
    text = re.sub(r"\bS\s*N\s*([12])\b", r"SN\1", text)
    text = re.sub(r"\bS\s+([12])\s*(?=机制|反应|速率|中|和|、|的)", r"SN\1", text)
    return text


def normalize_non_cn_text(value):
    text = CONTROL_RE.sub("", value).replace("\u3000", " ")
    text = re.sub(r"[ \t\r\n]+", " ", text)
    text = re.sub(r"(?<=[A-Za-z0-9])\s*-\s*(?=[A-Za-z0-9])", "-", text)
    return text.strip()


def repair_split_english_terms(text):
    def repl_single(match):
        combined = (match.group(1) + match.group(2)).lower()
        if combined in KNOWN_JOIN_WORDS:
            return match.group(1) + match.group(2)
        return match.group(0)

    def repl_multi(match):
        combined = (match.group(1) + match.group(2)).lower()
        if combined in KNOWN_JOIN_WORDS:
            return match.group(1) + match.group(2)
        return match.group(0)

    text = re.sub(r"\b([a-z])\s+([a-z]{3,})\b", repl_single, text)
    text = re.sub(r"\b([a-z]{2,6})\s+([a-z]{2,10})\b", repl_multi, text)
    return text


def add_heading_readability(text):
    text = re.sub(r"^(\d+)(本章数字资源)", r"\1 \2 ", text)
    text = re.sub(r"^(\d+)(第[一二三四五六七八九十百0-9]+章)", r"\1 \2", text)
    text = re.sub(r"(\s)(\d+)(第[一二三四五六七八九十百0-9]+章)", r"\1\2 \3", text)
    text = re.sub(r"(本章数字资源)(绪论|第[一二三四五六七八九十百0-9]+章)", r"\1 \2", text)
    text = re.sub(r"(本章思维导图)(第[一二三四五六七八九十百0-9]+章)", r"\1 \2", text)
    text = re.sub(r"(绪论|第[一二三四五六七八九十百0-9]+章)([一二三四五六七八九十]+、)", r"\1 \2", text)
    text = re.sub(r"(第[一二三四五六七八九十百0-9]+章)([" + CN + r"])", r"\1 \2", text)
    return text


def normalize_parentheses(text):
    text = re.sub(r"([：；])([1-9])(?=[" + CN + r"])", r"\1（\2）", text)
    text = re.sub(r"\(\s*([一二三四五六七八九十百0-9]+)\s*\)", r"（\1）", text)
    text = re.sub(r"\((?=（[一二三四五六七八九十百0-9]+）)", "", text)
    text = re.sub(r"([：；？！])\s*\(?（", r"\1（", text)
    text = re.sub(r"(?<![A-Za-z0-9（])([1-9])\s*\)\s*(?=[" + CN + r"])", r"（\1）", text)
    text = re.sub(r"\(\s*(图\s*[^)]*?)\s*\)", r"（\1）", text)
    text = re.sub(r"\(\s*(如[^)]*?)\s*\)", r"（\1）", text)
    text = re.sub(r"\(\s*([^)]*[" + CN + r"][^)]{0,80})\s*\)", r"（\1）", text)
    text = re.sub(r"(?<=[" + CN + r"]) +（", "（", text)
    text = re.sub(r" +）", "）", text)
    text = re.sub(r"） +(?=[" + CN + r"])", "）", text)
    text = re.sub(r"） *, *(?=[" + CN + r"])", "），", text)
    text = re.sub(r"） *: *(?=[" + CN + r"])", "）：", text)
    return text


def clean_string_holder(holder, key, report, label):
    before = holder.get(key)
    after = before
    for _ in range(4):
        cleaned = clean_text(after)
        if cleaned == after:
            break
        after = cleaned
    if isinstance(after, str) and has_cn(after):
        after = add_heading_readability(normalize_parentheses(after))
    if before != after:
        holder[key] = after
        record_change(report, label, key, before, after)


def record_change(report, label, key, before, after):
    report["changedFields"] += 1
    report["byField"][key] += 1
    if len(report["examples"]) < 80:
        report["examples"].append(
            {
                "label": label,
                "field": key,
                "before": before[:180],
                "after": after[:180],
            }
        )


def clean_term(course_id, term, report):
    label = f"{course_id}:{term.get('id')}:{term.get('zh')}"
    for field in TEXT_FIELDS:
        if field in term:
            clean_string_holder(term, field, report, label)

    for index, context in enumerate(term.get("contexts") or []):
        if "text" in context:
            clean_string_holder(context, "text", report, f"{label}:context[{index}]")

    gray = term.get("gray") or {}
    for field in GRAY_TEXT_FIELDS:
        if field in gray:
            clean_string_holder(gray, field, report, f"{label}:gray")

    book = gray.get("book") or {}
    for field in GRAY_BOOK_TEXT_FIELDS:
        if field in book:
            clean_string_holder(book, field, report, f"{label}:gray.book")
    for index, hit in enumerate(book.get("hits") or []):
        for field in GRAY_HIT_TEXT_FIELDS:
            if field in hit:
                clean_string_holder(hit, field, report, f"{label}:gray.hit[{index}]")


def clean_figures(course_id, figures, report):
    for index, figure in enumerate(figures or []):
        label = f"{course_id}:figure[{index}]:{figure.get('label') or figure.get('id') or index}"
        for field in FIGURE_TEXT_FIELDS:
            if field in figure:
                clean_string_holder(figure, field, report, label)


def parse_topics():
    text = TOPICS_JS.read_text(encoding="utf-8")
    prefix = "window.MED_GLOSSARY_TOPICS = "
    if not text.startswith(prefix):
        return []
    body = text[len(prefix) :].strip()
    if body.endswith(";"):
        body = body[:-1]
    return json.loads(body)


def write_topics(topics):
    TOPICS_JS.write_text(
        "window.MED_GLOSSARY_TOPICS = " + json.dumps(topics, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def clean_topics(report):
    topics = parse_topics()
    for topic in topics:
        label = f"topic:{topic.get('id')}"
        for field in ("title", "summary"):
            if field in topic:
                clean_string_holder(topic, field, report, label)
        if isinstance(topic.get("tags"), list):
            for index, tag in enumerate(topic["tags"]):
                after = clean_text(tag)
                if tag != after:
                    topic["tags"][index] = after
                    record_change(report, label, f"tags[{index}]", tag, after)
    write_topics(topics)


def write_split_files(data):
    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for course in data["courses"]:
        summary = {key: value for key, value in course.items() if key not in {"terms", "figures"}}
        summary["dataPath"] = f"data/courses/{course['id']}.js"
        summary["termCount"] = len(course.get("terms", []))
        summary["figureCount"] = len(course.get("figures", []))
        summaries.append(summary)
        (COURSES_DIR / f"{course['id']}.js").write_text(
            "window.MED_GLOSSARY_COURSES = window.MED_GLOSSARY_COURSES || {};\n"
            + f"window.MED_GLOSSARY_COURSES[{json.dumps(course['id'], ensure_ascii=False)}] = "
            + json.dumps(course, ensure_ascii=False, indent=2)
            + ";\n",
            encoding="utf-8",
        )

    index_payload = {
        "schemaVersion": data.get("schemaVersion", 2),
        "meta": {**data.get("meta", {}), "dataVersion": DATA_VERSION, "splitCourses": True},
        "courses": summaries,
    }
    (DATA_DIR / "index.js").write_text(
        "window.MED_GLOSSARY_INDEX = " + json.dumps(index_payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def build_known_join_words(data):
    words = {
        "ethmoidal",
        "sphenoidal",
        "cerebellar",
        "thyrohyoid",
        "metathalamus",
        "subthalamus",
        "extension",
        "joint",
        "oropharynx",
        "central",
        "basal",
        "frontal",
        "epithalamus",
        "circumduction",
        "sacroiliac",
        "brachialis",
        "gluteus",
        "obturator",
        "visual",
        "auditory",
        "vestibular",
        "lacrimal",
        "ophthalmic",
        "lingual",
        "auricular",
    }
    for course in data.get("courses", []):
        for term in course.get("terms", []):
            for value in [term.get("en"), term.get("definition"), term.get("structure"), term.get("function")]:
                if not isinstance(value, str):
                    continue
                for word in re.findall(r"[A-Za-z]{4,}", value):
                    words.add(word.lower())
    return words


def count_remaining_patterns(data):
    patterns = {
        "zh_space_zh": re.compile(f"[{CN}]\\s+[{CN}]"),
        "zh_space_punct": re.compile(f"[{CN}]\\s+[，。；：！？、,. ;:!?]"),
        "punct_space_zh": re.compile(f"[，。；：！？、,. ;!?]\\s+[{CN}]"),
        "ascii_punct_cn": re.compile(f"[{CN}][,.;:!?][{CN}]"),
        "control": CONTROL_RE,
    }
    counts = Counter()

    def visit(value):
        if not isinstance(value, str):
            return
        for key, pattern in patterns.items():
            if pattern.search(value):
                counts[key] += 1

    for course in data["courses"]:
        for figure in course.get("figures") or []:
            for field in FIGURE_TEXT_FIELDS:
                visit(figure.get(field))
        for term in course.get("terms", []):
            for field in TEXT_FIELDS:
                visit(term.get(field))
            for context in term.get("contexts") or []:
                visit(context.get("text"))
            gray = term.get("gray") or {}
            visit(gray.get("zh"))
            book = gray.get("book") or {}
            visit(book.get("zh"))
            for hit in book.get("hits") or []:
                for field in GRAY_HIT_TEXT_FIELDS:
                    visit(hit.get(field))
    return counts


def main():
    data = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    global KNOWN_JOIN_WORDS
    KNOWN_JOIN_WORDS = build_known_join_words(data)
    report = {
        "generatedAt": "2026-07-07",
        "dataVersion": DATA_VERSION,
        "changedFields": 0,
        "byField": Counter(),
        "examples": [],
    }

    for course in data.get("courses", []):
        for term in course.get("terms", []):
            clean_term(course["id"], term, report)
        clean_figures(course["id"], course.get("figures"), report)

    clean_topics(report)
    data.setdefault("meta", {})["textCleanupGeneratedAt"] = "2026-07-07"
    data["meta"]["textCleanupVersion"] = DATA_VERSION
    data["meta"]["textCleanupRules"] = [
        "remove OCR spaces between Chinese characters",
        "normalize spaces around Chinese punctuation",
        "convert Chinese-prose halfwidth punctuation to fullwidth punctuation",
        "normalize biomedical abbreviation spacing such as X线, DNA分子, pH值",
        "preserve URLs, English source labels, and standalone English terms",
    ]
    remaining = count_remaining_patterns(data)
    report["byField"] = dict(report["byField"])
    report["remainingPatternCounts"] = dict(remaining)

    GLOSSARY_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_split_files(data)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "examples"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
