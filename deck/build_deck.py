# -*- coding: utf-8 -*-
"""初賽簡報。文案與數字集中在本檔前半；不要在這裡重算統計。

版號見 DECK_VERSION。每次改動要升號：小改 +0.1，PO 審過的里程碑升整數。
可用 --version X.Y 覆蓋；--note 必填，寫進 deck/CHANGELOG.md。

重跑：python deck/build_deck.py --version X.Y --note "一句變更說明"
模板：attachments/2026和泰AI黑客松＿初賽簡報模板.pptx
輸出：deck/初賽簡報_vX.Y.pptx、deck/初賽簡報_latest.pptx、deck/README.md；
若本機有 PowerPoint，另匯 deck/preview/初賽簡報_vX.Y.pdf 與 deck/preview/vX.Y/。
內容是 v3.5（摘要、大綱、P1–P14、附錄 A0–A5）。投影片 23 張，沒有封面。
v3.5：拿掉自製封面，提案摘要成為第 1 頁（主辦方信：「提案摘要須置於簡報第一頁，並於同一頁內完整呈現」；
模板第 1 張是規則說明頁，不是封面，建置時刪除）。全冊頁碼與「第 N 頁」引用前移 1；內容、數字、版面不變。
v3.4：F9 圖例移到圖外上方、F6 的 n 標籤避開對角線且圖區加高；全冊文字套用中日韓換行禁則
（eaLnBrk／hangingPunct、lang=zh-TW），標點不再落行首；人物卡加高；數值標籤上移；流程卡標題齊頂。
v3.3 全頁版面重做：內容頁與附錄的卡片、字級、標籤位置統一；F1–F7 與資料處理鏈改用 pptx 原生形狀畫，
數字讀 reports/figures/figure_values.json（pipeline/make_figures.py --values-only）；F8 在第 8 頁與附錄 A0
都用原生形狀（draw_f8）；只有 F9 季趨勢仍貼 PNG。摘要頁左欄是模板，不動。
頁數算法：提案摘要第 1 頁不計入；計入 15 頁的是大綱 1 張（第 2 頁）加內容頁 14 張（第 3–16 頁）；
附錄 7 張（第 17–23 頁，含 A0）不計入。依據是主辦方信「15 頁內，提案摘要及附錄不計入頁數」。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
# 版號。每次改簡報內容都要升號：小改 +0.1，PO 審過的里程碑升整數。
# --version X.Y 可覆蓋。同版號已在 deck/versions/ 時，未加 --force 會中止。
DECK_VERSION = "3.5"
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
    "摘要給評審三層目標：回廠率假設加十點，核准八成，模型每季重驗。",
    "大綱列出六個章節與頁碼，並標示兩大產出各落在哪幾頁。",
    "提案分成兩份產出：一份輿情洞察，一份對準四種客群的溝通。",
    "三個前兆並行，不是依序發生：過保、刪項、間隔拉長。",
    "零件勝算比二點五八、價格二點六四，分母兩萬一千句。",
    "出口在一般外廠；定保口述中位原廠九千、外廠三千五，不是公告價。",
    "長句門檻是Q3+1.5×IQR，超過78字只標記。",
    "八層對到雙迴路：上面是產出一，下面是產出二，審核後才投遞。",
    "分群只獨立支持靜默出走者；其餘 Persona（客群輪廓）用規則定義。",
    "高風險七成四真有流失句；過保精算派人最多，平均風險也最高。",
    "人工兩人 κ 0.40，不一致處要經仲裁後才成為金標。",
    "r4 原值 P 0.617、R 0.769、κ 0.642。",
    "別人看不到不抱怨就走的人；我們給規則和機率，每句都能回原句。",
    "四種人配三種進廠時機，十二則已過查核，投遞前仍要人工審。",
    "人工篩選工時省九成以上（估），五項風險都已有對策。",
    "每季三百句金標、兩人共五小時，審核回饋持續再訓練。",
    "上方是兩個迴路；下方審核佇列是線框，決賽再給可操作版。",
    "附錄術語表：每個名詞一句定義、一句本案用法，評審追問時翻這頁。",
    "附錄前兩張圖：三站發言者流失率，以及高中低風險分布。",
    "附錄後兩張圖：校準曲線五個信心桶，以及季趨勢預警。",
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
        [("1. 從公開輿情 21,183 句售後語料自動標註流失意圖與九大面向，找出 4 種流失 Persona（客群輪廓）。", INK, False)],
        [("2. 本機自訓 System-One 決策模型即時給出流失機率與可解釋規則，發言者層級高／中／低分級。", INK, False)],
        [("3. Persona（客群輪廓） × 接觸點的 RAG 關懷內容生成，價格與保固只引用官方知識庫並經人工審核。", INK, False)],
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
        "id": "TOC",
        "section": "大綱（計入 15 頁）",
        "title": "六個章節、兩大產出，對照頁碼",
        "source": "來源：本簡報章節；兩大產出依企業挑戰題",
        "reports": ["raw/bh-challenge.txt"],
        "figures": [],
    },
    {
        "id": "P1",
        "section": "1 提案概述",
        "title": "提案是兩份產出：輿情洞察，以及對準客群的溝通",
        "source": "來源：企業挑戰題、統計檢定報告（T7）、殘餘切分報告（T3）",
        "reports": [
            "raw/bh-challenge.txt",
            "reports/T7_stats_tests.md",
            "reports/T3_residual_split_report.md",
        ],
        "figures": [],
    },
    {
        "id": "P2",
        "section": "2 目標對象與痛點分析",
        "title": "售後是人走了才知道；輿情能提前預警",
        "source": "來源：統計檢定（T7）、專案架構、風險報告（T10）；門檻見附錄 A4",
        "reports": [
            "reports/T7_stats_tests.md",
            "專案架構_2026-09-23.md",
            "reports/T10_risk_persona_report.md",
            "輿情訊號對應CRM欄位_草稿_2026-09-28.md",
        ],
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
        "source": "來源：風險與 Persona（客群輪廓）報告（T10）、專案架構、知識庫價格摘錄（T11）",
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
        "source": "來源：資料品質與去識別（T7）、趨勢報告（T15）；圖 F9_pipeline。季趨勢圖見附錄 A2b",
        "reports": [
            "題目選擇分析_2026-09-22.md",
            "reports/T7_data_quality.md",
            "reports/T7_deid_report.md",
            "reports/T15_trend_reports.md",
        ],
        "figures": ["reports/figures/F9_pipeline.png"],
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
        "source": "來源：風險與 Persona（客群輪廓）報告（T10）；圖 F5。未分類處置見 9/30 會議記錄",
        "reports": ["reports/T10_risk_persona_report.md", "會議記錄_2026-09-30.md"],
        "figures": ["reports/figures/F5.png"],
    },
    {
        "id": "P8",
        "section": "3 解決方案設計",
        "title": "高風險車主 74% 確有流失句，分級可信",
        "source": "來源：風險與 Persona（客群輪廓）報告（T10）；圖 F7",
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
        "source": "來源：本機模型報告（T8）；校準曲線見附錄 A2b",
        "reports": ["reports/T8_r4_report.md", "專案架構_2026-09-23.md"],
        "figures": [],
    },
    {
        "id": "P11",
        "section": "5 獨特優勢與差異化",
        "title": "看得見沒抱怨就走的人，分數說得出原因",
        "source": "來源：風險與 Persona（客群輪廓）報告（T10）、本機模型報告（T8）、專案架構",
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
        "id": "A0",
        "section": "附錄 A0 補充資料（不計入 15 頁）",
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
    ("L5", "Persona（客群輪廓）", "規則指派四種流失樣貌"),
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
    r_pr.set("lang", "zh-TW")  # 配合段落的 eaLnBrk，PowerPoint 才套用中日韓換行禁則
    for tag, face in (("a:latin", "Arial"), ("a:ea", "微軟正黑體"), ("a:cs", "Arial")):
        el = r_pr.find(qn(tag))
        if el is None:
            el = etree.SubElement(r_pr, qn(tag))
        el.set("typeface", face)


def set_tf(tf, blocks, size: float, align=None, anchor: str = "t", space_after: float = 2) -> None:
    tf.clear()
    tf.word_wrap = True
    body_pr = tf._txBody.bodyPr
    body_pr.set("anchor", anchor)
    for i, runs in enumerate(blocks):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align is not None:
            p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(space_after)
        p.line_spacing = 1.0
        # 中日韓換行禁則：行首不出現「，」「。」「）」等，句尾標點可懸掛在右邊界外。
        p_pr = p._p.get_or_add_pPr()
        p_pr.set("eaLnBrk", "1")
        p_pr.set("hangingPunct", "1")
        for item in runs:
            text, color, bold = item[0], item[1], item[2]
            sz = item[3] if len(item) > 3 else size
            run = p.add_run()
            run.text = text
            style_run(run, sz, bold, color)


def add_text(slide, x, y, w, h, blocks, size=14, align=None, anchor="t", margin=0.04, name=None, space_after=2):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    set_tf(tf, blocks, size, align, anchor, space_after=space_after)
    if name:
        box.name = name
    return box


def add_vtext(slide, x, y, w, h, text, size=14, color=MUTED, name=None):
    """直排（由下往上讀）的文字框，給圖表的縱軸標籤用。框本身仍是窄而高的矩形。"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0.02))
    set_tf(tf, [[(text, color, False, size)]], size, align=PP_ALIGN.CENTER, anchor="ctr")
    tf._txBody.bodyPr.set("vert", "vert270")
    if name:
        box.name = name
    return box


def add_card(slide, x, y, w, h, fill="F4F7FB", line=None, name=None, radius=0.08):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    try:
        shape.adjustments[0] = radius
    except Exception:
        pass
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1.25)
    if name:
        shape.name = name
    return shape


def add_rect(slide, x, y, w, h, fill=None, line=None, width=1.0, name=None, dashed=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill) if isinstance(fill, str) else fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(width)
        if dashed:
            shape.line.dash_style = MSO_LINE.DASH
    if name:
        shape.name = name
    return shape


def card_text(slide, x, y, w, h, blocks, size=16, fill="F4F7FB", line=None,
              pad_x=0.14, pad_y=0.06, anchor="t", align=None, name=None):
    """卡片＋同一組內距的文字框。全冊卡片內文統一用這個：左右 0.14、上下 0.06。"""
    card = add_card(slide, x, y, w, h, fill=fill, line=line, name=name)
    add_text(slide, x + pad_x, y + pad_y, w - 2 * pad_x, h - 2 * pad_y, blocks,
             size=size, anchor=anchor, align=align)
    return card


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
    cell.margin_top = Inches(0.03)
    cell.margin_bottom = Inches(0.03)
    set_tf(cell.text_frame, blocks, size, align, anchor="ctr")
    set_cell_fill(cell, fill)
    cell.text_frame.word_wrap = True


def add_table(slide, x, y, w, h, rows, col_w, font=12, header=True, row_h=None):
    """rows: list of list of blocks (each cell is a list of paragraphs).
    row_h：每列高度（吋）清單；沒給就平均分。PowerPoint 只會把列撐高，不會縮矮。"""
    n_r, n_c = len(rows), len(rows[0])
    graphic = slide.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(w), Inches(h))
    table = graphic.table
    for i, cw in enumerate(col_w):
        table.columns[i].width = Inches(cw)
    if row_h is not None:
        if len(row_h) != n_r:
            raise SystemExit(f"row_h 應有 {n_r} 列，給了 {len(row_h)}")
        for i, rh in enumerate(row_h):
            table.rows[i].height = Inches(rh)
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
                fill = "F4F7FB"
            paint_cell(table.cell(r, c), blocks, font, "44546A" if header_cell else fill)
    return graphic


def est_lines(text: str, width_in: float, pt: float) -> int:
    """估算一段文字在某寬度、字級下的行數（與 check_layout 同一套字寬）。"""
    width = max(width_in, 0.3)
    lines, used = 1, 0.0
    for ch in text:
        o = ord(ch)
        if ch.isspace():
            cw = pt / 72.0 * 0.33
        elif o > 0x2E00 or ch in "，。、；：？！（）「」『』％":
            cw = pt / 72.0
        else:
            cw = pt / 72.0 * 0.55
        if used + cw > width and used > 0:
            lines += 1
            used = cw
        else:
            used += cw
    return lines


def table_row_heights(rows, col_w, font, header_h=0.40, pad=0.10, min_h=0.30):
    """依每格最長段落估行數，給 add_table 的 row_h。回傳 (heights, total)。"""
    heights = []
    for r, row in enumerate(rows):
        if r == 0:
            heights.append(header_h)
            continue
        need = 0.0
        for c, blocks in enumerate(row):
            cell_lines = 0
            for para in blocks:
                text = "".join(run[0] for run in para)
                pt = max((run[3] if len(run) > 3 else font) for run in para) if para else font
                cell_lines += est_lines(text, col_w[c] - 0.14, pt)
            need = max(need, cell_lines * (font / 72.0 * 1.2))
        heights.append(max(min_h, need + pad))
    return heights, sum(heights)


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


