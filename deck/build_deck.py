# -*- coding: utf-8 -*-
"""初賽簡報 v0。文案與數字集中在本檔前半；不要在這裡重算統計。

重跑：python deck/build_deck.py
模板：attachments/2026和泰AI黑客松＿初賽簡報模板.pptx
輸出：deck/初賽簡報_v0.pptx、deck/README.md；若本機有 PowerPoint，另匯 deck/preview/
"""

from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deck" / "初賽簡報_v0.pptx"
README = ROOT / "deck" / "README.md"
PREVIEW = ROOT / "deck" / "preview"
FIG = ROOT / "reports" / "figures"

# 模板配色（theme1.xml）。占位用較深的橘，白底上才讀得清楚。
INK = RGBColor(0x24, 0x32, 0x3E)
NAVY = RGBColor(0x44, 0x54, 0x6A)
BLUE = RGBColor(0x2F, 0x5D, 0x9F)
MUTED = RGBColor(0x5C, 0x6B, 0x7A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xC0, 0x56, 0x00)  # 占位字色

ML = 0.46
CW = 12.42
FOOTER_Y = 7.16


def zi(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


# ---------------------------------------------------------------------------
# 文案。數字只轉抄報告，不在這裡計算。
# 態度負面 61%：任務大綱如此寫。專案架構 §0.1 寫 68%，T7 只給流失率 4.7%。
# v0 依大綱放 61%，README 列為待核，不另算。
# ---------------------------------------------------------------------------

NOTES = [
    "題三初賽：公開輿情裡，每六位售後發言就有一位在找出口。",
    "摘要先給評審：對象是售後決策者，模型在本機，話術還等目標值。",
    "先講規模感：六個人裡有一個在找出路，而且多數沒有先抱怨。",
    "決策者現在靠客訴才知道流失，我們要用輿情把時間往前拉。",
    "真正送走人的是等料和價格，態度罵很多，人卻還留著。",
    "出口在一般外廠；定保口述中位原廠九千、外廠三千五，不是公告價。",
    "三站切完是二十三萬句，售後兩萬一千句，遮蔽五百多次、抽查沒漏。",
    "八層從爬文走到接觸點，判斷在自己的顯卡上，資料不用出門。",
    "四種人裡過保精算最多；靜默出走沒有抱怨，分群也單獨撐得住。",
    "高風險七成四真有流失句；輿情訊號怎麼對上 CRM，這格還空著。",
    "兩段式補上漏標，Dcard 換模型複核，重疊句一致率達百分之九十八。",
    "四Ｂ模型只吐機率、不寫句子，八Ｇ顯卡五小時練完，一句零點七秒。",
    "別人看不到不抱怨就走的人；我們給規則和機率，每句都能回原句。",
    "四種人配三種進廠時機，話還沒寫，價格保固只能引用知識庫。",
    "模型與語料做得到；要守住的是樣本偏誤、個資，還有生成亂編。",
    "延遲和Ｆ１已經有現況，業務回廠率與導入週數都還是空格。",
    "程式在私有庫，報告從Ｔ１到Ｔ１１，畫面截圖等決賽再補。",
]

SUMMARY_RIGHT = {
    "team": [[("回廠率研究所", INK, True)]],
    "product": [[("Lexus車主流失預警與 AI 溝通系統", INK, True)]],
    "challenge": [[("AI 流失風險洞察與智慧溝通：打造Lexus車主忠誠度的終極防線", INK, False)]],
    "audience": [[("Lexus 售後服務部門決策者與服務廠客戶關係人員", INK, False)]],
    "design": [
        [("1. 從公開輿情 21,183 句售後語料自動標註流失意圖與九大面向，找出 4 種流失 Persona。", INK, False)],
        [("2. 本機自訓 System-One 決策模型即時給出流失機率與可解釋規則，作者層級高／中／低分級。", INK, False)],
        [("3. Persona × 接觸點的 RAG 關懷內容生成，價格與保固只引用官方知識庫並經人工審核。", INK, False)],
    ],
    "ai": [[(
        "Claude Haiku／Sonnet 兩段式標註、GPT-5.6 Sol 複核、Qwen3-4B QLoRA 自訓 prefill-only 決策模型"
        "（LLM2Jev 架構，本機 8 GB 顯卡）、K-means 分群、RAG（官方保修知識庫）、統計檢定（χ²、勝算比、Wilson CI）",
        INK,
        False,
    )]],
    "benefit": [[
        ("【待補：KPI 目標值】", ORANGE, True),
        ("（框架：高風險車主關懷觸達率、過保後回廠率、留存率；每句判斷 0.7 秒、零 API 費）", INK, False),
    ]],
}

# 每頁：章節標、結論標題、來源（寫進頁腳與 README）、圖檔
SLIDES = [
    {
        "id": "P1",
        "section": "1 提案概述",
        "title": "每 6 位在論壇談 Lexus 售後的車主，就有 1 位已在找出口，而且大多沒有抱怨",
        "source": "來源：reports/T7_stats_tests.md、reports/T3_residual_split_report.md",
        "reports": ["reports/T7_stats_tests.md", "reports/T3_residual_split_report.md"],
        "figures": [],
    },
    {
        "id": "P2",
        "section": "2 目標對象與痛點分析",
        "title": "售後現在是人走了才知道，公開輿情可以把時間往前拉",
        "source": "來源：reports/T7_stats_tests.md；圖 F2",
        "reports": ["reports/T7_stats_tests.md"],
        "figures": ["reports/figures/F2.png"],
    },
    {
        "id": "P3",
        "section": "2 目標對象與痛點分析",
        "title": "等料和價格才把人送走；態度抱怨很多，人卻很少真的離開",
        "source": "來源：reports/T7_stats_tests.md；圖 F1",
        "reports": ["reports/T7_stats_tests.md"],
        "figures": ["reports/figures/F1.png"],
    },
    {
        "id": "P4",
        "section": "2 目標對象與痛點分析",
        "title": "人主要去一般外廠；過保之後，口述價差把人推出去",
        "source": "來源：reports/T10_risk_persona_report.md（F3）、專案架構 §0.1、reports/T11_kb_prices_report.md",
        "reports": [
            "reports/T10_risk_persona_report.md",
            "專案架構_2026-09-23.md",
            "reports/T11_kb_prices_report.md",
        ],
        "figures": ["reports/figures/F3.png"],
    },
    {
        "id": "P5",
        "section": "2 目標對象與痛點分析",
        "title": "三站售後語料已經齊，品質門檻過了，句子也去過識別",
        "source": "來源：題目選擇分析 §6.5、reports/T7_data_quality.md、reports/T7_deid_report.md",
        "reports": [
            "題目選擇分析_2026-09-22.md",
            "reports/T7_data_quality.md",
            "reports/T7_deid_report.md",
        ],
        "figures": [],
    },
    {
        "id": "P6",
        "section": "3 解決方案設計",
        "title": "從蒐集到接觸點都在本機：判斷不用上雲，資料也不出門",
        "source": "來源：專案架構_2026-09-23.md §2",
        "reports": ["專案架構_2026-09-23.md"],
        "figures": [],
    },
    {
        "id": "P7",
        "section": "3 解決方案設計",
        "title": "四種流失樣貌裡，最多的是過保之後還在算價格的人",
        "source": "來源：reports/T10_risk_persona_report.md §6（例句為去識別版）",
        "reports": ["reports/T10_risk_persona_report.md"],
        "figures": [],
    },
    {
        "id": "P8",
        "section": "3 解決方案設計",
        "title": "高風險作者七成四真的有流失句，低風險只有百分之一點八",
        "source": "來源：reports/T10_risk_persona_report.md §2；圖 F4",
        "reports": ["reports/T10_risk_persona_report.md"],
        "figures": ["reports/figures/F4.png"],
    },
    {
        "id": "P9",
        "section": "4 AI 應用方法",
        "title": "先寬鬆抓住，再帶上下文複核；九個面向已經全量標完",
        "source": "來源：專案架構 §2、reports/T1_dcard_verify_report.md、T2、T3",
        "reports": [
            "專案架構_2026-09-23.md",
            "reports/T1_dcard_verify_report.md",
            "reports/T2_other_refine_report.md",
            "reports/T3_residual_split_report.md",
        ],
        "figures": [],
    },
    {
        "id": "P10",
        "section": "4 AI 應用方法",
        "title": "本機 4B 比雲端 Haiku 更會把流失句找回來，而且不生成文字",
        "source": "來源：reports/T8_r4_report.md；圖 F6",
        "reports": ["reports/T8_r4_report.md", "專案架構_2026-09-23.md"],
        "figures": ["reports/figures/F6.png"],
    },
    {
        "id": "P11",
        "section": "5 獨特優勢與差異化",
        "title": "靜默出走別隊看不到；分數說得出是哪條規則，也能回到原句",
        "source": "來源：reports/T10_risk_persona_report.md、reports/T8_r4_report.md、專案架構 §2",
        "reports": [
            "reports/T10_risk_persona_report.md",
            "reports/T8_r4_report.md",
            "專案架構_2026-09-23.md",
        ],
        "figures": [],
    },
    {
        "id": "P12",
        "section": "6 預期效益與落地評估",
        "title": "先對上是誰、在什麼時候開口；話術範例還等 Sprint 3",
        "source": "來源：專案架構 §2 L6–L7、knowledge/lexus_aftersales_kb.md（40 條）",
        "reports": ["專案架構_2026-09-23.md", "knowledge/lexus_aftersales_kb.md"],
        "figures": [],
    },
    {
        "id": "P13",
        "section": "6 預期效益與落地評估",
        "title": "技術與語料已在手上；要守的是代表性、個資，和生成亂編",
        "source": "來源：iPAS導入對照_2026-09-25.md §2.1–2.2",
        "reports": ["iPAS導入對照_2026-09-25.md"],
        "figures": [],
    },
    {
        "id": "P14",
        "section": "6 預期效益與落地評估",
        "title": "延遲和判準已有現況；業務目標與導入週數都還沒填",
        "source": "來源：iPAS導入對照_2026-09-25.md §2.4；現況數字見 T8、T10",
        "reports": [
            "iPAS導入對照_2026-09-25.md",
            "reports/T8_r4_report.md",
            "reports/T10_risk_persona_report.md",
        ],
        "figures": [],
    },
    {
        "id": "P15",
        "section": "7 補充資料",
        "title": "報告、模型紀錄與程式都在；畫面截圖留到決賽",
        "source": "來源：本 repo reports/T1–T11；GitHub 私有庫",
        "reports": ["reports/"],
        "figures": [],
    },
]

LAYERS = [
    ("L0", "蒐集", "三站公開論壇已爬完"),
    ("L1", "前處理", "合併、切句、去重，留下售後句"),
    ("L2", "標註", "流失、九面向、替代與車主特徵"),
    ("L3", "決策模型", "本機 QLoRA，只輸出各等級機率"),
    ("L4", "風險辨識", "八條規則乘上 r4 的流失機率"),
    ("L5", "Persona", "規則指派四種流失樣貌"),
    ("L6", "RAG 生成", "價格與保固只引用官方知識庫"),
    ("L7", "接觸點", "審核後投遞，並把 KPI 寫回去"),
]

PERSONAS = [
    ("過保精算派", "511 人", "39.9%", "價格句 48%，走向一般外廠與自備料", "「去外面換就好，原廠換很貴，外面四顆全換12000有找」"),
    ("品質失望派", "247 人", "19.3%", "技術品質 43%，替代裡看得到換車", "「原廠處理不好就去外場」"),
    ("口碑建議者", "195 人", "15.2%", "立場「建議他人」占 61%，會把別人帶走", "「電瓶、輪胎都不用在原廠換」"),
    ("靜默出走者", "128 人", "10.0%", "沒有抱怨；替代有 55% 是一般外廠", "「可以去外面民間保養廠」"),
]

SIGNALS = [
    ("R1", "過保"),
    ("R2", "價格負面"),
    ("R3", "找出口"),
    ("R4", "自理"),
    ("R5", "零件等料"),
    ("R6", "品質失望"),
    ("R7", "已離開"),
    ("R8", "帶人走"),
]

ADVANTAGES = [
    ("靜默出走者", "別隊若只看客訴，看不到這群沒抱怨就離開的人。"),
    ("機率可解釋", "輸出各等級機率，並標出命中的規則，不是一顆黑箱分數。"),
    ("本機就能跑", "CRM 資料不能出門。8 GB 顯卡可訓可推，零 API 費。"),
    ("數字回得去", "每個比率有檢定或區間，也能回到去識別原句。"),
]

TOUCH_COLS = ["保固到期前 60 天", "回廠間隔拉長", "刪項後首次回廠"]
PH_SPRINT = "【待補：Sprint 3 生成範例】"
PH_CRM = "【待補：B 的 PB-08】"
CRM_MAP = {
    "R1": "保固到期日（4 年／12 萬）、延保購買狀態：到期前 90 天未購延保",
    "R2": "工單估價 vs 實收、拒絕估價項目、滿意度價格題：連續 2 次拒項",
    "R3": "回廠間隔 vs 建議週期、預約取消、App 查據點未預約：逾期 1.5 倍",
    "R4": "工單自備零件／機油註記、只做換油套餐、金額逐次下降 > 40%",
    "R5": "零件待料天數、待料改期次數：待料 > 7 天或同車 ≥ 2 次",
    "R6": "30 天內同項目重複進廠、技術客訴、召回未完成：comeback ≥ 2",
    "R7": "12 個月無工單、過戶／退出會員、App 長期未開啟（驗證用）",
    "R8": "NPS 貶損者（0–6）且 12 個月內有客訴、推薦計畫無紀錄",
}
PH_WEEKS = "【待補：週數】"
PH_TARGET = "【待補：目標值】"


def template_path() -> Path:
    found = list((ROOT / "attachments").glob("*初賽簡報模板.pptx"))
    if len(found) != 1:
        raise SystemExit(f"模板數量不對：{found}")
    return found[0]


def style_run(run, size_pt: float, bold: bool, color: RGBColor) -> None:
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = False
    run.font.color.rgb = color
    run.font.name = "Arial"
    r_pr = run._r.get_or_add_rPr()
    for tag, face in (("a:latin", "Arial"), ("a:ea", "微軟正黑體"), ("a:cs", "Arial")):
        el = r_pr.find(qn(tag))
        if el is None:
            el = etree.SubElement(r_pr, qn(tag))
        el.set("typeface", face)


def set_tf(tf, blocks, size: float, align=None, anchor: str = "t") -> None:
    tf.clear()
    tf.word_wrap = True
    body_pr = tf._txBody.bodyPr
    body_pr.set("anchor", anchor)
    for i, runs in enumerate(blocks):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align is not None:
            p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(2)
        p.line_spacing = 1.0
        for item in runs:
            text, color, bold = item[0], item[1], item[2]
            sz = item[3] if len(item) > 3 else size
            run = p.add_run()
            run.text = text
            style_run(run, sz, bold, color)


def add_text(slide, x, y, w, h, blocks, size=14, align=None, anchor="t", margin=0.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    set_tf(tf, blocks, size, align, anchor)
    return box


def add_card(slide, x, y, w, h, fill="F4F7FB"):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    try:
        shape.adjustments[0] = 0.08
    except Exception:
        pass
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background()
    return shape


def set_cell_fill(cell, hex_color: str) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    for child in list(tc_pr):
        if child.tag == qn("a:solidFill"):
            tc_pr.remove(child)
    solid = etree.SubElement(tc_pr, qn("a:solidFill"))
    srgb = etree.SubElement(solid, qn("a:srgbClr"))
    srgb.set("val", hex_color)


def paint_cell(cell, blocks, size, fill, align=None) -> None:
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Inches(0.08)
    cell.margin_right = Inches(0.06)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.03)
    set_tf(cell.text_frame, blocks, size, align, anchor="ctr")
    set_cell_fill(cell, fill)
    cell.text_frame.word_wrap = True


def add_table(slide, x, y, w, h, rows, col_w, font=12, header=True):
    """rows: list of list of blocks (each cell is a list of paragraphs)."""
    n_r, n_c = len(rows), len(rows[0])
    graphic = slide.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(w), Inches(h))
    table = graphic.table
    for i, cw in enumerate(col_w):
        table.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        for c, blocks in enumerate(row):
            header_cell = header and r == 0
            flat = "".join(run[0] for para in blocks for run in para)
            orange = (not header_cell) and "【待補：" in flat
            if header_cell:
                fill, color = "44546A", WHITE
                blocks = [[(flat, WHITE, True)]]
            elif orange and flat.startswith("【待補：") and flat.endswith("】"):
                blocks = [[(flat, ORANGE, True)]]
                fill = "FDEBD0"
            elif orange:
                fill = "FDEBD0"
            elif r % 2 == 0:
                fill = "F7F9FB"
            else:
                fill = "FFFFFF"
            paint_cell(table.cell(r, c), blocks, font, "44546A" if header_cell else fill)
    return graphic


