import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
GLOSSARY_JSON = DATA_DIR / "glossary.json"
TOPICS_JS = DATA_DIR / "topics.js"
COURSES_DIR = DATA_DIR / "courses"
DATA_VERSION = "sources-20260707"


OPENSTAX = "OpenStax Anatomy and Physiology 2e"

SOURCE_CATALOG = {
    "anatomy-general": {
        "label": f"{OPENSTAX}: Introduction",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction",
    },
    "bone": {
        "label": f"{OPENSTAX}: Axial and Appendicular Skeleton",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/7-introduction",
    },
    "joint": {
        "label": f"{OPENSTAX}: Joints",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/9-introduction",
    },
    "muscle": {
        "label": f"{OPENSTAX}: Muscular System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/11-introduction",
    },
    "nerve": {
        "label": f"{OPENSTAX}: Anatomy of the Nervous System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/13-introduction",
    },
    "vessel": {
        "label": f"{OPENSTAX}: Blood Vessels and Circulation",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/20-introduction",
    },
    "viscera": {
        "label": f"{OPENSTAX}: Visceral Systems",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/23-introduction",
    },
    "sense": {
        "label": f"{OPENSTAX}: Sensory and Motor Integration",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/16-introduction",
    },
    "epithelium": {
        "label": f"{OPENSTAX}: Epithelial Tissue",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-2-epithelial-tissue",
    },
    "connective": {
        "label": f"{OPENSTAX}: Connective Tissue",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-3-connective-tissue-supports-and-protects",
    },
    "histology-muscle": {
        "label": f"{OPENSTAX}: Muscle Tissue",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-4-muscle-tissue-and-motion",
    },
    "histology-nerve": {
        "label": f"{OPENSTAX}: Nervous Tissue",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/4-5-nervous-tissue-mediates-perception-and-response",
    },
    "blood": {
        "label": f"{OPENSTAX}: Blood",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/18-introduction",
    },
    "immune": {
        "label": f"{OPENSTAX}: Lymphatic and Immune System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/21-introduction",
    },
    "skin": {
        "label": f"{OPENSTAX}: Integumentary System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/5-introduction",
    },
    "endocrine": {
        "label": f"{OPENSTAX}: Endocrine System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/17-introduction",
    },
    "digestive": {
        "label": f"{OPENSTAX}: Digestive System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/23-introduction",
    },
    "respiratory": {
        "label": f"{OPENSTAX}: Respiratory System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/22-introduction",
    },
    "urinary": {
        "label": f"{OPENSTAX}: Urinary System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/25-introduction",
    },
    "reproductive": {
        "label": f"{OPENSTAX}: Reproductive System",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/27-introduction",
    },
    "development": {
        "label": f"{OPENSTAX}: Development and Inheritance",
        "url": "https://openstax.org/books/anatomy-and-physiology-2e/pages/28-introduction",
    },
    "embryology": {
        "label": "UNSW Embryology",
        "url": "https://embryology.med.unsw.edu.au/embryology/index.php/Main_Page",
    },
    "histology-guide": {
        "label": "Histology Guide",
        "url": "https://histologyguide.com/",
    },
}