def file_page(slide_id: str) -> int:
    for i, meta in enumerate(SLIDES):
        if meta["id"] == slide_id:
            return i + 2
    raise KeyError(slide_id)


def page_span(ids: list[str]) -> str:
    nums = sorted(set(file_page(i) for i in ids))
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append(str(start) if start == prev else f"{start}–{prev}")
        start = prev = n
    ranges.append(str(start) if start == prev else f"{start}–{prev}")
    return "、".join(ranges)


# 產出 1 涵蓋概述、痛點與輿情、雙迴路、Persona、風險、標註與模型。
# 產出 2 涵蓋雙迴路、話術與效益、附錄 A0 審核線框，以及待料／門檻／客訴附錄。
OUT1_IDS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
OUT2_IDS = ["P6", "P12", "P13", "P14", "A0", "A3", "A4", "A5"]

# 內容區：標題下緣 1.08 吋到頁尾來源列上方 7.02 吋。
BOT = 7.02


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
        set_cell_fill(cell, "F4F7FB")
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
    """依圖檔實際比例放入方框，水平置中。"""
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


# ---------------------------------------------------------------------------
# 原生圖表。數字讀 reports/figures/figure_values.json（pipeline/make_figures.py --values-only），
# 與 F1–F7 畫上去的值相同；這裡只畫，不重算。形狀名稱以 chart 開頭，check_layout 不把圖區當文字卡。
# ---------------------------------------------------------------------------
RED = RGBColor(0xC0, 0x39, 0x2B)
RED_MID = RGBColor(0xE0, 0x7A, 0x72)
RED_LIGHT = RGBColor(0xF3, 0xC1, 0xBD)
BLUE_MID = RGBColor(0x5C, 0x84, 0xB0)
BLUE_LIGHT = RGBColor(0xA9, 0xC3, 0xDC)
GRID = RGBColor(0xD9, 0xDF, 0xE6)
AXIS = RGBColor(0x8A, 0x94, 0x9E)
CHART_FILL = "F4F7FB"
_FIGV = None


def figv() -> dict:
    global _FIGV
    if _FIGV is None:
        path = FIG / "figure_values.json"
        if not path.exists():
            raise SystemExit(f"缺少 {path}：先跑 python pipeline/make_figures.py --values-only")
        _FIGV = json.loads(path.read_text(encoding="utf-8"))
    return _FIGV


def fmt_int(n) -> str:
    return f"{int(round(n)):,}"


def add_line(slide, x1, y1, x2, y2, color=GRID, width=0.75, dashed=False, name="chart-line"):
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = color
    line.line.width = Pt(width)
    if dashed:
        line.line.dash_style = MSO_LINE.DASH
    line.name = name
    return line


def nice_ticks(ymax: float, n: int = 4):
    """回傳 0 到 ymax 的等距刻度值（含 0，不含超過 ymax 的）。"""
    import math

    raw = ymax / n
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for step in (1, 2, 2.5, 5, 10):
        if raw <= step * mag:
            step *= mag
            break
    ticks = []
    v = 0.0
    while v <= ymax + 1e-9:
        ticks.append(v)
        v += step
    return ticks


def chart_bars(slide, x, y, w, h, cats, vals, *, errs=None, highlight=None, title=None,
               ylabel=None, fmt="{:.1f}", ymax=None, ticks=True, tick_fmt=None,
               label_size=15, value_size=16, title_size=16, color=BLUE, hi_color=RED,
               name="chart", card=True, bar_frac=0.62, pad=0.14, value_lift=0.0, value_fill=None):
    """長條圖：方塊、數值標籤、類別標籤、刻度與縱軸標籤都是 pptx 物件。
    errs：每根的 (lo, hi) 絕對值，畫成誤差線。highlight：要標紅的索引。
    value_lift：數值標籤再往上移的吋數（離開誤差線頂端）。value_fill：標籤框底色，蓋住穿過的格線。"""
    if card:
        add_card(slide, x, y, w, h, fill=CHART_FILL, name=f"{name}:card")
    top = y + 0.08
    y_top = top  # 縱軸標籤框從標題頂端起算，標題框左緣讓出 0.40 吋給它
    if title:
        add_text(slide, x + pad + 0.40, top, w - 2 * pad - 0.40, 0.32, [[(title, INK, True, title_size)]],
                 size=title_size, align=PP_ALIGN.CENTER, anchor="ctr", name=f"{name}:title")
        top += 0.36
    cat_h = 0.34
    py = top + 0.32  # 最高那根上方留給數值標籤
    ph = y + h - 0.10 - cat_h - py
    left = x + pad
    if ylabel:
        ylabel_box(slide, left, y_top, py + ph + cat_h - y_top, ylabel, name)
        left += 0.36
    tick_w = 0.0
    hi_vals = [e[1] for e in errs] if errs else vals
    data_max = max(max(vals), max(hi_vals))
    ymax = ymax or data_max * 1.06
    tick_vals = nice_ticks(ymax, max(2, int(ph / 0.42))) if ticks else []
    if ticks:
        tick_w = 0.55 if max(tick_vals) >= 1000 else 0.42
    px = left + tick_w + 0.04
    pw = x + w - pad - 0.04 - px

    def ypos(v):
        return py + ph - ph * v / ymax

    for t in tick_vals:
        yy = ypos(t)
        add_line(slide, px, yy, px + pw, yy, color=GRID, width=0.75)
        if ticks:
            label = (tick_fmt or (lambda v: f"{v:g}"))(t)
            add_text(slide, left, yy - 0.12, tick_w, 0.24, [[(label, MUTED, False, 13)]],
                     size=13, align=PP_ALIGN.RIGHT, anchor="ctr", margin=0.0, name=f"{name}:tick")
    add_line(slide, px, py + ph, px + pw, py + ph, color=AXIS, width=1.0)
    n = len(cats)
    slot = pw / n
    bw = slot * bar_frac
    lab_w = min(bw + 0.5, slot - 0.02)
    for i, (cat, v) in enumerate(zip(cats, vals)):
        bx = px + i * slot + (slot - bw) / 2
        by = ypos(v)
        c = hi_color if (highlight is not None and i == highlight) else color
        if by < py + ph - 0.005:
            add_rect(slide, bx, by, bw, py + ph - by, fill=c, name=f"{name}:bar")
        label_bottom = by
        if errs:
            lo, hi = errs[i]
            y_lo, y_hi = ypos(lo), ypos(hi)
            cx = bx + bw / 2
            add_line(slide, cx, y_hi, cx, y_lo, color=INK, width=1.25)
            add_line(slide, cx - 0.08, y_hi, cx + 0.08, y_hi, color=INK, width=1.25)
            add_line(slide, cx - 0.08, y_lo, cx + 0.08, y_lo, color=INK, width=1.25)
            label_bottom = min(by, y_hi)
        lx = bx + bw / 2 - lab_w / 2
        txt = fmt.format(v)
        vx, vw = lx, lab_w
        if value_fill:  # 有底色時框只比字寬一點，格線只在字的位置被遮住；類別標籤仍用 lx／lab_w
            vw = min(lab_w, sum(0.06 if ch in ".," else 0.115 for ch in txt) * value_size / 16 + 0.10)
            vx = bx + bw / 2 - vw / 2
        vbox = add_text(slide, vx, label_bottom - 0.30 - value_lift, vw, 0.28,
                        [[(txt, INK, True, value_size)]], size=value_size,
                        align=PP_ALIGN.CENTER, anchor="b", margin=0.0, name=f"{name}:value")
        if value_fill:
            vbox.fill.solid()
            vbox.fill.fore_color.rgb = RGBColor.from_string(value_fill)
        add_text(slide, lx, py + ph + 0.03, lab_w, cat_h - 0.03,
                 [[(cat, INK, False, label_size)]], size=label_size,
                 align=PP_ALIGN.CENTER, anchor="t", margin=0.0, name=f"{name}:cat")
    return py + ph


def ylabel_box(slide, left, top, avail_h, text, name):
    """縱軸標籤：直排一欄。字數乘字高放得下就用 13pt，否則 12pt；框高拉到類別標籤底，避免折成兩欄。"""
    size = 13 if len(text) * 13 / 72 + 0.1 <= avail_h else 12
    add_vtext(slide, left, top, 0.34, avail_h, text, size=size, name=f"{name}:ylabel")


def chart_stacked(slide, x, y, w, h, cats, series, colors_by_cat, *, title=None, ylabel=None,
                  legend=None, totals=True, name="chart", pad=0.14, value_lift=0.0):
    """堆疊長條：series = [(label, [v per cat]), ...] 由下往上疊；colors_by_cat[cat_index][series_index]。"""
    add_card(slide, x, y, w, h, fill=CHART_FILL, name=f"{name}:card")
    top = y + 0.08
    y_top = top
    if title:
        add_text(slide, x + pad + 0.40, top, w - 2 * pad - 0.40, 0.32, [[(title, INK, True, 16)]],
                 size=16, align=PP_ALIGN.CENTER, anchor="ctr", name=f"{name}:title")
        top += 0.36
    cat_h = 0.34
    py = top + 0.32
    ph = y + h - 0.10 - cat_h - py
    left = x + pad
    if ylabel:
        ylabel_box(slide, left, y_top, py + ph + cat_h - y_top, ylabel, name)
        left += 0.36
    sums = [sum(vals[i] for _, vals in series) for i in range(len(cats))]
    ymax = max(sums) * 1.08
    tick_vals = nice_ticks(ymax, 3)
    tick_w = 0.55
    px = left + tick_w + 0.04
    pw = x + w - pad - 0.04 - px

    def ypos(v):
        return py + ph - ph * v / ymax

    for t in tick_vals:
        yy = ypos(t)
        add_line(slide, px, yy, px + pw, yy, color=GRID, width=0.75)
        add_text(slide, left, yy - 0.14, tick_w, 0.28, [[(fmt_int(t), MUTED, False, 13)]],
                 size=13, align=PP_ALIGN.RIGHT, anchor="ctr", margin=0.0, name=f"{name}:tick")
    add_line(slide, px, py + ph, px + pw, py + ph, color=AXIS, width=1.0)
    n = len(cats)
    slot = pw / n
    bw = slot * 0.56
    for i, cat in enumerate(cats):
        bx = px + i * slot + (slot - bw) / 2
        base = 0.0
        for s, (_label, vals) in enumerate(series):
            v = vals[i]
            if v <= 0:
                continue
            y1, y0 = ypos(base + v), ypos(base)
            if y0 - y1 >= 0.01:
                add_rect(slide, bx, y1, bw, y0 - y1, fill=colors_by_cat[i][s], name=f"{name}:bar")
            base += v
        if totals:
            add_text(slide, bx - 0.25, ypos(sums[i]) - 0.30 - value_lift, bw + 0.5, 0.28,
                     [[(fmt_int(sums[i]), INK, True, 16)]], size=16,
                     align=PP_ALIGN.CENTER, anchor="b", margin=0.0, name=f"{name}:value")
        add_text(slide, bx - 0.2, py + ph + 0.03, bw + 0.4, cat_h - 0.03,
                 [[(cat, INK, False, 15)]], size=15, align=PP_ALIGN.CENTER, anchor="t",
                 margin=0.0, name=f"{name}:cat")
    if legend:
        lx = x + w - pad - sum(0.22 + 0.06 + len(lbl) * 0.11 + 0.18 for lbl, _ in legend)
        ly = top + 0.02
        for lbl, col in legend:
            add_rect(slide, lx, ly + 0.06, 0.22, 0.16, fill=col, name=f"{name}:legend")
            lw = len(lbl) * 0.11 + 0.18
            add_text(slide, lx + 0.26, ly, lw, 0.28, [[(lbl, INK, False, 13)]], size=13,
                     anchor="ctr", margin=0.0, name=f"{name}:legend")
            lx += 0.22 + 0.06 + lw
    return py + ph


BLUES = [(247, 251, 255), (222, 235, 247), (198, 219, 239), (158, 202, 225), (107, 174, 214),
         (66, 146, 198), (33, 113, 181), (8, 81, 156), (8, 48, 107)]


def blues(t: float) -> RGBColor:
    t = min(max(t, 0.0), 1.0) * (len(BLUES) - 1)
    i = int(t)
    if i >= len(BLUES) - 1:
        r, g, b = BLUES[-1]
    else:
        f = t - i
        r, g, b = (round(BLUES[i][k] + (BLUES[i + 1][k] - BLUES[i][k]) * f) for k in range(3))
    return RGBColor(int(r), int(g), int(b))