def cell_text(text, color=INK, bold=False):
    return [[(text, color, bold)]]


def delete_slide(prs, index: int) -> None:
    sld_id_lst = prs.slides._sldIdLst
    sld_id = sld_id_lst[index]
    r_id = sld_id.get(qn("r:id"))
    prs.part.drop_rel(r_id)
    sld_id_lst.remove(sld_id)


def blank_layout(prs):
    for layout in prs.slide_layouts:
        if layout.name == "BLANK":
            return layout
    raise RuntimeError("模板沒有 BLANK 版面")


def strip_placeholders(slide) -> None:
    for shape in list(slide.placeholders):
        element = shape._element
        element.getparent().remove(element)


def chrome(slide, section: str, page: int, source: str) -> None:
    add_text(
        slide, ML, 0.10, 9.2, 0.26,
        [[(section, NAVY, False)]],
        size=12, margin=0.0,
    )
    add_text(
        slide, ML, FOOTER_Y, 10.3, 0.24,
        [[(source, MUTED, False)]],
        size=10, margin=0.0,
    )
    add_text(
        slide, 11.35, FOOTER_Y, 1.52, 0.24,
        [[(str(page), NAVY, False)]],
        size=12, align=PP_ALIGN.RIGHT, margin=0.0,
    )


def add_title(slide, text: str) -> float:
    size = 20 if len(text) > 28 else 24
    height = 0.92 if len(text) > 28 else 0.62
    add_text(
        slide, ML, 0.36, CW, height,
        [[(text, INK, True)]],
        size=size, margin=0.0,
    )
    return 0.36 + height + 0.10


