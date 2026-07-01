from __future__ import annotations

import json
import re
import unicodedata
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_JSON = ROOT / "data" / "glossary.json"
GLOSSARY_JS = ROOT / "data" / "glossary.js"
GLOSSARY_CSV = ROOT / "data" / "glossary.csv"
REPORT_JSON = ROOT / "data" / "report.json"

PDF_PAGE_OFFSET = 22

PARTS = [
    {"name": "有机化学总论", "start": 1, "end": 51},
    {"name": "有机化学各论", "start": 52, "end": 198},
    {"name": "重要的生物有机化合物", "start": 199, "end": 266},
]

CHAPTERS = [
    {"name": "第一章 绪论", "start": 2, "part": "有机化学总论"},
    {"name": "第二章 立体化学基础", "start": 15, "part": "有机化学总论"},
    {"name": "第三章 有机化合物的结构鉴定", "start": 29, "part": "有机化学总论"},
    {"name": "第四章 烷烃", "start": 52, "part": "有机化学各论"},
    {"name": "第五章 烯烃和炔烃", "start": 63, "part": "有机化学各论"},
    {"name": "第六章 脂环烃", "start": 82, "part": "有机化学各论"},
    {"name": "第七章 芳香烃", "start": 88, "part": "有机化学各论"},
    {"name": "第八章 卤代烃", "start": 100, "part": "有机化学各论"},
    {"name": "第九章 醇、硫醇、酚", "start": 110, "part": "有机化学各论"},
    {"name": "第十章 醚和环氧化合物", "start": 124, "part": "有机化学各论"},
    {"name": "第十一章 胺和生物碱", "start": 132, "part": "有机化学各论"},
    {"name": "第十二章 醛和酮", "start": 146, "part": "有机化学各论"},
    {"name": "第十三章 羧酸和取代羧酸", "start": 159, "part": "有机化学各论"},
    {"name": "第十四章 羧酸衍生物", "start": 172, "part": "有机化学各论"},
    {"name": "第十五章 杂环化合物", "start": 184, "part": "有机化学各论"},
    {"name": "第十六章 类脂化合物", "start": 200, "part": "重要的生物有机化合物"},
    {"name": "第十七章 糖类", "start": 215, "part": "重要的生物有机化合物"},
    {"name": "第十八章 氨基酸、多肽和蛋白质", "start": 231, "part": "重要的生物有机化合物"},
    {"name": "第十九章 核酸", "start": 244, "part": "重要的生物有机化合物"},
]


def T(
    zh: str,
    en: str,
    category: str,
    definition: str,
    structure: str,
    function: str,
    note: str,
    keywords: list[str],
    chapter: str,
) -> dict[str, Any]:
    return {
        "zh": zh,
        "en": en,
        "category": category,
        "definition": definition,
        "structure": structure,
        "function": function,
        "studyNote": note,
        "keywords": keywords,
        "chapter": chapter,
    }


