# -*- coding: utf-8 -*-
"""初賽簡報。文案與數字集中在本檔前半；不要在這裡重算統計。

版號見 DECK_VERSION。每次改動要升號：小改 +0.1，PO 審過的里程碑升整數。
可用 --version X.Y 覆蓋；--note 必填，寫進 deck/CHANGELOG.md。

重跑：python deck/build_deck.py --version X.Y --note "一句變更說明"
模板：attachments/2026和泰AI黑客松＿初賽簡報模板.pptx
輸出：deck/初賽簡報_vX.Y.pptx、deck/初賽簡報_latest.pptx、deck/README.md；
若本機有 PowerPoint，另匯 deck/preview/初賽簡報_vX.Y.pdf 與 deck/preview/vX.Y/。
內容是 v4.2（摘要、大綱、P1–P14、附錄 A0、A2、A2b、A3、A4、A5、A6、A1）。投影片 24 張，沒有封面。
v4.2：新增附錄 A6「部署架構與 MLOps 閉環」（第 23 頁，對照 iPAS 指引 5.2；A1 術語表移到第 24 頁）：左卡部署位置、
服務封裝、權限、版本管理；右上四方塊閉環＋日／週／月／季監控表（只有 F1 0.8、κ 0.6 是定案門檻）；底部四部門分工。
第 16 頁甘特圖第 5 列與護城河模型行改引附錄 A6；第 15 頁組織列對策加「跨部門小組月審」。全冊刪掉「顯卡容量」字樣，
改寫成內網 GPU 伺服器（建議規格只寫在 A6）；開發期實測（RTX 4060 Ti、5 小時）留在 reports/ 與問答稿。
v4.0：B 的 #20／#8 修正，頁碼不變。第 22 頁（A5）卡片下加一行小註「【】為專員填寫欄位，刻意保留」；
第 13 頁三張大數字卡換標籤（74%＝高風險確有流失句、0 元＝API 費、R1–R8＝每項可回溯原句，ARI 0.08 只留在表格），
四張卡各補一行與標籤一致的說明；第 11 頁標題拿掉「一致率 98.4%」、98.4% 卡註明是兩段標註一致率不是準確率、
底部摘要條改成一句結論；第 10 頁中段改成一句分級結論；第 4 頁「過保 62 句、保固內 17 句」改成兩行不再孤行。
v3.9：只改第 3 頁（提案概述）。原本八張「編號＋頁碼」小卡太像第 2 頁的目錄，改成由左到右的流程
（公開論壇輿情 → 產出 1 → 產出 2 → 車主回廠）加兩個勾選面板（產出 1 藍、產出 2 紅，各列官方題目四個子項與一個現有數字），
上方數據帶縮成一條並補一句主張，底部一句粗體收尾；頁上不再出現「第 N 頁」，只留「各章節頁碼見第 2 頁」。其餘頁不動。
v3.8：只改第 9 頁標題「四種流失車主」→「四種流失論壇發言者」（母體是論壇發言者，與第 10 頁一致）；其餘不動。
v3.7：摘要頁預期效益欄四處修字（+10 個百分點、≥、零成本推論）與 AI 技術欄補回兩段式標註；第 2–23 頁底部「來源：」列
全部移除（SLIDES 不再有 source 欄，chrome() 不畫來源），內容區下緣 BOT 由 7.02 延伸到 7.36，頁碼移到右側邊界內
（x 12.92–13.30）不與內容區重疊；第 10 頁標題「高風險車主」改「高風險論壇發言者」。報告對照仍在 README 頁次表。
v3.6：併入使用者手改（摘要三格逐字照抄、第 4 頁標題、第 5 頁說明條與來源列、附錄 A1 移到最後、A3／A4 標題）
與手寫修改清單：大綱改純目錄；第 3 頁兩張大卡各四個編號小塊；第 4 頁被動應對／主動掌握並排；第 5 頁零件紅、價格黃；
第 7 頁去識別框併進流程方塊；第 8 頁 L3／L6／L7 黃標；第 9 頁 48、43 兩格紅；第 10 頁改風險等級對照表；
第 11／13／15 頁放大重點；第 12 頁五步驟只留標題；第 14 頁每渠道一則範本；第 16 頁 24 週甘特圖；
附錄 A0 改五個 Dashboard 示意。頁碼不增減；附錄順序 17＝A0、18＝A2、19＝A2b、20＝A3、21＝A4、22＝A5、23＝A1。
v3.5：拿掉自製封面，提案摘要成為第 1 頁（主辦方信：「提案摘要須置於簡報第一頁，並於同一頁內完整呈現」；
模板第 1 張是規則說明頁，不是封面，建置時刪除）。全冊頁碼與「第 N 頁」引用前移 1；內容、數字、版面不變。
v3.4：F9 圖例移到圖外上方、F6 的 n 標籤避開對角線且圖區加高；全冊文字套用中日韓換行禁則
（eaLnBrk／hangingPunct、lang=zh-TW），標點不再落行首；人物卡加高；數值標籤上移；流程卡標題齊頂。
v3.3 全頁版面重做：內容頁與附錄的卡片、字級、標籤位置統一；F1–F7 與資料處理鏈改用 pptx 原生形狀畫，
數字讀 reports/figures/figure_values.json（pipeline/make_figures.py --values-only）；F8 在第 8 頁與附錄 A0
都用原生形狀（draw_f8）；只有 F9 季趨勢仍貼 PNG。摘要頁左欄是模板，不動。
頁數算法：提案摘要第 1 頁不計入；計入 15 頁的是大綱 1 張（第 2 頁）加內容頁 14 張（第 3–16 頁）；
附錄 8 張（第 17–24 頁，含 A0、A6；v4.1 以前是 7 張、第 17–23 頁）不計入。依據是主辦方信「15 頁內，提案摘要及附錄不計入頁數」。
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
DECK_VERSION = "4.0"
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
YELLOW = RGBColor(0xF2, 0xB6, 0x00)  # 第 5 頁價格、第 8 頁 L3／L6／L7 標籤；黃底配深色字

ML = 0.46
CW = 12.42
# 頁碼：右下角，框在內容區右緣 12.88 之外的邊界內（12.92–13.30），與內容區不重疊。v3.7 起沒有來源列。
FOOTER_Y = 7.16
PAGE_X = 12.92
PAGE_W = 0.38


def zi(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


# ---------------------------------------------------------------------------
# 文案。數字只轉抄報告，不在這裡計算。
# 態度負面 61%：任務大綱如此寫。專案架構 §0.1 寫 68%，T7 只給流失率 4.7%。
# v0 依大綱放 61%，README 列為待核，不另算。
# ---------------------------------------------------------------------------

NOTES = [
    "摘要給評審三層目標：回廠率假設加十點，核准八成，模型每季重驗。",
    "大綱只列六個章節與附錄的頁碼；兩大產出的對照放在第三頁。",
    "由輿情到回廠：產出一看見誰有風險，產出二經人工核准後關懷。",
    "三個前兆並行，不是依序發生：過保、刪項、間隔拉長。",
    "零件勝算比二點五八、價格二點六四，分母兩萬一千句。",
    "出口在一般外廠；定保口述中位原廠九千、外廠三千五，不是公告價。",
    "去識別遮蔽五百一十七次、抽查五十句漏網零；超過七十八字只標記不刪。",
    "八層對到雙迴路：上面是產出一，下面是產出二，審核後才投遞。",
    "分群只獨立支持靜默出走者；其餘 Persona（客群輪廓）用規則定義。",
    "高風險七成四真有流失句；風險分是模型機率六成加命中規則四成。",
    "人工兩人 κ 0.40，不一致處要經仲裁後才成為金標。",
    "r4 原值 P 0.617、R 0.769、κ 0.642。",
    "別人看不到不抱怨就走的人；我們給規則和機率，每句都能回原句。",
    "四種人配三種進廠時機，十二則已過查核，投遞前仍要人工審。",
    "人工篩選工時省九成以上（估），五項風險都已有對策。",
    "每季三百句金標、兩人共五小時，審核回饋持續再訓練。",
    "五個看板示意：洞察三個，知識庫與審核佇列各一；非實際介面。",
    "附錄前兩張圖：三站發言者流失率，以及高中低風險分布。",
    "附錄後兩張圖：校準曲線五個信心桶，以及季趨勢預警。",
    "附錄待料通知兩則：進度不承諾到貨日，代步車只照知識庫條件。",
    "CRM 八條規則的門檻列在本頁，投影片只留欄位名稱。",
    "客訴結案七天回訪兩則：電話先道歉，LINE 不要求刪評。",
    "內網地端部署，四級監控設門檻，不達標就重訓；四個部門分工，每月共審。",
    "附錄術語表：每個名詞一句定義、一句本案用法，評審追問時翻這頁。",
]

SUMMARY_RIGHT = {
    "team": [[("回廠率研究所", INK, True)]],
    "product": [[("Lexus車主流失預警與 AI 溝通系統", INK, True)]],
    "challenge": [[("AI 流失風險洞察與智慧溝通：打造Lexus車主忠誠度的終極防線", INK, False)]],
    "audience": [[("Lexus 售後服務部門決策者與服務廠客戶關係人員", INK, False)]],
    # v3.6：三格逐字照使用者 2026-10-04 手改版（USER_EDITED_v3.5_backup.pptx），含其標點與空格，不潤飾。
    "design": [
        [("1. 從公開輿情找出 4 種流失 Persona（客群輪廓）。", INK, False)],
        [("2. 本機自訓 決策模型即時給出流失機率與可解釋規則。", INK, False)],
        [("3. Persona（客群輪廓） × 接觸點的 RAG 關懷內容生成。", INK, False)],
    ],
    # 手改版這格是一段、中間一個換行（a:br）；粗體段也照抄。
    # v4.4：依使用者指示移除兩段式標註句（第 11 頁與附錄 A1 的兩段式標註不動）。
    "ai": [[
        ("核心模型：Claude / GPT /  Qwen3-4B QLoRA ", INK, False),
        ("自訓決策模型（LLM2Jev 架構，支援本地部署）", INK, True),
        ("\v", INK, False),
        ("技術與統計：RAG 官方保修知識庫、K-means 分群、χ² 檢定、勝算比與 Wilson CI 驗證", INK, False),
    ]],
    # v3.7：使用者決定「改」的四點：+10 個百分點（假設值，基期實測校正）、三處「大於等於」改 ≥（k→κ）、
    # 「零本推論」改「零成本推論」。其餘字（含手改的標點與空格）不動。
    "benefit": [
        [("回廠成長 : 高風險車主回廠率 +10 個百分點（假設值，基期實測校正）", INK, False, 12)],
        [("工時提效 :名單篩選工時 -90%、話術核准率 ≥ 80%", INK, False, 12)],
        [("模型嚴謹: 隨機層F1 ≥ 0.8、κ ≥ 0.6（季驗 300 句）", INK, False, 12)],
        [("零成本推論: 每句 0.7 秒 高速回應，達成 地端 0 API 費。", INK, False, 12)],
    ],
}

# 每頁：章節標、結論標題、對應報告（只寫進 README 頁次表；v3.7 起頁腳沒有來源列）、圖檔
SLIDES = [
    {
        "id": "TOC",
        "section": "大綱（計入 15 頁）",
        "title": "六個章節與附錄，對照頁碼",
        "reports": ["raw/bh-challenge.txt"],
        "figures": [],
    },
    {
        "id": "P1",
        "section": "1 提案概述",
        "title": "提案是兩份產出：輿情洞察，以及對準客群的溝通",
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
        "title": "輿情能提前預警，降低客戶流失率",
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
        "reports": ["reports/T7_stats_tests.md"],
        "figures": ["reports/figures/F1.png"],
    },
    {
        "id": "P4",
        "section": "2 目標對象與痛點分析",
        "title": "出口是一般外廠；過保後價差把人推走",
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
        "reports": ["L7運作流程_2026-09-30.md", "專案架構_2026-09-23.md"],
        "figures": ["reports/figures/F8.png"],
    },
    {
        "id": "P7",
        "section": "3 解決方案設計",
        "title": "四種流失論壇發言者，過保精算派最多（511 人）",  # v3.8：母體是論壇發言者，與第 10 頁一致
        "reports": ["reports/T10_risk_persona_report.md", "會議記錄_2026-09-30.md"],
        "figures": ["reports/figures/F5.png"],
    },
    {
        "id": "P8",
        "section": "3 解決方案設計",
        "title": "高風險論壇發言者 74% 確有流失句，分級可信",  # v3.7：母體是論壇發言者，不是車主
        "reports": ["reports/T10_risk_persona_report.md"],
        "figures": [],
    },
    {
        "id": "P9",
        "section": "4 AI 應用方法",
        "title": "兩段式標註：先寬抓、再複核",  # v4.0：98.4% 是兩段標註一致率，不是準確率，不放標題
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
        "reports": ["reports/T8_r4_report.md", "專案架構_2026-09-23.md"],
        "figures": [],
    },
    {
        "id": "P11",
        "section": "5 獨特優勢與差異化",
        "title": "看得見沒抱怨就走的人，分數說得出原因",
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
        "section": "附錄 A0 Dashboard 示意（不計入 15 頁）",
        "title": "五個看板：洞察三個、知識庫與審核佇列各一個",
        "reports": [
            "L7運作流程_2026-09-30.md",
            "reports/T10_risk_persona_report.md",
            "reports/T15_trend_reports.md",
            "knowledge/lexus_aftersales_kb.md",
        ],
        "figures": [],
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
    ("內網就能跑", "CRM 資料不能出門。內網 GPU 伺服器可訓可推，零 API 費。"),
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
            if text == "\v":  # 段內換行（a:br），摘要頁 AI 技術欄用
                p._p.add_br()
                continue
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


def chrome(slide, section: str, page: int) -> None:
    """頁首章節標與右下角頁碼。v3.7 起沒有來源列；頁碼框放在內容區右緣（ML+CW）之外的右側邊界內，
    內容區才能往下延伸到 BOT 而不壓到頁碼。"""
    add_text(
        slide, ML, 0.10, 9.2, 0.26,
        [[(section, NAVY, False)]],
        size=12, margin=0.0,
    )
    add_text(
        slide, PAGE_X, FOOTER_Y, PAGE_W, 0.24,
        [[(str(page), NAVY, False)]],
        size=12, align=PP_ALIGN.RIGHT, margin=0.0, name="page-number",
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


# 內容區：標題下緣 1.08 吋到 7.36 吋。v3.6 以前到 7.02（來源列上方）；v3.7 拿掉來源列後下延 0.34 吋，
# 頁碼在內容區右緣之外，所以內容區下緣不必避開它。
BOT = 7.36


def new_content_slide(prs, meta: dict, page: int):
    slide = prs.slides.add_slide(blank_layout(prs))
    strip_placeholders(slide)
    chrome(slide, meta["section"], page)
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
               name="chart", card=True, bar_frac=0.62, pad=0.14, value_lift=0.0, value_fill=None,
               colors=None):
    """長條圖：方塊、數值標籤、類別標籤、刻度與縱軸標籤都是 pptx 物件。
    errs：每根的 (lo, hi) 絕對值，畫成誤差線。highlight：要標紅的索引。colors：每根自訂色，給了就蓋過 highlight。
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
        if colors is not None:
            c = colors[i]
        else:
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