ANATOMY_TEXT = {
    "direction": (
        "这是解剖学方位、平面或轴向术语，本身不是单一器官；使用时应以标准解剖学姿势为参照，说明结构之间的相对位置、方向或切面关系。",
        "意义在于统一解剖描述，避免因观察者方向不同而产生歧义；读图、定位和描述毗邻关系时都要先确定参照姿势。",
        "anatomy-general",
    ),
    "bone": (
        "属于骨或骨性标志相关词条；复习时应定位到所在骨、表面形态、关节面、肌腱或韧带附着点，以及可能通过的神经血管。",
        "主要意义在于构成支架、形成关节或作为肌腱韧带附着和体表定位标志；部分骨性孔裂还决定神经血管通行路线。",
        "bone",
    ),
    "joint": (
        "属于关节或韧带相关词条；应按参与骨面、关节囊、韧带加强部位、运动轴和邻近肌腱神经血管来定位。",
        "功能意义在于连接骨骼、限定并引导运动，同时维持稳定性；临床复习要联系扭伤、脱位和运动受限。",
        "joint",
    ),
    "muscle": (
        "属于肌或肌群相关词条；应按起点、止点、所在层次、跨越关节、血供和支配神经来组织结构分布。",
        "功能意义通常体现为收缩后产生的关节运动、姿势维持或腔壁活动；判断动作时要同时看起止点和跨越的关节。",
        "muscle",
    ),
    "nerve": (
        "属于神经系统相关词条；应按中枢或周围位置、起止、走行、分支、穿行孔管、支配区域和相邻血管结构定位。",
        "功能意义在于传导感觉、运动或自主神经信息；学习时要把支配范围和损伤后的感觉缺失、运动障碍或反射改变对应起来。",
        "nerve",
    ),
    "vessel": (
        "属于血管、淋巴管或循环相关词条；应按起源或汇入、走行、分支或属支、供血/回流区域及伴行神经结构定位。",
        "功能意义在于完成供血、静脉回流或淋巴回流；临床上常与压迫止血、侧支循环、栓塞和淋巴转移路径有关。",
        "vessel",
    ),
    "viscera": (
        "属于内脏器官或器官组成部分；应按所在腔隙、壁层或实质结构、毗邻关系、开口管道、血管神经和淋巴回流来定位。",
        "功能意义取决于所属系统，通常涉及消化、呼吸、泌尿、生殖、内分泌或屏障转运；复习时要把形态结构和生理作用对应。",
        "viscera",
    ),
    "passage": (
        "属于孔、裂、管、窝或腔隙类通道；应重点掌握边界、连通区域，以及通过其中的神经、血管、肌腱或管道。",
        "功能意义在于为重要结构提供通路，也是解剖定位和病变扩散路径判断的关键；复习时建议把“边界-连通-内容物”连成表。",
        "anatomy-general",
    ),
    "sense": (
        "属于感觉器或感觉传导相关结构；应按感受细胞、支持结构、附属器、传导通路和相关血管神经来定位。",
        "功能意义在于接受特定刺激并转化为神经信号；临床复习要联系视、听、平衡、嗅、味等检查和损伤定位。",
        "sense",
    ),
    "concept": (
        "这是解剖学概念、方法或章节性术语，不一定对应单一可解剖分离的结构；应放回所属系统和教材上下文中理解。",
        "意义在于帮助建立解剖学描述、观察或临床应用框架；复习时可把它作为连接具体结构的上位概念。",
        "anatomy-general",
    ),
}


