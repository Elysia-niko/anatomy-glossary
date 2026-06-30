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

GRAY_FLASH_NAME = "Grays Anatomy for Students Flash Cards"

PASSAGE_FACTS = {
    "opticcanal": {
        "zh": "视神经管主要通过视神经(CN II)和眼动脉，是颅腔与眶之间的重要通道。",
        "en": "The optic canal transmits the optic nerve (CN II) and ophthalmic artery between the cranial cavity and the orbit.",
    },
    "superiororbitalfissure": {
        "zh": "眶上裂通过动眼神经(CN III)、滑车神经(CN IV)、展神经(CN VI)、眼神经(CN V1)的分支以及眼静脉等结构。",
        "en": "The superior orbital fissure transmits CN III, CN IV, CN VI, branches of CN V1, and ophthalmic venous channels.",
    },
    "foramenrotundum": {
        "zh": "圆孔位于中颅窝底、蝶骨大翼相关区域，主要通过上颌神经(CN V2)，连接中颅窝与翼腭窝。",
        "en": "The foramen rotundum is in the floor of the middle cranial fossa and transmits the maxillary nerve (CN V2) to the pterygopalatine fossa.",
    },
    "foramenovale": {
        "zh": "卵圆孔主要通过下颌神经(CN V3)，并可通过副脑膜动脉、导静脉和小岩神经等结构。",
        "en": "The foramen ovale transmits the mandibular nerve (CN V3) and may also transmit the accessory meningeal artery, an emissary vein, and the lesser petrosal nerve.",
    },
    "foramenspinosum": {
        "zh": "棘孔通过脑膜中动脉、脑膜中静脉及下颌神经的脑膜支，是颅底骨折和硬膜外血肿复习时很重要的定位点。",
        "en": "The foramen spinosum transmits the middle meningeal artery and vein and the meningeal branch of CN V3.",
    },
    "foramenlacerum": {
        "zh": "破裂孔活体多由软骨填充；岩大神经和岩深神经在其上方区域汇合，颈内动脉经过其上方而非真正穿过软骨性孔腔。",
        "en": "The foramen lacerum is largely filled by cartilage in life; petrosal nerves cross its region, while the internal carotid artery passes superior to it rather than through the cartilage-filled opening.",
    },
    "carotidcanal": {
        "zh": "颈动脉管通过颈内动脉和颈内动脉交感神经丛，进入颅底后与海绵窦区域关系密切。",
        "en": "The carotid canal transmits the internal carotid artery and the internal carotid sympathetic plexus.",
    },
    "jugularforamen": {
        "zh": "颈静脉孔通过舌咽神经(CN IX)、迷走神经(CN X)、副神经(CN XI)，并通过乙状窦延续为颈内静脉及岩下窦等静脉结构。",
        "en": "The jugular foramen transmits CN IX, CN X, CN XI, the sigmoid sinus continuing as the internal jugular vein, and the inferior petrosal sinus.",
    },
    "hypoglossalcanal": {
        "zh": "舌下神经管主要通过舌下神经(CN XII)，并伴有小静脉丛等结构。",
        "en": "The hypoglossal canal transmits the hypoglossal nerve (CN XII), with small accompanying venous channels.",
    },
    "internalacousticmeatus": {
        "zh": "内耳门通过面神经(CN VII)、前庭蜗神经(CN VIII)和迷路动脉，是桥小脑角和内耳通路复习的关键结构。",
        "en": "The internal acoustic meatus transmits CN VII, CN VIII, and the labyrinthine artery.",
    },
    "stylomastoidforamen": {
        "zh": "茎乳孔是面神经(CN VII)离开颅骨的出口，常伴茎乳动脉。",
        "en": "The stylomastoid foramen is the exit for the facial nerve (CN VII), often accompanied by the stylomastoid artery.",
    },
    "cribriformplate": {
        "zh": "筛板的小孔通过嗅神经纤维，连接鼻腔嗅区与颅前窝的嗅球区域。",
        "en": "Foramina in the cribriform plate transmit olfactory nerve filaments from the nasal cavity to the olfactory bulb.",
    },
    "mandibularforamen": {
        "zh": "下颌孔通过下牙槽神经、动脉和静脉，进入下颌管供应下颌牙及相关组织。",
        "en": "The mandibular foramen transmits the inferior alveolar nerve and vessels into the mandibular canal.",
    },
    "infraorbitalforamen": {
        "zh": "眶下孔通过眶下神经和血管，是上颌区感觉分布和局麻定位的重要标志。",
        "en": "The infra-orbital foramen transmits the infra-orbital nerve and vessels.",
    },
    "mentalforamen": {
        "zh": "颏孔通过颏神经和血管，供应下唇、颏部皮肤和相关黏膜。",
        "en": "The mental foramen transmits the mental nerve and vessels to the chin and lower lip region.",
    },
    "greaterpalatineforamen": {
        "zh": "腭大孔通过腭大神经和血管，进入硬腭后外侧部。",
        "en": "The greater palatine foramen transmits the greater palatine nerve and vessels to the hard palate.",
    },
    "lesserpalatineforamen": {
        "zh": "腭小孔通过腭小神经和血管，主要到软腭区域。",
        "en": "The lesser palatine foramina transmit lesser palatine nerves and vessels toward the soft palate.",
    },
    "openingofpterygoidcanal": {
        "zh": "翼管开口与翼管神经和翼管动脉相关，连接颅底破裂孔区域与翼腭窝。",
        "en": "The opening of the pterygoid canal is related to the nerve and artery of the pterygoid canal.",
    },
}


