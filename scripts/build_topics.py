import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = ROOT / "data" / "glossary.json"
OUTPUT_PATH = ROOT / "data" / "topics.js"


TOPIC_SPECS = [
    {
        "id": "skull-base-foramina",
        "courseId": "systematic-anatomy",
        "title": "颅底孔裂专题",
        "summary": "把颅底内外面的孔、裂、管和通过结构放在一起复习。",
        "tags": ["颅骨", "通道", "神经血管"],
        "anchors": ["筛孔", "视神经管", "眶上裂", "圆孔", "卵圆孔", "棘孔", "破裂孔", "内耳门", "颈静脉孔", "舌下神经管", "枕骨大孔", "颈动脉管", "翼管", "茎乳孔"],
        "keywords": ["颅底", "孔", "裂", "管", "foramen", "fissure", "canal"],
        "maxTerms": 32,
    },
    {
        "id": "cranial-nerve-passages",
        "courseId": "systematic-anatomy",
        "title": "脑神经出入颅专题",
        "summary": "按脑神经、颅底孔裂和相关神经节建立一张出入颅地图。",
        "tags": ["脑神经", "颅底", "定位"],
        "anchors": ["嗅神经", "视神经", "动眼神经", "滑车神经", "三叉神经", "眼神经", "上颌神经", "下颌神经", "展神经", "面神经", "前庭蜗神经", "舌咽神经", "迷走神经", "副神经", "舌下神经", "筛孔", "视神经管", "眶上裂", "圆孔", "卵圆孔", "内耳门", "颈静脉孔", "舌下神经管"],
        "keywords": ["脑神经", "神经", "颅底", "foramen", "canal"],
        "maxTerms": 36,
    },
    {
        "id": "pterygopalatine-fossa",
        "courseId": "systematic-anatomy",
        "title": "翼腭窝专题",
        "summary": "集中看翼腭窝的交通、上颌神经、翼腭神经节和鼻腭区分支。",
        "tags": ["翼腭窝", "上颌神经", "交通"],
        "anchors": ["翼腭窝", "翼腭神经节", "翼腭神经", "上颌神经", "圆孔", "翼管", "翼管神经", "腭大神经", "鼻腭神经", "蝶腭孔", "眶下裂", "翼上颌裂"],
        "keywords": ["翼腭", "上颌神经", "腭", "蝶腭", "pterygopalatine"],
        "maxTerms": 24,
    },
    {
        "id": "orbit-nasal-sinuses",
        "courseId": "systematic-anatomy",
        "title": "眶、鼻腔与鼻旁窦专题",
        "summary": "把眶壁、鼻腔通道、鼻旁窦开口和泪道连成一组。",
        "tags": ["眶", "鼻腔", "鼻旁窦"],
        "anchors": ["眶", "视神经管", "眶上裂", "眶下裂", "泪囊窝", "鼻腔", "鼻中隔", "上鼻甲", "中鼻甲", "下鼻甲", "上鼻道", "中鼻道", "下鼻道", "蝶筛隐窝", "鼻旁窦", "上颌窦", "额窦", "筛窦", "蝶窦"],
        "keywords": ["眶", "鼻", "窦", "泪", "sinus", "orbit"],
        "maxTerms": 36,
    },
    {
        "id": "inguinal-canal",
        "courseId": "systematic-anatomy",
        "title": "腹股沟管专题",
        "summary": "腹股沟管四壁两口、腹股沟三角、精索和疝相关结构合并复习。",
        "tags": ["腹股沟", "疝", "腹前壁"],
        "anchors": ["腹股沟管", "腹股沟管浅环", "腹股沟管浅(皮下)环", "腹股沟管深(腹)环", "腹股沟韧带", "腹股沟镰", "联合腱", "腹横筋膜", "腹股沟(海氏)三角", "精索", "子宫圆韧带", "髂腹股沟神经"],
        "keywords": ["腹股沟", "精索", "疝", "inguinal"],
        "maxTerms": 28,
    },
    {
        "id": "mediastinum",
        "courseId": "systematic-anatomy",
        "title": "纵隔专题",
        "summary": "按上纵隔、前中后纵隔归纳心包、胸腺、气管食管和大血管。",
        "tags": ["胸腔", "纵隔", "器官关系"],
        "anchors": ["纵隔", "上纵隔", "下纵隔", "前纵隔", "中纵隔", "后纵隔", "心包", "胸腺", "气管", "食管", "主动脉弓", "胸主动脉", "奇静脉", "胸导管", "膈神经", "迷走神经"],
        "keywords": ["纵隔", "心包", "胸腺", "胸导管", "mediastinum"],
        "maxTerms": 32,
    },
    {
        "id": "porta-hepatis",
        "courseId": "systematic-anatomy",
        "title": "肝门与肝蒂专题",
        "summary": "围绕肝门、肝蒂、胆道和肝十二指肠韧带整理出入肝结构。",
        "tags": ["肝门", "胆道", "门静脉"],
        "anchors": ["肝门", "肝蒂", "门静脉", "肝固有动脉", "肝管", "肝总管", "胆总管", "胆囊管", "胆囊", "肝十二指肠韧带", "网膜孔", "十二指肠大乳头", "肝胰壶腹"],
        "keywords": ["肝门", "肝蒂", "胆", "门静脉", "肝十二指肠"],
        "maxTerms": 30,
    },
    {
        "id": "portal-system",
        "courseId": "systematic-anatomy",
        "title": "门静脉系与侧支循环专题",
        "summary": "把门静脉属支、腔静脉交通和临床侧支循环放在一页看。",
        "tags": ["门静脉", "侧支循环", "静脉"],
        "anchors": ["门静脉", "肠系膜上静脉", "肠系膜下静脉", "脾静脉", "胃左静脉", "胃右静脉", "直肠上静脉", "食管静脉丛", "脐周静脉网", "上腔静脉", "下腔静脉"],
        "keywords": ["门静脉", "静脉", "侧支", "腔静脉"],
        "maxTerms": 28,
    },
    {
        "id": "heart-coronary-conduction",
        "courseId": "systematic-anatomy",
        "title": "心冠脉与传导系统专题",
        "summary": "心腔、冠状血管和心传导系统一起记，适合心脏章节总复习。",
        "tags": ["心", "冠脉", "传导"],
        "anchors": ["心", "右心房", "右心室", "左心房", "左心室", "冠状动脉", "右冠状动脉", "左冠状动脉", "冠状窦", "心传导系", "窦房结", "房室结", "房室束"],
        "keywords": ["心", "冠状", "房室", "传导", "动脉"],
        "maxTerms": 34,
    },
    {
        "id": "brachial-plexus",
        "courseId": "systematic-anatomy",
        "title": "臂丛与上肢神经专题",
        "summary": "臂丛、主要分支和上肢典型神经损伤结构集中复习。",
        "tags": ["臂丛", "上肢", "神经"],
        "anchors": ["臂丛", "腋神经", "肌皮神经", "正中神经", "尺神经", "桡神经", "胸长神经", "肩胛背神经", "肩胛上神经", "胸背神经", "腋窝"],
        "keywords": ["臂丛", "上肢", "神经"],
        "maxTerms": 30,
    },
    {
        "id": "lumbosacral-plexus",
        "courseId": "systematic-anatomy",
        "title": "腰骶丛与下肢神经专题",
        "summary": "腰丛、骶丛及下肢主要神经的走行和支配整合。",
        "tags": ["腰丛", "骶丛", "下肢"],
        "anchors": ["腰丛", "骶丛", "股神经", "闭孔神经", "坐骨神经", "胫神经", "腓总神经", "腓浅神经", "腓深神经", "阴部神经", "臀上神经", "臀下神经"],
        "keywords": ["腰丛", "骶丛", "下肢", "神经"],
        "maxTerms": 32,
    },
    {
        "id": "csf-ventricles",
        "courseId": "systematic-anatomy",
        "title": "脑室与脑脊液循环专题",
        "summary": "侧脑室、第三脑室、第四脑室、蛛网膜下隙和脑脊液通路。",
        "tags": ["脑室", "脑脊液", "脑膜"],
        "anchors": ["侧脑室", "第三脑室", "第四脑室", "室间孔", "中脑水管", "蛛网膜下隙", "脑脊液", "硬脑膜窦", "上矢状窦", "蛛网膜粒"],
        "keywords": ["脑室", "脑脊液", "蛛网膜", "硬脑膜窦"],
        "maxTerms": 28,
    },
    {
        "id": "spinal-tracts",
        "courseId": "systematic-anatomy",
        "title": "脊髓传导束专题",
        "summary": "后索、脊髓丘脑束、锥体系和交叉部位放在一起复盘。",
        "tags": ["脊髓", "传导束", "定位"],
        "anchors": ["薄束", "楔束", "脊髓丘脑束", "皮质脊髓束", "内侧丘系", "锥体束", "锥体交叉", "白质前连合"],
        "keywords": ["传导束", "脊髓", "丘脑", "锥体", "内侧丘系"],
        "maxTerms": 24,
    },
    {
        "id": "perineum-pelvic-floor",
        "courseId": "systematic-anatomy",
        "title": "会阴与盆底专题",
        "summary": "会阴、盆膈、尿生殖膈、坐骨肛门窝和阴部神经血管通路。",
        "tags": ["会阴", "盆底", "阴部神经"],
        "anchors": ["会阴", "盆膈", "尿生殖膈", "坐骨肛门窝", "阴部神经", "阴部管", "会阴浅隙", "会阴深隙", "肛提肌", "尾骨肌"],
        "keywords": ["会阴", "盆膈", "尿生殖", "阴部", "肛门"],
        "maxTerms": 28,
    },
    {
        "id": "slide-basics",
        "courseId": "histology-embryology",
        "title": "组胚读片入门专题",
        "summary": "从染色、切片、显微镜和细胞嗜酸/嗜碱性开始建立读片语言。",
        "tags": ["读片", "染色", "技术"],
        "anchors": ["苏木精-伊红染色", "石蜡切片", "光学显微镜", "电子显微镜", "组织化学", "免疫组织化学", "细胞化学", "嗜酸性", "嗜碱性"],
        "keywords": ["染色", "切片", "显微镜", "组织化学", "嗜酸", "嗜碱", "读片"],
        "maxTerms": 26,
    },
    {
        "id": "epithelium-glands",
        "courseId": "histology-embryology",
        "title": "上皮与腺体读片专题",
        "summary": "上皮分类、细胞连接、基膜、外分泌腺和内分泌腺的读片线索。",
        "tags": ["上皮", "腺", "读片"],
        "anchors": ["上皮组织", "单层扁平上皮", "单层立方上皮", "单层柱状上皮", "假复层纤毛柱状上皮", "复层扁平上皮", "腺上皮", "杯状细胞", "基膜", "紧密连接", "桥粒", "外分泌腺", "内分泌腺"],
        "keywords": ["上皮", "腺", "连接", "基膜", "杯状细胞"],
        "maxTerms": 34,
    },
    {
        "id": "connective-cartilage-bone",
        "courseId": "histology-embryology",
        "title": "结缔组织、软骨和骨专题",
        "summary": "细胞、纤维、基质、软骨类型和骨单位的识别重点。",
        "tags": ["结缔组织", "软骨", "骨"],
        "anchors": ["疏松结缔组织", "致密结缔组织", "成纤维细胞", "巨噬细胞", "胶原纤维", "弹性纤维", "透明软骨", "弹性软骨", "纤维软骨", "骨单位", "哈弗斯系统", "成骨细胞", "破骨细胞"],
        "keywords": ["结缔", "软骨", "骨", "纤维", "基质"],
        "maxTerms": 34,
    },
    {
        "id": "blood-immune",
        "courseId": "histology-embryology",
        "title": "血液、造血与免疫器官专题",
        "summary": "血细胞分类、骨髓造血、胸腺、淋巴结和脾的结构对比。",
        "tags": ["血液", "造血", "免疫"],
        "anchors": ["红细胞", "中性粒细胞", "嗜酸性粒细胞", "嗜碱性粒细胞", "淋巴细胞", "单核细胞", "血小板", "骨髓", "造血干细胞", "胸腺", "淋巴结", "脾"],
        "keywords": ["血", "造血", "淋巴", "胸腺", "脾", "免疫"],
        "maxTerms": 36,
    },
    {
        "id": "muscle-nerve",
        "courseId": "histology-embryology",
        "title": "肌组织与神经组织读片专题",
        "summary": "骨骼肌、心肌、平滑肌和神经组织的形态差异合并辨认。",
        "tags": ["肌组织", "神经组织", "读片"],
        "anchors": ["骨骼肌纤维", "心肌纤维", "平滑肌", "闰盘", "肌节", "神经元", "突触", "有髓神经纤维", "无髓神经纤维", "少突胶质细胞", "施万细胞", "血-脑屏障"],
        "keywords": ["肌", "神经", "闰盘", "突触", "髓鞘", "胶质"],
        "maxTerms": 36,
    },
    {
        "id": "digestive-respiratory-reading",
        "courseId": "histology-embryology",
        "title": "消化管与呼吸系统读片专题",
        "summary": "食管、胃肠黏膜、气管和肺泡结构放在一起做切片识别。",
        "tags": ["消化管", "呼吸", "读片"],
        "anchors": ["食管", "胃底腺", "主细胞", "壁细胞", "小肠绒毛", "杯状细胞", "结肠", "气管", "支气管", "肺泡", "Ⅰ型肺泡细胞", "Ⅱ型肺泡细胞"],
        "keywords": ["食管", "胃", "小肠", "结肠", "气管", "肺泡"],
        "maxTerms": 38,
    },
    {
        "id": "liver-pancreas-reading",
        "courseId": "histology-embryology",
        "title": "肝、胆与胰腺读片专题",
        "summary": "肝小叶、门管区、肝血窦、胆小管、胰腺腺泡和胰岛。",
        "tags": ["肝", "胰腺", "读片"],
        "anchors": ["肝小叶", "门管区", "肝血窦", "肝细胞", "胆小管", "库普弗细胞", "贮脂细胞", "胰腺", "胰岛", "浆液性腺泡"],
        "keywords": ["肝", "胆", "胰", "血窦", "门管"],
        "maxTerms": 32,
    },
    {
        "id": "urinary-reproductive-reading",
        "courseId": "histology-embryology",
        "title": "泌尿与生殖系统读片专题",
        "summary": "肾单位、滤过屏障、生精小管、卵泡、黄体和子宫内膜。",
        "tags": ["泌尿", "生殖", "读片"],
        "anchors": ["肾单位", "肾小体", "滤过屏障", "近端小管", "远端小管", "集合管", "生精小管", "支持细胞", "间质细胞", "卵泡", "黄体", "子宫内膜"],
        "keywords": ["肾", "小管", "生精", "卵泡", "黄体", "子宫"],
        "maxTerms": 40,
    },
    {
        "id": "embryo-general",
        "courseId": "histology-embryology",
        "title": "胚胎发生总论专题",
        "summary": "受精、卵裂、植入、三胚层、神经管和胚体折叠的时间线。",
        "tags": ["胚胎", "发生", "时间线"],
        "anchors": ["受精", "卵裂", "囊胚", "植入", "原条", "三胚层", "外胚层", "中胚层", "内胚层", "神经管", "神经嵴", "胚体折叠", "体节"],
        "keywords": ["胚胎", "受精", "卵裂", "植入", "胚层", "神经管", "体节"],
        "maxTerms": 42,
    },
    {
        "id": "placenta-membranes",
        "courseId": "histology-embryology",
        "title": "胎膜、胎盘与脐带专题",
        "summary": "绒毛膜、羊膜、胎盘屏障、蜕膜、脐带和胎儿循环的关联。",
        "tags": ["胎盘", "胎膜", "脐带"],
        "anchors": ["胎盘", "绒毛膜", "羊膜", "卵黄囊", "尿囊", "脐带", "胎盘屏障", "蜕膜", "绒毛", "脐静脉", "脐动脉"],
        "keywords": ["胎盘", "胎膜", "绒毛", "羊膜", "脐", "蜕膜"],
        "maxTerms": 34,
    },
    {
        "id": "embryo-malformations",
        "courseId": "histology-embryology",
        "title": "胚胎畸形专题",
        "summary": "神经管、颜面、心血管、消化呼吸和泌尿生殖常见畸形总览。",
        "tags": ["畸形", "临床", "胚胎"],
        "anchors": ["先天畸形", "神经管缺陷", "无脑儿", "脊柱裂", "唇裂", "腭裂", "法洛四联症", "室间隔缺损", "房间隔缺损", "动脉导管未闭", "先天性脐疝", "气管食管瘘", "先天性腹股沟疝"],
        "keywords": ["畸形", "先天", "缺损", "裂", "导管未闭", "瘘", "疝"],
        "maxTerms": 42,
    },
    {
        "id": "face-palate-limb-development",
        "courseId": "histology-embryology",
        "title": "颜面、腭与四肢发生专题",
        "summary": "额鼻突、上颌突、下颌突、腭突和四肢芽的发生与畸形。",
        "tags": ["颜面", "腭", "四肢"],
        "anchors": ["鳃弓", "额鼻突", "上颌突", "下颌突", "腭突", "原始口腔", "唇裂", "腭裂", "四肢芽"],
        "keywords": ["颜面", "腭", "鳃弓", "上颌突", "下颌突", "四肢"],
        "maxTerms": 30,
    },
    {
        "id": "cardiovascular-development",
        "courseId": "histology-embryology",
        "title": "心血管系统发生专题",
        "summary": "心管、心襻、房室分隔、动脉干和常见先心畸形。",
        "tags": ["心血管", "发生", "先心病"],
        "anchors": ["心管", "心襻", "心房分隔", "心室分隔", "房室管", "动脉干", "主动脉弓", "卵圆孔", "动脉导管", "法洛四联症", "室间隔缺损", "房间隔缺损"],
        "keywords": ["心", "血管", "房", "室", "动脉", "导管", "分隔"],
        "maxTerms": 42,
    },
    {
        "id": "nervous-sense-development",
        "courseId": "histology-embryology",
        "title": "神经系统与眼耳发生专题",
        "summary": "神经管、神经嵴、脑泡、脊髓、视杯、晶状体和耳泡发生。",
        "tags": ["神经发生", "眼耳", "神经嵴"],
        "anchors": ["神经管", "神经嵴", "神经板", "脑泡", "脊髓", "视杯", "晶状体板", "耳泡", "视网膜", "内耳"],
        "keywords": ["神经", "脑泡", "脊髓", "视", "晶状体", "耳"],
        "maxTerms": 38,
    },
]