def new_content_slide(prs, meta: dict, page: int):
    slide = prs.slides.add_slide(blank_layout(prs))
    strip_placeholders(slide)
    chrome(slide, meta["section"], page, meta["source"])
    y = add_title(slide, meta["title"])
    return slide, y


def fill_summary(slide) -> None:
    table = None
    for shape in slide.shapes:
        if shape.has_table:
            table = shape.table
            break
    if table is None or len(table.rows) != 7 or len(table.columns) != 2:
        raise RuntimeError("摘要表格不是 7×2")
    left_before = [table.cell(i, 0).text for i in range(7)]
    keys = ["team", "product", "challenge", "audience", "design", "ai", "benefit"]
    heights = [0.40, 0.52, 0.52, 0.46, 1.48, 0.98, 0.72]
    total_h = 0
    for i, key in enumerate(keys):
        cell = table.cell(i, 1)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        set_tf(cell.text_frame, SUMMARY_RIGHT[key], 12, anchor="ctr")
        table.rows[i].height = Inches(heights[i])
        total_h += heights[i]
    for shape in slide.shapes:
        if shape.has_table:
            shape.height = Inches(total_h)
            break
    left_after = [table.cell(i, 0).text for i in range(7)]
    if left_before != left_after:
        raise RuntimeError(f"摘要左欄被改到：{left_after}")