TITLE_REPLACEMENTS = {
    "M USCLES : A V IEW": "Muscles: anterior view",
    "M USCLES : P V IEW": "Muscles: posterior view",
    "S KELETON : A V IEW": "Skeleton: anterior view",
    "S KELETON : P V IEW": "Skeleton: posterior view",
    "V S YSTEM : A RTERIES": "Vascular system: arteries",
    "S KULL : L VIEW": "Skull: lateral view",
    "S KULL : I VIEW": "Skull: inferior view",
    "S KULL : A V IEW": "Skull: anterior view",
    "S KULL : A C F OSSA": "Skull: anterior cranial fossa",
    "S KULL : M C F OSSA": "Skull: middle cranial fossa",
    "S KULL : P C F OSSA": "Skull: posterior cranial fossa",
    "C S INUS": "Cavernous sinus",
    "CRANIAL NERVES: FLOOR OF CRANIAL CA VITY": "Cranial nerves: floor of cranial cavity",
    "O RBIT : B ONES": "Orbit: bones",
    "O RBIT : S N ERVES": "Orbit: sensory nerves",
    "P F OSSA": "Pterygopalatine fossa",
    "P F OSSA : G ATEW A YS": "Pterygopalatine fossa: gateways",
    "P F OSSA : N ERVES": "Pterygopalatine fossa: nerves",
    "N C A VITY : L W ALL , B ONES": "Nasal cavity: lateral wall, bones",
    "NASAL CA VITY : LATERAL W ALL, MUCOSA, AND OPENINGS": "Nasal cavity: lateral wall, mucosa, and openings",
}


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\ufeff", " ").replace("\u200b", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def norm_key(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = value.replace("[", " ").replace("]", " ")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def pretty_title(raw: str) -> str:
    raw = clean_text(raw)
    raw = re.sub(r"^Copyright 2015, Elsevier Inc\. All rights reserved\.\s*", "", raw)
    raw = re.sub(r"\s*\d+\.\s.*$", "", raw)
    raw = re.sub(r"\s*Figure from.*$", "", raw)
    raw = raw.replace("﻿", " ")
    raw = clean_text(raw)
    for bad, good in TITLE_REPLACEMENTS.items():
        if norm_key(raw) == norm_key(bad):
            return good
    return raw.title() if raw.isupper() else raw


def find_flash_pdf() -> Path:
    base = Path.home() / "Documents" / "xwechat_files"
    matches = sorted(base.rglob("*.pdf"), key=lambda path: path.stat().st_size, reverse=True)
    for path in matches:
        if GRAY_FLASH_NAME.lower() in path.name.lower():
            return path
    raise FileNotFoundError("Gray's Flash Cards PDF was not found in xwechat_files.")