HISTOLOGY_TEXT = {
    "基础概念": (
        "这是组织学基础层级概念；应放在“细胞—组织—器官—系统”的结构层次中理解，并结合所在章节判断它指向的组织组成或局部微环境。",
        "功能意义在于帮助建立组织学观察框架：从细胞和细胞外基质出发，理解组织如何组合成器官并支持相应生理功能。",
        "histology-guide",
    ),
    "技术": (
        "属于组织学观察或制备技术；结构分布重点不是单一组织位置，而是观察对象、染色或标记成分、显微层级和适用样本。",
        "功能意义在于帮助显示细胞、纤维、基质或分子标记，从而区分组织结构、发育阶段或病理改变。",
        "histology-guide",
    ),
    "上皮与腺": (
        "应按细胞层数、表层形态、极性、基膜、细胞连接及腺体导管/分泌部结构来整理，并联系分布部位。",
        "功能意义主要包括保护、吸收、分泌、转运和感觉；结构差异通常直接对应局部功能需求。",
        "epithelium",
    ),
    "结缔组织": (
        "应把细胞、纤维和基质分开记，再结合疏松、致密、脂肪等类型及其分布部位理解。",
        "功能意义在于支持、连接、营养、修复、防御和储能；不同纤维和基质比例决定力学性质。",
        "connective",
    ),
    "软骨和骨": (
        "应按细胞类型、基质成分、纤维类型、软骨膜或骨膜、骨单位和生长改建方式来定位。",
        "功能意义在于支持、保护、运动杠杆、造血微环境和矿物储存；软骨与骨的结构差异决定其力学和修复特点。",
        "bone",
    ),
    "血液与造血": (
        "应按血细胞类型、形态、比例、寿命、造血谱系和骨髓微环境来整理。",
        "功能意义包括运输、免疫防御、止血凝血和内环境维持；细胞形态常直接提示功能状态。",
        "blood",
    ),
    "肌组织": (
        "应比较骨骼肌、心肌和平滑肌的细胞形态、横纹、细胞连接、肌节或肌丝排列及支配方式。",
        "功能意义在于产生收缩、维持姿势、推动血液或管腔内容物；组织类型决定收缩速度、节律和可控性。",
        "histology-muscle",
    ),
    "神经组织与系统": (
        "应按神经元、神经胶质、神经纤维、突触、髓鞘和屏障结构来定位，并区分中枢与周围神经系统。",
        "功能意义在于接受、整合和传递信息；胶质细胞和屏障结构对支持、绝缘、免疫和内环境稳定同样关键。",
        "histology-nerve",
    ),
    "循环系统": (
        "应按管壁层次、内皮、平滑肌、弹性成分、瓣膜和血流压力关系来理解不同血管或心脏结构。",
        "功能意义在于运输血液、调节阻力与容量、交换物质并维持灌注；管壁结构反映其所承受的压力和流量。",
        "vessel",
    ),
    "免疫系统": (
        "应把淋巴细胞、抗原呈递细胞、网状组织和淋巴器官分区放在一起记，关注抗原进入和细胞迁移路径。",
        "功能意义在于免疫监视、抗原识别、免疫应答和淋巴细胞成熟；结构分区常对应不同免疫事件。",
        "immune",
    ),
    "皮肤": (
        "应按表皮分层、真皮乳头层/网织层、皮下组织和附属器来整理，并联系体表分布差异。",
        "功能意义包括屏障、感觉、体温调节、免疫防御和再生修复；角化程度和附属器分布决定区域特点。",
        "skin",
    ),
    "眼与耳": (
        "应按感受细胞、支持结构、透明介质、传导方向和附属保护结构来定位。",
        "功能意义在于视觉、听觉和平衡觉的感受与传导；结构层次常用于解释相应感觉障碍。",
        "sense",
    ),
    "内分泌系统": (
        "应按腺体位置、细胞类型、激素类别、血窦或滤泡结构及调节轴来整理。",
        "功能意义在于分泌激素并调节代谢、生长、生殖、应激和内环境稳态；细胞类型通常对应激素功能。",
        "endocrine",
    ),
    "消化系统": (
        "应按黏膜、黏膜下层、肌层和外膜/浆膜定位，再补充上皮、腺体和特殊细胞类型。",
        "功能意义包括摄取、消化、吸收、屏障和内分泌调节；各段管壁差异反映其主要任务。",
        "digestive",
    ),
    "呼吸系统": (
        "应沿导气部到呼吸部梳理上皮、腺体、软骨、平滑肌、肺泡细胞和气血屏障。",
        "功能意义在于通气、气体交换、过滤防御和表面活性物质维持肺泡稳定。",
        "respiratory",
    ),
    "泌尿系统": (
        "应以肾单位和集合管为主线，定位肾小体、肾小管各段、球旁复合体和尿路上皮。",
        "功能意义包括滤过、重吸收、分泌、浓缩尿液和内分泌调节；每段上皮结构对应不同转运任务。",
        "urinary",
    ),
    "生殖系统": (
        "应按生殖细胞发生、支持细胞、内分泌细胞、管道结构和周期性变化来整理。",
        "功能意义在于配子发生、激素分泌、受精准备和胚胎早期支持；结构变化常与周期或发育阶段相关。",
        "reproductive",
    ),
    "胚胎发生": (
        "应按时间顺序定位受精、卵裂、植入、胚层形成、胚体折叠、胎膜和胎盘等阶段。",
        "功能意义在于解释成熟组织器官来源、体腔和轴向建立，以及先天异常发生的时间窗。",
        "development",
    ),
    "器官发生": (
        "应追踪胚层来源、原基、管腔形成、分隔、旋转、迁移和重塑过程，并联系成熟器官形态。",
        "功能意义在于把成体解剖结构与发育来源相连，解释常见先天畸形和异常通道。",
        "embryology",
    ),
    "先天畸形": (
        "应把畸形放回相应发育步骤，判断异常发生的时期、受影响原基和最终形态改变。",
        "功能意义主要在临床解释和定位：同一畸形往往提示特定发育过程受阻或融合、迁移、闭合失败。",
        "embryology",
    ),
}