def chart_heatmap(slide, x, y, w, h, rows, cols, matrix, *, title=None, legend=None, name="chart", pad=0.14):
    """熱圖：每格一個矩形加數字；最大格套紅框。rows 直排、cols 橫排。"""
    add_card(slide, x, y, w, h, fill=CHART_FILL, name=f"{name}:card")
    top = y + 0.08
    legend_w = 3.0 if legend else 0.0
    if title:
        add_text(slide, x + pad, top, w - 2 * pad - legend_w, 0.32, [[(title, INK, True, 16)]],
                 size=16, align=PP_ALIGN.CENTER, anchor="ctr", name=f"{name}:title")
        top += 0.38
    if legend:
        add_text(slide, x + w - pad - legend_w, y + 0.08, legend_w, 0.32,
                 [[(legend, MUTED, False, 13)]], size=13, align=PP_ALIGN.RIGHT, anchor="ctr",
                 margin=0.0, name=f"{name}:legend")
    row_label_w = 1.35
    col_h = 0.34
    gx = x + pad + row_label_w
    gw = x + w - pad - gx
    gy = top
    gh = y + h - 0.10 - col_h - gy
    cw = gw / len(cols)
    ch = gh / len(rows)
    vmax = max(max(r) for r in matrix)
    best = max(((v, i, j) for i, r in enumerate(matrix) for j, v in enumerate(r)))[1:]
    for i, label in enumerate(rows):
        add_text(slide, x + pad, gy + i * ch, row_label_w - 0.06, ch, [[(label, INK, False, 15)]],
                 size=15, align=PP_ALIGN.RIGHT, anchor="ctr", margin=0.0, name=f"{name}:row")
        for j, v in enumerate(matrix[i]):
            cx, cy = gx + j * cw, gy + i * ch
            add_rect(slide, cx, cy, cw, ch, fill=blues(v / vmax), name=f"{name}:cell")
            color = WHITE if v > vmax * 0.62 else INK
            add_text(slide, cx, cy, cw, ch, [[(f"{v:.0f}", color, False, 16)]], size=16,
                     align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name=f"{name}:cellv")
    bi, bj = best
    add_rect(slide, gx + bj * cw, gy + bi * ch, cw, ch, fill=None, line=RED, width=2.25, name=f"{name}:best")
    for j, label in enumerate(cols):
        add_text(slide, gx + j * cw, gy + gh + 0.03, cw, col_h - 0.03, [[(label, INK, False, 14)]],
                 size=14, align=PP_ALIGN.CENTER, anchor="t", margin=0.0, name=f"{name}:col")


def chart_scatter(slide, x, y, w, h, points, *, title=None, xlabel=None, ylabel=None, name="chart", pad=0.14):
    """校準散點：points = [(mean%, rate%, n)]；對角虛線是完美校準。"""
    add_card(slide, x, y, w, h, fill=CHART_FILL, name=f"{name}:card")
    top = y + 0.08
    y_top = top
    if title:
        add_text(slide, x + pad + 0.40, top, w - 2 * pad - 0.40, 0.32, [[(title, INK, True, 16)]],
                 size=16, align=PP_ALIGN.CENTER, anchor="ctr", name=f"{name}:title")
        top += 0.36
    tick_h = 0.26
    xl_h = 0.26
    py = top + 0.10  # v3.4：n 標籤不再放到圖區上方，頂端留白縮到 0.10，圖區加高
    left = x + pad
    tick_w = 0.42
    px = left + 0.36 + tick_w + 0.04
    pw = x + w - pad - 0.30 - px
    ph = y + h - 0.06 - xl_h - tick_h - py
    if ylabel:
        ylabel_box(slide, left, y_top, py + ph + tick_h - y_top, ylabel, name)

    def xpos(v):
        return px + pw * v / 100

    def ypos(v):
        return py + ph - ph * v / 100

    for t in (0, 50, 100):
        add_line(slide, px, ypos(t), px + pw, ypos(t), color=GRID, width=0.75)
        add_text(slide, left + 0.36, ypos(t) - 0.12, tick_w, 0.24, [[(str(t), MUTED, False, 13)]], size=13,
                 align=PP_ALIGN.RIGHT, anchor="ctr", margin=0.0, name=f"{name}:tick")
    for t in (20, 40, 60, 80, 100):  # 原點的 0 由縱軸刻度標，橫軸不重複標
        add_line(slide, xpos(t), py, xpos(t), py + ph, color=GRID, width=0.75)
        add_text(slide, xpos(t) - 0.3, py + ph + 0.03, 0.6, tick_h - 0.03, [[(str(t), MUTED, False, 13)]], size=13,
                 align=PP_ALIGN.CENTER, anchor="t", margin=0.0, name=f"{name}:tick")
    add_line(slide, px, py + ph, px + pw, py + ph, color=AXIS, width=1.0)
    add_line(slide, px, py, px, py + ph, color=AXIS, width=1.0)
    # 完美校準的對角虛線：用旋轉的極薄矩形畫，外框不會像斜向連接線那樣罩住整個圖區。
    # 淡灰細線，先畫、再畫點與 n 標籤，所以在標籤之下。
    import math

    length = math.hypot(pw, ph)
    diag = add_rect(slide, px + pw / 2 - length / 2, py + ph / 2 - 0.005, length, 0.01,
                    fill=None, line=GRID, width=0.75, dashed=True, name=f"{name}:diag")
    diag.rotation = -math.degrees(math.atan2(ph, pw))
    if xlabel:
        add_text(slide, px, py + ph + tick_h, pw, xl_h, [[(xlabel, MUTED, False, 14)]], size=14,
                 align=PP_ALIGN.CENTER, anchor="t", margin=0.0, name=f"{name}:xlabel")
    nmax = max(n for _, _, n in points)
    lab_w, lab_h = 0.62, 0.24

    def place_label(cx, cy, d):
        """n 標籤位置：依序試「點上方、點下方、點右側、右上」，取第一個在圖區內、又不被對角線穿過的。
        對角線是 y=x（百分比座標），穿過矩形 [x0,x1]×[y0,y1] 的條件是 x0 <= y1 且 y0 <= x1。"""
        cands = [
            (cx - lab_w / 2, cy - d / 2 - 0.02 - lab_h, PP_ALIGN.CENTER),
            (cx - lab_w / 2, cy + d / 2 + 0.02, PP_ALIGN.CENTER),
            (cx + d / 2 + 0.05, cy - lab_h / 2, PP_ALIGN.LEFT),
            (cx + d / 2 + 0.05, cy - d / 2 - 0.02 - lab_h, PP_ALIGN.LEFT),
        ]
        for lx, ly, align in cands:
            x0, x1 = (lx - px) / pw * 100, (lx + lab_w - px) / pw * 100
            y1, y0 = (py + ph - ly) / ph * 100, (py + ph - ly - lab_h) / ph * 100
            inside = lx >= px - 0.02 and lx + lab_w <= px + pw + 0.02 and ly >= py - 0.02 and ly + lab_h <= py + ph + 0.01
            crossed = x0 <= y1 and y0 <= x1
            if inside and not crossed:
                return lx, ly, align
        raise SystemExit(f"F6 的 n 標籤找不到不被對角線穿過的位置（點 {cx:.2f},{cy:.2f}）")

    for mx, ry, n in points:
        d = 0.14 + 0.14 * (n / nmax) ** 0.5
        cx, cy = xpos(mx), ypos(ry)
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
        dot.fill.solid()
        dot.fill.fore_color.rgb = RED if mx >= 80 else BLUE
        dot.line.fill.background()
        dot.name = f"{name}:dot"
        lx, ly, align = place_label(cx, cy, d)
        add_text(slide, lx, ly, lab_w, lab_h, [[(f"n={n}", INK, False, 15)]], size=15,
                 align=align, anchor="ctr", margin=0.0, name=f"{name}:n")


# ---------------------------------------------------------------------------
# 各頁 builder。所有卡片用 card_text 的內距；數字卡「數字 26–28 藍粗、說明 15」；
# 編號用 add_pill；流程方塊用 F7FBFF 底、藍框。
# ---------------------------------------------------------------------------

TOC_BLURB = {
    "1": "21,183 句；186 句沒抱怨就走",
    "2": "零件 17.3%；一般外廠 736 句",
    "3": "雙迴路、511 人、高風險 74%",
    "4": "兩段式 98.4%；r4 F1 0.685",
    "5": "128 位靜默出走者看得到",
    "6": "12 則主表＋4 則附錄已查核",
}
TOC_TAG = {
    "1": "產出 1",
    "2": "產出 1",
    "3": "產出 1＋2",
    "4": "產出 1",
    "5": "支撐兩份產出",
    "6": "產出 2",
}


def add_pill(slide, x, y, w, h, text, size=12, fill=BLUE, color=WHITE):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        shape.adjustments[0] = 0.3
    except Exception:
        pass
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    tf = shape.text_frame
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0.01))
    set_tf(tf, [[(text, color, True, size)]], size, align=PP_ALIGN.CENTER, anchor="ctr")
    return shape


def build_toc(slide, y):
    groups = []
    for meta in SLIDES:
        if not meta["id"].startswith("P"):
            continue
        sec = meta["section"]
        if not groups or groups[-1]["section"] != sec:
            groups.append({"section": sec, "ids": [meta["id"]]})
        else:
            groups[-1]["ids"].append(meta["id"])
    appendix = [m["id"] for m in SLIDES if m["id"].startswith("A")]
    rows = []
    for g in groups:
        key = g["section"].split()[0]
        name = g["section"].split(" ", 1)[1]
        pages = page_span(g["ids"])
        rows.append((key, name, f"第 {pages} 頁", TOC_TAG[key], TOC_BLURB[key]))
    rows.append(("附", "附錄", f"第 {page_span(appendix)} 頁", "不計入 15 頁", "補充資料、術語、圖表與話術"))
    # 左欄：七列章節；右欄：兩份產出。
    left_w = 7.55
    gap = 0.08
    row_h = (BOT - y - 6 * gap) / 7
    for i, (key, name, pages, tag, blurb) in enumerate(rows):
        yy = y + i * (row_h + gap)
        add_card(slide, ML, yy, left_w, row_h)
        add_pill(slide, ML + 0.14, yy + (row_h - 0.44) / 2, 0.44, 0.44, key, size=16,
                 fill=NAVY if key == "附" else BLUE)
        add_text(
            slide, ML + 0.70, yy + 0.06, left_w - 0.84, row_h - 0.12,
            [
                [(name, INK, True, 18), ("　", INK, True, 18), (pages, BLUE, True, 18)],
                [(tag, NAVY, True, 15), ("　", INK, False, 15), (blurb, INK, False, 15)],
            ],
            size=15, anchor="ctr",
        )
    right_x = ML + left_w + 0.14
    right_w = CW - left_w - 0.14
    out_h = (BOT - y - 0.10) / 2
    blocks = [
        (
            "產出 1",
            "AI 網路輿情洞察系統架構與報告",
            [
                "客群 Persona、高風險議題、市場輿情、AI 技術／模型。",
                f"落在第 {page_span(OUT1_IDS)} 頁。",
                "21,183 句、四種流失 Persona、r4 F1 0.685。",
                "高風險 1,049 人，74% 真有流失句。",
            ],
        ),
        (
            "產出 2",
            "針對目標 Persona（客群輪廓）的 AI 溝通計畫與系統流程",
            [
                "核心溝通策略、AI 生成內容、接觸點、運作流程圖。",
                f"落在第 {page_span(OUT2_IDS)} 頁（第 {file_page('A0')} 頁為附錄 A0）。",
                "12 則主表＋4 則附錄已查核。",
                "待料 A3、門檻 A4、客訴 A5。人工核准才發。",
            ],
        ),
    ]
    for i, (head, title, lines) in enumerate(blocks):
        yy = y + i * (out_h + 0.10)
        card_text(
            slide, right_x, yy, right_w, out_h,
            [
                [(head, BLUE, True, 20)],
                [(title, INK, True, 16)],
                *[[(line, INK, False, 15)] for line in lines],
            ],
            size=15, fill="EAF1F8",
        )


