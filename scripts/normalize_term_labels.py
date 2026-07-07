import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
COURSES_DIR = DATA_DIR / "courses"
GLOSSARY_JSON = DATA_DIR / "glossary.json"
TOPICS_JS = DATA_DIR / "topics.js"
REPORT_JSON = DATA_DIR / "term_label_cleanup_report.json"
DATA_VERSION = "termformat-20260707"

CN = r"\u3400-\u4dbf\u4e00-\u9fff"
CN_RE = re.compile(f"[{CN}]")
TEXT_FIELDS = ("definition", "structure", "location", "function", "studyNote", "mnemonic")
GRAY_TEXT_FIELDS = ("zh",)
GRAY_BOOK_TEXT_FIELDS = ("zh",)
GRAY_HIT_TEXT_FIELDS = ("matched", "snippet", "line")


def has_cn(value):
    return isinstance(value, str) and bool(CN_RE.search(value))


def english_pattern(value):
    escaped = re.escape(value.strip())
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)
    escaped = escaped.replace(r"\-", r"\s*-\s*")
    return escaped


def build_term_pairs(data):
    pairs = []
    seen = set()
    for course in data.get("courses", []):
        for term in course.get("terms", []):
            zh = (term.get("zh") or "").strip()
            en = (term.get("en") or "").strip()
            if not zh or not en or not has_cn(zh) or not re.search(r"[A-Za-z]", en):
                continue
            key = (zh, en.lower())
            if key in seen:
                continue
            seen.add(key)
            direct_pattern = re.compile(rf"{re.escape(zh)}(?!\s*[（(])\s*{english_pattern(en)}", re.IGNORECASE)
            bracket_pattern = re.compile(rf"{re.escape(zh)}\s*\(\s*{english_pattern(en)}\s*\)", re.IGNORECASE)
            pairs.append((zh, en, direct_pattern, bracket_pattern))
    pairs.sort(key=lambda item: (len(item[0]), len(item[1])), reverse=True)
    return pairs


def wrap_known_english_labels(text, pairs):
    if not has_cn(text):
        return text
    for zh, en, direct_pattern, bracket_pattern in pairs:
        text = bracket_pattern.sub(f"{zh}（{en}）", text)
        text = direct_pattern.sub(f"{zh}（{en}）", text)
    return text


def strip_number_noise(text, term_zh=""):
    if not isinstance(text, str) or not text:
        return text
    value = text.strip()
    term_zh = (term_zh or "").strip()

    value = re.sub(r"第(\d)\s+(\d)(?=章)", r"第\1\2", value)

    # Remove exercise prompts that OCR pulled into explanatory contexts.
    value = re.sub(
        r"\b\d+-\d+\s*(?:试解释|根据|分析|判断|写出|指出|按|将|用).*?(?=（[一二三四五六七八九十]+）|第[一二三四五六七八九十]+节|$)",
        "",
        value,
    ).strip()
    value = re.sub(r"（[一二三四五六七八九十]+）[" + CN + r"]{0,12}$", "", value).strip()

    # Remove leading page/order numbers and common textbook heading debris.
    for _ in range(4):
        before = value
        value = re.sub(r"^\d+\s+(?=(?:本章|绪论|第[一二三四五六七八九十0-9]+章|[一二三四五六七八九十]+、|（\d+）))", "", value)
        value = re.sub(r"^\d+\s+\d+\s*\)\s*", "", value)
        value = re.sub(r"^(?:\d+\s+){2,}(?=[" + CN + r"（(])", "", value)
        value = re.sub(r"^\d+\s+(?=“)", "", value)
        value = re.sub(r"^\d+\s+(?!世纪)(?=[" + CN + r"（(图第])", "", value)
        value = re.sub(r"^\d+\.\s*(?=[" + CN + r"])", "", value)
        value = re.sub(r"^本章数字资源\s*", "", value)
        value = re.sub(r"^本章思维导图\s*", "", value)
        value = re.sub(r"^(绪论)\s+\d+\s*", r"\1 ", value)
        value = re.sub(r"^(第[一二三四五六七八九十0-9]+章\s+)([" + CN + r"]{2,20})\2", r"\2", value)
        if term_zh:
            term = re.escape(term_zh)
            value = re.sub(rf"^(?:绪论|第[一二三四五六七八九十0-9]+章[^，。；：]{{0,40}})?\s*[一二三四五六七八九十]+、[^，。；：]{{0,60}}?({term})(?=\s*[（(A-Za-z]|是|由|为|包括)", r"\1", value)
            value = re.sub(rf"^第[一二三四五六七八九十0-9]+章[^，。；：]{{0,60}}?({term})(?=\s*[（(A-Za-z]|是|由|为|包括)", r"\1", value)
        value = value.strip()
        if value == before:
            break
    return value