def pic(slide, name: str, x, y, w) -> float:
    path = FIG / name
    height = w * 900 / 1920
    slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(height))
    return height


def build_p1(slide, y):
    rates = [("18.2%", "Mobile01", "作者流失率最高"), ("14.1%", "PTT", "介於兩者之間"), ("6.8%", "Dcard", "作者流失率最低")]
    gap = 0.16
    card_w = (CW - 2 * gap) / 3
    for i, (num, name, note) in enumerate(rates):
        x = ML + i * (card_w + gap)
        add_card(slide, x, y, card_w, 1.85)
        add_text(
            slide, x + 0.12, y + 0.16, card_w - 0.24, 1.55,
            [
                [(num, BLUE, True, 36)],
                [(name, INK, True, 16)],
                [(note, MUTED, False, 13)],
            ],
            size=14,
        )
    lines_y = y + 2.05
    lines = [
        "作者層級 χ²=99.5，p<.001（Cramér's V=0.125）。母體是論壇發言者，不是全體車主。",
        "靜默出走：1,671 句流失裡，186 句沒有痛點訊號，只是在找出口。",
        "方案：提早辨識、分成 Persona、在對的接觸點說對的話。",
    ]
    add_text(
        slide, ML, lines_y, CW, 1.35,
        [[(line, INK, False, 16)] for line in lines],
        size=16,
    )


def build_p2(slide, y):
    left_w = 5.55
    add_card(slide, ML, y, left_w, 1.55)
    add_text(
        slide, ML + 0.16, y + 0.12, left_w - 0.32, 1.32,
        [
            [("As-Is", BLUE, True, 14)],
            [("只靠客訴與回廠紀錄，人流失之後才知道。", INK, False, 15)],
        ],
        size=15,
    )
    add_card(slide, ML, y + 1.72, left_w, 1.55)
    add_text(
        slide, ML + 0.16, y + 1.84, left_w - 0.32, 1.32,
        [
            [("To-Be", BLUE, True, 14)],
            [("公開輿情加上 CRM 訊號，在離開之前先辨識。", INK, False, 15)],
        ],
        size=15,
    )
    add_text(
        slide, ML, y + 3.42, left_w, 0.85,
        [[("使用者是售後決策者，以及服務廠的客戶關係人員。誤差線是 Wilson 95% CI。", MUTED, False, 13)]],
        size=13,
    )
    pic(slide, "F2.png", ML + left_w + 0.2, y, 6.65)


def build_p3(slide, y):
    width = 9.2
    h = pic(slide, "F1.png", ML + (CW - width) / 2, y, width)
    lines = [
        "零件供應 17.3%（勝算比 2.58）、價格 15.0%（勝算比 2.64），是流失率最高的兩面向。",
        "銷售交車 1.4%（勝算比 0.15）最低。分母是全部 21,183 句。",
        "態度負面 61%，流失卻只有 4.7%：抱怨多，不等於人會走。",
    ]
    add_text(
        slide, ML, y + h + 0.02, CW, 1.15,
        [[(line, INK, False, 15)] for line in lines],
        size=15,
    )


def build_p4(slide, y):
    width = 9.2
    h = pic(slide, "F3.png", ML + (CW - width) / 2, y, width)
    lines = [
        "一般外廠 736、自備料 234、DIY 135。一句可以多選，母體是 1,671 句流失。",
        "標得到保固狀態的流失句：過保 62，保固內 17。",
        "口述中位，不是定價：定保原廠 9,000 對外廠 3,500；機油 5,000 對 1,950。",
    ]
    add_text(
        slide, ML, y + h + 0.02, CW, 1.15,
        [[(line, INK, False, 15)] for line in lines],
        size=15,
    )


