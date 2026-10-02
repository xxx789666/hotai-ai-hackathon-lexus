# -*- coding: utf-8 -*-
"""初賽簡報。文案與數字集中在本檔前半；不要在這裡重算統計。

版號見 DECK_VERSION。每次改動要升號：小改 +0.1，PO 審過的里程碑升整數。
可用 --version X.Y 覆蓋；--note 必填，寫進 deck/CHANGELOG.md。

重跑：python deck/build_deck.py --version X.Y --note "一句變更說明"
模板：attachments/2026和泰AI黑客松＿初賽簡報模板.pptx
輸出：deck/初賽簡報_vX.Y.pptx、deck/初賽簡報_latest.pptx、deck/README.md；
若本機有 PowerPoint，另匯 deck/preview/初賽簡報_vX.Y.pdf 與 deck/preview/vX.Y/。
內容是 v2.4（22 張：封面、摘要、P1–P15、A1–A5）。
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
# 版號。每次改簡報內容都要升號：小改 +0.1，PO 審過的里程碑升整數。
# --version X.Y 可覆蓋。同版號已在 deck/versions/ 時，未加 --force 會中止。
DECK_VERSION = "2.4"
README = ROOT / "deck" / "README.md"
PREVIEW = ROOT / "deck" / "preview"
VERSIONS = ROOT / "deck" / "versions"
CHANGELOG = ROOT / "deck" / "CHANGELOG.md"
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
    "摘要給評審三層目標：回廠率假設加十點，核准八成，模型每季重驗。",
    "先講規模感：六個人裡有一個在找出路，而且多數沒有先抱怨。",
    "售後人走了才知道，三個前兆是過保、刪項、間隔拉長。",
    "零件勝算比二點五八、價格二點六四，分母兩萬一千句。",
    "出口在一般外廠；定保口述中位原廠九千、外廠三千五，不是公告價。",
    "IQR 定 78 字門檻，上游已去掉 15,182 句重複。",
    "兩個迴路：洞察每天進報告池，關懷由客訴結案等事件觸發，審核後才投遞。",
    "分群只獨立支持靜默出走者；其餘 Persona 用規則定義。",
    "高風險七成四真有流失句；過保精算派人最多，平均風險也最高。",
    "人工兩人 κ 0.40，不一致處要經仲裁後才成為金標。",
    "r4 原值 P 0.617、R 0.769、κ 0.642。",
    "別人看不到不抱怨就走的人；我們給規則和機率，每句都能回原句。",
    "四種人配三種進廠時機，十二則已過查核，投遞前仍要人工審。",
    "人工篩選工時省九成以上（估），五項風險都已有對策。",
    "每季三百句金標、兩人共五小時，審核回饋持續再訓練。",
    "左邊是兩個迴路；右邊審核佇列是線框，決賽再給可操作版。",
    "附錄術語表：每個名詞一句定義、一句本案用法，評審追問時翻這頁。",
    "附錄四張圖：來源差異、風險分布、校準曲線，和季趨勢預警。",
    "附錄待料通知兩則：進度不承諾到貨日，代步車只照知識庫條件。",
    "CRM 八條規則的門檻列在本頁，投影片只留欄位名稱。",
    "客訴結案七天回訪兩則：電話先道歉，LINE 不要求刪評。",
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
    "benefit": [
        [("成果：高風險車主 12 個月回廠率提升 10 個百分點（假設值，導入後以基期實測校正）。", INK, False, 12)],
        [("流程：高風險名單每月更新、話術人工核准率 ≥ 80%。高風險名單人工篩選工時 −90% 以上（估）。", INK, False, 12)],
        [("模型：隨機層 F1 ≥ 0.8、κ ≥ 0.6，每季 300 句人工金標重驗。每句 0.7 秒、零 API 費。", INK, False, 12)],
    ],
}

# 每頁：章節標、結論標題、來源（寫進頁腳與 README）、圖檔
SLIDES = [
    {
        "id": "P1",
        "section": "1 提案概述",
        "title": "每 6 位有 1 位在找出口，多數沒抱怨",
        "source": "來源：統計檢定報告（T7）、殘餘切分報告（T3）",
        "reports": ["reports/T7_stats_tests.md", "reports/T3_residual_split_report.md"],
        "figures": [],
    },
    {
        "id": "P2",
        "section": "2 目標對象與痛點分析",
        "title": "售後是人走了才知道；輿情能提前預警",
        "source": "來源：統計檢定報告（T7）；Dcard 偏購車階段",
        "reports": ["reports/T7_stats_tests.md"],
        "figures": [],
    },
    {
        "id": "P3",
        "section": "2 目標對象與痛點分析",
        "title": "等料和價格送走人；態度抱怨多，卻少有人走",
        "source": "來源：統計檢定報告（T7）；圖 F1",
        "reports": ["reports/T7_stats_tests.md"],
        "figures": ["reports/figures/F1.png"],
    },
    {
        "id": "P4",
        "section": "2 目標對象與痛點分析",
        "title": "出口是一般外廠；過保後價差把人推走",
        "source": "來源：風險與 Persona 報告（T10）、專案架構、知識庫價格摘錄（T11）",
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
        "title": "2.1 萬句售後語料，品質過關、全數去識別",
        "source": "來源：題目選擇分析、資料品質報告（T7）、去識別報告（T7）",
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
        "title": "洞察每日產出；關懷由事件觸發、人工核准才發",
        "source": "來源：L7 運作流程、專案架構；圖 F8",
        "reports": ["L7運作流程_2026-09-30.md", "專案架構_2026-09-23.md"],
        "figures": ["reports/figures/F8.png"],
    },
    {
        "id": "P7",
        "section": "3 解決方案設計",
        "title": "四種流失車主，過保精算派最多（511 人）",
        "source": "來源：風險與 Persona 報告（T10）；圖 F5。未分類處置見 9/30 會議記錄",
        "reports": ["reports/T10_risk_persona_report.md", "會議記錄_2026-09-30.md"],
        "figures": ["reports/figures/F5.png"],
    },
    {
        "id": "P8",
        "section": "3 解決方案設計",
        "title": "高風險車主 74% 確有流失句，分級可信",
        "source": "來源：風險與 Persona 報告（T10）；圖 F7",
        "reports": ["reports/T10_risk_persona_report.md"],
        "figures": ["reports/figures/F7.png"],
    },
    {
        "id": "P9",
        "section": "4 AI 應用方法",
        "title": "兩段式標註：先寬抓、再複核，一致率 98.4%",
        "source": "來源：專案架構、Dcard 複核報告（T1）、其他精煉報告（T2）、殘餘切分報告（T3）",
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
        "title": "本機小模型勝過雲端 Haiku，零 API 費",
        "source": "來源：本機模型報告（T8）；校準曲線見附錄 A2",
        "reports": ["reports/T8_r4_report.md", "專案架構_2026-09-23.md"],
        "figures": [],
    },
    {
        "id": "P11",
        "section": "5 獨特優勢與差異化",
        "title": "看得見沒抱怨就走的人，分數說得出原因",
        "source": "來源：風險與 Persona 報告（T10）、本機模型報告（T8）、專案架構",
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
        "title": "對的人、對的時機開口；12 則話術全數查核",
        "source": "來源：話術範例、生成與查核報告（T14）",
        "reports": [
            "knowledge/generated_examples.md",
            "reports/T14_generation_report.md",
            "knowledge/lexus_aftersales_kb.md",
        ],
        "figures": [],
    },
    {
        "id": "P13",
        "section": "6 預期效益與落地評估",
        "title": "人工篩選工時省九成以上；五項風險都有對策",
        "source": "來源：iPAS 骨架頁、9/30 會議記錄、iPAS 導入對照",
        "reports": [
            "iPAS骨架頁_草稿.md",
            "會議記錄_2026-09-30.md",
            "iPAS導入對照_2026-09-25.md",
        ],
        "figures": [],
    },
    {
        "id": "P14",
        "section": "6 預期效益與落地評估",
        "title": "24 週導入，目標高風險回廠率 +10 個百分點",
        "source": "來源：iPAS 骨架頁、9/30 會議記錄；模型現況見人工評估（T9）與本機模型報告（T8）",
        "reports": [
            "iPAS骨架頁_草稿.md",
            "會議記錄_2026-09-30.md",
            "reports/T9_human_eval.md",
            "reports/T8_r4_report.md",
        ],
        "figures": [],
    },
    {
        "id": "P15",
        "section": "7 補充資料",
        "title": "每則話術都經人工核准；決賽提供可操作版",
        "source": "來源：L7 運作流程；圖 F8。線框為示意",
        "reports": ["L7運作流程_2026-09-30.md"],
        "figures": ["reports/figures/F8.png"],
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
    ("靜默出走者", "只看客訴，看不到沒抱怨就走的人。"),
    ("機率可解釋", "輸出各級機率，並標出命中規則。不是黑箱分數。"),
    ("本機就能跑", "CRM 資料不能出門。8 GB 可訓可推，零 API 費。"),
    ("數字回得去", "每個比率有檢定或區間。也能回到去識別原句。"),
]

TOUCH_COLS = ["保固到期前 60 天", "回廠間隔拉長", "刪項後首次回廠"]
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
# P8 只留欄位名。門檻沿用上面 CRM_MAP 的數字，改寫進附錄 A4，不另計算。
CRM_FIELDS = {
    "R1": "保固到期日、延保狀態",
    "R2": "工單估價與實收、拒絕估價項目、滿意度價格題",
    "R3": "回廠間隔、預約取消、App 查據點",
    "R4": "自備零件或機油註記、換油套餐、工單金額",
    "R5": "待料天數、改期次數",
    "R6": "同項目重複進廠、技術客訴、召回未完成",
    "R7": "無工單、過戶或退出會員、App 未開啟",
    "R8": "NPS、客訴紀錄、推薦計畫",
}
CRM_THRESHOLD = {
    "R1": "到期前 90 天未購延保",
    "R2": "連續 2 次拒絕估價項目",
    "R3": "逾期超過建議週期 1.5 倍",
    "R4": "金額較前次下降超過 40%",
    "R5": "待料超過 7 天，或同車至少 2 次",
    "R6": "30 天內同項目回廠至少 2 次",
    "R7": "12 個月無工單（只驗證，不觸發）",
    "R8": "NPS 0–6，且 12 個月內有客訴",
}


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


def add_card(slide, x, y, w, h, fill="F4F7FB", line=None):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    try:
        shape.adjustments[0] = 0.08
    except Exception:
        pass
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
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
    heights = [0.40, 0.52, 0.52, 0.46, 1.28, 0.92, 1.28]
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


def fit_pic(slide, name: str, x, y, max_w, max_h) -> float:
    """依圖檔實際比例放入方框，水平置中。F1–F7 是 1920×1080，F8／F9 是 1920×900。"""
    path = FIG / name
    try:
        from PIL import Image

        with Image.open(path) as im:
            iw, ih = im.size
        aspect = ih / iw
    except Exception:
        aspect = 900 / 1920
    w, h = max_w, max_w * aspect
    if h > max_h:
        h = max_h
        w = h / aspect
    slide.shapes.add_picture(
        str(path), Inches(x + (max_w - w) / 2), Inches(y), Inches(w), Inches(h)
    )
    return h


def build_p1(slide, y):
    rates = [("18.2%", "Mobile01", "作者流失率"), ("14.1%", "PTT", "作者流失率"), ("6.8%", "Dcard", "作者流失率")]
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
        "三站差異顯著（χ²=99.5）。",
        "母體為論壇發言者。",
        "1,671 句流失中，186 句沒抱怨就找出口。",
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
        [[("使用者是售後決策者，以及服務廠的客戶關係人員。", MUTED, False, 13)]],
        size=13,
    )
    right_x = ML + left_w + 0.22
    right_w = CW - left_w - 0.22
    cards = [
        ("過保", "保固到期前先找到人。"),
        ("刪項", "未同意的項目，回廠時再問。"),
        ("回廠間隔拉長", "間隔超過建議週期就提醒。"),
    ]
    add_text(
        slide, right_x, y, right_w, 0.32,
        [[("三個流失前兆", BLUE, True, 16)]],
        size=16, margin=0.0,
    )
    for i, (head, body) in enumerate(cards):
        yy = y + 0.40 + i * 1.35
        add_card(slide, right_x, yy, right_w, 1.22)
        add_text(
            slide, right_x + 0.14, yy + 0.12, right_w - 0.28, 1.00,
            [
                [(head, INK, True, 16)],
                [(body, INK, False, 14)],
            ],
            size=14,
        )


def build_p3(slide, y):
    width = 9.2
    h = pic(slide, "F1.png", ML + (CW - width) / 2, y, width)
    lines = [
        "流失率最高：零件供應 17.3%、價格 15.0%。",
        "最低：銷售交車 1.4%。",
        "態度負面占 61%，流失只有 4.7%。",
    ]
    add_text(
        slide, ML, y + h + 0.02, CW, 1.05,
        [[(line, INK, False, 15)] for line in lines],
        size=15,
    )
    add_text(
        slide, ML, y + h + 1.08, CW, 0.32,
        [[("對應接觸點：待料通知（R5），話術見附錄 A3", MUTED, False, 12)]],
        size=12,
    )


def build_p4(slide, y):
    width = 9.2
    h = pic(slide, "F3.png", ML + (CW - width) / 2, y, width)
    add_text(
        slide, ML, y + h + 0.02, CW, 1.55,
        [
            [("去向：一般外廠 736 句、自備料 234、DIY 135。", INK, False, 15)],
            [("可複選；母體 1,671 句流失", MUTED, False, 12)],
            [("過保 62 句，保固內僅 17 句。", INK, False, 15)],
            [("定保口述價：原廠 9,000、外廠 3,500。", INK, False, 15)],
            [("論壇口述中位數，非公告價", MUTED, False, 12)],
        ],
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
        [[("異常值＝超過 78 字的長句，占 7.77%。", MUTED, False, 12)]],
        size=12,
    )


def build_p6(slide, y):
    # F8：兩個迴路、四個資料庫、五個 Dashboard（L7運作流程_2026-09-30.md）。八層 L0–L7 併成下方一行。
    pic_w = 11.6
    h = pic(slide, "F8.png", ML + (CW - pic_w) / 2, y - 0.08, pic_w)
    strip = "　".join(f"{code} {name}" for code, name, _ in LAYERS)
    add_text(slide, ML, y + h - 0.02, CW, 0.34, [[("八層對應：" + strip, MUTED, False, 11)]], size=11, align=PP_ALIGN.CENTER)


def build_p7(slide, y):
    left_w = 6.15
    gap_x, gap_y = 0.12, 0.10
    card_w = (left_w - gap_x) / 2
    card_h = 2.05
    for i, (name, people, share, feature, quote) in enumerate(PERSONAS):
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        add_card(slide, x, yy, card_w, card_h)
        add_text(
            slide, x + 0.10, yy + 0.08, card_w - 0.18, card_h - 0.14,
            [
                [(name, INK, True, 14)],
                [(f"{people}　{share}", BLUE, True, 16)],
                [(feature, INK, False, 11)],
                [(quote, NAVY, False, 11)],
            ],
            size=11,
        )
    fig_x = ML + left_w + 0.16
    fig_w = CW - left_w - 0.16
    fig_h = fit_pic(slide, "F5.png", fig_x, y, fig_w, 4.15)
    add_text(
        slide, ML, y + max(card_h * 2 + gap_y, fig_h) + 0.06, CW, 0.95,
        [
            [("分母：高、中風險 1,280 人。", MUTED, False, 13)],
            [("未分類 199 人列觀察名單，不投遞。", MUTED, False, 13)],
            [("Persona 為規則定義，每項可回溯原句。", MUTED, False, 13)],
        ],
        size=13,
    )


def build_p8(slide, y):
    add_text(
        slide, ML, y, 6.55, 2.35,
        [
            [("風險分＝模型機率占 6 成＋規則命中占 4 成。", INK, False, 14)],
            [("高 1,049／中 231／低 5,114。", INK, True, 18)],
            [("高風險作者 74% 有流失句，低風險 1.8%。", INK, False, 16)],
            [("過保精算派 511 人，平均風險 0.73 最高。", INK, False, 14)],
        ],
        size=14,
    )
    fit_pic(slide, "F7.png", ML + 6.70, y, 5.72, 2.72)
    header = [cell_text(h, WHITE, True) for h in ("規則", "輿情訊號", "CRM 欄位")]
    body = []
    body.append(header)
    for code, signal in SIGNALS:
        body.append([
            cell_text(code),
            cell_text(signal),
            cell_text(CRM_FIELDS[code], INK, False),
        ])
    add_table(slide, ML, y + 2.82, CW, 2.35, body, [1.3, 2.4, 8.72], font=10)
    add_text(slide, ML, y + 5.22, CW, 0.40,
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
    add_text(
        slide, ML, y + 1.90, CW, 0.40,
        [[("九面向全量標完，殘餘僅 4 句。", INK, False, 16)]],
        size=16,
    )
    add_card(slide, ML, y + 2.45, CW, 1.45, fill="FDEBD0")
    add_text(
        slide, ML + 0.16, y + 2.55, CW - 0.32, 1.25,
        [
            [("人工金標 300 句：本機模型 F1 0.82，與 Sonnet 同級。", INK, False, 15)],
            [("Haiku 只有 F1 0.50。", INK, False, 15)],
            [("限制：正例僅 9 句，召回區間 0.45–0.94。", INK, False, 15)],
        ],
        size=15,
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
        slide, ML, y + 1.48, 6.15, 0.55,
        [
            [("同一 600 句測試集比較。", MUTED, False, 12)],
            [("校準曲線見附錄。", MUTED, False, 12)],
        ],
        size=11,
    )
    lines = [
        "Prefill-only：只輸出各等級機率，不生成文字。",
        "8 GB 顯卡可訓（約 5 小時）、可推（每句 0.7 秒）。",
        "資料不出門，推論零 API 費。",
    ]
    add_card(slide, ML + 6.40, y, 6.02, 3.15)
    add_text(
        slide, ML + 6.56, y + 0.16, 5.70, 2.85,
        [[(line, INK, False, 16)] for line in lines],
        size=16,
    )
    # 訓練步驟：五張小卡
    steps = [
        ("1 ETL＋弱監督標註", "篩出 21,183 句售後語料。先寬鬆標，再帶上下文複核。"),
        ("2 資料切分（防洩漏）", "GroupSplit 整篇排除測試 600 句。驗證 1,096 句，訓練池 9,431 句。"),
        ("3 任務轉換", "流失四級拆成四個是非題。Prefill-only 只取下一詞機率。"),
        ("4 監督式微調 SFT", "Qwen3-4B 用 QLoRA r=16。過採樣到四成；2 epoch、8 GB、5 小時。"),
        ("5 評估與校準", "金標 300 句：F1 0.82、κ 0.81。另看 P、R 與五段校準。"),
    ]
    gap = 0.12
    cw = (CW - 4 * gap) / 5
    sy = y + 3.55
    for i, (head, body) in enumerate(steps):
        x = ML + i * (cw + gap)
        add_card(slide, x, sy, cw, 1.35)
        add_text(slide, x + 0.12, sy + 0.08, cw - 0.24, 1.2,
                 [[(head, BLUE, True, 11.5)], [(body, INK, False, 9.5)]], size=9.5)
    add_text(slide, ML, sy + 1.45, CW, 0.5,
             [
                 [("架構沿用開源 LLM2Jev。", MUTED, False, 12)],
                 [("最高信心桶命中約七成，見附錄。", MUTED, False, 12)],
             ], size=12)


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


def load_p12_messages() -> list[dict]:
    """轉抄 generated_examples.md 的逐則區，不在簡報腳本裡重算。"""
    path = ROOT / "knowledge" / "generated_examples.md"
    if not path.exists():
        raise SystemExit(f"缺少 {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("### "):
            i += 1
            continue
        head = lines[i][4:]
        persona, rest = head.split(" × ", 1)
        touch = rest.split()[0]
        channel = ""
        text = ""
        i += 1
        while i < len(lines) and not lines[i].startswith("#"):
            line = lines[i]
            if line.startswith("- 渠道："):
                channel = line.split("：", 1)[1].strip()
            elif line.startswith("- 訊息全文："):
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                chunk = []
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
                    chunk.append(lines[i].strip())
                    i += 1
                text = "".join(chunk)
                continue
            i += 1
        items.append({"persona": persona.strip(), "touch": touch, "channel": channel, "text": text})
    items = [it for it in items if it["touch"] in ("T1", "T2", "T3")]
    if len(items) != 12:
        raise SystemExit(f"P12 應有 12 則，讀到 {len(items)}")
    return items


def build_p12(slide, y):
    msgs = {(m["persona"], m["touch"]): m for m in load_p12_messages()}
    header = [cell_text("Persona", WHITE, True)] + [cell_text(c, WHITE, True) for c in TOUCH_COLS]
    rows = [header]
    for name, *_rest in PERSONAS:
        row = [cell_text(name, INK, True)]
        for touch in ("T1", "T2", "T3"):
            msg = msgs[(name, touch)]
            compact = re.sub(r"\s+", "", msg["text"])
            preview = compact[:40] + "…"
            row.append([
                [(msg["channel"], BLUE, True)],
                [(preview, INK, False)],
            ])
        rows.append(row)
    add_table(slide, ML, y, CW, 4.05, rows, [1.62, 3.60, 3.60, 3.60], font=10)
    add_text(
        slide, ML, y + 4.12, CW, 1.20,
        [
            [("12 則對 76 條官方條款查核通過。", INK, True, 13)],
            [("人工核准才投遞。", INK, False, 13)],
            [("全文與查核見附錄 A3。", MUTED, False, 12)],
            [("客訴結案後 7 天回訪，見附錄 A5。", MUTED, False, 12)],
        ],
        size=12,
    )


def build_p13(slide, y):
    left_w = 5.55
    items = [
        ("需求", "人走了才知道 → 過保、刪項、間隔拉長時先找到人。"),
        ("技術", "判斷、分群、生成都有原型。8 條規則已對到 DMS 欄位。"),
        ("財務：人力成本節省", "人工逐句篩 2.1 萬句約需 106 人時（估）。本機模型 4.1 小時跑完，零 API 費。人力改花在審名單、審話術。"),
        ("風險", "五項主要風險，對策見右表。"),
    ]
    for i, (head, body) in enumerate(items):
        yy = y + i * 1.22
        add_card(slide, ML, yy, left_w, 1.14)
        add_text(
            slide, ML + 0.12, yy + 0.06, left_w - 0.22, 1.02,
            [
                [(head, BLUE, True, 13)],
                [(body, INK, False, 11)],
            ],
            size=11,
        )
    # 風險登錄表前 5 列（iPAS骨架頁_草稿.md）。四欄：層別、風險、對策、責任人。
    risks = [
        ("層別", "風險", "對策", "責任人"),
        ("技術", "生成內容寫錯價格或保固條款", "只引用 76 條知識庫、數字逐字比對、人工審核必經", "A"),
        ("技術", "模型在模糊句多報（困難層 F1 ≤ 0.51，精確率 0.34）", "定位成「初篩＋人工複核」", "A"),
        ("資料", "論壇代表性（正例 67% 來自 Mobile01，母體是論壇發言者）", "分析頁註明母體與來源構成；上線改用 CRM 資料", "B"),
        ("法規", "個資與再識別", "去識別流程，簡報與 Demo 只用去識別版", "A"),
        ("組織", "Persona 被質疑主觀（ARI 0.08）", "寫成「規則定義、每項可回溯原句」", "B"),
    ]
    rows = []
    for i, cols in enumerate(risks):
        if i == 0:
            rows.append([cell_text(c, WHITE, True) for c in cols])
        else:
            rows.append([cell_text(cols[0], INK, True), cell_text(cols[1]), cell_text(cols[2]), cell_text(cols[3], INK, True)])
    add_table(
        slide, ML + 5.72, y, 6.70, 4.72, rows,
        [0.72, 2.35, 2.85, 0.78],
        font=10,
    )


def build_p14(slide, y):
    add_text(
        slide, ML, y, CW, 0.28,
        [[("層級對照 iPAS：成果＝業務、流程＝應用、模型＝系統", MUTED, False, 12)]],
        size=12, margin=0.0,
    )
    headers = ["層級", "指標", "現況", "目標"]
    data = [
        ("成果", "高風險車主 12 個月回廠率", "導入後建立基期", "提升 10 個百分點＊"),
        ("流程", "高風險名單更新頻率；話術人工核准率", "名單一次性產出；16 則已查核、待人工審", "每月更新；核准率 ≥ 80%"),
        ("流程", "高風險名單人工篩選工時", "人工約 106 人時 → 模型 4.1 小時", "−90% 以上（估）"),
        ("模型", "隨機層 F1、κ；每句判斷時間", "F1 0.82、κ 0.81；0.7 秒", "F1 ≥ 0.8、κ ≥ 0.6，每季 300 句人工金標重驗"),
    ]
    rows = [[cell_text(h, WHITE, True) for h in headers]]
    for layer, metric, now, goal in data:
        rows.append([
            cell_text(layer, INK, True),
            cell_text(metric),
            cell_text(now),
            cell_text(goal),
        ])
    add_table(slide, ML, y + 0.26, CW, 2.05, rows, [1.15, 3.55, 3.85, 3.87], font=10)
    add_text(
        slide, ML, y + 2.32, CW, 0.22,
        [[("＊假設值，導入後以基期實測校正。模型現況用隨機層人工金標，與目標同一把尺。", MUTED, False, 11)]],
        size=11, margin=0.0,
    )
    moat_y = y + 2.56
    add_card(slide, ML, moat_y, CW, 1.28)
    add_text(
        slide, ML + 0.14, moat_y + 0.06, CW - 0.28, 1.16,
        [
            [("數據護城河：三項資產，全部留在和泰內網", BLUE, True, 14)],
            [("語料：2.1 萬句標註＋300 句人工金標", INK, False, 13)],
            [("模型：自有 4B 模型，8 GB 顯卡 5 小時可重訓。人工審核回饋持續再訓練。", INK, False, 13)],
            [("知識庫：76 條官方條款＋每則話術查核紀錄", INK, False, 13)],
        ],
        size=13,
    )
    phases = [
        ("資料接入", "4 週", "R1–R8 換成 DMS 實際欄位，工單文字去識別後接入"),
        ("模型校準", "4 週", "重標 300 句金標，重驗 r4、調觸發門檻"),
        ("單一據點試行", "8 週", "一個服務廠跑完流程，專員審核後投遞"),
        ("擴大至全台", "8 週", "依試行調整話術與渠道，分批上線"),
        ("持續監控", "不設終點", "日監控、週收樣本、月重評、季重驗模型"),
    ]
    gap = 0.12
    card_w = (CW - 4 * gap) / 5
    base = y + 3.92
    for i, (name, weeks, doing) in enumerate(phases):
        x = ML + i * (card_w + gap)
        add_card(slide, x, base, card_w, 1.05)
        add_text(
            slide, x + 0.06, base + 0.04, card_w - 0.12, 0.98,
            [
                [(str(i + 1) + "  " + name, BLUE, True, 12)],
                [(weeks, NAVY, True, 12)],
                [(doing, MUTED, False, 10)],
            ],
            size=11,
        )
    add_text(
        slide, ML, base + 1.10, CW, 0.24,
        [[("合計約 24 週（持續監控不設終點）。", INK, True, 12)]],
        size=12, margin=0.0,
    )


def build_p15(slide, y):
    left_w = 6.20
    h = pic(slide, "F8.png", ML, y, left_w)
    add_text(
        slide, ML, y + h + 0.06, left_w, 0.70,
        [
            [("兩個迴路、四個資料庫、五個 Dashboard。", INK, False, 13)],
            [("報告 T1–T15 與程式在私有庫，評審需要時開。", MUTED, False, 12)],
        ],
        size=13,
    )
    rx = ML + left_w + 0.18
    rw = CW - left_w - 0.18
    rh = 4.85
    add_card(slide, rx, y, rw, rh, fill="FFFFFF", line=NAVY)
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(rx), Inches(y), Inches(rw), Inches(0.42)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    add_text(
        slide, rx + 0.10, y + 0.04, rw - 0.20, 0.34,
        [[("Dashboard 5　溝通審核佇列", WHITE, True, 14)]],
        size=14, anchor="ctr", margin=0.0,
    )
    add_card(slide, rx + 0.14, y + 0.54, rw - 0.28, 1.15, fill="F4F7FB")
    add_text(
        slide, rx + 0.24, y + 0.60, rw - 0.48, 1.02,
        [
            [("車主　H-7F3A　　風險　高", INK, True, 13)],
            [("Persona　過保精算派", INK, False, 13)],
            [("觸發　R1 過保", INK, False, 13)],
        ],
        size=13,
    )
    add_card(slide, rx + 0.14, y + 1.82, rw - 0.28, 1.35, fill="F7F9FB")
    add_text(
        slide, rx + 0.24, y + 1.90, rw - 0.48, 1.18,
        [
            [("話術草稿", BLUE, True, 13)],
            [("引用條目 1、13", NAVY, False, 14)],
        ],
        size=13,
    )
    labels = [("核准", "2F5D9F"), ("改寫", "44546A"), ("退回", "C05600")]
    btn_gap = 0.10
    btn_w = (rw - 0.28 - 2 * btn_gap) / 3
    btn_y = y + 3.32
    for i, (label, fill) in enumerate(labels):
        bx = rx + 0.14 + i * (btn_w + btn_gap)
        add_card(slide, bx, btn_y, btn_w, 0.48, fill=fill)
        add_text(
            slide, bx, btn_y + 0.06, btn_w, 0.36,
            [[(label, WHITE, True, 14)]],
            size=14, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0,
        )
    add_text(
        slide, rx + 0.14, y + 3.95, rw - 0.28, 0.70,
        [
            [("決賽提供可操作版。", INK, True, 14)],
            [("未核准不投遞。代號為示意，不是論壇帳號。", MUTED, False, 11)],
        ],
        size=12,
    )


SLIDES.append({
    "id": "A1",
    "section": "附錄 術語表（不計入 15 頁）",
    "title": "本案用到的技術名詞：定義與在本案的用法",
    "source": "來源：本機模型報告（T8）、人工評估（T9）、風險與 Persona 報告（T10）",
    "reports": ["reports/T8_r4_report.md", "reports/T9_human_eval.md", "reports/T10_risk_persona_report.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A2",
    "section": "附錄 補充圖表（不計入 15 頁）",
    "title": "來源差異、風險分布、校準曲線，與季趨勢",
    "source": "來源：統計檢定報告（T7）、風險與 Persona 報告（T10）、本機模型報告（T8）、趨勢報告（T15）",
    "reports": [
        "reports/T7_stats_tests.md",
        "reports/T10_risk_persona_report.md",
        "reports/T8_r4_report.md",
        "reports/T15_trend_reports.md",
    ],
    "figures": [
        "reports/figures/F2.png",
        "reports/figures/F4.png",
        "reports/figures/F6.png",
        "reports/figures/F9.png",
    ],
})
SLIDES.append({
    "id": "A3",
    "section": "附錄 待料通知話術（不計入 15 頁）",
    "title": "待料逾 7 天就主動通知，話術不寫到貨日",
    "source": "來源：話術範例、生成與查核報告（T14）",
    "reports": ["knowledge/generated_examples.md", "reports/T14_generation_report.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A4",
    "section": "附錄 CRM 觸發門檻（不計入 15 頁）",
    "title": "八條規則的欄位與門檻；投影片只留欄位名",
    "source": "來源：風險與 Persona 報告（T10）、L7 運作流程",
    "reports": ["reports/T10_risk_persona_report.md", "L7運作流程_草稿.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A5",
    "section": "附錄 客訴回訪話術（不計入 15 頁）",
    "title": "客訴結案第 7 天回訪，不推銷、不要求刪評",
    "source": "來源：客訴關懷策略、話術範例",
    "reports": ["客訴關懷策略_草稿.md", "knowledge/generated_examples.md"],
    "figures": [],
})


def build_a1(slide, y):
    rows = [
        ("ETL", "Extract-Transform-Load：擷取、清洗轉換、載入。與 ELT（先載入再轉換）不同", "爬蟲擷取→去重、切句、售後關鍵詞篩選→寫入 jsonl；23.6 萬句留 21,183 句"),
        ("弱監督標註（LLM-as-labeler）", "用模型而非人工產生訓練標籤，事後以人工樣本驗證品質", "Haiku 初篩＋Sonnet／GPT 帶上下文複核；人工 300 句驗證"),
        ("監督式學習／監督式微調 SFT", "用「輸入＋正確答案」訓練；SFT 是在預訓練模型上以標籤資料微調，非從零訓練", "以 21,183 句 LLM 標籤微調 Qwen3-4B"),
        ("QLoRA（NF4 4-bit、LoRA r=16）", "把基底模型量化成 4 位元，只訓練低秩附加參數，省顯存", "8 GB 顯卡 5 小時完成；adapter 約數十 MB"),
        ("GroupSplit／資料洩漏", "依群組（文章）切分訓練與測試，避免同篇句子兩邊都出現而高估", "600 句測試集所在 421 篇整篇排除訓練"),
        ("類別不平衡／過採樣", "正例太少時重複抽樣正例，避免模型全猜負例", "流失句 7.9% → 訓練時提高到四成"),
        ("Prefill-only（System-One 決策）", "只讀 prompt 取下一個 token 在候選選項上的機率，不生成文字，快且可控", "流失四級與立場各成 yes/no 候選題；每句 0.7 秒"),
        ("Precision／Recall／F1", "報流失的句子有多少是真的／真的流失有多少被抓到／兩者調和平均", "r4 隨機層 P 0.88、R 0.78、F1 0.82"),
        ("Cohen's κ", "扣掉瞎猜也會對的部分後的一致程度；0.6 以上算好", "人工兩人 κ 0.40（仲裁後成金標）；r4 對人工 κ 0.81"),
        ("校準（reliability bins）", "把預測機率分箱，看每箱實際正例比例是否接近機率", "最高信心桶約七成為真正例，方向對、尚未完全校準"),
        ("χ²、Cramér's V、Wilson CI", "類別關聯檢定、其效果量、比例的信賴區間", "來源流失率差異 χ²=99.5、V=0.125；九面向勝算比"),
        ("RAG（檢索增強生成）", "先從知識庫檢索相關條目，再讓模型只依這些內容生成", "76 條（官網 40、手冊 36）；16 則話術每則附引用與查核"),
        ("K-means／silhouette／ARI", "分群法、分群品質指標、兩種分群結果的一致度", "驗證四個 Persona：只有靜默出走者被資料獨立支持"),
    ]
    body = [[cell_text(h, WHITE, True) for h in ("名詞", "定義", "本案用法")]]
    for a, b, c in rows:
        body.append([cell_text(a, INK, True), cell_text(b), cell_text(c)])
    add_table(slide, ML, y, CW, 5.6, body, [2.6, 5.0, 4.82], font=9.5)


def build_a2(slide, y):
    items = [
        ("F2.png", "F2　Mobile01 18.2%、PTT 14.1%、Dcard 6.8%（作者流失率）。"),
        ("F4.png", "F4　高風險 1,049 人（16.4%）；約八成作者在低風險。"),
        ("F6.png", "F6　最高信心桶 n=71，實際流失 68%（校準曲線）。"),
        ("F9.png", "F9　季趨勢，日報／週報／季報與 200% 預警。"),
    ]
    gap_x, gap_y = 0.18, 0.08
    cell_w = (CW - gap_x) / 2
    cell_h = (7.02 - y - gap_y) / 2
    cap_h = 0.32
    for i, (fig, cap) in enumerate(items):
        col, row = i % 2, i // 2
        x = ML + col * (cell_w + gap_x)
        yy = y + row * (cell_h + gap_y)
        fit_pic(slide, fig, x, yy, cell_w, cell_h - cap_h)
        add_text(
            slide, x, yy + cell_h - cap_h, cell_w, cap_h,
            [[(cap, MUTED, False, 12)]],
            size=12,
        )


def load_a3_messages() -> list[dict]:
    path = ROOT / "knowledge" / "generated_examples.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    i = 0
    while i < len(lines):
        if not (lines[i].startswith("### ") and "待料通知" in lines[i]):
            i += 1
            continue
        persona = lines[i][4:].split(" × ", 1)[0].strip()
        channel = cites = check = text = ""
        i += 1
        while i < len(lines) and not lines[i].startswith("#"):
            line = lines[i]
            if line.startswith("- 渠道："):
                channel = line.split("：", 1)[1].strip()
            elif line.startswith("- 引用條目："):
                cites = line.split("：", 1)[1].strip()
            elif line.startswith("- 查核："):
                check = line.split("：", 1)[1].strip()
            elif line.startswith("- 訊息全文："):
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                chunk = []
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith("- "):
                    chunk.append(lines[i].strip())
                    i += 1
                text = "".join(chunk)
                continue
            i += 1
        items.append({
            "persona": persona,
            "channel": channel,
            "cites": cites,
            "check": check,
            "text": text,
        })
    if len(items) != 2:
        raise SystemExit(f"A3 應有 2 則待料通知，讀到 {len(items)}")
    return items


def build_a3(slide, y):
    msgs = load_a3_messages()
    card_h = 2.55
    for i, msg in enumerate(msgs):
        yy = y + i * (card_h + 0.14)
        add_card(slide, ML, yy, CW, card_h)
        add_text(
            slide, ML + 0.16, yy + 0.08, CW - 0.32, card_h - 0.14,
            [
                [(f"{msg['persona']} × 待料通知", BLUE, True, 16)],
                [(f"渠道：{msg['channel']}　　引用條目：{msg['cites']}", NAVY, False, 12)],
                [(msg["text"], INK, False, 13)],
                [(f"查核：{msg['check']}", MUTED, False, 12)],
            ],
            size=13,
        )


def build_a4(slide, y):
    header = [cell_text(h, WHITE, True) for h in ("規則", "欄位", "門檻")]
    rows = [header]
    for code, signal in SIGNALS:
        rows.append([
            cell_text(f"{code} {signal}", INK, True),
            cell_text(CRM_FIELDS[code]),
            cell_text(CRM_THRESHOLD[code]),
        ])
    add_table(slide, ML, y, CW, 5.4, rows, [2.3, 5.3, 4.82], font=12)


def load_a5_messages() -> list[dict]:
    path = ROOT / "knowledge" / "generated_examples.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    i = 0
    while i < len(lines):
        if not (lines[i].startswith("### ") and "客訴結案後" in lines[i]):
            i += 1
            continue
        persona = lines[i][4:].split(" × ", 1)[0].strip()
        channel = cites = check = text = ""
        i += 1
        while i < len(lines) and not lines[i].startswith("#"):
            line = lines[i]
            if line.startswith("- 渠道："):
                channel = line.split("：", 1)[1].strip()
            elif line.startswith("- 引用條目："):
                cites = line.split("：", 1)[1].strip()
            elif line.startswith("- 查核："):
                check = line.split("：", 1)[1].strip()
            elif line.startswith("- 訊息全文："):
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                chunk = []
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#") and not lines[i].startswith("- "):
                    chunk.append(lines[i].strip())
                    i += 1
                text = "".join(chunk)
                continue
            i += 1
        items.append({
            "persona": persona,
            "channel": channel,
            "cites": cites,
            "check": check,
            "text": text,
        })
    if len(items) != 2:
        raise SystemExit(f"A5 應有 2 則客訴回訪，讀到 {len(items)}")
    return items


def build_a5(slide, y):
    msgs = load_a5_messages()
    card_h = 2.55
    for i, msg in enumerate(msgs):
        yy = y + i * (card_h + 0.14)
        add_card(slide, ML, yy, CW, card_h)
        add_text(
            slide, ML + 0.16, yy + 0.08, CW - 0.32, card_h - 0.14,
            [
                [(f"{msg['persona']} × 客訴結案後 7 天回訪", BLUE, True, 16)],
                [(f"渠道：{msg['channel']}　　引用條目：{msg['cites']}", NAVY, False, 12)],
                [(msg["text"], INK, False, 13)],
                [(f"查核：{msg['check']}", MUTED, False, 12)],
            ],
            size=13,
        )


BUILDERS = [build_p1, build_p2, build_p3, build_p4, build_p5, build_p6, build_p7, build_p8, build_p9, build_p10, build_p11, build_p12, build_p13, build_p14, build_p15, build_a1, build_a2, build_a3, build_a4, build_a5]


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


def write_readme(prs, placeholders, preview_note: str, version: str) -> None:
    lines = [
        f"# 初賽簡報 v{version}",
        "",
        "和泰 AI 黑客松題 3 初賽簡報。數字轉抄自報告，未在產生腳本裡重算。"
        f"本版檔名是 `初賽簡報_v{version}.pptx`，最新複本是 `初賽簡報_latest.pptx`。"
        "占位若還有，是橘色字，形式為 `【待補：說明】`。",
        "",
        "## 版本",
        "",
        f"- 目前版號：v{version}。",
        f"- 檔名規則：`deck/初賽簡報_v{version}.pptx`、`deck/preview/初賽簡報_v{version}.pdf`、`deck/preview/v{version}/slide-NN.png`。每次建置用新版號，不覆蓋舊版檔。",
        "- 怎麼升號：小改 +0.1；PO 審過的里程碑升整數。改 `DECK_VERSION` 或傳 `--version X.Y`。`deck/versions/` 已有同版號且未加 `--force` 時，建置中止。",
        "- 變更紀錄：`deck/CHANGELOG.md`（新的一列在表格最上方）。",
        "- 最新複本：`deck/初賽簡報_latest.pptx` 與 `deck/preview/初賽簡報_latest.pdf` 是本次建置的複本，給 Issue 連結用，每次建置覆寫這兩個檔。",
        "",
        "## 頁數怎麼算",
        "",
        "- 投影片共 22 張：封面 1、提案摘要 1、內容 15（P1–P15）、附錄 5（A1 術語表、A2 補充圖表、A3 待料通知、A4 CRM 觸發門檻、A5 客訴回訪）。",
        "- 待料通知與客訴回訪話術分兩頁：A3 兩則待料、A5 兩則客訴。四則全文塞不進同一頁。",
        "- 模板寫明提案摘要不計入 15 頁上限。附錄也不計。內容頁剛好 15，所以沒有把 P5 併進 P2。",
        "- 若評審把封面也算進 15 頁，合計會是 16。那時再把 P5 的兩張表併進 P2。",
        "",
        "## 頁次對照",
        "",
        "| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |",
        "| --- | --- | --- | --- | --- | --- |",
        "| 1 | 封面 | — | Lexus車主流失預警與 AI 溝通系統 | — | 模板封面，改作品名／主題／團隊 |",
        "| 2 | 摘要 | 提案摘要 | 提案摘要（表格右欄） | — | 會議記錄 §四；模型現況見 T8、T9 |",
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
        "圖檔只用現成的 `reports/figures/`。洞察頁用 F1、F3、F5、F7。P6 與 P15 用 F8。附錄 A2 放 F2、F4、F6、F9。",
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
        f"共 {len(placeholders)} 處。P12 的十二則話術在 build 時讀 `knowledge/generated_examples.md` 前 40 字，不在本腳本寫死。",
        "",
        "## 待核（不是占位，但數字來源要對得上）",
        "",
        "- P1 三張卡轉抄 `reports/T7_stats_tests.md` 作者層級表：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。P2 已刪這張表，改放三個流失前兆。",
        "- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。",
        "- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。",
        "- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值 P 0.617、R 0.769、κ 0.642 在該頁備註。校準曲線在附錄 A2。F1 0.685 沒有放進 25–35 字備註。",
        "- P1 內文不再寫 p<.001 與 Cramér's V=0.125。檢定見統計檢定報告（T7），χ²=99.5 仍在頁上。",
        "- P2 刪三站流失率表。Dcard 偏購車階段留在頁腳來源。χ²(2)=99.5、V=0.125 與 P1 重複，依清單刪掉。",
        "- P3 備註只放得下零件勝算比 2.58、價格勝算比 2.64、分母 21,183 句。銷售交車勝算比 0.15 放這裡。",
        "- P4 內文依清單只留定保口述價。機油口述中位仍是原廠 5,000、外廠 1,950，不是公告價。",
        "- P14 備註放每季 300 句、兩人共 5 小時，以及「人工審核回饋持續再訓練」。話術由模型生成、人工每則只審約 1–2 分鐘（估），放這裡。旁白：別家買雲端 API，資料和經驗都留在別人那裡；我們每多審一則話術、多標一批句子，模型和知識庫就更懂 Lexus 車主。",
        "",
        "## 重新產生",
        "",
        "```text",
        "python deck/build_deck.py --version X.Y --note \"一句變更說明\"",
        "```",
        "",
        "需要 Python 3.12 與 python-pptx。`--note` 必填。腳本開官方模板，保留封面與摘要左欄，刪掉七張章節分隔頁，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。同版號已存在時加上 `--force` 才會覆寫。",
        "",
        "本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/` 的版號檔與 `vX.Y/` 資料夾。",
        "",
        "## 預覽",
        "",
        preview_note,
        "",
        "例句取自 `reports/T10_risk_persona_report.md` §6 的去識別代表句，不讀論壇帳號。P7 沒用到的較長句（含店名者）沒有放上投影片。",
        "",
    ]
    README.write_text("\n".join(lines), encoding="utf-8")


def export_preview(pptx_path: Path, version: str) -> str:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return "本機沒有 pywin32，略過 PowerPoint 匯出。預覽資料夾未產生。"
    PREVIEW.mkdir(parents=True, exist_ok=True)
    png_dir = PREVIEW / f"v{version}"
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = (PREVIEW / f"初賽簡報_v{version}.pdf").resolve()
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
            png = (png_dir / f"slide-{i:02d}.png").resolve()
            pres.Slides(i).Export(str(png), "PNG", 1920, 1080)
        return (
            f"已用 PowerPoint 匯出 `deck/preview/初賽簡報_v{version}.pdf`"
            f" 與 `deck/preview/v{version}/slide-01.png`–`slide-{n:02d}.png`。"
        )
    except Exception as exc:
        return f"PowerPoint 匯出失敗，略過預覽：{exc}"
    finally:
        if pres is not None:
            pres.Close()
        if app is not None:
            app.Quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="產生初賽簡報。每次改動要升版號。")
    parser.add_argument("--version", default=DECK_VERSION, help="版號 X.Y，預設 DECK_VERSION")
    parser.add_argument("--note", required=True, help="一句變更說明，寫進 CHANGELOG")
    parser.add_argument("--force", action="store_true", help="同版號已在 versions/ 時仍覆寫")
    return parser.parse_args()


def deck_pptx(version: str) -> Path:
    return ROOT / "deck" / f"初賽簡報_v{version}.pptx"


def archive_pptx(version: str) -> Path:
    return VERSIONS / f"初賽簡報_v{version}.pptx"


def preview_pdf(version: str) -> Path:
    return PREVIEW / f"初賽簡報_v{version}.pdf"


def ensure_version_available(version: str, force: bool) -> None:
    path = archive_pptx(version)
    if path.exists() and not force:
        raise SystemExit(
            f"版本已存在：deck/versions/初賽簡報_v{version}.pptx。"
            "請升號（小改 +0.1，PO 審過的里程碑升整數），或加上 --force 覆寫。"
        )


def git_short_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "git rev-parse 失敗")
    return result.stdout.strip()


def prepend_changelog(version: str, slides: int, content: int, note: str) -> None:
    safe = " ".join(note.split()).replace("|", "｜")
    row = (
        f"| v{version} | {date.today().isoformat()} | {git_short_head()} "
        f"| {slides}／{content} | {safe} | — |"
    )
    if not CHANGELOG.exists():
        CHANGELOG.write_text(
            "\n".join([
                "# 初賽簡報變更紀錄",
                "",
                row,
                "",
            ]),
            encoding="utf-8",
        )
        return
    lines = CHANGELOG.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("| ---"):
            lines.insert(i + 1, row)
            CHANGELOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise SystemExit("CHANGELOG.md 找不到表格分隔列，無法插入紀錄")


def publish_copies(version: str) -> None:
    src = deck_pptx(version)
    VERSIONS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, ROOT / "deck" / "初賽簡報_latest.pptx")
    shutil.copy2(src, archive_pptx(version))
    pdf = preview_pdf(version)
    if pdf.exists() and pdf.stat().st_size > 0:
        shutil.copy2(pdf, PREVIEW / "初賽簡報_latest.pdf")
        shutil.copy2(pdf, VERSIONS / f"初賽簡報_v{version}.pdf")


def assert_notes() -> None:
    if len(NOTES) != 22 or len(SLIDES) != 20 or len(BUILDERS) != 20:
        raise SystemExit(
            f"NOTES / SLIDES / BUILDERS 數量不一致：{len(NOTES)} / {len(SLIDES)} / {len(BUILDERS)}"
        )
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
                 "團隊：回廠率研究所", "初賽提案簡報（v2，2026-10）"]
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
    args = parse_args()
    version = args.version.strip()
    if version.startswith("v") or version.startswith("V"):
        version = version[1:]
    if not version:
        raise SystemExit("請用 --version 指定版號，例如 2.4。")
    if not args.note or not args.note.strip():
        raise SystemExit("請用 --note 寫一句變更說明，否則無法寫入變更紀錄。")
    ensure_version_available(version, args.force)
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
    if len(prs.slides) != 22:
        raise SystemExit(f"頁數應為 22，實際 {len(prs.slides)}")
    content = sum(1 for m in SLIDES if not m["id"].startswith("A"))
    if content != 15:
        raise SystemExit(f"內容頁應為 15，實際 {content}")
    for i, slide in enumerate(prs.slides, 1):
        note = slide.notes_slide.notes_text_frame.text.strip()
        if not note:
            raise SystemExit(f"第 {i} 頁沒有備註")
    out = deck_pptx(version)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    check = Presentation(str(out))
    if len(check.slides) != 22:
        raise SystemExit("重開後頁數不是 22")
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
    preview_note = export_preview(out, version)
    publish_copies(version)
    prepend_changelog(version, len(check.slides), content, args.note.strip())
    write_readme(check, placeholders, preview_note, version)
    print(f"version={version} slides={len(check.slides)} content={content} placeholders={len(placeholders)}")
    print(preview_note)
    for page, pid, text in placeholders:
        print(f"  p{page} {pid} {text}")


if __name__ == "__main__":
    main()