def clean_value(value, pairs, term_zh=""):
    if not isinstance(value, str):
        return value
    cleaned = strip_number_noise(value, term_zh)
    cleaned = wrap_known_english_labels(cleaned, pairs)
    cleaned = re.sub(r"）\s+(?=[" + CN + r"])", "）", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def clean_holder(holder, key, pairs, report, label, term_zh=""):
    before = holder.get(key)
    after = clean_value(before, pairs, term_zh)
    if before != after:
        holder[key] = after
        report["changedFields"] += 1
        report["byField"][key] += 1
        if len(report["examples"]) < 100:
            report["examples"].append(
                {
                    "label": label,
                    "field": key,
                    "before": str(before)[:200],
                    "after": str(after)[:200],
                }
            )


def clean_term(course_id, term, pairs, report):
    label = f"{course_id}:{term.get('id')}:{term.get('zh')}"
    term_zh = term.get("zh") or ""
    for field in TEXT_FIELDS:
        if field in term:
            clean_holder(term, field, pairs, report, label, term_zh)
    for index, context in enumerate(term.get("contexts") or []):
        clean_holder(context, "text", pairs, report, f"{label}:context[{index}]", term_zh)
    gray = term.get("gray") or {}
    for field in GRAY_TEXT_FIELDS:
        if field in gray:
            clean_holder(gray, field, pairs, report, f"{label}:gray", term_zh)
    book = gray.get("book") or {}
    for field in GRAY_BOOK_TEXT_FIELDS:
        if field in book:
            clean_holder(book, field, pairs, report, f"{label}:gray.book", term_zh)
    for index, hit in enumerate(book.get("hits") or []):
        for field in GRAY_HIT_TEXT_FIELDS:
            if field in hit:
                clean_holder(hit, field, pairs, report, f"{label}:gray.hit[{index}]", term_zh)


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


def count_remaining(data):
    counts = Counter()
    leading_number = re.compile(r"^\s*(?:\d+\s+|\d+\.\s*)")
    exercise = re.compile(r"\b\d+-\d+\s*(?:试解释|根据|分析|判断|写出|指出|按|将|用)")
    unwrapped = 0
    pairs = build_term_pairs(data)

    def visit(value):
        nonlocal unwrapped
        if not isinstance(value, str):
            return
        if leading_number.search(value):
            counts["leadingNumber"] += 1
        if exercise.search(value):
            counts["exercisePrompt"] += 1
        if has_cn(value):
            for _, _, direct_pattern, _ in pairs:
                if direct_pattern.search(value):
                    unwrapped += 1
                    break

    for course in data.get("courses", []):
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
    counts["unwrappedKnownZhEn"] = unwrapped
    return counts


def main():
    data = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    pairs = build_term_pairs(data)
    report = {
        "generatedAt": "2026-07-07",
        "dataVersion": DATA_VERSION,
        "termPairs": len(pairs),
        "changedFields": 0,
        "byField": Counter(),
        "examples": [],
    }
    for course in data.get("courses", []):
        for term in course.get("terms", []):
            clean_term(course["id"], term, pairs, report)
    data.setdefault("meta", {})["termLabelCleanupGeneratedAt"] = "2026-07-07"
    data["meta"]["termLabelCleanupVersion"] = DATA_VERSION
    data["meta"]["termLabelCleanupRules"] = [
        "wrap known Chinese term + English term pairs as Chinese（English）",
        "strip leading OCR page/order numbers from term explanations",
        "remove exercise prompt fragments pulled into contexts",
    ]
    report["byField"] = dict(report["byField"])
    report["remainingPatternCounts"] = dict(count_remaining(data))

    GLOSSARY_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_split_files(data)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "examples"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