def build_p5(slide, y):
    scale_rows_l = ["項目", "三站文章", "留言／樓層", "切句去重後", "售後句", "流失句 c≥2"]
    scale_rows_r = ["數量", "5,765 篇", "225,157（22.5 萬）", "235,775（23.6 萬）", "21,183", "1,671"]
    qual_l = ["指標（售後句）", "關鍵欄缺失率", "重複率", "一致性率", "異常值率", "完整性率"]
    qual_r = ["結果", "0.00%", "0.00%", "100%", "7.77%", "100%"]
    def pairs(labels, values):
        out = []
        for i, (a, b) in enumerate(zip(labels, values)):
            if i == 0:
                out.append([cell_text(a, WHITE, True), cell_text(b, WHITE, True)])
            else:
                out.append([cell_text(a), cell_text(b)])
        return out

    add_table(slide, ML, y, 6.05, 3.15, pairs(scale_rows_l, scale_rows_r), [3.15, 2.90], font=13)
    add_table(slide, ML + 6.35, y, 6.07, 3.15, pairs(qual_l, qual_r), [3.35, 2.72], font=13)
    add_text(
        slide, ML, y + 3.30, CW, 0.85,
        [[("去識別：文本遮蔽 517 次。抽查 50 句（seed 42）漏網 0。簡報例句只用去識別版，不出現論壇帳號。", INK, False, 14)]],
        size=14,
    )
    add_text(
        slide, ML, y + 4.22, CW, 0.40,
        [[("異常值是字數超過 Q3+1.5×IQR 的句子，門檻 78 字，占 7.77%。上游已先去掉 15,182 句重複。", MUTED, False, 12)]],
        size=12,
    )


def build_p6(slide, y):
    gap_x, gap_y = 0.14, 0.14
    card_w = (CW - 3 * gap_x) / 4
    card_h = 2.15
    for i, (code, name, sentence) in enumerate(LAYERS):
        col, row = i % 4, i // 4
        x = ML + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        add_card(slide, x, yy, card_w, card_h)
        add_text(
            slide, x + 0.12, yy + 0.16, card_w - 0.24, card_h - 0.28,
            [
                [(code, BLUE, True, 18)],
                [(name, INK, True, 16)],
                [(sentence, NAVY, False, 13)],
            ],
            size=13,
        )


def build_p7(slide, y):
    gap = 0.14
    card_w = (CW - 3 * gap) / 4
    card_h = 3.05
    for i, (name, people, share, feature, quote) in enumerate(PERSONAS):
        x = ML + i * (card_w + gap)
        add_card(slide, x, y, card_w, card_h)
        add_text(
            slide, x + 0.10, y + 0.12, card_w - 0.20, card_h - 0.22,
            [
                [(name, INK, True, 15)],
                [(people, BLUE, True, 26)],
                [(share, NAVY, False, 14)],
                [(feature, INK, False, 12)],
                [(quote, NAVY, False, 12)],
            ],
            size=12,
        )
    add_text(
        slide, ML, y + card_h + 0.08, CW, 0.55,
        [[("規則指派，分母是高／中風險 1,280 人。另有未分類 199 人（15.5%）。分群只獨立支持靜默出走者（78% 在同一群）。", MUTED, False, 12)]],
        size=12,
    )


def build_p8(slide, y):
    add_text(
        slide, ML, y, 6.35, 1.15,
        [
            [("分數＝作者 p_churn 最大值 × 0.6 ＋（命中規則數／8）× 0.4。", INK, False, 13)],
            [("高 1,049／中 231／低 5,114。", INK, True, 16)],
            [("高風險作者 74% 有流失句，低風險 1.8%。", INK, False, 14)],
        ],
        size=14,
    )
    pic(slide, "F4.png", ML + 6.55, y, 5.85)
    header = [cell_text(h, WHITE, True) for h in ("規則", "輿情訊號", "CRM 欄位")]
    body = []
    body.append(header)
    for code, signal in SIGNALS:
        body.append([
            cell_text(code),
            cell_text(signal),
            cell_text(CRM_MAP.get(code.split()[0], PH_CRM), INK if code.split()[0] in CRM_MAP else ORANGE, code.split()[0] not in CRM_MAP),
        ])
    add_table(slide, ML, y + 2.85, CW, 2.45, body, [1.3, 2.4, 8.72], font=10)
    add_text(slide, ML, y + 5.35, CW, 0.35,
             [[("CRM 欄位為業界通用假設，導入時以和泰 DMS 實際欄位替換；模型輸入由論壇文字改為工單備註與客訴文字，架構不變。", MUTED, False, 10)]], size=10)


def build_p9(slide, y):
    steps = [
        ("1", "Haiku 初篩", "單獨召回約 57%，先把可能流失的句子留住"),
        ("2", "帶上下文複核", "Mobile01、PTT 用 Sonnet；Dcard 5,355 句用 GPT-5.6 Sol"),
        ("3", "對得起來", "重疊 3,760 句，c≥2 一致率 98.4%"),
    ]
    gap = 0.16
    card_w = (CW - 2 * gap) / 3
    for i, (n, head, body) in enumerate(steps):
        x = ML + i * (card_w + gap)
        add_card(slide, x, y, card_w, 1.70)
        add_text(
            slide, x + 0.14, y + 0.12, card_w - 0.28, 1.46,
            [
                [(n + "  " + head, BLUE, True, 16)],
                [(body, INK, False, 13)],
            ],
            size=13,
        )
    lines = [
        "同時標九個面向、替代選項，和車主特徵（車型、是否過保）。",
        "流失原因裡標成「其他」的 396 句再細分；真正沒有原因的殘餘剩 4 句。",
    ]
    add_text(
        slide, ML, y + 1.90, CW, 0.85,
        [[(line, INK, False, 16)] for line in lines],
        size=16,
    )
    add_card(slide, ML, y + 2.90, CW, 0.85, fill="FDEBD0")
    add_text(
        slide, ML + 0.16, y + 3.02, CW - 0.32, 0.62,
        [[("【待補：人工標註 300 句 A/B κ 與三模型對人工指標（9/29）】", ORANGE, True, 15)]],
        size=15, anchor="ctr",
    )