TERMS = [
    T("有机化合物", "organic compound", "基础概念", "以碳骨架为核心、通常含 C-H 键并可含 O、N、S、卤素等元素的化合物。", "有机化合物的性质主要由碳骨架、官能团和空间结构共同决定。", "学习时把分子分成骨架和官能团：骨架决定疏水性和空间位阻，官能团决定主要反应。", "先问它有什么官能团，再问该官能团在什么电子环境里。", ["有机化合物", "organic compound"], "第一章 绪论"),
    T("官能团", "functional group", "基础概念", "决定一类有机化合物典型化学性质的原子或原子团。", "羟基、羰基、羧基、氨基、卤素、碳碳双键等都可作为官能团。", "官能团是反应和鉴别的入口，同一官能团在不同电子环境中的活性可能明显不同。", "复习反应时按官能团建表，再补反应条件、主要产物和鉴别现象。", ["官能团", "羟基", "羰基", "氨基"], "第一章 绪论"),
    T("杂化轨道", "hybrid orbital", "基础理论", "同一原子内能量相近的原子轨道重新组合形成方向性更强的新轨道。", "碳常见 sp3、sp2、sp 三种杂化，对应四面体、平面三角形、直线形。", "杂化决定键角、键长、酸性和反应位置；s 成分越高，碳原子电负性越大。", "酸性顺序常用 s 成分解释：端炔 C-H 比烯烃、烷烃 C-H 更酸。", ["杂化轨道", "sp3", "sp2", "sp"], "第一章 绪论"),
    T("σ键和π键", "sigma bond and pi bond", "基础理论", "σ键由轨道沿键轴重叠形成，π键由平行 p 轨道侧面重叠形成。", "单键通常是 σ键；双键含 1 个 σ键和 1 个 π键；叁键含 1 个 σ键和 2 个 π键。", "π键电子云外露、较易极化，是烯烃、炔烃发生加成和氧化的关键。", "看到不饱和键，先判断 π键能否被亲电试剂或氧化剂进攻。", ["σ键", "π键", "双键", "叁键"], "第一章 绪论"),
    T("共振理论", "resonance theory", "基础理论", "当一个分子或离子不能用单一 Lewis 式准确表示时，用多个仅电子位置不同的共振式描述真实结构。", "共振式原子位置不变，只改变 π电子或孤对电子分布；真实结构是共振杂化体。", "共振能降低体系能量，解释羧酸盐稳定、芳香性、酚和苯胺的取代定位等。", "画共振式时不要移动原子，只移动电子。贡献大的共振式通常八隅体完整、电荷分离少。", ["共振", "resonance", "共振式"], "第一章 绪论"),
    T("诱导效应", "inductive effect", "电子效应", "由原子或基团电负性差异引起，并沿 σ键传递的电子偏移效应。", "吸电子诱导效应用 -I 表示，给电子诱导效应用 +I 表示，传递距离通常较短。", "诱导效应用于解释酸性、碳正离子稳定性、双键极化和取代基对反应活性的影响。", "卤素有 -I；烷基一般有 +I。比较酸性时，吸电子基越近、越强，酸性越强。", ["诱导效应", "inductive", "-I", "+I"], "第五章 烯烃和炔烃"),
    T("共轭效应", "conjugation effect", "电子效应", "π键、p 轨道或孤对电子连续重叠导致电子离域的效应。", "共轭体系可包含 C=C-C=C、芳环、羰基相邻双键、含孤对电子的杂原子等。", "共轭能稳定碳正离子、自由基和羧酸盐，也改变紫外吸收和亲电取代定位。", "判断共轭先看是否有连续 p 轨道；sp3 碳插入会打断共轭。", ["共轭", "conjugation", "离域"], "第五章 烯烃和炔烃"),
    T("超共轭效应", "hyperconjugation effect", "电子效应", "C-H 或 C-C σ键与相邻 π键或空 p 轨道重叠产生的弱电子离域。", "烷基越多，能参与超共轭的 σ键越多，对碳正离子和烯烃的稳定作用越明显。", "常用来解释碳正离子稳定性、烯烃稳定性和自由基稳定性。", "看到三级碳正离子更稳定，别只背顺序，要想到烷基给电子和超共轭。", ["超共轭", "hyperconjugation"], "第五章 烯烃和炔烃"),
    T("碳正离子稳定性顺序", "carbocation stability order", "活性顺序", "碳正离子越能通过烷基给电子、超共轭或共振分散正电荷，就越稳定。", "常见顺序：苄基/烯丙基型因共振很稳定；脂肪族通常 3° > 2° > 1° > 甲基。", "决定 SN1、E1、Markovnikov 加成等反应中间体的形成倾向和重排风险。", "凡是经碳正离子的反应，都要主动检查是否会重排为更稳定碳正离子。", ["碳正离子", "carbocation", "稳定"], "第一章 绪论"),
    T("自由基稳定性顺序", "radical stability order", "活性顺序", "自由基稳定性取决于单电子能否被超共轭或共振分散。", "常见顺序：苄基/烯丙基型 > 3° > 2° > 1° > 甲基。", "影响烷烃卤代选择性和自由基链反应的主要产物。", "氯代反应选择性较低，溴代更偏向形成稳定自由基的位置。", ["自由基", "free radical", "稳定"], "第四章 烷烃"),
    T("酸性强弱判断", "acidity trend", "活性顺序", "有机酸性主要看共轭碱稳定性，稳定性越高，酸越强。", "常用因素包括原子电负性和半径、杂化 s 成分、诱导效应、共振效应、溶剂化。", "用于比较羧酸、酚、醇、端炔、胺盐等酸性。", "答题时按 ARIO 思路：Atom、Resonance、Induction、Orbital。", ["酸性", "pKa", "共轭碱"], "第一章 绪论"),
    T("亲核性", "nucleophilicity", "活性顺序", "亲核体是能提供电子对进攻正电性中心的物种，亲核性表示进攻速度能力。", "亲核性受电荷、碱性、溶剂、位阻和可极化性影响；强碱不一定总是好亲核体。", "用于判断 SN2、羰基加成、酰基取代和环氧开环的反应方向。", "区分亲核性和碱性：前者看进攻碳的速度，后者看夺取质子的平衡能力。", ["亲核", "nucleophile", "亲核性"], "第一章 绪论"),
    T("离去基能力顺序", "leaving group ability order", "活性顺序", "离去基越能稳定离去后的负电荷，越容易离去。", "卤离子常见离去能力 I- > Br- > Cl- >> F-；磺酸酯也是优良离去基。", "影响亲核取代和消除反应速率，是判断卤代烃反应活性的核心因素之一。", "好离去基通常是弱碱；F- 碱性较强、C-F 键强，所以氟代烷反应性低。", ["离去基", "I-", "Br-", "Cl-", "F-"], "第八章 卤代烃"),
    T("手性碳原子", "chiral carbon", "立体化学", "连接四个不同原子或基团的饱和碳原子常称为手性碳原子。", "手性碳使分子可能具有非叠合镜像关系，但有对称面时可能整体不手性。", "是判断旋光性、对映体和 R/S 构型的入口。", "先找 sp3 碳，再看四个连接对象是否真正不同。", ["手性碳", "chiral carbon", "手性中心"], "第二章 立体化学基础"),
    T("对映体", "enantiomer", "立体化学", "互为不能重叠镜像的一对立体异构体。", "对映体在非手性环境中多数物理性质相同，但旋光方向相反。", "药物、氨基酸和糖的生理活性常与对映异构密切相关。", "看到一个手性中心通常有一对对映体；多个手性中心还要考虑内消旋。", ["对映体", "enantiomer"], "第二章 立体化学基础"),
    T("非对映异构体", "diastereomer", "立体化学", "不互为镜像关系的立体异构体。", "包括多个手性中心中部分构型不同的异构体，也包括 E/Z 异构。", "非对映体物理性质不同，通常可用普通分离方法分开。", "多个手性中心比较时，若不是全部相反，多半是非对映体。", ["非对映", "diastereomer"], "第二章 立体化学基础"),
    T("内消旋化合物", "meso compound", "立体化学", "含手性中心但因分子内部对称而整体不旋光的化合物。", "常有对称面或对称中心，使各手性部分旋光效应相互抵消。", "用于判断含两个或多个手性中心化合物的异构体数目。", "不要只数手性碳；最后一定看整体对称性。", ["内消旋", "meso"], "第二章 立体化学基础"),
    T("外消旋体", "racemate", "立体化学", "等量左旋和右旋对映体组成的混合物。", "外消旋体整体不显示旋光性，但各单一对映体仍有旋光性。", "拆分外消旋体是获得单一手性药物或天然产物的重要方法。", "外消旋体不等于内消旋体：前者是混合物，后者是单一化合物。", ["外消旋", "racemate"], "第二章 立体化学基础"),
    T("R/S 构型标记", "R/S configuration", "立体化学", "按 CIP 次序规则标记手性中心绝对构型的方法。", "按原子序数排优先级，最低优先级背向观察，1->2->3 顺时针为 R，逆时针为 S。", "用于准确命名手性分子并比较立体异构关系。", "Fischer 投影中横线朝前、竖线朝后，最低优先级在横线时结果要反转。", ["R/S", "CIP", "构型"], "第二章 立体化学基础"),
    T("E/Z 构型标记", "E/Z configuration", "立体化学", "用于描述双键两端高优先级基团相对位置的构型标记。", "两端高优先级基团在同侧为 Z，在异侧为 E。", "比顺反标记适用范围更广，常用于取代烯烃。", "先分别在双键两端排优先级，再判断同侧或异侧。", ["E/Z", "顺反", "双键构型"], "第五章 烯烃和炔烃"),
    T("构象", "conformation", "立体化学", "单键旋转产生的、通常可相互转化的空间排列。", "乙烷有交叉式和重叠式；丁烷有反交叉、邻交叉等构象。", "构象影响能量、稳定性和反应空间取向。", "构象不是构型，通常不需要断键就能互相转化。", ["构象", "conformation"], "第四章 烷烃"),
    T("环己烷椅式构象", "chair conformation of cyclohexane", "立体化学", "环己烷最稳定的构象，能使键角张力和扭转张力较小。", "取代基有轴向键和赤道键；体积大的取代基通常更愿意处于赤道键。", "解释取代环己烷稳定性和反应选择性。", "判断稳定构象时，优先让大基团在 e 键。", ["椅式构象", "环己烷", "chair"], "第六章 脂环烃"),
    T("不饱和度", "degree of unsaturation", "结构鉴定", "分子式相对饱和链烷少的氢对数，反映环和π键总数。", "一个环或一个双键贡献 1 个不饱和度，一个叁键贡献 2 个。", "用于从分子式快速推断是否有芳环、羰基、双键、环等结构。", "含卤素按氢处理，含氮时加一个氢，氧和硫通常不影响计算。", ["不饱和度", "U", "degree"], "第三章 有机化合物的结构鉴定"),
    T("紫外光谱", "ultraviolet spectra", "结构鉴定", "由分子中电子能级跃迁产生的吸收光谱，常用于识别共轭体系。", "共轭越长，吸收波长通常越长；羰基可有 n->π* 吸收。", "适合判断芳香环、共轭双键和部分羰基共轭结构。", "UV 给的是共轭信息，不能单独完成结构鉴定。", ["紫外光谱", "UV", "共轭"], "第三章 有机化合物的结构鉴定"),
    T("红外光谱", "infrared spectra", "结构鉴定", "由化学键振动能级跃迁产生的吸收光谱，常用于识别官能团。", "羰基约在 1700 cm-1 强吸收，羟基常有宽峰，叁键约在 2100 cm-1 附近。", "用于快速判断羰基、羟基、氨基、叁键、芳环等官能团。", "IR 先看特征区，再看指纹区；强峰位置要结合分子环境判断。", ["红外光谱", "IR", "官能团"], "第三章 有机化合物的结构鉴定"),
    T("核磁共振氢谱", "proton nuclear magnetic resonance", "结构鉴定", "利用氢核在磁场中的共振吸收分析不同化学环境氢原子的谱法。", "化学位移、积分面积、裂分峰形和偶合常数共同提供结构信息。", "用于判断氢的类型、数量及相邻氢关系。", "读谱顺序：先积分和组数，再看化学位移，最后用裂分拼片段。", ["核磁共振", "1H-NMR", "化学位移"], "第三章 有机化合物的结构鉴定"),
    T("质谱", "mass spectroscopy", "结构鉴定", "使分子离子化并按质荷比检测的结构分析方法。", "分子离子峰给相对分子质量，碎片峰反映易裂解部位。", "与 IR、NMR、UV 合用可推断分子式、官能团和骨架。", "质谱先找分子离子峰，再看同位素峰和特征碎片。", ["质谱", "MS", "分子离子峰"], "第三章 有机化合物的结构鉴定"),
    T("羰基红外特征峰", "carbonyl IR absorption", "结构鉴定", "羰基 C=O 伸缩振动通常在 1700 cm-1 左右出现强吸收。", "酰卤、酸酐、酯、醛、酮、羧酸、酰胺位置不同，共轭会使波数降低。", "是鉴别羰基化合物最直接的 IR 信号之一。", "看到 1700 cm-1 强峰先判断是否羰基，再结合 O-H、C-H、N-H 等峰细分。", ["羰基", "1700", "IR"], "第三章 有机化合物的结构鉴定"),
    T("羟基和氨基红外特征", "OH and NH IR absorption", "结构鉴定", "O-H 和 N-H 伸缩振动常出现在 3200-3600 cm-1 区域。", "羟基峰常较宽，羧酸 O-H 更宽；胺的 N-H 峰通常较尖，伯胺可有双峰。", "用于区分醇、酚、羧酸和胺类化合物。", "羧酸 O-H 宽而拖尾，容易和普通醇羟基峰混淆。", ["羟基", "氨基", "IR", "O-H", "N-H"], "第三章 有机化合物的结构鉴定"),
    T("烷烃自由基卤代", "free radical halogenation of alkanes", "烃类反应", "烷烃在光照或高温下与卤素发生自由基取代反应。", "反应包含链引发、链增长和链终止，常生成多种卤代产物。", "用于理解自由基链反应和选择性来源。", "氯代快但选择性较低，溴代慢但更偏向稳定自由基位置。", ["烷烃", "卤代", "自由基链反应"], "第四章 烷烃"),
    T("卤代反应选择性", "selectivity of halogenation", "活性顺序", "自由基卤代产物比例由氢原子数目和相应自由基稳定性共同决定。", "叔氢、仲氢、伯氢反应活性通常依次降低；溴代比氯代更能体现这种差异。", "用于预测烷烃卤代主产物。", "不要只看有几个氢，也要看抽氢后形成什么自由基。", ["卤代", "选择性", "叔氢", "仲氢", "伯氢"], "第四章 烷烃"),
    T("烯烃亲电加成", "electrophilic addition of alkenes", "烃类反应", "烯烃 π键向亲电试剂提供电子，形成加成产物。", "常见反应包括加 HX、加 X2、加水、加次卤酸等。", "是烯烃最重要的反应类型，产物取向受碳正离子稳定性或环状中间体控制。", "先判断试剂是否亲电，再看是否有 Markovnikov 取向、反式加成或重排。", ["烯烃", "亲电加成", "π键"], "第五章 烯烃和炔烃"),
    T("Markovnikov 规则", "Markovnikov rule", "烃类反应", "不对称烯烃与 HX 等加成时，氢通常加到含氢较多的双键碳上。", "本质是形成更稳定碳正离子或类碳正离子过渡态。", "用于预测不对称烯烃加 HX、酸催化水合等反应主产物。", "口诀能用，但本质是中间体稳定性；有过氧化物时 HBr 可反向。", ["Markovnikov", "马氏", "加成取向"], "第五章 烯烃和炔烃"),
    T("过氧化物效应", "peroxide effect", "烃类反应", "过氧化物存在时 HBr 对烯烃可发生自由基加成，表现为反 Markovnikov 取向。", "该效应主要适用于 HBr，不适用于 HCl 和 HI 的普通条件。", "用于区分离子型加成和自由基加成的取向差异。", "看到 ROOR 和 HBr，优先想到自由基机制和反马氏加成。", ["过氧化物效应", "HBr", "反马氏"], "第五章 烯烃和炔烃"),
    T("烯烃加氢", "hydrogenation of alkenes", "烃类反应", "烯烃在催化剂存在下与氢气加成生成烷烃。", "常用 Ni、Pt、Pd 等催化剂，通常发生同面加成。", "用于还原碳碳双键，也可反映不饱和程度。", "加氢消耗 H2 的量可帮助判断双键或叁键数目。", ["加氢", "烯烃", "催化"], "第五章 烯烃和炔烃"),
    T("溴水鉴别不饱和键", "bromine test for unsaturation", "鉴别反应", "烯烃、炔烃等不饱和化合物可使溴水或溴的四氯化碳溶液褪色。", "本质是卤素对 π键加成，红棕色溴被消耗。", "用于初步鉴别碳碳双键或叁键。", "能褪色不一定只代表烯烃；酚、醛等还可能发生其他反应。", ["溴水", "褪色", "不饱和", "鉴别"], "第五章 烯烃和炔烃"),
    T("高锰酸钾鉴别不饱和键", "Baeyer test", "鉴别反应", "烯烃、炔烃可使稀冷 KMnO4 紫色褪去并生成棕色 MnO2。", "温和条件下烯烃可氧化为邻二醇；强氧化条件下可发生断裂。", "用于鉴别不饱和键，也用于推断双键位置。", "KMnO4 是氧化剂，阳性不专属于烯烃，醛等还原性物质也会反应。", ["高锰酸钾", "KMnO4", "Baeyer", "鉴别"], "第五章 烯烃和炔烃"),
    T("烯烃臭氧化", "ozonolysis of alkenes", "烃类反应", "臭氧与烯烃反应后经还原或氧化处理，使双键断裂为羰基化合物或羧酸。", "还原处理常得醛/酮，氧化处理可将醛进一步氧化为酸。", "用于确定双键位置和合成羰基化合物。", "反推结构时，把产物羰基碳重新连成双键。", ["臭氧化", "ozonolysis", "双键断裂"], "第五章 烯烃和炔烃"),
    T("硼氢化-氧化", "hydroboration-oxidation", "烃类反应", "烯烃先与硼烷加成，再经氧化水解生成醇。", "总体表现为反 Markovnikov 水合，且通常为同面加成。", "用于把末端烯烃转化为伯醇。", "和酸催化水合对比记：酸水合马氏，硼氢化-氧化反马氏。", ["硼氢化", "氧化", "反马氏", "醇"], "第五章 烯烃和炔烃"),
    T("共轭二烯 1,2-加成和 1,4-加成", "1,2- and 1,4-addition of conjugated dienes", "烃类反应", "共轭二烯发生亲电加成时可形成 1,2-加成和 1,4-加成产物。", "低温常有动力学控制产物，高温常有热力学控制产物。", "体现共轭体系中烯丙基碳正离子的离域。", "看到共轭二烯加成，别只写一个产物，要考虑 1,2 和 1,4 两种。", ["共轭二烯", "1,2-加成", "1,4-加成"], "第五章 烯烃和炔烃"),
    T("炔烃亲电加成", "electrophilic addition of alkynes", "烃类反应", "炔烃可与 HX、X2、水等发生亲电加成，逐步由叁键变双键再变单键。", "末端炔水合常经烯醇互变为甲基酮，硼氢化-氧化可得醛。", "用于炔烃向烯烃、卤代烯烃、羰基化合物的转化。", "炔烃加一当量和两当量产物不同，答题要看试剂用量。", ["炔烃", "亲电加成", "叁键"], "第五章 烯烃和炔烃"),
    T("端炔酸性", "acidity of terminal alkynes", "烃类性质", "端炔 C-H 因 sp 碳 s 成分高而具有弱酸性。", "端炔可与强碱形成炔负离子，也可与银氨溶液或亚铜盐形成炔化物沉淀。", "端炔负离子是重要亲核体，可用于增长碳链。", "只有端炔有可脱去的炔氢，内炔没有这种鉴别反应。", ["端炔", "酸性", "炔氢"], "第五章 烯烃和炔烃"),
    T("端炔银盐和亚铜盐鉴别", "silver and cuprous acetylide test", "鉴别反应", "端炔可与银氨溶液或氯化亚铜氨溶液生成炔化银或炔化亚铜沉淀。", "内炔不含炔氢，通常不发生该沉淀反应。", "用于鉴别端炔和内炔。", "炔化银、炔化亚铜干燥时可能有爆炸危险，实验中需谨慎处理。", ["端炔", "银氨", "亚铜", "沉淀", "鉴别"], "第五章 烯烃和炔烃"),
    T("环张力", "ring strain", "脂环烃", "环状化合物因键角偏离理想值或构象受限产生的能量升高。", "小环如环丙烷、环丁烷张力较大，反应性与普通烷烃不同。", "解释小环加成、开环和稳定性差异。", "三元环不是普通单键思维，它有明显张力和类似不饱和的反应倾向。", ["环张力", "环丙烷", "脂环烃"], "第六章 脂环烃"),
    T("芳香性", "aromaticity", "芳香烃", "环状、平面、连续共轭并具有特殊稳定性的性质。", "苯是典型芳香化合物，六个 π电子离域在整个环上。", "芳香性解释苯难加成、易取代及芳香杂环的稳定性。", "芳香性不是有香味，而是电子结构稳定。", ["芳香性", "aromaticity", "苯"], "第七章 芳香烃"),
    T("Huckel 规则", "Huckel rule", "芳香烃", "单环平面连续共轭体系若含 4n+2 个 π电子，通常具有芳香性。", "苯有 6 个 π电子，符合 n=1；环戊二烯负离子也可符合。", "用于判断芳香、反芳香和非芳香体系。", "先确认环状、平面、连续共轭，再数 π电子。", ["Huckel", "4n+2", "芳香"], "第七章 芳香烃"),
    T("芳香亲电取代", "electrophilic aromatic substitution", "芳香烃反应", "芳环与亲电试剂反应，以取代氢的方式保持芳香性。", "包括硝化、磺化、卤代、Friedel-Crafts 烷基化和酰基化。", "是苯及其衍生物最重要的反应模式。", "关键中间体是 σ络合物；最终脱 H+ 恢复芳香性。", ["亲电取代", "芳香烃", "EAS"], "第七章 芳香烃"),
    T("芳烃硝化反应", "nitration of aromatic hydrocarbons", "芳香烃反应", "芳环在硝酸和硫酸作用下引入硝基。", "活性亲电体通常是硝酰正离子 NO2+。", "用于制备硝基芳香化合物，也用于后续还原为芳胺。", "硝基是强吸电子、间位定位、钝化基团。", ["硝化", "硝基", "NO2"], "第七章 芳香烃"),
    T("芳烃磺化反应", "sulfonation of aromatic hydrocarbons", "芳香烃反应", "芳环与浓硫酸或发烟硫酸反应引入磺酸基。", "磺化通常可逆，磺酸基是强吸电子、间位定位基团。", "可用于引入水溶性或作为合成中的临时定位基。", "磺酸基可作为阻挡基记忆，用完还能脱去。", ["磺化", "磺酸", "SO3H"], "第七章 芳香烃"),
    T("芳烃卤代反应", "halogenation of aromatic hydrocarbons", "芳香烃反应", "苯环在 Lewis 酸催化下与卤素发生亲电取代生成卤代芳烃。", "常用 FeBr3、FeCl3、AlCl3 等促进卤素极化。", "卤素取代基虽钝化芳环，但定位为邻、对位。", "卤素是特殊定位基：吸电子诱导使其钝化，孤对共轭使其邻对位定位。", ["芳烃卤代", "FeBr3", "FeCl3"], "第七章 芳香烃"),
    T("Friedel-Crafts 烷基化", "Friedel-Crafts alkylation", "芳香烃反应", "芳环在 Lewis 酸作用下与卤代烃等反应引入烷基。", "反应可能经碳正离子或类似活性物种，易发生重排和多烷基化。", "用于构建烷基苯，但对强钝化芳环常不适用。", "烷基化最常见坑：重排、多取代、芳环太钝不反应。", ["Friedel-Crafts", "烷基化", "傅克"], "第七章 芳香烃"),
    T("Friedel-Crafts 酰基化", "Friedel-Crafts acylation", "芳香烃反应", "芳环与酰卤或酸酐在 Lewis 酸作用下反应生成芳香酮。", "酰基正离子或其等价体是关键亲电体，通常不发生碳链重排。", "用于合成芳香酮，产物酰基钝化芳环，一般不易多酰基化。", "酰基化比烷基化更可控，常用于先酰化再还原得到烷基苯。", ["酰基化", "Friedel-Crafts", "芳香酮"], "第七章 芳香烃"),
    T("芳环定位效应", "directing effect in benzene substitution", "活性顺序", "已有取代基通过电子效应影响新的亲电取代进入邻对位或间位。", "给电子基多为邻、对位定位并活化；强吸电子基多为间位定位并钝化。", "用于预测二取代苯主要产物和芳环反应速度。", "定位和活性要分开答：卤素邻对位定位但总体钝化。", ["定位效应", "邻对位", "间位"], "第七章 芳香烃"),
    T("芳环反应活性顺序", "reactivity order of substituted benzenes", "活性顺序", "芳环电子云密度越高，亲电取代通常越快；强吸电子基会显著降低活性。", "常见趋势：强给电子基活化 > 烷基苯 > 苯 > 卤苯 > 含硝基、羰基、磺酸基等钝化芳环。", "用于判断芳香亲电取代的快慢、条件强弱和主产物。", "做题时先分活化/钝化，再分邻对/间定位。", ["芳环活性", "活化", "钝化", "反应活性"], "第七章 芳香烃"),
    T("卤代烃亲核取代", "nucleophilic substitution of halohydrocarbons", "卤代烃反应", "卤代烃中 C-X 键极化，碳带部分正电，可被亲核体进攻发生取代。", "常见机制为 SN1 和 SN2，受底物结构、亲核体、溶剂和离去基影响。", "用于将卤代烃转化为醇、醚、腈、胺等。", "先判断底物是甲基/伯/仲/叔，再看亲核体强弱和溶剂。", ["卤代烃", "亲核取代", "SN1", "SN2"], "第八章 卤代烃"),
    T("SN1 反应", "SN1 reaction", "卤代烃反应", "单分子亲核取代反应，速率主要取决于底物生成碳正离子的能力。", "通常有两步：离去基先离去形成碳正离子，亲核体再进攻。", "叔卤代烃、苄基或烯丙基卤代物在极性质子溶剂中较易发生。", "SN1 可能外消旋化，也可能发生碳正离子重排。", ["SN1", "碳正离子", "亲核取代"], "第八章 卤代烃"),
    T("SN2 反应", "SN2 reaction", "卤代烃反应", "双分子亲核取代反应，亲核体背面进攻并同时挤出离去基。", "速率与底物和亲核体浓度有关，位阻越小越有利。", "甲基和伯卤代烷最适合 SN2，产物构型通常发生 Walden 反转。", "强亲核体、小位阻、极性非质子溶剂有利于 SN2。", ["SN2", "背面进攻", "构型反转"], "第八章 卤代烃"),
    T("消除反应", "elimination reaction", "卤代烃反应", "底物失去相邻原子或基团形成不饱和键的反应。", "卤代烃可发生脱卤化氢形成烯烃，常见机制包括 E1 和 E2。", "与亲核取代竞争，受底物、碱、溶剂和温度影响。", "强碱、高温、位阻大时更要考虑消除。", ["消除", "E1", "E2", "脱卤化氢"], "第八章 卤代烃"),
    T("卤代烃水解活性顺序", "hydrolysis reactivity of alkyl halides", "活性顺序", "卤代烃水解活性受 C-X 键强度、离去基能力、底物结构和机制共同影响。", "同类烷基中常见离去基趋势 RI > RBr > RCl >> RF；SN1 底物常 3° > 2° > 1°，SN2 则位阻小更快。", "用于比较卤代烃取代反应速率和选择合成条件。", "不要背一个万能顺序，要先判机制：SN1 看碳正离子，SN2 看位阻和亲核体。", ["卤代烃", "水解", "活性顺序"], "第八章 卤代烃"),
    T("乙烯基和芳基卤代烃惰性", "low reactivity of vinyl and aryl halides", "卤代烃反应", "乙烯基卤和芳基卤的 C-X 键因 sp2 碳和共轭作用较强，通常不易发生普通亲核取代。", "卤素直接连在双键碳或芳环碳上，C-X 键具有部分双键性。", "用于区分卤代烷、烯丙基/苄基卤和芳基/乙烯基卤的反应性。", "看到氯苯不要按普通氯代烷处理，它通常不能轻易水解。", ["乙烯基卤代烃", "芳基卤代烃", "惰性"], "第八章 卤代烃"),
    T("醇的分类", "classification of alcohols", "醇酚醚", "按羟基所连碳原子连接的烃基数目，醇可分为伯醇、仲醇和叔醇。", "伯醇 RCH2OH，仲醇 R2CHOH，叔醇 R3COH。", "醇的分类直接影响氧化、脱水和 Lucas 试验速度。", "醇的反应活性常要先判断伯、仲、叔。", ["伯醇", "仲醇", "叔醇", "醇"], "第九章 醇、硫醇、酚"),
    T("Lucas 试验", "Lucas test", "鉴别反应", "浓盐酸和无水氯化锌组成 Lucas 试剂，可根据浑浊速度鉴别低级伯、仲、叔醇。", "叔醇迅速浑浊，仲醇较慢，伯醇常温下通常很慢或不明显。", "用于根据取代程度判断醇类型。", "Lucas 试验适合低级可溶醇；高碳醇溶解性差会干扰现象。", ["Lucas", "卢卡斯", "氯化锌", "醇鉴别"], "第九章 醇、硫醇、酚"),
    T("醇氧化活性顺序", "oxidation order of alcohols", "活性顺序", "醇是否易氧化取决于羟基碳上是否有氢。", "伯醇可氧化为醛再到酸，仲醇可氧化为酮，叔醇通常不易被普通氧化剂氧化。", "用于预测醇氧化产物和鉴别伯、仲、叔醇。", "记住关键：没有 α-H 的叔醇不容易普通氧化。", ["醇氧化", "伯醇", "仲醇", "叔醇", "活性顺序"], "第九章 醇、硫醇、酚"),
    T("醇脱水反应", "dehydration of alcohols", "醇酚醚", "醇在酸性条件和加热下可脱水生成烯烃或醚。", "分子内脱水生成烯烃，分子间脱水可生成醚；条件和底物结构决定方向。", "用于由醇制备烯烃或醚。", "脱水成烯烃常遵循生成更稳定烯烃的倾向，并可能重排。", ["醇脱水", "烯烃", "醚"], "第九章 醇、硫醇、酚"),
    T("醇成酯反应", "esterification of alcohols", "醇酚醚", "醇与羧酸、酰卤、酸酐等反应生成酯。", "酸催化羧酸酯化为可逆反应，酰卤和酸酐酰化通常更活泼。", "用于连接羧酸和醇，也是理解脂类、磷脂和糖苷衍生物的基础。", "判断酯化效率时，羧酸衍生物活性顺序很重要。", ["酯化", "醇", "酯"], "第九章 醇、硫醇、酚"),
    T("酚的酸性", "acidity of phenols", "醇酚醚", "酚羟基可电离，酸性强于脂肪醇但弱于羧酸。", "酚氧负离子可通过芳环共振分散负电荷；吸电子基增强酚酸性。", "用于区分酚、醇和羧酸，也影响酚的成盐和取代反应。", "酚能与 NaOH 成盐，普通醇通常不能；酚一般不能与 NaHCO3 放 CO2。", ["酚", "酸性", "酚氧负离子"], "第九章 醇、硫醇、酚"),
    T("三氯化铁鉴别酚", "ferric chloride test for phenols", "鉴别反应", "多数酚类与 FeCl3 溶液形成有色配合物，出现紫、蓝、绿等颜色。", "显色来自酚氧负离子与铁离子的配位。", "用于鉴别酚羟基，尤其是与普通醇区分。", "不是所有酚显色都相同，且烯醇类也可能显色。", ["三氯化铁", "FeCl3", "酚", "鉴别"], "第九章 醇、硫醇、酚"),
    T("溴水鉴别酚", "bromine water test for phenols", "鉴别反应", "苯酚等活化芳环可与溴水迅速反应，常生成白色 2,4,6-三溴苯酚沉淀并使溴水褪色。", "酚羟基强烈活化芳环并使邻、对位易发生取代。", "用于鉴别活泼酚类化合物。", "溴水褪色也可能来自不饱和键，看到白色沉淀更支持苯酚。", ["溴水", "酚", "白色沉淀", "鉴别"], "第九章 醇、硫醇、酚"),
    T("醚过氧化物鉴别", "peroxide test for ethers", "鉴别反应", "含 α-H 的醚久置空气中可形成过氧化物，可用酸性 KI-淀粉试纸检验。", "过氧化物能把 I- 氧化为 I2，碘遇淀粉呈蓝色。", "用于蒸馏醚前安全检查。", "醚类蒸馏不要蒸干；检出过氧化物应先用还原剂处理。", ["醚", "过氧化物", "KI", "淀粉", "鉴别"], "第十章 醚和环氧化合物"),
    T("环氧化合物开环", "ring opening of epoxides", "醇酚醚", "环氧化合物因三元环张力大，易受亲核试剂进攻开环。", "酸性条件下亲核体多进攻取代较多碳，碱性条件下多进攻位阻较小碳。", "用于合成邻二醇、氨基醇、醚醇等。", "酸开环看类 SN1 稳定性，碱开环看 SN2 位阻。", ["环氧", "开环", "酸催化", "碱性"], "第十章 醚和环氧化合物"),
    T("胺碱性顺序", "basicity order of amines", "活性顺序", "胺的碱性取决于氮上孤对电子接受质子的能力。", "脂肪胺通常比氨强；芳香胺因孤对电子与苯环共轭，碱性明显降低。", "用于比较胺、苯胺、吡啶、吡咯等含氮化合物。", "水溶液中还要考虑溶剂化，不能只看烷基给电子。", ["胺", "碱性", "苯胺", "吡啶", "顺序"], "第十一章 胺和生物碱"),
    T("胺的酰化反应", "acylation of amines", "胺和生物碱", "伯胺和仲胺可与酰卤或酸酐反应生成酰胺。", "叔胺没有 N-H，通常不能形成普通酰胺，但可作为碱捕获酸。", "用于保护氨基、合成酰胺，也可辅助区分胺类。", "酰化后氮孤对电子与羰基共轭，碱性大幅降低。", ["胺", "酰化", "酰胺"], "第十一章 胺和生物碱"),
    T("芳香伯胺重氮化", "diazotization of aromatic primary amines", "胺和生物碱", "芳香伯胺在低温酸性条件下与亚硝酸作用生成重氮盐。", "常用 NaNO2/HCl 原位生成 HNO2，温度通常控制在 0-5 ℃。", "重氮盐可用于 Sandmeyer 反应和偶联反应。", "脂肪伯胺和芳香伯胺遇亚硝酸现象不同，注意反应条件和稳定性。", ["重氮化", "芳香伯胺", "亚硝酸"], "第十一章 胺和生物碱"),
    T("偶联反应", "azo coupling reaction", "胺和生物碱", "芳香重氮盐与活化芳环发生偶联生成偶氮化合物。", "酚和芳胺等富电子芳环常在对位或邻位偶联，生成有色偶氮染料。", "用于制备偶氮染料，也可作为芳香胺衍生反应。", "偶联需要芳环足够活化，pH 对酚和芳胺偶联很重要。", ["偶联", "重氮盐", "偶氮"], "第十一章 胺和生物碱"),
    T("生物碱沉淀反应", "alkaloid precipitation reactions", "鉴别反应", "许多生物碱具有碱性，可与某些酸性沉淀试剂形成难溶盐或配合物。", "常见沉淀试剂包括苦味酸、碘化铋钾、碘化汞钾等。", "用于生物碱的初步检识。", "沉淀反应是初筛，不等于结构鉴定；需结合其他方法确认。", ["生物碱", "沉淀", "鉴别"], "第十一章 胺和生物碱"),
    T("羰基亲核加成", "nucleophilic addition to carbonyl", "醛酮反应", "醛、酮的 C=O 键极化，羰基碳带正电性，易被亲核体进攻。", "反应可生成醇、氰醇、半缩醛、肟、腙等产物。", "是醛酮最核心的反应类型，也是糖化学和生物羰基反应的基础。", "先让亲核体进攻羰基碳，再处理氧负离子质子化。", ["羰基", "亲核加成", "醛", "酮"], "第十二章 醛和酮"),
    T("醛酮反应活性顺序", "reactivity order of aldehydes and ketones", "活性顺序", "羰基亲核加成活性受电子效应和空间位阻影响。", "一般脂肪醛 > 芳香醛 > 脂肪酮 > 芳香酮；甲醛通常最活泼。", "用于判断加成反应速率和选择性。", "醛比酮活泼主要因为位阻更小、烷基给电子更少。", ["醛酮", "羰基", "活性顺序"], "第十二章 醛和酮"),
    T("半缩醛和缩醛", "hemiacetal and acetal", "醛酮反应", "醛或酮与醇加成生成半缩醛，进一步在酸催化下生成缩醛。", "糖的环状结构本质上常含半缩醛或半缩酮。", "缩醛在碱性条件较稳定，酸性条件可水解，可用于保护羰基。", "糖类里看到端基碳，想半缩醛和变旋光。", ["半缩醛", "缩醛", "糖"], "第十二章 醛和酮"),
    T("2,4-二硝基苯肼试验", "2,4-DNPH test", "鉴别反应", "醛、酮与 2,4-二硝基苯肼反应生成黄色、橙色或红色腙沉淀。", "反应属于羰基与含氮亲核试剂的加成-脱水。", "用于鉴别醛酮羰基。", "羧酸、酯、酰胺通常不呈普通 DNPH 阳性。", ["2,4-二硝基苯肼", "DNPH", "醛酮", "鉴别"], "第十二章 醛和酮"),
    T("Tollens 试剂银镜反应", "Tollens silver mirror test", "鉴别反应", "醛和部分还原糖可还原 Tollens 试剂，生成银镜或黑色银沉淀。", "醛被氧化为羧酸盐，银氨络离子被还原为金属银。", "用于鉴别醛与多数酮，也用于判断还原糖。", "甲酸和部分 α-羟基酮也可能阳性，不能机械地等同于醛。", ["Tollens", "银镜", "醛", "还原糖", "鉴别"], "第十二章 醛和酮"),
    T("Fehling 和 Benedict 反应", "Fehling and Benedict tests", "鉴别反应", "脂肪醛和还原糖可在碱性铜试剂中还原 Cu2+，生成砖红色 Cu2O 沉淀。", "芳香醛通常较难使 Fehling 试剂阳性。", "用于鉴别脂肪醛和还原糖。", "糖类题中，能开链形成醛基或 α-羟基酮结构的糖常表现还原性。", ["Fehling", "Benedict", "砖红色", "还原糖"], "第十二章 醛和酮"),
    T("碘仿反应", "iodoform reaction", "鉴别反应", "甲基酮或能被氧化为甲基酮的醇与 I2/NaOH 反应生成黄色碘仿沉淀。", "乙醇和含 CH3CHOH- 结构的仲醇也可阳性。", "用于鉴别甲基酮、乙醛、乙醇及相关结构。", "黄色、有特殊气味的 CHI3 沉淀是关键词。", ["碘仿", "iodoform", "甲基酮", "黄色沉淀"], "第十二章 醛和酮"),
    T("醛酮还原", "reduction of aldehydes and ketones", "醛酮反应", "醛、酮可被还原剂还原为相应醇。", "醛通常还原为伯醇，酮还原为仲醇；催化氢化或金属氢化物均可实现。", "用于羰基到醇的官能团转化。", "反应前后碳骨架不变，羰基碳变成醇碳。", ["醛", "酮", "还原", "醇"], "第十二章 醛和酮"),
    T("羟醛缩合", "aldol condensation", "醛酮反应", "含 α-H 的醛或酮在碱或酸催化下形成 β-羟基醛/酮，并可进一步脱水。", "关键是 α-H 酸性和烯醇/烯醇负离子形成。", "用于形成新的 C-C 键。", "先找 α-H；没有 α-H 的羰基化合物不能作自身羟醛缩合供体。", ["羟醛缩合", "α-H", "醛酮"], "第十二章 醛和酮"),
    T("羧酸酸性顺序", "acidity order of carboxylic acids", "活性顺序", "羧酸酸性来自羧酸根负离子的共振稳定，取代基会进一步调节酸性。", "吸电子基增强酸性，给电子基减弱酸性；吸电子基越近影响越强。", "用于比较脂肪酸、芳香酸、卤代酸、羟基酸等酸性。", "比较取代羧酸时看取代基吸/给电子能力和距离。", ["羧酸", "酸性", "取代羧酸", "顺序"], "第十三章 羧酸和取代羧酸"),
    T("羧酸成盐与碳酸氢钠鉴别", "bicarbonate test for carboxylic acids", "鉴别反应", "羧酸可与 NaHCO3 反应生成羧酸盐并放出 CO2 气泡。", "酚酸性通常不足以与 NaHCO3 明显放 CO2。", "用于区分羧酸与酚、醇等弱酸性化合物。", "有气泡是羧酸鉴别的核心现象，但也要排除其他可放气的酸性物质。", ["羧酸", "碳酸氢钠", "气泡", "鉴别"], "第十三章 羧酸和取代羧酸"),
    T("羧酸酯化反应", "esterification of carboxylic acids", "羧酸及衍生物", "羧酸与醇在酸催化下可逆生成酯和水。", "提高醇或酸浓度、移去水或产物可推动平衡向酯生成方向移动。", "是合成酯、理解脂类和药物前体的重要反应。", "Fischer 酯化是平衡反应，不是单向到底。", ["羧酸", "酯化", "Fischer"], "第十三章 羧酸和取代羧酸"),
    T("羧酸脱羧", "decarboxylation", "羧酸及衍生物", "羧酸或其衍生物失去 CO2 的反应。", "β-酮酸、丙二酸类化合物等较易脱羧。", "用于解释体内代谢和有机合成中的碳链缩短。", "易脱羧结构通常能形成稳定过渡态或稳定产物。", ["脱羧", "CO2", "羧酸"], "第十三章 羧酸和取代羧酸"),
    T("α-羟基酸氧化", "oxidation of alpha-hydroxy acids", "羧酸及衍生物", "α-羟基酸中的羟基受邻近羧基影响，比普通醇羟基更易被氧化。", "Tollens 试剂等通常不氧化普通醇，却可氧化某些 α-羟基酸。", "用于理解乳酸、苹果酸等生物相关羟基酸的反应性。", "羧基的 -I 效应增强邻位羟基相关反应。", ["α-羟基酸", "氧化", "Tollens"], "第十三章 羧酸和取代羧酸"),
    T("羧酸衍生物反应活性顺序", "reactivity order of carboxylic acid derivatives", "活性顺序", "羧酸衍生物的酰基取代活性主要取决于离去基能力和羰基亲电性。", "常见顺序：酰卤 > 酸酐 > 酯 ≈ 羧酸 > 酰胺；酰胺因氮给电子共轭最不活泼。", "用于选择酰化试剂、判断水解和醇解难易。", "衍生物互相转化一般从高活性到低活性更容易。", ["羧酸衍生物", "酰卤", "酸酐", "酯", "酰胺", "活性顺序"], "第十四章 羧酸衍生物"),
    T("酰卤", "acid halide", "羧酸及衍生物", "羧酸羟基被卤素取代形成的高活性羧酸衍生物。", "酰氯最常见，易水解、醇解、氨解生成酸、酯、酰胺。", "常用作酰化试剂。", "酰氯遇水敏感，反应常需要无水条件或碱捕酸。", ["酰卤", "酰氯", "羧酸衍生物"], "第十四章 羧酸衍生物"),
    T("酸酐", "acid anhydride", "羧酸及衍生物", "两个羧酸分子脱水或羧酸与无机酸形成的酸酐。", "酸酐可与醇、胺、水反应生成酯、酰胺或羧酸。", "乙酸酐常用作乙酰化试剂。", "酸酐活性低于酰氯但高于酯，反应更温和可控。", ["酸酐", "乙酸酐", "酰化"], "第十四章 羧酸衍生物"),
    T("酯水解", "hydrolysis of esters", "羧酸及衍生物", "酯在酸或碱条件下水解生成羧酸和醇，碱性水解又称皂化。", "酸性水解可逆，碱性水解因生成羧酸盐而较完全。", "用于脂类水解、药物酯键代谢和合成转化。", "皂化不可简单当作普通可逆酯化的逆反应，因为羧酸盐形成推动反应。", ["酯", "水解", "皂化"], "第十四章 羧酸衍生物"),
    T("酰胺", "amide", "羧酸及衍生物", "羧酸衍生物中羟基被氨基或取代氨基替换形成的化合物。", "氮孤对电子与羰基共轭，使酰胺 C-N 键具有部分双键性。", "酰胺键是蛋白质肽键的化学基础。", "酰胺最不活泼，水解通常需要较强酸、强碱或酶催化。", ["酰胺", "amide", "肽键"], "第十四章 羧酸衍生物"),
    T("异羟肟酸铁试验", "hydroxamic acid test", "鉴别反应", "酯与羟胺反应生成异羟肟酸，再与 Fe3+ 形成紫红色络合物。", "用于某些酯类和酰基衍生物的检识。", "可作为酯类化合物的特定鉴别反应之一。", "不同底物反应速度不同，实验条件会影响显色。", ["异羟肟酸", "Fe3+", "酯", "鉴别"], "第十四章 羧酸衍生物"),
    T("吡咯、呋喃和噻吩", "pyrrole, furan and thiophene", "杂环化合物", "含 N、O、S 的五元芳杂环，杂原子孤对电子参与芳香体系。", "环上电子云密度通常高于苯，易发生亲电取代，主要在 α 位。", "是许多天然产物和药物结构的基本单元。", "吡咯碱性很弱，因为氮孤对电子参与芳香性。", ["吡咯", "呋喃", "噻吩", "杂环"], "第十五章 杂环化合物"),
    T("吡啶碱性", "basicity of pyridine", "杂环化合物", "吡啶氮的孤对电子不参与芳香 sextet，可接受质子，表现弱碱性。", "吡啶比脂肪胺弱碱，但比吡咯明显更碱。", "用于比较含氮杂环在生理和药物环境中的质子化状态。", "吡咯的孤对电子在芳香体系里，吡啶的孤对电子在环平面内，这是核心差别。", ["吡啶", "碱性", "吡咯"], "第十五章 杂环化合物"),
    T("杂环亲电取代定位", "electrophilic substitution of heterocycles", "杂环化合物", "富电子五元杂环的亲电取代通常优先发生在 α 位。", "α 位取代形成的中间体可有更多稳定共振式。", "用于预测吡咯、呋喃、噻吩硝化、卤代等反应产物。", "吡咯和呋喃遇强酸容易破坏芳香体系，条件要温和。", ["杂环", "亲电取代", "α位"], "第十五章 杂环化合物"),
    T("皂化", "saponification", "生物有机", "油脂在碱性条件下水解生成甘油和脂肪酸盐的反应。", "脂肪酸钠盐或钾盐就是肥皂的主要成分。", "用于理解油脂水解、肥皂制备和酯的碱性水解。", "皂化本质是酯的碱性水解。", ["皂化", "油脂", "酯水解"], "第十六章 类脂化合物"),
    T("碘值", "iodine value", "生物有机", "碘值表示一定量油脂能吸收碘的量，反映不饱和程度。", "双键越多，能加成卤素越多，碘值越高。", "用于比较脂肪酸或油脂的不饱和程度。", "碘值高通常说明不饱和脂肪酸比例高。", ["碘值", "油脂", "不饱和"], "第十六章 类脂化合物"),
    T("酸值", "acid value", "生物有机", "酸值表示中和一定量油脂中游离脂肪酸所需 KOH 的量。", "油脂酸败会增加游离脂肪酸含量，使酸值升高。", "用于评价油脂质量和水解酸败程度。", "酸值看游离酸，碘值看不饱和。", ["酸值", "油脂", "脂肪酸"], "第十六章 类脂化合物"),
    T("Libermann-Burchard 反应", "Libermann-Burchard reaction", "鉴别反应", "甾醇类化合物与乙酸酐和浓硫酸作用可出现红、紫、褐、绿色等颜色变化。", "胆固醇常用该反应鉴别。", "用于甾醇类化合物的特定检识。", "颜色变化序列是记忆点，但实验条件会影响色调。", ["Libermann-Burchard", "胆固醇", "甾醇", "鉴别"], "第十六章 类脂化合物"),
    T("还原糖", "reducing sugar", "糖类", "能在溶液中形成游离醛基或 α-羟基酮结构并还原弱氧化剂的糖。", "葡萄糖、果糖、麦芽糖等通常有还原性；蔗糖因两个端基都成苷键而无还原性。", "可用 Tollens、Fehling、Benedict 等反应鉴别。", "果糖虽是酮糖，但在碱性条件下可异构化而呈还原性。", ["还原糖", "Fehling", "Tollens", "糖"], "第十七章 糖类"),
    T("变旋光现象", "mutarotation", "糖类", "糖溶液中 α、β 端基异构体经开链形式相互转化，使旋光度随时间变化并达到平衡。", "具有游离半缩醛羟基的糖常有变旋光现象。", "用于判断糖是否保留还原端。", "没有游离端基的糖苷通常不显示变旋光。", ["变旋光", "端基异构", "糖"], "第十七章 糖类"),
    T("苷键", "glycosidic bond", "糖类", "糖的端基羟基与醇、酚、糖或其他基团脱水形成的键。", "苷键形成后端基碳被锁定，可能失去还原性和变旋光。", "是二糖、多糖、核苷等结构的关键连接方式。", "判断还原糖时看是否还有游离半缩醛羟基。", ["苷键", "glycosidic", "糖苷"], "第十七章 糖类"),
    T("糖类 Fehling/Tollens 鉴别", "reducing sugar tests", "鉴别反应", "还原糖可使 Fehling 试剂生成砖红色 Cu2O，也可发生 Tollens 银镜反应。", "非还原糖如蔗糖通常阴性，水解后可转为阳性。", "用于区分还原糖和非还原糖。", "判断二糖还原性时看参与苷键的端基碳是否都被占用。", ["还原糖", "Fehling", "Tollens", "银镜", "砖红色"], "第十七章 糖类"),
    T("淀粉碘反应", "iodine test for starch", "鉴别反应", "淀粉遇碘显蓝色或蓝紫色。", "碘分子进入直链淀粉螺旋空腔形成有色包合物。", "用于鉴别淀粉，也可观察淀粉水解程度。", "加热颜色可减弱，冷却后可恢复。", ["淀粉", "碘", "蓝色", "鉴别"], "第十七章 糖类"),
    T("Seliwanoff 反应", "Seliwanoff test", "鉴别反应", "酮糖在强酸中脱水较快，可与间苯二酚显红色。", "果糖等酮糖反应较快，醛糖反应较慢。", "用于区分酮糖和醛糖的经典鉴别。", "时间控制很关键，久置醛糖也可能显色。", ["Seliwanoff", "酮糖", "果糖", "鉴别"], "第十七章 糖类"),
    T("氨基酸两性电解质", "amphoteric amino acid", "氨基酸与蛋白质", "氨基酸同时含氨基和羧基，可表现酸性和碱性。", "在水溶液中常以内盐或两性离子形式存在。", "解释氨基酸溶解性、等电点和电泳行为。", "写氨基酸状态时要看 pH，而不是固定写中性分子。", ["氨基酸", "两性", "内盐"], "第十八章 氨基酸、多肽和蛋白质"),
    T("等电点", "isoelectric point", "氨基酸与蛋白质", "氨基酸或蛋白质净电荷为零时溶液的 pH。", "pH 低于等电点时整体偏正电，高于等电点时整体偏负电。", "用于解释蛋白质沉淀、电泳和分离。", "等电点附近溶解度常较低，容易沉淀。", ["等电点", "pI", "氨基酸"], "第十八章 氨基酸、多肽和蛋白质"),
    T("茚三酮反应", "ninhydrin reaction", "鉴别反应", "多数 α-氨基酸与茚三酮反应生成蓝紫色物质。", "脯氨酸等亚氨基酸常显黄色。", "用于氨基酸和肽的显色检识。", "茚三酮是氨基酸题最常见的显色反应。", ["茚三酮", "ninhydrin", "氨基酸", "鉴别"], "第十八章 氨基酸、多肽和蛋白质"),
    T("双缩脲反应", "biuret reaction", "鉴别反应", "含两个或两个以上肽键的化合物在碱性 Cu2+ 条件下呈紫色。", "蛋白质和多肽通常阳性，游离氨基酸通常阴性。", "用于鉴别蛋白质或多肽。", "看的是肽键数量，不是单个氨基酸。", ["双缩脲", "biuret", "肽键", "蛋白质"], "第十八章 氨基酸、多肽和蛋白质"),
    T("黄蛋白反应", "xanthoproteic reaction", "鉴别反应", "含芳香环的氨基酸或蛋白质遇浓硝酸可发生硝化而显黄色。", "酪氨酸、色氨酸、苯丙氨酸等芳香族氨基酸相关结构可阳性。", "用于提示蛋白质中芳香族氨基酸残基。", "黄色反应不能说明蛋白总量，只提示芳香环结构。", ["黄蛋白", "浓硝酸", "芳香族氨基酸"], "第十八章 氨基酸、多肽和蛋白质"),
    T("蛋白质变性", "protein denaturation", "氨基酸与蛋白质", "蛋白质空间结构被破坏而理化性质和生物活性改变的过程。", "高温、强酸强碱、有机溶剂、重金属盐等可导致变性。", "解释消毒、沉淀、酶失活和重金属中毒等现象。", "变性通常不破坏一级结构肽键，水解才断肽键。", ["蛋白质", "变性", "重金属"], "第十八章 氨基酸、多肽和蛋白质"),
    T("核苷酸", "nucleotide", "核酸", "由碱基、戊糖和磷酸组成的核酸基本单位。", "核苷是碱基加戊糖，核苷酸是在核苷基础上再连磷酸。", "用于理解 DNA、RNA、ATP 和辅酶结构。", "核苷和核苷酸不要混：有没有磷酸是关键。", ["核苷酸", "核苷", "磷酸"], "第十九章 核酸"),
    T("磷酸二酯键", "phosphodiester bond", "核酸", "核酸链中一个核苷酸 3'-羟基与另一个核苷酸 5'-磷酸形成的连接键。", "核酸链具有 5' 端和 3' 端方向性。", "决定 DNA、RNA 主链结构和序列书写方向。", "核酸序列通常从 5' 端写到 3' 端。", ["磷酸二酯键", "5'", "3'", "核酸"], "第十九章 核酸"),
    T("DNA 与 RNA 稳定性差异", "stability difference between DNA and RNA", "核酸", "RNA 因核糖 2'-羟基存在，在碱性条件下较易发生分子内反应而断链。", "DNA 缺少 2'-羟基，化学稳定性通常高于 RNA。", "解释遗传信息长期储存多由 DNA 承担，而 RNA 更适合短期功能和调控。", "记忆点：RNA 多一个 2'-OH，所以更活泼、更不稳定。", ["DNA", "RNA", "稳定性", "2'-羟基"], "第十九章 核酸"),
    T("反应活性顺序总览", "organic reactivity order overview", "活性顺序", "把常考的有机反应活性顺序集中比较，避免孤立背诵。", "核心包括碳正离子、自由基、芳环活化、卤代烃取代、醛酮加成、羧酸衍生物酰基取代、醇氧化和胺碱性。", "用于做选择题、推主产物、判断反应条件强弱和设计合成路线。", "先判机制，再套顺序；机制不同，同一底物顺序可能反过来。", ["活性顺序", "反应活性", "总览", "比较"], "第一章 绪论"),
    T("特定鉴别反应总览", "specific identification reactions overview", "鉴别反应", "把有机化学中用试剂和现象鉴别官能团的反应集中整理。", "常见包括溴水、KMnO4、端炔银盐、Lucas、FeCl3、Tollens、Fehling、DNPH、碘仿、茚三酮、双缩脲、淀粉碘反应等。", "用于实验鉴别题和官能团推断题。", "鉴别反应要记三件事：试剂、阳性现象、能排除或混淆的对象。", ["鉴别反应", "试剂", "现象", "官能团"], "第三章 有机化合物的结构鉴定"),
]