def build_p1(slide, y):
    # 上帶：為什麼要做。三站流失率各一格，句子放右邊。
    band_h = 0.98
    add_card(slide, ML, y, CW, band_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.14, y + 0.08, 1.95, band_h - 0.16,
        [[("為什麼要做", BLUE, True, 18)], [("論壇發言者流失率", INK, True, 14)], [("χ²=99.5", NAVY, False, 14)]],
        size=14, anchor="ctr",
    )
    stats = [("18.2%", "Mobile01"), ("14.1%", "PTT"), ("6.8%", "Dcard")]
    sx = ML + 2.15
    for num, site in stats:
        add_text(
            slide, sx, y + 0.06, 1.55, band_h - 0.12,
            [[(num, BLUE, True, 26)], [(site, INK, True, 14)]],
            size=14, align=PP_ALIGN.CENTER, anchor="ctr",
        )
        sx += 1.55
    add_text(
        slide, sx + 0.10, y + 0.08, ML + CW - 0.14 - sx - 0.10, band_h - 0.16,
        [[("1,671 句流失中，186 句沒抱怨就找出口。母體是論壇發言者，不是全體車主。", INK, False, 15)]],
        size=15, anchor="ctr",
    )
    gap = 0.14
    card_w = (CW - gap) / 2
    card_y = y + band_h + 0.12
    card_h = BOT - card_y
    left = [
        ("客群 Persona（客群輪廓）", "四種流失樣貌；過保精算派 511 人", f"第 {file_page('P7')} 頁"),
        ("高風險議題", "零件供應 17.3%、價格 15.0%", f"第 {file_page('P3')} 頁"),
        ("整體市場輿情", "售後語料 21,183 句；186 句沒抱怨就走", f"第 {file_page('P5')} 頁"),
        ("AI 技術／模型", "r4 本機模型 F1 0.685", f"第 {file_page('P6')}、{file_page('P10')} 頁"),
    ]
    right = [
        ("核心溝通策略", "對的人、對的時機開口", f"第 {file_page('P12')} 頁"),
        ("AI 生成內容範例", "12 則主表已對 76 條條款查核", f"第 {file_page('P12')} 頁；附錄 A3、A5"),
        ("精準接觸點", "保固前 60 天、間隔拉長、刪項後", f"第 {file_page('P12')} 頁"),
        ("運作流程圖", "洞察與溝通雙迴路，人工核准才發", f"第 {file_page('P6')}、{file_page('A0')} 頁"),
    ]
    panels = [
        ("產出 1", "AI 網路輿情洞察系統架構與報告", left),
        ("產出 2", "針對目標 Persona（客群輪廓）的 AI 溝通計畫與系統流程", right),
    ]
    head_h = 0.70
    for i, (head, title, items) in enumerate(panels):
        x = ML + i * (card_w + gap)
        add_card(slide, x, card_y, card_w, card_h)
        add_text(
            slide, x + 0.14, card_y + 0.06, card_w - 0.28, head_h,
            [[(head, BLUE, True, 20)], [(title, INK, True, 15)]],
            size=15,
        )
        row_top = card_y + head_h + 0.12
        row_h = (card_h - head_h - 0.20) / 4
        for n, (name, body, page) in enumerate(items, start=1):
            yy = row_top + (n - 1) * row_h
            if n > 1:
                add_line(slide, x + 0.14, yy - 0.02, x + card_w - 0.14, yy - 0.02, color=GRID, width=0.75, name="divider")
            add_pill(slide, x + 0.14, yy + 0.08, 0.36, 0.36, str(n), size=14)
            add_text(
                slide, x + 0.62, yy + 0.02, card_w - 0.76, row_h - 0.06,
                [
                    [(name, INK, True, 18)],
                    [(body, INK, False, 16)],
                    [(page, BLUE, True, 15)],
                ],
                size=16, anchor="ctr",
            )


def flow_box(slide, x, y, w, h, blocks, size=15, line=BLUE, fill="F7FBFF", align=PP_ALIGN.CENTER):
    """流程方塊：淡藍底、藍框、文字置中。全冊的流程圖（第 4、7、8、17 頁）共用。"""
    card = add_card(slide, x, y, w, h, fill=fill, line=line)
    add_text(slide, x + 0.08, y + 0.05, w - 0.16, h - 0.10, blocks, size=size, align=align, anchor="ctr")
    return card


def down_arrow(slide, cx, y, h=0.22, w=0.22, color=BLUE):
    arrow = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(cx - w / 2), Inches(y), Inches(w), Inches(h))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()
    return arrow


def build_p2(slide, y):
    # 上半：As-Is／To-Be 左、三個訊號右；下半：三個前兆並排匯流（已核准的邏輯，不動）。
    upper = 2.50
    left_w = 7.80
    gap = 0.10
    card_h = (upper - gap) / 2
    card_text(
        slide, ML, y, left_w, card_h,
        [
            [("As-Is", BLUE, True, 18)],
            [("只靠客訴與回廠紀錄，人流失之後才知道。1,671 句裡 186 句沒抱怨就找出口。", INK, False, 15)],
            [("使用者是售後決策者與服務廠客戶關係人員。", MUTED, False, 14)],
        ],
        size=15, pad_x=0.12,
    )
    card_text(
        slide, ML, y + card_h + gap, left_w, card_h,
        [
            [("To-Be", BLUE, True, 18)],
            [("三個訊號並行。到期前 90 天進名單，第 60 天再開口。", INK, False, 15)],
            [("公開輿情加上 CRM，在離開原廠之前先辨識。", INK, False, 15)],
        ],
        size=15, pad_x=0.12,
    )
    right_x = ML + left_w + 0.14
    right_w = CW - left_w - 0.14
    shorts = [
        ("過保", "到期前先找到人"),
        ("刪項", "回廠時再問一次"),
        ("間隔拉長", "超過週期就提醒"),
    ]
    rh = (upper - 2 * 0.08) / 3
    for i, (head, body) in enumerate(shorts):
        yy = y + i * (rh + 0.08)
        card_text(slide, right_x, yy, right_w, rh,
                  [[(head, INK, True, 17)], [(body, INK, False, 15)]], size=15, pad_y=0.05, anchor="ctr")
    flow_y = y + upper + 0.12
    flow_h = BOT - flow_y
    add_card(slide, ML, flow_y, CW, flow_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.14, flow_y + 0.06, CW - 0.28, 0.30,
        [[("三個前兆並排，匯流後才是離開；資料沒有先後順序", NAVY, True, 14)]],
        size=14, margin=0.0, anchor="ctr",
    )
    precursors = [
        ("過保", "過保 62 句、保固內 17 句", "觸發：到期前 90 天"),
        ("刪項", "連續 2 次拒項", "拒絕估價項目就列管"),
        ("間隔拉長", "逾期超過建議週期", "1.5 倍"),
    ]
    inner_x, inner_w = ML + 0.14, CW - 0.28
    gap_x = 0.12
    bw = (inner_w - 2 * gap_x) / 3
    by = flow_y + 0.42
    arrow_h = 0.24
    merge_h = 0.58
    out_h = 0.58
    bh = BOT - 0.14 - out_h - arrow_h - merge_h - arrow_h - by
    for i, (head, line, sub) in enumerate(precursors):
        xx = inner_x + i * (bw + gap_x)
        flow_box(slide, xx, by, bw, bh,
                 [[(head, INK, True, 18)], [(line, BLUE, True, 16)], [(sub, NAVY, False, 15)]], size=15)
        down_arrow(slide, xx + bw / 2, by + bh + 0.02, h=arrow_h - 0.04)
    merge_y = by + bh + arrow_h
    flow_box(slide, inner_x, merge_y, inner_w, merge_h,
             [[("離開原廠", INK, True, 18), ("　　人走了才知道", NAVY, False, 15)]], size=16)
    down_arrow(slide, ML + CW / 2, merge_y + merge_h + 0.02, h=arrow_h - 0.04)
    out_y = merge_y + merge_h + arrow_h
    flow_box(slide, inner_x, out_y, inner_w, out_h,
             [[("一般外廠　736 句", BLUE, True, 20), ("　　可複選", NAVY, False, 15)]], size=16)


def stat_chips(slide, y, items, num_size=26, label_size=15, h=0.98):
    """一列四格數字卡：數字藍粗、說明一行。回傳下一個 y。"""
    gap = 0.10
    n = len(items)
    chip_w = (CW - (n - 1) * gap) / n
    for i, (num, label) in enumerate(items):
        x = ML + i * (chip_w + gap)
        card_text(slide, x, y, chip_w, h,
                  [[(num, BLUE, True, num_size)], [(label, INK, False, label_size)]],
                  size=label_size, align=PP_ALIGN.CENTER, anchor="ctr", pad_x=0.08)
    return y + h + 0.10


def note_bar(slide, y, h, text, size=16, fill="EAF1F8", bold=False):
    """內容區底部的一行說明。h 低於 0.7 時不列入卡片留白檢查。"""
    card_text(slide, ML, y, CW, h, [[(text, INK, bold, size)]], size=size, fill=fill, anchor="ctr")


def build_p3(slide, y):
    y = stat_chips(slide, y, [
        ("17.3%", "零件供應最高"),
        ("15.0%", "價格次高"),
        ("1.4%", "銷售交車最低"),
        ("61%", "態度負面；流失 4.7%"),
    ])
    note_h = 0.62
    rows = figv()["F1"]
    chart_bars(
        slide, ML, y, CW, BOT - note_h - 0.10 - y,
        [r["name"] for r in rows], [r["p"] * 100 for r in rows],
        errs=[(r["lo"] * 100, r["hi"] * 100) for r in rows], highlight=0,
        title="零件供應流失率最高（17.3%），銷售交車最低", ylabel="流失率（%）",
        name="chart:F1",
    )
    note_bar(slide, BOT - note_h, note_h,
             "對應接觸點：待料通知（R5），話術見附錄 A3。零件勝算比 2.58、價格 2.64，分母 21,183 句。")


def build_p4(slide, y):
    y = stat_chips(slide, y, [
        ("736", "一般外廠（句）"),
        ("234／135", "自備料／DIY"),
        ("62／17", "過保／保固內"),
        ("9,000／3,500", "定保口述價"),
    ], num_size=24)
    note_h = 0.62
    rows = figv()["F3"]
    chart_bars(
        slide, ML, y, CW, BOT - note_h - 0.10 - y,
        [r["name"] for r in rows], [r["n"] for r in rows], highlight=0, fmt="{:,.0f}",
        title="1,671 句流失裡，替代去向以一般外廠最多（736 句）", ylabel="句數（一句可多選）",
        tick_fmt=fmt_int, name="chart:F3",
    )
    note_bar(slide, BOT - note_h, note_h,
             "去向可複選，母體 1,671 句流失。定保價是論壇口述中位數，原廠 9,000、外廠 3,500，不是公告價。")


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

    table_h = 2.56
    row_h = [0.40] + [(table_h - 0.40) / 5] * 5
    add_table(slide, ML, y, 6.05, table_h, pairs(scale_rows_l, scale_rows_r), [3.15, 2.90], font=15, row_h=row_h)
    add_table(slide, ML + 6.35, y, 6.07, table_h, pairs(qual_l, qual_r), [3.35, 2.72], font=15, row_h=row_h)
    note_y = y + table_h + 0.10
    note_h = 0.80
    card_text(
        slide, ML, note_y, CW, note_h,
        [[(
            "去識別：文本遮蔽 517 次，抽查 50 句（seed 42）漏網 0。"
            "超過 78 字的長句占 7.77%，只標記、不刪除。21,183 句仍全部進入標註。",
            INK, False, 17,
        )]],
        size=17, anchor="ctr",
    )
    trend_y = note_y + note_h + 0.10
    trend_h = 0.56
    note_bar(slide, trend_y, trend_h,
             "整體輿情：2026Q3 流失率 4.2%，上季 5.3%，去年同季 10.9%（至 9/19）。佐證見附錄 A2b 的 F9。", size=16)
    # 資料處理鏈（原 F9_pipeline.png），改畫原生方塊：數字轉抄 P5 與 T7 品質報告。
    pipe_y = trend_y + trend_h + 0.10
    pipe_h = BOT - pipe_y
    add_card(slide, ML, pipe_y, CW, pipe_h)
    nodes = [
        ("爬取留言", "22.5 萬則"),
        ("切句・去重・去識別", "23.6 萬句"),
        ("售後關鍵詞篩選", "21,183 句"),
        ("五指標品質檢查", "超過 78 字只標記"),
        ("進入標註", "供模型與報告"),
    ]
    inner_x, inner_w = ML + 0.14, CW - 0.28
    gap = 0.22
    bw = (inner_w - 4 * gap) / 5
    bh = pipe_h - 0.24
    by = pipe_y + 0.12
    for i, (title, sub) in enumerate(nodes):
        xx = inner_x + i * (bw + gap)
        flow_box(slide, xx, by, bw, bh,
                 [[(str(i + 1), BLUE, True, 26)], [(title, INK, True, 16)], [(sub, NAVY, False, 16)]], size=16)
        if i < 4:
            add_arrow(slide, xx + bw + 0.04, by + bh / 2, xx + bw + gap - 0.04, by + bh / 2, width=1.75)


# 第 8 頁（P6）與附錄 A0 用原生形狀畫 F8：方塊、L# 標籤、連接線都是 pptx 物件，投影不會糊。
# 文字逐字對齊 pipeline/make_flow_figure.py；只重排換行，不刪字。
F8_PROC, F8_DB, F8_DB_EDGE = "EAF1F8", "F6EFE3", RGBColor(0x8A, 0x6D, 0x3B)
F8_HUMAN, F8_HUMAN_EDGE = "F3C1BD", RGBColor(0xC0, 0x39, 0x2B)
F8_BAND_TOP, F8_BAND_BOT = "F7F9FC", "FBF7F7"
F8_GREY = RGBColor(0x5C, 0x65, 0x70)
F8_BODY = RGBColor(0x3C, 0x46, 0x53)
F8_FONT = 13