def text_for(term):
    parts = [
        term.get("zh", ""),
        term.get("en", ""),
        term.get("category", ""),
        term.get("part", ""),
        " ".join(term.get("chapters", [])),
        term.get("definition", ""),
        term.get("structure", ""),
        term.get("location", ""),
        term.get("function", ""),
        term.get("studyNote", ""),
    ]
    parts.extend(context.get("text", "") for context in term.get("contexts", []))
    gray = term.get("gray") or {}
    parts.extend([gray.get("zh", ""), gray.get("en", "")])
    book = gray.get("book") or {}
    parts.extend([book.get("zh", ""), book.get("en", "")])
    parts.extend(hit.get("snippet", "") for hit in book.get("hits", []))
    return " ".join(str(part) for part in parts if part).lower()


def score_term(term, spec, anchor_index):
    zh = str(term.get("zh", "")).lower()
    en = str(term.get("en", "")).lower()
    haystack = text_for(term)
    score = 0

    for anchor, index in anchor_index.items():
        key = anchor.lower()
        if zh == key or en == key:
            score += 1000 - index
        elif key and (key in zh or key in en):
            score += 240 - min(index, 80)
        elif key and key in haystack:
            score += 80 - min(index, 40)

    for keyword in spec.get("keywords", []):
        key = keyword.lower()
        if not key:
            continue
        if key in zh or key in en:
            score += 120
        elif key in haystack:
            score += 28

    return score