GENERATED_STRUCTURES = {item[0] for item in ANATOMY_TEXT.values()} | {item[0] for item in HISTOLOGY_TEXT.values()}
GENERATED_FUNCTIONS = {item[1] for item in ANATOMY_TEXT.values()} | {item[1] for item in HISTOLOGY_TEXT.values()}


MNEMONICS = {
    "systematic-anatomy": {
        "腕骨": {
            "text": "腕骨由桡侧到尺侧记：近排“舟月三角豆”，远排“大小头状钩”。即舟骨、月骨、三角骨、豌豆骨；大多角骨、小多角骨、头状骨、钩骨。",
            "source": "腕骨顺序记忆口诀",
        },
        "脑神经": {
            "text": "十二对脑神经顺序口诀：一嗅二视三动眼，四滑五叉六外展，七面八听九舌咽，迷副舌下十二全。",
            "source": "脑神经顺序记忆口诀",
        },
    }
}


WIKI_SKIP = {
    "superior",
    "inferior",
    "anterior",
    "posterior",
    "internal",
    "external",
    "deep",
    "superficial",
    "other",
    "organ",
}


def clean_title(value):
    text = re.sub(r"\([^)]*\)", " ", value or "")
    text = re.sub(r"[^A-Za-z0-9 ,/\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_wikipedia_links(terms):
    candidates = {}
    for term in terms:
        title = clean_title(term.get("en", ""))
        if not title or len(title) < 4 or title.lower() in WIKI_SKIP:
            continue
        candidates.setdefault(title, []).append(term["id"])

    links = {}
    titles = list(candidates)
    for index in range(0, len(titles), 45):
        batch = titles[index : index + 45]
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "redirects": "1",
                "prop": "info|pageprops",
                "inprop": "url",
                "titles": "|".join(batch),
            }
        )
        req = urllib.request.Request(
            "https://en.wikipedia.org/w/api.php?" + params,
            headers={"User-Agent": "ElysiaMedicalGlossary/1.0 (personal study site)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            continue

        normalized = {item["to"]: item["from"] for item in payload.get("query", {}).get("normalized", [])}
        redirects = {item["to"]: item["from"] for item in payload.get("query", {}).get("redirects", [])}
        for page in payload.get("query", {}).get("pages", {}).values():
            if "missing" in page or "disambiguation" in page.get("pageprops", {}):
                continue
            url = page.get("fullurl")
            if not url:
                continue
            final_title = page.get("title", "")
            original = redirects.get(final_title) or normalized.get(final_title) or final_title
            for term_id in candidates.get(original, []):
                links[term_id] = {"label": f"Wikipedia: {final_title}", "url": url}
        time.sleep(0.08)
    return links


def source_for_text_key(key):
    return SOURCE_CATALOG.get(key, SOURCE_CATALOG["anatomy-general"])


def textbook_source(course, term):
    if term.get("pageImages"):
        context = term.get("contexts", [{}])[0]
        bits = []
        if context.get("bookPage"):
            bits.append(f"书页 {context['bookPage']}")
        if context.get("pdfPage"):
            bits.append(f"PDF {context['pdfPage']}")
        label = f"{course['shortTitle']}教材上下文"
        if bits:
            label += "：" + " / ".join(bits)
        return {"label": label, "url": term["pageImages"][0]}
    return {"label": f"{course['shortTitle']}教材上下文"}


def anatomy_kind(term):
    category = term.get("category") or ""
    chapters = " ".join(term.get("chapters") or [])
    zh = term.get("zh") or ""
    if category == "解剖方位":
        return "direction"
    if category == "骨与骨性标志":
        return "bone"
    if category == "关节韧带":
        return "joint"
    if category == "肌肉":
        return "muscle"
    if category == "神经结构" or "神经" in chapters:
        return "nerve"
    if category == "脉管结构" or "脉管" in chapters:
        return "vessel"
    if category == "腔隙通道" or any(token in zh for token in ("孔", "裂", "管", "窝", "腔")):
        return "passage"
    if category == "内脏器官" or any(token in chapters for token in ("消化", "呼吸", "泌尿", "生殖", "内分泌")):
        return "viscera"
    if category == "感觉器" or "感觉器" in chapters:
        return "sense"
    return "concept"


def histology_key(term):
    category = term.get("category") or ""
    zh = term.get("zh") or ""
    if zh in {"器官", "基本组织", "微环境", "细胞", "组织", "细胞外基质"}:
        return "基础概念"
    for key in HISTOLOGY_TEXT:
        if key in category:
            return key
    return "胚胎发生" if "胚胎" in " ".join(term.get("chapters") or []) else "技术"


def unique_sources(items):
    seen = set()
    result = []
    for item in items:
        if not item:
            continue
        key = (item.get("label"), item.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def enrich_term(course, term, wiki_links):
    course_id = course["id"]
    field_sources = term.get("fieldSources") or {}
    local_source = textbook_source(course, term)
    wiki_source = wiki_links.get(term["id"])

    if course_id == "systematic-anatomy":
        structure, function, source_key = ANATOMY_TEXT[anatomy_kind(term)]
    elif course_id == "histology-embryology":
        structure, function, source_key = HISTOLOGY_TEXT[histology_key(term)]
    else:
        structure = term.get("structure") or term.get("location") or ""
        function = term.get("function") or ""
        source_key = "anatomy-general"

    external_source = source_for_text_key(source_key)

    current_structure = term.get("structure") or term.get("location") or ""
    current_function = term.get("function") or ""

    if (not current_structure or current_structure in GENERATED_STRUCTURES) and structure:
        term["structure"] = structure
        term["location"] = structure
    if (not current_function or current_function in GENERATED_FUNCTIONS) and function:
        term["function"] = function

    base_sources = unique_sources([local_source, external_source, wiki_source])
    if term.get("structure") or term.get("location"):
        field_sources["structure"] = unique_sources(field_sources.get("structure", []) + base_sources)
    if term.get("function"):
        field_sources["function"] = unique_sources(field_sources.get("function", []) + base_sources)

    mnemonic = MNEMONICS.get(course_id, {}).get(term.get("zh"))
    term["studyNote"] = ""
    term.pop("mnemonic", None)
    if mnemonic:
        term["studyNote"] = mnemonic["text"]
        term["mnemonic"] = mnemonic["text"]
        field_sources["studyNote"] = unique_sources(
            [
                {"label": mnemonic["source"]},
                local_source,
                wiki_source,
            ]
        )

    if field_sources:
        term["fieldSources"] = field_sources


def write_split_files(data):
    COURSES_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for course in data["courses"]:
        summary = {k: v for k, v in course.items() if k not in {"terms", "figures"}}
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


def update_mnemonic_topic(data):
    topics = [topic for topic in parse_topics() if topic.get("id") != "mnemonic-formulas"]
    term_ids = []
    for course in data["courses"]:
        if course["id"] != "systematic-anatomy":
            continue
        for term in course["terms"]:
            if term.get("mnemonic"):
                term_ids.append(term["id"])
    if term_ids:
        topics.append(
            {
                "id": "mnemonic-formulas",
                "courseId": "systematic-anatomy",
                "title": "口诀速记专题",
                "summary": "只收真正适合背诵的顺序口诀；非口诀型自动学习提示已从词条中移除。",
                "tags": ["口诀", "顺序", "速记"],
                "termIds": term_ids,
            }
        )
    write_topics(topics)


def main():
    data = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    terms = [term for course in data["courses"] for term in course.get("terms", [])]
    wiki_links = get_wikipedia_links(terms)
    for course in data["courses"]:
        for term in course.get("terms", []):
            enrich_term(course, term, wiki_links)
    data["meta"]["fieldSupplementGeneratedAt"] = "2026-07-07"
    data["meta"]["fieldSupplementSources"] = ["local textbook context", "OpenStax", "Histology Guide", "UNSW Embryology", "Wikipedia when matched"]
    GLOSSARY_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_split_files(data)
    update_mnemonic_topic(data)
    print(
        json.dumps(
            {
                "terms": len(terms),
                "wikiLinks": len(wiki_links),
                "courses": [course["id"] for course in data["courses"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