def build_p10(slide, y):
    headers = ["", "P", "R", "F1", "κ"]
    haiku = ["Haiku 零樣本", "0.60", "0.55", "0.58", "0.53"]
    r4 = ["r4　4B", "0.62", "0.77", "0.685", "0.64"]
    rows = []
    for i, row in enumerate((headers, haiku, r4)):
        rows.append([cell_text(v, WHITE, True) if i == 0 else cell_text(v, INK, c == 0) for c, v in enumerate(row)])
    add_table(slide, ML, y, 6.15, 1.35, rows, [2.15, 1.0, 1.0, 1.0, 1.0], font=13)
    add_text(
        slide, ML, y + 1.48, 6.15, 0.45,
        [[("同一 600 句測試集。r4 原值 P 0.617、R 0.769、κ 0.642（T8 ep2）。", MUTED, False, 11)]],
        size=11,
    )
    lines = [
        "Prefill-only：只輸出各等級機率，不生成文字。",
        "8 GB 顯卡可訓（約 5 小時）、可推（每句 0.7 秒）。",
        "資料不出門，推論零 API 費。",
    ]
    add_text(
        slide, ML, y + 2.00, 6.15, 1.35,
        [[(line, INK, False, 14)] for line in lines],
        size=14,
    )
    pic(slide, "F6.png", ML + 6.40, y, 6.00)


def build_p11(slide, y):
    gap_x, gap_y = 0.16, 0.16
    card_w = (CW - gap_x) / 2
    card_h = 2.05
    for i, (head, body) in enumerate(ADVANTAGES):
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        add_card(slide, x, yy, card_w, card_h)
        add_text(
            slide, x + 0.18, yy + 0.22, card_w - 0.36, card_h - 0.36,
            [
                [(head, BLUE, True, 18)],
                [(body, INK, False, 15)],
            ],
            size=15,
        )


def build_p12(slide, y):
    header = [cell_text("Persona", WHITE, True)] + [cell_text(c, WHITE, True) for c in TOUCH_COLS]
    rows = [header]
    for name, *_rest in PERSONAS:
        rows.append([cell_text(name, INK, True)] + [cell_text(PH_SPRINT, ORANGE, True) for _ in TOUCH_COLS])
    add_table(slide, ML, y, CW, 2.55, rows, [2.15, 3.42, 3.42, 3.43], font=12)
    add_text(
        slide, ML, y + 2.70, CW, 0.85,
        [
            [("觸發 → 判 Persona → 生成 → 人工審核 → 投遞 → KPI 回饋。", INK, False, 15)],
            [("知識庫已備 40 條。價格與保固只引用有 URL 的條目，不能拿口述中位數當官方定價。", INK, False, 14)],
        ],
        size=14,
    )


def build_p13(slide, y):
    left_w = 5.85
    items = [
        ("需求", "只靠客訴與回廠才知道流失，改成輿情加 CRM 提前辨識。"),
        ("技術", "監督分類、分群、RAG 都有原型。CRM 欄位對照仍空著。"),
        ("財務", "推論零 API 費，本機 8 GB 可跑。"),
        ("風險", "代表性、雙模型、個資、生成幻覺。對策在右表。"),
    ]
    for i, (head, body) in enumerate(items):
        yy = y + i * 1.18
        add_card(slide, ML, yy, left_w, 1.08)
        blocks = [
            [(head, BLUE, True, 14)],
            [(body, INK, False, 13)],
        ]
        if head == "財務":
            blocks.append([("【待補：成本與回收期】", ORANGE, True, 13)])
        add_text(slide, ML + 0.14, yy + 0.08, left_w - 0.28, 0.94, blocks, size=13)
    risks = [
        ("風險", "對策"),
        ("兩個複核模型並存", "揭露。重疊 3,760 句，c≥2 一致率 98.4%"),
        ("論壇代表性", "母體是論壇發言者，不是全體車主"),
        ("個資與再識別", "遮蔽 517 次；抽查 50 句漏網 0"),
        ("生成幻覺", "價格與保固只引用知識庫，並人工審核"),
    ]
    rows = []
    for i, (a, b) in enumerate(risks):
        if i == 0:
            rows.append([cell_text(a, WHITE, True), cell_text(b, WHITE, True)])
        else:
            rows.append([cell_text(a, INK, True), cell_text(b)])
    add_table(slide, ML + 6.05, y, 6.37, 4.55, rows, [2.35, 4.02], font=12)


def build_p14(slide, y):
    headers = ["層級", "現況", "目標"]
    data = [
        ("系統", "延遲每句 0.7 秒；可用率見右", "【待補：目標值】"),
        ("應用", "F1 0.685、κ 0.64；校準見 F6", "【待補：目標值】"),
        ("業務", "觸達率、過保後回廠率、留存率", "【待補：目標值】"),
    ]
    # 可用率與業務現況沒有數字，放占位。用混合儲存格會讓整格掃描仍抓得到。
    rows = [[cell_text(h, WHITE, True) for h in headers]]
    rows.append([
        cell_text("系統"),
        [[("每句 0.7 秒。可用率 ", INK, False), ("【待補：可用率現況】", ORANGE, True)]],
        cell_text(PH_TARGET, ORANGE, True),
    ])
    rows.append([
        cell_text("應用"),
        cell_text("F1 0.685、κ 0.64；校準見 P10 的 F6"),
        cell_text(PH_TARGET, ORANGE, True),
    ])
    rows.append([
        cell_text("業務"),
        cell_text("【待補：業務現況】", ORANGE, True),
        cell_text(PH_TARGET, ORANGE, True),
    ])
    add_table(slide, ML, y, CW, 1.85, rows, [1.6, 6.5, 4.32], font=13)
    phases = ["問題定義", "資料準備與標註", "模型訓練", "驗證", "部署"]
    gap = 0.12
    card_w = (CW - 4 * gap) / 5
    base = y + 2.15
    for i, name in enumerate(phases):
        x = ML + i * (card_w + gap)
        add_card(slide, x, base, card_w, 1.85)
        add_text(
            slide, x + 0.08, base + 0.14, card_w - 0.16, 1.58,
            [
                [(str(i + 1), BLUE, True, 18)],
                [(name, INK, True, 13)],
                [(PH_WEEKS, ORANGE, True, 12)],
            ],
            size=12,
        )