def add_flow_box(slide, x, y, w, h, head, body, fill=F8_PROC, edge=BLUE, tag=None, dashed=False, thick=False, size=F8_FONT, max_lines=None):
    """方塊＋粗體標題＋置中內文；L# 標籤貼右上角內緣，標題框讓出標籤寬度。"""
    card = add_card(slide, x, y, w, h, fill=fill, line=edge)
    card.line.width = Pt(2.0 if thick else 1.25)
    if dashed:
        card.line.dash_style = MSO_LINE.DASH
    # 標題與內文同一個文字框：標題靠左，內文置中；標籤最後畫，壓在右上角。
    box = add_text(
        slide, x + 0.02, y + 0.04, w - 0.04, h - 0.06,
        [[(head, INK, True, size)]] + [[(line, F8_BODY, False, size)] for line in body],
        size=size,
    )
    for para in box.text_frame.paragraphs[1:]:
        para.alignment = PP_ALIGN.CENTER
    # 內文行數少於同列最多行數時，內文往下推半個差額，上下留白平均。
    slack_lines = (max_lines or len(body)) - len(body)
    if slack_lines > 0:
        box.text_frame.paragraphs[1].space_before = Pt(slack_lines * (size * 1.15 + 2) / 2)
    if tag:
        pill_w = 0.42 if len(tag) <= 2 else 0.92
        add_pill(slide, x + w - pill_w - 0.06, y + 0.07, pill_w, 0.24, tag)
    return card