def build_topic(spec, course_terms):
    anchor_index = {anchor: index for index, anchor in enumerate(spec.get("anchors", []))}
    ranked = []
    for term in course_terms:
        score = score_term(term, spec, anchor_index)
        if score > 0:
            ranked.append((score, term.get("id")))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    term_ids = []
    seen = set()
    for _, term_id in ranked:
        if term_id and term_id not in seen:
            term_ids.append(term_id)
            seen.add(term_id)
        if len(term_ids) >= spec.get("maxTerms", 30):
            break
    return {
        "id": spec["id"],
        "courseId": spec["courseId"],
        "title": spec["title"],
        "summary": spec["summary"],
        "tags": spec.get("tags", []),
        "termIds": term_ids,
    }


def main():
    payload = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    courses = {course["id"]: course.get("terms", []) for course in payload.get("courses", [])}
    topics = [build_topic(spec, courses.get(spec["courseId"], [])) for spec in TOPIC_SPECS]
    empty = [topic["id"] for topic in topics if not topic["termIds"]]
    if empty:
        raise RuntimeError(f"Topics without terms: {', '.join(empty)}")

    OUTPUT_PATH.write_text(
        "window.MED_GLOSSARY_TOPICS = "
        + json.dumps(topics, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {len(topics)} topics to {OUTPUT_PATH}")
    for topic in topics:
        print(f"{topic['courseId']} {topic['title']}: {len(topic['termIds'])}")


if __name__ == "__main__":
    main()