def chart_heatmap(slide, x, y, w, h, rows, cols, matrix, *, title=None, legend=None, name="chart", pad=0.14,
                  red_at=None):
    """熱圖：每格一個矩形加數字；最大格套紅框。rows 直排、cols 橫排。
    red_at：給了門檻就把達門檻的格子塗成紅色（白字），其餘仍是藍階，不再另畫紅框。"""
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
            hot = red_at is not None and v >= red_at
            add_rect(slide, cx, cy, cw, ch, fill=RED if hot else blues(v / vmax), name=f"{name}:cell")
            color = WHITE if (hot or v > vmax * 0.62) else INK
            add_text(slide, cx, cy, cw, ch, [[(f"{v:.0f}", color, hot, 16)]], size=16,
                     align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name=f"{name}:cellv")
    if red_at is None:
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
    """純目錄：六個章節與附錄，只有標題與頁碼。左側一條時間軸串起編號，字級放大把版面填滿。"""
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
        key, name = g["section"].split(" ", 1)
        rows.append((key, name, f"第 {page_span(g['ids'])} 頁"))
    rows.append(("附", "附錄（不計入 15 頁）", f"第 {page_span(appendix)} 頁"))
    n = len(rows)
    row_h = 0.78  # v3.7：內容區下延後列高 0.74 → 0.78，列距才不會拉到 0.18
    gap = (BOT - y - n * row_h) / (n - 1)
    pill = 0.56
    axis_x = ML + 0.16 + pill / 2
    add_line(slide, axis_x, y + row_h / 2, axis_x, y + (n - 1) * (row_h + gap) + row_h / 2,
             color=BLUE_LIGHT, width=2.0, name="toc-axis")
    for i, (key, name, pages) in enumerate(rows):
        yy = y + i * (row_h + gap)
        add_card(slide, ML, yy, CW, row_h)
        add_pill(slide, ML + 0.16, yy + (row_h - pill) / 2, pill, pill, key, size=20,
                 fill=NAVY if key == "附" else BLUE)
        add_text(slide, ML + 0.16 + pill + 0.30, yy + 0.04, 7.6, row_h - 0.08,
                 [[(name, INK, True, 32)]], size=32, anchor="ctr")
        add_text(slide, ML + CW - 0.20 - 3.6, yy + 0.04, 3.6, row_h - 0.08,
                 [[(pages, BLUE, True, 32)]], size=32, align=PP_ALIGN.RIGHT, anchor="ctr")