def add_arrow(slide, x1, y1, x2, y2, color=BLUE, width=1.5, head=True, both=False):
    line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = color
    line.line.width = Pt(width)
    ln = line.line._get_or_add_ln()
    if both:
        ln.append(ln.makeelement(qn("a:headEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    if head or both:
        ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return line


def draw_f8(slide, y, *, compact=False):
    """畫 F8 雙迴路。compact=False 是第 8 頁（含八層圖例與說明列）；
    compact=True 給附錄 A0：兩帶標題各併成一行、資料庫列矮一點、不畫圖例，回傳下緣 y。"""
    gap = 0.10
    size = F8_FONT
    # ---- 上帶：產出 1，七個方塊，欄寬依內文最長一行配置 ----
    # compact 只把上帶標題併成一行；下帶的溝通迴路說明太長，仍維持兩行。
    head_h = 0.34 if compact else 0.56
    bot_head_h = 0.56
    top_y, top_h = y, head_h + 1.10
    add_card(slide, ML, top_y, CW, top_h, fill=F8_BAND_TOP)
    if compact:
        add_text(slide, ML + 0.10, top_y + 0.05, CW - 0.2, 0.26,
                 [[("產出 1：AI 網路輿情洞察系統架構與報告", BLUE, True, size),
                   ("　洞察迴路｜每日排程：新留言 → 標註與風險 → 日報 → Dashboard", BLUE, False, 12)]], size=size)
    else:
        add_text(slide, ML + 0.10, top_y + 0.05, CW - 0.2, 0.26,
                 [[("產出 1：AI 網路輿情洞察系統架構與報告", BLUE, True, size)]], size=size)
        add_text(slide, ML + 0.10, top_y + 0.29, CW - 0.2, 0.25,
                 [[("洞察迴路｜每日排程：新留言 → 標註與風險 → 日報 → Dashboard", BLUE, False, 12)]], size=12)
    tw = [1.46, 1.74, 1.68, 2.00, 1.96, 1.42, 1.56]
    top = [
        ("論壇爬蟲", ["每日抓新留言", "三站公開論壇"], F8_PROC, BLUE, "L0", False),
        ("去重・去識別", ["作者雜湊、店名", "人名遮蔽（L1）"], F8_PROC, BLUE, "L1", False),
        ("資料庫 B", ["原始輿情", "去識別版，可溯源"], F8_DB, F8_DB_EDGE, "L2", False),
        ("流失判斷", ["r4 逐句判流失、面向", "→ 風險分數 →", "Persona（客群輪廓）"], F8_PROC, BLUE, "L3·L4·L5", False),
        ("洞察報告", ["日報・週報・季報", "趨勢分析、200% 預警"], F8_PROC, BLUE, None, False),
        ("資料庫 A", ["報告池", "日／週／季報、", "預警紀錄"], F8_DB, F8_DB_EDGE, None, False),
        ("Dashboard 1–3", ["1 戰情總覽", "2 報告池・", "3 原始輿情"], F8_PROC, BLUE, None, True),
    ]
    box_y, box_h = top_y + head_h, 1.06
    xs = []
    x = ML
    for w in tw:
        xs.append(x)
        x += w + gap
    for bx, w, (head, body, fill, edge, tag, dashed) in zip(xs, tw, top):
        add_flow_box(slide, bx, box_y, w, box_h, head, body, fill=fill, edge=edge, tag=tag, dashed=dashed, max_lines=3)
    for bx, w in zip(xs[:-1], tw[:-1]):
        add_arrow(slide, bx + w, box_y + 0.50, bx + w + gap, box_y + 0.50)
    risk_x = xs[3] + tw[3] / 2  # 流失判斷底緣中點

    # ---- 兩帶之間：風險升為高 → 觸發 ----
    band_gap = 0.26 if compact else 0.32
    mid_y = top_y + top_h + band_gap / 2
    bot_y = top_y + top_h + band_gap
    gut_x = ML + 0.10  # 直向線走帶內左緣
    bot_box_y, bot_box_h = bot_y + bot_head_h, 1.06
    db_h = 0.80 if compact else 0.98
    db_y = bot_box_y + bot_box_h + 0.16
    red_y = db_y + db_h + 0.08
    # 底卡先畫，灰線與紅線才不會被蓋住。第 8 頁沿用 v3.2 的高度（留 0.94 吋給圖例與說明列）。
    bot_h = (red_y + 0.10 - bot_y) if compact else (BOT - 0.94 - bot_y)
    add_card(slide, ML, bot_y, CW, bot_h, fill=F8_BAND_BOT)
    add_arrow(slide, risk_x, box_y + box_h, risk_x, mid_y, color=F8_GREY, width=1.25, head=False)
    add_arrow(slide, risk_x, mid_y, gut_x, mid_y, color=F8_GREY, width=1.25, head=False)
    add_arrow(slide, gut_x, mid_y, gut_x, bot_box_y + 0.30, color=F8_GREY, width=1.25, head=False)
    add_arrow(slide, gut_x, bot_box_y + 0.30, ML + 0.22, bot_box_y + 0.30, color=F8_GREY, width=1.25)
    lab = add_text(slide, (xs[1] + xs[2] + tw[2]) / 2 - 0.9, mid_y - 0.13, 1.8, 0.26,
                   [[("風險升為高 → 觸發", F8_GREY, False, 12)]], size=12, align=PP_ALIGN.CENTER)
    lab.fill.solid()
    lab.fill.fore_color.rgb = WHITE

    # ---- 下帶：產出 2，六個方塊＋資料庫列 ----
    add_text(slide, ML + 0.26, bot_y + 0.05, CW - 0.36, 0.26,
             [[("產出 2：針對目標 Persona（客群輪廓）的 AI 溝通計畫與系統流程", F8_HUMAN_EDGE, True, size)]], size=size)
    add_text(slide, ML + 0.26, bot_y + 0.29, CW - 0.36, 0.25,
             [[("溝通迴路｜事件觸發：CRM 訊號・客訴結案 → Persona（客群輪廓）→ RAG 話術 → 人工核准 → 投遞 → KPI 回饋", F8_HUMAN_EDGE, False, 12)]], size=12)
    bw = [2.81, 1.80, 2.05, 1.79, 1.61, 1.74]
    bot = [
        ("觸發事件", ["CRM 命中 R1–R8（含 R5 待料）", "客訴結案 → 第 7 天回訪", "或風險分數升為高"], F8_PROC, BLUE, "L4", False),
        ("判定 Persona", ["（客群輪廓）", "四類之一", "未分類 → 觀察名單"], F8_PROC, BLUE, "L5", False),
        ("RAG 生成話術", ["檢索條款 → 生成", "→ 第二輪事實查核"], F8_PROC, BLUE, "L6", False),
        ("人工審核", ["Dashboard 5 ", "審核佇列", "核准或改寫才投遞"], F8_HUMAN, F8_HUMAN_EDGE, None, True),
        ("投遞", ["LINE・App", "Email・專員電話"], F8_PROC, BLUE, "L7", False),
        ("KPI 回饋", ["點擊・預約・回廠", "寫回 CRM"], F8_PROC, BLUE, "L7", False),
    ]
    bxs = []
    x = ML + 0.22
    for w in bw:
        bxs.append(x)
        x += w + 0.08
    for bx, w, (head, body, fill, edge, tag, thick) in zip(bxs, bw, bot):
        add_flow_box(slide, bx, bot_box_y, w, bot_box_h, head, body, fill=fill, edge=edge, tag=tag, thick=thick, max_lines=3)
    for bx, w in zip(bxs[:-1], bw[:-1]):
        add_arrow(slide, bx + w, bot_box_y + 0.50, bx + w + 0.08, bot_box_y + 0.50)

    # 第 1 欄：灰字註記（觸發事件下方）
    add_text(slide, bxs[0], db_y, bw[0], db_h,
             [[("客訴回訪不計頻率上限；", F8_GREY, False, size)], [("觀察名單車主也回訪", F8_GREY, False, size)]], size=size, anchor="ctr")
    # 第 2 欄：紅色回饋說明，貼近底部紅線
    add_text(slide, bxs[1], db_y, bw[1], db_h,
             [[("回頭校正觸發門檻，", F8_HUMAN_EDGE, False, size)], [("再訓練 r4", F8_HUMAN_EDGE, False, size)]], size=size, anchor="b")
    # 第 3、4 欄：資料庫 C、D
    add_flow_box(slide, bxs[2], db_y, bw[2], db_h, "資料庫 C", ["知識庫 76 條・保固條款", "Dashboard 4 可查閱"], fill=F8_DB, edge=F8_DB_EDGE, max_lines=3 if not compact else None)
    add_arrow(slide, bxs[2] + bw[2] / 2, db_y, bxs[2] + bw[2] / 2, bot_box_y + bot_box_h, color=F8_DB_EDGE)
    add_flow_box(slide, bxs[3], db_y, bw[3], db_h, "資料庫 D", ["溝通佇列：草稿、", "審核狀態、投遞結果"], fill=F8_DB, edge=F8_DB_EDGE, max_lines=3 if not compact else None)
    add_arrow(slide, bxs[3] + bw[3] / 2, bot_box_y + bot_box_h, bxs[3] + bw[3] / 2, db_y, color=F8_DB_EDGE, both=True)
    # 第 5–6 欄：內網說明；右側留 0.28 吋給紅線直向段
    note_w = bw[4] + 0.08 + bw[5] - 0.28
    add_text(slide, bxs[4], db_y, note_w, db_h, [
        [("資料庫與模型都在和泰內網，不出門；", F8_BODY, False, size)],
        [("論壇文字只作研究語料，", F8_BODY, False, size)],
        [("上線後輸入改為工單與客訴文字。", F8_BODY, False, size)],
    ], size=size, anchor="ctr")

    # ---- 紅色回饋迴路：KPI 回饋 → 帶底 → 左緣 → 觸發事件 ----
    red_x = bxs[5] + bw[5] - 0.14
    add_arrow(slide, red_x, bot_box_y + bot_box_h, red_x, red_y, color=F8_HUMAN_EDGE, width=1.5, head=False)
    add_arrow(slide, red_x, red_y, gut_x, red_y, color=F8_HUMAN_EDGE, width=1.5, head=False)
    add_arrow(slide, gut_x, red_y, gut_x, bot_box_y + bot_box_h - 0.30, color=F8_HUMAN_EDGE, width=1.5, head=False)
    add_arrow(slide, gut_x, bot_box_y + bot_box_h - 0.30, ML + 0.22, bot_box_y + bot_box_h - 0.30, color=F8_HUMAN_EDGE, width=1.5)
    if compact:
        return bot_y + bot_h

    # ---- 八層圖例 ----
    legend_y = bot_y + bot_h + 0.06
    bar_h = 0.30
    bar_y = BOT - bar_h
    legend_h = bar_y - 0.06 - legend_y
    lgap = 0.08
    cell_w = (CW - 7 * lgap) / 8
    brief = {
        "L0": "三站已爬完",
        "L1": "切句去重",
        "L2": "標註入庫",
        "L3": "只出機率",
        "L4": "規則辨識",
        "L5": "四種客群",
        "L6": "引用知識庫",
        "L7": "核准才投遞",
    }
    for i, (code, name, _desc) in enumerate(LAYERS):
        x = ML + i * (cell_w + lgap)
        add_card(slide, x, legend_y, cell_w, legend_h)
        add_text(
            slide, x + 0.04, legend_y + 0.03, cell_w - 0.06, legend_h - 0.04,
            [
                [(code, BLUE, True, 13), ("  " + brief[code], INK, True, 13)],
                [(name if code != "L5" else "客群輪廓", MUTED, False, 12)],
            ],
            size=13,
        )
    add_card(slide, ML, bar_y, CW, bar_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.12, bar_y + 0.01, CW - 0.22, bar_h - 0.02,
        [[("先讀上帶產出 1（左到右），再讀下帶產出 2。外緣 L# 對下面八格。KPI 回頭校正門檻，再訓練 r4。", INK, False, 14)]],
        size=14, anchor="ctr",
    )
    return BOT


def build_p6(slide, y):
    draw_f8(slide, y, compact=False)


def build_p7(slide, y):
    gap = 0.10
    card_w = (CW - 3 * gap) / 4
    card_h = 1.72  # v3.4：加高 0.10 吋，第 1 張卡兩行引言不再貼到卡片下緣
    for i, (name, people, share, feature, quote) in enumerate(PERSONAS):
        x = ML + i * (card_w + gap)
        card_text(
            slide, x, y, card_w, card_h,
            [
                [(name, INK, True, 17)],
                [(f"{people}　{share}", BLUE, True, 18)],
                [(feature, INK, False, 14)],
                [(quote, NAVY, False, 13)],
            ],
            size=14, pad_x=0.12,
        )
    fig_y = y + card_h + 0.10
    foot_h = 0.58
    f5 = figv()["F5"]
    chart_heatmap(
        slide, ML, fig_y, CW, BOT - foot_h - 0.10 - fig_y,
        f5["personas"], f5["aspects"], f5["matrix"],
        title="過保精算派近半句子在談價格，品質失望派則集中在技術品質",
        legend="格內數字為面向出現比例（%）", name="chart:F5",
    )
    note_bar(slide, BOT - foot_h, foot_h,
             "分母：高、中風險 1,280 人。未分類 199 人列觀察名單，不投遞。Persona（客群輪廓）為規則定義，每項可回溯原句。", size=15)


def build_p8(slide, y):
    f7 = figv()["F7"]
    chart_h = 2.20
    add_card(slide, ML, y, CW, chart_h, fill=CHART_FILL, name="chart:F7:card")
    add_text(slide, ML + 0.14, y + 0.08, CW - 0.28, 0.32,
             [[("過保精算派人數最多，平均風險也最高", INK, True, 16)]],
             size=16, align=PP_ALIGN.CENTER, anchor="ctr", name="chart:F7:title")
    half = (CW - 0.30) / 2
    peak = max(range(len(f7["risks"])), key=lambda i: f7["risks"][i])
    chart_bars(slide, ML, y + 0.40, half, chart_h - 0.40, f7["personas"], f7["counts"],
               highlight=peak, fmt="{:,.0f}", ylabel="發言者數", tick_fmt=fmt_int,
               name="chart:F7a", card=False, label_size=13, value_lift=0.05, value_fill=CHART_FILL)
    chart_bars(slide, ML + half + 0.30, y + 0.40, half, chart_h - 0.40, f7["personas"], f7["risks"],
               highlight=peak, fmt="{:.2f}", ylabel="平均風險分", ymax=1.0,
               name="chart:F7b", card=False, label_size=13, value_lift=0.05, value_fill=CHART_FILL)
    note_y = y + chart_h + 0.08
    note_h = 0.50
    note_bar(slide, note_y, note_h,
             "高 1,049／中 231／低 5,114。高風險 74% 有流失句，低風險 1.8%。過保精算派 511 人，平均風險 0.73。", size=15)
    header = [cell_text(h, WHITE, True) for h in ("規則", "輿情訊號", "CRM 欄位")]
    body = [header]
    for code, signal in SIGNALS:
        body.append([
            cell_text(code, BLUE, True),
            cell_text(signal, INK, True),
            cell_text(CRM_FIELDS[code], INK, False),
        ])
    table_y = note_y + note_h + 0.08
    foot_h = 0.28
    table_h = BOT - foot_h - 0.04 - table_y
    row_h = [0.34] + [(table_h - 0.34) / 8] * 8
    add_table(slide, ML, table_y, CW, table_h, body, [1.1, 2.2, 9.12], font=13, row_h=row_h)
    add_text(
        slide, ML, BOT - foot_h, CW, foot_h,
        [[("CRM 欄位為業界通用假設，導入時以和泰 DMS 實際欄位替換；模型輸入由論壇文字改為工單備註與客訴文字，架構不變。", MUTED, False, 12)]],
        size=12, margin=0.0, anchor="ctr",
    )


def build_p9(slide, y):
    steps = [
        ("57%", "Haiku 初篩", "單獨召回約 57%。先把可能流失的句子留住，不能只靠這一段初篩。"),
        ("3,760", "帶上下文複核", "重疊 3,760 句。Mobile01、PTT 用 Sonnet，Dcard 用 GPT 再看一次。"),
        ("98.4%", "對得起來", "c≥2 一致率 98.4%。九面向標完，殘餘僅 4 句，不再另開面向。"),
    ]
    note_h = 0.86
    gap = 0.12
    left_w = 7.40
    body_h = BOT - note_h - gap - y
    step_h = (body_h - 2 * 0.10) / 3
    for i, (num, head, body) in enumerate(steps):
        yy = y + i * (step_h + 0.10)
        card_text(
            slide, ML, yy, left_w, step_h,
            [
                [(num, BLUE, True, 36), ("   " + head, INK, True, 20)],
                [(body, INK, False, 18)],
            ],
            size=18, anchor="ctr",
        )
    right_x = ML + left_w + gap
    right_w = CW - left_w - gap
    gold_h = (body_h - 0.12) / 2
    golds = [
        ("F1  0.82", BLUE, "本機模型，與 Sonnet 同級", "人工金標 300 句。正例僅 9 句，召回區間 0.45–0.94。0.82 還不是穩定成績。"),
        ("F1  0.50", ORANGE, "Haiku 零樣本", "同一批人工金標。召回約 57% 不夠，所以才要兩段式，不能只靠初篩。"),
    ]
    for i, (num, color, head, body) in enumerate(golds):
        yy = y + i * (gold_h + 0.12)
        card_text(
            slide, right_x, yy, right_w, gold_h,
            [[(num, color, True, 44)], [(head, INK, True, 22)], [(body, INK, False, 18)]],
            size=18, fill="FDEBD0", anchor="ctr", pad_x=0.12,
        )
    note_y = BOT - note_h
    card_text(
        slide, ML, note_y, CW, note_h,
        [
            [("九面向全量標完，殘餘僅 4 句。Haiku 單獨召回約 57%，所以第二段才複核。", INK, False, 18)],
            [("正例僅 9 句，召回區間 0.45–0.94。本機 F1 0.82 還不是穩定成績。", INK, False, 18)],
        ],
        size=18, fill="EAF1F8", anchor="ctr",
    )


def build_p10(slide, y):
    headers = ["", "P", "R", "F1", "κ"]
    haiku = ["Haiku 零樣本", "0.60", "0.55", "0.58", "0.53"]
    r4 = ["r4　4B", "0.62", "0.77", "0.685", "0.64"]
    rows = []
    for i, row in enumerate((headers, haiku, r4)):
        rows.append([cell_text(v, WHITE, True) if i == 0 else cell_text(v, INK, c == 0) for c, v in enumerate(row)])
    left_w = 6.15
    table_h = 1.14
    add_table(slide, ML, y, left_w, table_h, rows, [2.15, 1.0, 1.0, 1.0, 1.0], font=15, row_h=[0.36, 0.39, 0.39])
    note_y = y + table_h + 0.10
    prefill_x, prefill_w = ML + left_w + 0.25, CW - left_w - 0.25
    prefill_h = 1.86
    note_h = prefill_h - table_h - 0.10
    card_text(
        slide, ML, note_y, left_w, note_h,
        [[("同一 600 句測試集比較。", MUTED, False, 15)], [("校準曲線見附錄 A2b。", MUTED, False, 15)]],
        size=15, anchor="ctr",
    )
    lines = [
        "Prefill-only：只輸出各等級機率，不生成文字。",
        "8 GB 顯卡可訓（約 5 小時）、可推（每句 0.7 秒）。",
        "資料不出門，推論零 API 費。",
        "同一 600 句：r4 F1 0.685，高於 Haiku 的 0.58。",
    ]
    add_card(slide, prefill_x, y, prefill_w, prefill_h)
    add_text(
        slide, prefill_x + 0.14, y + 0.06, prefill_w - 0.28, 1.24,
        [[(line, INK, False, 16)] for line in lines],
        size=16,
    )
    # 小流程用頁上已有的說法：只取下一詞機率、只輸出各等級機率。
    chips = [("輸入", 1.05), ("只取下一詞機率", 2.05), ("各等級機率", 1.55)]
    chip_gap = 0.28
    chip_h = 0.42
    chip_y = y + prefill_h - chip_h - 0.08
    chip_x = prefill_x + 0.14
    for label, chip_w in chips:
        add_card(slide, chip_x, chip_y, chip_w, chip_h, fill="EAF1F8")
        add_text(
            slide, chip_x, chip_y + 0.04, chip_w, chip_h - 0.06,
            [[(label, BLUE, True, 14)]],
            size=14, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.02,
        )
        chip_x += chip_w
        if label != chips[-1][0]:
            add_text(
                slide, chip_x, chip_y, chip_gap, chip_h,
                [[("→", BLUE, True, 16)]],
                size=16, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0,
            )
            chip_x += chip_gap
    steps = [
        ("1 ETL＋弱監督標註", "篩出 21,183 句售後語料。先用 Haiku 寬鬆標，再用 Sonnet 或 GPT 帶上下文複核。c≥2 一致率 98.4%，殘餘僅 4 句。"),
        ("2 資料切分\n（防洩漏）", "GroupSplit 整篇排除測試 600 句。驗證 1,096 句，訓練池 9,431 句。同篇句子不進訓練，避免把成績高估。"),
        ("3 任務轉換", "流失四級拆成四個是非題。Prefill-only 只取下一詞在候選上的機率，不生成文字。每句約 0.7 秒，8 GB 顯卡可推，資料不出門。"),
        ("4 監督式微調 SFT", "Qwen3-4B，QLoRA r=16。流失句過採樣到四成。2 epoch，8 GB 顯卡約 5 小時。只訓低秩參數，推論零 API 費。"),
        ("5 評估與校準", "金標 300 句：F1 0.82、κ 0.81。另看精確率、召回與五段校準。最高信心桶 n=71、實際約 68%。曲線見附錄 A2b。"),
    ]
    gap = 0.10
    cw = (CW - 4 * gap) / 5
    sy = y + prefill_h + 0.12
    bar_h = 1.20
    bar_y = BOT - bar_h
    step_h = bar_y - 0.10 - sy
    for i, (head, body) in enumerate(steps):
        x = ML + i * (cw + gap)
        blocks = [[(line, BLUE, True, 16)] for line in head.split("\n")]
        blocks.append([(body, INK, False, 16)])
        card_text(slide, x, sy, cw, step_h, blocks, size=16, pad_x=0.10, anchor="t")  # 齊頂：五張卡標題同一高度
    card_text(
        slide, ML, bar_y, CW, bar_h,
        [
            [("架構沿用開源 LLM2Jev。8 GB 可訓可推，推論零 API 費。", INK, False, 16)],
            [("最高信心桶 n=71、實際約 68%（約七成），見附錄 A2b。", INK, False, 16)],
            [("同一 600 句測試集：r4 F1 0.685，高於 Haiku 零樣本的 F1 0.58。", INK, False, 16)],
        ],
        size=16, fill="EAF1F8", anchor="ctr",
    )


def build_p11(slide, y):
    cards = [
        ("128 人", "靜默出走者", "規則看替代去向，不靠客訴關鍵字。", "這 128 人裡，替代有 55% 是一般外廠。"),
        ("74%", "分數說得出原因", "風險＝模型機率 ×0.6＋命中規則／8 ×0.4。", "高風險 74% 真有流失句，低風險只有 1.8%。"),
        ("0 元", "本機就能跑", "Qwen3-4B，8 GB 約 5 小時，每句 0.7 秒。", "測試集 F1 0.685。CRM 文字不上雲。"),
        ("0.080", "只有一組被資料分開", "k=4 的 ARI 0.08，四個假設沒有全被拆開。", "簡報仍用可回溯原句的規則，不假裝分群已分開。"),
    ]
    gap_x, gap_y = 0.14, 0.10
    card_w = (CW - gap_x) / 2
    card_h = 1.32
    for i, (num, head, how, how2) in enumerate(cards):
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        card_text(
            slide, x, yy, card_w, card_h,
            [
                [(num, BLUE, True, 28), ("   " + head, INK, True, 18)],
                [(how, INK, False, 16)],
                [(how2, INK, False, 16)],
            ],
            size=16, anchor="ctr",
        )
    table_y = y + 2 * card_h + gap_y + 0.12
    rows = [
        [cell_text(h, WHITE, True) for h in ("", "只看客訴", "本案")],
        [cell_text("沒抱怨就走", INK, True), cell_text("看不到這群人"), cell_text("靜默出走者 128 人，替代 55% 到一般外廠")],
        [cell_text("分數", INK, True), cell_text("沒有原因"), cell_text("機率 6 成＋規則 4 成；高 74%、低 1.8%")],
        [cell_text("在哪裡算", INK, True), cell_text("資料得出門"), cell_text("8 GB 本機，每句 0.7 秒，F1 0.685，API 費 0")],
        [cell_text("四個客群", INK, True), cell_text("主觀標籤"), cell_text("ARI 0.08；只有靜默出走者被資料獨立支持")],
    ]
    table_h = BOT - table_y
    row_h = [0.40] + [(table_h - 0.40) / 4] * 4
    add_table(slide, ML, table_y, CW, table_h, rows, [1.7, 3.3, 7.42], font=16, row_h=row_h)


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
    header = [cell_text("Persona（客群輪廓）", WHITE, True)] + [cell_text(c, WHITE, True) for c in TOUCH_COLS]
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
    foot_h = 0.82
    table_h = BOT - y - foot_h - 0.12
    row_h = [0.42] + [(table_h - 0.42) / 4] * 4
    add_table(slide, ML, y, CW, table_h, rows, [2.08, 3.4467, 3.4467, 3.4466], font=14, row_h=row_h)
    foot_y = BOT - foot_h
    card_text(
        slide, ML, foot_y, CW, foot_h,
        [
            [("12 則對 76 條官方條款查核通過。人工核准才投遞。", INK, True, 17)],
            [("十二則只列前 40 字。待料全文見附錄 A3，客訴回訪見附錄 A5。", INK, False, 16)],
        ],
        size=16, anchor="ctr",
    )


def build_p13(slide, y):
    left_w = 5.35
    # 第三個數是高度權重：依標題一行加內文行數（15pt、寬 5.07 吋）估，內文 1 行 0.74、2 行 1.0、3 行 1.36。
    items = [
        ("需求", "人走了才知道。過保、刪項、間隔拉長時先找到人。", 0.74),
        ("技術", "判斷、分群、生成都有原型。8 條規則已對到 DMS 欄位。", 1.00),
        ("財務：人力成本節省", "人工逐句篩 2.1 萬句約需 106 人時（估）。本機模型 4.1 小時跑完，零 API 費。人力改花在審名單與話術。", 1.36),
        ("風險", "五項主要風險，對策與責任人見右表。", 0.72),
        ("怎麼讀右表", "技術：寫錯條款只引用 76 條並人工審；模糊句多報就當初篩。資料註明論壇母體，上線改 CRM。法規只用去識別版。客群寫成可回溯原句的規則。", 1.36),
    ]
    gap = 0.08
    avail = BOT - y - gap * (len(items) - 1)
    scale = avail / sum(rh for _, _, rh in items)
    yy = y
    for head, body, rh in items:
        rh *= scale
        card_text(
            slide, ML, yy, left_w, rh,
            [[(head, BLUE, True, 17)], [(body, INK, False, 15)]],
            size=15, anchor="ctr",
        )
        yy += rh + gap
    # 風險登錄表前 5 列（iPAS骨架頁_草稿.md）。四欄：層別、風險、對策、責任人。
    risks = [
        ("層別", "風險", "對策", "責任人"),
        ("技術", "生成內容寫錯價格或保固條款", "只引用 76 條知識庫、數字逐字比對、人工審核必經", "A"),
        ("技術", "模型在模糊句多報（困難層 F1 ≤ 0.51，精確率 0.34）", "定位成「初篩＋人工複核」", "A"),
        ("資料", "論壇代表性（正例 67% 來自 Mobile01，母體是論壇發言者）", "分析頁註明母體與來源構成；上線改用 CRM 資料", "B"),
        ("法規", "個資與再識別", "去識別流程，簡報與 Demo 只用去識別版", "A"),
        ("組織", "Persona（客群輪廓）被質疑主觀（ARI 0.08）", "寫成「規則定義、每項可回溯原句」", "B"),
    ]
    rows = []
    for i, cols in enumerate(risks):
        if i == 0:
            rows.append([cell_text(c, WHITE, True) for c in cols])
        else:
            rows.append([cell_text(cols[0], INK, True), cell_text(cols[1]), cell_text(cols[2]), cell_text(cols[3], BLUE, True)])
    table_h = BOT - y
    row_h = [0.42] + [(table_h - 0.42) / 5] * 5
    add_table(
        slide, ML + left_w + 0.14, y, CW - left_w - 0.14, table_h, rows,
        [0.78, 2.25, 3.02, 0.88],
        font=14, row_h=row_h,
    )


def build_p14(slide, y):
    # 說明列都放進淺底橫條，和其他頁的說明列同一個樣子，頁面也不會留白色空檔。
    note_bar(slide, y, 0.30, "層級對照 iPAS：成果＝業務、流程＝應用、模型＝系統", size=13, fill="F4F7FB")
    headers = ["層級", "指標", "現況", "目標"]
    data = [
        ("成果", "高風險車主 12 個月回廠率", "導入後建立基期", "提升 10 個百分點＊"),
        ("流程", "高風險名單更新頻率；話術人工核准率", "名單一次性產出；12 則主表＋4 則附錄已查核", "每月更新；核准率 ≥ 80%"),
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
    table_y = y + 0.38
    table_h = 1.50
    add_table(slide, ML, table_y, CW, table_h, rows, [1.0, 3.3, 3.9, 4.22], font=13,
              row_h=[0.34] + [(table_h - 0.34) / 4] * 4)
    foot_y = table_y + table_h + 0.06
    note_bar(slide, foot_y, 0.30, "＊假設值，導入後以基期實測校正。模型現況用隨機層人工金標，與目標同一把尺。", size=13, fill="F4F7FB")
    moat_y = foot_y + 0.40
    moat_h = 1.34
    card_text(
        slide, ML, moat_y, CW, moat_h,
        [
            [("數據護城河：三項資產，全部留在和泰內網", BLUE, True, 17)],
            [("語料：2.1 萬句標註＋300 句人工金標。每季重標，審核回饋持續再訓練。", INK, False, 15)],
            [("模型：自有 4B 模型，8 GB 顯卡 5 小時可重訓。推論零 API 費，資料不出門。", INK, False, 15)],
            [("知識庫：76 條官方條款＋每則話術查核紀錄。價格與保固只引用這 76 條。", INK, False, 15)],
        ],
        size=15, anchor="ctr",
    )
    phases = [
        ("資料接入", "4 週", "R1–R8 換成\nDMS 實際欄位\n工單去識別後接入"),
        ("模型校準", "4 週", "重標 300 句金標\n重驗 r4\n再調觸發門檻"),
        ("單一據點試行", "8 週", "一個服務廠跑完\n專員審核後投遞\n未核准不發出"),
        ("擴大至全台", "8 週", "依試行調話術\n與渠道分批上線\n不一次開全台"),
        ("持續監控", "不設終點", "日監控、週收樣本\n月重評客群輪廓\n季重驗模型"),  # 「Persona（客群輪廓）」一行放不下，改中文
    ]
    gap = 0.12
    card_w = (CW - 4 * gap) / 5
    base = moat_y + moat_h + 0.10
    total_h = 0.32
    phase_h = BOT - total_h - 0.10 - base
    for i, (name, weeks, doing) in enumerate(phases):
        x = ML + i * (card_w + gap)
        add_card(slide, x, base, card_w, phase_h)
        add_pill(slide, x + 0.12, base + 0.12, 0.36, 0.36, str(i + 1), size=14)
        add_text(
            slide, x + 0.56, base + 0.10, card_w - 0.66, 0.40,
            [[(name, BLUE, True, 16)]],
            size=16, anchor="ctr",
        )
        add_text(
            slide, x + 0.12, base + 0.56, card_w - 0.22, phase_h - 0.62,
            [
                [(weeks, NAVY, True, 15)],
                *[[(line, INK, False, 15)] for line in doing.split("\n")],
            ],
            size=15,
        )
    note_bar(slide, BOT - total_h, total_h, "合計約 24 週（持續監控不設終點）。", size=15, bold=True)


def build_p15(slide, y):
    """附錄 A0：上方雙迴路（原生 F8，緊湊版），下方審核佇列線框。"""
    bottom = draw_f8(slide, y, compact=True)
    rx, rw = ML, CW
    mock_y = bottom + 0.10
    rh = BOT - mock_y
    add_card(slide, rx, mock_y, rw, rh, fill="F4F7FB", line=NAVY)
    bar_h = 0.34
    bar = add_rect(slide, rx, mock_y, rw, bar_h, fill=NAVY)
    add_text(
        slide, rx + 0.14, mock_y + 0.02, rw - 0.28, bar_h - 0.04,
        [[("Dashboard 5　溝通審核佇列", WHITE, True, 14)]],
        size=14, anchor="ctr", margin=0.0,
    )
    body_y = mock_y + bar_h + 0.05
    body_h = rh - bar_h - 0.10
    # 左：佇列一筆的欄位；右：三個動作鈕，鈕下一行說明。
    btn_w, btn_gap, btn_h = 1.30, 0.10, 0.46
    right_w = 3 * btn_w + 2 * btn_gap
    right_x = rx + rw - 0.16 - right_w
    add_text(
        slide, rx + 0.16, body_y, 6.0, body_h,
        [
            [("車主 H-7F3A　風險 高", INK, True, 18)],
            [("Persona　過保精算派　觸發 R1 過保", INK, False, 18)],
            [("話術草稿　引用條目 41、52", NAVY, False, 18)],
        ],
        size=18, anchor="ctr",
    )
    labels = [("核准", "2F5D9F"), ("改寫", "44546A"), ("退回", "C05600")]
    btn_y = body_y + 0.04
    for i, (label, fill) in enumerate(labels):
        bx = right_x + i * (btn_w + btn_gap)
        add_card(slide, bx, btn_y, btn_w, btn_h, fill=fill)
        add_text(
            slide, bx, btn_y + 0.03, btn_w, btn_h - 0.06,
            [[(label, WHITE, True, 16)]],
            size=16, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0,
        )
    add_text(
        slide, right_x - 1.3, btn_y + btn_h + 0.04, right_w + 1.3, body_y + body_h - btn_y - btn_h - 0.04,
        [[("未核准不投遞。決賽再給可操作版。代號為示意，不是論壇帳號。", MUTED, False, 13)]],
        size=13, align=PP_ALIGN.RIGHT, anchor="t",
    )


SLIDES.append({
    "id": "A1",
    "section": "附錄 A1 術語表（不計入 15 頁）",
    "title": "本案用到的技術名詞：定義與在本案的用法",
    "source": "來源：本機模型報告（T8）、人工評估（T9）、風險與 Persona（客群輪廓）報告（T10）",
    "reports": ["reports/T8_r4_report.md", "reports/T9_human_eval.md", "reports/T10_risk_persona_report.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A2",
    "section": "附錄 A2 補充圖表（不計入 15 頁）",
    "title": "三站發言者流失率，與發言者風險分布",
    "source": "來源：統計檢定報告（T7）、風險與 Persona（客群輪廓）報告（T10）；圖 F2、F4",
    "reports": ["reports/T7_stats_tests.md", "reports/T10_risk_persona_report.md"],
    "figures": ["reports/figures/F2.png", "reports/figures/F4.png"],
})
SLIDES.append({
    "id": "A2b",
    "section": "附錄 A2b 補充圖表（不計入 15 頁）",
    "title": "校準曲線，與季趨勢預警",
    "source": "來源：本機模型報告（T8）、趨勢報告（T15）；圖 F6、F9",
    "reports": ["reports/T8_r4_report.md", "reports/T15_trend_reports.md"],
    "figures": ["reports/figures/F6.png", "reports/figures/F9.png"],
})
SLIDES.append({
    "id": "A3",
    "section": "附錄 A3 待料通知話術（不計入 15 頁）",
    "title": "待料逾 7 天就主動通知，話術不寫到貨日",
    "source": "來源：話術範例、生成與查核報告（T14）",
    "reports": ["knowledge/generated_examples.md", "reports/T14_generation_report.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A4",
    "section": "附錄 A4 CRM 觸發門檻（不計入 15 頁）",
    "title": "八條規則的欄位與門檻；投影片只留欄位名",
    "source": "來源：風險與 Persona（客群輪廓）報告（T10）、L7 運作流程",
    "reports": ["reports/T10_risk_persona_report.md", "L7運作流程_草稿.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A5",
    "section": "附錄 A5 客訴回訪話術（不計入 15 頁）",
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
        ("RAG（檢索增強生成）", "先從知識庫檢索相關條目，再讓模型只依這些內容生成", "76 條（官網 40、手冊 36）；12 則主表＋4 則附錄，每則附引用與查核"),
        ("K-means／silhouette／ARI", "分群法、分群品質指標、兩種分群結果的一致度", "驗證四個 Persona（客群輪廓）：只有靜默出走者被資料獨立支持"),
    ]
    body = [[cell_text(h, WHITE, True) for h in ("名詞", "定義", "本案用法")]]
    for a, b, c in rows:
        body.append([cell_text(a, INK, True), cell_text(b), cell_text(c)])
    col_w = [2.35, 4.85, 5.22]
    font = 12
    heights, total = table_row_heights(body, col_w, font, header_h=0.36, pad=0.08, min_h=0.30)
    avail = BOT - y
    if total < avail:  # 還有餘裕就平均分給每列，表格填滿內容區
        extra = (avail - total) / (len(heights) - 1)
        heights = [heights[0]] + [h + extra for h in heights[1:]]
    add_table(slide, ML, y, CW, min(total, avail), body, col_w, font=font, row_h=heights)


def caption_bar(slide, y, h, code, cap, extra):
    card_text(slide, ML, y, CW, h,
              [[(code, BLUE, True, 16), ("　" + cap, INK, True, 16), (extra, INK, False, 16)]],
              size=16, fill="EAF1F8", anchor="ctr")


def build_a2(slide, y):
    cap_h = 0.56
    gap = 0.08
    chart_h = (BOT - y - 2 * cap_h - 3 * gap) / 2
    f2 = figv()["F2"]
    chart_bars(
        slide, ML, y, CW, chart_h,
        [r["name"] for r in f2], [r["p"] * 100 for r in f2],
        errs=[(r["lo"] * 100, r["hi"] * 100) for r in f2],
        highlight=max(range(len(f2)), key=lambda i: f2[i]["p"]),
        title="Mobile01 論壇發言者流失率 18.2%，高於 Dcard 的 6.8%", ylabel="論壇發言者流失率（%）",
        name="chart:F2", bar_frac=0.5, value_lift=0.05,
    )
    caption_bar(slide, y + chart_h + gap, cap_h, "F2", "論壇發言者流失率。",
                "　Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。母體是論壇發言者，χ²=99.5。")
    f4 = figv()["F4"]
    y2 = y + chart_h + gap + cap_h + gap
    series = [(src, f4["counts"][src]) for src in f4["sources"]]
    blue_set = [BLUE_LIGHT, BLUE_MID, BLUE]
    red_set = [RED_LIGHT, RED_MID, RED]
    colors = [blue_set, blue_set, red_set]
    chart_stacked(
        slide, ML, y2, CW, chart_h, f4["levels"], series, colors,
        title=f"高風險發言者 {f4['n_high']:,} 人，占全部發言者 {100 * f4['n_high'] / f4['n_all']:.1f}%",
        ylabel="發言者數", legend=list(zip(f4["sources"], blue_set)), name="chart:F4", value_lift=0.05,
    )
    caption_bar(slide, y2 + chart_h + gap, cap_h, "F4", "發言者風險分布。",
                "　高風險發言者 1,049 人（16.4%）；約八成在低風險。風險等級：紅＝高。")


def build_a2b(slide, y):
    # F6 原生散點在上；F9 季趨勢 PNG 依本格尺寸重畫（12.42×2.62 吋），貼進來不縮放、填滿整格。
    # v3.4 起 F9 的圖例畫在圖外上方（pipeline/trend_reports.py fig_quarterly），不壓資料。
    cap_h = 0.50
    gap = 0.08
    f6 = figv()["F6"]["bins"]
    chart_h = 2.08
    hi = max(f6, key=lambda b: b["mean"])
    chart_scatter(
        slide, ML, y, CW, chart_h,
        [(b["mean"] * 100, b["rate"] * 100, b["n"]) for b in f6],
        title=f"高分仍偏高：預測接近 {hi['mean'] * 100:.0f}% 時，實際流失是 {hi['rate'] * 100:.0f}%",
        xlabel="桶內平均預測機率（%）", ylabel="實際流失比例（%）", name="chart:F6",
    )
    caption_bar(slide, y + chart_h + gap, cap_h, "F6", "校準曲線。", "　最高信心桶 n=71，實際流失 68%。高分仍偏高，方向對。")
    y2 = y + chart_h + gap + cap_h + gap
    fig_h = BOT - cap_h - gap - y2
    add_card(slide, ML, y2, CW, fig_h, fill=CHART_FILL, name="chart:F9:card")
    fit_pic(slide, "F9.png", ML, y2, CW, fig_h)
    caption_bar(slide, BOT - cap_h, cap_h, "F9", "季趨勢預警。", "　討論量達前 4 週平均 3 倍且至少 5 句就亮燈。")


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


def message_cards(slide, y, msgs, touch_label):
    """A3／A5 共用：兩張話術卡，全文 24pt，標題與引用 18pt，查核 15pt。"""
    card_h = (BOT - y - 0.12) / 2
    for i, msg in enumerate(msgs):
        yy = y + i * (card_h + 0.12)
        text = re.sub(r"([，。、；：！？）】」])\s+", r"\1", msg["text"])  # 全形標點後的空格不進簡報，行首才不會多一格
        card_text(
            slide, ML, yy, CW, card_h,
            [
                [(f"{msg['persona']} × {touch_label}　{msg['channel']}", BLUE, True, 18)],
                [(f"引用條目　{msg['cites']}", NAVY, True, 18)],
                [(text, INK, False, 24)],
                [(f"查核結果　{msg['check']}", MUTED, False, 15)],
            ],
            size=18, pad_y=0.10, anchor="ctr",
        )


def build_a3(slide, y):
    message_cards(slide, y, load_a3_messages(), "待料通知")


def build_a4(slide, y):
    header = [cell_text(h, WHITE, True) for h in ("規則", "欄位", "門檻")]
    rows = [header]
    for code, signal in SIGNALS:
        rows.append([
            [[(code, BLUE, True), ("　" + signal, INK, True)]],
            cell_text(CRM_FIELDS[code]),
            cell_text(CRM_THRESHOLD[code]),
        ])
    table_h = BOT - y
    row_h = [0.44] + [(table_h - 0.44) / 8] * 8
    add_table(slide, ML, y, CW, table_h, rows, [2.3, 5.3, 4.82], font=16, row_h=row_h)


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
    message_cards(slide, y, load_a5_messages(), "客訴結案後 7 天回訪")


BUILDERS = [build_toc, build_p1, build_p2, build_p3, build_p4, build_p5, build_p6, build_p7, build_p8, build_p9, build_p10, build_p11, build_p12, build_p13, build_p14, build_p15, build_a1, build_a2, build_a2b, build_a3, build_a4, build_a5]


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
            pid = "摘要" if i == 1 else SLIDES[i - 2]["id"]
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
        f"- 投影片共 {1 + len(SLIDES)} 張，沒有封面：提案摘要 1（第 1 頁，不計入）、大綱 1（第 2 頁，計入 15 頁）、內容 "
        f"{sum(1 for m in SLIDES if m['id'].startswith('P'))}（第 3–16 頁，P1–P14）、附錄 "
        f"{sum(1 for m in SLIDES if m['id'].startswith('A'))}（第 17–23 頁：A0 補充資料、A1 術語表、A2 與 A2b 補充圖表、A3 待料通知、A4 CRM 觸發門檻、A5 客訴回訪）。",
        "- 計入 15 頁上限的是大綱 1 張加內容頁 14 張，合計 15。提案摘要與附錄 7 張不計入。",
        "- 依據：主辦方信寫「提案摘要須置於簡報第一頁，並於同一頁內完整呈現」「請繳交 15 頁內的提案簡報，提案摘要及附錄不計入頁數」。官方模板第 1 張是「2026和泰AI黑客松」規則說明頁，沒有團隊名與作品名，不是封面；建置時刪掉它，提案摘要成為第 1 頁。團隊名與作品名在摘要表第 1、2 列。",
        "- 待料通知與客訴回訪話術分兩頁：A3 兩則待料、A5 兩則客訴。四則全文塞不進同一頁。",
        "- 備案：若主辦方仍判定超過 15 頁，下一步是第 4 頁痛點併入第 5 頁，或第 13 頁差異化併入第 12 頁，內容頁減為 13。",
        "",
        "## 頁次對照",
        "",
        "| 檔案頁 | 代碼 | 章節 | 標題 | 圖 | 報告 |",
        "| --- | --- | --- | --- | --- | --- |",
        "| 1 | 摘要 | 提案摘要（不計入 15 頁） | 提案摘要（表格右欄；團隊名與作品名在第 1、2 列） | — | 會議記錄 §四；模型現況見 T8、T9 |",
    ]
    for i, meta in enumerate(SLIDES):
        figs = "、".join(Path(p).name for p in meta["figures"]) or "—"
        reports = "、".join(f"`{r}`" for r in meta["reports"])
        title = meta["title"]
        lines.append(
            f"| {i + 2} | {meta['id']} | {meta['section']} | {title} | {figs} | {reports} |"
        )
    lines += [
        "",
        "圖欄是該頁對應的報告圖。自 v3.3 起 F1–F7 與 F9_pipeline 在簡報裡用 pptx 原生形狀重畫，數字讀 `reports/figures/figure_values.json`（`python pipeline/make_figures.py --values-only` 產生，與 PNG 畫的值相同）；F8 在第 8 頁與附錄 A0 都用原生形狀（`draw_f8`）；只有 F9 季趨勢仍貼 `reports/figures/F9.png`。PNG 原檔留在 `reports/figures/` 供報告用。",
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
        "- P1 三站比率轉抄 `reports/T7_stats_tests.md` 作者層級表，簡報寫成論壇發言者流失率：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。P2 已刪這張表，改放三個流失前兆。",
        "- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。",
        "- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。",
        "- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值 P 0.617、R 0.769、κ 0.642 在該頁備註。校準曲線在附錄 A2b。F1 0.685 沒有放進 25–35 字備註。",
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
        "需要 Python 3.12 與 python-pptx。`--note` 必填。腳本開官方模板，刪掉第 1 張規則說明頁與七張章節分隔頁，只留提案摘要頁並保留其左欄，再依 `SLIDES` 與各頁 builder 重畫。改文案請改本檔前半的 dict，不要改投影片後再存，否則重跑會蓋掉。同版號已存在時加上 `--force` 才會覆寫。",
        "",
        "本機若裝了 PowerPoint，腳本會用 pywin32 把每頁匯出成 PNG，並把整份匯出成 PDF，放在 `deck/preview/` 的版號檔與 `vX.Y/` 資料夾。",
        "",
        "建置後檢查重疊與空白：",
        "",
        "```text",
        "python deck/check_layout.py deck/初賽簡報_vX.Y.pptx",
        "```",
        "",
        "腳本列出非包含關係的形狀重疊、超出頁面或壓到頁尾來源列的形狀，以及每張預覽圖的 PIL 空白比例。文字放在卡片上、標籤放在方塊內這種包含關係不算重疊。",
        "另列卡片內留白：文字實際高度（依字級與換行估算）除以底下卡片高度，低於 0.7 的會印出來；全冊每張文字卡都要達 0.7。名稱以 `chart` 開頭的形狀是原生圖表的圖區與長條，不是文字卡，不列入這項檢查。",
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
    if len(NOTES) != 1 + len(SLIDES) or len(BUILDERS) != len(SLIDES):
        raise SystemExit(
            f"NOTES / SLIDES / BUILDERS 數量不一致：{len(NOTES)} / {len(SLIDES)} / {len(BUILDERS)}"
        )
    for i, note in enumerate(NOTES, 1):
        n = zi(note)
        if not 25 <= n <= 35:
            raise SystemExit(f"第 {i} 頁旁白 {n} 字（要 25–35）：{note}")


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
    # 模板第 1 張是「2026和泰AI黑客松」規則說明頁，不是封面，最後會刪掉，讓提案摘要成為第 1 頁。
    # 先留著再加內容頁：python-pptx 用「現有張數＋1」命名新投影片的 part，若先刪說明頁，
    # 新的大綱頁會拿到 slide2.xml 而與摘要頁撞名，存檔就壞。
    fill_summary(prs.slides[1])
    set_notes(prs.slides[1], NOTES[0])
    for i, (meta, builder) in enumerate(zip(SLIDES, BUILDERS)):
        page = i + 2
        slide, y = new_content_slide(prs, meta, page)
        builder(slide, y)
        set_notes(slide, NOTES[page - 1])
    delete_slide(prs, 0)
    expected = 1 + len(SLIDES)
    if expected != 23:
        raise SystemExit(f"總張數應為 23（摘要 1＋大綱 1＋內容 14＋附錄 7），SLIDES 給出 {expected}")
    if len(prs.slides) != expected:
        raise SystemExit(f"頁數應為 {expected}，實際 {len(prs.slides)}")
    content = sum(1 for m in SLIDES if m["id"].startswith("P"))
    appendix = sum(1 for m in SLIDES if m["id"].startswith("A"))
    if content != 14 or appendix != 7:
        raise SystemExit(f"內容頁應為 14、附錄應為 7，實際內容 {content}、附錄 {appendix}")
    for i, slide in enumerate(prs.slides, 1):
        note = slide.notes_slide.notes_text_frame.text.strip()
        if not note:
            raise SystemExit(f"第 {i} 頁沒有備註")
    out = deck_pptx(version)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    check = Presentation(str(out))
    if len(check.slides) != expected:
        raise SystemExit(f"重開後頁數不是 {expected}")
    table = next(shape.table for shape in check.slides[0].shapes if shape.has_table)
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