def parse_labels(text: str) -> list[dict[str, str]]:
    labels = []
    body = re.split(r"\bIN THE CLINIC\b|Figure from", text, maxsplit=1)[0]
    for match in re.finditer(r"(\d{1,2})\.\s*(.*?)(?=\s+\d{1,2}\.\s|$)", body):
        label = clean_text(match.group(2)).strip(" ;,.")
        if not label or len(label) > 120:
            continue
        labels.append({"number": match.group(1), "en": label})
    return labels


def parse_source(text: str) -> str:
    match = re.search(r"Figure from\s+(.*?p\.?\s*\d+)", text, re.IGNORECASE)
    if match:
        return clean_text(match.group(1))
    match = re.search(r"Figure from\s+(.*?)(?:IN THE CLINIC|Copyright|$)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return "Gray's Anatomy for Students Flash Cards"
    return clean_text(match.group(1))


def parse_clinic_keywords(text: str) -> list[str]:
    if "IN THE CLINIC" not in text:
        return []
    clinic = clean_text(text.split("IN THE CLINIC", 1)[1])
    keywords = []
    rules = [
        ("tumor", "tumor localization"),
        ("infection", "infection spread"),
        ("hemorrhage", "hemorrhage"),
        ("hematoma", "hematoma"),
        ("nerve", "nerve injury"),
        ("fracture", "fracture"),
        ("consciousness", "consciousness assessment"),
        ("neuralgia", "neuralgia"),
    ]
    lower = clinic.lower()
    for needle, label in rules:
        if needle in lower and label not in keywords:
            keywords.append(label)
    return keywords[:3]


def parse_flash_cards(pdf_path: Path) -> list[dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    cards = []
    for page_index, page in enumerate(reader.pages):
        text = clean_text(page.extract_text() or "")
        if "Figure from Gray" not in text and "Figure from" not in text:
            continue
        labels = parse_labels(text)
        if not labels:
            continue
        title = pretty_title(text)
        cards.append(
            {
                "answerPdfPage": page_index + 1,
                "imagePdfPage": max(1, page_index),
                "title": title,
                "source": parse_source(text),
                "labels": labels,
                "clinicKeywords": parse_clinic_keywords(text),
                "image": f"assets/pages/gray-flash/pdf-{page_index:03d}.jpg",
            }
        )
    return cards


def english_aliases(term: dict[str, Any]) -> list[str]:
    aliases = []
    for part in re.split(r"[,，;；/]", term.get("en", "")):
        part = clean_text(part)
        key = norm_key(part)
        if len(key) >= 4:
            aliases.append(part)
    full = clean_text(term.get("en", ""))
    if full and full not in aliases:
        aliases.append(full)
    return aliases


def build_translation_map(terms: list[dict[str, Any]]) -> dict[str, str]:
    mapping = {}
    for term in terms:
        for alias in english_aliases(term):
            key = norm_key(alias)
            if key and key not in mapping:
                mapping[key] = term.get("zh", "")
    return mapping


def card_matches(term: dict[str, Any], card: dict[str, Any]) -> list[dict[str, str]]:
    aliases = [(alias, norm_key(alias)) for alias in english_aliases(term)]
    aliases = [(alias, key) for alias, key in aliases if key and key not in {"artery", "vein", "nerve", "bone", "muscle"}]
    matched = []
    for label in card["labels"]:
        label_key = norm_key(label["en"])
        for alias, alias_key in aliases:
            if not alias_key:
                continue
            exact = label_key == alias_key
            contained = False
            if alias_key in label_key or label_key in alias_key:
                shorter_text = alias if len(alias_key) <= len(label_key) else label["en"]
                shorter_key = alias_key if len(alias_key) <= len(label_key) else label_key
                shorter_words = re.findall(r"[a-z0-9]+", clean_text(shorter_text).lower())
                contained = len(shorter_key) >= 10 and len(shorter_words) >= 2
            if exact or contained:
                matched.append(label)
                break
    return matched


def related_labels(card: dict[str, Any], translation: dict[str, str], matched: list[dict[str, str]]) -> list[dict[str, str]]:
    matched_numbers = {item["number"] for item in matched}
    related = []
    for label in card["labels"]:
        key = norm_key(label["en"])
        zh = translation.get(key, "")
        if not zh and label["number"] not in matched_numbers:
            continue
        related.append({"number": label["number"], "en": label["en"], "zh": zh})
        if len(related) >= 10:
            break
    return related


def build_gray_supplement(term: dict[str, Any], cards: list[dict[str, Any]], translation: dict[str, str]) -> dict[str, Any] | None:
    aliases = [norm_key(alias) for alias in english_aliases(term)]
    fact = next((PASSAGE_FACTS[key] for key in aliases if key in PASSAGE_FACTS), None)
    matched_cards = []
    for card in cards:
        matched = card_matches(term, card)
        if not matched:
            continue
        matched_cards.append(
            {
                "title": card["title"],
                "source": card["source"],
                "answerPdfPage": card["answerPdfPage"],
                "imagePdfPage": card["imagePdfPage"],
                "image": card["image"],
                "matchedLabels": [
                    {
                        "number": item["number"],
                        "en": item["en"],
                        "zh": translation.get(norm_key(item["en"]), term.get("zh", "")),
                    }
                    for item in matched[:4]
                ],
                "relatedLabels": related_labels(card, translation, matched),
                "clinicKeywords": card["clinicKeywords"],
            }
        )
        if len(matched_cards) >= 3:
            break

    if not fact and not matched_cards:
        return None

    zh_bits = []
    en_bits = []
    if fact:
        zh_bits.append(fact["zh"])
        en_bits.append(fact["en"])
    if matched_cards:
        card = matched_cards[0]
        related_zh = [item["zh"] or item["en"] for item in card["relatedLabels"] if item["number"] not in {m["number"] for m in card["matchedLabels"]}]
        related_en = [item["en"] for item in card["relatedLabels"] if item["number"] not in {m["number"] for m in card["matchedLabels"]}]
        zh_bits.append(
            f"Gray's Flash Cards 在“{card['title']}”图中标出{term.get('zh', '')}；同图可对照"
            + ("、".join(related_zh[:6]) if related_zh else "周围结构")
            + "。"
        )
        en_bits.append(
            f"Gray's Flash Cards identifies {term.get('en', '')} in the “{card['title']}” figure; compare it with "
            + (", ".join(related_en[:6]) if related_en else "nearby labeled structures")
            + "."
        )

    return {
        "zh": "".join(zh_bits),
        "en": " ".join(en_bits),
        "cards": matched_cards,
    }


def write_outputs(payload: dict[str, Any], out_dir: Path) -> None:
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    data_dir = out_dir / "data"
    (data_dir / "glossary.json").write_text(json_text, encoding="utf-8")
    (data_dir / "glossary.js").write_text(
        "window.MED_GLOSSARY = " + json_text + ";\nwindow.ANATOMY_GLOSSARY = window.MED_GLOSSARY;\n",
        encoding="utf-8",
    )

    report_path = data_dir / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["grayGeneratedAt"] = payload["meta"].get("grayGeneratedAt")
        report["graySupplementTerms"] = payload["meta"].get("graySupplementTerms")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add Gray's Flash Cards supplements to systematic anatomy terms.")
    parser.add_argument("--out", type=Path, default=ROOT)
    parser.add_argument("--flash-pdf", type=Path, default=None)
    args = parser.parse_args()

    payload_path = args.out / "data" / "glossary.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    anatomy = next(course for course in payload["courses"] if course["id"] == "systematic-anatomy")
    cards = parse_flash_cards(args.flash_pdf or find_flash_pdf())
    translation = build_translation_map(anatomy["terms"])

    count = 0
    card_links = 0
    for term in anatomy["terms"]:
        supplement = build_gray_supplement(term, cards, translation)
        if supplement:
            term["gray"] = supplement
            count += 1
            card_links += len(supplement.get("cards", []))
        else:
            term.pop("gray", None)

    payload["meta"]["grayGeneratedAt"] = datetime.now().isoformat(timespec="seconds")
    payload["meta"]["graySupplementTerms"] = count
    payload["meta"]["grayCardLinks"] = card_links
    write_outputs(payload, args.out)
    print(json.dumps({"cards": len(cards), "graySupplementTerms": count, "grayCardLinks": card_links}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