def build_p15(slide, y):
    add_card(slide, ML, y, CW, 1.35)
    add_text(
        slide, ML + 0.16, y + 0.12, CW - 0.32, 1.12,
        [
            [("GitHub（private，評審需要時開）", NAVY, False, 12)],
            [("https://github.com/xxx789666/hotai-ai-hackathon-lexus", BLUE, True, 16)],
        ],
        size=14,
    )
    reports = [
        "T1　Dcard 複核（c≥2 一致率 98.4%）",
        "T2　「其他」396 句細分",
        "T3　靜默出走 186 句；殘餘 4 句",
        "T4　LLM2Jev 試點",
        "T5–T6　QLoRA 診斷（未採用）",
        "T7　品質、去識別、統計檢定",
        "T8　r4 決策模型（F1 0.685）",
        "T10　風險分級與四個 Persona",
        "T11　口述價格（非官方定價）",
        "T9　人工評估尚未產出（見 P9）",
    ]
    gap = 0.12
    card_w = (CW - gap) / 2
    for i, line in enumerate(reports):
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap)
        yy = y + 1.52 + row * 0.58
        add_card(slide, x, yy, card_w, 0.50, fill="F7F9FB")
        add_text(
            slide, x + 0.12, yy + 0.06, card_w - 0.2, 0.38,
            [[(line, INK, False, 13)]],
            size=13, anchor="ctr",
        )
    add_card(slide, ML, y + 4.55, CW, 0.72, fill="FDEBD0")
    add_text(
        slide, ML + 0.16, y + 4.66, CW - 0.32, 0.50,
        [[("【待補：Prototype 畫面截圖（決賽）】", ORANGE, True, 16)]],
        size=16, anchor="ctr",
    )
    add_text(
        slide, ML, y + 5.32, CW, 0.32,
        [[("Model Card 與匿名化紀錄放附錄（T8、T7 去識別報告），不計入 15 頁。", MUTED, False, 12)]],
        size=12,
    )


BUILDERS = [build_p1, build_p2, build_p3, build_p4, build_p5, build_p6, build_p7, build_p8, build_p9, build_p10, build_p11, build_p12, build_p13, build_p14, build_p15]


def set_notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


def iter_shape_text(slide):
    for shape in slide.shapes:
        if shape.has_text_frame:
            yield shape.text_frame.text
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    yield cell.text


def collect_placeholders(prs):
    found = []
    pat = re.compile(r"【待補：[^】]*】")
    for i, slide in enumerate(prs.slides, 1):
        blob = "\n".join(iter_shape_text(slide))
        for match in pat.findall(blob):
            pid = "封面" if i == 1 else ("摘要" if i == 2 else SLIDES[i - 3]["id"])
            found.append((i, pid, match))
    return found


def write_readme(prs, placeholders, preview_note: str) -> None:
    lines = [
        "# 初賽簡報 v0",
        "",
        "和泰 AI 黑客松題 3 初賽簡報骨架。數字轉抄自報告，未在產生腳本裡重算。占位是橘色字，形式為 `【待補：說明】`。",
        "",
        "## 頁數怎麼算",
        "",
        "- 投影片共 17 張：封面 1、提案摘要 1、內容 15（P1–P15）。",
        "- 模板寫明提案摘要不計入 15 頁上限。內容頁剛好 15，所以沒有把 P5 併進 P2。",
        "- 若評審把封面也算進 15 頁，合計會是 16。那時再把 P5 的兩張表併進 P2。",
        "",
        "## 頁次對照",
        "",
        "| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |",
        "| --- | --- | --- | --- | --- | --- |",
        "| 1 | 封面 | — | Lexus車主流失預警與 AI 溝通系統 | — | 模板封面，改作品名／主題／團隊 |",
        "| 2 | 摘要 | 提案摘要 | 提案摘要（表格右欄） | — | 模板表格；數字來自 T1、T7、T8、T10、專案架構 |",
    ]
    for i, meta in enumerate(SLIDES):
        figs = "、".join(Path(p).name for p in meta["figures"]) or "—"
        reports = "、".join(f"`{r}`" for r in meta["reports"])
        title = meta["title"]
        lines.append(
            f"| {i + 3} | {meta['id']} | {meta['section']} | {title} | {figs} | {reports} |"
        )
    lines += [
        "",
        "圖檔只用現成的 `reports/figures/`。本版用到 F1、F2、F3、F4、F6。F5、F7 沒有放上投影片。",
        "",
        "## 占位清單",
        "",
        "| 檔案頁 | 代碼 | 占位 |",
        "| --- | --- | --- |",
    ]
    for page, pid, text in placeholders:
        lines.append(f"| {page} | {pid} | {text} |")
    lines += [
        "",
        f"共 {len(placeholders)} 處。同一句在 P8 出現 8 次（八條輿情訊號各一格），P12 出現 12 次（四個 Persona × 三個接觸點），P14 的週數出現 5 次。",
        "",
        "## 待核（不是占位，但數字來源不一致）",
        "",
        "- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。v0 不另算，簡報先用 61%。",
        "- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值是 P 0.617、R 0.769、F1 0.685、κ 0.642，頁內有小字。",
        "",
        "## 重新產生",
        "",
        "```text",
        "python deck/build_deck.py",
        "```",
        "",
        "需要 Python 3.12 與 python-pptx。腳本開官方模板，保留封面與摘要左欄，刪掉七張章節分隔頁，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。",
        "",
        "本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/`。",
        "",
        "## 預覽",
        "",
        preview_note,
        "",
        "例句取自 `reports/T10_risk_persona_report.md` §6 的去識別代表句，不讀論壇帳號。P7 沒用到的較長句（含店名者）沒有放上投影片。",
        "",
    ]
    README.write_text("\n".join(lines), encoding="utf-8")