def find_organic_pdf() -> Path:
    desktop = Path.home() / "Desktop"
    candidates = [path for path in desktop.glob("*.pdf") if path.name.startswith("04.")]
    if not candidates:
        candidates = [path for path in desktop.glob("*.pdf") if "有机" in path.name]
    if not candidates:
        raise FileNotFoundError("No organic chemistry PDF found on Desktop.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = re.sub(r"\s+", " ", value.replace("\u3000", " ")).strip()
    return value


def norm(value: str) -> str:
    return clean_text(value).lower().replace(" ", "")


def extract_pages(pdf_path: Path) -> list[dict[str, Any]]:
    pages = []
    with pdfplumber.open(pdf_path) as doc:
        for index, page in enumerate(doc.pages, start=1):
            text = clean_text(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            book_page = index - PDF_PAGE_OFFSET
            if book_page < 1 or book_page > 258 or not text:
                continue
            pages.append(
                {
                    "pdfPage": index,
                    "bookPage": book_page,
                    "text": text,
                    "norm": norm(text),
                }
            )
    return pages


def chapter_for_page(book_page: int) -> dict[str, str]:
    chapter = CHAPTERS[0]
    for item in CHAPTERS:
        if book_page >= item["start"]:
            chapter = item
        else:
            break
    return chapter


def chapter_by_name(name: str) -> dict[str, str]:
    for item in CHAPTERS:
        if item["name"] == name:
            return item
    return CHAPTERS[0]


def chapter_range(name: str) -> tuple[int, int]:
    chapter = chapter_by_name(name)
    start = int(chapter["start"])
    starts = [int(item["start"]) for item in CHAPTERS if int(item["start"]) > start]
    end = min(starts) - 1 if starts else 258
    return start, end


def context_snippet(text: str, keyword: str, limit: int = 220) -> str:
    compact = clean_text(text)
    pos = norm(compact).find(norm(keyword))
    if pos == -1:
        return compact[:limit]
    rough = max(0, min(len(compact), pos) - 70)
    snippet = compact[rough : rough + limit].strip()
    return snippet


def find_hits(spec: dict[str, Any], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keywords = [spec["zh"], spec["en"], *spec["keywords"]]
    start, end = chapter_range(spec["chapter"])
    chapter_pages = [page for page in pages if start <= page["bookPage"] <= end]
    scored = []
    for page in chapter_pages:
        score = 0
        matched = ""
        for keyword in keywords:
            key = norm(keyword)
            if not key:
                continue
            if key in page["norm"]:
                score += 5 if keyword in (spec["zh"], spec["en"]) else 2
                if not matched:
                    matched = keyword
        if score:
            scored.append((score, page["bookPage"], matched, page))
    scored.sort(key=lambda item: (-item[0], item[1]))
    hits = []
    seen = set()
    for _, _, matched, page in scored:
        if page["bookPage"] in seen:
            continue
        seen.add(page["bookPage"])
        hits.append(
            {
                "bookPage": page["bookPage"],
                "pdfPage": page["pdfPage"],
                "matched": matched or spec["zh"],
                "text": context_snippet(page["text"], matched or spec["zh"]),
            }
        )
        if len(hits) >= 3:
            break
    return hits


def fallback_hit(spec: dict[str, Any]) -> dict[str, Any]:
    chapter = chapter_by_name(spec["chapter"])
    book_page = int(chapter["start"])
    return {
        "bookPage": book_page,
        "pdfPage": book_page + PDF_PAGE_OFFSET,
        "matched": spec["zh"],
        "text": f"{chapter['name']}相关知识点：{spec['definition']}",
    }


def build_terms(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    built = []
    for index, spec in enumerate(TERMS, start=1):
        hits = find_hits(spec, pages) or [fallback_hit(spec)]
        first = hits[0]
        chapter = chapter_for_page(first["bookPage"])
        pages_found = sorted({hit["bookPage"] for hit in hits})
        pdf_pages = sorted({hit["pdfPage"] for hit in hits})
        term = {
            "id": f"oc{index:04d}",
            "zh": spec["zh"],
            "en": spec["en"],
            "category": spec["category"],
            "part": chapter["part"],
            "parts": [chapter["part"]],
            "chapters": [chapter["name"]],
            "pages": pages_found,
            "pdfPages": pdf_pages,
            "firstPage": first["bookPage"],
            "firstPdfPage": first["pdfPage"],
            "occurrences": len(hits),
            "confidence": 0.94,
            "confidenceLabel": "高",
            "definition": spec["definition"],
            "structure": spec["structure"],
            "location": spec["structure"],
            "function": spec["function"],
            "studyNote": spec["studyNote"],
            "figures": [],
            "pageFigures": [],
            "pageImages": [f"assets/pages/organic/pdf-{hit['pdfPage']:03d}.jpg" for hit in hits],
            "contexts": [
                {
                    "part": chapter_for_page(hit["bookPage"])["part"],
                    "chapter": chapter_for_page(hit["bookPage"])["name"],
                    "bookPage": hit["bookPage"],
                    "pdfPage": hit["pdfPage"],
                    "text": hit["text"],
                }
                for hit in hits
            ],
            "sources": [{"type": "pdf", "name": "有机化学（第10版）", "pdfPage": first["pdfPage"], "bookPage": first["bookPage"]}],
            "relatedTerms": [],
        }
        built.append(term)

    assign_related_terms(built)
    return built


def assign_related_terms(terms: list[dict[str, Any]]) -> None:
    tokens_by_id = {}
    for term, spec in zip(terms, TERMS):
        tokens = set(spec["keywords"])
        tokens.update([term["category"], term["part"], *term["chapters"]])
        tokens.update(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", term["zh"] + " " + term["en"]))
        tokens_by_id[term["id"]] = {norm(token) for token in tokens if len(norm(token)) >= 2}

    for term in terms:
        scores = []
        own = tokens_by_id[term["id"]]
        for other in terms:
            if other["id"] == term["id"]:
                continue
            overlap = len(own & tokens_by_id[other["id"]])
            if other["category"] == term["category"]:
                overlap += 2
            if other["chapters"][0] == term["chapters"][0]:
                overlap += 1
            if overlap:
                scores.append((overlap, other["id"]))
        scores.sort(key=lambda item: (-item[0], item[1]))
        term["relatedTerms"] = [item[1] for item in scores[:10]]


def write_glossary(payload: dict[str, Any]) -> None:
    GLOSSARY_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    GLOSSARY_JS.write_text("window.MED_GLOSSARY = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    with GLOSSARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["课程", "篇", "中文", "English", "分类", "章节", "书页", "PDF页", "解释", "结构/分布", "功能/意义", "相关词条", "关联图", "置信度"])
        for course in payload.get("courses", []):
            terms_by_id = {term["id"]: term for term in course.get("terms", [])}
            for term in course.get("terms", []):
                related = " / ".join(terms_by_id[item]["zh"] for item in term.get("relatedTerms", []) if item in terms_by_id)
                figures = " / ".join([*term.get("figures", []), *term.get("pageFigures", []), *term.get("pageImages", [])])
                writer.writerow(
                    [
                        course.get("title", ""),
                        term.get("part", ""),
                        term.get("zh", ""),
                        term.get("en", ""),
                        term.get("category", ""),
                        " / ".join(term.get("chapters", [])),
                        ", ".join(str(page) for page in term.get("pages", [])),
                        ", ".join(str(page) for page in term.get("pdfPages", [])),
                        term.get("definition", ""),
                        term.get("structure") or term.get("location", ""),
                        term.get("function", ""),
                        related,
                        figures,
                        term.get("confidenceLabel", ""),
                    ]
                )
    report = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "courses": [
            {
                "id": course["id"],
                "title": course["title"],
                "terms": len(course.get("terms", [])),
                "figures": len(course.get("figures", [])),
            }
            for course in payload.get("courses", [])
        ],
        "totalTerms": sum(len(course.get("terms", [])) for course in payload.get("courses", [])),
        "totalFigures": sum(len(course.get("figures", [])) for course in payload.get("courses", [])),
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def build_course(pdf_path: Path) -> dict[str, Any]:
    pages = extract_pages(pdf_path)
    terms = build_terms(pages)
    category_counts = Counter(term["category"] for term in terms)
    return {
        "id": "organic-chemistry",
        "title": "有机化学",
        "shortTitle": "有机化学",
        "description": "围绕官能团性质、反应机制、鉴别反应、活性顺序和生物有机化合物建立的知识点词库。",
        "parts": PARTS,
        "chapters": CHAPTERS,
        "figures": [],
        "terms": terms,
        "meta": {
            "sourcePdf": pdf_path.name,
            "pageOffset": PDF_PAGE_OFFSET,
            "totalTerms": len(terms),
            "totalFigures": 0,
            "categoryCounts": dict(sorted(category_counts.items())),
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
        },
    }


def main() -> None:
    payload = json.loads(GLOSSARY_JSON.read_text(encoding="utf-8"))
    pdf_path = find_organic_pdf()
    course = build_course(pdf_path)
    courses = [item for item in payload.get("courses", []) if item.get("id") != course["id"]]
    courses.append(course)
    payload["courses"] = courses
    payload.setdefault("meta", {})
    payload["meta"]["totalCourses"] = len(courses)
    payload["meta"]["totalTerms"] = sum(len(item.get("terms", [])) for item in courses)
    payload["meta"]["totalFigures"] = sum(len(item.get("figures", [])) for item in courses)
    write_glossary(payload)
    print(f"added {len(course['terms'])} organic chemistry terms from {pdf_path}")


if __name__ == "__main__":
    main()