def build_p1(slide, y):
    """v3.9：第 3 頁改成「由左到右的流程＋勾選面板」，不再是帶頁碼的格子清單（第 2 頁才是目錄）。
    上：一條「為什麼要做」數據帶（三站流失率、χ²）加一句主張（與第 4 頁一致）。
    中：公開論壇輿情 → 產出 1（藍）→ 產出 2（紅）→ 車主回廠，用實心箭頭串接；
        兩個產出是大面板，面板內用勾選清單列官方題目的四個子項，每項接一個現有數字或交付物。
    下：一句粗體收尾（內容取自第 8 頁），右側一行小字「各章節頁碼見第 2 頁」。本頁沒有「第 N 頁」。"""
    # ---- 上：數據帶，一條 ----
    band_h = 0.86
    add_card(slide, ML, y, CW, band_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.14, y + 0.06, 1.70, band_h - 0.12,
        [[("為什麼要做", BLUE, True, 18)], [("論壇發言者流失率", INK, True, 13)], [("χ²=99.5", NAVY, False, 13)]],
        size=13, anchor="ctr",
    )
    stats = [("18.2%", "Mobile01"), ("14.1%", "PTT"), ("6.8%", "Dcard")]
    runs = []
    for i, (num, site) in enumerate(stats):
        if i:
            runs.append(("　", INK, False, 14))
        runs.append((num, BLUE, True, 24))
        runs.append((" " + site, INK, True, 14))
    add_text(slide, ML + 1.90, y + 0.06, 5.10, band_h - 0.12, [runs], size=14, anchor="ctr")
    add_text(
        slide, ML + 7.10, y + 0.06, CW - 7.10 - 0.14, band_h - 0.12,
        [[("公開輿情能在車主離開原廠之前先辨識", NAVY, True, 18)]],
        size=18, align=PP_ALIGN.RIGHT, anchor="ctr",
    )

    # ---- 下：一句收尾（粗體）＋頁碼提示 ----
    bar_h = 0.56
    bar_y = BOT - bar_h
    add_card(slide, ML, bar_y, CW, bar_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.14, bar_y + 0.04, CW - 0.28 - 2.60, bar_h - 0.08,
        [[("兩份產出，一個閉環：每日洞察 → 人工核准的關懷 → 結果回寫 CRM", INK, True, 18)]],
        size=18, anchor="ctr",
    )
    add_text(
        slide, ML + CW - 0.14 - 2.50, bar_y + 0.04, 2.50, bar_h - 0.08,
        [[("各章節頁碼見第 2 頁", MUTED, False, 12)]],
        size=12, align=PP_ALIGN.RIGHT, anchor="ctr",
    )

    # ---- 中：流程列 ----
    row_y = y + band_h + 0.14
    row_h = bar_y - 0.14 - row_y
    node_w = 1.62
    arrow_w, arrow_h, arrow_pad = 0.30, 0.44, 0.06
    slot = arrow_w + 2 * arrow_pad
    panel_w = (CW - 2 * node_w - 3 * slot) / 2
    node_h = 1.70
    node_y = row_y + (row_h - node_h) / 2
    mid_y = row_y + row_h / 2

    def arrow(x, color=BLUE):
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RIGHT_ARROW, Inches(x + arrow_pad), Inches(mid_y - arrow_h / 2), Inches(arrow_w), Inches(arrow_h)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    # 光帶：三段淡色底，從左緣穿過兩個箭頭槽到右緣，面板壓在上面；起點與終點節點坐在帶上。
    # 左右兩段把節點整個包住（check_layout 視為外框，不算卡片留白），中段只含箭頭。
    p1x = ML + node_w + slot
    p2x = p1x + panel_w + slot
    track_y, track_h = node_y - 0.30, node_h + 0.60
    for tx, tw in ((ML, node_w + slot), (p1x + panel_w, slot), (p2x + panel_w, slot + node_w)):
        add_card(slide, tx, track_y, tw, track_h, fill="F4F7FB", radius=0.04)

    # 起點：公開論壇輿情
    x = ML
    add_card(slide, x, node_y, node_w, node_h, fill="EAF1F8", line=NAVY)
    add_text(
        slide, x + 0.08, node_y + 0.06, node_w - 0.16, node_h - 0.12,
        [[("公開論壇輿情", INK, True, 15)], [("Mobile01", INK, False, 14)], [("PTT", INK, False, 14)],
         [("Dcard", INK, False, 14)], [("每日抓新留言", MUTED, False, 13)]],
        size=14, align=PP_ALIGN.CENTER, anchor="ctr",
    )
    x += node_w
    arrow(x)
    x += slot

    panels = [
        ("產出 1", "AI 網路輿情洞察系統", "看見誰有風險", BLUE, "EAF1F8", BLUE_LIGHT, [
            ("客群 Persona（客群輪廓）", "四種客群，過保精算派 511 人"),
            ("高風險議題分析", "零件等料 17.3%、價格 15.0%"),
            ("整體市場輿情洞察", "21,183 句售後語料，日週季報"),
            ("使用的 AI 技術／模型", "Qwen3-4B 本機模型，F1 0.685"),
        ]),
        ("產出 2", "AI 溝通計畫", "對的人、對的時機、說對的話，人工核准", F8_HUMAN_EDGE, "FBF3F2", RGBColor(0xE3, 0xA9, 0xA3), [
            ("核心溝通策略", "四種客群配三種進廠時機"),
            ("AI 生成內容範例", "12 則話術對 76 條條款查核"),
            ("精準接觸點規劃", "三個接觸點＋客訴第 7 天回訪"),
            ("AI 方案運作流程圖", "雙迴路，人工核准才投遞"),
        ]),
    ]
    head_h = 1.02
    tick = 0.30
    for head, title, sub, color, fill, edge, items in panels:
        add_card(slide, x, row_y, panel_w, row_h, fill=fill, line=edge)
        add_text(
            slide, x + 0.14, row_y + 0.08, panel_w - 0.28, head_h,
            [[(head, color, True, 24)], [(title, INK, True, 18)], [(sub, MUTED, False, 14)]],
            size=14, anchor="t",
        )
        list_top = row_y + head_h + 0.16
        list_h = row_h - head_h - 0.16 - 0.10
        pitch = list_h / len(items)
        for n, (name, deliver) in enumerate(items):
            ry = list_top + n * pitch
            if n:
                add_line(slide, x + 0.14, ry - 0.02, x + panel_w - 0.14, ry - 0.02, color=edge, width=0.75, name="chart-sep")
            circle = slide.shapes.add_shape(
                MSO_SHAPE.OVAL, Inches(x + 0.16), Inches(ry + (pitch - tick) / 2), Inches(tick), Inches(tick)
            )
            circle.fill.solid()
            circle.fill.fore_color.rgb = color
            circle.line.fill.background()
            tf = circle.text_frame
            for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
                setattr(tf, side, Inches(0.0))
            set_tf(tf, [[("✓", WHITE, True, 14)]], 14, align=PP_ALIGN.CENTER, anchor="ctr")
            add_text(
                slide, x + 0.16 + tick + 0.10, ry + 0.03, panel_w - 0.16 - tick - 0.10 - 0.14, pitch - 0.06,
                [[(name, INK, True, 18)], [(deliver, INK, False, 16)]],
                size=16, anchor="ctr",
            )
        x += panel_w
        arrow(x, color=color)
        x += slot

    # 終點：車主回廠
    add_card(slide, x, node_y, node_w, node_h, fill="EAF1F8", line=NAVY)
    add_text(
        slide, x + 0.08, node_y + 0.06, node_w - 0.16, node_h - 0.12,
        [[("車主回廠", INK, True, 15)], [("點擊・預約", INK, False, 13)], [("回廠", INK, False, 13)], [("寫回 CRM", INK, False, 14)],
         [("KPI 回饋", MUTED, False, 13)], [("回頭校正門檻", MUTED, False, 13)]],
        size=14, align=PP_ALIGN.CENTER, anchor="ctr",
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
    # 上半：被動應對（現況）與主動掌握（導入後）左右等寬對比；下半：三個前兆並排匯流（已核准的邏輯，不動）。
    upper = 2.06  # v3.7：內容區下延 0.34，上半 +0.10、前兆方塊 +0.24 並把字級放大到 26／24／20，留白都維持 ≥ 0.7
    gap = 0.14
    card_w = (CW - gap) / 2
    cols = [
        ("現況", "被動應對", NAVY, "F4F7FB", [
            [("只靠客訴與回廠紀錄，人流失之後才知道。", INK, False, 20)],
            [("1,671 句裡 186 句沒抱怨就找出口。", INK, False, 20)],
            [("使用者是售後決策者與服務廠客戶關係人員。", MUTED, False, 18)],
        ]),
        ("導入後", "主動掌握", BLUE, "EAF1F8", [
            [("三個訊號並行。到期前 90 天進名單，第 60 天再開口。", INK, False, 20)],
            [("公開輿情加上 CRM，在離開原廠之前先辨識。", INK, False, 20)],
        ]),
    ]
    for i, (tag, head, color, fill, body) in enumerate(cols):
        x = ML + i * (card_w + gap)
        add_card(slide, x, y, card_w, upper, fill=fill)
        add_text(slide, x + 0.14, y + 0.10, card_w - 0.28, upper - 0.20,
                 [[(head, color, True, 24)]] + body, size=20, anchor="ctr")
        add_pill(slide, x + card_w - 0.14 - 1.10, y + 0.14, 1.10, 0.36, tag, size=14, fill=color)
    flow_y = y + upper + 0.12
    flow_h = BOT - flow_y
    add_card(slide, ML, flow_y, CW, flow_h, fill="EAF1F8")
    add_text(
        slide, ML + 0.14, flow_y + 0.06, CW - 0.28, 0.30,
        [[("三個前兆並排，匯流後才是離開；資料沒有先後順序", NAVY, True, 14)]],
        size=14, margin=0.0, anchor="ctr",
    )
    # v4.0：第一格藍字 24pt 在 3.97 吋寬會把「句」折成孤行，改在頓號處硬換行（\v → a:br），兩行各自完整。
    precursors = [
        ("過保", "過保 62 句\v保固內 17 句", "觸發：到期前 90 天"),
        ("刪項", "連續 2 次拒項", "拒絕估價項目就列管"),
        ("間隔拉長", "逾期超過建議週期", "1.5 倍"),
    ]
    inner_x, inner_w = ML + 0.14, CW - 0.28
    gap_x = 0.12
    bw = (inner_w - 2 * gap_x) / 3
    by = flow_y + 0.42
    arrow_h = 0.24
    merge_h = 0.66
    out_h = 0.66
    bh = BOT - 0.14 - out_h - arrow_h - merge_h - arrow_h - by
    for i, (head, line, sub) in enumerate(precursors):
        xx = inner_x + i * (bw + gap_x)
        line_runs = []
        for j, part in enumerate(line.split("\v")):
            if j:
                line_runs.append(("\v", BLUE, True))
            line_runs.append((part, BLUE, True, 24))
        flow_box(slide, xx, by, bw, bh,
                 [[(head, INK, True, 26)], line_runs, [(sub, NAVY, False, 20)]], size=20)
        down_arrow(slide, xx + bw / 2, by + bh + 0.02, h=arrow_h - 0.04)
    merge_y = by + bh + arrow_h
    flow_box(slide, inner_x, merge_y, inner_w, merge_h,
             [[("離開原廠", INK, True, 20), ("　　人走了才知道", NAVY, False, 16)]], size=16)
    down_arrow(slide, ML + CW / 2, merge_y + merge_h + 0.02, h=arrow_h - 0.04)
    out_y = merge_y + merge_h + arrow_h
    flow_box(slide, inner_x, out_y, inner_w, out_h,
             [[("一般外廠　736 句", BLUE, True, 22), ("　　可複選", NAVY, False, 16)]], size=16)


def stat_chips(slide, y, items, num_size=26, label_size=15, h=0.98):
    """一列四格數字卡：數字藍粗、說明一行。回傳下一個 y。
    每項可多給 (底色, 數字色, 說明色)，第 5 頁用來把零件磚塗紅、價格磚塗黃。"""
    gap = 0.10
    n = len(items)
    chip_w = (CW - (n - 1) * gap) / n
    for i, item in enumerate(items):
        num, label = item[0], item[1]
        fill = item[2] if len(item) > 2 else "F4F7FB"
        num_color = item[3] if len(item) > 3 else BLUE
        label_color = item[4] if len(item) > 4 else INK
        x = ML + i * (chip_w + gap)
        card_text(slide, x, y, chip_w, h,
                  [[(num, num_color, True, num_size)], [(label, label_color, False, label_size)]],
                  size=label_size, align=PP_ALIGN.CENTER, anchor="ctr", pad_x=0.08, fill=fill)
    return y + h + 0.10


def note_bar(slide, y, h, text, size=16, fill="EAF1F8", bold=False):
    """內容區底部的一行說明。h 低於 0.7 時不列入卡片留白檢查。"""
    card_text(slide, ML, y, CW, h, [[(text, INK, bold, size)]], size=size, fill=fill, anchor="ctr")


def build_p3(slide, y):
    # 零件磚紅、價格磚黃，對應下方長條的第一、二根；其餘藍。
    y = stat_chips(slide, y, [
        ("17.3%", "零件供應最高", "C0392B", WHITE, WHITE),
        ("15.0%", "價格次高", "F2B600", INK, INK),
        ("1.4%", "銷售交車最低"),
        ("61%", "態度負面；流失 4.7%"),
    ])
    note_h = 0.62
    rows = figv()["F1"]
    if rows[0]["name"] != "零件供應" or rows[1]["name"] != "價格":
        raise SystemExit(f"F1 前兩根應為零件供應、價格，實際 {[r['name'] for r in rows[:2]]}")
    chart_bars(
        slide, ML, y, CW, BOT - note_h - 0.10 - y,
        [r["name"] for r in rows], [r["p"] * 100 for r in rows],
        errs=[(r["lo"] * 100, r["hi"] * 100) for r in rows],
        colors=[RED, YELLOW] + [BLUE] * (len(rows) - 2),
        title="零件供應流失率最高（17.3%），銷售交車最低", ylabel="流失率（%）",
        name="chart:F1",
    )
    # 說明條逐字照使用者手改版（拿掉「待料通知（R5），話術見附錄 A3。」）。
    note_bar(slide, BOT - note_h, note_h,
             "對應接觸點：零件勝算比 2.58、價格 2.64，分母 21,183 句。")


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

    table_h = 3.44  # v3.7：內容區下延 0.34 全給兩張表格，說明條與下方流程方塊維持原高
    row_h = [0.40] + [(table_h - 0.40) / 5] * 5
    add_table(slide, ML, y, 6.05, table_h, pairs(scale_rows_l, scale_rows_r), [3.15, 2.90], font=15, row_h=row_h)
    add_table(slide, ML + 6.35, y, 6.07, table_h, pairs(qual_l, qual_r), [3.35, 2.72], font=15, row_h=row_h)
    trend_y = y + table_h + 0.10
    trend_h = 0.60
    note_bar(slide, trend_y, trend_h,
             "整體輿情：2026Q3 流失率 4.2%，上季 5.3%，去年同季 10.9%（至 9/19）。佐證見附錄 A2b 的 F9。", size=16)
    # 資料處理鏈（原 F9_pipeline.png），改畫原生方塊：數字轉抄 P5 與 T7 品質報告。
    # v3.6：原「去識別…只標記、不刪除…全部進入標註」說明框刪除，內容併進第 2、3、4 步方塊；
    # 抽查 50 句（seed 42）漏網 0 放講者備註。
    pipe_y = trend_y + trend_h + 0.10
    pipe_h = BOT - pipe_y
    add_card(slide, ML, pipe_y, CW, pipe_h)
    nodes = [
        ("爬取留言", ["22.5 萬則", "三站 5,765 篇"]),
        ("切句・去重・去識別", ["23.6 萬句", "文本遮蔽 517 次"]),
        ("售後關鍵詞篩選", ["21,183 句", "全部進入標註"]),
        ("五指標品質檢查", ["超過 78 字的長句", "占 7.77%", "只標記、不刪除"]),
        ("進入標註", ["供模型與報告", "流失句 c≥2：1,671"]),
    ]
    inner_x, inner_w = ML + 0.14, CW - 0.28
    gap = 0.22
    bw = (inner_w - 4 * gap) / 5
    bh = pipe_h - 0.24
    by = pipe_y + 0.12
    for i, (title, subs) in enumerate(nodes):
        xx = inner_x + i * (bw + gap)
        flow_box(slide, xx, by, bw, bh,
                 [[(str(i + 1), BLUE, True, 26)], [(title, INK, True, 16)]]
                 + [[(sub, NAVY, False, 16)] for sub in subs], size=16)
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
# v3.6：L3、L6、L7 標籤改黃底深字（使用者指定），其餘仍藍底白字。
TAG_FILL = {"L3": YELLOW, "L6": YELLOW, "L7": YELLOW}


def add_flow_box(slide, x, y, w, h, head, body, fill=F8_PROC, edge=BLUE, tag=None, dashed=False, thick=False, size=F8_FONT, max_lines=None):
    """方塊＋粗體標題＋置中內文；L# 標籤貼右上角內緣，標題框讓出標籤寬度。
    tag 可用「·」串多顆（如 L3·L4·L5），會拆成三顆小標籤由右往左排。"""
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
        pill_w = 0.42
        tx = x + w - 0.06
        for code in reversed(tag.split("·")):
            tx -= pill_w
            add_pill(slide, tx, y + 0.07, pill_w, 0.24, code,
                     fill=TAG_FILL.get(code, BLUE), color=INK if code in TAG_FILL else WHITE)
            tx -= 0.04
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
    # v3.7：內容區下延 0.34 吋。方塊高度不動（加高會讓卡片留白低於 0.7），分給兩帶標題各 +0.06、
    # 帶間 +0.08、圖例 +0.06、底部說明列 +0.08（bot_h 預留 1.10）。
    head_h = 0.34 if compact else 0.62
    bot_head_h = 0.56 if compact else 0.62
    box_h = 1.06
    top_y, top_h = y, head_h + box_h + 0.04
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
    tw = [1.36, 1.74, 1.58, 2.20, 1.96, 1.42, 1.56]  # v3.6：流失判斷加寬放三顆標籤，從爬蟲與資料庫 B 各借 0.10
    top = [
        ("論壇爬蟲", ["每日抓新留言", "三站公開論壇"], F8_PROC, BLUE, "L0", False),
        ("去重・去識別", ["作者雜湊、店名", "人名遮蔽（L1）"], F8_PROC, BLUE, "L1", False),
        ("資料庫 B", ["原始輿情", "去識別版，可溯源"], F8_DB, F8_DB_EDGE, "L2", False),
        ("流失判斷", ["r4 逐句判流失、面向", "→ 風險分數 →", "Persona（客群輪廓）"], F8_PROC, BLUE, "L3·L4·L5", False),
        ("洞察報告", ["日報・週報・季報", "趨勢分析、200% 預警"], F8_PROC, BLUE, None, False),
        ("資料庫 A", ["報告池", "日／週／季報、", "預警紀錄"], F8_DB, F8_DB_EDGE, None, False),
        ("Dashboard 1–3", ["1 戰情總覽", "2 報告池・", "3 原始輿情"], F8_PROC, BLUE, None, True),
    ]
    box_y = top_y + head_h
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
    band_gap = 0.26 if compact else 0.40
    mid_y = top_y + top_h + band_gap / 2
    bot_y = top_y + top_h + band_gap
    gut_x = ML + 0.10  # 直向線走帶內左緣
    bot_box_y, bot_box_h = bot_y + bot_head_h, box_h
    db_h = 0.80 if compact else 0.98
    db_y = bot_box_y + bot_box_h + 0.16
    red_y = db_y + db_h + 0.08
    # 底卡先畫，灰線與紅線才不會被蓋住。第 8 頁留 1.10 吋給圖例與說明列（v3.7；v3.2–v3.6 是 0.94）。
    bot_h = (red_y + 0.10 - bot_y) if compact else (BOT - 1.10 - bot_y)
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
    bar_h = 0.38
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
        hot = code in TAG_FILL
        add_card(slide, x, legend_y, cell_w, legend_h, fill="F2B600" if hot else "F4F7FB")
        add_text(
            slide, x + 0.04, legend_y + 0.03, cell_w - 0.06, legend_h - 0.04,
            [
                [(code, INK if hot else BLUE, True, 13), ("  " + brief[code], INK, True, 13)],
                [(name if code != "L5" else "客群輪廓", INK if hot else MUTED, False, 12)],
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
        legend="格內數字為面向出現比例（%）", name="chart:F5", red_at=40,  # 48 與 43 兩格塗紅
    )
    note_bar(slide, BOT - foot_h, foot_h,
             "分母：高、中風險 1,280 人。未分類 199 人列觀察名單，不投遞。Persona（客群輪廓）為規則定義，每項可回溯原句。", size=15)


def build_p8(slide, y):
    # 風險等級對照：數字轉抄 T10「等級與來源」表；公式與門檻轉抄 T10（初版權重）。下方 R1–R8 表不動。
    cap_h = 0.32
    note_bar(slide, y, cap_h, "風險等級對照說明（發言者層級）", size=15, fill="F4F7FB", bold=True)
    header = [cell_text(h, WHITE, True) for h in
              ("等級", "風險分範圍", "發言者數", "占全部發言者", "有被標為流失句（c≥2）的發言者比例")]
    levels = [
        ("高", RED, "≥ 0.6", "1,049", "16.4%", "74.1%"),
        ("中", INK, "0.3–0.6", "231", "3.6%", "19.5%"),
        ("低", BLUE, "< 0.3", "5,114", "80.0%", "1.8%"),
    ]
    rows = [header]
    for name, color, rng, n, share, hit in levels:
        rows.append([cell_text(name, color, True), cell_text(rng), cell_text(n), cell_text(share), cell_text(hit)])
    table_y = y + cap_h + 0.04
    table_h = 1.40
    add_table(slide, ML, table_y, CW, table_h, rows, [1.3, 2.2, 2.2, 2.6, 4.12], font=15,
              row_h=[0.36] + [(table_h - 0.36) / 3] * 3)
    formula_y = table_y + table_h + 0.08
    formula_h = 0.40
    note_bar(slide, formula_y, formula_h,
             "風險分＝模型最高流失機率×0.6＋命中規則數/8×0.4（初版權重）", size=15, bold=True)
    note_y = formula_y + formula_h + 0.08
    note_h = 0.50
    # v4.0：人數與比例都在上表，這條只留一句結論，不再重抄數字列。
    note_bar(slide, note_y, note_h,
             "分級方向可信：高風險 74% 真有流失句，低風險只有 1.8%。", size=15)
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
        # v4.0：98.4% 是兩段標註的一致率，不是模型準確率；卡上明說，標題不再放這個數字。
        ("98.4%", "對得起來", "c≥2 一致率 98.4%，是兩段標註一致率，不是準確率。九面向標完，殘餘僅 4 句，不再另開面向。"),
    ]
    # v3.6：左三卡縮小（窄、字小），右兩張 F1 卡放大並加粗藍框。
    note_h = 0.62  # v4.0：底部改一句結論（單行），0.86 → 0.62，多出的高度還給上方五張卡
    gap = 0.12
    left_w = 6.0
    body_h = BOT - note_h - gap - y
    step_gap = 0.22  # v4.0：底部條縮小後，左三卡維持 1.71 吋高（留白 ≥ 0.7），多出的 0.24 吋進卡距
    step_h = (body_h - 2 * step_gap) / 3
    for i, (num, head, body) in enumerate(steps):
        yy = y + i * (step_h + step_gap)
        card_text(
            slide, ML, yy, left_w, step_h,
            [
                [(num, BLUE, True, 34), ("   " + head, INK, True, 18)],
                [(body, INK, False, 18)],  # v3.7：卡片隨內容區加高，內文 17→18 維持留白 ≥ 0.7
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
        card = card_text(
            slide, right_x, yy, right_w, gold_h,
            [[(num, color, True, 56)], [(head, INK, True, 24)], [(body, INK, False, 20)]],
            size=20, fill="FDEBD0", line=BLUE, anchor="ctr", pad_x=0.12,
        )
        card.line.width = Pt(2.5)
    note_y = BOT - note_h
    # v4.0：原本兩行是左三卡與右兩卡的重抄，改成一句結論；數字都已在本頁卡上。
    card_text(
        slide, ML, note_y, CW, note_h,
        [[("Haiku 初篩召回約 57%，所以第二段複核不能省；人工金標 300 句、正例僅 9 句，0.82 不是穩定成績。", INK, False, 18)]],
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
    prefill_h = 2.00  # v3.7：內容區下延 0.34，上區 +0.14、底部說明卡 +0.06、步驟帶標題與註腳 +0.08，步驟方塊 +0.06
    note_h = prefill_h - table_h - 0.10
    card_text(
        slide, ML, note_y, left_w, note_h,
        [[("同一 600 句測試集比較。", MUTED, False, 15)], [("校準曲線見附錄 A2b。", MUTED, False, 15)]],
        size=15, anchor="ctr",
    )
    lines = [
        "Prefill-only：只輸出各等級機率，不生成文字。",
        "內網單機可訓可推（每句 0.7 秒）；正式規格見附錄 A6。",
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
    # v3.6：五張步驟卡只留藍色標題，重排成一條五步驟流程；做法與數字在附錄 A1 術語表與本頁其他處。
    steps = ["ETL＋\n弱監督標註", "資料切分\n（防洩漏）", "任務轉換", "監督式微調\nSFT", "評估與校準"]
    band_y = y + prefill_h + 0.12
    bar_h = 1.26
    bar_y = BOT - bar_h
    band_h = bar_y - 0.10 - band_y
    add_card(slide, ML, band_y, CW, band_h, fill="EAF1F8")
    add_text(slide, ML + 0.14, band_y + 0.12, CW - 0.28, 0.34,
             [[("五個步驟：從語料到可用的本機模型", NAVY, True, 16)]], size=16, anchor="ctr", margin=0.0)
    cap_h = 0.34
    box_y = band_y + 0.60
    box_h = band_h - 0.60 - cap_h - 0.24
    gap = 0.26
    bw = (CW - 0.28 - 4 * gap) / 5
    for i, name in enumerate(steps):
        xx = ML + 0.14 + i * (bw + gap)
        flow_box(slide, xx, box_y, bw, box_h,
                 [[(str(i + 1), BLUE, True, 46)]] + [[(line, BLUE, True, 21)] for line in name.split("\n")], size=21)
        if i < 4:
            add_arrow(slide, xx + bw + 0.04, box_y + box_h / 2, xx + bw + gap - 0.04, box_y + box_h / 2, width=1.75)
    add_text(slide, ML + 0.14, box_y + box_h + 0.12, CW - 0.28, cap_h,
             [[("各步驟的做法與數字見附錄 A1 術語表；指標見上表與附錄 A2b。", MUTED, False, 14)]],
             size=14, anchor="ctr", margin=0.0)
    card_text(
        slide, ML, bar_y, CW, bar_h,
        [
            [("架構沿用開源 LLM2Jev，推論零 API 費。", INK, False, 16)],  # v4.3：刪與右上卡重複的一句
            [("最高信心桶 n=71、實際約 68%（約七成），見附錄 A2b。", INK, False, 16)],
            [("同一 600 句測試集：r4 F1 0.685，高於 Haiku 零樣本的 F1 0.58。", INK, False, 16)],
        ],
        size=16, fill="EAF1F8", anchor="ctr",
    )


def build_p11(slide, y):
    # v3.6：四張卡只留大數字與藍色標題（解釋文字刪除，內容在下表與第 10、12 頁），字放大。
    # v4.0（B #8）：標籤要跟數字說同一件事。74% 是「高風險發言者確有流失句」的比例，不是「分數說得出原因」；
    # 0 元是 API 費；ARI 0.08 不適合當大字，只留在下表「四個客群」列，第四格改以「每項可回溯原句」為主張，
    # 大字用 R1–R8（八條規則）。每張卡補一行與標籤一致的說明，數字只用本冊已有的。
    cards = [
        ("128 人", "靜默出走者", "沒抱怨就找出口；只看客訴看不到這群人"),
        ("74%", "高風險確有流失句", "高風險 1,049 人中 74% 有流失句，低風險 1.8%"),
        ("0 元", "API 費", "內網自有 GPU，每句 0.7 秒"),
        ("R1–R8", "每項可回溯原句", "命中規則與機率一起標出，每句回得到去識別原句"),
    ]
    gap_x, gap_y = 0.14, 0.10
    card_w = (CW - gap_x) / 2
    card_h = 1.62  # v4.0：多一行 18pt 說明，1.40 → 1.62；下表列高仍夠放一行 16pt
    for i, (num, head, sub) in enumerate(cards):
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        card_text(
            slide, x, yy, card_w, card_h,
            [[(num, BLUE, True, 48)], [(head, BLUE, True, 26)], [(sub, INK, False, 18)]],
            size=26, align=PP_ALIGN.CENTER, anchor="ctr",
        )
    table_y = y + 2 * card_h + gap_y + 0.12
    rows = [
        [cell_text(h, WHITE, True) for h in ("", "只看客訴", "本案")],
        [cell_text("沒抱怨就走", INK, True), cell_text("看不到這群人"), cell_text("靜默出走者 128 人，替代 55% 到一般外廠")],
        [cell_text("分數", INK, True), cell_text("沒有原因"), cell_text("機率 6 成＋規則 4 成；高 74%、低 1.8%")],
        [cell_text("在哪裡算", INK, True), cell_text("資料得出門"), cell_text("內網自有 GPU，每句 0.7 秒，F1 0.685，API 費 0")],
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
        channel = cites = check = ""
        text = ""
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
                while i < len(lines) and lines[i].strip() and not lines[i].startswith("#"):
                    chunk.append(lines[i].strip())
                    i += 1
                text = "".join(chunk)
                continue
            i += 1
        items.append({"persona": persona.strip(), "touch": touch, "channel": channel,
                      "cites": cites, "check": check, "text": text})
    items = [it for it in items if it["touch"] in ("T1", "T2", "T3")]
    if len(items) != 12:
        raise SystemExit(f"P12 應有 12 則，讀到 {len(items)}")
    return items


# 第 14 頁每個渠道一則範本：四則涵蓋四種 Persona（客群輪廓）與三種接觸點（T3 出現兩次，因為口碑建議者只有 T3 走 App）。
P12_TEMPLATES = [
    ("Email", "過保精算派", "T1"),
    ("LINE 官方帳號推播", "靜默出走者", "T2"),
    ("服務廠專員電話腳本", "品質失望派", "T3"),
    ("App 通知", "口碑建議者", "T3"),
]
TOUCH_NAME = {"T1": TOUCH_COLS[0], "T2": TOUCH_COLS[1], "T3": TOUCH_COLS[2]}


def build_p12(slide, y):
    msgs = {(m["persona"], m["touch"]): m for m in load_p12_messages()}
    foot_h = 0.82
    gap = 0.12
    card_w = (CW - gap) / 2
    card_h = (BOT - foot_h - 0.12 - y - gap) / 2
    for i, (channel, persona, touch) in enumerate(P12_TEMPLATES):
        msg = msgs[(persona, touch)]
        if msg["channel"] != channel:
            raise SystemExit(f"第 14 頁範本 {persona}×{touch} 的渠道是 {msg['channel']}，不是 {channel}")
        if not msg["check"].startswith("通過"):
            raise SystemExit(f"第 14 頁範本 {persona}×{touch} 查核未通過：{msg['check']}")
        compact = re.sub(r"\s+", "", msg["text"])
        preview = compact[:76] + "…"
        col, row = i % 2, i // 2
        x = ML + col * (card_w + gap)
        yy = y + row * (card_h + gap)
        card_text(
            slide, x, yy, card_w, card_h,
            [
                [(channel, BLUE, True, 20)],
                [(f"{persona} × {TOUCH_NAME[touch]}", INK, True, 16)],
                [(preview, INK, False, 18)],
                [(f"引用條目 {msg['cites']}　查核通過", MUTED, False, 15)],
            ],
            size=18, anchor="ctr",
        )
    card_text(
        slide, ML, BOT - foot_h, CW, foot_h,
        [
            [("12 則主表已對 76 條條款查核通過；每個渠道列一則範本", INK, True, 17)],
            [("待料全文見附錄 A3，客訴回訪見附錄 A5。人工核准才投遞。", INK, False, 16)],
        ],
        size=16, anchor="ctr",
    )


def build_p13(slide, y):
    left_w = 5.35
    # v3.6：財務卡放大並以大數字呈現；其他左卡縮小保留。第三個數是高度權重（吋），第四個是框色。
    items = [
        ("需求", [[("人走了才知道。過保、刪項、間隔拉長時先找到人。", INK, False, 15)]], 0.70, None),
        ("技術", [[("判斷、分群、生成都有原型。8 條規則已對到 DMS 欄位。", INK, False, 15)]], 0.94, None),
        ("財務：人力成本節省", [
            [("106 人時（估）→ 4.1 小時", BLUE, True, 26)],
            [("省 90% 以上（估）、零 API 費", BLUE, True, 20)],
            [("人工逐句篩 2.1 萬句約需 106 人時（估）；本機模型 4.1 小時跑完。人力改花在審名單與話術。", INK, False, 14)],
        ], 2.00, BLUE),
        ("風險", [[("五項主要風險，對策與責任人見右表。", INK, False, 15)]], 0.70, None),
        # v4.2：最後一句加「跨部門月審」（與右表組織列、附錄 A6 一致）。
        ("怎麼讀右表", [[("技術：寫錯條款只引用 76 條並人工審；模糊句多報就當初篩。資料註明論壇母體，上線改 CRM。法規只用去識別版。客群寫成可回溯規則，跨部門月審。", INK, False, 15)]], 1.26, None),
    ]
    gap = 0.08
    avail = BOT - y - gap * (len(items) - 1)
    scale = avail / sum(rh for _, _, rh, _ in items)
    yy = y
    for head, body, rh, line in items:
        rh *= scale
        card = card_text(
            slide, ML, yy, left_w, rh,
            [[(head, BLUE, True, 18 if line else 17)]] + body,
            size=15, anchor="ctr", fill="EAF1F8" if line else "F4F7FB", line=line,
        )
        if line is not None:
            card.line.width = Pt(2.0)
        yy += rh + gap
    # 風險登錄表前 5 列（iPAS骨架頁_草稿.md）。四欄：層別、風險、對策、責任人。
    risks = [
        ("層別", "風險", "對策", "責任人"),
        ("技術", "生成內容寫錯價格或保固條款", "只引用 76 條知識庫、數字逐字比對、人工審核必經", "A"),
        ("技術", "模型在模糊句多報（困難層 F1 ≤ 0.51，精確率 0.34）", "定位成「初篩＋人工複核」", "A"),
        ("資料", "論壇代表性（正例 67% 來自 Mobile01，母體是論壇發言者）", "分析頁註明母體與來源構成；上線改用 CRM 資料", "B"),
        ("法規", "個資與再識別", "去識別流程，簡報與 Demo 只用去識別版", "A"),
        ("組織", "Persona（客群輪廓）被質疑主觀（ARI 0.08）", "規則定義、可回溯原句；每月跨部門工作小組覆核", "B"),
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
    moat_h = 1.30
    card_text(
        slide, ML, moat_y, CW, moat_h,
        [
            [("數據護城河：三項資產，全部留在和泰內網", BLUE, True, 17)],
            [("語料：2.1 萬句標註＋300 句人工金標。每季重標，審核回饋持續再訓練。", INK, False, 15)],
            [("模型：自有 4B 模型，地端部署、API 封裝；GPU 伺服器建議規格見附錄 A6，零 API 費。", INK, False, 15)],
            [("知識庫：76 條官方條款＋每則話術查核紀錄。價格與保固只引用這 76 條。", INK, False, 15)],
        ],
        size=15, anchor="ctr",
    )
    # v3.6：五張步驟卡改成 24 週甘特圖（原生形狀）。每條橫條旁保留該階段一句說明，取自原卡片文字。
    phases = [
        ("資料接入", 1, 4, "R1–R8 換成 DMS 實際欄位，工單去識別後接入"),
        ("模型校準", 5, 8, "重標 300 句金標，重驗 r4，再調觸發門檻"),
        ("單一據點試行", 9, 16, "一個服務廠跑完，專員審核後投遞，未核准不發出"),
        ("擴大至全台", 17, 24, "依試行調話術與渠道分批上線，不一次開全台"),
        ("持續監控", 9, None, "日／週／月／季監控；不達標即重訓（附錄 A6）"),  # v4.2：改引附錄 A6
    ]
    gy = moat_y + moat_h + 0.10
    gh = BOT - gy
    add_card(slide, ML, gy, CW, gh, fill="F4F7FB", name="chart:gantt:card")
    title_h = 0.28
    add_text(slide, ML + 0.14, gy + 0.08, 7.0, title_h,
             [[("導入時程：合計約 24 週（持續監控不設終點）", NAVY, True, 15)]],
             size=15, margin=0.0, anchor="ctr", name="chart:gantt:title")
    name_w, desc_w = 1.75, 4.40
    tl_x = ML + 0.14 + name_w
    tl_w = CW - 0.28 - name_w - desc_w - 0.30
    desc_x = tl_x + tl_w + 0.30
    axis_y = gy + 0.08 + title_h + 0.02
    axis_h = 0.22
    rows_y = axis_y + axis_h + 0.02
    row_h = (gy + gh - 0.10 - rows_y) / len(phases)
    bottom = rows_y + row_h * len(phases)

    def wx(week):  # 第 week 週結束時的 x；week=0 是起點
        return tl_x + tl_w * week / 24

    for w in range(0, 25, 4):
        add_line(slide, wx(w), rows_y, wx(w), bottom, color=GRID, width=0.75)
        if w:
            add_text(slide, wx(w) - 0.45, axis_y, 0.9, axis_h, [[(f"{w} 週", MUTED, False, 12)]],
                     size=12, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name="chart:gantt:tick")
    for i, (name, start, end, desc) in enumerate(phases):
        ry = rows_y + i * row_h
        add_pill(slide, ML + 0.14, ry + (row_h - 0.26) / 2, 0.26, 0.26, str(i + 1), size=12)
        add_text(slide, ML + 0.46, ry, name_w - 0.32, row_h, [[(name, INK, True, 14)]],
                 size=14, anchor="ctr", margin=0.0)
        bar_h = row_h - 0.08
        bx = wx(start - 1)
        if end is None:  # 持續監控：第 9 週起，箭頭伸出 24 週之外
            bar_w = wx(24) + 0.26 - bx
            bar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(bx), Inches(ry + 0.04), Inches(bar_w), Inches(bar_h))
            bar.fill.solid()
            bar.fill.fore_color.rgb = NAVY
            bar.line.fill.background()
            bar.name = "chart:gantt:bar"
            label = f"第 {start} 週起，不設終點"
        else:
            bar_w = wx(end) - bx
            add_rect(slide, bx, ry + 0.04, bar_w, bar_h, fill=BLUE, name="chart:gantt:bar")
            label = f"{start}–{end} 週"
        add_text(slide, bx, ry + 0.04, min(bar_w, wx(24) - bx), bar_h, [[(label, WHITE, True, 12)]],
                 size=12, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name="chart:gantt:label")
        add_text(slide, desc_x, ry, desc_w, row_h, [[(desc, INK, False, 13)]],
                 size=13, anchor="ctr", margin=0.0)


def add_segment(slide, x1, y1, x2, y2, color=BLUE, width=1.5, name="chart-line"):
    """斜線：用旋轉的極薄矩形畫（同 F6 對角線），外框不會像斜向連接線那樣罩住整塊圖區。"""
    import math

    length = math.hypot(x2 - x1, y2 - y1)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    seg = add_rect(slide, cx - length / 2, cy - 0.005, length, 0.01, fill=None, line=color, width=width, name=name)
    seg.rotation = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return seg


def mock_frame(slide, x, y, w, h, title):
    """Dashboard 示意畫面的外框：淺底、深藍邊、深藍標題列。回傳 (內容區 y, 內容區高)。"""
    add_card(slide, x, y, w, h, fill="F4F7FB", line=NAVY)
    bar_h = 0.34
    add_rect(slide, x, y, w, bar_h, fill=NAVY)
    add_text(slide, x + 0.12, y + 0.02, w - 0.24, bar_h - 0.04, [[(title, WHITE, True, 14)]],
             size=14, anchor="ctr", margin=0.0)
    return y + bar_h + 0.10, h - bar_h - 0.20


def mock_row(slide, x, y, w, h, tag, text, tag_fill=BLUE, tag_color=WHITE, tag_w=1.0, size=12):
    """示意清單的一列：左邊小標籤、右邊一行字。"""
    add_card(slide, x, y, w, h, fill="EAF1F8")
    add_pill(slide, x + 0.08, y + (h - 0.26) / 2, tag_w, 0.26, tag, size=12, fill=tag_fill, color=tag_color)
    add_text(slide, x + 0.08 + tag_w + 0.08, y + 0.02, w - tag_w - 0.24, h - 0.04,
             [[(text, INK, False, size)]], size=size, anchor="ctr")


def build_p15(slide, y):
    """附錄 A0：五個 Dashboard 的示意畫面（原生形狀）。數字只用簡報與報告已有的；代號為示意。
    上列 Dashboard 1–3（洞察），下列 Dashboard 4 知識庫、5 審核佇列（沿用原線框）。"""
    cap_h = 0.30
    gap = 0.12
    row_h = (BOT - y - cap_h - 2 * gap) / 2
    top_w = (CW - 2 * gap) / 3
    bot_w = (CW - gap) / 2
    y2 = y + row_h + gap

    # ---- Dashboard 1 戰情總覽：三個風險等級 KPI 磚、本季流失率、季趨勢小圖 ----
    x = ML
    by, bh = mock_frame(slide, x, y, top_w, row_h, "Dashboard 1　戰情總覽")
    tiles = [("高", "1,049", "C0392B", WHITE), ("中", "231", "F2B600", INK), ("低", "5,114", "2F5D9F", WHITE)]
    tw = (top_w - 0.24 - 0.16) / 3
    th = 0.72
    for i, (lv, n, fill, col) in enumerate(tiles):
        card_text(slide, x + 0.12 + i * (tw + 0.08), by, tw, th,
                  [[(f"{lv}風險", col, True, 13)], [(n, col, True, 18)]],
                  size=13, fill=fill, align=PP_ALIGN.CENTER, anchor="ctr", pad_x=0.04, pad_y=0.04)
    ty = by + th + 0.10
    tth = by + bh - ty
    add_card(slide, x + 0.12, ty, top_w - 0.24, tth, fill="EAF1F8", name="chart:trend:card")
    add_text(slide, x + 0.20, ty + 0.04, top_w - 0.40, 0.28, [[("2026Q3 流失率 4.2%，季趨勢", INK, True, 14)]],
             size=14, anchor="ctr", margin=0.0, name="chart:trend:title")
    pts = [("2025Q3", 10.9), ("2026Q2", 5.3), ("2026Q3", 4.2)]  # T15：去年同季、上季、本季
    px0, px1 = x + 0.55, x + top_w - 0.55
    py0, py1 = ty + 0.72, ty + tth - 0.32
    coords = []
    for i, (_q, v) in enumerate(pts):
        cx = px0 + (px1 - px0) * i / (len(pts) - 1)
        cy = py1 - (py1 - py0) * v / 12.0
        coords.append((cx, cy))
    for (ax, ay), (bx2, by2) in zip(coords, coords[1:]):
        add_segment(slide, ax, ay, bx2, by2, color=BLUE, width=2.0, name="chart:trend:line")
    for (cx, cy), (q, v) in zip(coords, pts):
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - 0.07), Inches(cy - 0.07), Inches(0.14), Inches(0.14))
        dot.fill.solid()
        dot.fill.fore_color.rgb = RED if v == min(p[1] for p in pts) else BLUE
        dot.line.fill.background()
        dot.name = "chart:trend:dot"
        add_text(slide, cx - 0.45, cy - 0.34, 0.9, 0.24, [[(f"{v}%", INK, True, 12)]], size=12,
                 align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name="chart:trend:value")
        add_text(slide, cx - 0.45, py1 + 0.06, 0.9, 0.24, [[(q, MUTED, False, 12)]], size=12,
                 align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0, name="chart:trend:cat")

    # ---- Dashboard 2 報告池：日報／週報／季報／預警紀錄 ----
    x = ML + top_w + gap
    by, bh = mock_frame(slide, x, y, top_w, row_h, "Dashboard 2　報告池")
    rw = top_w - 0.24
    hero_h = 0.70
    small_h = (bh - hero_h - 3 * 0.08) / 3
    rows = [
        ("日報", "每日排程：新留言 → 標註與風險 → 日報"),
        ("週報", "趨勢分析，依車型、風險等級、客群篩選"),
    ]
    yy = by
    for tag, text in rows:
        mock_row(slide, x + 0.12, yy, rw, small_h, tag, text, tag_w=0.60)
        yy += small_h + 0.08
    card_text(slide, x + 0.12, yy, rw, hero_h,
              [[("季報　2026Q3", BLUE, True, 16)], [("流失率 4.2%，上季 5.3%，去年同季 10.9%", INK, False, 13)]],
              size=13, fill="EAF1F8", anchor="ctr", pad_x=0.10, pad_y=0.04)
    yy += hero_h + 0.08
    mock_row(slide, x + 0.12, yy, rw, small_h, "預警", "討論量達前 4 週平均 3 倍且至少 5 句就亮燈", tag_fill=RED, tag_w=0.60)

    # ---- Dashboard 3 原始輿情：篩選列＋去識別句子 ----
    x = ML + 2 * (top_w + gap)
    by, bh = mock_frame(slide, x, y, top_w, row_h, "Dashboard 3　原始輿情")
    filt_h = 0.36  # v3.7：+0.06
    add_card(slide, x + 0.12, by, rw, filt_h, fill="EAF1F8")
    add_text(slide, x + 0.20, by + 0.02, rw - 0.16, filt_h - 0.04,
             [[("篩選：來源 ▾　日期 ▾　流失等級 ▾　面向 ▾", NAVY, True, 12)]], size=12, anchor="ctr", margin=0.0)
    sents = [  # 取自 T10 代表句（去識別檔），來源、p_churn 與面向照報告；第一則兩行、第二則一行
        ("PTT", "p 0.998", "保固", "10萬耶，過保外廠處理吧，說不定一萬都不用就幫你解決", 1.00),  # v3.7：各 +0.08／+0.09
        ("Mobile01", "p 0.998", "價格", "電瓶、輪胎都不用在原廠換", 0.69),
    ]
    yy = by + filt_h + 0.10
    for src_, p, aspect, text, h in sents:
        card_text(slide, x + 0.12, yy, rw, h,
                  [[(src_, BLUE, True, 12), (f"　{p}　面向：{aspect}", MUTED, False, 12)], [(text, INK, False, 13)]],
                  size=12, fill="EAF1F8", anchor="ctr", pad_x=0.10, pad_y=0.04)
        yy += h + 0.12

    # ---- Dashboard 4 知識庫：76 條，條目清單 ----
    x = ML
    by, bh = mock_frame(slide, x, y2, bot_w, row_h, "Dashboard 4　知識庫")
    rw = bot_w - 0.24
    card_text(slide, x + 0.12, by, rw, 0.70,
              [[("76 條", BLUE, True, 22), ("　官網 40／手冊 36", INK, True, 15)],
               [("價格、保固年限、里程、次數只能引用這 76 條；RAG 檢索與審核都查這裡", MUTED, False, 12)]],
              size=12, fill="EAF1F8", anchor="ctr", pad_x=0.10, pad_y=0.04)
    entries = [
        ("1", "新車基本保證"),
        ("13", "免費延保的次數、車種與建議售價上限"),
        ("41", "新車基本保證的組成（原廠三年加總代理追加一年）"),
        ("52", "準時保養享延長保證（連續準時 8 次定保）"),
    ]
    yy = by + 0.70 + 0.08
    eh = (bh - 0.70 - 0.08 - 3 * 0.06) / 4
    for code, title in entries:
        mock_row(slide, x + 0.12, yy, rw, eh, code, title, tag_fill=NAVY, tag_w=0.50, size=13)
        yy += eh + 0.06

    # ---- Dashboard 5 溝通審核佇列：沿用原線框 ----
    x = ML + bot_w + gap
    by, bh = mock_frame(slide, x, y2, bot_w, row_h, "Dashboard 5　溝通審核佇列")
    item_h = 1.37  # v3.7：列高 +0.17，整個給草稿卡
    card_text(slide, x + 0.12, by, rw, item_h,
              [
                  [("車主 H-7F3A　風險 高", INK, True, 20)],  # v3.7：卡片加高 0.17，字級 18／16 → 20／18
                  [("Persona（客群輪廓）過保精算派　觸發 R1 過保", INK, False, 18)],
                  [("話術草稿　引用條目 41、52", NAVY, False, 18)],
              ],
              size=16, fill="EAF1F8", anchor="ctr", pad_x=0.12)
    btn_w, btn_gap, btn_h = 1.30, 0.10, 0.46
    btn_y = by + item_h + 0.10
    labels = [("核准", "2F5D9F"), ("改寫", "44546A"), ("退回", "C05600")]
    for i, (label, fill) in enumerate(labels):
        bx = x + 0.12 + i * (btn_w + btn_gap)
        add_card(slide, bx, btn_y, btn_w, btn_h, fill=fill)
        add_text(slide, bx, btn_y + 0.03, btn_w, btn_h - 0.06, [[(label, WHITE, True, 16)]],
                 size=16, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0)
    add_text(slide, x + 0.12, btn_y + btn_h + 0.08, rw, 0.30,
             [[("核准、改寫或退回；未核准不投遞。", MUTED, False, 13)]], size=13, anchor="ctr", margin=0.0)

    add_text(slide, ML, BOT - cap_h, CW, cap_h,
             [[("示意畫面，非實際介面；代號為示意，不是論壇帳號。決賽再給可操作版。", MUTED, False, 13)]],
             size=13, anchor="ctr", margin=0.0)


SLIDES.append({
    "id": "A2",
    "section": "附錄 A2 補充圖表（不計入 15 頁）",
    "title": "三站發言者流失率，與發言者風險分布",
    "reports": ["reports/T7_stats_tests.md", "reports/T10_risk_persona_report.md"],
    "figures": ["reports/figures/F2.png", "reports/figures/F4.png"],
})
SLIDES.append({
    "id": "A2b",
    "section": "附錄 A2b 補充圖表（不計入 15 頁）",
    "title": "校準曲線，與季趨勢預警",
    "reports": ["reports/T8_r4_report.md", "reports/T15_trend_reports.md"],
    "figures": ["reports/figures/F6.png", "reports/figures/F9.png"],
})
SLIDES.append({
    "id": "A3",
    "section": "附錄 A3 待料通知話術（不計入 15 頁）",
    "title": "待料逾 7 天就主動通知",
    "reports": ["knowledge/generated_examples.md", "reports/T14_generation_report.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A4",
    "section": "附錄 A4 CRM 觸發門檻（不計入 15 頁）",
    "title": "八條規則的欄位與門檻",
    "reports": ["reports/T10_risk_persona_report.md", "L7運作流程_草稿.md"],
    "figures": [],
})
SLIDES.append({
    "id": "A5",
    "section": "附錄 A5 客訴回訪話術（不計入 15 頁）",
    "title": "客訴結案第 7 天回訪，不推銷、不要求刪評",
    "reports": ["客訴關懷策略_草稿.md", "knowledge/generated_examples.md"],
    "figures": [],
})
# v4.2：附錄 A6 部署架構與 MLOps 閉環（iPAS 指引 5.2），插在 A5 之後、A1 之前。
SLIDES.append({
    "id": "A6",
    "section": "附錄 A6 部署與閉環（不計入 15 頁）",
    "title": "地端部署、四級監控、不達標即重訓：監控到再訓練閉環",
    "reports": ["L7運作流程_草稿.md", "iPAS骨架頁_草稿.md", "iPAS導入對照_2026-09-25.md", "reports/T16_cost_notes.md"],
    "figures": [],
})
# v3.6：使用者把術語表移到最後一頁。代號仍是 A1，只換順序。
SLIDES.append({
    "id": "A1",
    "section": "附錄 A1 術語表（不計入 15 頁）",
    "title": "本案用到的技術名詞：定義與在本案的用法",
    "reports": ["reports/T8_r4_report.md", "reports/T9_human_eval.md", "reports/T10_risk_persona_report.md"],
    "figures": [],
})


def build_a1(slide, y):
    rows = [
        ("ETL", "Extract-Transform-Load：擷取、清洗轉換、載入。與 ELT（先載入再轉換）不同", "爬蟲擷取→去重、切句、售後關鍵詞篩選→寫入 jsonl；23.6 萬句留 21,183 句"),
        ("弱監督標註（LLM-as-labeler）", "用模型而非人工產生訓練標籤，事後以人工樣本驗證品質", "Haiku 初篩＋Sonnet／GPT 帶上下文複核；人工 300 句驗證"),
        ("監督式學習／監督式微調 SFT", "用「輸入＋正確答案」訓練；SFT 是在預訓練模型上以標籤資料微調，非從零訓練", "以 21,183 句 LLM 標籤微調 Qwen3-4B"),
        ("QLoRA（NF4 4-bit、LoRA r=16）", "把基底模型量化成 4 位元，只訓練低秩附加參數，省顯存", "單張 GPU 數小時可重訓；adapter 約數十 MB"),
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
    f9_h = 2.62  # F9.png 是依 12.42×2.62 吋重畫的，格高固定；v3.7 內容區下延的 0.34 吋全給上方 F6 散點圖
    chart_h = BOT - y - 2 * cap_h - 3 * gap - f9_h
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


def message_cards(slide, y, msgs, touch_label, footnote: str | None = None):
    """A3／A5 共用：兩張話術卡，全文 24pt，標題與引用 20pt，查核 16pt（v3.7 卡片隨內容區加高 0.17，字級 18／15 → 20／16）。
    footnote（v4.0，A5 用）：卡片下方一行 18pt 灰字小註，兩張卡各讓出 0.19 吋。"""
    foot_h = 0.30 if footnote else 0.0
    card_h = (BOT - foot_h - y - 0.12) / 2
    for i, msg in enumerate(msgs):
        yy = y + i * (card_h + 0.12)
        text = re.sub(r"([，。、；：！？）】」])\s+", r"\1", msg["text"])  # 全形標點後的空格不進簡報，行首才不會多一格
        card_text(
            slide, ML, yy, CW, card_h,
            [
                [(f"{msg['persona']} × {touch_label}　{msg['channel']}", BLUE, True, 20)],
                [(f"引用條目　{msg['cites']}", NAVY, True, 20)],
                [(text, INK, False, 24)],
                [(f"查核結果　{msg['check']}", MUTED, False, 16)],
            ],
            size=20, pad_y=0.10, anchor="ctr",
        )
    if footnote:
        add_text(slide, ML, BOT - foot_h, CW, foot_h, [[(footnote, MUTED, False, 18)]],
                 size=18, margin=0.0, anchor="ctr")


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
    # v4.0（B #20）：第二則的「【改善做法，由專員填入】」是刻意保留的填寫欄位，評審只看 PDF，頁上要說明。
    message_cards(slide, y, load_a5_messages(), "客訴結案後 7 天回訪",
                  footnote="【】為專員填寫欄位，刻意保留")


def build_a6(slide, y):
    """v4.2 附錄 A6：部署架構與 MLOps 閉環（對照 iPAS 指引 5.2）。全部 pptx 原生形狀。
    左：部署架構四段（位置與建議規格、服務封裝、權限、版本管理）；右上：監控→門檻→重訓→分批替換的閉環，
    紅色回頭線回到監控，下方日／週／月／季監控表；底：四部門分工橫條。只有 F1 0.8、κ 0.6 是定案門檻，
    其餘門檻寫「超門檻」。數字（0.7 秒、300 句、12 個月、r4）都是本冊已有的；建議規格依 T48b。"""
    foot_h = 0.24
    foot_y = BOT - foot_h
    # ---- 底區：跨部門分工橫條（外框卡含四張小卡，外框不列入留白檢查）----
    dept_h = 1.46
    dept_y = foot_y - 0.06 - dept_h
    add_card(slide, ML, dept_y, CW, dept_h, fill="F4F7FB")
    add_text(slide, ML + 0.14, dept_y + 0.06, CW - 0.28, 0.30,
             [[("跨部門分工　", NAVY, True, 15),
               ("每月跨部門工作小組；共同指標＝高風險車主 12 個月回廠率（上線後母體是 CRM 車主）", INK, False, 14)]],
             size=14, margin=0.0, anchor="ctr")
    depts = [
        ("業務行銷", "定三層 KPI 與客群策略，每月審高風險名單。"),
        ("服務廠／客服", "審核與投遞話術，回收退件與客訴案例（Human-in-the-Loop）。"),
        ("法務風險", "去識別流程、條款引用、拒收名單與頻率上限審查。"),
        ("資訊", "地端部署、API、權限、備援與版本替換。"),
    ]
    d_gap = 0.10
    d_w = (CW - 0.28 - 3 * d_gap) / 4
    d_y = dept_y + 0.42
    d_h = dept_y + dept_h - 0.08 - d_y
    for i, (head, body) in enumerate(depts):
        dx = ML + 0.14 + i * (d_w + d_gap)
        card_text(slide, dx, d_y, d_w, d_h,
                  [[(head, BLUE, True, 14)], [(body, INK, False, 13)]],
                  size=13, fill="EAF1F8", pad_x=0.12, pad_y=0.05, anchor="ctr")
    add_text(slide, ML, foot_y, CW, foot_h,
             [[("以上為導入設計，尚未實作；週期與門檻取自 L7 運作流程草稿第 6 節。", MUTED, False, 12)]],
             size=12, margin=0.0, anchor="ctr")

    # ---- 左區：部署架構（外框卡含四張小卡）----
    top_h = dept_y - 0.10 - y
    left_w = 5.60
    add_card(slide, ML, y, left_w, top_h, fill="F4F7FB")
    add_text(slide, ML + 0.14, y + 0.06, left_w - 0.28, 0.30,
             [[("部署架構", NAVY, True, 16)]], size=16, margin=0.0, anchor="ctr")
    arch = [
        ("部署位置", "和泰內網地端（私有雲），資料不出門；論壇文字只做研究語料，上線改用工單與客訴文字。"
                   "建議規格：GPU 伺服器 2 台（主＋備援），各 2× L40S 48 GB、256 GB RAM、2 TB NVMe；試行可先用 1 台。"),
        ("服務封裝", "自有 4B 模型（r4）包成內網 API，四個端點：流失判斷、風險分、Persona（客群輪廓）、RAG 話術。"
                   "CRM／DMS 每日批次呼叫，溝通佇列即時呼叫；每句約 0.7 秒。"),
        ("權限", "Dashboard 依角色分權：服務廠專員只審核與投遞，AI 團隊調門檻與重訓，法務查條款引用與拒收名單。"
                 "投遞紀錄寫回 CRM：時間、渠道、話術版本、審核人。"),
        ("版本管理", "每版記錄資料版本、金標 F1／κ、校準表（r4 → r5…）；單張 GPU 數小時可重訓。"
                   "新版先換單一據點試行，再換全台。"),
    ]
    a_x = ML + 0.12
    a_w = left_w - 0.24
    a_gap = 0.05
    a_top = y + 0.36
    a_avail = y + top_h - 0.06 - a_top - a_gap * (len(arch) - 1)
    text_w = a_w - 2 * 0.12 - 0.08
    need = [0.25 + est_lines(body, text_w, 12) * (12 / 72.0 * 1.15) + 2 / 72.0 + 0.12 for _, body in arch]
    scale = a_avail / sum(need)
    if scale < 1.0:
        raise SystemExit(f"A6 部署架構四段估計高度 {sum(need):.2f} 超過可用 {a_avail:.2f}")
    yy = a_top
    for (head, body), h0 in zip(arch, need):
        h = h0 * scale
        card_text(slide, a_x, yy, a_w, h,
                  [[(head, BLUE, True, 14)], [(body, INK, False, 12)]],
                  size=12, fill="EAF1F8", pad_x=0.12, pad_y=0.05, anchor="ctr")
        yy += h + a_gap

    # ---- 右上區：監控到再訓練閉環 ----
    r_x = ML + left_w + 0.14
    r_w = CW - left_w - 0.14
    add_text(slide, r_x, y, r_w, 0.30,
             [[("監控到再訓練閉環", NAVY, True, 16),
               ("　不達標就重訓、分批替換，再回到監控", MUTED, False, 13)]],
             size=16, margin=0.0, anchor="ctr")
    steps = ["監控", "觸發門檻", "再訓練／更新", "分批替換"]
    box_y = y + 0.36
    box_h = 0.50
    arrow_w = 0.34
    box_w = (r_w - 3 * arrow_w) / 4
    centers = []
    for i, text in enumerate(steps):
        bx = r_x + i * (box_w + arrow_w)
        shape = add_card(slide, bx, box_y, box_w, box_h, fill="2F5D9F", radius=0.12)
        tf = shape.text_frame
        for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(tf, side, Inches(0.02))
        set_tf(tf, [[(text, WHITE, True, 14)]], 14, align=PP_ALIGN.CENTER, anchor="ctr")
        centers.append(bx + box_w / 2)
        if i < 3:
            add_arrow(slide, bx + box_w + 0.03, box_y + box_h / 2, bx + box_w + arrow_w - 0.03, box_y + box_h / 2)
    # 回頭線（紅）：分批替換 → 下方 → 回到監控；標籤放在回頭線上方的中段。
    loop_y = box_y + box_h + 0.34
    add_arrow(slide, centers[3], box_y + box_h + 0.02, centers[3], loop_y, color=F8_HUMAN_EDGE, head=False)
    add_arrow(slide, centers[3], loop_y, centers[0], loop_y, color=F8_HUMAN_EDGE, head=False)
    add_arrow(slide, centers[0], loop_y, centers[0], box_y + box_h + 0.02, color=F8_HUMAN_EDGE, head=True)
    add_text(slide, centers[0] + 0.30, box_y + box_h + 0.06, centers[3] - centers[0] - 0.60, 0.24,
             [[("替換後回到監控；不達標再進下一輪", F8_HUMAN_EDGE, False, 12)]],
             size=12, align=PP_ALIGN.CENTER, anchor="ctr", margin=0.0)
    # 四級監控表
    header = ["週期", "監控什麼", "觸發門檻", "動作"]
    body = [
        ("每日", "投遞量、查核失敗率、投遞失敗", "查核失敗率異常", "暫停該接觸點，人工檢查"),
        ("每週", "退回與修改的話術樣本", "退件集中於同一條目", "更新提示詞與知識庫條目"),
        ("每月", "高風險名單命中率（R7 回驗）、輸入句分布漂移（KS 檢定）", "命中率下降或分布差異超門檻", "調觸發門檻、重評 Persona（客群輪廓）"),
        ("每季", "300 句人工金標：F1、κ", "F1 < 0.8 或 κ < 0.6", "重訓下一版，先試行據點再全台"),
    ]
    rows = [[cell_text(h, WHITE, True) for h in header]]
    for cyc, what, thr, act in body:
        rows.append([cell_text(cyc, INK, True), cell_text(what), cell_text(thr), cell_text(act)])
    col_w = [0.70, 2.56, 1.70, r_w - 0.70 - 2.56 - 1.70]  # v4.3：監控什麼欄加寬，每日列不再孤字
    t_y = loop_y + 0.10
    t_h = y + top_h - t_y
    est, total = table_row_heights(rows, col_w, 12, header_h=0.34, pad=0.10, min_h=0.40)
    if total > t_h:
        raise SystemExit(f"A6 監控表估計高度 {total:.2f} 超過可用 {t_h:.2f}")
    extra = (t_h - total) / (len(rows) - 1)
    row_h = [est[0]] + [h + extra for h in est[1:]]
    add_table(slide, r_x, t_y, r_w, t_h, rows, col_w, font=12, row_h=row_h)


BUILDERS = [build_toc, build_p1, build_p2, build_p3, build_p4, build_p5, build_p6, build_p7, build_p8, build_p9, build_p10, build_p11, build_p12, build_p13, build_p14, build_p15, build_a2, build_a2b, build_a3, build_a4, build_a5, build_a6, build_a1]


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
    appendix_ids = [m["id"] for m in SLIDES if m["id"].startswith("A")]
    appendix_n = len(appendix_ids)
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
        f"{appendix_n}（第 {page_span(appendix_ids)} 頁，依序 A0 Dashboard 示意、A2 與 A2b 補充圖表、A3 待料通知、A4 CRM 觸發門檻、A5 客訴回訪、A6 部署與閉環、A1 術語表；代號不改，只換順序）。",
        f"- 計入 15 頁上限的是大綱 1 張加內容頁 14 張，合計 15。提案摘要與附錄 {appendix_n} 張不計入。",
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
        "報告欄是該頁數字轉抄的來源文件（專案文件，保留）；v3.7 起投影片頁腳不再印「來源：」列，頁碼在右下角。圖欄是該頁對應的報告圖。自 v3.3 起 F1–F6 與 F9_pipeline 在簡報裡用 pptx 原生形狀重畫，數字讀 `reports/figures/figure_values.json`（`python pipeline/make_figures.py --values-only` 產生，與 PNG 畫的值相同）；F8 在第 8 頁用原生形狀（`draw_f8`）；v3.6 起第 10 頁不再畫 F7（改風險等級對照表），附錄 A0 改五個 Dashboard 示意（原生形狀）；只有 F9 季趨勢仍貼 `reports/figures/F9.png`。PNG 原檔留在 `reports/figures/` 供報告用。",
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
        f"共 {len(placeholders)} 處。P12 的四則範本（每渠道一則）在 build 時讀 `knowledge/generated_examples.md` 前 76 字與引用條目，不在本腳本寫死。",
        "",
        "## 待核（不是占位，但數字來源要對得上）",
        "",
        "- P1 三站比率轉抄 `reports/T7_stats_tests.md` 作者層級表，簡報寫成論壇發言者流失率：Mobile01 18.2%、PTT 14.1%、Dcard 6.8%。P2 已刪這張表，改放三個流失前兆。",
        "- 摘要與 P14 成果層「提升 10 個百分點」是 `會議記錄_2026-09-30.md` §四的假設值，導入後以基期實測校正，不是已觀測的提升。",
        "- P3「態度負面 61%」依本任務大綱。`專案架構_2026-09-23.md` §0.1 寫的是 68%。`reports/T7_stats_tests.md` 只給態度面向的流失率 4.7%（62／1,306），沒有負面占比。簡報先用 61%。",
        "- P10 表格的 r4 用架構頁四捨五入（P 0.62、R 0.77、κ 0.64）。T8 ep2 原值 P 0.617、R 0.769、κ 0.642 在該頁備註。校準曲線在附錄 A2b。F1 0.685 沒有放進 25–35 字備註。",
        "- P1 內文不再寫 p<.001 與 Cramér's V=0.125。檢定見統計檢定報告（T7），χ²=99.5 仍在頁上。",
        "- P2 刪三站流失率表。Dcard 偏購車階段不在頁上（v3.7 起頁腳沒有來源列）。χ²(2)=99.5、V=0.125 與 P1 重複，依清單刪掉。",
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
        "腳本列出非包含關係的形狀重疊、超出頁面或壓到右下角頁碼的形狀，以及每張預覽圖的 PIL 空白比例。文字放在卡片上、標籤放在方塊內這種包含關係不算重疊。",
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
    if expected != 24:
        raise SystemExit(f"總張數應為 24（摘要 1＋大綱 1＋內容 14＋附錄 8），SLIDES 給出 {expected}")
    if len(prs.slides) != expected:
        raise SystemExit(f"頁數應為 {expected}，實際 {len(prs.slides)}")
    content = sum(1 for m in SLIDES if m["id"].startswith("P"))
    appendix = sum(1 for m in SLIDES if m["id"].startswith("A"))
    if content != 14 or appendix != 8:
        raise SystemExit(f"內容頁應為 14、附錄應為 8，實際內容 {content}、附錄 {appendix}")
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