def export_preview(pptx_path: Path) -> str:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return "本機沒有 pywin32，略過 PowerPoint 匯出。預覽資料夾未產生。"
    PREVIEW.mkdir(parents=True, exist_ok=True)
    pdf_path = (PREVIEW / "初賽簡報_v0.pdf").resolve()
    app = None
    pres = None
    try:
        pythoncom.CoInitialize()
        app = win32com.client.DispatchEx("PowerPoint.Application")
        # 關鍵字參數會讓 COM 把 Python 物件當參數，Open 必須用位置參數。
        pres = app.Presentations.Open(str(pptx_path.resolve()), True, False, False)
        # ExportAsFixedFormat 在這台 PowerPoint 的動態 COM 包裝會丟型別錯誤；32 = ppSaveAsPDF。
        pres.SaveAs(str(pdf_path), 32)
        n = pres.Slides.Count
        for i in range(1, n + 1):
            png = (PREVIEW / f"slide-{i:02d}.png").resolve()
            pres.Slides(i).Export(str(png), "PNG", 1920, 1080)
        return f"已用 PowerPoint 匯出 `deck/preview/初賽簡報_v0.pdf` 與 slide-01.png–slide-{n:02d}.png。"
    except Exception as exc:
        return f"PowerPoint 匯出失敗，略過預覽：{exc}"
    finally:
        if pres is not None:
            pres.Close()
        if app is not None:
            app.Quit()


def assert_notes() -> None:
    if len(NOTES) != 17 or len(SLIDES) != 15 or len(BUILDERS) != 15:
        raise SystemExit("NOTES / SLIDES / BUILDERS 數量不一致")
    for i, note in enumerate(NOTES, 1):
        n = zi(note)
        if not 25 <= n <= 35:
            raise SystemExit(f"第 {i} 頁旁白 {n} 字（要 25–35）：{note}")


def fill_cover(slide) -> None:
    """封面：標題改作品名，說明框改主題／團隊／場次。"""
    texts = [sh for sh in slide.shapes if sh.has_text_frame]
    title = [sh for sh in texts if sh.text_frame.text.strip().startswith("2026")]
    note = [sh for sh in texts if "說明" in sh.text_frame.text]
    if title:
        tf = title[0].text_frame
        for para in list(tf.paragraphs)[1:]:
            para._p.getparent().remove(para._p)
        run_para = tf.paragraphs[0]
        for r in list(run_para.runs)[1:]:
            r._r.getparent().remove(r._r)
        run_para.runs[0].text = "Lexus車主流失預警與 AI 溝通系統"
        run_para.runs[0].font.size = Pt(44)
        run_para.runs[0].font.bold = True
    if note:
        tf = note[0].text_frame
        lines = ["2026 和泰 AI 黑客松｜AI 流失風險洞察與智慧溝通：打造Lexus車主忠誠度的終極防線",
                 "團隊：回廠率研究所", "初賽提案簡報（v0，2026-09）"]
        for para in list(tf.paragraphs)[1:]:
            para._p.getparent().remove(para._p)
        first = tf.paragraphs[0]
        for r in list(first.runs)[1:]:
            r._r.getparent().remove(r._r)
        first.runs[0].text = lines[0]
        first.runs[0].font.size = Pt(18)
        for ln in lines[1:]:
            para = tf.add_paragraph()
            run = para.add_run(); run.text = ln; run.font.size = Pt(18)


def main() -> None:
    assert_notes()
    prs = Presentation(str(template_path()))
    if len(prs.slides) != 9:
        raise SystemExit(f"模板應為 9 頁，實際 {len(prs.slides)}")
    while len(prs.slides) > 2:
        delete_slide(prs, len(prs.slides) - 1)
    fill_cover(prs.slides[0])
    fill_summary(prs.slides[1])
    set_notes(prs.slides[0], NOTES[0])
    set_notes(prs.slides[1], NOTES[1])
    for i, (meta, builder) in enumerate(zip(SLIDES, BUILDERS)):
        page = i + 3
        slide, y = new_content_slide(prs, meta, page)
        builder(slide, y)
        set_notes(slide, NOTES[page - 1])
    if len(prs.slides) != 17:
        raise SystemExit(f"頁數應為 17，實際 {len(prs.slides)}")
    content = len(prs.slides) - 2
    if content > 15:
        raise SystemExit(f"內容頁 {content} 超過 15")
    for i, slide in enumerate(prs.slides, 1):
        note = slide.notes_slide.notes_text_frame.text.strip()
        if not note:
            raise SystemExit(f"第 {i} 頁沒有備註")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    check = Presentation(str(OUT))
    if len(check.slides) != 17:
        raise SystemExit("重開後頁數不對")
    table = next(shape.table for shape in check.slides[1].shapes if shape.has_table)
    left = [table.cell(i, 0).text for i in range(7)]
    expected = [
        "團隊名稱",
        "產品/服務名稱",
        "企業挑戰題目",
        "目標對象",
        "解決方案設計重點\n(至多3項)",
        "運用到的AI技術、\n服務或模型等資源",
        "預期效益簡述",
    ]
    if left != expected:
        raise SystemExit(f"摘要左欄與模板不一致：{left!r}")
    placeholders = collect_placeholders(check)
    preview_note = export_preview(OUT)
    write_readme(check, placeholders, preview_note)
    print(f"slides={len(check.slides)} content={len(check.slides) - 2} placeholders={len(placeholders)}")
    print(preview_note)
    for page, pid, text in placeholders:
        print(f"  p{page} {pid} {text}")


if __name__ == "__main__":
    main()
